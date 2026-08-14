#!/usr/bin/env python3
"""Materializa PR19D: net local 5V_HMI sobre checkpoint PR19C.

No toca placement, outline ni routing UART. Usa F.Cu solo para escapes SMD y
In2.Cu para la distribución local de potencia.
"""
from __future__ import annotations
import json
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
OUT=ROOT/'hardware'/'pr19d_hmi_power_routing_manifest.json'
TARGETS=[('J_HMI','1'),('U_HMI_LVL','7'),('C_HMI_B','1')]

def iu(x): return pcbnew.FromMM(float(x))
def mm(x): return round(pcbnew.ToMM(x),4)
def V(x,y): return pcbnew.VECTOR2I(iu(x),iu(y))
def fail(m): raise SystemExit('ERROR: '+m)

def segment(board,net,layer,a,b,width=0.40):
    t=pcbnew.PCB_TRACK(board); t.SetNet(net); t.SetLayer(layer); t.SetWidth(iu(width)); t.SetStart(V(*a)); t.SetEnd(V(*b)); board.Add(t)
    return {'net':'5V_HMI','layer':board.GetLayerName(layer),'start_mm':[a[0],a[1]],'end_mm':[b[0],b[1]],'width_mm':width}

def via(board,net,p):
    v=pcbnew.PCB_VIA(board); v.SetNet(net); v.SetPosition(V(*p)); v.SetWidth(iu(0.80)); v.SetDrill(iu(0.40)); board.Add(v)
    return {'net':'5V_HMI','at_mm':[p[0],p[1]],'diameter_mm':0.80,'drill_mm':0.40}

def main():
    b=pcbnew.LoadBoard(str(PCB))
    base_seg=sum(not isinstance(t,pcbnew.PCB_VIA) for t in b.GetTracks()); base_via=sum(isinstance(t,pcbnew.PCB_VIA) for t in b.GetTracks())
    if (base_seg,base_via)!=(917,119): fail(f'baseline PR19C inesperado {(base_seg,base_via)}')
    if len(list(b.Zones()))!=0: fail('PR19D no parte de zones=0')
    if any(t.GetNetname()=='5V_RAIL' for t in b.GetTracks()): fail('5V_RAIL ya tiene cobre; ECO deja de ser no destructivo')
    if any(t.GetNetname()=='5V_HMI' for t in b.GetTracks()): fail('5V_HMI ya tiene cobre')

    net=pcbnew.NETINFO_ITEM(b,'5V_HMI'); b.Add(net)
    fps={f.GetReference():f for f in b.GetFootprints()}
    endpoints=[]
    for ref,pn in TARGETS:
        pad=next((p for p in fps[ref].Pads() if str(p.GetNumber())==pn),None)
        if pad is None: fail(f'falta {ref}.{pn}')
        if pad.GetNetname()!='5V_RAIL': fail(f'{ref}.{pn} baseline net={pad.GetNetname()} != 5V_RAIL')
        pos=pad.GetPosition(); endpoints.append({'ref':ref,'pad':pn,'before':'5V_RAIL','after':'5V_HMI','x_mm':mm(pos.x),'y_mm':mm(pos.y)})
        pad.SetNet(net)

    # Geometría deliberadamente simple; In2 estaba reservado a potencia y sin cobre en PR19C.
    u=(157.035,17.775); vu=(158.20,17.775)
    c=(148.815,20.835); vc=(148.815,22.20)
    j=(151.635,3.635); a=(153.00,12.00); bu=(158.20,12.00); bc=(153.00,22.20)
    segs=[]; vias=[]
    segs.append(segment(b,net,pcbnew.F_Cu,u,vu))
    vias.append(via(b,net,vu))
    segs.append(segment(b,net,pcbnew.F_Cu,c,vc))
    vias.append(via(b,net,vc))
    segs.append(segment(b,net,pcbnew.In2_Cu,j,a))
    segs.append(segment(b,net,pcbnew.In2_Cu,a,bu))
    segs.append(segment(b,net,pcbnew.In2_Cu,bu,vu))
    segs.append(segment(b,net,pcbnew.In2_Cu,a,bc))
    segs.append(segment(b,net,pcbnew.In2_Cu,bc,vc))

    manifest={
      'schema_version':1,'status':'HMI_POWER_ROUTING_PR19D','target_nets':['5V_HMI'],'baseline':{'segments':917,'vias':119},
      'new_segment_count':len(segs),'new_via_count':len(vias),'new_segments':segs,'new_vias':vias,'endpoints':endpoints,
      'policies':{'in1_signal_tracks':0,'zones_added':0,'existing_routing_removed':0,'uart_routing_changed':0,'future_batch_copper':0},
      'intent':'Local 5V_HMI only. HMI display/audio high current remains external; PCBA route feeds TXU0202 VCCB/C_HMI_B.'
    }
    pcbnew.SaveBoard(str(PCB),b); OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f"PR19D candidate: segments={len(segs)} vias={len(vias)} total={917+len(segs)}/{119+len(vias)}")

if __name__=='__main__': main()
