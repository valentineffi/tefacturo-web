#!/usr/bin/env python3
# Extrae paths de un color del SVG de pdftocairo, agrupa por proximidad, y escribe un SVG por grupo.
import sys,re,xml.etree.ElementTree as ET
src,color,outprefix=sys.argv[1],sys.argv[2],sys.argv[3]; gap=float(sys.argv[4]) if len(sys.argv)>4 else 12
ns='{http://www.w3.org/2000/svg}'
root=ET.parse(src).getroot()
paths=[]
for el in root.iter(ns+'path'):
    if el.get('fill','').replace(' ','')!=color.replace(' ',''): continue
    d=el.get('d'); nums=list(map(float,re.findall(r'-?\d+\.?\d*',d)))
    xs=nums[0::2]; ys=nums[1::2]
    paths.append([min(xs),min(ys),max(xs),max(ys),d])
# cluster
groups=[]
for p in paths:
    merged=[g for g in groups if not (p[0]>g["b"][2]+gap*5 or p[2]<g["b"][0]-gap*5 or p[1]>g['b'][3]+gap or p[3]<g['b'][1]-gap)]
    ng={'b':p[:4],'d':[p[4]]}
    for g in merged:
        groups.remove(g); ng['d']+=g['d']; b=g['b']; ng['b']=[min(ng['b'][0],b[0]),min(ng['b'][1],b[1]),max(ng['b'][2],b[2]),max(ng['b'][3],b[3])]
    groups.append(ng)
# re-merge pass
changed=True
while changed:
    changed=False
    for i in range(len(groups)):
        for j in range(i+1,len(groups)):
            a,b=groups[i]['b'],groups[j]['b']
            if not (a[0]>b[2]+gap*5 or a[2]<b[0]-gap*5 or a[1]>b[3]+gap or a[3]<b[1]-gap):
                groups[i]['d']+=groups[j]['d']; groups[i]['b']=[min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3])]; del groups[j]; changed=True; break
        if changed: break
groups.sort(key=lambda g:(round(g['b'][1]/50),g['b'][0]))
for i,g in enumerate(groups):
    x0,y0,x1,y1=g['b']; w,h=x1-x0,y1-y0
    print(i,len(g['d']),'paths',round(x0),round(y0),'size',round(w,1),'x',round(h,1))
    body=''.join(f'<path d="{d}"/>' for d in g['d'])
    open(f'{outprefix}{i}.svg','w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.3f} {y0:.3f} {w:.3f} {h:.3f}" width="{w:.2f}" height="{h:.2f}"><g fill="#FF5B04">{body}</g></svg>')
