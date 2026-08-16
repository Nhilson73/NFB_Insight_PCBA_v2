#!/usr/bin/env python3
"""Candidato completo PR20A con islas de potencia probadas por micro-DRC.

Mantiene el lote PR20A 10/10. Se aplica un ECO localizado previo en dos nets
PR19C de la isla CO2 para permitir las vías de clase 0.9/0.45 de 12V_ACT:
- CO2_EN_DRV: relocaliza una vía y su ramal, preservando endpoints/conectividad.
- CO2_OPENLOAD_N: rerutea una diagonal B.Cu, preservando endpoints/vías.
No cambia placement, outline, netlist, In1.Cu ni zones.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import pcbnew
import materialize_pr20a_power_router as m
import run_pr20a_power_router_v7  # instala portales eFuse/TPSM y políticas previas

BASE_SEG=924; BASE_VIA=121
ECO_LOG={}

def canon(a,z):
    return frozenset(((round(float(a[0]),3),round(float(a[1]),3)),(round(float(z[0]),3),round(float(z[1]),3))))
def pos(t):
    q=t.GetPosition(); return (round(m.mm(q.x),3),round(m.mm(q.y),3))
def endpoints(t):
    a,z=t.GetStart(),t.GetEnd(); return (round(m.mm(a.x),3),round(m.mm(a.y),3)),(round(m.mm(z.x),3),round(m.mm(z.y),3))
def near(a,b,tol=.08): return math.hypot(a[0]-b[0],a[1]-b[1])<=tol

def add_raw_seg(b,netinfo,n,layer,a,z,w):
    t=pcbnew.PCB_TRACK(b);t.SetNet(netinfo[n]);t.SetLayer(layer);t.SetWidth(m.iu(w));t.SetStart(pcbnew.VECTOR2I(m.iu(a[0]),m.iu(a[1])));t.SetEnd(pcbnew.VECTOR2I(m.iu(z[0]),m.iu(z[1])));b.Add(t)
def add_raw_via(b,netinfo,n,p,d,dr):
    v=pcbnew.PCB_VIA(b);v.SetNet(netinfo[n]);v.SetPosition(pcbnew.VECTOR2I(m.iu(p[0]),m.iu(p[1])));v.SetWidth(m.iu(d));v.SetDrill(m.iu(dr));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)

def apply_co2_access_eco(b):
    netinfo={}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname():netinfo.setdefault(p.GetNetname(),p.GetNet())
    tracks=list(b.GetTracks())
    en_geoms={canon((216.8,15.2),(213.705,15.2)),canon((213.705,15.2),(213.705,21.5))}
    en_f=canon((213.705,21.5),(213.705,20.045)); ol_geom=canon((219.8,16.0),(218.5,20.8))
    removed={'CO2_EN_DRV_B':[],'CO2_EN_DRV_F':[],'CO2_OPENLOAD_N_B':[]}; old_via=None
    for t in tracks:
        if isinstance(t,pcbnew.PCB_VIA):
            if t.GetNetname()=='CO2_EN_DRV' and near(pos(t),(213.75,21.5),.12): old_via=t
            continue
        A,Z=endpoints(t); k=canon(A,Z)
        if t.GetNetname()=='CO2_EN_DRV' and t.GetLayer()==pcbnew.B_Cu and k in en_geoms:
            removed['CO2_EN_DRV_B'].append([A,Z]);b.Remove(t)
        elif t.GetNetname()=='CO2_EN_DRV' and t.GetLayer()==pcbnew.F_Cu and k==en_f:
            removed['CO2_EN_DRV_F'].append([A,Z]);b.Remove(t)
        elif t.GetNetname()=='CO2_OPENLOAD_N' and t.GetLayer()==pcbnew.B_Cu and k==ol_geom:
            removed['CO2_OPENLOAD_N_B'].append([A,Z]);b.Remove(t)
    if len(removed['CO2_EN_DRV_B'])!=2 or len(removed['CO2_EN_DRV_F'])!=1 or len(removed['CO2_OPENLOAD_N_B'])!=1 or old_via is None:
        m.fail(f'baseline CO2 ECO inesperado {removed} via={old_via is not None}')
    b.Remove(old_via)
    added=[]
    def S(n,l,a,z,w):add_raw_seg(b,netinfo,n,l,a,z,w);added.append({'net':n,'layer':b.GetLayerName(l),'start_mm':list(a),'end_mm':list(z),'width_mm':w})
    def V(n,p,d,dr):add_raw_via(b,netinfo,n,p,d,dr);added.append({'net':n,'via_mm':list(p),'diameter_mm':d,'drill_mm':dr})
    enpts=[(216.8,15.2),(218.0,15.2),(218.0,19.5),(216.25,19.5),(216.25,23.0)]
    for a,z in zip(enpts,enpts[1:]):S('CO2_EN_DRV',pcbnew.B_Cu,a,z,.2)
    V('CO2_EN_DRV',(216.25,23.0),.6,.3)
    for a,z in zip([(213.705,20.045),(213.705,23.0),(216.25,23.0)],[(213.705,23.0),(216.25,23.0),(216.25,23.0)]):
        if a!=z:S('CO2_EN_DRV',pcbnew.F_Cu,a,z,.2)
    olpts=[(219.8,16.0),(218.8,16.0),(218.8,19.75),(218.5,20.8)]
    for a,z in zip(olpts,olpts[1:]):S('CO2_OPENLOAD_N',pcbnew.B_Cu,a,z,.2)
    ECO_LOG.update({'id':'PR20A_CO2_ACCESS_ECO','removed':removed,'removed_via':{'net':'CO2_EN_DRV','at_mm':[213.75,21.5]},'added':added,'netlist_change':False,'placement_change':False,'outline_change':False,'via_count_delta':0,'segment_count_delta':5})

original_route=m.Router.route_net

def route_12v_act(self,n):
    if n!='12V_ACT': return original_route(self,n)
    bs,bv=len(self.seg),len(self.vias)
    # Backbone dirty desde F_ACT.2 por borde superior, columna limpia X=199.5.
    self.add_seg(n,pcbnew.F_Cu,(175.118,53.875),(175.118,63.0),1.0,'backbone')
    self.add_via(n,m.gc(175.118),m.gc(63.0),'backbone')
    self.add_seg(n,pcbnew.In2_Cu,(175.118,63.0),(199.5,63.0),1.0,'backbone')
    self.add_seg(n,pcbnew.In2_Cu,(199.5,63.0),(199.5,18.125),1.0,'backbone')
    self.add_via(n,m.gc(199.5),m.gc(18.125),'backbone')
    self.add_seg(n,pcbnew.F_Cu,(199.5,18.125),(200.19,18.125),1.0,'backbone')
    # Isla pump: variante PUMP_SIDE_VM_HIGH ya micro-DRC=0.
    self.add_seg(n,pcbnew.F_Cu,(200.19,18.125),(200.19,13.5),.5,'local_power_island')
    self.add_seg(n,pcbnew.F_Cu,(200.19,13.5),(205.52,13.5),.5,'local_power_island')
    self.add_seg(n,pcbnew.F_Cu,(205.52,13.5),(205.52,17.255),.5,'local_power_island')
    # Continuación In2 por corredor superior hasta isla CO2. X=222 fue DRC=0 a 1 mm.
    self.add_seg(n,pcbnew.In2_Cu,(199.5,63.0),(222.0,63.0),1.0,'backbone')
    self.add_seg(n,pcbnew.In2_Cu,(222.0,63.0),(222.0,24.5),1.0,'backbone')
    self.add_seg(n,pcbnew.In2_Cu,(222.0,24.5),(213.99,24.5),1.0,'local_power_island')
    # Isla CO2 v3: DRC=0 aislada con ECO previo.
    self.add_via(n,m.gc(213.99),m.gc(17.255),'local_power_island')
    self.add_via(n,m.gc(219.9),m.gc(18.45),'smd_escape')
    self.add_seg(n,pcbnew.F_Cu,(218.82,18.375),(219.9,18.45),.2,'smd_escape')
    self.add_seg(n,pcbnew.In2_Cu,(213.99,17.255),(213.99,24.5),1.0,'local_power_island')
    self.add_seg(n,pcbnew.In2_Cu,(221.5,24.5),(221.5,18.45),1.0,'local_power_island')
    self.add_seg(n,pcbnew.In2_Cu,(221.5,18.45),(219.9,18.45),1.0,'local_power_island')
    # El tramo 213.99->221.5 ya está cubierto por backbone 213.99->222 en Y24.5.
    # Endpoints locales restantes como taps sobre el árbol ya materializado.
    fixed={'F_ACT.2','C_PUMP_BULK.1','C_PUMP_VM.1','C_CO2_DRV.1','U_CO2_DRV.8'}
    allkeys=sorted(k for k,e in self.ep.items() if e['net']==n)
    for k in allkeys:
        if k in fixed: continue
        tw=.2 if k in {'U_PUMP_DRV.6','U_PUMP_DRV.15'} else .5
        e=self.prepare_escape(n,self.ep[k],tw,'tap')
        goals=self.own_goals(n,e)
        if not goals:m.fail(f'{n}: sin árbol para tap {k}')
        p=self.astar(n,e,goals,tw,'tap');self.materialize_path(n,p,e,goals,tw,'tap')
    stat={'net':n,'endpoints':len(allkeys),'backbone_endpoints':len(fixed),'tap_endpoints':len(allkeys)-len(fixed),'segments':len(self.seg)-bs,'vias':len(self.vias)-bv,'distribution_width_mm':1.0,'fixed_dirty_backbone':True}
    self.stats.append(stat);print('ROUTED',stat)

m.Router.route_net=route_12v_act
# Dirty first, then outputs, clean rails/long-haul.
m.ORDER=['12V_IN_RAW','12V_PROTECTED','12V_ACT','PUMP_OUT1','PUMP_OUT2','CO2_SOL_POS','12V_LOGIC','12V_HOST_VIN','5V_RAIL','3V3_RAIL']

def main():
    b=pcbnew.LoadBoard(str(m.PCB));seg0=sum(not isinstance(t,pcbnew.PCB_VIA) for t in b.GetTracks());via0=sum(isinstance(t,pcbnew.PCB_VIA) for t in b.GetTracks())
    if (seg0,via0)!=(BASE_SEG,BASE_VIA):m.fail(f'baseline {(seg0,via0)} != {(BASE_SEG,BASE_VIA)}')
    if len(b.Zones())!=0:m.fail('zones != 0 antes PR20B')
    touched={t.GetNetname() for t in b.GetTracks()}
    if set(m.TARGET)&touched:m.fail('PR20A inicia con cobre propio')
    if 'GND' in touched:m.fail('GND adelantado')
    apply_co2_access_eco(b)
    r=m.Router(b);man=r.run()
    man['status']='CANDIDATE_POWER_ROUTING_PR20A'
    man['routing_eco']=ECO_LOG
    man['actual_final_totals']={'segments':BASE_SEG+ECO_LOG['segment_count_delta']+man['new_segment_count'],'vias':BASE_VIA+ECO_LOG['via_count_delta']+man['new_via_count'],'zones':0}
    m.OUT.write_text(json.dumps(man,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');pcbnew.SaveBoard(str(m.PCB),b)
    print('PR20A_V8',man['new_segment_count'],man['new_via_count'],'FINAL',man['actual_final_totals'])

if __name__=='__main__':main()
