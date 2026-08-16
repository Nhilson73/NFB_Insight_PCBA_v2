#!/usr/bin/env python3
"""Micro-DRC de vía 12V_ACT solapada con C_CO2_DRV.1."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
PTS=[(214.45,16.70),(214.50,16.70),(214.55,16.70),(214.45,16.75),(214.50,16.75),(214.55,16.75),(214.45,17.75),(214.50,17.75),(214.55,17.75),(214.45,17.80),(214.50,17.80),(214.55,17.80)]
def iu(x):return pcbnew.FromMM(float(x))
def P(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def net(b):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()=='12V_ACT':return p.GetNet()
 raise RuntimeError('12V_ACT')
def via(b,n,p):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(P(*p));v.SetWidth(iu(.9));v.SetDrill(iu(.45));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def main():
 out={}
 with tempfile.TemporaryDirectory(prefix='pr20a_capvia_') as td:
  td=Path(td)
  for x,y in PTS:
   b=pcbnew.LoadBoard(str(PCB));n=net(b);via(b,n,(x,y))
   name=f'{x:.2f}_{y:.2f}'.replace('.','p');p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
   d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
   out[name]={'x':x,'y':y,'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'first':e[:4]}
 print('CO2_CAP_VIA',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print('CO2_CAP_VIA_GOOD',[k for k,v in out.items() if v['errors']==0])
 if not any(v['errors']==0 for v in out.values()):raise SystemExit('ERROR: no hay vía-en-pad DRC=0')
if __name__=='__main__':main()
