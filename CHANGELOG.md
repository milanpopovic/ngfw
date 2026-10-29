# ngfw — izmene po verzijama

Svaka promena koda u `ngfw/` dobija novu verziju (`__version__` u
`ngfw/__init__.py`) i stavku ovde; zatim `bash build.sh <aplikacije>`.
Brojevi: 0.3.**1** = ispravka, bez promene upotrebe; 0.**4**.0 = nešto novo
ili promena koja traži izmenu u aplikacijama.

## 0.4.1
- Primer se pokreće direktno sa GitHub-a: komanda `ngfw-demo` (`ngfw/demo.py`: početna, tabela, stablo,
  podešavanja, prijava demo / demo1234; `--port`, `--data`) i dugme „Open in GitHub Codespaces” (`.devcontainer/`).
- `ngfw.tree` = ngtree 0.1.1 (i `ngfw.tree.demo`). Aplikacije ne moraju ništa da menjaju.

## 0.4.0
- `ngfw.tree` — `TreeEditor`, stablo koje se menja direktno u prikazu, kao NiceGUI element za bilo koju
  stranicu (iz aplikacije stabla); `JsonFileStore` / `MemoryStore` / sopstveni `TreeStore`; takođe kao
  `ngfw.components.TreeEditor`. Isti kod kao paket `ngtree` 0.1.0 (izvor:
  https://github.com/milanpopovic/ngtree, `bash build.sh --ngfw`). Postojeće aplikacije ne moraju ništa da menjaju.
- `build.sh` čita aplikacije iz `apps.local` (nije u git-u).

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
