"""Login/logout/user-management functions. All state lives in
`app.storage.user`, which NiceGUI signs and persists via a browser cookie
(requires `storage_secret` — ngfw.run_app sets this from AppConfig).
"""
from __future__ import annotations

import hashlib
import hmac
import re
from typing import TYPE_CHECKING, Any

import bcrypt
from nicegui import app, ui

from ..config import AppConfig
from .storage import JSONUserStore, UserStore

if TYPE_CHECKING:
    from ..pages.registry import NavItem

_store: UserStore | None = None
_config: AppConfig | None = None

DEFAULT_ROLE = "user"
_LEGACY_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def configure(config: AppConfig, store: UserStore | None = None) -> None:
    """Wire up the user store. Called automatically by `ngfw.run_app`;
    pass a custom `store` there if you don't want the default JSON file."""
    global _store, _config
    _store = store or JSONUserStore(config.users_file)
    _config = config


def _require_store() -> UserStore:
    if _store is None:
        raise RuntimeError(
            "ngfw.auth is not configured yet. Call ngfw.run_app(config) "
            "(or ngfw.auth.service.configure(config)) before using auth."
        )
    return _store


def _check_hash(password: str, hashed: str) -> tuple[bool, bool]:
    """(matches, is_legacy). Besides bcrypt, accepts an unsalted SHA-256
    hex digest — the format of older apps' users.json — so imported users
    can log in with their existing password."""
    if hashed.startswith("$2"):
        return bcrypt.checkpw(password.encode(), hashed.encode()), False
    if _LEGACY_SHA256.match(hashed):
        digest = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(digest, hashed), True
    return False, False


def verify_password(username: str, password: str) -> bool:
    """Check a password. A correct password stored in the legacy SHA-256
    format is re-saved as bcrypt on the spot, so legacy hashes disappear
    as users log in."""
    store = _require_store()
    hashed = store.get_password_hash(username)
    if not hashed or not password:
        return False
    ok, legacy = _check_hash(password, hashed)
    if ok and legacy:
        store.set_password_hash(username, bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())
    return ok


def user_exists(username: str) -> bool:
    return _require_store().user_exists(username)


def create_user(username: str, password: str, *, is_admin: bool | None = None) -> None:
    """Create a new user, or overwrite an existing one's password. Fine to
    call from a one-off setup script (see templates/settings_page.py's
    change-password/add-user forms for the running-app case too).

    `is_admin` left as None preserves an existing user's admin status (or
    defaults a brand-new user to non-admin); pass True/False to set it
    explicitly in the same call. Role and other fields are preserved.
    """
    _require_store().create_user(username, password, is_admin=is_admin)


def import_user(username: str, password_hash: str, *, is_admin: bool = False, **fields: Any) -> None:
    """Add a user with an existing password hash (bcrypt, or a legacy
    SHA-256 hex digest that is upgraded at the first login), plus any
    app-defined fields — for moving users over from another app."""
    store = _require_store()
    store.set_password_hash(username, password_hash)
    store.set_admin(username, is_admin)
    for key, value in fields.items():
        store.set_field(username, key, value)


def list_users() -> list[str]:
    """Usernames currently in the store, for an admin/settings page."""
    return _require_store().list_users()


def delete_user(username: str) -> None:
    """Remove a user. Refuses to delete the last remaining admin."""
    if is_admin(username) and admin_count() <= 1:
        raise ValueError(f"Can't delete '{username}' — they're the only admin left.")
    _require_store().delete_user(username)


def is_admin(username: str | None = None) -> bool:
    """Whether `username` (default: the current logged-in user) is an
    admin. False for a logged-out visitor or an unknown username."""
    if username is None:
        username = current_user()
    if not username:
        return False
    return _require_store().is_admin(username)


def set_admin(username: str, admin: bool) -> None:
    """Promote or demote a user. Raises ValueError if the username doesn't
    exist. Refuses to demote the last remaining admin, so you can't
    accidentally lock every admin-only page."""
    if not admin and is_admin(username) and _require_store().admin_count() <= 1:
        raise ValueError(f"Can't remove admin from '{username}' — they're the only admin left.")
    _require_store().set_admin(username, admin)


def admin_count() -> int:
    """How many users currently have is_admin set — mainly so a Settings
    page can decide whether it's safe to let someone demote themselves."""
    return _require_store().admin_count()


# --- app-defined user fields and roles (ngfw 0.2) ---------------------------

def get_user_field(username: str | None, key: str, default: Any = None) -> Any:
    """An app-defined field of a user (default: the current user)."""
    username = username or current_user()
    if not username:
        return default
    return _require_store().get_field(username, key, default)


def set_user_field(username: str, key: str, value: Any) -> None:
    """Set an app-defined field of a user; `None` removes it."""
    _require_store().set_field(username, key, value)


def get_role(username: str | None = None) -> str | None:
    """The user's role (default: the current user): the `role` field, or
    "user" when it isn't set. None for a logged-out visitor."""
    username = username or current_user()
    if not username:
        return None
    return _require_store().get_field(username, "role", DEFAULT_ROLE) or DEFAULT_ROLE


def set_role(username: str, role: str) -> None:
    set_user_field(username, "role", None if role == DEFAULT_ROLE else role)


def can_access(item: "NavItem", username: str | None = None) -> bool:
    """Whether a user (default: the current one) may open a registered page.

    - public pages (`requires_auth=False`): everyone;
    - otherwise the user must be logged in;
    - `requires_admin=True`: admins only;
    - a user whose role is in `AppConfig.restricted_roles` (e.g. "portal")
      may open only pages that list that role in `roles`;
    - everyone else may open pages without `roles`, pages whose `roles`
      include their role, and — admins — every page.
    """
    if not item.requires_auth:
        return True
    username = username or current_user()
    if not username or not user_exists(username):
        return False
    admin = is_admin(username)
    if item.requires_admin and not admin:
        return False
    role = get_role(username)
    restricted = _config.restricted_roles if _config else set()
    if role in restricted:
        return bool(item.roles) and role in item.roles
    return item.roles is None or role in item.roles or admin


def home_path(username: str | None = None) -> str:
    """Landing page for a user: `AppConfig.role_home[role]`, else
    `AppConfig.after_login_path`."""
    after = _config.after_login_path if _config else "/"
    role = get_role(username)
    if _config and role in _config.role_home:
        return _config.role_home[role]
    return after


def login(username: str, password: str) -> bool:
    """Verify credentials and, on success, mark the current browser
    session as authenticated. Returns whether it succeeded."""
    if verify_password(username, password):
        app.storage.user.update({"authenticated": True, "username": username})
        return True
    return False


def logout(redirect_to: str = "/login") -> None:
    app.storage.user.clear()
    ui.navigate.to(redirect_to)


def current_user() -> str | None:
    return app.storage.user.get("username") if app.storage.user.get("authenticated") else None
