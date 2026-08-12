#!/usr/bin/env python3
"""PR17 probe: locate all production footprints and report geometric bounds.

Runs in the pinned KiCad 10.0.5 container. No repo files are modified.
"""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
KICAD_STD=Path('/usr/share/kicad/footprints')
LOCAL=ROOT/'kicad/lib/nfb_footprints.pretty'
FILES=[ROOT/'hardware/z1_production_netlist.json',ROOT/'hardware/z2_production_netlist.json',ROOT/'hardware/power_production_netlist.json',ROOT/'hardware/z4_production_netlist.json']

def locate(fid:str)->Path:
    lib,name=fid.split(':',1)
    if lib=='NFB': p=LOCAL/(name+'.kicad_mod')
    else: p=KICAD_STD/(lib+'.pretty')/(name+'.kicad_mod')
    if not p.exists(): raise FileNotFoundError(f'{fid} -> {p}')
    return p

def nums(s): return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',s)]
def bbox(text:str):
    pts=[]
    # courtyard lines/rectangles/arcs first
    for m in re.finditer(r'\(fp_line\s+\(start\s+([-.0-9]+)\s+([-.0-9]+)\)\s+\(end\s+([-.0-9]+)\s+([-.0-9]+)\).*?\(layer\s+"?F\.CrtYd"?\)',text,re.S):
        pts += [(float(m.group(1)),float(m.group(2))),(float(m.group(3)),float(m.group(4)))]
    for m in re.finditer(r'\(fp_rect\s+\(start\s+([-.0-9]+)\s+([-.0-9]+)\)\s+\(end\s+([-.0-9]+)\s+([-.0-9]+)\).*?\(layer\s+"?F\.CrtYd"?\)',text,re.S):
        pts += [(float(m.group(1)),float(m.group(2))),(float(m.group(3)),float(m.group(4)))]
    if not pts:
        # fallback pads
        for m in re.finditer(r'\(pad\s+"[^"]*"[^\n]*?\(at\s+([-.0-9]+)\s+([-.0-9]+)(?:\s+[-.0-9]+)?\).*?\(size\s+([-.0-9]+)\s+([-.0-9]+)\)',text,re.S):
            x,y,sx,sy=map(float,m.groups()); pts += [(x-sx/2,y-sy/2),(x+sx/2,y+sy/2)]
    if not pts: return None
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    return min(xs),min(ys),max(xs),max(ys)

def main():
    refs={}
    for f in FILES:
        d=json.loads(f.read_text(encoding='utf-8'))
        for c in d['components']:
            refs[c['ref']]=c['footprint']
    missing=[]
    for ref,fid in sorted(refs.items()):
        try:
            p=locate(fid); b=bbox(p.read_text(encoding='utf-8',errors='replace'))
            if b: w=b[2]-b[0]; h=b[3]-b[1]
            else: w=h=float('nan')
            print(f'{ref:24s} {fid:100s} bbox={b} wh=({w:.3f},{h:.3f}) path={p}')
        except Exception as e:
            missing.append((ref,fid,str(e))); print('MISSING',ref,fid,e)
    print(f'REFS={len(refs)} UNIQUE_FOOTPRINTS={len(set(refs.values()))} MISSING={len(missing)}')
    if missing: raise SystemExit(2)
if __name__=='__main__': main()
