#!/usr/bin/env python3
"""Busca microportales DRC=0 para U_CO2_DRV.8 y C_CO2_DRV.1 sin ECO previo."""
from __future__ import annotations
import concurrent.futures, json, math, shutil, subprocess, tempfile
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'; DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'

def iu(x): return pcbnew.FromMM(float(x))
def P(x,y): return pcbnew.VECTOR2I(iu(x),iu(y))
def getnet(b):
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()=='12V_ACT': return p.GetNet()
    raise RuntimeError('12V_ACT missing')
def seg(b,n,layer,a,z,w):
    t=pcbnew.PCB_TRACK(b); t.SetNet(n); t.SetLayer(layer); t.SetWidth(iu(w)); t.SetStart(P(*a)); t.SetEnd(P(*z)); b.Add(t)
def via(b,n,p):
    v=pcbnew.PCB_VIA(b); v.SetNet(n); v.SetPosition(P(*p)); v.SetWidth(iu(.9)); v.SetDrill(iu(.45)); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); b.Add(v)

def dogleg(b,n,start,end,w,mode):
    sx,sy=start; ex,ey=end
    if mode=='H':
        seg(b,n,pcbnew.F_Cu,start,(ex,sy),w); seg(b,n,pcbnew.F_Cu,(ex,sy),end,w)
    else:
        seg(b,n,pcbnew.F_Cu,start,(sx,ey),w); seg(b,n,pcbnew.F_Cu,(sx,ey),end,w)

def evaluate(args):
    kind,x,y,mode,td=args; td=Path(td)
    b=pcbnew.LoadBoard(str(PCB)); n=getnet(b)
    if kind=='PIN': start=(218.82,18.375); w=.20
    else: start=(213.99,17.255); w=.50
    via(b,n,(x,y)); dogleg(b,n,start,(x,y),w,mode)
    # pequeño stub In2 alejándose del bloque para demostrar acceso al backbone.
    dx=2.0 if x>=start[0] else -2.0
    seg(b,n,pcbnew.In2_Cu,(x,y),(x+dx,y),1.0)
    name=f'{kind}_{x:.2f}_{y:.2f}_{mode}'.replace('.','p')
    p=td/f'{name}.kicad_pcb'; r=td/f'{name}.json'; pcbnew.SaveBoard(str(p),b); shutil.copyfile(DRU,td/f'{name}.kicad_dru')
    subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
    d=json.loads(r.read_text(encoding='utf-8')); e=[q for q in d.get('violations',[]) if q.get('severity')=='error']
    return {'kind':kind,'x':x,'y':y,'mode':mode,'errors':len(e),'types':dict(Counter(q.get('type','?') for q in e)),'first':e[:2]}

def frange(a,b,step):
    n=int(round((b-a)/step)); return [round(a+i*step,2) for i in range(n+1)]

def main():
    jobs=[]
    # Pin 8: buscar solo a derecha/abajo/arriba inmediatos, antes o alrededor del muro ILIM.
    for x in frange(219.25,220.50,.25):
      for y in frange(18.25,19.75,.25):
        for mode in ('H','V'): jobs.append(('PIN',x,y,mode,None))
    # C_CO2_DRV.1: halo local, priorizando izquierda/arriba/abajo del capacitor.
    for x in frange(211.50,215.00,.50):
      for y in frange(14.50,20.00,.50):
        for mode in ('H','V'): jobs.append(('CAP',x,y,mode,None))
    out=[]
    with tempfile.TemporaryDirectory(prefix='pr20a_co2micro_') as td:
        jobs=[(k,x,y,m,td) for k,x,y,m,_ in jobs]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            for r in ex.map(evaluate,jobs): out.append(r)
    good=[r for r in out if r['errors']==0]
    good.sort(key=lambda r:(r['kind'], abs(r['x']-(218.82 if r['kind']=='PIN' else 213.99))+abs(r['y']-(18.375 if r['kind']=='PIN' else 17.255)),r['x'],r['y'],r['mode']))
    best={'PIN':[r for r in good if r['kind']=='PIN'][:20],'CAP':[r for r in good if r['kind']=='CAP'][:20]}
    hist=Counter((r['kind'],r['errors']) for r in out)
    print('CO2_MICROVIA_GOOD',json.dumps(best,ensure_ascii=False,separators=(',',':')))
    print('CO2_MICROVIA_COUNTS',dict((f'{k[0]}:{k[1]}',v) for k,v in sorted(hist.items())))
    if not best['PIN'] or not best['CAP']:
        # mostrar mejores candidatos no verdes para dirigir el siguiente ajuste
        for kind in ('PIN','CAP'):
            q=sorted((r for r in out if r['kind']==kind),key=lambda r:(r['errors'],abs(r['x']-(218.82 if kind=='PIN' else 213.99))+abs(r['y']-(18.375 if kind=='PIN' else 17.255))))[:10]
            print('CO2_MICROVIA_BEST_'+kind,json.dumps(q,ensure_ascii=False,separators=(',',':')))
        raise SystemExit('ERROR: faltan microportales DRC=0')
if __name__=='__main__': main()
