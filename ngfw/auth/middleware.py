"""Starlette middleware that guards every page registered with
`@ngfw.page`: anonymous visitors go to the login page, logged-in users who
may not open a page (admin-only page, page limited to other roles, or a
restricted role such as "portal" outside its own pages) go to their home
page. The rules live in `ngfw.auth.can_access`.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from nicegui import app

from ..config import AppConfig
from ..pages.registry import NAV_ITEMS
from . import service


def build_auth_middleware(config: AppConfig):
    class AuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            path = request.url.path
            item = next((i for i in NAV_ITEMS if i.path == path), None)
            if item is None or not item.requires_auth:
                return await call_next(request)

            if not service.current_user():
                app.storage.user["referrer_path"] = path
                return RedirectResponse(config.login_path)

            if not service.can_access(item):
                home = service.home_path()
                if home == path:  # nowhere better to send them -> log out
                    app.storage.user.clear()
                    return RedirectResponse(config.login_path)
                return RedirectResponse(home)

            return await call_next(request)

    return AuthMiddleware
