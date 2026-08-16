#!/usr/bin/env python3
"""Prueba mínima CO2 para PR20A.

Mantiene CO2_EN_DRV intacto. Solo desvía la diagonal B.Cu de CO2_OPENLOAD_N
para liberar el portal de U_CO2_DRV.8. C_CO2_DRV.1 sale por F.Cu hacia una vía
por debajo de la vía CO2_EN y ambos puntos 12V_ACT se unen en In2.Cu.
"""
from __future__ import annotations
import json,subprocess,tempfile,shutil,math
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
 b=pcbnew.LoadBoard(str(PCB));ol=getnet(b,'CO2_OPENLOAD_N');act=getnet(b,'12V_ACT')
 old=canon((219.8,16.0),(218.5,20.8));removed=[]
 for t in list(b.GetTracks()):
  if isinstance(t,pcbnew.PCB_VIA) or t.GetNetname()!='CO2_OPENLOAD_N' or t.GetLayer()!=pcbnew.B_Cu:continue
  a,z=t.GetStart(),t.GetEnd();A=(mm(a.x),mm(a.y));Z=(mm(z.x),mm(z.y))
  if canon(A,Z)==old:removed.append([A,Z]);b.Remove(t)
 if len(removed)!=1:raise SystemExit(f'ERROR: diagonal OPENLOAD esperada 1, got {removed}')
 # Detour local a la izquierda del portal power, manteniendo ambos endpoints/vías históricos.
 olpts=[(219.8,16.0),(218.8,16.0),(218.8,19.75),(218.5,20.8)]
 for a,z in zip(olpts,olpts[1:]):seg(b,ol,pcbnew.B_Cu,a,z,.2)
 # Portal pin8 validado casi completo en probes anteriores; ahora libre de la diagonal B.
 via(b,act,(219.9,18.45));seg(b,act,pcbnew.F_Cu,(218.82,18.375),(219.9,18.45),.2)
 # C_CO2_DRV.1: escape por debajo de ACT_FAULT local y R_CO2_EN_PD.
 cappts=[(213.99,17.255),(213.0,18.5),(213.0,22.75),(214.0,22.75)]
 for a,z in zip(cappts,cappts[1:]):seg(b,act,pcbnew.F_Cu,a,z,.4)
 via(b,act,(214.0,22.75))
 # Backbone local In2 por debajo de las vías ACT_FAULT/PUMP_CURRENT/OPENLOAD.
 pwr=[(214.0,22.75),(214.0,24.5),(221.5,24.5),(221.5,18.45),(219.9,18.45)]
 for a,z in zip(pwr,pwr[1:]):seg(b,act,pcbnew.In2_Cu,a,z,1.0)
 with tempfile.TemporaryDirectory(prefix='pr20a_co2minimal_') as td:
  td=Path(td);p=td/'co2minimal.kicad_pcb';r=td/'co2minimal.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/'co2minimal.kicad_dru')
  subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
  d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
  un=[q for q in d.get('unconnected_items',[]) if any(x in json.dumps(q) for x in ('CO2_OPENLOAD_N','12V_ACT'))]
  out={'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'target_unconnected':len(un),'first':e[:20],'removed':removed}
  print('CO2_MINIMAL_POWER',json.dumps(out,ensure_ascii=False,separators=(',',':')))
  if e:raise SystemExit('ERROR: solución mínima CO2 no DRC=0')
if __name__=='__main__':main()
