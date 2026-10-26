"""Pluggable user storage for auth.

The default `JSONUserStore` is fine for small internal tools (matches what
Milan's earlier auth starter did, minus the Postgres dependency). For an
app that already has a database, implement the `UserStore` protocol
against SQLModel/asyncpg (or anything else) and pass it to
`ngfw.auth.service.configure(config, store=MyStore())`.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional, Protocol

import bcrypt

# Keys the store manages itself; everything else in a user record is an
# app-defined field (role, clients, e-mail, ...) kept as-is.
_CORE_KEYS = {"password_hash", "is_admin"}


class UserStore(Protocol):
    def get_password_hash(self, username: str) -> Optional[str]: ...

    def user_exists(self, username: str) -> bool: ...

    def create_user(self, username: str, password: str, *, is_admin: Optional[bool] = None) -> None: ...

    def list_users(self) -> list[str]: ...

    def is_admin(self, username: str) -> bool: ...

    def set_admin(self, username: str, is_admin: bool) -> None: ...

    def admin_count(self) -> int: ...

    # --- added in ngfw 0.2 (JSONUserStore implements them) ---
    def set_password_hash(self, username: str, password_hash: str) -> None: ...

    def get_field(self, username: str, key: str, default: Any = None) -> Any: ...

    def set_field(self, username: str, key: str, value: Any) -> None: ...

    def delete_user(self, username: str) -> None: ...


class JSONUserStore:
    """File-backed user store::

        {"username": {"password_hash": "<bcrypt hash>", "is_admin": false,
                      "role": "portal", "clients": ["obrenovac"], ...}, ...}

    `password_hash` and `is_admin` are managed by the store; any other key
    is an app-defined field (`get_field` / `set_field`) and survives
    password changes and admin toggles.

    Transparently upgrades the older flat format
    (`{"username": "<bcrypt hash>", ...}`, no roles) the moment it's read —
    existing users just come back as non-admin until you promote one. The
    file on disk is rewritten in the new format the next time anything is
    saved; nothing needs a manual migration step.
    """

    def __init__(self, path: Path | str):
        self.path = Path(path)
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("{}", encoding="utf-8")

    def _read(self) -> dict[str, dict]:
        text = self.path.read_text(encoding="utf-8").strip()
        raw = json.loads(text) if text else {}
        return {
            username: (value if isinstance(value, dict) else {"password_hash": value, "is_admin": False})
            for username, value in raw.items()
        }

    def _write(self, data: dict[str, dict]) -> None:
        # Write to a temp file and swap, so a crash mid-write can't leave a
        # half-written (unreadable) users file that locks everyone out.
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def _require(self, data: dict[str, dict], username: str) -> dict:
        if username not in data:
            raise ValueError(f"No such user: {username}")
        return data[username]

    def get_password_hash(self, username: str) -> Optional[str]:
        record = self._read().get(username)
        return record.get("password_hash") if record else None

    def user_exists(self, username: str) -> bool:
        return username in self._read()

    def create_user(self, username: str, password: str, *, is_admin: Optional[bool] = None) -> None:
        """Create a new user, or overwrite an existing one's password.

        `is_admin` left as None preserves the existing user's admin status
        (or defaults a brand-new user to non-admin); pass True/False to set
        it explicitly at the same time. App-defined fields are preserved.
        """
        data = self._read()
        existing = data.get(username, {})
        record = {k: v for k, v in existing.items() if k not in _CORE_KEYS}
        record["password_hash"] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        record["is_admin"] = is_admin if is_admin is not None else existing.get("is_admin", False)
        data[username] = record
        self._write(data)

    # convenience alias — same operation, clearer name at call sites
    def set_password(self, username: str, password: str) -> None:
        self.create_user(username, password)

    def set_password_hash(self, username: str, password_hash: str) -> None:
        """Store an already-computed hash as-is (used when upgrading a
        legacy hash to bcrypt, and when importing users from another app).
        Creates the user if it doesn't exist."""
        data = self._read()
        record = data.setdefault(username, {"is_admin": False})
        record["password_hash"] = password_hash
        self._write(data)

    def list_users(self) -> list[str]:
        return sorted(self._read().keys())

    def is_admin(self, username: str) -> bool:
        record = self._read().get(username)
        return bool(record and record.get("is_admin", False))

    def set_admin(self, username: str, is_admin: bool) -> None:
        data = self._read()
        self._require(data, username)["is_admin"] = is_admin
        self._write(data)

    def admin_count(self) -> int:
        return sum(1 for record in self._read().values() if record.get("is_admin", False))

    def get_field(self, username: str, key: str, default: Any = None) -> Any:
        record = self._read().get(username)
        return record.get(key, default) if record else default

    def set_field(self, username: str, key: str, value: Any) -> None:
        """Set an app-defined field; `None` removes it."""
        if key in _CORE_KEYS:
            raise ValueError(f"'{key}' is managed by the store — use set_password / set_admin.")
        data = self._read()
        record = self._require(data, username)
        if value is None:
            record.pop(key, None)
        else:
            record[key] = value
        self._write(data)

    def delete_user(self, username: str) -> None:
        data = self._read()
        self._require(data, username)
        del data[username]
        self._write(data)
