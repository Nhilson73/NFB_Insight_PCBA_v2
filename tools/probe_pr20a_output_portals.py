#!/usr/bin/env python3
"""Micro-DRC de portales QFN para PUMP_OUT1/2 y CO2_SOL_POS."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
import run_pr20a_power_router_v8 as v8
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
VARS={
 'OUT1_A':('PUMP_OUT1',[((209.025,19.825),(207.75,19.825),.2),((209.025,20.325),(207.75,20.325),.2),((207.75,19.825),(207.75,20.325),.2),((207.75,20.075),(206.5,20.075),.4)],(206.5,20.075)),
 'OUT1_B':('PUMP_OUT1',[((209.025,19.825),(207.5,19.825),.2),((209.025,20.325),(207.5,20.325),.2),((207.5,19.825),(207.5,20.325),.2),((207.5,20.075),(206.0,20.075),.4)],(206.0,20.075)),
 'OUT1_C':('PUMP_OUT1',[((209.025,19.825),(207.75,19.825),.2),((209.025,20.325),(207.75,20.325),.2),((207.75,19.825),(207.75,20.325),.2),((207.75,20.075),(207.75,21.25),.4)],(207.75,21.25)),
 'OUT2_A':('PUMP_OUT2',[((212.325,19.825),(213.75,19.825),.2),((212.325,20.325),(213.75,20.325),.2),((213.75,19.825),(213.75,20.325),.2),((213.75,20.075),(214.75,20.075),.4)],(214.75,20.075)),
 'OUT2_B':('PUMP_OUT2',[((212.325,19.825),(213.75,19.825),.2),((212.325,20.325),(213.75,20.325),.2),((213.75,19.825),(213.75,20.325),.2),((213.75,20.075),(213.75,21.25),.4)],(213.75,21.25)),
 'OUT2_C':('PUMP_OUT2',[((212.325,19.825),(214.0,19.825),.2),((212.325,20.325),(214.0,20.325),.2),((214.0,19.825),(214.0,20.325),.2),((214.0,20.075),(215.0,20.075),.4)],(215.0,20.075)),
 'CO2_A':('CO2_SOL_POS',[((218.82,17.875),(219.4,17.875),.2),((219.4,17.875),(219.4,15.5),.2),((219.4,15.5),(222.0,15.5),.4)],(222.0,15.5)),
 'CO2_B':('CO2_SOL_POS',[((218.82,17.875),(219.2,17.875),.2),((219.2,17.875),(219.2,15.0),.2),((219.2,15.0),(222.0,15.0),.4)],(222.0,15.0)),
 'CO2_C':('CO2_SOL_POS',[((218.82,17.875),(219.4,17.875),.2),((219.4,17.875),(219.4,20.5),.2),((219.4,20.5),(221.5,20.5),.4)],(221.5,20.5)),
}
def iu(x):return pcbnew.FromMM(float(x))
def P(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def net(b,name):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()==name:return p.GetNet()
 raise RuntimeError(name)
def seg(b,n,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(pcbnew.F_Cu);t.SetWidth(iu(w));t.SetStart(P(*a));t.SetEnd(P(*z));b.Add(t)
def via(b,n,p):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(P(*p));v.SetWidth(iu(.9));v.SetDrill(iu(.45));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def main():
 out={}
 with tempfile.TemporaryDirectory(prefix='pr20a_outputs_') as td:
  td=Path(td)
  for name,(nn,tracks,vp) in VARS.items():
   b=pcbnew.LoadBoard(str(PCB));v8.apply_co2_access_eco(b);n=net(b,nn)
   for a,z,w in tracks:seg(b,n,a,z,w)
   via(b,n,vp)
   p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
   d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
   out[name]={'net':nn,'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'first':e[:5]}
 print('OUTPUT_PORTALS',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print('OUTPUT_PORTALS_GOOD',[k for k,v in out.items() if v['errors']==0])
if __name__=='__main__':main()
