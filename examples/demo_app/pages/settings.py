"""A protected page showing the form components and a confirm dialog."""
from nicegui import ui

import ngfw
from ngfw import components
from app_config import config


@ngfw.page("/settings", "Settings", icon="settings", group="Account")
def settings_page() -> None:
    with ngfw.frame(config, "/settings"):
        ui.label("Settings").classes("text-2xl font-bold")
        ui.label(f"Logged in as {ngfw.auth.current_user()}").classes("text-grey-8 mb-2")

        with components.form_card("Update display name"):
            name = components.labeled_input("Display name", validation={"Required": components.required()})

            async def save() -> None:
                if name.validate():
                    ui.notify(f"Saved '{name.value}' (demo only, not persisted)", color="positive")

            ui.button("Save", on_click=save).props("color=primary")

        async def do_logout() -> None:
            if await components.confirm("Log out of the demo app?"):
                ngfw.auth.logout(config.login_path)

        ui.button("Log out", on_click=do_logout).props("outline color=negative").classes("mt-4")
