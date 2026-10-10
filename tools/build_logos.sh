#!/bin/bash
# Regenera brand/logos y brand/favicon a partir del manual de marca (vectores de la pág. 7).
# Requiere: poppler (pdftocairo), Google Chrome, python3 + Pillow.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; T="$(mktemp -d)"
pdftocairo -svg -f 7 -l 7 "$ROOT/Assets/Manual de Marca TeFacturo (1).pdf" "$T/p7.svg" 2>/dev/null
python3 "$ROOT/tools/extract_logo_paths.py" "$T/p7.svg" "rgb(100%, 35.699463%, 1.599121%)" "$T/logo_" 15
# orden de clusters: 0 = isologotipo horizontal, 1 = isologotipo con bajada, 2 = isologo
names=(isologotipo-horizontal isologotipo-bajada isologo)
mkdir -p "$ROOT/brand/logos/svg" "$ROOT/brand/logos/png" "$ROOT/brand/favicon"
for i in 0 1 2; do for c in naranja:FF5B04 negro:010A0A blanco:FFFFFF; do
  sed "s/#FF5B04/#${c##*:}/" "$T/logo_$i.svg" > "$ROOT/brand/logos/svg/tefacturo-${names[$i]}-${c%%:*}.svg"
done; done
cd "$ROOT/brand/logos/svg"
for f in *.svg; do b=${f%.svg}; case $b in *isologo-*) W=1024;; *) W=2400;; esac; "$ROOT/tools/svg2png.sh" "$f" "../png/$b.png" $W; done
cd "$ROOT/brand/favicon"
for s in 32 180 512; do "$ROOT/tools/svg2png.sh" ../logos/svg/tefacturo-isologo-naranja.svg "$T/fav-$s.png" $s; done
T="$T" python3 - <<'PY'
import os
from PIL import Image
T=os.environ["T"]
for s,n in ((32,"favicon-32.png"),(180,"apple-touch-icon.png"),(512,"icon-512.png")):
    im=Image.open(f"{T}/fav-{s}.png").convert("RGBA"); W,H=im.size
    c=Image.new("RGBA",(max(W,H),)*2,(0,0,0,0)); c.paste(im,((c.width-W)//2,(c.height-H)//2)); c.resize((s,s),Image.LANCZOS).save(n)
PY
cp ../logos/svg/tefacturo-isologo-naranja.svg favicon.svg
