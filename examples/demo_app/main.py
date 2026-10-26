"""Demo app showing ngfw's pieces wired together: multipage nav, a
protected page, auth (with one seeded user), the app shell/theme, and the
AG Grid + form components.

Run it with:

    cd examples/demo_app
    python main.py

Then open http://localhost:8080 and log in as demo / demo1234.
"""
from __future__ import annotations

import ngfw

from app_config import config

# Import the pages package so its @ngfw.page-decorated functions register
# themselves before ui.run starts serving requests.
import pages  # noqa: E402,F401


def _seed_demo_user() -> None:
    """Create the demo/demo1234 login the first time this runs, so the
    app is usable out of the box."""
    ngfw.auth.service.configure(config)
    if not ngfw.auth.user_exists("demo"):
        ngfw.auth.create_user("demo", "demo1234")


if __name__ in {"__main__", "__mp_main__"}:
    _seed_demo_user()
    ngfw.run_app(config)
