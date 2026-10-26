"""The framework entry point: wires up auth, the login page, and (if
asked) auto-imports your pages package, then hands off to ui.run.
"""
from __future__ import annotations

import importlib

from nicegui import app as nicegui_app
from nicegui import ui

from .config import AppConfig


def create_app(config: AppConfig, *, pages_package: str | None = None) -> None:
    """Wire up an ngfw application without starting the server. Useful if
    you want to call `ui.run(...)` yourself. Most apps should use
    `run_app` instead.

    - Imports `pages_package` (if given) so its `@ngfw.page`-decorated
      functions register themselves.
    - Always configures the user store (so `ngfw.auth.*` — e.g. a
      Settings page listing/adding users — works even if login isn't
      being enforced right now).
    - If `config.auth_enabled`, additionally installs the built-in
      /login page and adds the auth-redirect middleware.
    - If `config.backup_source_dir` is set, starts the periodic zip
      backup loop (see `ngfw.backup`).
    - If `config.webdav_folders` is set, mounts the WebDAV share for
      editing those files from Word (see `ngfw.webdav`).
    """
    if pages_package:
        importlib.import_module(pages_package)

    # Imported lazily to keep import order flexible (avoids any
    # circularity between ngfw's top-level package and ngfw.auth).
    from .auth import service
    from .backup import start_periodic_backup

    service.configure(config)

    from .i18n import set_language
    set_language(config.language)

    if config.auth_enabled:
        from .auth import pages as auth_pages
        from .auth.middleware import build_auth_middleware

        auth_pages.install_login_page(config)
        nicegui_app.add_middleware(build_auth_middleware(config))

    start_periodic_backup(config)

    if config.webdav_folders:
        from .webdav import mount
        mount(config)


def run_app(config: AppConfig, *, pages_package: str | None = None, **ui_run_kwargs) -> None:
    """`create_app(...)` followed by `ui.run(...)`, using AppConfig's
    networking settings as defaults (override any of them by passing
    keyword arguments through, e.g. `run_app(config, port=8081)`).

    Call this from your app's main.py, guarded the way NiceGUI expects::

        if __name__ in {"__main__", "__mp_main__"}:
            ngfw.run_app(config, pages_package="myapp.pages")
    """
    create_app(config, pages_package=pages_package)
    run_kwargs = dict(
        title=config.title,
        favicon=config.favicon,
        host=config.host,
        port=config.port,
        reload=config.reload,
        storage_secret=config.storage_secret,
    )
    run_kwargs.update(ui_run_kwargs)
    ui.run(**run_kwargs)
