#!/usr/bin/env python3
"""PR19C v16: costo de vía por net + bypass B.Cu de ACT_FAULT_N.

Mantiene las correcciones físicas v15, pero evita penalización global:
- 32 para nets que demostraron mejorar con menos cambios de capa;
- 20 para PUMP_DIR para preservar resolubilidad;
- bypass ACT_FAULT_N a x107.5 en B.Cu, a la derecha de I2C SDA/SCL.
"""
from __future__ import annotations
import json
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v4 as v4
import materialize_pr19c_digital_v7 as v7
import materialize_pr19c_digital_v15 as v15

CANDIDATE_REVISION='v16-per-net-via-cost-act-b-detour'

HIGH_COST={
    'I2C_SDA','I2C_SCL','PUMP_PWM','CO2_SOL_CTL','CHILLER_CTL',
    'HX711_DOUT','HX711_SCK','MCU_NRST','MCU_WDI','HMI_RX','HMI_TX','LED_STATUS',
}

class RouterV16(v15.RouterV15):
    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'J_UNOQ','R_ACT_FAULT_PU'}:
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),(8.00,36.50,pcbnew.B_Cu),(8.00,9.50,pcbnew.B_Cu),
                (90.00,9.50,pcbnew.B_Cu),(90.00,19.50,pcbnew.B_Cu),(107.50,19.50,pcbnew.B_Cu),(107.50,9.50,pcbnew.B_Cu),
                (112.50,9.50,pcbnew.B_Cu),(112.50,9.50,pcbnew.F_Cu),(114.00,9.50,pcbnew.F_Cu),(114.00,9.50,pcbnew.B_Cu),
                (150.00,9.50,pcbnew.B_Cu),(150.00,20.00,pcbnew.B_Cu),(164.00,20.00,pcbnew.B_Cu),(164.00,9.50,pcbnew.B_Cu),
                (197.00,9.50,pcbnew.B_Cu),(197.00,52.00,pcbnew.B_Cu),(202.50,52.00,pcbnew.B_Cu),(202.50,50.00,pcbnew.B_Cu),
                (202.50,50.00,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return list(reversed(p)) if a['ref']=='R_ACT_FAULT_PU' else p

        old=v4.VIA_COST
        try:
            if net=='PUMP_DIR': v4.VIA_COST=20.0
            elif net in HIGH_COST: v4.VIA_COST=32.0
            else: v4.VIA_COST=12.0
            return super()._astar(net,a,z)
        finally:
            v4.VIA_COST=old

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r.setdefault('planner',{}).update({
            'via_cost_policy':'HIGH_COST=32; PUMP_DIR=20; resto=12',
            'act_fault_i2c_bypass':'B y19.5 hasta x107.5; baja a y9.5 a la derecha de SDA/SCL',
        })
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); v15.eco_co2_ilim(board)
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV16(board,placement,routing,batches); manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V16',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
