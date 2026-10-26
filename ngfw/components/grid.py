"""AG Grid wrapper with sensible defaults, plus optional toggleable
column groups — the pattern from the Dunav app, where clicking a
section name (Dužnik, Adresa, Sud, ...) shows/hides that section's
columns.
"""
from __future__ import annotations

from nicegui import ui


def styled_aggrid(
    row_data: list[dict],
    column_defs: list[dict],
    *,
    groups: dict[str, list[str]] | None = None,
    height: str = "70vh",
    editable: bool = True,
    **aggrid_kwargs,
):
    """A `ui.aggrid` with sensible defaults.

    `groups` maps a toggle-button label to the list of column `field`
    names it controls, e.g.::

        styled_aggrid(rows, columns, groups={
            'Dužnik': ['name', 'jmbg'],
            'Adresa': ['street', 'city'],
        })

    Returns the `ui.aggrid` element. If `groups` is given, the toggle
    buttons are placed in a row above the grid (also returned as
    `grid.toggle_row` for further styling if needed).
    """
    if editable:
        for col in column_defs:
            col.setdefault("editable", True)

    toggle_row = None
    if groups:
        with ui.row().classes("gap-2 mb-2") as toggle_row:
            pass

    grid = ui.aggrid(
        {
            "columnDefs": column_defs,
            "rowData": row_data,
            "rowSelection": "multiple",
            "stopEditingWhenCellsLoseFocus": True,
            **aggrid_kwargs,
        }
    ).classes("w-full").style(f"height: {height}")

    if groups:
        visible = {group: True for group in groups}

        def make_toggle(group: str, btn: ui.button):
            def toggle() -> None:
                visible[group] = not visible[group]
                btn.props(f'color={"primary" if visible[group] else "grey-5"}')
                # AG Grid >= 31 merged columnApi into gridApi; setColumnsVisible
                # takes the *list* of column keys at once.
                grid.run_grid_method("setColumnsVisible", groups[group], visible[group])

            return toggle

        with toggle_row:
            for group in groups:
                btn = ui.button(group).props("dense color=primary")
                btn.on_click(make_toggle(group, btn))

    grid.toggle_row = toggle_row
    return grid
