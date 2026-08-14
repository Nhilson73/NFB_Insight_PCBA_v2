#!/usr/bin/env python3
"""PR19C v9: v8 + micro-escape local ACT_FAULT_N entre drivers Z4."""
from __future__ import annotations
import json
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v5 as v5
import materialize_pr19c_digital_v8 as v8

CANDIDATE_REVISION='v9-act-local-driver-escape'

class RouterV9(v8.RouterV8):
    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'U_CO2_DRV','U_PUMP_DRV'}:
            # Pad U_PUMP_DRV.18 queda entre pads 17/19; la única salida limpia
            # es horizontal hacia +X y luego por encima de C_CO2_DRV.
            pump=a if a['ref']=='U_PUMP_DRV' else z
            co2=z if z['ref']=='U_CO2_DRV' else a
            pts=[
                (pump['x_mm'],pump['y_mm']),
                (213.00,17.75),(213.00,19.00),(216.75,19.00),(216.75,18.50),
                (co2['x_mm'],co2['y_mm']),
            ]
            p=v5.grid_path(pts,pcbnew.F_Cu)
            return p if a['ref']=='U_PUMP_DRV' else list(reversed(p))
        return super()._astar(net,a,z)
    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r.setdefault('planner',{})['act_fault_local_driver_escape']='U_PUMP_DRV.18 -> x213/y19 -> U_CO2_DRV.1 on F.Cu'
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV9(board,placement,routing,batches); manifest=r.route_all(); core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V9',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
