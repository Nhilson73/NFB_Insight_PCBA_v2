#!/usr/bin/env python3
"""Prueba ECO de CO2_ILIM junto con acceso 12V_ACT a U_CO2_DRV.8."""
from __future__ import annotations
import json,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
import pcbnew
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb';DRU=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_dru'
A=(217.67,17.875); B=(220.665,16.995)
VARS={
 'TOP_15_5':[A,(216.2,17.875),(216.2,15.5),(220.665,15.5),B],
 'TOP_15_0':[A,(216.0,17.875),(216.0,15.0),(220.665,15.0),B],
 'RIGHT_222':[A,(217.67,20.5),(222.5,20.5),(222.5,16.995),B],
 'RIGHT_224':[A,(217.67,20.75),(224.0,20.75),(224.0,16.995),B],
 'LOW_RIGHT':[A,(216.5,17.875),(216.5,22.0),(223.0,22.0),(223.0,16.995),B],
}
def iu(x):return pcbnew.FromMM(float(x))
def P(x,y):return pcbnew.VECTOR2I(iu(x),iu(y))
def netinfo(b,name):
 for f in b.GetFootprints():
  for p in f.Pads():
   if p.GetNetname()==name:return p.GetNet()
 raise SystemExit(name+' missing')
def addseg(b,n,net,layer,a,z,w):
 t=pcbnew.PCB_TRACK(b);t.SetNet(net);t.SetLayer(layer);t.SetWidth(iu(w));t.SetStart(P(*a));t.SetEnd(P(*z));b.Add(t)
def addvia(b,n,p):
 v=pcbnew.PCB_VIA(b);v.SetNet(n);v.SetPosition(P(*p));v.SetWidth(iu(.9));v.SetDrill(iu(.45));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
def main():
 out={}
 with tempfile.TemporaryDirectory(prefix='pr20a_ilim_') as td:
  td=Path(td)
  for name,nodes in VARS.items():
   b=pcbnew.LoadBoard(str(PCB)); ilim=netinfo(b,'CO2_ILIM'); act=netinfo(b,'12V_ACT')
   old=[t for t in b.GetTracks() if not isinstance(t,pcbnew.PCB_VIA) and t.GetNetname()=='CO2_ILIM']
   for t in old:b.Remove(t)
   for a,z in zip(nodes,nodes[1:]):addseg(b,'CO2_ILIM',ilim,pcbnew.F_Cu,a,z,.2)
   # acceso de potencia que antes fallaba solo contra el muro ILIM
   addseg(b,'12V_ACT',act,pcbnew.In2_Cu,(222,63),(222,18.375),1.0);addvia(b,act,(222,18.375))
   addseg(b,'12V_ACT',act,pcbnew.F_Cu,(222,18.375),(220.0,18.375),.5)
   addseg(b,'12V_ACT',act,pcbnew.F_Cu,(220.0,18.375),(218.82,18.375),.2)
   p=td/f'{name}.kicad_pcb';r=td/f'{name}.json';pcbnew.SaveBoard(str(p),b);shutil.copyfile(DRU,td/f'{name}.kicad_dru')
   subprocess.run(['kicad-cli','pcb','drc',str(p),'--format','json','--output',str(r),'--severity-all'],capture_output=True,text=True)
   d=json.loads(r.read_text());e=[x for x in d.get('violations',[]) if x.get('severity')=='error']
   un=[x for x in d.get('unconnected_items',[]) if 'CO2_ILIM' in json.dumps(x) or '12V_ACT' in json.dumps(x)]
   out[name]={'errors':len(e),'types':dict(Counter(x.get('type','?') for x in e)),'target_unconnected':len(un),'first':e[:6]}
 print('CO2_ILIM_ECO',json.dumps(out,ensure_ascii=False,separators=(',',':')))
 print('CO2_ILIM_ECO_GOOD',[k for k,v in out.items() if v['errors']==0])
if __name__=='__main__':main()
