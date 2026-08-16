#!/usr/bin/env python3
"""Micro-DRC CO2: entrar por encima de CO2_ILIM y alimentar cap por portal separado."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
VARS={
 'PIN_TOP_A':{
  'tracks':[('I2',(222,63),(222,14),1.0),('F',(222,14),(219.5,14),0.5),('F',(219.5,14),(219.5,16.5),0.5),('F',(219.5,16.5),(218.82,18.375),0.2)],'vias':[((222,14),.9,.45)]},
 'PIN_TOP_B':{
  'tracks':[('I2',(222,63),(222,13),1.0),('F',(222,13),(219.25,13),0.5),('F',(219.25,13),(219.25,16.25),0.5),('F',(219.25,16.25),(218.82,18.375),0.2)],'vias':[((222,13),.9,.45)]},
 'PIN_TOP_C':{
  'tracks':[('I2',(226,63),(226,13),1.0),('F',(226,13),(219.5,13),0.5),('F',(219.5,13),(219.5,16.5),0.5),('F',(219.5,16.5),(218.82,18.375),0.2)],'vias':[((226,13),.9,.45)]},
 'CAP_BOTTOM_A':{
  'tracks':[('I2',(207,63),(207,24),1.0),('F',(207,24),(212.5,24),0.5),('F',(212.5,24),(212.5,21.5),0.5),('F',(212.5,21.5),(213.99,21.5),0.5),('F',(213.99,21.5),(213.99,17.255),0.5)],'vias':[((207,24),.9,.45)]},
 'CAP_BOTTOM_B':{
  'tracks':[('I2',(205.5,63),(205.5,24),1.0),('F',(205.5,24),(211.0,24),0.5),('F',(211.0,24),(211.0,22),0.5),('F',(211.0,22),(213.99,22),0.5),('F',(213.99,22),(213.99,17.255),0.5)],'vias':[((205.5,24),.9,.45)]},
 'CAP_BOTTOM_C':{
  'tracks':[('I2',(207,63),(207,25.5),1.0),('F',(207,25.5),(213.99,25.5),0.5),('F',(213.99,25.5),(213.99,17.255),0.5)],'vias':[((207,25.5),.9,.45)]},
 'COMBINED_A':{
  'tracks':[('I2',(175.118,63),(222,63),1.0),('I2',(207,63),(207,24),1.0),('F',(207,24),(212.5,24),0.5),('F',(212.5,24),(212.5,21.5),0.5),('F',(212.5,21.5),(213.99,21.5),0.5),('F',(213.99,21.5),(213.99,17.255),0.5),('I2',(222,63),(222,14),1.0),('F',(222,14),(219.5,14),0.5),('F',(219.5,14),(219.5,16.5),0.5),('F',(219.5,16.5),(218.82,18.375),0.2)],
  'vias':[((175.118,63),.9,.45),((207,24),.9,.45),((222,14),.9,.45)]},
}
def iu(x):return pcbnew.FromMM(float(x))
def P(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def net(b):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()=='12V_ACT':return p.GetNet()
 raise SystemExit('missing')
def t(b,n,l,a,z,w):
 q=pcbnew.PCB_TRACK(b);q.SetNet(n);q.SetLayer(pcbnew.In2_Cu if l=='I2' else pcbnew.F_Cu);q.SetWidth(iu(w));q.SetStart(P(*a));q.SetEnd(P(*z));b.Add(q)
def v(b,n,p,d,dr):
 q=pcbnew.PCB_VIA(b);q.SetNet(n);q.SetPosition(P(*p));q.SetWidth(iu(d));q.SetDrill(iu(dr));q.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(q)
def main():
 out={}
 with tempfile.TemporaryDirectory(prefix='pr20a_co2v2_') as td:
  td=Path(td)
  for name,c in VARS.items():
   b=pcbnew.LoadBoard(str(PCB));n=net(b)
   for q in c['tracks']:t(b,n,*q)
   for q in c['vias']:v(b,n,*q)
   p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
   d=json.loads(r.read_text());e=[x for x in d.get('violations',[]) if x.get('severity')=='error']
   out[name]={'errors':len(e),'types':dict(Counter(x.get('type','?') for x in e)),'first':e[:5]}
 print('CO2_POWER_V2',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print('CO2_POWER_V2_GOOD',[k for k,vv in out.items() if vv['errors']==0])
if __name__=='__main__':main()
