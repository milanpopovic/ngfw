"""Periodic zip backups of a data folder, driven by `AppConfig`. Wired up
automatically by `ngfw.create_app`/`run_app` when `config.backup_source_dir`
is set — nothing else to call yourself for the periodic part.

`make_backup(config)` is also exposed on its own so an app can trigger an
on-demand backup too (e.g. a "Backup now" button on an admin page).
"""
from __future__ import annotations

import asyncio
import zipfile
from datetime import datetime
from pathlib import Path

from nicegui import app as nicegui_app
from nicegui import background_tasks

from .config import AppConfig


def _default_backup_dir(source: Path) -> Path:
    return source.parent / "backups_zip"


def make_backup(config: AppConfig) -> Path:
    """Zip `config.backup_source_dir` into a timestamped `.zip` inside
    `config.backup_dir`, prune old archives per `config.backup_keep_count`,
    and return the path of the new archive.

    Raises `ValueError` if `backup_source_dir` isn't set, or if
    `backup_dir` resolves inside `backup_source_dir` (which would make
    the archive include itself on the next run).
    """
    if not config.backup_source_dir:
        raise ValueError("AppConfig.backup_source_dir isn't set — nothing to back up.")

    source = Path(config.backup_source_dir).resolve()
    dest_dir = Path(config.backup_dir).resolve() if config.backup_dir else _default_backup_dir(source)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if dest_dir == source or dest_dir in source.parents or source in dest_dir.parents:
        raise ValueError(
            f"backup_dir ({dest_dir}) can't be the same as, inside, or contain "
            f"backup_source_dir ({source}) — the archive would include itself next time."
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = dest_dir / f"{source.name}_{stamp}.zip"

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in source.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(source.parent))

    _prune_old_backups(dest_dir, source.name, config.backup_keep_count)
    return archive_path


def _prune_old_backups(dest_dir: Path, prefix: str, keep_count: int | None) -> None:
    if keep_count is None:
        return
    archives = sorted(dest_dir.glob(f"{prefix}_*.zip"), key=lambda p: p.stat().st_mtime)
    stale = archives[:-keep_count] if keep_count > 0 else archives
    for old_archive in stale:
        old_archive.unlink(missing_ok=True)


def start_periodic_backup(config: AppConfig) -> None:
    """Start the background loop that calls `make_backup` once at
    startup, then again every `config.backup_interval_seconds`. A no-op
    if `config.backup_source_dir` isn't set. Called automatically by
    `ngfw.create_app`.
    """
    if not config.backup_source_dir:
        return

    async def _loop() -> None:
        while True:
            try:
                path = make_backup(config)
                print(f"[ngfw.backup] wrote {path}")
            except Exception as exc:  # a bad backup should never crash the app
                print(f"[ngfw.backup] backup failed: {exc}")
            await asyncio.sleep(config.backup_interval_seconds)

    # background_tasks.create (rather than a bare asyncio.create_task) keeps
    # a reference to the task so it isn't garbage-collected mid-run.
    nicegui_app.on_startup(lambda: background_tasks.create(_loop(), name="ngfw-periodic-backup"))
