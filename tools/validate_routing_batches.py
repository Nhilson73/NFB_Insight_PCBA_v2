#!/usr/bin/env python3
"""Valida la partición incremental 28+4+16+1+10+1 = 60 nets."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROUTING=ROOT/'hardware'/'routing_contract.json'; BATCHES=ROOT/'hardware'/'routing_batches_contract.json'; KB=ROOT/'docs'/'ROUTING_KNOWLEDGE_BASE.md'
def fail(m): raise SystemExit('ERROR: '+m)
def main():
    r=json.loads(ROUTING.read_text(encoding='utf-8')); b=json.loads(BATCHES.read_text(encoding='utf-8'))
    if b.get('status')!='INCREMENTAL_ROUTING_BATCHES_FROZEN' or b.get('strategy')!='divide_y_venceras': fail('contrato batches no congelado')
    if not KB.exists(): fail('falta ROUTING_KNOWLEDGE_BASE')
    prod=[n for c in r.get('routing_classes',[]) for n in c.get('nets',[])]
    if len(prod)!=60 or len(set(prod))!=60: fail(f'routing_contract debe contener 60 nets únicas; {len(prod)}/{len(set(prod))}')
    ids=['PR19A','PR19B','PR19C','PR19D','PR20A','PR20B']; counts=[28,4,16,1,10,1]
    bl=b.get('batches',[])
    if [x.get('id') for x in bl]!=ids: fail(f'orden lotes != {ids}')
    if [x.get('expected_net_count') for x in bl]!=counts: fail(f'conteos lotes != {counts}')
    if bl[3].get('nets')!=['5V_HMI']: fail('PR19D debe ser exclusivamente 5V_HMI')
    seen=[]
    for x in bl:
        nets=x.get('nets',[])
        if len(nets)!=x['expected_net_count'] or len(nets)!=len(set(nets)): fail(f"{x['id']}: lista/conteo inválido")
        seen+=nets
    if len(seen)!=60 or len(set(seen))!=60: fail('partición no suma 60 nets únicas')
    if set(seen)!=set(prod): fail(f'partición no exhaustiva missing={sorted(set(prod)-set(seen))} extra={sorted(set(seen)-set(prod))}')
    inv=b.get('invariants',{})
    for key in ('placement_changes_allowed','board_geometry_changes_allowed','netlist_changes_allowed','in1_signal_routing_allowed_before_pr20b'):
        if inv.get(key) is not False: fail(f'invariante debe ser false: {key}')
    if inv.get('batch_merge_policy')!='ALL_OR_NOTHING': fail('policy debe ser ALL_OR_NOTHING')
    print('OK: routing batches 60 nets / ALL_OR_NOTHING')
    print('BATCHES=PR19A:28 PR19B:4 PR19C:16 PR19D:1 PR20A:10 PR20B:1')
if __name__=='__main__': main()
