#!/usr/bin/env python3
"""PR16: cierra J_LOADCELL con MPN/footprint Phoenix exactos.

Fuente primaria: Phoenix Contact MSTBA 2,5/4-G-5,08, order no. 1757268,
4 posiciones, pitch 5.08 mm. El script migra JSON+BOM de forma idempotente;
la hoja KiCad generada se regenera luego mediante normalize_pr15_schematics.py.
"""
from __future__ import annotations
import argparse, csv, io, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NET=ROOT/'hardware/z2_production_netlist.json'
BOM=ROOT/'bom/insight_z2_production_bom.csv'
REF='J_LOADCELL'
OLD_MPN='Phoenix PT-1,5-4-5.0-H'
NEW_MPN='1757268'
OLD_FP='TerminalBlock_Phoenix:TerminalBlock_Phoenix_PT-1,5-4-5.0-H_1x04_P5.00mm_Horizontal'
NEW_FP='Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_4-G-5,08_1x04_P5.08mm_Horizontal'
NEW_VALUE='MSTBA 2,5/4-G-5,08'

def fail(m): raise SystemExit('ERROR: '+m)

def expected_json():
    d=json.loads(NET.read_text(encoding='utf-8'))
    c=next((x for x in d['components'] if x['ref']==REF),None)
    if c is None: fail('J_LOADCELL no existe en Z2')
    if c.get('mpn') not in (OLD_MPN,NEW_MPN): fail(f"MPN inesperado {c.get('mpn')}")
    if c.get('footprint') not in (OLD_FP,NEW_FP): fail(f"footprint inesperado {c.get('footprint')}")
    c['mpn']=NEW_MPN; c['footprint']=NEW_FP; c['value']=NEW_VALUE
    return json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n'

def expected_bom():
    with BOM.open(newline='',encoding='utf-8') as fh:
        rd=csv.DictReader(fh); fields=rd.fieldnames; rows=list(rd)
    if not fields: fail('BOM sin encabezado')
    r=next((x for x in rows if x['ref']==REF),None)
    if r is None: fail('J_LOADCELL no existe en BOM')
    if r['mpn_o_familia'] not in (OLD_MPN,NEW_MPN): fail(f"MPN BOM inesperado {r['mpn_o_familia']}")
    if r['footprint'] not in (OLD_FP,NEW_FP): fail(f"footprint BOM inesperado {r['footprint']}")
    r['valor']=NEW_VALUE; r['mpn_o_familia']=NEW_MPN; r['footprint']=NEW_FP
    r['nota']='E+/E-/A+/A-; Phoenix 1757268 exacto, 4 posiciones, pitch 5.08 mm; side-entry hacia -Y.'
    out=io.StringIO(newline=''); wr=csv.DictWriter(out,fieldnames=fields,lineterminator='\n'); wr.writeheader(); wr.writerows(rows)
    return out.getvalue()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); a=ap.parse_args()
    exp={NET:expected_json(),BOM:expected_bom()}; stale=[]
    for p,c in exp.items():
        if p.read_text(encoding='utf-8')!=c:
            stale.append(p)
            if not a.check: p.write_text(c,encoding='utf-8'); print('updated',p.relative_to(ROOT))
    if a.check and stale: fail('migración pendiente: '+', '.join(str(x.relative_to(ROOT)) for x in stale))
    if a.check: print('OK: J_LOADCELL = Phoenix Contact 1757268 / 5.08 mm')
    return 0
if __name__=='__main__': raise SystemExit(main())
