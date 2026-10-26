"""A protected page showing the AG Grid component with toggleable
column groups, in the spirit of the Dunav app."""
from nicegui import ui

import ngfw
from ngfw import components
from app_config import config

ROWS = [
    {"name": "Petrović Marko", "jmbg": "0101990710015", "street": "Kneza Miloša 12", "city": "Beograd", "court": "Prvi osnovni sud", "cost": 12500},
    {"name": "Jovanović Ana", "jmbg": "1503985715020", "street": "Bulevar oslobođenja 5", "city": "Novi Sad", "court": "Osnovni sud NS", "cost": 8300},
]

COLUMNS = [
    {"field": "name", "headerName": "Ime i prezime"},
    {"field": "jmbg", "headerName": "JMBG"},
    {"field": "street", "headerName": "Ulica"},
    {"field": "city", "headerName": "Grad"},
    {"field": "court", "headerName": "Sud"},
    {"field": "cost", "headerName": "Troškovi", "type": "numericColumn"},
]

GROUPS = {
    "Dužnik": ["name", "jmbg"],
    "Adresa": ["street", "city"],
    "Sud": ["court"],
    "Troškovi": ["cost"],
}


@ngfw.page("/cases", "Cases", icon="table_chart", group="Data")
def cases_page() -> None:
    with ngfw.frame(config, "/cases"):
        ui.label("Cases").classes("text-2xl font-bold")
        ui.label("Click a section button to show/hide its columns.").classes("text-grey-8 mb-2")
        components.styled_aggrid(ROWS, COLUMNS, groups=GROUPS, height="50vh")
