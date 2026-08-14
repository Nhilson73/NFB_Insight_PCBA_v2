#!/usr/bin/env python3
"""PR19C v13: rediseño geométrico de los focos DRC de v12.

- UNO_IOREF_3V3 cambia de capa por encima de 5V_PGOOD.
- ACT_FAULT_N usa trunk B.Cu bajo (y=2.0 mm), por debajo de I2C/HMI.
- El ascenso a RPU sortea PUMP_SR_CFG con bypass corto F.Cu.
- RPU→PUMP y PUMP→CO2 usan vías alejadas de pads GND/12V y de PUMP_CURRENT_ADC.
- Se conserva deduplicación de vías y el modelo conservador de obstáculos.
"""
from __future__ import annotations
import json
import math
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v7 as v7
import materialize_pr19c_digital_v12 as v12

CANDIDATE_REVISION='v13-low-act-trunk-clean-driver-escapes-active'

class RouterV13(v12.RouterV12):
    def _manual_uno_ioref_local(self,eps):
        by={e['ref']:e for e in eps}; r=by['R_5V_EN_PD']; u=by['U_5V']
        before_s,before_v=len(self.new_segments),len(self.new_vias)
        clsinfo=self.class_info[self.class_by_net['UNO_IOREF_3V3']]; length=0.0
        def seg(layer,a,b):
            nonlocal length
            self._manual_segment('UNO_IOREF_3V3',layer,a,b)
            length += math.hypot(b[0]-a[0],b[1]-a[1])
        v1=(190.0,28.0); v2=(190.5,18.75)
        seg(pcbnew.F_Cu,(r['x_mm'],r['y_mm']),v1)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v1[0]),core.gcoord(v1[1]))
        seg(pcbnew.B_Cu,v1,(190.5,28.0)); seg(pcbnew.B_Cu,(190.5,28.0),v2)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v2[0]),core.gcoord(v2[1]))
        seg(pcbnew.F_Cu,v2,(190.5,u['y_mm'])); seg(pcbnew.F_Cu,(190.5,u['y_mm']),(u['x_mm'],u['y_mm']))
        return len(self.new_segments)-before_s,len(self.new_vias)-before_v,3,length

    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'J_UNOQ','R_ACT_FAULT_PU'}:
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),(8.00,36.50,pcbnew.B_Cu),(8.00,2.00,pcbnew.B_Cu),
                (202.50,2.00,pcbnew.B_Cu),(202.50,13.25,pcbnew.B_Cu),
                (202.50,13.25,pcbnew.F_Cu),(202.50,15.75,pcbnew.F_Cu),(202.50,15.75,pcbnew.B_Cu),
                (202.50,50.00,pcbnew.B_Cu),(202.50,50.00,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes)
            return list(reversed(p)) if a['ref']=='R_ACT_FAULT_PU' else p

        if net=='ACT_FAULT_N' and refs=={'R_ACT_FAULT_PU','U_PUMP_DRV'}:
            nodes=[
                (200.75,50.00,pcbnew.F_Cu),(207.00,50.00,pcbnew.F_Cu),(207.00,50.00,pcbnew.B_Cu),
                (207.00,27.75,pcbnew.B_Cu),(207.00,27.75,pcbnew.F_Cu),(207.00,25.25,pcbnew.F_Cu),
                (207.00,25.25,pcbnew.B_Cu),(214.50,25.25,pcbnew.B_Cu),(214.50,17.75,pcbnew.B_Cu),
                (214.50,17.75,pcbnew.F_Cu),(212.25,17.75,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes)
            return p if a['ref']=='R_ACT_FAULT_PU' else list(reversed(p))

        if net=='ACT_FAULT_N' and refs=={'U_CO2_DRV','U_PUMP_DRV'}:
            nodes=[
                (212.25,17.75,pcbnew.F_Cu),(214.50,17.75,pcbnew.F_Cu),(214.50,17.75,pcbnew.B_Cu),
                (214.50,22.50,pcbnew.B_Cu),(214.50,22.50,pcbnew.F_Cu),(217.00,22.50,pcbnew.F_Cu),
                (217.00,22.50,pcbnew.B_Cu),(217.00,18.50,pcbnew.B_Cu),(216.50,18.50,pcbnew.B_Cu),
                (216.50,18.50,pcbnew.F_Cu),(217.00,18.50,pcbnew.F_Cu),(217.67,18.375,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes)
            return p if a['ref']=='U_PUMP_DRV' else list(reversed(p))
        return super()._astar(net,a,z)

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r.setdefault('planner',{}).update({
            'uno_ioref_via':'x190.5/y18.75 above 5V_PGOOD',
            'act_fault_long':'B y2.0; F bypass PUMP_SR_CFG at x202.5/y13.25-15.75',
            'act_fault_rpu_pump':'F RPU→x207; B/F bypass PUMP_CURRENT; B x214.5; F pad18',
            'act_fault_pump_co2':'shared x214.5; F y22.5 cross; B x217; F entry pad1',
        })
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB))
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8'))
    routing=json.loads(core.ROUTING.read_text(encoding='utf-8'))
    batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV13(board,placement,routing,batches); manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V13',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count'])
    return 0
if __name__=='__main__': raise SystemExit(main())
