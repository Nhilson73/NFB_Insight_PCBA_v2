#!/usr/bin/env python3
"""Valida DRC placement contra deuda exacta PR17/PR22/PR24 y ECO netlist PR19D.

Los contratos históricos fijaron 250 unconnected con 59 nets. PR19D divide tres
endpoints que compartían 5V_RAIL en una net adicional 5V_HMI; sobre una vista
placement-only de la misma geometría eso reduce el conteo esperado a 249 sin
cambiar warnings, placement ni reglas DRC.
"""
from __future__ import annotations
import json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'hardware'/'placement_manifest.json'; CONTRACT=ROOT/'hardware'/'placement_drc_contract.json'; Z2=ROOT/'hardware'/'z2_production_netlist.json'
ALLOWED={(1,'BOUNDED_PLACEMENT_DRC_DEBT_PR17'),(2,'BOUNDED_PLACEMENT_DRC_DEBT_PR22_ECO'),(3,'BOUNDED_PLACEMENT_DRC_DEBT_PR24_ECO')}

def fail(m): raise SystemExit('ERROR: '+m)

def expected_unconnected(c):
    base=int(c['expected_unconnected_items'])
    if not Z2.exists(): return base
    z=json.loads(Z2.read_text(encoding='utf-8'))
    nets={n.get('name'):set(n.get('nodes',[])) for n in z.get('nets',[])}
    if '5V_HMI' not in nets: return base
    if nets['5V_HMI']!={'J_HMI.1','U_HMI_LVL.7','C_HMI_B.1'}:
        fail(f"5V_HMI presente con endpoints inesperados: {sorted(nets['5V_HMI'])}")
    if {'J_HMI.1','U_HMI_LVL.7','C_HMI_B.1'} & nets.get('5V_RAIL',set()):
        fail('5V_HMI y 5V_RAIL comparten endpoints tras ECO')
    if base!=250: fail(f'baseline histórico unconnected inesperado={base}')
    return 249

def main():
    if len(sys.argv)!=2: fail('uso: validate_pr17_drc.py <reporte-drc.json>')
    rp=Path(sys.argv[1])
    for p in (rp,MANIFEST,CONTRACT):
        if not p.exists(): fail(f'no existe {p}')
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8')); c=json.loads(CONTRACT.read_text(encoding='utf-8'))
    if manifest.get('status')!='PRODUCTION_PLACEMENT_PR17': fail('status placement PR17 no preservado')
    if manifest.get('policies',{}).get('routing_allowed') is not False: fail('placement baseline habilitó routing')
    ident=(int(c.get('schema_version',-1)),str(c.get('status','')))
    if ident not in ALLOWED: fail(f'contrato DRC no reconocido: {ident}')
    if c.get('scope')!='PLACEMENT_ONLY_NO_ROUTING': fail('scope inesperado')
    if ident[0]==2 and c.get('eco_revision',{}).get('id')!='PR22_Z3_BUCK': fail('schema v2 sin PR22 explícito')
    if ident[0]==3:
        ids=[x.get('id') for x in c.get('eco_revisions',[])]
        if ids!=['PR22_Z3_BUCK','PR24_Z2_LOADCELL_TP']: fail(f'schema v3 requiere PR22+PR24 ordenados; ids={ids}')
        if manifest.get('eco_revision')!=2: fail('schema v3 requiere manifest eco_revision=2')
    if int(c.get('expected_error_count',-1))!=0: fail('placement nunca puede aceptar errores físicos')
    d=json.loads(rp.read_text(encoding='utf-8')); v=d.get('violations'); u=d.get('unconnected_items')
    if not isinstance(v,list) or not isinstance(u,list): fail('reporte KiCad incompleto')
    sev=Counter(str(x.get('severity','?')) for x in v); typ=Counter(str(x.get('type','?')) for x in v)
    exp=Counter({str(k):int(val) for k,val in c['allowed_warning_types_exact'].items()})
    print('DRC_CONTRACT',ident); print('DRC_TYPE_COUNTS',dict(sorted(typ.items()))); print('DRC_SEVERITY_COUNTS',dict(sorted(sev.items())))
    if sev.get('error',0)!=0: fail(f'errores DRC={sev.get("error",0)}')
    nonwarn={k:n for k,n in sev.items() if k!='warning' and n}
    if nonwarn: fail(f'severidades no autorizadas={nonwarn}')
    if typ!=exp: fail(f'deuda warning cambió actual={dict(typ)} esperado={dict(exp)}')
    if sum(typ.values())!=int(c['expected_warning_count']): fail('warning total cambió')
    bad=set(c.get('forbidden_violation_types',[])) & set(typ)
    if bad: fail(f'tipos físicos prohibidos={sorted(bad)}')
    expected=expected_unconnected(c)
    if len(u)!=expected: fail(f'unconnected={len(u)} esperado={expected}')
    mode='PR19D_60_NETS' if expected==249 else 'HISTORICAL_59_NETS'
    print(f'OK: placement DRC exacto; errors=0 warnings={sum(typ.values())} unconnected={len(u)} mode={mode}')
    return 0
if __name__=='__main__': raise SystemExit(main())
