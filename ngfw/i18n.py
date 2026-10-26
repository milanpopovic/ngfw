"""Built-in UI texts of the framework itself (login page, header menu,
dialog buttons) in a few languages. App pages keep their own texts.

The language comes from `AppConfig.language` and is set once by
`ngfw.create_app`; `t(key)` returns the text in that language, falling
back to English for a missing key or an unknown language.
"""
from __future__ import annotations

TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "username": "Username",
        "password": "Password",
        "login": "Log in",
        "logout": "Logout",
        "invalid_login": "Invalid username or password",
        "dark_mode": "Dark mode",
        "menu": "Menu",
        "confirm_title": "Confirm",
        "yes": "Yes",
        "cancel": "Cancel",
        "notice_title": "Notice",
        "ok": "OK",
    },
    "sr": {
        "username": "Korisničko ime",
        "password": "Lozinka",
        "login": "Prijavi se",
        "logout": "Odjava",
        "invalid_login": "Pogrešno korisničko ime ili lozinka.",
        "dark_mode": "Tamni režim",
        "menu": "Meni",
        "confirm_title": "Potvrda",
        "yes": "Da",
        "cancel": "Otkaži",
        "notice_title": "Obaveštenje",
        "ok": "U redu",
    },
}

_language = "en"


def set_language(language: str) -> None:
    global _language
    _language = language if language in TEXTS else "en"


def get_language() -> str:
    return _language


def t(key: str) -> str:
    return TEXTS.get(_language, {}).get(key) or TEXTS["en"].get(key, key)
