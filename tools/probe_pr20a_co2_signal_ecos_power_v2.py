#!/usr/bin/env python3
"""Segunda prueba: ECOs CO2 por exterior + isla 12V_ACT con dogleg In2."""
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
def via(b,n,p,d=.9,dr=.45):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(P(*p));v.SetWidth(iu(d));v.SetDrill(iu(dr));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def main():
 b=pcbnew.LoadBoard(str(PCB));en=getnet(b,'CO2_EN_DRV');ol=getnet(b,'CO2_OPENLOAD_N');act=getnet(b,'12V_ACT');tracks=list(b.GetTracks())
 targets={
  'CO2_EN_DRV':{canon((216.8,15.2),(213.705,15.2)),canon((213.705,15.2),(213.705,21.5))},
  'CO2_OPENLOAD_N':{canon((219.8,16.0),(218.5,20.8))},
 }
 got={k:[] for k in targets}
 for t in tracks:
  if isinstance(t,pcbnew.PCB_VIA) or t.GetLayer()!=pcbnew.B_Cu or t.GetNetname() not in targets:continue
  a,z=t.GetStart(),t.GetEnd();A=(mm(a.x),mm(a.y));Z=(mm(z.x),mm(z.y));k=canon(A,Z)
  if k in targets[t.GetNetname()]:got[t.GetNetname()].append([A,Z]);b.Remove(t)
 for name,want in targets.items():
  if {canon(*g) for g in got[name]}!=want:raise SystemExit(f'ERROR baseline {name}: {got[name]}')
 # CO2_EN: rodeo exterior derecho y regreso por y24.5, por debajo de ACT_FAULT local.
 enpts=[(216.8,15.2),(228.0,15.2),(228.0,24.5),(213.705,24.5),(213.705,21.5)]
 for a,z in zip(enpts,enpts[1:]):seg(b,en,pcbnew.B_Cu,a,z,.2)
 # OPENLOAD: sube desde su vía, pasa por y12.5 y baja por x226; evita CO2_SOL_CTL @223.5,16.
 olpts=[(219.8,16.0),(219.8,12.5),(226.0,12.5),(226.0,22.5),(218.5,22.5),(218.5,20.8)]
 for a,z in zip(olpts,olpts[1:]):seg(b,ol,pcbnew.B_Cu,a,z,.2)
 # Isla power: cap vía-en-pad y pin8. Dogleg In2 por y11.0 para evitar vías PUMP_CURRENT/ACT_FAULT y rutas B exteriores.
 via(b,act,(213.99,17.255));via(b,act,(219.9,18.45))
 seg(b,act,pcbnew.F_Cu,(218.82,18.375),(219.9,18.45),.2)
 pwr=[(213.99,17.255),(213.99,11.0),(222.0,11.0),(222.0,18.45),(219.9,18.45)]
 for a,z in zip(pwr,pwr[1:]):seg(b,act,pcbnew.In2_Cu,a,z,1.0)
 with tempfile.TemporaryDirectory(prefix='pr20a_co2ecos2_') as td:
  td=Path(td);p=td/'co2ecos2.kicad_pcb';r=td/'co2ecos2.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/'co2ecos2.kicad_dru')
  subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
  d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
  un=[q for q in d.get('unconnected_items',[]) if any(x in json.dumps(q) for x in ('CO2_EN_DRV','CO2_OPENLOAD_N','12V_ACT'))]
  print('CO2_ECOS_POWER_V2',json.dumps({'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'target_unconnected':len(un),'first':e[:20]},ensure_ascii=False,separators=(',',':')))
  if e:raise SystemExit('ERROR: v2 no DRC=0')
if __name__=='__main__':main()
