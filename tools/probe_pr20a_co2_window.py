#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
X0,X1,Y0,Y1=210.0,230.0,10.0,28.0

def mm(v): return round(float(pcbnew.ToMM(v)),3)
def intersects(a,z):
    return max(a[0],z[0])>=X0 and min(a[0],z[0])<=X1 and max(a[1],z[1])>=Y0 and min(a[1],z[1])<=Y1
def via_w(v):
    try:return mm(v.GetWidth(pcbnew.F_Cu))
    except TypeError:return mm(v.GetWidth())
def main():
    b=pcbnew.LoadBoard(str(PCB)); out={'B.Cu':[],'In2.Cu':[],'F.Cu':[],'vias':[],'pads':[]}
    layers={pcbnew.B_Cu:'B.Cu',pcbnew.In2_Cu:'In2.Cu',pcbnew.F_Cu:'F.Cu'}
    for t in b.GetTracks():
        if isinstance(t,pcbnew.PCB_VIA):
            p=t.GetPosition();x,y=mm(p.x),mm(p.y)
            if X0<=x<=X1 and Y0<=y<=Y1:
                out['vias'].append({'net':t.GetNetname(),'x':x,'y':y,'diameter':via_w(t),'drill':mm(t.GetDrillValue())})
            continue
        if t.GetLayer() not in layers:continue
        a,z=t.GetStart(),t.GetEnd();A=[mm(a.x),mm(a.y)];Z=[mm(z.x),mm(z.y)]
        if intersects(A,Z):out[layers[t.GetLayer()]].append({'net':t.GetNetname(),'a':A,'z':Z,'w':mm(t.GetWidth())})
    for fp in b.GetFootprints():
        for p in fp.Pads():
            q=p.GetPosition();x,y=mm(q.x),mm(q.y)
            if not(X0<=x<=X1 and Y0<=y<=Y1):continue
            s=p.GetSize();out['pads'].append({'ref':fp.GetReference(),'pad':str(p.GetNumber()),'net':p.GetNetname(),'x':x,'y':y,'sx':mm(s.x),'sy':mm(s.y),'layers':[b.GetLayerName(l) for l in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu) if p.IsOnLayer(l)]})
    for k in out:out[k].sort(key=lambda x:(x.get('net',''),x.get('x',x.get('a',[0])[0]),x.get('y',x.get('a',[0,0])[1]),json.dumps(x,sort_keys=True)))
    print('CO2_WINDOW_BEGIN');print(json.dumps(out,ensure_ascii=False,separators=(',',':')));print('CO2_WINDOW_END')
if __name__=='__main__':main()
