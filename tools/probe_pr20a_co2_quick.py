#!/usr/bin/env python3
"""Probe secuencial corto para cerrar localmente 12V_ACT en la isla CO2."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
CAPS={
 'DIRECT':[(205.52,17.255),(213.99,17.255)],
 'Y17_0':[(205.52,17.255),(206.25,17.0),(213.25,17.0),(213.99,17.255)],
 'Y17_5':[(205.52,17.255),(206.25,17.5),(213.25,17.5),(213.99,17.255)],
 'Y16_75':[(205.52,17.255),(206.25,16.75),(212.75,16.75),(213.99,17.255)],
 'Y17_75':[(205.52,17.255),(206.25,17.75),(212.75,17.75),(213.99,17.255)],
}
PINS=[(219.80,18.40),(219.825,18.40),(219.85,18.40),(219.875,18.40),(219.85,18.45),(219.875,18.45),(219.90,18.45)]
def iu(x):return pcbnew.FromMM(float(x))
def P(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def net(b):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()=='12V_ACT':return p.GetNet()
 raise RuntimeError('12V_ACT')
def seg(b,n,l,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(l);t.SetWidth(iu(w));t.SetStart(P(*a));t.SetEnd(P(*z));b.Add(t)
def via(b,n,p):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(P(*p));v.SetWidth(iu(.9));v.SetDrill(iu(.45));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def drc(board,name,td):
 p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),board);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
 subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
 d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
 return {'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'first':e[:4]}
def main():
 out={'caps':{},'pins':{}}
 with tempfile.TemporaryDirectory(prefix='pr20a_co2quick_') as x:
  td=Path(x)
  for name,pts in CAPS.items():
   b=pcbnew.LoadBoard(str(PCB));n=net(b)
   for a,z in zip(pts,pts[1:]):seg(b,n,pcbnew.F_Cu,a,z,.40 if name!='DIRECT' else .50)
   out['caps'][name]=drc(b,'CAP_'+name,td)
  for x,y in PINS:
   name=f'{x:.3f}_{y:.3f}'.replace('.','p');b=pcbnew.LoadBoard(str(PCB));n=net(b)
   via(b,n,(x,y));seg(b,n,pcbnew.F_Cu,(218.82,18.375),(x,y),.20)
   # solo prueba portal; no se añade troncal In2 aquí para separar el problema de la vía del del backbone.
   out['pins'][name]=drc(b,'PIN_'+name,td)
 print('CO2_QUICK',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print('CO2_QUICK_CAP_GOOD',[k for k,v in out['caps'].items() if v['errors']==0])
 print('CO2_QUICK_PIN_GOOD',[k for k,v in out['pins'].items() if v['errors']==0])
 if not any(v['errors']==0 for v in out['caps'].values()) or not any(v['errors']==0 for v in out['pins'].values()):raise SystemExit('ERROR: probe rápido no cerró ambos portales')
if __name__=='__main__':main()
