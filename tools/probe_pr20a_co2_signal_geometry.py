#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[1]; PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
NETS={'ACT_FAULT_N','CO2_EN_DRV','CO2_OPENLOAD_N','CO2_ILIM','PUMP_CURRENT_ADC','CO2_SOL_POS','12V_ACT'}
def mm(v):return round(float(pcbnew.ToMM(v)),4)
def vw(v):
 try:return mm(v.GetWidth(pcbnew.F_Cu))
 except TypeError:return mm(v.GetWidth())
def main():
 b=pcbnew.LoadBoard(str(PCB));out={n:{'segments':[],'vias':[],'pads':[]} for n in NETS}
 for f in b.GetFootprints():
  for p in f.Pads():
   n=p.GetNetname()
   if n not in NETS:continue
   q=p.GetPosition();x,y=mm(q.x),mm(q.y)
   if x<205:continue
   s=p.GetSize();out[n]['pads'].append({'ref':f.GetReference(),'pad':str(p.GetNumber()),'x':x,'y':y,'sx':mm(s.x),'sy':mm(s.y),'layers':[b.GetLayerName(l) for l in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu) if p.IsOnLayer(l)]})
 for t in b.GetTracks():
  n=t.GetNetname()
  if n not in NETS:continue
  if isinstance(t,pcbnew.PCB_VIA):
   q=t.GetPosition();x,y=mm(q.x),mm(q.y)
   if x>=205:out[n]['vias'].append({'x':x,'y':y,'d':vw(t),'drill':mm(t.GetDrillValue())})
  else:
   a=t.GetStart();z=t.GetEnd();A=[mm(a.x),mm(a.y)];Z=[mm(z.x),mm(z.y)]
   if max(A[0],Z[0])>=205:out[n]['segments'].append({'layer':b.GetLayerName(t.GetLayer()),'a':A,'z':Z,'w':mm(t.GetWidth())})
 for n in out:
  for k in out[n]:out[n][k].sort(key=lambda d:json.dumps(d,sort_keys=True))
 print('CO2_SIGNAL_GEOMETRY',json.dumps(out,ensure_ascii=False,separators=(',',':')))
if __name__=='__main__':main()
