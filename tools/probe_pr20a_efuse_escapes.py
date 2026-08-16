#!/usr/bin/env python3
"""Micro-DRC de escapes/portales U_EFUSE.5/.6 con el DRU real."""
from __future__ import annotations
import json, subprocess, tempfile, shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'; DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
# tracks = (net, layer, a, z, width); vias=(net,xy,diam,drill)
VARIANTS={
 'RAW_PORTAL':{
   'tracks':[('12V_IN_RAW','F',(177.525,17.975),(177.525,14.0),0.25),('12V_IN_RAW','F',(177.525,14.0),(175.5,12.0),0.25),('12V_IN_RAW','I2',(175.5,12.0),(170.0,12.0),2.0)],
   'vias':[('12V_IN_RAW',(175.5,12.0),1.2,0.6)]},
 'PROT_PORTAL':{
   'tracks':[('12V_PROTECTED','F',(178.025,17.975),(178.025,14.0),0.25),('12V_PROTECTED','F',(178.025,14.0),(181.0,12.0),0.25),('12V_PROTECTED','I2',(181.0,12.0),(186.0,12.0),2.0)],
   'vias':[('12V_PROTECTED',(181.0,12.0),1.2,0.6)]},
 'BOTH_PORTALS':{
   'tracks':[('12V_IN_RAW','F',(177.525,17.975),(177.525,14.0),0.25),('12V_IN_RAW','F',(177.525,14.0),(175.5,12.0),0.25),('12V_IN_RAW','I2',(175.5,12.0),(170.0,12.0),2.0),('12V_PROTECTED','F',(178.025,17.975),(178.025,14.0),0.25),('12V_PROTECTED','F',(178.025,14.0),(181.0,12.0),0.25),('12V_PROTECTED','I2',(181.0,12.0),(186.0,12.0),2.0)],
   'vias':[('12V_IN_RAW',(175.5,12.0),1.2,0.6),('12V_PROTECTED',(181.0,12.0),1.2,0.6)]},
}
def iu(x):return pcbnew.FromMM(float(x))
def V(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def nets(b):
 d={}
 for fp in b.GetFootprints():
  for p in fp.Pads():
   if p.GetNetname():d.setdefault(p.GetNetname(),p.GetNet())
 return d
def add_track(b,nn,net,layer,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(nn[net]);t.SetLayer(pcbnew.F_Cu if layer=='F' else pcbnew.In2_Cu);t.SetWidth(iu(w));t.SetStart(V(*a));t.SetEnd(V(*z));b.Add(t)
def add_via(b,nn,net,p,d,dr):
 v=pcbnew.PCB_VIA(b);v.SetNet(nn[net]);v.SetPosition(V(*p));v.SetWidth(iu(d));v.SetDrill(iu(dr));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def main():
 results={}
 with tempfile.TemporaryDirectory(prefix='pr20a_efuse_') as td:
  td=Path(td)
  for name,cfg in VARIANTS.items():
   b=pcbnew.LoadBoard(str(PCB));nn=nets(b)
   for q in cfg['tracks']:add_track(b,nn,*q)
   for q in cfg['vias']:add_via(b,nn,*q)
   p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],check=False,capture_output=True,text=True)
   d=json.loads(r.read_text(encoding='utf-8'));e=[v for v in d.get('violations',[]) if v.get('severity')=='error']
   results[name]={'errors':len(e),'types':dict(Counter(str(v.get('type','?')) for v in e)),'warnings':sum(v.get('severity')=='warning' for v in d.get('violations',[])),'unconnected':len(d.get('unconnected_items',[])),'first_errors':e[:10]}
 print('EFUSE_PORTAL_DRC',json.dumps(results,ensure_ascii=False,separators=(',',':')))
 good=[k for k,v in results.items() if v['errors']==0];print('EFUSE_PORTAL_GOOD',good)
 if 'BOTH_PORTALS' not in good:raise SystemExit('ERROR: portales combinados eFuse no son DRC=0')
if __name__=='__main__':main()
