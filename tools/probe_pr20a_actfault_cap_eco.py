#!/usr/bin/env python3
"""Valida ECO local ACT_FAULT_N + alimentación F.Cu de C_CO2_DRV.1."""
from __future__ import annotations
import json,subprocess,tempfile,shutil,math
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'

def iu(x):return pcbnew.FromMM(float(x))
def mm(v):return round(float(pcbnew.ToMM(v)),3)
def P(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def key(a,z):return frozenset(((round(a[0],3),round(a[1],3)),(round(z[0],3),round(z[1],3))))
def findnet(b,name):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()==name:return p.GetNet()
 raise RuntimeError(name)
def seg(b,n,l,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(l);t.SetWidth(iu(w));t.SetStart(P(*a));t.SetEnd(P(*z));b.Add(t)
def main():
 b=pcbnew.LoadBoard(str(PCB)); fault=findnet(b,'ACT_FAULT_N'); act=findnet(b,'12V_ACT')
 remove={
  key((212.5,16.0),(213.0,16.0)),
  key((213.0,16.0),(213.0,17.75)),
  key((213.0,16.0),(214.5,16.0)),
 }
 removed=[]
 for t in list(b.GetTracks()):
  if isinstance(t,pcbnew.PCB_VIA) or t.GetNetname()!='ACT_FAULT_N' or t.GetLayer()!=pcbnew.F_Cu:continue
  a=t.GetStart();z=t.GetEnd();A=(mm(a.x),mm(a.y));Z=(mm(z.x),mm(z.y))
  if key(A,Z) in remove:
   removed.append([A,Z]);b.Remove(t)
 # El baseline PR19C contiene la vertical (213,16)<->(213,17.75) duplicada en ambos sentidos.
 # Se retiran 4 objetos / 3 geometrías únicas y se reemplazan por una sola ruta equivalente.
 if len(removed)!=4:raise SystemExit(f'ERROR: ECO esperaba remover 4 segmentos (3 geometrías), removió {len(removed)} {removed}')
 # Nuevo ramal pump: conserva endpoint (213,17.75) y vía tree (212.5,16).
 seg(b,fault,pcbnew.F_Cu,(213.0,17.75),(211.75,17.75),.2)
 seg(b,fault,pcbnew.F_Cu,(211.75,17.75),(211.75,16.0),.2)
 seg(b,fault,pcbnew.F_Cu,(211.75,16.0),(212.5,16.0),.2)
 # Las dos vías históricas quedan unidas en B.Cu, fuera del corredor F de potencia.
 seg(b,fault,pcbnew.B_Cu,(212.5,16.0),(214.5,16.0),.2)
 # Alimentación CO2 desde C_PUMP_VM.1 por corredor superior F.Cu.
 seg(b,act,pcbnew.F_Cu,(205.52,17.255),(205.52,15.25),.5)
 seg(b,act,pcbnew.F_Cu,(205.52,15.25),(213.99,15.25),.5)
 seg(b,act,pcbnew.F_Cu,(213.99,15.25),(213.99,17.255),.5)
 with tempfile.TemporaryDirectory(prefix='pr20a_faultcap_') as td:
  td=Path(td);p=td/'faultcap.kicad_pcb';r=td/'faultcap.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/'faultcap.kicad_dru')
  subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
  d=json.loads(r.read_text());e=[x for x in d.get('violations',[]) if x.get('severity')=='error']
  un=[x for x in d.get('unconnected_items',[]) if 'ACT_FAULT_N' in json.dumps(x) or '12V_ACT' in json.dumps(x)]
  out={'errors':len(e),'types':dict(Counter(x.get('type','?') for x in e)),'target_unconnected':len(un),'first':e[:15],'removed':removed}
  print('ACTFAULT_CAP_ECO',json.dumps(out,ensure_ascii=False,separators=(',',':')))
  if e:raise SystemExit('ERROR: ECO ACT_FAULT/C_CO2 no es DRC=0')
if __name__=='__main__':main()
