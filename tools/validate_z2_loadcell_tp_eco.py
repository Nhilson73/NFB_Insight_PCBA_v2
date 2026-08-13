#!/usr/bin/env python3
"""Valida que PR24 mueva únicamente TP_LOAD_A_POS/NEG sobre base PR22."""
from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'hardware'/'placement_manifest.json'
ECO=ROOT/'hardware'/'z2_loadcell_tp_placement_eco.json'
TOL=1e-3

def fail(m): raise SystemExit('ERROR: '+m)
def near(a,b): return abs(float(a)-float(b))<=TOL

def main():
    if len(sys.argv)!=2: fail('uso: validate_z2_loadcell_tp_eco.py <base_pr22.json>')
    base=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    now=json.loads(MANIFEST.read_text(encoding='utf-8'))
    eco=json.loads(ECO.read_text(encoding='utf-8'))
    if base.get('eco_revision')!=1 or now.get('eco_revision')!=2: fail('revisiones ECO inesperadas')
    if base['board']!=now['board'] or base['zone_bounds_mm']!=now['zone_bounds_mm']: fail('board/zonas cambiaron')
    b={p['ref']:p for p in base['placements']}; n={p['ref']:p for p in now['placements']}
    if set(b)!=set(n) or len(n)!=119: fail('refs cambiaron')
    expected=set(eco['scope']['moved_refs_only']); changed=set()
    for ref in b:
        ob,nn=b[ref],n[ref]
        if not (near(ob['x_mm'],nn['x_mm']) and near(ob['y_mm'],nn['y_mm']) and near(ob.get('rotation_deg',0),nn.get('rotation_deg',0))): changed.add(ref)
        for key in ('zone','block','role','footprint'):
            if ob.get(key)!=nn.get(key): fail(f'{ref}: cambió {key}')
    if changed!=expected: fail(f'changed={sorted(changed)} expected={sorted(expected)}')
    for ref,t in eco['targets'].items():
        p=n[ref]
        if not (near(p['x_mm'],t['x_mm']) and near(p['y_mm'],t['y_mm']) and near(p['rotation_deg'],t['rotation_deg'])): fail(f'{ref}: target no coincide')
        if p.get('placement_eco')!='PR24_Z2_LOADCELL_TP': fail(f'{ref}: falta marca ECO')
        c=p['courtyard_global_mm']
        if c[0]<108.84-TOL or c[2]>163.34+TOL or c[1]<-TOL or c[3]>68.58+TOL: fail(f'{ref}: courtyard fuera Z2')
    # two 1-mm-radius testpoint courtyards must not overlap
    a=n['TP_LOAD_A_POS']['courtyard_global_mm']; z=n['TP_LOAD_A_NEG']['courtyard_global_mm']
    if min(a[2],z[2])-max(a[0],z[0])>0 and min(a[3],z[3])-max(a[1],z[1])>0: fail('TP load-cell se solapan')
    print('OK: PR24 mueve solo 2 TP load-cell; 117 refs intactas')
    print('POS',n['TP_LOAD_A_POS']['x_mm'],n['TP_LOAD_A_POS']['y_mm'],n['TP_LOAD_A_POS']['courtyard_global_mm'])
    print('NEG',n['TP_LOAD_A_NEG']['x_mm'],n['TP_LOAD_A_NEG']['y_mm'],n['TP_LOAD_A_NEG']['courtyard_global_mm'])
    return 0
if __name__=='__main__': raise SystemExit(main())
