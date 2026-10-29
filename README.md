# ngfw (0.4.0)

A reusable NiceGUI application framework: multipage routing + nav, auth &
sessions, an app shell with theming, and a handful of shared UI
components — so a new app starts from a working skeleton instead of a
blank `main.py`.

## Install

ngfw is a pip package with a version number (it is not on PyPI). Each app keeps the exact wheel it uses in
its own `wheels/` folder and lists it in `requirements.txt` (`./wheels/ngfw-0.4.0-py3-none-any.whl`), so a
server installs exactly that version — never something named „ngfw” from PyPI.

```bash
# straight from GitHub (a tagged version):
pip install "ngfw @ git+https://github.com/milanpopovic/ngfw@v0.4.0"

# or a wheel: download it from the GitHub release, or build it yourself —
# edit ngfw/, raise __version__ in ngfw/__init__.py, add a CHANGELOG.md entry, then
bash build.sh myapp otherapp     # dist/ngfw-<version>.whl -> <app>/wheels + requirements.txt
```

`build.sh` reads the apps it knows from `apps.local` (not in git): one app per line, `name  path`
(`~` allowed), e.g. `myapp ~/projects/myapp`. Without arguments it only builds the wheel.

While working on ngfw itself, install it in editable mode into the Python you run the app with, so
changes show up without rebuilding: `venv/bin/python -m pip install -e path/to/ngfw` (undo:
`venv/bin/python -m pip install --force-reinstall -r requirements.txt` in the app).

Always `venv/bin/python -m pip`, not `venv/bin/pip`: after a venv folder is moved, `venv/bin/pip` still
installs into the OLD location.

Optional extra for `ngfw.webdav` (editing Word templates from desktop Word):
`ngfw[webdav]` = wsgidav, a2wsgi, docxtpl — the apps list these in their own requirements.

### Versions

Every version is a git tag (`v0.3.0`, `v0.4.0`, …) with its wheel attached to the GitHub release; what changed is in `CHANGELOG.md`.

## Quickstart

```python
# app_config.py
import ngfw

config = ngfw.AppConfig(
    title="My App",
    storage_secret="change-me",  # required — sign/encrypt session storage
)
```

```python
# pages/home.py
from nicegui import ui
import ngfw
from app_config import config

@ngfw.page('/', 'Home', icon='home', requires_auth=False)
def home_page():
    with ngfw.frame(config, '/'):
        ui.label('Hello, world')
```

```python
# main.py
import ngfw
from app_config import config
import pages  # noqa: F401  (imports register the @ngfw.page functions)

if __name__ in {"__main__", "__mp_main__"}:
    ngfw.run_app(config)
```

Layout: `app_config.py`, `main.py` and `pages/` sit next to each other in
the app's root folder; ngfw itself is installed from `wheels/` (never a
copied `ngfw/` folder — main.py warns if one is left). Run with `python
main.py`. See `examples/demo_app` for a complete, runnable version with
auth, a protected page, and the AG Grid component.

## What's included

### Multipage (`ngfw.page`, `ngfw.frame`)

`@ngfw.page(path, label, icon=..., group=..., requires_auth=True,
requires_admin=False, show_in_nav=True, order=0)` combines NiceGUI's
`@ui.page` with registration in a central nav list — add a page, and its
sidebar entry appears automatically, grouped and ordered however you
like. `ngfw.frame(config, current_path)` is the context manager that
renders the header/sidebar/footer shell around a page's content and
highlights the active nav item.

### Auth & sessions (`ngfw.auth`)

- `ngfw.auth.login(username, password)` / `ngfw.auth.logout()` /
  `ngfw.auth.current_user()`
- `ngfw.auth.create_user(username, password, is_admin=None)` /
  `ngfw.auth.user_exists(...)` / `ngfw.auth.list_users()`
- `ngfw.auth.is_admin(username=None)` (defaults to the current user) /
  `ngfw.auth.set_admin(username, True/False)` / `ngfw.auth.admin_count()`
  — a simple admin-vs-regular-user role, see "Roles" below.
- Passwords are bcrypt-hashed. The default store is a JSON file
  (`AppConfig.users_file`); swap in your own by implementing the
  `ngfw.auth.UserStore` protocol (e.g. SQLModel/asyncpg) and passing it to
  `ngfw.auth.configure(config, store=MyStore())` before `run_app`.
- Pages registered with `requires_auth=True` (the default) redirect
  anonymous visitors to `config.login_path` (`/login` by default); a
  built-in login page is installed automatically.

### Roles (`is_admin`)

There's one built-in role — `is_admin`, a boolean per user — deliberately
kept simple rather than a full permissions system:

- Mark a page admin-only with `@ngfw.page(..., requires_admin=True)`. The
  auth middleware sends non-admins to their home page
  (`ngfw.auth.home_path()`: `AppConfig.role_home[role]`, else
  `config.after_login_path`), and the sidebar hides that entry from
  non-admins entirely rather than showing a link that 403s.
- `ngfw.auth.create_user(username, password, is_admin=True)` sets the
  flag when creating (or password-resetting) a user; leaving `is_admin`
  as `None` (the default) preserves whatever that user already had.
  `ngfw.auth.set_admin(username, False)` demotes — it refuses to demote
  the *last* remaining admin, so you can't lock yourself out of every
  admin-only page by accident.
- The Settings template (below) only shows its "Users" section — the
  list of accounts, add-user form, and admin toggle per user — to
  admins; the self-service password form above it stays open to anyone
  logged in.
- **Bootstrapping the first admin**: a freshly-created user (or one that
  predates this feature) is non-admin by default, and there's no UI path
  to promote yourself from nothing — you need at least one admin already
  to grant that. Use whatever setup script your app has (e.g.
  `scripts/create_user.py` in Dunav) to create/promote the first admin
  from the command line, then manage the rest from the Settings page.
- For more than admin vs. regular user (e.g. an external "portal" user
  who may see only one page), use roles — see the next section.

### Roles, restricted users and app fields (ngfw 0.2)

Besides `is_admin`, a user record can carry any app-defined fields
(`ngfw.auth.get_user_field` / `set_user_field`), and a `role`
(`get_role` / `set_role`; default `"user"`).

```python
config = ngfw.AppConfig(
    ...,
    restricted_roles={"portal"},          # these users see ONLY their own pages
    role_home={"portal": "/portal"},      # where they land after login
)

@ngfw.page("/portal", "Portal", icon="dashboard", roles={"portal"})
def portal_page(): ...
```

Rules (`ngfw.auth.can_access`, used by the middleware and the sidebar):
public pages are open to everyone; otherwise the user must be logged in;
`requires_admin` pages need an admin; a role in `restricted_roles` may open
only pages that list it in `roles`; everyone else may open pages without
`roles`, pages listing their role, and admins every page. A user who
opens a page they can't access is sent to their `role_home` page.

Other additions: `delete_user` (refuses the last admin), `import_user`
(add a user with an existing hash + fields, for moving users between
apps), and **legacy password hashes** — an unsalted SHA-256 hex digest is
accepted at login and re-saved as bcrypt on the spot.

### Language (`AppConfig.language`, `ngfw.i18n`)

`language="sr"` switches the framework's own texts (login page, logout,
dark-mode tooltip, `confirm`/`alert` buttons) to Serbian. Default `"en"`.

### Header extras (`AppConfig.header_extra`)

A function called inside the header's right-hand row on every page, e.g.
to show a client selector: `header_extra=lambda: ui.select(...)`.

### Unsaved-changes guard (`ngfw.set_dirty`)

`ngfw.set_dirty(True)` makes the browser warn before closing/reloading the
page; `ngfw.set_dirty(False)` turns it off (e.g. after saving).

### App shell & theming

`ngfw.frame` renders a header (title, dark-mode toggle, user menu with
logout), a left drawer built from the nav registry (grouped, with
icons), and a footer — all driven by `AppConfig` (colors, title,
show/hide any of the three regions). The sidebar is compact (2px between
items, `py-1.5` per item) so a menu of ~15 entries fits without scrolling
on a 768px-high screen. Dark mode is remembered per browser
session via `app.storage.user`.

Page content sits in a centered column capped at `AppConfig.content_max_width`
(default `"max-w-6xl"`, ~1152px) so text-heavy pages don't stretch edge to
edge on a wide monitor. A page that wants more room — a wide data grid
that already scrolls horizontally, say — can opt out per-page instead of
changing it for the whole app: `ngfw.frame(config, path,
max_width="max-w-full")`.

### Periodic backups (`ngfw.backup`)

Zips a folder on a timer — e.g. an app's `data/` directory — and prunes
old archives so it doesn't grow forever. Off by default; turn it on by
setting `AppConfig.backup_source_dir`:

```python
config = ngfw.AppConfig(
    ...,
    backup_source_dir=DATA_DIR,                 # the folder to zip
    backup_dir=BASE_DIR / "backups_zip",         # where zips go (must not be inside backup_source_dir)
    backup_interval_seconds=24 * 60 * 60,        # daily; 3600 = hourly, 7*24*60*60 = weekly
    backup_keep_count=30,                        # keep the last 30, prune older ones; None = keep all
)
```

`ngfw.run_app`/`create_app` then starts a background loop automatically —
one backup right at startup, then one every `backup_interval_seconds`,
each as `<folder-name>_<timestamp>.zip`. A failed backup is logged to the
console and never crashes the app. Nothing else needs wiring, but
`ngfw.backup.make_backup(config)` is also callable directly if you want
an on-demand "Backup now" button somewhere (e.g. an admin-only spot on
the Settings page) in addition to the periodic one.

`backup_dir` must not be the same as, inside, or contain
`backup_source_dir` — otherwise each new zip would include the previous
zips and grow without bound; `make_backup` raises `ValueError` if you
get that wrong. Left as `None`, it defaults to a `backups_zip` folder
next to `backup_source_dir`.

### Editing Word files from the server (`ngfw.webdav`, 0.3)

Admins open a file in desktop Word straight from the server and save it
back with Ctrl+S — no download/upload. Handy for docxtpl templates.

```python
config = ngfw.AppConfig(
    ...,
    webdav_folders={"sabloni": DATA / "TEMPLATES"},   # {"name": folder}; empty = off
)
# after the pages are imported:
ngfw.webdav.register_page(config, "/sabloni", "Šabloni", group="Nalog")
```

- Each folder is shared over WebDAV at `/dav/<name>/` (`AppConfig.webdav_path`),
  served by wsgidav mounted inside the NiceGUI app — same port, same process.
- Word logs in with the app's own username and password; **only admins** are
  accepted. Non-admins and `portal` users get 401 (and the page is admin-only).
- `register_page` adds an admin-only page listing the Word files of every
  folder with **Uredi u Wordu** (an `ms-word:ofe|u|https://…` link),
  **Preuzmi**, and **Proveri** — lists the `{{ placeholders }}` and reports a
  broken `{{ … }}` / `{% … %}` before documents are generated with it.
- `labels={"racuni": "Računi"}` gives folders nicer titles on that page.

Requirements:

- `pip install wsgidav a2wsgi` (only for apps that set `webdav_folders`).
- **HTTPS.** Word sends the password only over HTTPS, so users must open the
  app through `https://…` (e.g. nginx with a certificate in front of the app).
  In that nginx `location`, raise the upload limit — the default 1 MB is
  smaller than many .docx files:

  ```nginx
  client_max_body_size 50m;
  ```

  nginx passes WebDAV methods (PROPFIND, LOCK, PUT, …) through `proxy_pass`
  without extra settings.
- Desktop Word (Windows or Mac) on the computer that edits. On Ubuntu the
  same `ms-word:` link opens the file in LibreOffice, which also saves back
  over WebDAV — choose the Word (.docx) format when it asks, and run
  **Proveri** after editing (LibreOffice re-saves the whole file and can
  split a `{{ field }}`).

Locks (so two people can't edit the same file at once) are kept in memory and
cleared on restart. The daily `ngfw.backup` zip of the data folder includes
the templates, so an earlier version can be restored from there.

### Tree editor (`ngfw.tree`, 0.4)

A tree you edit right in the tree view, as one element for any page — the editor from the *stabla* app:
add / edit / delete / drag / up-down / sort, notes with clickable links, branch tags, filter, undo,
import/export (.txt paths or JSON, whole tree or a subtree), view-only mode, Serbian/English.

```python
from ngfw.tree import TreeEditor, JsonFileStore, MemoryStore

ORG = JsonFileStore(DATA / 'organizacija.json')        # one file per tree; created if missing

@ngfw.page('/org', 'Organizacija', icon='account_tree')
def org_page():
    with ngfw.frame(config, '/org'):
        TreeEditor(ORG, editable=lambda doc: ngfw.auth.is_admin(), language='sr', filename='organizacija')

# your own data: you save it
TreeEditor(MemoryStore(nodes, on_change=save_to_db), features={'add', 'edit', 'delete', 'drag'},
           on_select=lambda node: show_details(node))
```

- **Stores:** `JsonFileStore(path)` — atomic writes, a backup before every change (undo walks back through
  them), live updates in every browser showing the same file; `MemoryStore(nodes, on_change=...)` — your data
  (database, app.storage…), undo in memory; subclass `TreeStore` (`_read`, `_write`) for anything else.
- **Rights:** `editable` is a bool or `(doc) -> bool`, checked again before every change; `can_view(doc)`.
- **Options:** `features` (`add edit delete move drag sort notes tags import export undo filter`), `language`,
  `texts` (replace any text), `on_change`, `on_select`, `menu_extra` (your items in the ⋮ menu), `filename`,
  `show_stats`, `hint`, `help_url`, `expand`.
- `ngfw.tree.ops` — the same operations without UI (scripts, imports, tests).
- Also available as `ngfw.components.TreeEditor`. The same code is the standalone package
  [ngtree](https://github.com/milanpopovic/ngtree) (for apps without ngfw) — the source lives there and its
  `build.sh --ngfw` copies it here. Full reference: the ngtree README.

### UI components (`ngfw.components`)

- `styled_aggrid(rows, columns, groups=...)` — an AG Grid with sane
  defaults and optional toggle buttons that show/hide groups of columns
  (the pattern from the Dunav app: click "Dužnik" to hide/show that
  section's fields).
- `labeled_input`, `form_card`, `required`, `min_length` — small form
  building blocks.
- `confirm(message)` (awaitable, returns bool), `alert(message)`.

### Starter page templates (`templates/`)

Not imported — these are copy-and-adapt starting points, same spirit as
the framework itself:

- `templates/settings_page.py` — a ready-made Settings page: shows the
  logged-in user, a self-service change-password form (open to anyone
  logged in), and — admins only — a "Backup now" button (only shown if
  `AppConfig.backup_source_dir` is set) and a users list with an add-user
  form and a per-user admin toggle. Copy it into your app's `pages/`
  folder, adjust the import at the top to match your `app_config`
  module, and register it (it already carries its own `@ngfw.page`).

## Notes / things to change per app

- **`storage_secret`** — set a real secret (e.g. from an environment
  variable), not the default placeholder.
- **`host`** — behind nginx on the same server, set `host="127.0.0.1"` so the
  app is reachable only through nginx/HTTPS, not directly over plain HTTP
  (`0.0.0.0`, the default, listens on every interface).
- **AG Grid column API** — `styled_aggrid`'s column-group toggling calls
  `grid.run_grid_method('setColumnsVisible', [...fields], visible)`,
  matching AG Grid >= 31 (columnApi merged into gridApi). If you're
  pinned to an older NiceGUI/AG Grid version that still needs
  `columnApi.setColumnVisible`, adjust `ngfw/components/grid.py`
  accordingly here, then a new version + `bash build.sh ...`.
- **SQL-backed auth** — if an app needs Postgres-backed users instead of
  the JSON file (matching the SQLModel/asyncpg pattern from earlier
  projects), implement `ngfw.auth.UserStore` and pass it to
  `ngfw.auth.configure`.
- **Roles** — `is_admin` plus one `role` per user and `roles=` on pages
  (see "Roles, restricted users and app fields"). That covers page-level
  access; it is not a per-action permissions system — check
  `ngfw.auth.get_role()` / `is_admin()` inside a page for finer rules.
