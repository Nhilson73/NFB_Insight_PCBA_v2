#!/usr/bin/env python3
"""Runner PR20A: escapes SMD terminan en vía de clase y backbone nace en In2."""
from __future__ import annotations
from collections import deque
import math
import pcbnew
import materialize_pr20a_power_router as m

def states(self,e):
    ix,iy=m.gc(e['x']),m.gc(e['y'])
    if e.get('virtual'):
        return [(ix,iy,e.get('layer',pcbnew.F_Cu),0)]
    p=e['obj']; out=[]
    for l in m.LAYERS:
        if p.IsOnLayer(l): out.append((ix,iy,l,0))
    if not out: m.fail(f"{e['ref']}.{e['pad']}: sin capa PR20A")
    return out

def prepare_escape(self,n,e,w,role):
    ew=self.escape_width(e,w)
    if ew is None or e['obj'].IsOnLayer(pcbnew.In2_Cu): return e
    blocked,vblock=self.build_blocked(n,ew)
    start=(m.gc(e['x']),m.gc(e['y'])); q=deque([(start,0)]); prev={start:None}; goal=None
    # El escape termina en una vía propia de la clase. El troncal completo
    # comienza al otro lado, en In2.Cu, sin exigir 2 mm dentro del footprint.
    while q:
        (ix,iy),d=q.popleft()
        if d>=3 and (ix,iy) not in vblock and (ix,iy) not in blocked[pcbnew.F_Cu]:
            goal=(ix,iy); break
        if d>=56: continue
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            z=(ix+dx,iy+dy); x,y=m.xy(*z)
            if z in prev or not self.restrictions(n,x,y): continue
            if z!=start and z in blocked[pcbnew.F_Cu]: continue
            prev[z]=(ix,iy); q.append((z,d+1))
    if goal is None: m.fail(f'sin vía de escape {n} {e["ref"]}.{e["pad"]} w={w} ew={ew}')
    pts=[]; c=goal
    while c is not None: pts.append(c); c=prev[c]
    pts.reverse()
    self.add_seg(n,pcbnew.F_Cu,(e['x'],e['y']),m.xy(*pts[0]),ew,'smd_escape')
    for aa,bb in zip(pts,pts[1:]): self.add_seg(n,pcbnew.F_Cu,m.xy(*aa),m.xy(*bb),ew,'smd_escape')
    self.add_via(n,goal[0],goal[1],'smd_escape')
    x,y=m.xy(*goal)
    return {'net':n,'ref':e['ref']+'_PORTAL','pad':e['pad'],'obj':None,'x':x,'y':y,'sx':w,'sy':w,'virtual':True,'layer':pcbnew.In2_Cu,'source':m.pad_key(e['ref'],e['pad']),'escape_width':ew}

def own_goals(self,n,origin):
    pts=[]
    for t in self.b.GetTracks():
        if t.GetNetname()!=n: continue
        if isinstance(t,pcbnew.PCB_VIA):
            q=t.GetPosition(); x,y=m.mm(q.x),m.mm(q.y)
            for layer in m.LAYERS:
                pts.append({'net':n,'ref':'TREE','pad':'','obj':None,'x':x,'y':y,'sx':0,'sy':0,'virtual':True,'layer':layer})
        elif t.GetLayer() in m.LAYERS:
            a=t.GetStart(); z=t.GetEnd(); A=(m.mm(a.x),m.mm(a.y)); Z=(m.mm(z.x),m.mm(z.y)); layer=t.GetLayer()
            d=math.hypot(Z[0]-A[0],Z[1]-A[1]); k=max(1,int(math.ceil(d/1.0)))
            for i in range(k+1):
                q=i/k
                pts.append({'net':n,'ref':'TREE','pad':'','obj':None,'x':A[0]+(Z[0]-A[0])*q,'y':A[1]+(Z[1]-A[1])*q,'sx':0,'sy':0,'virtual':True,'layer':layer})
    pts.sort(key=lambda g:abs(g['x']-origin['x'])+abs(g['y']-origin['y']))
    return pts[:120]

m.Router.states=states
m.Router.prepare_escape=prepare_escape
m.Router.own_goals=own_goals

if __name__=='__main__': m.main()
