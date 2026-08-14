#!/usr/bin/env python3
"""Sondea la geometría/cobre del ECO 5V_HMI sin modificar el PCB."""
from __future__ import annotations
import json
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
TARGETS=[('J_HMI','1'),('U_HMI_LVL','7'),('C_HMI_B','1')]

def mm(v): return pcbnew.ToMM(v)

def main():
    b=pcbnew.LoadBoard(str(PCB))
    fps={fp.GetReference():fp for fp in b.GetFootprints()}
    out={'targets':[], 'net_copper':{}, 'board':{'tracks':0,'vias':0,'zones':len(list(b.Zones()))}}
    for ref,pn in TARGETS:
        fp=fps[ref]
        pad=next(p for p in fp.Pads() if str(p.GetNumber())==pn)
        pos=pad.GetPosition()
        out['targets'].append({'ref':ref,'pad':pn,'net':pad.GetNetname(),'x_mm':round(mm(pos.x),4),'y_mm':round(mm(pos.y),4),'layer':pad.GetLayerName() if hasattr(pad,'GetLayerName') else None})
    counts={}
    for t in b.GetTracks():
        net=t.GetNetname()
        kind='via' if isinstance(t,pcbnew.PCB_VIA) else 'segment'
        out['board']['vias' if kind=='via' else 'tracks']+=1
        d=counts.setdefault(net,{'segments':0,'vias':0})
        d['vias' if kind=='via' else 'segments']+=1
    for n in ('5V_RAIL','HMI_FIELD_RX','HMI_FIELD_TX','HMI_RX','HMI_TX'):
        out['net_copper'][n]=counts.get(n,{'segments':0,'vias':0})
    print(json.dumps(out,indent=2,ensure_ascii=False))
    if any(x['net']!='5V_RAIL' for x in out['targets']):
        raise SystemExit('targets HMI no están todavía en 5V_RAIL baseline')
    if out['net_copper']['5V_RAIL'] != {'segments':0,'vias':0}:
        raise SystemExit(f"5V_RAIL ya tiene cobre inesperado: {out['net_copper']['5V_RAIL']}")
    if out['board']['zones'] != 0:
        raise SystemExit('checkpoint previo debe seguir sin zonas')
    print('OK: 5V_HMI puede separarse antes de PR20A sin retirar cobre 5V_RAIL')

if __name__=='__main__': main()
