# ngfw — izmene po verzijama

Svaka promena koda u `ngfw/` dobija novu verziju (`__version__` u
`ngfw/__init__.py`) i stavku ovde; zatim `bash build.sh <aplikacije>`.
Brojevi: 0.3.**1** = ispravka, bez promene upotrebe; 0.**4**.0 = nešto novo
ili promena koja traži izmenu u aplikacijama.

## 0.3.0
- Pip paket (`pyproject.toml`, `build.sh`) umesto kopiranja `ngfw/` foldera u aplikacije.
- `ngfw.webdav`: uređivanje fajlova (Word šablona) direktno iz desktop Worda,
  stranica „Šabloni” (samo administratori). Zahteva extra `ngfw[webdav]`.

## 0.2.0
- Uloge i ograničeni korisnici (`restricted_roles`, `role_home`), dodatna polja korisnika.
- Srpski tekstovi (`language="sr"`, `ngfw.i18n`), dodaci u zaglavlju, kompaktan meni.
- Prijava sa starim (legacy) heš lozinkama, uz automatsku zamenu.
- `set_dirty` — upozorenje pri napuštanju stranice sa nesačuvanim izmenama.

## 0.1.0
- Stranice i meni (`@ngfw.page`), prijava i sesije, okvir aplikacije (`ngfw.frame`),
  tema, rezervne kopije (`ngfw.backup`), komponente (dijalozi, forme, tabela).
