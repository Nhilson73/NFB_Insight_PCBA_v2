#!/usr/bin/env python3
"""Micro-DRC de portales separados para U_CO2_DRV.8 y C_CO2_DRV.1."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
VARS={
 'PIN_RIGHT_222':{
  'tracks':[('I2',(222,63),(222,18.375),1.0),('F',(222,18.375),(220.0,18.375),0.5),('F',(220.0,18.375),(218.82,18.375),0.2)],'vias':[((222,18.375),.9,.45)]},
 'PIN_RIGHT_226':{
  'tracks':[('I2',(226,63),(226,18.375),1.0),('F',(226,18.375),(220.0,18.375),0.5),('F',(220.0,18.375),(218.82,18.375),0.2)],'vias':[((226,18.375),.9,.45)]},
 'CAP_TOP_222':{
  'tracks':[('I2',(222,63),(222,27),1.0),('F',(222,27),(228,27),0.5),('F',(228,27),(228,10.5),0.5),('F',(228,10.5),(213.99,10.5),0.5),('F',(213.99,10.5),(213.99,17.255),0.5)],'vias':[((222,27),.9,.45)]},
 'CAP_TOP_226':{
  'tracks':[('I2',(226,63),(226,27),1.0),('F',(226,27),(230,27),0.5),('F',(230,27),(230,9.5),0.5),('F',(230,9.5),(213.99,9.5),0.5),('F',(213.99,9.5),(213.99,17.255),0.5)],'vias':[((226,27),.9,.45)]},
 'CAP_TOP_236':{
  'tracks':[('I2',(236,63),(236,27),1.0),('F',(236,27),(238,27),0.5),('F',(238,27),(238,8.5),0.5),('F',(238,8.5),(212.5,8.5),0.5),('F',(212.5,8.5),(212.5,12.0),0.5),('F',(212.5,12.0),(213.99,17.255),0.5)],'vias':[((236,27),.9,.45)]},
 'CAP_LEFT_207':{
  'tracks':[('I2',(207,63),(207,27),1.0),('F',(207,27),(204,27),0.5),('F',(204,27),(204,11),0.5),('F',(204,11),(213.99,11),0.5),('F',(213.99,11),(213.99,17.255),0.5)],'vias':[((207,27),.9,.45)]},
 'CAP_TOP_240':{
  'tracks':[('I2',(240,63),(240,27),1.0),('F',(240,27),(240,7.5),0.5),('F',(240,7.5),(212.5,7.5),0.5),('F',(212.5,7.5),(212.5,12.0),0.5),('F',(212.5,12.0),(213.99,17.255),0.5)],'vias':[((240,27),.9,.45)]},
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
 with tempfile.TemporaryDirectory(prefix='pr20a_co2_') as td:
  td=Path(td)
  for name,c in VARS.items():
   b=pcbnew.LoadBoard(str(PCB));n=net(b)
   for q in c['tracks']:t(b,n,*q)
   for q in c['vias']:v(b,n,*q)
   p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
   d=json.loads(r.read_text());e=[x for x in d.get('violations',[]) if x.get('severity')=='error']
   out[name]={'errors':len(e),'types':dict(Counter(x.get('type','?') for x in e)),'first':e[:5]}
 print('CO2_POWER_PORTALS',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print('CO2_POWER_GOOD',[k for k,vv in out.items() if vv['errors']==0])
if __name__=='__main__':main()
