#!/usr/bin/env python3
"""PR19C v17: conserva la topología low-via v16 y corrige solo tres microzonas DRC.

- UNO_IOREF_3V3: vía B→F en (190.25,17.50) y entrada diagonal a U_5V.2.
- CO2_ILIM: ECO 4→4 con muro x=216.20, entre PUMP_CURRENT_ADC y ACT_FAULT_N.
- ACT_FAULT_N: bypass F.Cu x106.75→110 para cruzar load-cell; vía local CO2 en x216.95.

Sin cambios de placement, outline, netclasses, DRC ni lotes futuros.
"""
from __future__ import annotations
import json
import math
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v7 as v7
import materialize_pr19c_digital_v14 as v14
import materialize_pr19c_digital_v16 as v16

CANDIDATE_REVISION='v17-three-local-drc-closures'
OLD_CO2_ILIM=v14.OLD_CO2_ILIM
NEW_CO2_ILIM=[
    ((217.67,17.875),(216.20,17.875)),
    ((216.20,17.875),(216.20,19.25)),
    ((216.20,19.25),(220.665,19.25)),
    ((220.665,19.25),(220.665,16.995)),
]

def r4(v): return round(float(v),4)
def canon(a,b): return ((r4(a[0]),r4(a[1])),(r4(b[0]),r4(b[1])))

def eco_co2_ilim(board):
    old=[]; netinfo=None; width=None
    for item in list(board.GetTracks()):
        if item.GetNetname()!='CO2_ILIM': continue
        if isinstance(item,pcbnew.PCB_VIA): core.fail('CO2_ILIM PR19A no debe tener vías')
        if item.GetLayer()!=pcbnew.F_Cu: core.fail('CO2_ILIM PR19A esperado solo F.Cu')
        a=item.GetStart(); b=item.GetEnd(); aa=(core.mm(a.x),core.mm(a.y)); bb=(core.mm(b.x),core.mm(b.y))
        old.append((item,canon(aa,bb))); netinfo=item.GetNet(); width=core.mm(item.GetWidth())
    if {x[1] for x in old}!=OLD_CO2_ILIM: core.fail('geometría CO2_ILIM baseline inesperada')
    if len(old)!=4 or abs(float(width)-0.2)>1e-6: core.fail('checkpoint CO2_ILIM no es 4 segmentos de 0.20 mm')
    for item,_ in old: board.Remove(item)
    for a,b in NEW_CO2_ILIM:
        t=pcbnew.PCB_TRACK(board); t.SetNet(netinfo); t.SetLayer(pcbnew.F_Cu); t.SetWidth(core.iu(0.20))
        t.SetStart(pcbnew.VECTOR2I(core.iu(a[0]),core.iu(a[1]))); t.SetEnd(pcbnew.VECTOR2I(core.iu(b[0]),core.iu(b[1]))); board.Add(t)
    print('ECO_CO2_ILIM_V17_OK 4->4 segmentos, 0 vías, muro x216.20')

class RouterV17(v16.RouterV16):
    def _manual_uno_ioref_local(self,eps):
        by={e['ref']:e for e in eps}; r=by['R_5V_EN_PD']; u=by['U_5V']
        before_s,before_v=len(self.new_segments),len(self.new_vias)
        clsinfo=self.class_info[self.class_by_net['UNO_IOREF_3V3']]; length=0.0
        def seg(layer,a,b):
            nonlocal length
            self._manual_segment('UNO_IOREF_3V3',layer,a,b); length+=math.hypot(b[0]-a[0],b[1]-a[1])
        v1=(190.0,28.0); v2=(190.25,17.50)
        seg(pcbnew.F_Cu,(r['x_mm'],r['y_mm']),v1)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v1[0]),core.gcoord(v1[1]))
        seg(pcbnew.B_Cu,v1,(190.25,28.0)); seg(pcbnew.B_Cu,(190.25,28.0),v2)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v2[0]),core.gcoord(v2[1]))
        seg(pcbnew.F_Cu,v2,(u['x_mm'],u['y_mm']))
        return len(self.new_segments)-before_s,len(self.new_vias)-before_v,2,length

    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'J_UNOQ','R_ACT_FAULT_PU'}:
            # B superior sobre I2C; F cruza ambas verticales load-cell; vuelve a B a x110.
            # Se reutilizan las dos transiciones que antes gastaba el bypass x112.5→114.
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),(8.00,36.50,pcbnew.B_Cu),(8.00,9.50,pcbnew.B_Cu),
                (90.00,9.50,pcbnew.B_Cu),(90.00,19.50,pcbnew.B_Cu),(106.75,19.50,pcbnew.B_Cu),
                (106.75,19.50,pcbnew.F_Cu),(110.00,19.50,pcbnew.F_Cu),(110.00,9.50,pcbnew.F_Cu),
                (110.00,9.50,pcbnew.B_Cu),(150.00,9.50,pcbnew.B_Cu),
                (150.00,20.00,pcbnew.B_Cu),(164.00,20.00,pcbnew.B_Cu),(164.00,9.50,pcbnew.B_Cu),
                (197.00,9.50,pcbnew.B_Cu),(197.00,52.00,pcbnew.B_Cu),(202.50,52.00,pcbnew.B_Cu),(202.50,50.00,pcbnew.B_Cu),
                (202.50,50.00,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return list(reversed(p)) if a['ref']=='R_ACT_FAULT_PU' else p

        if net=='ACT_FAULT_N' and refs=={'U_CO2_DRV','U_PUMP_DRV'}:
            nodes=[
                (212.25,17.75,pcbnew.F_Cu),(213.00,17.75,pcbnew.F_Cu),(213.00,16.00,pcbnew.F_Cu),(214.50,16.00,pcbnew.F_Cu),
                (214.50,16.00,pcbnew.B_Cu),(216.95,16.00,pcbnew.B_Cu),(216.95,18.50,pcbnew.B_Cu),
                (216.95,18.50,pcbnew.F_Cu),(217.75,18.50,pcbnew.F_Cu),(217.67,18.375,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return p if a['ref']=='U_PUMP_DRV' else list(reversed(p))
        return super()._astar(net,a,z)

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r['prior_routing_eco']={
            'net':'CO2_ILIM','batch':'PR19A','reason':'abrir acceso físico ACT_FAULT_N con margen entre PUMP_CURRENT_ADC y vía ACT',
            'segments_before':4,'segments_after':4,'vias_before':0,'vias_after':0,
            'connectivity_changed':False,'placement_changed':False,
        }
        r.setdefault('planner',{}).update({
            'uno_ioref_local':'B→F @190.25,17.50; diagonal directa a U_5V.2',
            'act_fault_loadcell_bypass':'F x106.75→110 y19.5→9.5; 2 transiciones',
            'act_fault_co2_via':'x216.95/y18.50',
            'co2_ilim_eco':'muro F x216.20; 4 segmentos/0 vías',
        })
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); eco_co2_ilim(board)
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV17(board,placement,routing,batches); manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V17',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
