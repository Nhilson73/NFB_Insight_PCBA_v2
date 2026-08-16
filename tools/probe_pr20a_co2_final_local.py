#!/usr/bin/env python3
"""Micro-DRC focalizado: alimentación lateral C_CO2_DRV y microportal fino U_CO2_DRV.8."""
from __future__ import annotations
import concurrent.futures,json,shutil,subprocess,tempfile
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1]; PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'; DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'

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
def run_variant(arg):
 kind,name,cfg,td=arg;td=Path(td);b=pcbnew.LoadBoard(str(PCB));n=net(b)
 if kind=='CAP':
  pts,w=cfg
  for a,z in zip(pts,pts[1:]):seg(b,n,pcbnew.F_Cu,a,z,w)
 elif kind=='PIN':
  x,y=cfg;via(b,n,(x,y));seg(b,n,pcbnew.F_Cu,(218.82,18.375),(x,y),.20)
  # stub In2 de 1 mm hacia la derecha; prueba que el portal puede incorporarse a backbone.
  seg(b,n,pcbnew.In2_Cu,(x,y),(x+1.5,y),1.0)
 p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
 subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
 d=json.loads(r.read_text());e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
 return {'kind':kind,'name':name,'cfg':cfg,'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'first':e[:3]}
def main():
 jobs=[]
 # Cap: primero la línea lateral directa; luego ligeros doglegs por arriba/abajo sin tocar Y=16 ni Y=18.325.
 caps={
  'CAP_DIRECT':([(205.52,17.255),(213.99,17.255)],.50),
  'CAP_Y169':([(205.52,17.255),(206.5,16.9),(213.0,16.9),(213.99,17.255)],.40),
  'CAP_Y176':([(205.52,17.255),(206.5,17.6),(213.0,17.6),(213.99,17.255)],.40),
  'CAP_Y168':([(205.52,17.255),(206.5,16.8),(212.5,16.8),(213.99,17.255)],.40),
  'CAP_Y177':([(205.52,17.255),(206.5,17.7),(212.5,17.7),(213.99,17.255)],.40),
 }
 for name,cfg in caps.items():jobs.append(('CAP',name,cfg,None))
 # Pin: barrido fino entre B.Cu CO2_OPENLOAD_N y muro F.Cu CO2_ILIM.
 for ix in range(219775,220001,25):
  x=ix/1000.0
  for iy in range(18300,18601,50):
   y=iy/1000.0;name=f'PIN_{x:.3f}_{y:.3f}'.replace('.','p');jobs.append(('PIN',name,(x,y),None))
 out=[]
 with tempfile.TemporaryDirectory(prefix='pr20a_co2final_') as td:
  jobs=[(a,b,c,td) for a,b,c,_ in jobs]
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
   for r in ex.map(run_variant,jobs):out.append(r)
 good=[r for r in out if r['errors']==0]
 gc=[r for r in good if r['kind']=='CAP'];gp=[r for r in good if r['kind']=='PIN']
 gp.sort(key=lambda r:(abs(r['cfg'][0]-218.82)+abs(r['cfg'][1]-18.375),r['cfg']))
 print('CO2_FINAL_CAP_GOOD',json.dumps(gc,ensure_ascii=False,separators=(',',':')))
 print('CO2_FINAL_PIN_GOOD',json.dumps(gp[:20],ensure_ascii=False,separators=(',',':')))
 if not gc:
  q=sorted((r for r in out if r['kind']=='CAP'),key=lambda r:r['errors']);print('CO2_FINAL_CAP_BEST',json.dumps(q[:5],ensure_ascii=False,separators=(',',':')))
 if not gp:
  q=sorted((r for r in out if r['kind']=='PIN'),key=lambda r:(r['errors'],abs(r['cfg'][0]-219.85)+abs(r['cfg'][1]-18.4)));print('CO2_FINAL_PIN_BEST',json.dumps(q[:10],ensure_ascii=False,separators=(',',':')))
 if not gc or not gp:raise SystemExit('ERROR: falta solución local CO2 DRC=0')
if __name__=='__main__':main()
