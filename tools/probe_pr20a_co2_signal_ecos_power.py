#!/usr/bin/env python3
"""Prueba dos ECOs locales B.Cu y la isla 12V_ACT CO2 resultante.

- CO2_EN_DRV: conserva las dos vías y endpoints; solo desvía sus dos tramos B originales.
- CO2_OPENLOAD_N: conserva vías/endpoints; desvía la diagonal B al exterior derecho.
- 12V_ACT: vía-en-pad C_CO2_DRV.1 + vía de clase junto a U_CO2_DRV.8, unidas en In2.
"""
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
def net(b,name):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()==name:return p.GetNet()
 raise RuntimeError(name)
def addseg(b,n,l,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(l);t.SetWidth(iu(w));t.SetStart(P(*a));t.SetEnd(P(*z));b.Add(t)
def addvia(b,n,p,d=.9,dr=.45):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(P(*p));v.SetWidth(iu(d));v.SetDrill(iu(dr));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def remove_segments(b,tracks,name,layer,geoms):
 want={canon(*g) for g in geoms};got=[]
 for t in tracks:
  if isinstance(t,pcbnew.PCB_VIA) or t.GetNetname()!=name or t.GetLayer()!=layer:continue
  a,z=t.GetStart(),t.GetEnd();A=(mm(a.x),mm(a.y));Z=(mm(z.x),mm(z.y))
  if canon(A,Z) in want:got.append([A,Z]);b.Remove(t)
 if {canon(*g) for g in got}!=want:raise SystemExit(f'ERROR: {name} baseline inesperado removed={got}')
 return got
def main():
 b=pcbnew.LoadBoard(str(PCB));en=net(b,'CO2_EN_DRV');ol=net(b,'CO2_OPENLOAD_N');act=net(b,'12V_ACT')
 # Snapshot único: pcbnew/SWIG puede invalidar Tracks() después de Remove().
 tracks=list(b.GetTracks())
 rem_en=remove_segments(b,tracks,'CO2_EN_DRV',pcbnew.B_Cu,[((216.8,15.2),(213.705,15.2)),((213.705,15.2),(213.705,21.5))])
 rem_ol=remove_segments(b,tracks,'CO2_OPENLOAD_N',pcbnew.B_Cu,[((219.8,16.0),(218.5,20.8))])
 # rodear CO2_EN por debajo del extremo ACT_FAULT_N en y22.5
 for a,z in zip([(216.8,15.2),(211.0,15.2),(211.0,23.25),(213.705,23.25)],[(211.0,15.2),(211.0,23.25),(213.705,23.25),(213.705,21.5)]):addseg(b,en,pcbnew.B_Cu,a,z,.2)
 # CO2_OPENLOAD al exterior derecho, lejos de la ventana de potencia x219.9/y18.45
 for a,z in zip([(219.8,16.0),(223.0,16.0),(223.0,22.5),(218.5,22.5)],[(223.0,16.0),(223.0,22.5),(218.5,22.5),(218.5,20.8)]):addseg(b,ol,pcbnew.B_Cu,a,z,.2)
 # isla power: vía-en-pad del capacitor y portal del pin8, ambas de clase 0.9/0.45
 addvia(b,act,(213.99,17.255)); addvia(b,act,(219.9,18.45))
 addseg(b,act,pcbnew.F_Cu,(218.82,18.375),(219.9,18.45),.2)
 addseg(b,act,pcbnew.In2_Cu,(213.99,17.255),(219.9,18.45),1.0)
 with tempfile.TemporaryDirectory(prefix='pr20a_co2ecos_') as td:
  td=Path(td);p=td/'co2ecos.kicad_pcb';r=td/'co2ecos.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/'co2ecos.kicad_dru')
  subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
  d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
  un=[q for q in d.get('unconnected_items',[]) if any(x in json.dumps(q) for x in ('CO2_EN_DRV','CO2_OPENLOAD_N','12V_ACT'))]
  out={'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'target_unconnected':len(un),'first':e[:20],'removed_en':rem_en,'removed_openload':rem_ol}
  print('CO2_SIGNAL_ECOS_POWER',json.dumps(out,ensure_ascii=False,separators=(',',':')))
  if e:raise SystemExit('ERROR: ECOs CO2 + isla power no son DRC=0')
if __name__=='__main__':main()
