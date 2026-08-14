#!/usr/bin/env python3
"""PR19C v15: corrige las tres microzonas restantes de v14 y reduce cambios de capa.

Cambios acotados:
- mueve la vía local UNO_IOREF_3V3 lejos de U_5V.4;
- reperfila CO2_ILIM 4→4 segmentos por el lado +X, sin cambiar conectividad;
- cruza la garganta I2C de ACT_FAULT_N temporalmente por F.Cu;
- aumenta el costo A* de vía para favorecer corredores mono-capa.

No cambia placement, outline, netclasses, DRC ni alcance de lotes.
"""
from __future__ import annotations
import json
import math
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v4 as v4
import materialize_pr19c_digital_v7 as v7
import materialize_pr19c_digital_v14 as v14

CANDIDATE_REVISION='v15-local-drc-fixes-high-via-cost'
v4.VIA_COST=32.0

OLD_CO2_ILIM=v14.OLD_CO2_ILIM
NEW_CO2_ILIM=[
    ((217.67,17.875),(218.50,17.875)),
    ((218.50,17.875),(218.50,19.75)),
    ((218.50,19.75),(220.665,19.75)),
    ((220.665,19.75),(220.665,16.995)),
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
    actual={x[1] for x in old}
    if actual!=OLD_CO2_ILIM: core.fail(f'geometría CO2_ILIM baseline inesperada: {sorted(actual)}')
    if len(old)!=4 or abs(float(width)-0.2)>1e-6: core.fail('checkpoint CO2_ILIM no es 4 segmentos de 0.20 mm')
    for item,_ in old: board.Remove(item)
    for a,b in NEW_CO2_ILIM:
        t=pcbnew.PCB_TRACK(board); t.SetNet(netinfo); t.SetLayer(pcbnew.F_Cu); t.SetWidth(core.iu(0.20))
        t.SetStart(pcbnew.VECTOR2I(core.iu(a[0]),core.iu(a[1]))); t.SetEnd(pcbnew.VECTOR2I(core.iu(b[0]),core.iu(b[1]))); board.Add(t)
    print('ECO_CO2_ILIM_V15_OK 4->4 segmentos, 0 vías')

class RouterV15(v14.RouterV14):
    def _manual_uno_ioref_local(self,eps):
        by={e['ref']:e for e in eps}; r=by['R_5V_EN_PD']; u=by['U_5V']
        before_s,before_v=len(self.new_segments),len(self.new_vias)
        clsinfo=self.class_info[self.class_by_net['UNO_IOREF_3V3']]; length=0.0
        def seg(layer,a,b):
            nonlocal length
            self._manual_segment('UNO_IOREF_3V3',layer,a,b); length+=math.hypot(b[0]-a[0],b[1]-a[1])
        v1=(190.0,28.0); v2=(189.50,20.50)
        seg(pcbnew.F_Cu,(r['x_mm'],r['y_mm']),v1)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v1[0]),core.gcoord(v1[1]))
        seg(pcbnew.B_Cu,v1,(189.50,28.0)); seg(pcbnew.B_Cu,(189.50,28.0),v2)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v2[0]),core.gcoord(v2[1]))
        seg(pcbnew.F_Cu,v2,(189.50,u['y_mm'])); seg(pcbnew.F_Cu,(189.50,u['y_mm']),(u['x_mm'],u['y_mm']))
        return len(self.new_segments)-before_s,len(self.new_vias)-before_v,3,length

    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'J_UNOQ','R_ACT_FAULT_PU'}:
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),(8.00,36.50,pcbnew.B_Cu),(8.00,9.50,pcbnew.B_Cu),
                (90.00,9.50,pcbnew.B_Cu),(90.00,9.50,pcbnew.F_Cu),(98.00,9.50,pcbnew.F_Cu),(98.00,9.50,pcbnew.B_Cu),
                (104.50,9.50,pcbnew.B_Cu),(104.50,9.50,pcbnew.F_Cu),(112.50,9.50,pcbnew.F_Cu),(112.50,9.50,pcbnew.B_Cu),
                (150.00,9.50,pcbnew.B_Cu),(150.00,20.00,pcbnew.B_Cu),(164.00,20.00,pcbnew.B_Cu),(164.00,9.50,pcbnew.B_Cu),
                (197.00,9.50,pcbnew.B_Cu),(197.00,52.00,pcbnew.B_Cu),(202.50,52.00,pcbnew.B_Cu),(202.50,50.00,pcbnew.B_Cu),
                (202.50,50.00,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return list(reversed(p)) if a['ref']=='R_ACT_FAULT_PU' else p
        return super()._astar(net,a,z)

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r['prior_routing_eco']={
            'net':'CO2_ILIM','batch':'PR19A','reason':'abrir acceso físico a ACT_FAULT_N sin intersectar PUMP_CURRENT_ADC',
            'segments_before':4,'segments_after':4,'vias_before':0,'vias_after':0,
            'connectivity_changed':False,'placement_changed':False,
        }
        r.setdefault('planner',{}).update({
            'via_cost':v4.VIA_COST,
            'uno_ioref_local':'via x189.5/y20.5 fuera de U_5V.4',
            'act_fault_i2c_bypass':'B->F x90-98 @ y9.5 ->B',
            'co2_ilim_eco':'escape +X; y19.75; 4 segmentos/0 vías',
        })
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); eco_co2_ilim(board)
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV15(board,placement,routing,batches); manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V15',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
