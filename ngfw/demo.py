"""ngfw demo — a small app built from ngfw's pieces: pages & menu, login, the app shell, AG Grid with column
groups, form components, a confirm dialog and the tree editor (ngfw.tree).

    ngfw-demo                           # after: pip install "git+https://github.com/milanpopovic/ngfw"
    ngfw-demo --port 8090 --data /tmp/ngfw-demo
    python -m ngfw.demo                 # the same

Open http://localhost:8080 and log in as demo / demo1234. The user file, the tree file and the session secret
are kept in --data (default ./ngfw-demo-data). The same app as source files: examples/demo_app/.
"""
from __future__ import annotations

import argparse
import secrets
from pathlib import Path

from nicegui import ui

from . import auth, components
from .app import run_app
from .config import AppConfig
from .pages.registry import page
from .shell import frame
from .tree import JsonFileStore, TreeEditor

ROWS = [
    {"name": "Petrović Marko", "jmbg": "0101990710015", "street": "Kneza Miloša 12", "city": "Beograd",
     "court": "Prvi osnovni sud", "cost": 12500},
    {"name": "Jovanović Ana", "jmbg": "1503985715020", "street": "Bulevar oslobođenja 5", "city": "Novi Sad",
     "court": "Osnovni sud NS", "cost": 8300},
]
COLUMNS = [
    {"field": "name", "headerName": "Ime i prezime"},
    {"field": "jmbg", "headerName": "JMBG"},
    {"field": "street", "headerName": "Ulica"},
    {"field": "city", "headerName": "Grad"},
    {"field": "court", "headerName": "Sud"},
    {"field": "cost", "headerName": "Troškovi", "type": "numericColumn"},
]
GROUPS = {"Dužnik": ["name", "jmbg"], "Adresa": ["street", "city"], "Sud": ["court"], "Troškovi": ["cost"]}

TREE = [
    {"label": "Company", "children": [
        {"label": "Sales", "children": [{"label": "North"}, {"label": "South"}]},
        {"label": "Development", "note": "Code: https://github.com/milanpopovic/ngfw",
         "children": [{"label": "Web"}, {"label": "Mobile"}]},
        {"label": "Accounting"},
    ]},
]


def build(data: Path) -> AppConfig:
    """Register the demo pages and return the app config; everything the demo writes goes into `data`."""
    data.mkdir(parents=True, exist_ok=True)
    secret_file = data / "storage_secret.txt"
    if not secret_file.exists():
        secret_file.write_text(secrets.token_urlsafe(32), encoding="utf-8")

    config = AppConfig(
        title="ngfw demo",
        subtitle="reference app",
        favicon="🧭",
        primary_color="#1976d2",
        storage_secret=secret_file.read_text(encoding="utf-8").strip(),
        users_file=data / "demo_users.json",
    )
    tree_file = data / "tree.json"
    if not tree_file.exists():
        from .tree import ops
        import json
        tree_file.write_text(json.dumps(ops.new_doc(TREE), ensure_ascii=False, indent=1), encoding="utf-8")
    tree_store = JsonFileStore(tree_file)

    @page("/", "Home", icon="home", requires_auth=False)
    def home_page() -> None:
        with frame(config, "/"):
            ui.label("Welcome to the ngfw demo").classes("text-2xl font-bold")
            ui.label("This page is public. Cases, Tree and Settings in the menu are behind the login: "
                     "demo / demo1234.").classes("text-grey-8")

    @page("/cases", "Cases", icon="table_chart", group="Data")
    def cases_page() -> None:
        with frame(config, "/cases"):
            ui.label("Cases").classes("text-2xl font-bold")
            ui.label("Click a section button to show/hide its columns.").classes("text-grey-8 mb-2")
            components.styled_aggrid(ROWS, COLUMNS, groups=GROUPS, height="50vh")

    @page("/tree", "Tree", icon="account_tree", group="Data")
    def tree_page() -> None:
        with frame(config, "/tree"):
            ui.label("Tree (ngfw.tree)").classes("text-2xl font-bold")
            ui.label("Hover a node for + ✎ 🗑 ⋮, drag a name onto another node. Open the page in a second "
                     "window: changes show up at once.").classes("text-grey-8 mb-2")
            TreeEditor(tree_store, language="en", filename="company")

    @page("/settings", "Settings", icon="settings", group="Account")
    def settings_page() -> None:
        with frame(config, "/settings"):
            ui.label("Settings").classes("text-2xl font-bold")
            ui.label(f"Logged in as {auth.current_user()}").classes("text-grey-8 mb-2")
            with components.form_card("Update display name"):
                name = components.labeled_input("Display name", validation={"Required": components.required()})

                async def save() -> None:
                    if name.validate():
                        ui.notify(f"Saved '{name.value}' (demo only, not persisted)", color="positive")

                ui.button("Save", on_click=save).props("color=primary")

            async def do_logout() -> None:
                if await components.confirm("Log out of the demo app?"):
                    auth.logout(config.login_path)

            ui.button("Log out", on_click=do_logout).props("outline color=negative").classes("mt-4")

    auth.service.configure(config)
    if not auth.user_exists("demo"):
        auth.create_user("demo", "demo1234")
    return config


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="ngfw-demo", description="ngfw demo app")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--data", default="ngfw-demo-data", help="folder for users, tree and secret (default: %(default)s)")
    a = p.parse_args(argv)
    config = build(Path(a.data))
    print(f"ngfw demo: http://localhost:{a.port}  — log in as demo / demo1234  (data: {Path(a.data).resolve()})")
    run_app(config, host=a.host, port=a.port, reload=False, show=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
