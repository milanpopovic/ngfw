"""A public page (no login required) showing the shell + theme."""
from nicegui import ui

import ngfw
from app_config import config


@ngfw.page("/", "Home", icon="home", requires_auth=False)
def home_page() -> None:
    with ngfw.frame(config, "/"):
        ui.label("Welcome to the ngfw demo").classes("text-2xl font-bold")
        ui.label(
            "This page is public. Try Cases or Settings in the sidebar — "
            "those are behind the login (demo / demo1234)."
        ).classes("text-grey-8")
