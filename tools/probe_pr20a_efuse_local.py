#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
CX,CY=177.775,17.975; R=12.0

def mm(v):return round(float(pcbnew.ToMM(v)),4)
def near(x,y):return math.hypot(x-CX,y-CY)<=R

def main():
 b=pcbnew.LoadBoard(str(PCB)); out={'pads':[],'tracks':[],'vias':[]}
 for fp in b.GetFootprints():
  for p in fp.Pads():
   q=p.GetPosition();x,y=mm(q.x),mm(q.y)
   if not near(x,y):continue
   s=p.GetSize();out['pads'].append({'ref':fp.GetReference(),'pad':str(p.GetNumber()),'net':p.GetNetname(),'x':x,'y':y,'sx':mm(s.x),'sy':mm(s.y),'layers':[b.GetLayerName(l) for l in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu) if p.IsOnLayer(l)]})
 for t in b.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA):
   q=t.GetPosition();x,y=mm(q.x),mm(q.y)
   if near(x,y):
    try:d=mm(t.GetWidth(pcbnew.F_Cu))
    except TypeError:d=mm(t.GetWidth())
    out['vias'].append({'net':t.GetNetname(),'x':x,'y':y,'diam':d,'drill':mm(t.GetDrillValue())})
  else:
   a,z=t.GetStart(),t.GetEnd();ax,ay,zx,zy=mm(a.x),mm(a.y),mm(z.x),mm(z.y)
   # include if either endpoint near or bbox overlaps local circle bbox
   if near(ax,ay) or near(zx,zy) or (min(ax,zx)<=CX+R and max(ax,zx)>=CX-R and min(ay,zy)<=CY+R and max(ay,zy)>=CY-R):
    out['tracks'].append({'net':t.GetNetname(),'layer':b.GetLayerName(t.GetLayer()),'a':[ax,ay],'z':[zx,zy],'w':mm(t.GetWidth())})
 for k in out:out[k].sort(key=lambda d:(d.get('x',d.get('a',[0])[0]),d.get('y',d.get('a',[0,0])[1]),d.get('ref',''),d.get('pad','')))
 print('EFUSE_LOCAL_BEGIN');print(json.dumps(out,ensure_ascii=False,separators=(',',':')));print('EFUSE_LOCAL_END')
if __name__=='__main__':main()
