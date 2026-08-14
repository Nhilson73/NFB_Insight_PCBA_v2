#!/usr/bin/env python3
"""Gate acumulativo del ECO de potencia HMI y routing PR19D."""
from __future__ import annotations
import csv, json, re, sys
from pathlib import Path
import pcbnew
import validate_pr17_placement as p17

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'; ECO=ROOT/'hardware'/'hmi_power_eco.json'; HMI=ROOT/'hardware'/'hmi_system_contract.json'
Z2=ROOT/'hardware'/'z2_production_netlist.json'; POWER=ROOT/'hardware'/'power_architecture_contract.json'; BATCHES=ROOT/'hardware'/'routing_batches_contract.json'
MAN=ROOT/'hardware'/'pr19d_hmi_power_routing_manifest.json'; PLACEMENT=ROOT/'hardware'/'placement_manifest.json'; BOM=ROOT/'bom'/'insight_hmi_system_bom.csv'
KNOWN={'silk_edge_clearance','text_height','silk_overlap','silk_over_copper'}

def fail(m): raise SystemExit('ERROR: '+m)
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def strings(o):
    if isinstance(o,str): yield o
    elif isinstance(o,dict):
        for k,v in o.items(): yield from strings(k); yield from strings(v)
    elif isinstance(o,list):
        for v in o: yield from strings(v)
def mentions(item,net): return any(s==net or re.search(rf'(?<![A-Za-z0-9_]){re.escape(net)}(?![A-Za-z0-9_])',s) for s in strings(item))

def main():
    drc_path=Path(sys.argv[1]) if len(sys.argv)>1 else None
    for p in (PCB,ECO,HMI,Z2,POWER,BATCHES,MAN,PLACEMENT,BOM):
        if not p.exists(): fail(f'falta {p.relative_to(ROOT)}')
    eco=load(ECO); h=load(HMI); z=load(Z2); power=load(POWER); rb=load(BATCHES); man=load(MAN); pm=load(PLACEMENT)
    if eco.get('status')!='HMI_POWER_ECO_PR19D': fail('contrato ECO no es PR19D')
    if eco['external_components']!={'converter':'R-78K5.0-2.0L','fuse_holder':'0FHM0001ZXJ','fuse':'0997002.WXN'}: fail('componentes externos del ECO divergieron')
    da=h.get('dedicated_power_assembly',{})
    if da.get('status')!='SELECTED_POWER_ECO_CLOSED': fail('HMI power assembly no cerrado')
    if da.get('converter',{}).get('mpn')!='R-78K5.0-2.0L' or float(da['converter']['iout_a'])!=2.0: fail('RECOM HMI incorrecto')
    if da.get('fuse_holder',{}).get('mpn')!='0FHM0001ZXJ' or da.get('fuse',{}).get('mpn')!='0997002.WXN': fail('protección HMI incorrecta')
    if h['pcba_interface']['pinout_board']['1']!='5V_HMI' or h['pcba_interface']['signal_mapping']['power']!='5V_HMI': fail('J_HMI no migró a 5V_HMI')
    if h['power_integration']['status']!='POWER_ECO_CLOSED_EXTERNAL_5V_HMI': fail('power integration HMI sigue abierta')
    if power['shield_5v'].get('hmi_integration',{}).get('status')!='CLOSED_EXTERNAL_DEDICATED_5V_HMI': fail('power architecture no cierra HMI')
    if 'HMI' in power['shield_5v'].get('loads',[]): fail('HMI todavía figura como carga 5V_RAIL')
    if power['power_budget'].get('hmi_power_gate')!='CLOSED_EXTERNAL_DEDICATED_5V_HMI': fail('power gate no cerrado')

    comps={c['ref']:c for c in z['components']}
    expected_nodes={'J_HMI.1','U_HMI_LVL.7','C_HMI_B.1'}
    for ref,pin in [('J_HMI','1'),('U_HMI_LVL','7'),('C_HMI_B','1')]:
        if comps[ref]['pins'][pin]!='5V_HMI': fail(f'{ref}.{pin} no es 5V_HMI')
    nets={n['name']:set(n['nodes']) for n in z['nets']}
    if nets.get('5V_HMI')!=expected_nodes: fail(f'5V_HMI nodes={nets.get("5V_HMI")}')
    if expected_nodes & nets.get('5V_RAIL',set()): fail('5V_RAIL retuvo endpoints HMI')
    if nets.get('5V_RAIL')!={'TP_5V.1'}: fail(f'5V_RAIL Z2 inesperado: {nets.get("5V_RAIL")}')

    with BOM.open(newline='',encoding='utf-8') as f: items={r['item_id']:r for r in csv.DictReader(f)}
    for item,mpn in {'HMI_PWR_REG':'R-78K5.0-2.0L','HMI_PWR_FUSE_HOLDER':'0FHM0001ZXJ','HMI_PWR_FUSE':'0997002.WXN'}.items():
        if items.get(item,{}).get('mpn_modelo')!=mpn: fail(f'BOM HMI sin {item}/{mpn}')

    by={b['id']:b for b in rb['batches']}
    if list(by)!=['PR19A','PR19B','PR19C','PR19D','PR20A','PR20B']: fail(f'orden batches inesperado {list(by)}')
    if by['PR19D']['nets']!=['5V_HMI'] or by['PR19D']['expected_net_count']!=1: fail('PR19D no es 5V_HMI 1/1')
    if sum(b['expected_net_count'] for b in rb['batches'])!=60: fail('partición no suma 60')

    if man.get('status')!='HMI_POWER_ROUTING_PR19D' or man.get('target_nets')!=['5V_HMI']: fail('manifest PR19D inválido')
    if man.get('baseline')!={'segments':917,'vias':119}: fail('baseline PR19D no es PR19C')
    if man.get('new_segment_count')!=len(man.get('new_segments',[])) or man.get('new_segment_count')!=7: fail('PR19D debe tener 7 segmentos')
    if man.get('new_via_count')!=len(man.get('new_vias',[])) or man.get('new_via_count')!=2: fail('PR19D debe tener 2 vías')
    if man.get('policies')!={'in1_signal_tracks':0,'zones_added':0,'existing_routing_removed':0,'uart_routing_changed':0,'future_batch_copper':0}: fail('políticas manifest PR19D cambiaron')

    board=pcbnew.LoadBoard(str(PCB)); fps={f.GetReference():f for f in board.GetFootprints()}; pmap={x['ref']:x for x in pm['placements']}
    if set(fps)!=({'J_UNOQ'}|set(pmap)): fail('refs/footprints cambiaron')
    for ref,e in pmap.items():
        fp=fps[ref]; q=fp.GetPosition(); actual=(p17.mm(q.x),p17.mm(q.y),fp.GetOrientationDegrees()); target=(float(e['x_mm']),float(e['y_mm']),float(e['rotation_deg']))
        if not all(p17.near(a,b) for a,b in zip(actual,target)): fail(f'{ref}: placement cambió')
    text=PCB.read_text(encoding='utf-8'); x0,y0,x1,y1=p17.edge_bbox(text)
    if not all(p17.near(a,b) for a,b in zip((x0,y0,x1,y1),(0,0,242.34,68.58))): fail('outline cambió')
    if re.search(r'^\s*\(zone\b',text,re.M): fail('zones no permitidas antes PR20B')

    seg=via=0; bynet={}; in1=[]
    for t in board.GetTracks():
        n=t.GetNetname(); d=bynet.setdefault(n,{'segments':0,'vias':0})
        if isinstance(t,pcbnew.PCB_VIA): via+=1; d['vias']+=1
        else: seg+=1; d['segments']+=1
        if t.GetLayer()==pcbnew.In1_Cu: in1.append(n)
    if (seg,via)!=(924,121): fail(f'totales cobre {(seg,via)} != (924,121)')
    if bynet.get('5V_HMI')!={'segments':7,'vias':2}: fail(f'cobre 5V_HMI inesperado {bynet.get("5V_HMI")}')
    if bynet.get('5V_RAIL',{'segments':0,'vias':0})!={'segments':0,'vias':0}: fail('5V_RAIL fue adelantado')
    if in1: fail(f'In1.Cu usado por señales: {sorted(set(in1))}')
    for ref,pn in [('J_HMI','1'),('U_HMI_LVL','7'),('C_HMI_B','1')]:
        pad=next(p for p in fps[ref].Pads() if str(p.GetNumber())==pn)
        if pad.GetNetname()!='5V_HMI': fail(f'PCB {ref}.{pn} no es 5V_HMI')

    if drc_path:
        drc=load(drc_path); errors=[v for v in drc.get('violations',[]) if v.get('severity')=='error']
        if errors: fail(f'DRC errors={len(errors)} primero={errors[0]}')
        unexpected={v.get('type','?') for v in drc.get('violations',[])}-KNOWN
        if unexpected: fail(f'tipos DRC nuevos: {sorted(unexpected)}')
        leaks=[u for u in drc.get('unconnected_items',[]) if mentions(u,'5V_HMI')]
        if leaks: fail('5V_HMI sigue unconnected')
        print(f"DRC_ERRORS=0 WARNINGS={len(drc.get('violations',[]))} UNCONNECTED={len(drc.get('unconnected_items',[]))}")
    print('OK PR19D: 5V_HMI 1/1; external 5V/2A ECO closed; PCB placement/outline/UART preserved')

if __name__=='__main__': main()
