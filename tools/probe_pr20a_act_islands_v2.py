#!/usr/bin/env python3
"""Micro-DRC de portales laterales para las islas 12V_ACT."""
from __future__ import annotations
import json, subprocess, tempfile, shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'; DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
# (layer,a,z,width), vias(xy,d,dr)
VARIANTS={
 'PUMP_SIDE':{
  'tracks':[('I2',(199.5,63.0),(199.5,18.125),1.0),('F',(199.5,18.125),(200.19,18.125),1.0)],
  'vias':[((199.5,18.125),0.9,0.45)]},
 'PUMP_SIDE_VM':{
  'tracks':[('I2',(199.5,63.0),(199.5,18.125),1.0),('F',(199.5,18.125),(200.19,18.125),1.0),('F',(200.19,18.125),(200.19,15.25),0.5),('F',(200.19,15.25),(205.52,15.25),0.5),('F',(205.52,15.25),(205.52,17.255),0.5)],
  'vias':[((199.5,18.125),0.9,0.45)]},
 'PUMP_SIDE_VM_HIGH':{
  'tracks':[('I2',(199.5,63.0),(199.5,18.125),1.0),('F',(199.5,18.125),(200.19,18.125),1.0),('F',(200.19,18.125),(200.19,13.5),0.5),('F',(200.19,13.5),(205.52,13.5),0.5),('F',(205.52,13.5),(205.52,17.255),0.5)],
  'vias':[((199.5,18.125),0.9,0.45)]},
 'CO2_SIDE':{
  'tracks':[('I2',(211.5,63.0),(211.5,17.255),1.0),('F',(211.5,17.255),(213.99,17.255),0.5)],
  'vias':[((211.5,17.255),0.9,0.45)]},
 'CO2_SIDE_LOW':{
  'tracks':[('I2',(211.5,63.0),(211.5,15.0),1.0),('F',(211.5,15.0),(213.99,15.0),0.5),('F',(213.99,15.0),(213.99,17.255),0.5)],
  'vias':[((211.5,15.0),0.9,0.45)]},
 'COMBINED_CAPS':{
  'tracks':[('I2',(175.118,63.0),(211.5,63.0),1.0),('I2',(199.5,63.0),(199.5,18.125),1.0),('F',(199.5,18.125),(200.19,18.125),1.0),('I2',(211.5,63.0),(211.5,17.255),1.0),('F',(211.5,17.255),(213.99,17.255),0.5)],
  'vias':[((175.118,63.0),0.9,0.45),((199.5,18.125),0.9,0.45),((211.5,17.255),0.9,0.45)]},
}
def iu(x):return pcbnew.FromMM(float(x))
def V(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def getnet(b):
 for fp in b.GetFootprints():
  for p in fp.Pads():
   if p.GetNetname()=='12V_ACT':return p.GetNet()
 raise SystemExit('12V_ACT missing')
def addt(b,n,l,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(pcbnew.In2_Cu if l=='I2' else pcbnew.F_Cu);t.SetWidth(iu(w));t.SetStart(V(*a));t.SetEnd(V(*z));b.Add(t)
def addv(b,n,p,d,dr):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(V(*p));v.SetWidth(iu(d));v.SetDrill(iu(dr));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def main():
 out={}
 with tempfile.TemporaryDirectory(prefix='pr20a_act2_') as td:
  td=Path(td)
  for name,cfg in VARIANTS.items():
   b=pcbnew.LoadBoard(str(PCB));n=getnet(b)
   for q in cfg['tracks']:addt(b,n,*q)
   for q in cfg['vias']:addv(b,n,*q)
   p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
   d=json.loads(r.read_text());e=[v for v in d.get('violations',[]) if v.get('severity')=='error']
   out[name]={'errors':len(e),'types':dict(Counter(v.get('type','?') for v in e)),'first':e[:6]}
 print('ACT_ISLANDS_V2',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print('ACT_ISLANDS_V2_GOOD',[k for k,v in out.items() if v['errors']==0])
if __name__=='__main__':main()
