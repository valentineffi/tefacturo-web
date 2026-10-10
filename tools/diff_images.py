#!/usr/bin/env python3
"""diff_images.py ref.png clone.png out.png [offset_ref]
Compara la referencia (recortando offset_ref px arriba: banner de Wix) con el clon.
Imprime % de píxeles distintos y franjas verticales con diferencias; guarda lado a lado con diferencias en rojo."""
import sys
from PIL import Image, ImageChops

ref, clone, out = sys.argv[1:4]
off = int(sys.argv[4]) if len(sys.argv) > 4 else 0
a = Image.open(ref).convert('RGB')
a = a.crop((0, off, a.width, a.height))
b = Image.open(clone).convert('RGB')
H = min(a.height, b.height)
a, b = a.crop((0, 0, a.width, H)), b.crop((0, 0, b.width, H))
d = ImageChops.difference(a, b).convert('L').point(lambda v: 255 if v > 24 else 0)
hist = d.histogram()
n = hist[255]
rows = []
px = d.load()
for y in range(H):
    if d.crop((0, y, d.width, y + 1)).getbbox():
        rows.append(y)
bands = []
for y in rows:
    if bands and y - bands[-1][1] <= 12:
        bands[-1][1] = y
    else:
        bands.append([y, y])
ov = b.copy()
ov.paste(Image.new('RGB', b.size, (255, 0, 0)), mask=d)
sb = Image.new('RGB', (a.width * 2 + 10, H), (128, 128, 128))
sb.paste(a, (0, 0)); sb.paste(ov, (a.width + 10, 0))
sb.save(out)
print('ref_h=%d clone_h=%d diff=%.3f%% bands=%s' % (a.height + off, b.height, 100.0 * n / (a.width * H), bands[:25]))
