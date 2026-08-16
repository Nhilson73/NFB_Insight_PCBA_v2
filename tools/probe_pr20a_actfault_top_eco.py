#!/usr/bin/env python3
"""Micro-DRC: ECO solo F.Cu de ACT_FAULT_N para abrir C_CO2_DRV.1."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
def iu(x):return pcbnew.FromMM(float(x))
def mm(v):return round(float(pcbnew.ToMM(v)),3)
def P(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def canon(a,z):return frozenset(((round(a[0],3),round(a[1],3)),(round(z[0],3),round(z[1],3))))
def getnet(b,name):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()==name:return p.GetNet()
 raise RuntimeError(name)
def seg(b,n,l,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(l);t.SetWidth(iu(w));t.SetStart(P(*a));t.SetEnd(P(*z));b.Add(t)
def main():
 b=pcbnew.LoadBoard(str(PCB));fault=getnet(b,'ACT_FAULT_N');act=getnet(b,'12V_ACT')
 targets={canon((212.5,16),(213,16)),canon((213,16),(213,17.75)),canon((213,16),(214.5,16))}
 removed=[]
 for t in list(b.GetTracks()):
  if isinstance(t,pcbnew.PCB_VIA) or t.GetNetname()!='ACT_FAULT_N' or t.GetLayer()!=pcbnew.F_Cu:continue
  a,z=t.GetStart(),t.GetEnd();A=(mm(a.x),mm(a.y));Z=(mm(z.x),mm(z.y))
  if canon(A,Z) in targets:removed.append([A,Z]);b.Remove(t)
 # PR19C dejó duplicada la vertical 213/16<->213/17.75: 4 objetos / 3 geometrías.
 if len(removed)!=4:raise SystemExit(f'ERROR: esperaba 4 segmentos ACT_FAULT, got {removed}')
 # Pump pad -> vía izquierda, manteniéndose a la izquierda del corredor power.
 for a,z in zip([(213,17.75),(211.75,17.75),(211.75,16),(212.5,16)],[(211.75,17.75),(211.75,16),(212.5,16),(212.5,16)]):
  if a!=z:seg(b,fault,pcbnew.F_Cu,a,z,.2)
 # Conectar las vías 212.5/16 y 214.5/16 por arriba, solo F.Cu.
 fault_top=[(212.5,16),(212.5,13.0),(214.5,13.0),(214.5,16)]
 for a,z in zip(fault_top,fault_top[1:]):seg(b,fault,pcbnew.F_Cu,a,z,.2)
 # 12V_ACT desde C_PUMP_VM.1: backbone 1 mm hasta portal superior y neck-down local
 # para atravesar el encapsulado de señales sin relajar clearance.
 pwr=[
  ((205.52,17.255),(205.52,12.0),1.0,'backbone'),
  ((205.52,12.0),(212.0,12.0),1.0,'backbone'),
  ((212.0,12.0),(213.55,13.5),0.4,'local_escape'),
  ((213.55,13.5),(213.55,17.255),0.4,'local_escape'),
  ((213.55,17.255),(213.99,17.255),0.4,'local_escape'),
 ]
 for a,z,w,_ in pwr:seg(b,act,pcbnew.F_Cu,a,z,w)
 with tempfile.TemporaryDirectory(prefix='pr20a_faulttop_') as td:
  td=Path(td);p=td/'faulttop.kicad_pcb';r=td/'faulttop.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/'faulttop.kicad_dru')
  subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
  d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
  un=[q for q in d.get('unconnected_items',[]) if any(x in json.dumps(q) for x in ('ACT_FAULT_N','12V_ACT'))]
  print('ACTFAULT_TOP_ECO',json.dumps({'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'target_unconnected':len(un),'first':e[:20],'removed':removed},ensure_ascii=False,separators=(',',':')))
  if e:raise SystemExit('ERROR: ECO F ACT_FAULT + cap CO2 no DRC=0')
if __name__=='__main__':main()
