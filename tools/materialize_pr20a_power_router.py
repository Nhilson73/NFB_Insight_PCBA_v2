#!/usr/bin/env python3
"""Router determinista PR20A con F.Cu + In2.Cu y escapes SMD locales.

No toca placement/outline/zones/In1/GND. Las troncales conservan los anchos
PR18; taps de diagnóstico/configuración y escapes de pads finos se etiquetan
de forma explícita para validación posterior.
"""
from __future__ import annotations
import heapq, json, math
from collections import deque
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
OUT=ROOT/'hardware'/'pr20a_power_routing_manifest.json'
BASE_SEG=924; BASE_VIA=121
STEP=0.25; MAX_EXP=900_000
LAYERS=(pcbnew.In2_Cu,pcbnew.F_Cu)
LNAME={pcbnew.F_Cu:'F.Cu',pcbnew.In2_Cu:'In2.Cu'}
TARGET=['12V_IN_RAW','12V_PROTECTED','12V_HOST_VIN','12V_LOGIC','12V_ACT','5V_RAIL','3V3_RAIL','PUMP_OUT1','PUMP_OUT2','CO2_SOL_POS']
SPEC={
 '12V_IN_RAW':(2.0,0.5,1.2,0.6), '12V_PROTECTED':(2.0,0.5,1.2,0.6),
 '12V_HOST_VIN':(1.0,0.4,0.9,0.45), '12V_LOGIC':(1.0,0.4,0.9,0.45), '12V_ACT':(1.0,0.4,0.9,0.45),
 '5V_RAIL':(0.75,0.3,0.8,0.4), '3V3_RAIL':(0.4,0.25,0.7,0.35),
 'PUMP_OUT1':(0.75,0.4,0.9,0.45), 'PUMP_OUT2':(0.75,0.4,0.9,0.45), 'CO2_SOL_POS':(0.75,0.4,0.9,0.45),
}
BACKBONE={
 '12V_IN_RAW':['J_PWR_IN.1','U_EFUSE.5'],
 '12V_PROTECTED':['U_EFUSE.6','C_IN_BULK.1','NT_HOST.1','NT_LOGIC.1','F_ACT.1'],
 '12V_HOST_VIN':['J_UNOQ.8','NT_HOST.2'],
 '12V_LOGIC':['NT_LOGIC.2','C_5V_IN_4U7.1','U_5V.3'],
 '12V_ACT':['F_ACT.2','C_PUMP_BULK.1','U_PUMP_DRV.6','U_PUMP_DRV.15','U_CO2_DRV.8'],
 '5V_RAIL':['U_5V.4','C_5V_OUT1.1','C_5V_OUT2.1','C_3V3_IN.1','U_3V3.1','J_PH.1','J_ORP.1','J_DO.1','TP_5V.1'],
 '3V3_RAIL':[],
 'PUMP_OUT1':['U_PUMP_DRV.7','U_PUMP_DRV.8','J_PUMP.1','TP_PUMP_OUT1.1'],
 'PUMP_OUT2':['U_PUMP_DRV.13','U_PUMP_DRV.14','J_PUMP.2','TP_PUMP_OUT2.1'],
 'CO2_SOL_POS':['U_CO2_DRV.7','J_CO2_SOL.1','TP_CO2_SOL_POS.1'],
}
TAP_WIDTH={
 '12V_IN_RAW':{'D_IN_TVS.1':1.0,'C_IN_HF.1':0.5,'R_UVOV_R1.1':0.3,'TP_12V_RAW.1':0.5},
 '12V_PROTECTED':{'TP_12V_PROT.1':0.5},
 '12V_LOGIC':{'C_5V_IN_100N.1':0.5,'TP_12V_LOGIC.1':0.5},
 '12V_ACT':{'C_PUMP_VM.1':0.5,'C_CO2_DRV.1':0.5,'TP_12V_ACT.1':0.5},
 '5V_RAIL':{'C_5V_HF.1':0.4,'R_5V_FBT.1':0.4,'R_5V_PG_PU.1':0.4},
}
ORDER=['12V_IN_RAW','12V_PROTECTED','12V_HOST_VIN','12V_LOGIC','12V_ACT','PUMP_OUT1','PUMP_OUT2','CO2_SOL_POS','5V_RAIL','3V3_RAIL']

def fail(m): raise SystemExit('ERROR: '+m)
def iu(x): return pcbnew.FromMM(float(x))
def mm(x): return float(pcbnew.ToMM(x))
def gc(x): return int(round(float(x)/STEP))
def xy(ix,iy): return (ix*STEP,iy*STEP)
def P(ix,iy): return pcbnew.VECTOR2I(iu(ix*STEP),iu(iy*STEP))
def via_width(v):
    try: return mm(v.GetWidth(pcbnew.F_Cu))
    except TypeError: return mm(v.GetWidth())

def pad_key(ref,pad): return f'{ref}.{pad}'
def rect_pad(p):
    bb=p.GetBoundingBox(); x0=mm(bb.GetX()); y0=mm(bb.GetY()); return (x0,y0,x0+mm(bb.GetWidth()),y0+mm(bb.GetHeight()))
def cells_rect(r):
    x0,y0,x1,y1=r
    for ix in range(math.floor(x0/STEP),math.ceil(x1/STEP)+1):
      for iy in range(math.floor(y0/STEP),math.ceil(y1/STEP)+1):
        x,y=xy(ix,iy)
        if x0-1e-9<=x<=x1+1e-9 and y0-1e-9<=y<=y1+1e-9: yield (ix,iy)
def sample_line(a,z):
    d=math.hypot(z[0]-a[0],z[1]-a[1]); n=max(1,int(math.ceil(d/(STEP/2))))
    for k in range(n+1):
        t=k/n; yield (a[0]+(z[0]-a[0])*t,a[1]+(z[1]-a[1])*t)
def disk_cells(x,y,r):
    n=int(math.ceil(r/STEP)); cx,cy=gc(x),gc(y)
    for dx in range(-n,n+1):
      for dy in range(-n,n+1):
        px,py=xy(cx+dx,cy+dy)
        if math.hypot(px-x,py-y)<=r+STEP*0.71: yield (cx+dx,cy+dy)

def mst(eps):
    if len(eps)<2:return []
    used={0}; out=[]
    while len(used)<len(eps):
      best=None
      for i in sorted(used):
        for j in range(len(eps)):
          if j in used: continue
          d=abs(eps[i]['x']-eps[j]['x'])+abs(eps[i]['y']-eps[j]['y'])
          q=(round(d,6),i,j)
          if best is None or q<best[0]: best=(q,i,j)
      _,i,j=best; used.add(j); out.append((i,j))
    return out

class Router:
  def __init__(self,b):
    self.b=b; self.fps={f.GetReference():f for f in b.GetFootprints()}; self.ep={}; self.netinfo={}
    self.seg=[]; self.vias=[]; self.stats=[]; self._index()
  def _index(self):
    seen=set()
    for ref,fp in self.fps.items():
      for p in fp.Pads():
        n=p.GetNetname()
        if n: self.netinfo.setdefault(n,p.GetNet())
        if n not in TARGET: continue
        k=(n,ref,str(p.GetNumber()))
        if k in seen: continue
        seen.add(k); q=p.GetPosition(); s=p.GetSize()
        self.ep[pad_key(ref,str(p.GetNumber()))]={'net':n,'ref':ref,'pad':str(p.GetNumber()),'obj':p,'x':mm(q.x),'y':mm(q.y),'sx':mm(s.x),'sy':mm(s.y),'virtual':False}
    for n in TARGET:
      got=sorted(k for k,e in self.ep.items() if e['net']==n)
      if len(got)<2: fail(f'{n}: endpoints insuficientes')
  def add_seg(self,n,layer,a,z,w,role):
    if math.hypot(z[0]-a[0],z[1]-a[1])<1e-6:return
    t=pcbnew.PCB_TRACK(self.b); t.SetNet(self.netinfo[n]); t.SetLayer(layer); t.SetWidth(iu(w)); t.SetStart(pcbnew.VECTOR2I(iu(a[0]),iu(a[1]))); t.SetEnd(pcbnew.VECTOR2I(iu(z[0]),iu(z[1]))); self.b.Add(t)
    self.seg.append({'net':n,'layer':LNAME[layer],'start_mm':[round(a[0],4),round(a[1],4)],'end_mm':[round(z[0],4),round(z[1],4)],'width_mm':w,'role':role})
  def add_via(self,n,ix,iy,role):
    _,_,d,dr=SPEC[n]; v=pcbnew.PCB_VIA(self.b); v.SetNet(self.netinfo[n]); v.SetPosition(P(ix,iy)); v.SetWidth(iu(d)); v.SetDrill(iu(dr)); v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); self.b.Add(v)
    x,y=xy(ix,iy); self.vias.append({'net':n,'at_mm':[x,y],'diameter_mm':d,'drill_mm':dr,'role':role})
  def restrictions(self,n,x,y):
    edge=0.8
    if not(edge<=x<=242.34-edge and edge<=y<=68.58-edge):return False
    if n in {'12V_IN_RAW','12V_PROTECTED','12V_LOGIC'} and not(162.8<=x<=198.8):return False
    if n=='12V_ACT' and x<162.8:return False
    if n in {'PUMP_OUT1','PUMP_OUT2','CO2_SOL_POS'} and x<197.0:return False
    return True
  def build_blocked(self,n,w):
    _,clr,vd,_=SPEC[n]; blocked={pcbnew.F_Cu:set(),pcbnew.In2_Cu:set()}; vblock=set(); own=n
    # pads
    for fp in self.b.GetFootprints():
      for p in fp.Pads():
        if p.GetNetname()==own: continue
        r=rect_pad(p); ex=w/2+clr; rr=(r[0]-ex,r[1]-ex,r[2]+ex,r[3]+ex)
        for layer in LAYERS:
          if p.IsOnLayer(layer): blocked[layer].update(cells_rect(rr))
        # via must avoid any copper pad on any layer
        if any(p.IsOnLayer(l) for l in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu)):
          exv=vd/2+clr; rv=(r[0]-exv,r[1]-exv,r[2]+exv,r[3]+exv); vblock.update(cells_rect(rv))
    # tracks/vias
    for t in self.b.GetTracks():
      if t.GetNetname()==own: continue
      if isinstance(t,pcbnew.PCB_VIA):
        q=t.GetPosition(); x,y=mm(q.x),mm(q.y); r=via_width(t)/2+w/2+clr
        cc=set(disk_cells(x,y,r)); blocked[pcbnew.F_Cu].update(cc); blocked[pcbnew.In2_Cu].update(cc)
        vblock.update(disk_cells(x,y,via_width(t)/2+vd/2+clr)); continue
      a=t.GetStart(); z=t.GetEnd(); A=(mm(a.x),mm(a.y)); Z=(mm(z.x),mm(z.y)); tw=mm(t.GetWidth()); layer=t.GetLayer()
      if layer in blocked:
        r=tw/2+w/2+clr; rc=int(math.ceil(r/STEP))
        for x,y in sample_line(A,Z):
          cx,cy=gc(x),gc(y)
          for dx in range(-rc,rc+1):
            for dy in range(-rc,rc+1):
              px,py=xy(cx+dx,cy+dy)
              if math.hypot(px-x,py-y)<=r+STEP*.71: blocked[layer].add((cx+dx,cy+dy))
      # via drill crosses all copper layers: conservatively avoid every existing track
      r=tw/2+vd/2+clr; rc=int(math.ceil(r/STEP))
      for x,y in sample_line(A,Z):
        cx,cy=gc(x),gc(y)
        for dx in range(-rc,rc+1):
          for dy in range(-rc,rc+1):
            px,py=xy(cx+dx,cy+dy)
            if math.hypot(px-x,py-y)<=r+STEP*.71:vblock.add((cx+dx,cy+dy))
    return blocked,vblock
  def states(self,e):
    ix,iy=gc(e['x']),gc(e['y'])
    if e.get('virtual'): return [(ix,iy,pcbnew.F_Cu,0)]
    p=e['obj']; out=[]
    for l in LAYERS:
      if p.IsOnLayer(l): out.append((ix,iy,l,0))
    if not out: fail(f"{e['ref']}.{e['pad']}: sin capa PR20A")
    return out
  def astar(self,n,a,goals,w,role):
    blocked,vblock=self.build_blocked(n,w); starts=self.states(a); goalstates=[]
    for g in goals: goalstates.extend(self.states(g))
    goalset={(x,y,l) for x,y,l,_ in goalstates}; goalxy={(x,y) for x,y,_,_ in goalstates}
    q=[]; dist={}; prev={}
    def heur(s):
      ix,iy,l,_=s; return min(abs(ix-gx)+abs(iy-gy)+(10 if l!=gl else 0) for gx,gy,gl,_ in goalstates)
    for s in starts: dist[s]=0.; prev[s]=None; heapq.heappush(q,(heur(s),0.,s))
    reached=None; ex=0; moves=((1,0,1),(-1,0,2),(0,1,3),(0,-1,4))
    while q:
      _,d,cur=heapq.heappop(q)
      if abs(d-dist.get(cur,1e99))>1e-9:continue
      ix,iy,l,pd=cur
      if (ix,iy,l) in goalset:reached=cur;break
      ex+=1
      if ex>MAX_EXP:break
      for dx,dy,nd in moves:
        nx,ny=ix+dx,iy+dy; x,y=xy(nx,ny)
        if not self.restrictions(n,x,y):continue
        if (nx,ny) not in goalxy and (nx,ny) in blocked[l]:continue
        cost=1.0 if l==pcbnew.In2_Cu else 2.8
        if pd and pd!=nd:cost+=.18
        ns=(nx,ny,l,nd); ndist=d+cost
        if ndist+1e-9<dist.get(ns,1e99):dist[ns]=ndist;prev[ns]=cur;heapq.heappush(q,(ndist+heur(ns),ndist,ns))
      other=pcbnew.F_Cu if l==pcbnew.In2_Cu else pcbnew.In2_Cu
      if (ix,iy) not in vblock and (ix,iy) not in blocked[other]:
        ns=(ix,iy,other,0); ndist=d+12.0
        if ndist+1e-9<dist.get(ns,1e99):dist[ns]=ndist;prev[ns]=cur;heapq.heappush(q,(ndist+heur(ns),ndist,ns))
    if reached is None:fail(f'sin ruta {n} {a.get("ref","portal")}.{a.get("pad","")} role={role} exp={ex}')
    path=[]; c=reached
    while c is not None:path.append(c);c=prev[c]
    return list(reversed(path))
  def materialize_path(self,n,path,a,goals,w,role):
    # identify exact goal matching final snapped cell
    gx,gy,gl,_=path[-1]; candidates=[g for g in goals if any(gc(g['x'])==gx and gc(g['y'])==gy and l==gl for _,_,l,_ in self.states(g))]
    g=candidates[0] if candidates else {'x':gx*STEP,'y':gy*STEP,'virtual':True}
    sx,sy,sl,_=path[0]; self.add_seg(n,sl,(a['x'],a['y']),xy(sx,sy),w,role)
    run=0
    for i in range(1,len(path)+1):
      split=i==len(path) or path[i][2]!=path[i-1][2]
      if not split:continue
      layer=path[run][2]; pts=[(path[j][0],path[j][1]) for j in range(run,i)]
      if len(pts)>1:
        keep=[pts[0]]
        for k in range(1,len(pts)-1):
          aa,bb,cc=keep[-1],pts[k],pts[k+1]
          if (bb[0]-aa[0],bb[1]-aa[1])!=(cc[0]-bb[0],cc[1]-bb[1]):keep.append(bb)
        keep.append(pts[-1])
        for aa,bb in zip(keep,keep[1:]):self.add_seg(n,layer,xy(*aa),xy(*bb),w,role)
      if i<len(path):
        ix,iy,_,_=path[i-1]; self.add_via(n,ix,iy,role);run=i
    self.add_seg(n,gl,xy(gx,gy),(g['x'],g['y']),w,role)
  def escape_width(self,e,w):
    m=min(e['sx'],e['sy'])
    if m>=w*.85:return None
    if m<=.28:return .20
    if m<=.38:return .25
    if m<=.55:return min(.40,w)
    return min(.50,w)
  def prepare_escape(self,n,e,w,role):
    ew=self.escape_width(e,w)
    if ew is None or (e['obj'].IsOnLayer(pcbnew.In2_Cu)):return e
    be,_=self.build_blocked(n,ew); bf,vf=self.build_blocked(n,w)
    start=(gc(e['x']),gc(e['y'])); q=deque([(start,0)]); prev={start:None}; goal=None
    while q:
      (ix,iy),d=q.popleft()
      if d>=3 and (ix,iy) not in bf[pcbnew.F_Cu] and (ix,iy) not in vf:
        goal=(ix,iy);break
      if d>=18:continue
      for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        z=(ix+dx,iy+dy); x,y=xy(*z)
        if z in prev or not self.restrictions(n,x,y):continue
        if z!=start and z in be[pcbnew.F_Cu]:continue
        prev[z]=(ix,iy);q.append((z,d+1))
    if goal is None:fail(f'sin portal escape {n} {e["ref"]}.{e["pad"]} w={w} ew={ew}')
    pts=[]; c=goal
    while c is not None:pts.append(c);c=prev[c]
    pts.reverse(); exact=(e['x'],e['y']); self.add_seg(n,pcbnew.F_Cu,exact,xy(*pts[0]),ew,'smd_escape')
    # no comprimir el primer mm en una sola diagonal: conservar ortogonal y auditable
    for aa,bb in zip(pts,pts[1:]):self.add_seg(n,pcbnew.F_Cu,xy(*aa),xy(*bb),ew,'smd_escape')
    x,y=xy(*goal)
    return {'net':n,'ref':e['ref']+'_PORTAL','pad':e['pad'],'obj':None,'x':x,'y':y,'sx':w,'sy':w,'virtual':True,'source':pad_key(e['ref'],e['pad']),'escape_width':ew}
  def own_goals(self,n,limit_from):
    pts=[]
    for t in self.b.GetTracks():
      if t.GetNetname()!=n:continue
      if isinstance(t,pcbnew.PCB_VIA):
        q=t.GetPosition(); x,y=mm(q.x),mm(q.y); pts.append({'net':n,'ref':'TREE','pad':'','obj':None,'x':x,'y':y,'sx':0,'sy':0,'virtual':True})
      elif t.GetLayer() in LAYERS:
        a=t.GetStart();z=t.GetEnd();A=(mm(a.x),mm(a.y));Z=(mm(z.x),mm(z.y))
        d=math.hypot(Z[0]-A[0],Z[1]-A[1]); k=max(1,int(math.ceil(d/1.0)))
        for i in range(k+1):
          q=i/k; pts.append({'net':n,'ref':'TREE','pad':'','obj':None,'x':A[0]+(Z[0]-A[0])*q,'y':A[1]+(Z[1]-A[1])*q,'sx':0,'sy':0,'virtual':True})
    # virtual goals currently force F; create layer-specific samples based on nearest actual track would be better.
    # For tap routing we target endpoints of the backbone portals/pads plus sampled F cells; taps are low-current and F-biased.
    pts.sort(key=lambda g:abs(g['x']-limit_from['x'])+abs(g['y']-limit_from['y']))
    return pts[:80]
  def route_net(self,n):
    w,clr,_,_=SPEC[n]; allkeys=sorted(k for k,e in self.ep.items() if e['net']==n)
    bbkeys=BACKBONE[n] or allkeys
    if set(bbkeys)-set(allkeys):fail(f'{n}: backbone referencia inexistente {sorted(set(bbkeys)-set(allkeys))}')
    taps=[k for k in allkeys if k not in bbkeys]
    prepared=[]; bs=len(self.seg);bv=len(self.vias)
    for k in bbkeys:prepared.append(self.prepare_escape(n,self.ep[k],w,'backbone'))
    for i,j in mst(prepared):
      p=self.astar(n,prepared[i],[prepared[j]],w,'backbone');self.materialize_path(n,p,prepared[i],[prepared[j]],w,'backbone')
    for k in taps:
      tw=TAP_WIDTH.get(n,{}).get(k,w)
      e=self.prepare_escape(n,self.ep[k],tw,'tap')
      goals=self.own_goals(n,e)
      if not goals:fail(f'{n}: sin árbol para tap {k}')
      p=self.astar(n,e,goals,tw,'tap');self.materialize_path(n,p,e,goals,tw,'tap')
    stat={'net':n,'endpoints':len(allkeys),'backbone_endpoints':len(bbkeys),'tap_endpoints':len(taps),'segments':len(self.seg)-bs,'vias':len(self.vias)-bv,'distribution_width_mm':w}
    self.stats.append(stat);print('ROUTED',stat)
  def run(self):
    for n in ORDER:self.route_net(n)
    return {'schema_version':2,'status':'CANDIDATE_POWER_ROUTING_PR20A','target_nets':TARGET,'baseline':{'segments':BASE_SEG,'vias':BASE_VIA,'zones':0},'net_stats':self.stats,'new_segment_count':len(self.seg),'new_via_count':len(self.vias),'new_segments':self.seg,'new_vias':self.vias,'policies':{'in1_signal_tracks':0,'zones_added':0,'gnd_copper_added':0,'future_batch_copper':0,'placement_change':0,'outline_change':0},'escape_policy':'Backbone at frozen PR18 width; only SMD escape/tap roles may be narrower; clearance unchanged.'}

def main():
  b=pcbnew.LoadBoard(str(PCB)); seg=sum(not isinstance(t,pcbnew.PCB_VIA) for t in b.GetTracks());via=sum(isinstance(t,pcbnew.PCB_VIA) for t in b.GetTracks())
  if (seg,via)!=(BASE_SEG,BASE_VIA):fail(f'baseline {(seg,via)} != {(BASE_SEG,BASE_VIA)}')
  if len(b.Zones())!=0:fail('zones != 0 antes PR20B')
  touched={t.GetNetname() for t in b.GetTracks()}
  if set(TARGET)&touched:fail('PR20A inicia con cobre propio')
  if 'GND' in touched:fail('GND adelantado')
  r=Router(b);man=r.run();OUT.write_text(json.dumps(man,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');pcbnew.SaveBoard(str(PCB),b)
  print('PR20A_ROUTER',man['new_segment_count'],man['new_via_count'],'TOTAL',BASE_SEG+man['new_segment_count'],BASE_VIA+man['new_via_count'])
if __name__=='__main__':main()
