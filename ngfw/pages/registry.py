"""Multipage core: a `@page` decorator that registers a NiceGUI page AND
adds it to a central nav registry in one step, so adding a page auto-wires
its sidebar entry too.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from nicegui import ui


@dataclass
class NavItem:
    path: str
    label: str
    icon: str | None = None
    group: str | None = None
    requires_auth: bool = True
    requires_admin: bool = False
    show_in_nav: bool = True
    order: int = 0
    func: Optional[Callable] = None
    roles: Optional[frozenset[str]] = None


NAV_ITEMS: list[NavItem] = []


def page(
    path: str,
    label: str,
    *,
    icon: str | None = None,
    group: str | None = None,
    requires_auth: bool = True,
    requires_admin: bool = False,
    show_in_nav: bool = True,
    order: int = 0,
    roles: set[str] | None = None,
):
    """Decorator combining `@ui.page` with nav registration.

    Usage::

        import ngfw

        @ngfw.page('/', 'Home', icon='home')
        def home_page():
            ui.label('Hello')

        @ngfw.page('/reports', 'Reports', icon='bar_chart', group='Data')
        def reports_page():
            ...

        @ngfw.page('/admin', 'Admin', icon='admin_panel_settings', requires_admin=True)
        def admin_page():
            ...

    `requires_auth=True` (the default) means the auth middleware will
    redirect anonymous visitors to the login page. Set it False for public
    pages. `requires_admin=True` additionally requires the logged-in user
    to have `is_admin` set (see `ngfw.auth.is_admin`/`set_admin`) — anyone
    else gets redirected to `AppConfig.after_login_path`, and the sidebar
    hides the entry from them entirely. `show_in_nav=False` registers a
    route without a sidebar entry (useful for detail pages reached via
    links, not the menu). `roles={"portal"}` limits the page to users with
    one of those roles (admins always pass); a role listed in
    `AppConfig.restricted_roles` can open ONLY pages that name it here.
    See `ngfw.auth.can_access`.
    """

    def decorator(func: Callable) -> Callable:
        decorated = ui.page(path)(func)
        NAV_ITEMS.append(
            NavItem(
                path=path,
                label=label,
                icon=icon,
                group=group,
                requires_auth=requires_auth,
                requires_admin=requires_admin,
                show_in_nav=show_in_nav,
                order=order,
                func=decorated,
                roles=frozenset(roles) if roles is not None else None,
            )
        )
        return decorated

    return decorator


def get_nav_items(include_hidden: bool = False) -> list[NavItem]:
    """Registered pages, sorted by (order, label). By default only the
    ones meant to appear in the sidebar (show_in_nav=True)."""
    items = NAV_ITEMS if include_hidden else [i for i in NAV_ITEMS if i.show_in_nav]
    return sorted(items, key=lambda i: (i.order, i.label))


def grouped_nav_items(
    include_hidden: bool = False,
    group_order: list[str | None] | None = None,
) -> dict[str | None, list[NavItem]]:
    """Nav items bucketed by their `group` (None = ungrouped).

    Groups follow `group_order` when given (see `AppConfig.nav_group_order`);
    groups not listed there come after, in their first-seen order. Items
    inside each group keep their (order, label) sort."""
    groups: dict[str | None, list[NavItem]] = {}
    for item in get_nav_items(include_hidden):
        groups.setdefault(item.group, []).append(item)
    if group_order:
        rank = {g: i for i, g in enumerate(group_order)}
        groups = dict(sorted(groups.items(), key=lambda kv: rank.get(kv[0], len(rank))))
    return groups
