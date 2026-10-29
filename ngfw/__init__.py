"""ngfw — Milan's reusable NiceGUI application framework.

Multipage routing + nav, auth/sessions, an app shell with theming, and a
handful of shared UI components, so a new app starts from a working
skeleton instead of a blank file.

Typical main.py::

    import ngfw
    from nicegui import ui

    config = ngfw.AppConfig(title="My App", storage_secret="change-me")

    @ngfw.page('/', 'Home', icon='home')
    def home_page():
        with ngfw.frame(config, '/'):
            ui.label('Hello, world')

    if __name__ in {"__main__", "__mp_main__"}:
        ngfw.run_app(config)
"""
from .app import create_app, run_app
from .config import AppConfig
from .pages.registry import NavItem, get_nav_items, grouped_nav_items, page
from .shell import frame, set_dirty
from . import auth, backup, components, i18n, tree, webdav

__all__ = [
    "AppConfig",
    "create_app",
    "run_app",
    "page",
    "NavItem",
    "get_nav_items",
    "grouped_nav_items",
    "frame",
    "set_dirty",
    "auth",
    "backup",
    "components",
    "i18n",
    "tree",
    "webdav",
]

__version__ = "0.4.1"
