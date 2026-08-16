#!/usr/bin/env python3
"""Micro-DRC focalizado de portales 12V_ACT en isla CO2."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
# kind, via, path points, width
VARS={
 'PIN_21925_H':('PIN',(219.25,18.375),[(218.82,18.375),(219.25,18.375)],.20),
 'PIN_21950_H':('PIN',(219.50,18.375),[(218.82,18.375),(219.50,18.375)],.20),
 'PIN_21975_H':('PIN',(219.75,18.375),[(218.82,18.375),(219.75,18.375)],.20),
 'PIN_22000_H':('PIN',(220.00,18.375),[(218.82,18.375),(220.00,18.375)],.20),
 'PIN_21950_LOW':('PIN',(219.50,19.00),[(218.82,18.375),(219.10,18.375),(219.10,19.00),(219.50,19.00)],.20),
 'PIN_21975_LOW':('PIN',(219.75,19.00),[(218.82,18.375),(219.10,18.375),(219.10,19.00),(219.75,19.00)],.20),
 'PIN_22000_LOW':('PIN',(220.00,19.00),[(218.82,18.375),(219.10,18.375),(219.10,19.00),(220.00,19.00)],.20),
 'CAP_L_2130':('CAP',(213.00,17.255),[(213.99,17.255),(213.00,17.255)],.50),
 'CAP_L_2125':('CAP',(212.50,17.255),[(213.99,17.255),(212.50,17.255)],.50),
 'CAP_UP_2140':('CAP',(213.99,15.75),[(213.99,17.255),(213.99,15.75)],.50),
 'CAP_UP_2140_15':('CAP',(213.99,15.00),[(213.99,17.255),(213.99,15.00)],.50),
 'CAP_DOWN_2140':('CAP',(213.99,18.75),[(213.99,17.255),(213.99,18.75)],.50),
 'CAP_R_21475':('CAP',(214.75,17.255),[(213.99,17.255),(214.75,17.255)],.40),
 'CAP_UL_21275':('CAP',(212.75,15.50),[(213.99,17.255),(213.25,17.255),(213.25,15.50),(212.75,15.50)],.40),
 'CAP_DL_21275':('CAP',(212.75,19.25),[(213.99,17.255),(213.25,17.255),(213.25,19.25),(212.75,19.25)],.40),
}
def iu(x):return pcbnew.FromMM(float(x))
def P(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def net(b):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()=='12V_ACT':return p.GetNet()
 raise SystemExit('missing')
def seg(b,n,l,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(l);t.SetWidth(iu(w));t.SetStart(P(*a));t.SetEnd(P(*z));b.Add(t)
def via(b,n,p):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(P(*p));v.SetWidth(iu(.9));v.SetDrill(iu(.45));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def main():
 out={}
 with tempfile.TemporaryDirectory(prefix='pr20a_co2fast_') as td:
  td=Path(td)
  for name,(kind,vp,pts,w) in VARS.items():
   b=pcbnew.LoadBoard(str(PCB));n=net(b);via(b,n,vp)
   for a,z in zip(pts,pts[1:]):seg(b,n,pcbnew.F_Cu,a,z,w)
   # stub corto en In2, hacia el exterior del bloque
   dx=2.0 if vp[0]>=213.99 else -2.0;seg(b,n,pcbnew.In2_Cu,vp,(vp[0]+dx,vp[1]),1.0)
   p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
   d=json.loads(r.read_text());e=[x for x in d.get('violations',[]) if x.get('severity')=='error']
   out[name]={'kind':kind,'errors':len(e),'types':dict(Counter(x.get('type','?') for x in e)),'first':e[:3]}
 print('CO2_MICRO_FAST',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print('CO2_MICRO_FAST_GOOD',[k for k,v in out.items() if v['errors']==0])
if __name__=='__main__':main()
