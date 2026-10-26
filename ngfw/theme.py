"""App-wide theming: brand colors and a per-user dark-mode toggle."""
from __future__ import annotations

from typing import Callable

from nicegui import app, ui

from .config import AppConfig


def apply_theme(config: AppConfig) -> None:
    """Apply the AppConfig's brand colors to the current page."""
    ui.colors(
        primary=config.primary_color,
        secondary=config.secondary_color,
        accent=config.accent_color,
    )


def dark_mode_toggle(config: AppConfig) -> tuple[ui.dark_mode, Callable[[], None]]:
    """Create a `ui.dark_mode` element bound to a per-user stored
    preference, and return it along with a toggle callback.

    Requires ui.run(storage_secret=...) to be set (ngfw.run_app does this).
    """
    stored = app.storage.user.get("dark_mode", config.dark_mode_default)
    dark = ui.dark_mode(value=stored)

    def toggle() -> None:
        dark.value = not dark.value
        app.storage.user["dark_mode"] = dark.value

    return dark, toggle
# x
