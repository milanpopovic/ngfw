"""The built-in /login page. Installed automatically by `ngfw.run_app`
when `AppConfig.auth_enabled` is True. Texts follow `AppConfig.language`.
"""
from __future__ import annotations

from nicegui import app, ui

from ..config import AppConfig
from ..i18n import t
from ..pages.registry import NAV_ITEMS, page
from . import service


def install_login_page(config: AppConfig) -> None:
    @page(config.login_path, "Login", show_in_nav=False, requires_auth=False)
    def login_page() -> None:
        if service.current_user():
            ui.navigate.to(service.home_path())
            return

        async def try_login() -> None:
            name = (username.value or "").strip()
            if service.login(name, password.value or ""):
                # go back to the page that sent us here — if this user may open it
                target = app.storage.user.pop("referrer_path", None)
                item = next((i for i in NAV_ITEMS if i.path == target), None)
                if item and item.path != config.login_path and service.can_access(item, name):
                    ui.navigate.to(target)
                else:
                    ui.navigate.to(service.home_path(name))
            else:
                ui.notify(t("invalid_login"), color="negative")

        with ui.card().classes("absolute-center w-80 gap-2"):
            ui.label(config.title).classes("text-xl font-bold mb-2")
            username = ui.input(t("username")).classes("w-full")
            username.on("keydown.enter", try_login)
            password = ui.input(t("password"), password=True, password_toggle_button=True).classes("w-full")
            password.on("keydown.enter", try_login)
            ui.button(t("login"), on_click=try_login).classes("w-full mt-2")
