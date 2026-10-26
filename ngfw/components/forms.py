"""Small form helpers: a labeled input, a form-shaped card, and a couple
of ready-made validators."""
from __future__ import annotations

from typing import Callable

from nicegui import ui


def labeled_input(label: str, *, validation: dict[str, Callable] | None = None, **kwargs) -> ui.input:
    """An input with its label rendered above it (rather than as a
    floating placeholder), matching a denser form layout."""
    with ui.column().classes("gap-0 w-full"):
        ui.label(label).classes("text-xs text-grey-7")
        field = ui.input(**kwargs).classes("w-full")
        if validation:
            field.validation = validation
    return field


def form_card(title: str | None = None) -> ui.card:
    """A `ui.card` pre-sized and spaced for a form. Use as a context
    manager::

        with ngfw.components.form_card('New user'):
            ngfw.components.labeled_input('Username')
    """
    card = ui.card().classes("w-full max-w-md gap-2 p-4")
    if title:
        with card:
            ui.label(title).classes("text-lg font-semibold mb-2")
    return card


def required(message: str = "Required") -> Callable[[object], bool | str]:
    return lambda v: (v is not None and str(v).strip() != "") or message


def min_length(n: int, message: str | None = None) -> Callable[[object], bool | str]:
    return lambda v: (v is not None and len(str(v)) >= n) or (message or f"Minimum {n} characters")
