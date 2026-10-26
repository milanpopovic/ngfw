#!/usr/bin/env bash
# Pravi ngfw wheel i (po želji) ga ubacuje u aplikacije.
#
#   bash build.sh               samo napravi dist/ngfw-<verzija>-py3-none-any.whl
#   bash build.sh app1 app2     + kopira wheel u <aplikacija>/wheels/ i upiše ga u requirements.txt
#
# Aplikacije su u apps.local (nije u git-u): jedna po redu, "ime  putanja", npr. "jkp ~/projects/jkp".
#
# Pravilo: svaka promena ngfw koda = nova verzija (__version__ u ngfw/__init__.py
# + stavka u CHANGELOG.md). Skripta odbija da istu verziju sa drugačijim kodom
# ubaci u aplikaciju — pip bi je na serveru smatrao već instaliranom.
#
# Posle ubacivanja, u aplikaciji: pip install -r requirements.txt, testovi, deploy.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
declare -A APPS=()
if [[ -f apps.local ]]; then
  while read -r name path _; do
    [[ -z ${name:-} || $name == \#* ]] && continue
    APPS[$name]="${path/#\~/$HOME}"
  done < apps.local
fi

VER=$(python3 -c 'import re;print(re.search(r"__version__ = \"(.+?)\"", open("ngfw/__init__.py").read())[1])')
grep -q "^## $VER" CHANGELOG.md || { echo "✘ CHANGELOG.md nema stavku „## $VER” — dopišite šta je novo." >&2; exit 1; }

rm -rf dist build ./*.egg-info
python3 -m pip wheel --quiet --no-deps --wheel-dir dist . >/dev/null
WHL=dist/ngfw-$VER-py3-none-any.whl
[[ -f $WHL ]] || { echo "✘ Wheel nije napravljen." >&2; exit 1; }
rm -rf build ./*.egg-info
echo "✔ $WHL"

# isti sadržaj? (RECORD sadrži sha256 svakog fajla; datumi u zip-u se ne gledaju)
isti_kod() {
  python3 - "$1" "$2" <<'PY'
import sys, zipfile
def h(p):
    with zipfile.ZipFile(p) as z:
        rec = next(n for n in z.namelist() if n.endswith("RECORD"))
        return sorted(l for l in z.read(rec).decode().splitlines() if l and not l.split(",")[0].endswith("RECORD"))
sys.exit(0 if h(sys.argv[1]) == h(sys.argv[2]) else 1)
PY
}

for app in "$@"; do
  dir=${APPS[$app]:-}
  [[ -n $dir && -d $dir ]] || { echo "✘ Nepoznata aplikacija: $app (poznate iz apps.local: ${!APPS[*]})" >&2; exit 1; }
  dest="$dir/wheels/$(basename "$WHL")"
  if [[ -f $dest ]] && ! isti_kod "$WHL" "$dest"; then
    echo "✘ $app već ima ngfw $VER sa DRUGAČIJIM kodom — povećajte verziju u ngfw/__init__.py." >&2; exit 1
  fi
  mkdir -p "$dir/wheels"
  find "$dir/wheels" -name 'ngfw-*.whl' ! -name "$(basename "$WHL")" -delete
  cp "$WHL" "$dest"
  if grep -q '^\./wheels/ngfw-.*\.whl' "$dir/requirements.txt"; then
    sed -i "s|^\./wheels/ngfw-.*\.whl.*|./wheels/$(basename "$WHL")|" "$dir/requirements.txt"
  else
    printf '\n# ngfw — naš framework, verzija iz ngfw repozitorijuma (bash build.sh %s)\n./wheels/%s\n' "$app" "$(basename "$WHL")" >> "$dir/requirements.txt"
  fi
  echo "✔ $app: wheels/$(basename "$WHL") + requirements.txt"
done
