"""The app shell: header, sidebar nav (built from the page registry),
and footer, wrapped around each page's content.
"""
from __future__ import annotations

from contextlib import contextmanager

from nicegui import app, ui

from . import theme
from .auth import service as auth_service
from .config import AppConfig
from .i18n import t
from .pages.registry import grouped_nav_items

# Upozorenje pri zatvaranju / osvežavanju / napuštanju stranice ako ima
# nesačuvanih izmena. Stranica uključuje/isključuje sa ngfw.set_dirty().
# Chrome prikazuje svoju (nepromenljivu) poruku.
UNSAVED_GUARD_JS = """<script>
window.prDirty = false;
if (!window.prUnloadHooked) {
  window.prUnloadHooked = true;
  window.addEventListener('beforeunload', (e) => {
    if (!window.prDirty) return;
    e.preventDefault(); e.returnValue = ''; return '';
  });
}
</script>"""


def set_dirty(value: bool = True) -> None:
    """Uključuje (True) ili isključuje (False) upozorenje o nesačuvanim
    izmenama za trenutnu stranicu."""
    ui.run_javascript(f"window.prDirty = {'true' if value else 'false'}")


@contextmanager
def frame(config: AppConfig, current_path: str | None = None, *, max_width: str | None = None):
    """Wrap a page's content in the standard ngfw shell::

        @ngfw.page('/', 'Home', icon='home')
        def home_page():
            with ngfw.frame(config, '/'):
                ui.label('Hello')

    `current_path` is used only to highlight the active sidebar item.

    `max_width` overrides `config.content_max_width` (default
    "max-w-6xl", ~1152px) for just this page — pass e.g.
    `max_width="max-w-full"` for a wide data-grid page that should use
    the full available width, while every other page in the app keeps
    the normal centered/capped layout::

        with ngfw.frame(config, '/grid', max_width='max-w-full'):
            ui.aggrid(...).classes('w-full')
    """
    ui.add_head_html(UNSAVED_GUARD_JS)
    theme.apply_theme(config)
    dark, toggle_dark = theme.dark_mode_toggle(config)
    drawer = None

    if config.show_header:
        with ui.header(elevated=True).classes("items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                if config.show_sidebar:
                    ui.button(icon="menu", on_click=lambda: drawer.toggle() if drawer else None).props(
                        "flat round color=white"
                    )
                ui.label(config.title).classes("text-xl font-bold")
                if config.subtitle:
                    ui.label(config.subtitle).classes("text-sm opacity-75 hidden sm:block")
            with ui.row().classes("items-center gap-1"):
                if config.header_extra:
                    config.header_extra()
                ui.button(icon="dark_mode", on_click=toggle_dark).props("flat round color=white").tooltip(t("dark_mode"))
                if config.auth_enabled and app.storage.user.get("authenticated"):
                    with ui.button(icon="account_circle").props("flat round color=white"):
                        with ui.menu():
                            username = app.storage.user.get("username")
                            if username:
                                ui.menu_item(username).props("disable")
                                ui.separator()
                            ui.menu_item(t("logout"), on_click=lambda: auth_service.logout(config.login_path))

    if config.show_sidebar:
        drawer = ui.left_drawer(bordered=True).props("width=260").style("gap: 2px; padding: 8px")  # zbijen meni, bez skrolovanja
        with drawer:
            for group, items in grouped_nav_items(group_order=config.nav_group_order).items():
                items = [i for i in items if auth_service.can_access(i)] if config.auth_enabled else [
                    i for i in items if not i.requires_admin]
                if not items:
                    continue
                if group:
                    ui.label(group).classes("text-xs uppercase text-grey mt-2 mb-0.5 px-2")
                for item in items:
                    active = current_path == item.path
                    with ui.link(target=item.path).classes("no-underline"):
                        with ui.row().classes(
                            "items-center gap-2 px-3 py-1.5 rounded-lg w-full "
                            + ("bg-primary text-white" if active else "hover:bg-grey-3")
                        ):
                            if item.icon:
                                ui.icon(item.icon)
                            ui.label(item.label)

    width_class = max_width if max_width is not None else config.content_max_width
    with ui.column().classes(f"w-full {width_class} mx-auto p-4 gap-4"):
        yield

    if config.show_footer:
        with ui.footer().classes("justify-center text-xs opacity-70 py-2"):
            ui.label(config.footer_text or f"© {config.title}")
