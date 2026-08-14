#!/usr/bin/env python3
"""PR19C v14: ECO geométrico PR19A de CO2_ILIM + routing PR19C.

Hallazgo: los 4 segmentos PR19A de CO2_ILIM formaban una U en F.Cu que
encerraba U_CO2_DRV.1 (ACT_FAULT_N). Se reperfilan 4→4 segmentos, 0→0 vías,
sin cambiar conectividad, netclass, placement ni conteos del checkpoint.
Después se enruta PR19C con el modelo conservador ya validado.
"""
from __future__ import annotations
import json
import math
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v7 as v7
import materialize_pr19c_digital_v12 as v12

CANDIDATE_REVISION='v14-co2-ilim-routing-eco-clean-act'

OLD_CO2_ILIM={
    ((217.67,17.875),(216.4,17.875)),
    ((216.4,19.0),(220.665,19.0)),
    ((216.4,17.875),(216.4,19.0)),
    ((220.665,19.0),(220.665,16.995)),
}
NEW_CO2_ILIM=[
    ((217.67,17.875),(216.4,17.875)),
    ((216.4,17.875),(214.5,19.25)),
    ((214.5,19.25),(220.665,19.25)),
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
    actual={x[1] for x in old}
    if actual!=OLD_CO2_ILIM:
        core.fail(f'geometría CO2_ILIM baseline inesperada: {sorted(actual)}')
    if len(old)!=4 or abs(float(width)-0.2)>1e-6: core.fail('checkpoint CO2_ILIM no es 4 segmentos de 0.20 mm')
    for item,_ in old: board.Remove(item)
    for a,b in NEW_CO2_ILIM:
        t=pcbnew.PCB_TRACK(board); t.SetNet(netinfo); t.SetLayer(pcbnew.F_Cu); t.SetWidth(core.iu(0.20))
        t.SetStart(pcbnew.VECTOR2I(core.iu(a[0]),core.iu(a[1]))); t.SetEnd(pcbnew.VECTOR2I(core.iu(b[0]),core.iu(b[1]))); board.Add(t)
    print('ECO_CO2_ILIM_OK 4->4 segmentos, 0 vías')

class RouterV14(v12.RouterV12):
    def _manual_uno_ioref_local(self,eps):
        by={e['ref']:e for e in eps}; r=by['R_5V_EN_PD']; u=by['U_5V']
        before_s,before_v=len(self.new_segments),len(self.new_vias)
        clsinfo=self.class_info[self.class_by_net['UNO_IOREF_3V3']]; length=0.0
        def seg(layer,a,b):
            nonlocal length
            self._manual_segment('UNO_IOREF_3V3',layer,a,b); length+=math.hypot(b[0]-a[0],b[1]-a[1])
        v1=(190.0,28.0); v2=(190.75,20.5)
        seg(pcbnew.F_Cu,(r['x_mm'],r['y_mm']),v1); self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v1[0]),core.gcoord(v1[1]))
        seg(pcbnew.B_Cu,v1,(190.75,28.0)); seg(pcbnew.B_Cu,(190.75,28.0),v2); self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v2[0]),core.gcoord(v2[1]))
        seg(pcbnew.F_Cu,v2,(190.75,u['y_mm'])); seg(pcbnew.F_Cu,(190.75,u['y_mm']),(u['x_mm'],u['y_mm']))
        return len(self.new_segments)-before_s,len(self.new_vias)-before_v,3,length

    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'J_UNOQ','R_ACT_FAULT_PU'}:
            # B y9.5; detour B superior alrededor de I2C; bypass F load-cell;
            # detour B superior alrededor de HMI; ascenso x197 evita PUMP_SR_CFG.
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),(8.00,36.50,pcbnew.B_Cu),(8.00,9.50,pcbnew.B_Cu),
                (90.00,9.50,pcbnew.B_Cu),(90.00,19.50,pcbnew.B_Cu),(96.00,19.50,pcbnew.B_Cu),(96.00,9.50,pcbnew.B_Cu),
                (104.50,9.50,pcbnew.B_Cu),(104.50,9.50,pcbnew.F_Cu),(112.50,9.50,pcbnew.F_Cu),(112.50,9.50,pcbnew.B_Cu),
                (150.00,9.50,pcbnew.B_Cu),(150.00,20.00,pcbnew.B_Cu),(164.00,20.00,pcbnew.B_Cu),(164.00,9.50,pcbnew.B_Cu),
                (197.00,9.50,pcbnew.B_Cu),(197.00,52.00,pcbnew.B_Cu),(202.50,52.00,pcbnew.B_Cu),(202.50,50.00,pcbnew.B_Cu),
                (202.50,50.00,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return list(reversed(p)) if a['ref']=='R_ACT_FAULT_PU' else p

        if net=='ACT_FAULT_N' and refs=={'R_ACT_FAULT_PU','U_PUMP_DRV'}:
            nodes=[
                (200.75,50.00,pcbnew.F_Cu),(207.00,50.00,pcbnew.F_Cu),(207.00,50.00,pcbnew.B_Cu),
                (207.00,27.75,pcbnew.B_Cu),(207.00,27.75,pcbnew.F_Cu),(207.00,25.25,pcbnew.F_Cu),(207.00,25.25,pcbnew.B_Cu),
                (207.00,22.50,pcbnew.B_Cu),(212.50,22.50,pcbnew.B_Cu),(212.50,16.00,pcbnew.B_Cu),
                (212.50,16.00,pcbnew.F_Cu),(213.00,16.00,pcbnew.F_Cu),(213.00,17.75,pcbnew.F_Cu),(212.25,17.75,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return p if a['ref']=='R_ACT_FAULT_PU' else list(reversed(p))

        if net=='ACT_FAULT_N' and refs=={'U_CO2_DRV','U_PUMP_DRV'}:
            nodes=[
                (212.25,17.75,pcbnew.F_Cu),(213.00,17.75,pcbnew.F_Cu),(213.00,16.00,pcbnew.F_Cu),(214.50,16.00,pcbnew.F_Cu),
                (214.50,16.00,pcbnew.B_Cu),(216.75,16.00,pcbnew.B_Cu),(216.75,18.50,pcbnew.B_Cu),
                (216.75,18.50,pcbnew.F_Cu),(217.67,18.375,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return p if a['ref']=='U_PUMP_DRV' else list(reversed(p))
        return super()._astar(net,a,z)

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r['prior_routing_eco']={
            'net':'CO2_ILIM','batch':'PR19A','reason':'abrir acceso físico a U_CO2_DRV.1 ACT_FAULT_N',
            'segments_before':4,'segments_after':4,'vias_before':0,'vias_after':0,
            'connectivity_changed':False,'placement_changed':False,
        }
        r.setdefault('planner',{}).update({
            'uno_ioref_via':'x190.75/y20.5',
            'act_fault_long':'B y9.5 + B I2C/HMI detours + F load-cell bypass + x197 ascent',
            'act_fault_rpu_pump':'B x207/x212.5 with F PUMP_CURRENT bypass; F escape pad18',
            'act_fault_pump_co2':'F escape -> B x214.5-216.75 -> via F -> U_CO2_DRV.1',
        })
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB))
    eco_co2_ilim(board)
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV14(board,placement,routing,batches); manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V14',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
