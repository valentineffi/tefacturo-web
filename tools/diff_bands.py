#!/usr/bin/env python3
"""diff_bands.py ref.png clone.png out.png offset y0:y1 [y0:y1 ...]  -> recortes ref|clon|diff de cada franja."""
import sys
from PIL import Image, ImageChops
ref, clone, out, off = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
a = Image.open(ref).convert('RGB'); b = Image.open(clone).convert('RGB')
W = a.width; rows = []
for spec in sys.argv[5:]:
    y0, y1 = map(int, spec.split(':')); y0 = max(0, y0 - 15); y1 += 15
    ca = a.crop((0, y0 + off, W, y1 + off)); cb = b.crop((0, y0, W, y1))
    d = ImageChops.difference(ca, cb).point(lambda v: min(255, v * 4))
    row = Image.new('RGB', (W * 3 + 20, y1 - y0), (255, 0, 255))
    row.paste(ca, (0, 0)); row.paste(cb, (W + 10, 0)); row.paste(d, (2 * W + 20, 0)); rows.append(row)
H = sum(r.height + 6 for r in rows)
sheet = Image.new('RGB', (W * 3 + 20, H), (255, 0, 255)); y = 0
for r in rows: sheet.paste(r, (0, y)); y += r.height + 6
sheet.save(out)
