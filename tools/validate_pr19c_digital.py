#!/usr/bin/env python3
"""Gate acumulativo PR19A + PR19B + PR19C."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pcbnew  # type: ignore
import validate_pr17_placement as p17

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
PLACEMENT=ROOT/'hardware'/'placement_manifest.json'
BATCHES=ROOT/'hardware'/'routing_batches_contract.json'
M19A=ROOT/'hardware'/'pr19a_local_routing_manifest.json'
M19B=ROOT/'hardware'/'pr19b_analog_routing_manifest.json'
M19C=ROOT/'hardware'/'pr19c_digital_routing_manifest.json'
KNOWN_WARNING_TYPES={'silk_edge_clearance','text_height','silk_overlap','silk_over_copper'}


def fail(x): raise SystemExit('ERROR: '+x)
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def strings(o):
    if isinstance(o,str): yield o
    elif isinstance(o,dict):
        for k,v in o.items(): yield from strings(k); yield from strings(v)
    elif isinstance(o,list):
        for v in o: yield from strings(v)
def mentions(item,net):
    return any(s==net or re.search(rf'(?<![A-Za-z0-9_]){re.escape(net)}(?![A-Za-z0-9_])',s) for s in strings(item))


def frozen(board,placement):
    ps={p['ref']:p for p in placement['placements']}; fps={x.GetReference():x for x in board.GetFootprints()}
    if set(fps)!=({'J_UNOQ'}|set(ps)): fail('refs/footprints cambiaron')
    text=PCB.read_text(encoding='utf-8'); x0,y0,x1,y1=p17.edge_bbox(text)
    expected=(0,0,float(placement['board']['width_mm']),float(placement['board']['height_mm']))
    if not all(p17.near(a,b) for a,b in zip((x0,y0,x1,y1),expected)): fail('outline cambió')
    h=fps['J_UNOQ']; hp=h.GetPosition()
    if not (p17.near(p17.mm(hp.x),0) and p17.near(p17.mm(hp.y),0) and p17.near(h.GetOrientationDegrees(),0)): fail('J_UNOQ cambió')
    for ref,e in ps.items():
        fp=fps[ref]; q=fp.GetPosition(); actual=(p17.mm(q.x),p17.mm(q.y),fp.GetOrientationDegrees()); target=(float(e['x_mm']),float(e['y_mm']),float(e['rotation_deg']))
        if not all(p17.near(a,b) for a,b in zip(actual,target)): fail(f'{ref}: placement cambió')
        if p17.fpid_text(fp)!=e['footprint']: fail(f'{ref}: footprint cambió')
    if re.search(r'^\s*\(zone\b',text,re.M): fail('copper zones no permitidas antes de PR20B')


def main():
    if len(sys.argv)!=2: fail('uso: validate_pr19c_digital.py <drc.json>')
    drcp=Path(sys.argv[1])
    for p in (PCB,PLACEMENT,BATCHES,M19A,M19B,M19C,drcp):
        if not p.exists(): fail(f'falta {p.relative_to(ROOT) if p.is_relative_to(ROOT) else p}')
    placement=load(PLACEMENT); batches=load(BATCHES); a=load(M19A); b=load(M19B); c=load(M19C); drc=load(drcp)
    by={x['id']:x for x in batches['batches']}
    n19a=set(by['PR19A']['nets']); n19b=set(by['PR19B']['nets']); n19c=set(by['PR19C']['nets'])
    expected=n19a|n19b|n19c
    future=set(by['PR20A']['nets'])|set(by['PR20B']['nets'])
    if (len(n19a),len(n19b),len(n19c),len(expected),len(future))!=(28,4,16,48,11): fail('partición acumulativa inesperada')
    if set(a.get('routed_nets',[]))!=n19a or len(a.get('segments',[]))!=523 or len(a.get('vias',[]))!=24: fail('checkpoint PR19A cambió')
    if b.get('status')!='ANALOG_ROUTING_PR19B' or set(b.get('target_nets',[]))!=n19b or b.get('new_segment_count')!=32 or b.get('new_via_count')!=7: fail('checkpoint PR19B cambió')
    if c.get('status') not in {'PR19C_DIGITAL_ROUTING_CANDIDATE','DIGITAL_ROUTING_PR19C'}: fail('status manifest PR19C inválido')
    if set(c.get('target_nets',[]))!=n19c or len(c.get('target_nets',[]))!=16: fail('manifest PR19C no cubre 16 nets')
    stats=c.get('net_stats',[])
    if len(stats)!=16 or {s.get('net') for s in stats}!=n19c: fail('net_stats PR19C incompleto')
    if int(c.get('new_segment_count',-1)) != len(c.get('new_segments',[])): fail('conteo segmentos manifest PR19C inconsistente')
    if int(c.get('new_via_count',-1)) != len(c.get('new_vias',[])): fail('conteo vías manifest PR19C inconsistente')
    for s in stats:
        if int(s['segment_count'])>140: fail(f"{s['net']}: ruta excesivamente fragmentada ({s['segment_count']} segmentos)")
        if int(s['via_count'])>10: fail(f"{s['net']}: demasiadas vías ({s['via_count']})")
        if int(s.get('bend_count',0))>100: fail(f"{s['net']}: demasiados giros ({s.get('bend_count')})")

    board=pcbnew.LoadBoard(str(PCB)); frozen(board,placement)
    touched=set(); in1=[]; seg=via=0
    for x in board.GetTracks():
        n=x.GetNetname()
        if not n: fail('cobre sin net')
        touched.add(n)
        if isinstance(x,pcbnew.PCB_VIA): via+=1
        else: seg+=1
        if x.GetLayer()==pcbnew.In1_Cu: in1.append(n)
    if touched!=expected: fail(f'cobre fuera de PR19A+PR19B+PR19C: faltan={sorted(expected-touched)} sobran={sorted(touched-expected)}')
    if touched&future: fail(f'nets PR20 adelantadas: {sorted(touched&future)}')
    expected_totals=(555+int(c['new_segment_count']),31+int(c['new_via_count']))
    if (seg,via)!=expected_totals: fail(f'totales segmentos/vías={(seg,via)} != {expected_totals}')
    if in1: fail(f'In1.Cu usado para señal: {sorted(set(in1))}')

    violations=drc.get('violations',[])
    errors=[v for v in violations if v.get('severity')=='error']
    if errors: fail(f'DRC errors={len(errors)} primero={errors[0]}')
    types={v.get('type','?') for v in violations}
    unexpected=types-KNOWN_WARNING_TYPES
    if unexpected: fail(f'tipos DRC nuevos/no autorizados: {sorted(unexpected)}')
    unc=drc.get('unconnected_items',[])
    leaks=[(n,u) for u in unc for n in n19c if mentions(u,n)]
    if leaks: fail(f'PR19C no cerró 16/16; unconnected en {leaks[0][0]}')
    if len(unc)!=154: fail(f'unconnected={len(unc)} != 154 esperado tras 38 conexiones lógicas PR19C')

    counts={}
    for v in violations: counts[v.get('type','?')]=counts.get(v.get('type','?'),0)+1
    print('OK PR19C: PR19A 28/28 + PR19B 4/4 + PR19C 16/16')
    print(f"- acumulado segments={seg}, vias={via}; PR20 sin cobre; In1.Cu=0 señales; zones=0")
    print(f"- DRC errors=0; warnings={sum(counts.values())} {counts}; unconnected=154")
    print('- métricas PR19C:')
    for s in sorted(stats,key=lambda x:x['net']):
        print(f"  {s['net']}: seg={s['segment_count']} vias={s['via_count']} bends={s.get('bend_count')} len={s.get('grid_length_mm')} mm")
    return 0


if __name__=='__main__': raise SystemExit(main())
