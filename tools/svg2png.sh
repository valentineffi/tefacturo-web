#!/bin/bash
# rast.sh in.svg out.png width  -> PNG transparente al ancho dado
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
in="$1"; out="$2"; W="$3"
vb=$(grep -o 'viewBox="[^"]*"' "$in" | head -1 | tr -d '"' | cut -d= -f2)
read x y w h <<< "$vb"
H=$(python3 -c "import math;print(math.ceil($W*$h/$w))")
tmp=$(mktemp -d)/p.html
printf '<html><body style="margin:0;background:transparent"><img src="file://%s" style="display:block;width:%spx;height:%spx"></body></html>' "$(cd "$(dirname "$in")";pwd)/$(basename "$in")" "$W" "$H" > "$tmp"
"$C" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files --default-background-color=00000000 --window-size=$W,$H --screenshot="$out" "file://$tmp" >/dev/null 2>&1
