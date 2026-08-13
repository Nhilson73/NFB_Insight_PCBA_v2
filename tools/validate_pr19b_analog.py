#!/usr/bin/env python3
"""Gate final acumulativo PR19A + PR19B."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
import pcbnew  # type: ignore
import validate_pr17_placement as p17

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
PLACEMENT=ROOT/'hardware'/'placement_manifest.json'
BATCHES=ROOT/'hardware'/'routing_batches_contract.json'
M19A=ROOT/'hardware'/'pr19a_local_routing_manifest.json'
M19B=ROOT/'hardware'/'pr19b_analog_routing_manifest.json'
BASE=ROOT/'hardware'/'placement_drc_contract.json'

def fail(x): raise SystemExit('ERROR: '+x)
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def strings(o):
    if isinstance(o,str): yield o
    elif isinstance(o,dict):
        for k,v in o.items(): yield from strings(k); yield from strings(v)
    elif isinstance(o,list):
        for v in o: yield from strings(v)
def mentions(item,net): return any(s==net or re.search(rf'(?<![A-Za-z0-9_]){re.escape(net)}(?![A-Za-z0-9_])',s) for s in strings(item))

def frozen(board,placement):
    ps={p['ref']:p for p in placement['placements']}; fps={x.GetReference():x for x in board.GetFootprints()}
    if set(fps)!=({'J_UNOQ'}|set(ps)): fail('refs/footprints cambiaron')
    text=PCB.read_text(encoding='utf-8'); x0,y0,x1,y1=p17.edge_bbox(text)
    if not all(p17.near(a,b) for a,b in zip((x0,y0,x1,y1),(0,0,float(placement['board']['width_mm']),float(placement['board']['height_mm'])))): fail('outline cambió')
    h=fps['J_UNOQ']; hp=h.GetPosition()
    if not (p17.near(p17.mm(hp.x),0) and p17.near(p17.mm(hp.y),0) and p17.near(h.GetOrientationDegrees(),0)): fail('J_UNOQ cambió')
    for ref,e in ps.items():
        fp=fps[ref]; q=fp.GetPosition(); actual=(p17.mm(q.x),p17.mm(q.y),fp.GetOrientationDegrees()); target=(float(e['x_mm']),float(e['y_mm']),float(e['rotation_deg']))
        if not all(p17.near(a,b) for a,b in zip(actual,target)): fail(f'{ref}: placement cambió')
        if p17.fpid_text(fp)!=e['footprint']: fail(f'{ref}: footprint cambió')
    if re.search(r'^\s*\(zone\b',text,re.M): fail('copper zones no permitidas todavía')

def main():
    if len(sys.argv)!=2: fail('uso: validate_pr19b_analog.py <drc.json>')
    drcp=Path(sys.argv[1]); placement=load(PLACEMENT); batches=load(BATCHES); a=load(M19A); b=load(M19B); base=load(BASE); drc=load(drcp)
    by={x['id']:x for x in batches['batches']}; n19a=set(by['PR19A']['nets']); n19b=set(by['PR19B']['nets']); expected=n19a|n19b
    future=set().union(*(set(x['nets']) for x in batches['batches'] if x['id'] not in {'PR19A','PR19B'}))
    if len(n19a)!=28 or len(n19b)!=4 or len(expected)!=32 or len(future)!=27: fail('partición acumulativa inesperada')
    if set(a.get('routed_nets',[]))!=n19a or len(a.get('segments',[]))!=523 or len(a.get('vias',[]))!=24: fail('checkpoint PR19A cambió')
    if b.get('status')!='ANALOG_ROUTING_PR19B' or set(b.get('target_nets',[]))!=n19b: fail('manifest PR19B inválido')
    if b.get('new_segment_count')!=32 or b.get('new_via_count')!=7: fail('métricas PR19B inesperadas')
    board=pcbnew.LoadBoard(str(PCB)); frozen(board,placement)
    touched=set(); in1=[]; seg=via=0
    for x in board.GetTracks():
        n=x.GetNetname();
        if not n: fail('cobre sin net')
        touched.add(n)
        if isinstance(x,pcbnew.PCB_VIA): via+=1
        else: seg+=1
        if x.GetLayer()==pcbnew.In1_Cu: in1.append(n)
    if touched!=expected: fail(f'cobre fuera de PR19A+PR19B: faltan={sorted(expected-touched)} sobran={sorted(touched-expected)}')
    if touched&future: fail(f'nets futuras tocadas: {sorted(touched&future)}')
    if (seg,via)!=(555,31): fail(f'totales inesperados segmentos/vías={(seg,via)}')
    if in1: fail(f'In1.Cu usado para señal: {sorted(set(in1))}')
    errors=[v for v in drc.get('violations',[]) if v.get('severity')=='error']
    if errors: fail(f'DRC errors={len(errors)} primero={errors[0]}')
    counts={}
    for v in drc.get('violations',[]): counts[v.get('type','?')]=counts.get(v.get('type','?'),0)+1
    exp={'silk_edge_clearance':13,'text_height':1,'silk_overlap':173,'silk_over_copper':68}
    if counts!=exp: fail(f'deuda DRC cambió: {counts}')
    unc=drc.get('unconnected_items',[])
    leaks=[(n,u) for u in unc for n in expected if mentions(u,n)]
    if leaks: fail(f'net ruteada aún unconnected: {leaks[0][0]}')
    if len(unc)!=192: fail(f'unconnected={len(unc)} != 192')
    print('OK PR19B: PR19A 28/28 preservado + PR19B 4/4')
    print('- 555 segmentos, 31 vías; 27 nets futuras sin cobre; In1.Cu=0 señales; zones=0')
    print('- DRC errors=0; warnings conocidos=255; unconnected=192')
    return 0
if __name__=='__main__': raise SystemExit(main())
