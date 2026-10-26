"""Editing files on the server directly from desktop Word (WebDAV).

An admin clicks "Uredi u Wordu" next to a template; Word opens the file
straight from the server and Ctrl+S saves it back — no download/upload.

How it works:

- `AppConfig.webdav_folders = {"sabloni": DATA / "TEMPLATES"}` turns it on.
  Each folder is shared at `<webdav_path>/<name>/` (default `/dav/sabloni/`)
  by a WebDAV server (wsgidav) mounted inside the NiceGUI app — same port,
  same process, nothing extra to run.
- Word logs in with HTTP Basic auth: the app's own username and password.
  Only ADMINS are accepted (`ngfw.auth.is_admin`). Word sends the password
  only over HTTPS, so the app must be reached through HTTPS (see README).
- The page registered by `register_page()` (default `/sabloni`, admins
  only) lists the .docx files with "Uredi u Wordu" (an `ms-word:ofe|u|…`
  link), "Preuzmi", and "Proveri" (lists the docxtpl `{{ placeholders }}`,
  so a field broken by editing is spotted before documents are made).

Requires `pip install wsgidav a2wsgi` (only when webdav_folders is set).
"""
from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import quote

from nicegui import app as nicegui_app
from nicegui import ui

from .config import AppConfig

log = logging.getLogger("ngfw.webdav")

WORD_EXTENSIONS = (".docx", ".dotx", ".doc")


# --- WebDAV server ------------------------------------------------------------

def _domain_controller_class():
    from wsgidav.dc.base_dc import BaseDomainController

    class AdminDomainController(BaseDomainController):
        """Basic auth against ngfw's user store; admins only."""

        def __str__(self) -> str:
            return "ngfw-admins"

        def get_domain_realm(self, path_info, environ):
            return "ngfw"

        def require_authentication(self, realm, environ):
            return True

        def basic_auth_user(self, realm, user_name, password, environ):
            from .auth import service
            try:
                ok = service.verify_password(user_name, password) and service.is_admin(user_name)
            except Exception:  # never let a store error open the share
                log.exception("WebDAV auth failed for %s", user_name)
                return False
            if not ok:
                log.warning("WebDAV: login refused for %r", user_name)
            return bool(ok)

        def supports_http_digest_auth(self):
            return False

    return AdminDomainController


def mount(config: AppConfig) -> None:
    """Mount the WebDAV server for `config.webdav_folders` (no-op if empty)."""
    if not config.webdav_folders:
        return
    try:
        from a2wsgi import WSGIMiddleware
        from wsgidav.wsgidav_app import WsgiDAVApp
    except ImportError as e:
        raise RuntimeError("AppConfig.webdav_folders is set, but WebDAV packages are missing: "
                           "pip install wsgidav a2wsgi") from e

    mapping = {}
    for name, folder in config.webdav_folders.items():
        folder = Path(folder)
        if not folder.is_dir():
            raise RuntimeError(f"webdav_folders[{name!r}]: folder does not exist: {folder}")
        mapping[f"/{name}"] = {"root": str(folder.resolve()), "readonly": False}

    dav = WsgiDAVApp({
        "provider_mapping": mapping,
        "mount_path": config.webdav_path,  # so links in replies are /dav/<name>/...
        "http_authenticator": {
            "domain_controller": _domain_controller_class(),
            "accept_basic": True,
            "accept_digest": False,
            "default_to_digest": False,
            "trusted_auth_header": None,
        },
        "simple_dc": {"user_mapping": {}},  # unused: AdminDomainController decides
        "lock_storage": True,        # Word needs LOCK/UNLOCK to open for editing
        "property_manager": True,
        "dir_browser": {"enable": False},
        "verbose": 1,
        "logging": {"enable_loggers": []},
    })
    nicegui_app.mount(config.webdav_path, WSGIMiddleware(dav, workers=4))
    log.info("WebDAV: %s -> %s", config.webdav_path, ", ".join(mapping))


# --- helpers for pages --------------------------------------------------------

def file_url_path(config: AppConfig, folder_name: str, file_name: str) -> str:
    """Server path of a shared file, e.g. /dav/sabloni/Koverta%20template.docx."""
    return f"{config.webdav_path}/{quote(folder_name)}/{quote(file_name)}"


def open_in_word(config: AppConfig, folder_name: str, file_name: str) -> None:
    """Open a shared file in desktop Word for editing (call from a click handler).
    The full https:// address is taken from the browser, so it also works
    behind a reverse proxy."""
    path = file_url_path(config, folder_name, file_name)
    ui.run_javascript(f"window.location.href = 'ms-word:ofe|u|' + window.location.origin + {path!r};")


def placeholders(file: Path) -> list[str]:
    """docxtpl/Jinja variables used in a template, sorted ({{ x }} and {% … %})."""
    from docxtpl import DocxTemplate
    return sorted(DocxTemplate(str(file)).get_undeclared_template_variables())


def word_files(folder: Path) -> list[Path]:
    return sorted(p for p in Path(folder).iterdir()
                  if p.is_file() and p.suffix.lower() in WORD_EXTENSIONS and not p.name.startswith(("~$", ".")))


# --- the "Šabloni" page -------------------------------------------------------

def register_page(config: AppConfig, path: str = "/sabloni", label: str = "Šabloni", *,
                  icon: str = "edit_document", group: str | None = None, order: int = 50,
                  labels: dict[str, str] | None = None) -> None:
    """Admin-only page listing the Word files of every webdav folder.
    `labels` = display names for the folders, e.g. {"racuni": "Računi"}."""
    from .pages.registry import page
    from .shell import frame

    @page(path, label, icon=icon, group=group, order=order, requires_admin=True)
    def sabloni_page() -> None:
        with frame(config, path):
            ui.label(label).classes("text-2xl font-bold")
            ui.markdown(
                "**Uredi u Wordu** otvara šablon direktno sa servera; posle izmene samo "
                "**Sačuvaj** (Ctrl+S) u Wordu i zatvorite dokument. Word traži korisničko ime i "
                "lozinku — iste kao za ovu aplikaciju (samo administratori).\n\n"
                "Polja kao `{{ ime_duznika }}` ne menjajte. Posle izmene kliknite **Proveri**."
            ).classes("text-sm text-grey-8")

            for name, folder in config.webdav_folders.items():
                files = word_files(Path(folder))
                with ui.card().classes("w-full"):
                    if len(config.webdav_folders) > 1:
                        title = (labels or {}).get(name) or name.replace("_", " ").capitalize()
                        ui.label(title).classes("text-lg font-medium")
                    if not files:
                        ui.label("Nema Word šablona u ovom folderu.").classes("text-grey")
                    for f in files:
                        with ui.row().classes("items-center w-full gap-2 no-wrap"):
                            ui.icon("description").classes("text-primary")
                            ui.label(f.name).classes("grow")
                            ui.button("Uredi u Wordu", icon="edit",
                                      on_click=lambda n=name, fn=f.name: open_in_word(config, n, fn)
                                      ).props("dense color=primary")
                            ui.button(icon="download", on_click=lambda p=f: ui.download.file(p)
                                      ).props("dense flat").tooltip("Preuzmi")
                            ui.button(icon="fact_check", on_click=lambda p=f: _check(p)
                                      ).props("dense flat").tooltip("Proveri polja")


def _check(file: Path) -> None:
    try:
        used = placeholders(file)
    except Exception as e:  # broken {{ }} / {% %} syntax shows up here
        _show(file.name, f"❌ Šablon ima grešku u poljima:\n\n`{e}`")
        return
    _show(file.name, f"✅ Šablon je ispravan. Polja u šablonu ({len(used)}):\n\n"
          + (", ".join(f"`{p}`" for p in used) or "—"))


def _show(title: str, text: str) -> None:
    with ui.dialog() as d, ui.card().classes("max-w-2xl"):
        ui.label(title).classes("text-lg font-medium")
        ui.markdown(text)
        ui.button("U redu", on_click=d.close).props("flat")
    d.open()
