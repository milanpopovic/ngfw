"""Confirm/alert dialog helpers, so call sites don't re-build a
ui.dialog + ui.card every time they need a yes/no prompt."""
from __future__ import annotations

from nicegui import ui

from ..i18n import t


async def confirm(
    message: str,
    *,
    title: str | None = None,
    ok_text: str | None = None,
    cancel_text: str | None = None,
) -> bool:
    """Await this to show a confirm dialog and get True/False back::

        if await ngfw.components.confirm('Delete this record?'):
            ...
    """
    title, ok_text, cancel_text = title or t("confirm_title"), ok_text or t("yes"), cancel_text or t("cancel")
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes("text-lg font-semibold")
        ui.label(message)
        with ui.row().classes("justify-end w-full gap-2 mt-4"):
            ui.button(cancel_text, on_click=lambda: dialog.submit(False)).props("flat")
            ui.button(ok_text, on_click=lambda: dialog.submit(True)).props("color=primary")
    result = await dialog
    return bool(result)


def alert(message: str, *, title: str | None = None, ok_text: str | None = None) -> None:
    """Show a one-button informational dialog."""
    title, ok_text = title or t("notice_title"), ok_text or t("ok")
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes("text-lg font-semibold")
        ui.label(message)
        ui.button(ok_text, on_click=dialog.close).classes("mt-4")
    dialog.open()
