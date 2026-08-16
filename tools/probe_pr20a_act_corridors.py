#!/usr/bin/env python3
"""Barrido DRC de columnas In2 para el backbone 12V_ACT en Z4."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1]; PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'; DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
XS=[199.5,201.0,202.5,204.0,205.5,207.0,208.5,210.0,211.5,213.0,214.5,216.0,218.0,220.0,222.0,224.0,226.0,228.0,230.0,232.0,234.0,236.0,238.0,240.0]
def iu(x):return pcbnew.FromMM(float(x))
def V(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def net(b,name):
 for fp in b.GetFootprints():
  for p in fp.Pads():
   if p.GetNetname()==name:return p.GetNet()
 raise SystemExit('net missing')
def seg(b,n,l,a,z,w=1.0):
 t=pcbnew.PCB_TRACK(b);t.SetNet(n);t.SetLayer(l);t.SetWidth(iu(w));t.SetStart(V(*a));t.SetEnd(V(*z));b.Add(t)
def via(b,n,p):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(V(*p));v.SetWidth(iu(.9));v.SetDrill(iu(.45));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def main():
 out={}
 with tempfile.TemporaryDirectory(prefix='pr20a_act_') as td:
  td=Path(td)
  for x in XS:
   b=pcbnew.LoadBoard(str(PCB));n=net(b,'12V_ACT')
   # acceso desde F_ACT.2 hacia corredor superior, transición a In2 y columna Z4
   seg(b,n,pcbnew.F_Cu,(175.118,53.875),(175.118,63.0));via(b,n,(175.118,63.0))
   seg(b,n,pcbnew.In2_Cu,(175.118,63.0),(x,63.0));seg(b,n,pcbnew.In2_Cu,(x,63.0),(x,12.0))
   p=td/f'x{x:.1f}.kicad_pcb';r=td/f'x{x:.1f}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'x{x:.1f}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
   d=json.loads(r.read_text());e=[v for v in d.get('violations',[]) if v.get('severity')=='error']
   out[str(x)]={'errors':len(e),'types':dict(Counter(v.get('type','?') for v in e)),'first':e[:2]}
 print('ACT_CORRIDORS',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 good=[float(x) for x,v in out.items() if v['errors']==0];print('ACT_CORRIDORS_GOOD',good)
 if not good:raise SystemExit('ERROR: no hay columna dirty DRC=0 en barrido')
if __name__=='__main__':main()
