#!/usr/bin/env python3
"""Micro-DRC de portales locales 12V_ACT desde columnas In2 probadas."""
from __future__ import annotations
import json, subprocess, tempfile, shutil
from pathlib import Path
from collections import Counter
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'

# Cada variante incluye columnas ya probadas y una transición local F.Cu.
# tracks: (layer,a,z,width), vias:(xy,diam,drill)
VARIANTS={
 'PUMP_A':{
   'tracks':[('I2',(205.5,63.0),(205.5,12.0),1.0),('F',(205.5,12.0),(205.5,17.255),1.0),('F',(205.5,17.255),(200.19,18.125),1.0)],
   'vias':[((205.5,12.0),0.9,0.45)]},
 'PUMP_B':{
   'tracks':[('I2',(205.5,63.0),(205.5,27.5),1.0),('F',(205.5,27.5),(205.5,17.255),1.0),('F',(205.5,17.255),(200.19,18.125),1.0)],
   'vias':[((205.5,27.5),0.9,0.45)]},
 'PUMP_C':{
   'tracks':[('I2',(205.5,63.0),(205.5,12.0),1.0),('F',(205.5,12.0),(203.0,12.0),1.0),('F',(203.0,12.0),(200.19,18.125),1.0),('F',(203.0,12.0),(205.52,17.255),0.5)],
   'vias':[((205.5,12.0),0.9,0.45)]},
 'PUMP_D':{
   'tracks':[('I2',(207.0,63.0),(207.0,12.0),1.0),('F',(207.0,12.0),(204.5,12.0),1.0),('F',(204.5,12.0),(200.19,18.125),1.0),('F',(204.5,12.0),(205.52,17.255),0.5)],
   'vias':[((207.0,12.0),0.9,0.45)]},
 'CO2_A':{
   'tracks':[('I2',(222.0,63.0),(222.0,12.0),1.0),('F',(222.0,12.0),(222.0,14.0),1.0),('F',(222.0,14.0),(213.99,17.255),0.5)],
   'vias':[((222.0,12.0),0.9,0.45)]},
 'CO2_B':{
   'tracks':[('I2',(222.0,63.0),(222.0,27.0),1.0),('F',(222.0,27.0),(224.0,27.0),1.0),('F',(224.0,27.0),(224.0,12.0),1.0),('F',(224.0,12.0),(213.99,17.255),0.5)],
   'vias':[((222.0,27.0),0.9,0.45)]},
 'CO2_C':{
   'tracks':[('I2',(226.0,63.0),(226.0,12.0),1.0),('F',(226.0,12.0),(224.5,12.0),1.0),('F',(224.5,12.0),(213.99,17.255),0.5)],
   'vias':[((226.0,12.0),0.9,0.45)]},
 'CO2_D':{
   'tracks':[('I2',(222.0,63.0),(222.0,12.0),1.0),('F',(222.0,12.0),(220.5,12.0),1.0),('F',(220.5,12.0),(220.5,14.0),1.0),('F',(220.5,14.0),(213.99,17.255),0.5)],
   'vias':[((222.0,12.0),0.9,0.45)]},
}

def iu(x): return pcbnew.FromMM(float(x))
def V(x,y): return pcbnew.VECTOR2I(iu(x),iu(y))
def getnet(b):
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname()=='12V_ACT': return p.GetNet()
    raise SystemExit('12V_ACT missing')
def add_track(b,n,l,a,z,w):
    t=pcbnew.PCB_TRACK(b); t.SetNet(n); t.SetLayer(pcbnew.In2_Cu if l=='I2' else pcbnew.F_Cu); t.SetWidth(iu(w)); t.SetStart(V(*a)); t.SetEnd(V(*z)); b.Add(t)
def add_via(b,n,p,d,dr):
    v=pcbnew.PCB_VIA(b); v.SetNet(n); v.SetPosition(V(*p)); v.SetWidth(iu(d)); v.SetDrill(iu(dr)); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); b.Add(v)
def main():
    out={}
    with tempfile.TemporaryDirectory(prefix='pr20a_islands_') as td:
        td=Path(td)
        for name,cfg in VARIANTS.items():
            b=pcbnew.LoadBoard(str(PCB)); n=getnet(b)
            for l,a,z,w in cfg['tracks']: add_track(b,n,l,a,z,w)
            for p,d,dr in cfg['vias']: add_via(b,n,p,d,dr)
            p=td/f'{name}.kicad_pcb'; r=td/f'{name}.json'; pcbnew.SaveBoard(str(p),b); shutil.copyfile(DRU,td/f'{name}.kicad_dru')
            subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
            d=json.loads(r.read_text(encoding='utf-8')); errs=[v for v in d.get('violations',[]) if v.get('severity')=='error']
            out[name]={'errors':len(errs),'types':dict(Counter(str(v.get('type','?')) for v in errs)),'first':errs[:5]}
    print('ACT_ISLANDS',json.dumps(out,ensure_ascii=False,separators=(',',':')))
    print('ACT_ISLANDS_GOOD',[k for k,v in out.items() if v['errors']==0])

if __name__=='__main__': main()
