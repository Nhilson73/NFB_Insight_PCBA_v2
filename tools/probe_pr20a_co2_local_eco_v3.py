#!/usr/bin/env python3
"""Prueba combinada CO2 v3 para PR20A.

- CO2_EN_DRV: mueve solo la vía inferior/ramal asociado; mantiene vía superior.
- CO2_OPENLOAD_N: sustituye solo su diagonal B.Cu local.
- 12V_ACT: vía de clase en C_CO2_DRV.1 y portal de clase en U_CO2_DRV.8,
  unidos en In2.Cu sin alterar placement ni otras nets.
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
def via(b,n,p,d,dr):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(P(*p));v.SetWidth(iu(d));v.SetDrill(iu(dr));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def near(a,b,tol=.08):return math.hypot(a[0]-b[0],a[1]-b[1])<=tol
def main():
 b=pcbnew.LoadBoard(str(PCB));en=getnet(b,'CO2_EN_DRV');ol=getnet(b,'CO2_OPENLOAD_N');act=getnet(b,'12V_ACT')
 tracks=list(b.GetTracks())
 # Retirar exactamente los dos segmentos B del ramal inferior CO2_EN y su F vertical al pull-down.
 en_geoms={canon((216.8,15.2),(213.705,15.2)),canon((213.705,15.2),(213.705,21.5))}
 ol_geom=canon((219.8,16.0),(218.5,20.8));removed_en=[];removed_ol=[];removed_f=[];old_via=None
 for t in tracks:
  if isinstance(t,pcbnew.PCB_VIA):
   if t.GetNetname()=='CO2_EN_DRV':
    q=t.GetPosition();p=(mm(q.x),mm(q.y))
    if near(p,(213.75,21.5),.12):old_via=t
   continue
  a,z=t.GetStart(),t.GetEnd();A=(mm(a.x),mm(a.y));Z=(mm(z.x),mm(z.y));k=canon(A,Z)
  if t.GetNetname()=='CO2_EN_DRV' and t.GetLayer()==pcbnew.B_Cu and k in en_geoms:removed_en.append([A,Z]);b.Remove(t)
  elif t.GetNetname()=='CO2_EN_DRV' and t.GetLayer()==pcbnew.F_Cu and k==canon((213.705,21.5),(213.705,20.045)):removed_f.append([A,Z]);b.Remove(t)
  elif t.GetNetname()=='CO2_OPENLOAD_N' and t.GetLayer()==pcbnew.B_Cu and k==ol_geom:removed_ol.append([A,Z]);b.Remove(t)
 if len(removed_en)!=2 or len(removed_ol)!=1 or len(removed_f)!=1 or old_via is None:
  raise SystemExit(f'ERROR baseline ECO en={removed_en} ol={removed_ol} f={removed_f} via={old_via is not None}')
 b.Remove(old_via)
 # CO2_EN: desde vía superior, rodea ACT_FAULT por la derecha hasta y19.5,
 # cruza a x216.25 tras terminar ACT_FAULT vertical y baja a nueva vía.
 enpts=[(216.8,15.2),(218.0,15.2),(218.0,19.5),(216.25,19.5),(216.25,23.0)]
 for a,z in zip(enpts,enpts[1:]):seg(b,en,pcbnew.B_Cu,a,z,.2)
 via(b,en,(216.25,23.0),.6,.3)
 # F del pull-down por debajo del bloque.
 for a,z in zip([(213.705,20.045),(213.705,23.0),(216.25,23.0)],[(213.705,23.0),(216.25,23.0),(216.25,23.0)]):
  if a!=z:seg(b,en,pcbnew.F_Cu,a,z,.2)
 # OPENLOAD: detour local a la izquierda del portal power.
 olpts=[(219.8,16.0),(218.8,16.0),(218.8,19.75),(218.5,20.8)]
 for a,z in zip(olpts,olpts[1:]):seg(b,ol,pcbnew.B_Cu,a,z,.2)
 # Power: cap via-in-pad de clase + portal pin8 de clase.
 via(b,act,(213.99,17.255),.9,.45)
 via(b,act,(219.9,18.45),.9,.45)
 seg(b,act,pcbnew.F_Cu,(218.82,18.375),(219.9,18.45),.2)
 # Enlace local In2 por y24.5, por debajo de las vías locales.
 pwr=[(213.99,17.255),(213.99,24.5),(221.5,24.5),(221.5,18.45),(219.9,18.45)]
 for a,z in zip(pwr,pwr[1:]):seg(b,act,pcbnew.In2_Cu,a,z,1.0)
 with tempfile.TemporaryDirectory(prefix='pr20a_co2v3_') as td:
  td=Path(td);p=td/'co2v3.kicad_pcb';r=td/'co2v3.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/'co2v3.kicad_dru')
  subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
  d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
  un=[q for q in d.get('unconnected_items',[]) if any(x in json.dumps(q) for x in ('CO2_EN_DRV','CO2_OPENLOAD_N','12V_ACT'))]
  out={'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'target_unconnected':len(un),'first':e[:25]}
  print('CO2_LOCAL_ECO_V3',json.dumps(out,ensure_ascii=False,separators=(',',':')))
  if e:raise SystemExit('ERROR: CO2 local ECO v3 no DRC=0')
if __name__=='__main__':main()
