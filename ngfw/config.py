"""Central configuration object for an ngfw-based application.

An app built on ngfw creates one `AppConfig`, passes it to `ngfw.run_app`,
and everything else (theming, the shell, auth, nav) reads from it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class AppConfig:
    # --- Identity ---
    title: str = "NiceGUI App"
    """Shown in the browser tab and the shell header."""

    subtitle: str | None = None
    """Optional small text under the title in the header, e.g. a tagline."""

    favicon: str = "🧭"
    """Emoji or path used as the favicon."""

    # --- Theming ---
    primary_color: str = "#1976d2"
    secondary_color: str = "#26a69a"
    accent_color: str = "#9c27b0"
    dark_mode_default: bool = False
    """Initial dark-mode state for a viewer with no stored preference yet."""

    # --- Storage / sessions ---
    storage_secret: str = "CHANGE-ME-before-deploying"
    """Passed to ui.run(storage_secret=...). Required for app.storage.user
    and for the auth session cookie to be signed. Override this per app,
    e.g. from an environment variable."""

    # --- Auth ---
    auth_enabled: bool = True
    """If True, pages registered with requires_auth=True (the default)
    redirect anonymous visitors to /login."""

    users_file: Path = field(default_factory=lambda: Path("users.json"))
    """Where the default JSON user store keeps credentials. Ignored if a
    custom UserStore is passed to ngfw.auth.configure()."""

    login_path: str = "/login"
    after_login_path: str = "/"

    restricted_roles: set[str] = field(default_factory=set)
    """Roles that may open ONLY pages registered with that role in
    `@ngfw.page(..., roles={...})`, e.g. {"portal"} for external users who
    must see nothing but their portal page. Users with any other role (or
    none) see every page that isn't limited by `roles`. See
    `ngfw.auth.can_access`."""

    role_home: dict[str, str] = field(default_factory=dict)
    """Landing page per role, e.g. {"portal": "/portal"} — used after login
    and when a user opens a page their role can't access. Roles not listed
    use `after_login_path`."""

    # --- Language ---
    language: str = "en"
    """Language of the framework's own texts (login page, logout, dialog
    buttons): "en" or "sr". See `ngfw.i18n`."""

    # --- Layout ---
    show_header: bool = True
    show_sidebar: bool = True
    show_footer: bool = True
    footer_text: str | None = None

    nav_group_order: list[str | None] = field(default_factory=list)
    """Order of top-level sidebar groups, e.g. [None, 'Podaci', 'Admin'].
    None = pages registered without a group. Groups not listed keep their
    default position after the listed ones. Pages inside each group are
    not affected (they stay sorted by their own `order`, then label)."""

    header_extra: Callable[[], None] | None = None
    """Optional function that adds extra elements to the right side of the
    header, before the dark-mode and account buttons — e.g. a selector for
    the current client. Called inside a `ui.row`, once per page render."""

    content_max_width: str = "max-w-6xl"
    """Tailwind max-width class applied to the centered content column
    `ngfw.frame` wraps each page in (~1152px by default). Pass
    "max-w-full" (or "max-w-none") for pages/apps that want to use the
    full available width instead — e.g. a wide data-grid page that
    already scrolls horizontally on its own."""

    # --- Periodic backups ---
    backup_source_dir: Path | None = None
    """Folder to back up periodically as a zip (e.g. your app's `data/`
    directory). Left as None (the default), periodic backups are off —
    nothing else below matters until this is set."""

    backup_dir: Path | None = None
    """Where zip backups are written. Must NOT be inside
    `backup_source_dir` — the archive would end up including itself (and
    growing) on every later run. None (the default, once
    `backup_source_dir` is set) uses a `backups_zip` folder next to it."""

    backup_interval_seconds: int = 24 * 60 * 60
    """How often to take a periodic zip backup, in seconds. Default is
    daily; common alternatives: 3600 (hourly), 7 * 24 * 60 * 60 (weekly).
    The first backup runs right at startup, then every interval after."""

    backup_keep_count: int | None = 30
    """How many of the most recent zip backups to keep — older ones are
    deleted automatically so the backup folder doesn't grow forever.
    None disables pruning (keep everything)."""

    # --- Editing files from Word (WebDAV) ---
    webdav_folders: dict[str, Path] = field(default_factory=dict)
    """Folders admins may edit directly from desktop Word, as
    {"name": folder}, e.g. {"sabloni": DATA / "TEMPLATES"}. Each is shared
    at `<webdav_path>/<name>/`. Empty (the default) = off. Needs
    `pip install wsgidav a2wsgi` and HTTPS. See `ngfw.webdav`."""

    webdav_path: str = "/dav"
    """URL prefix of the WebDAV share."""

    # --- Networking (forwarded to ui.run) ---
    host: str = "0.0.0.0"
    port: int = 8080
    reload: bool = False
