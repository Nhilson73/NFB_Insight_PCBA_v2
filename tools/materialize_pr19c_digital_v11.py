#!/usr/bin/env python3
"""PR19C v11: v10 + corredor local RPU→PUMP para ACT_FAULT_N.

Cruza en F.Cu la barrera vertical de PUMP_CURRENT_ADC (B.Cu x≈203.5),
baja por B.Cu al este de esa barrera y entra al pad 18 del driver desde +X.
No modifica reglas KiCad, placement ni contratos.
"""
from __future__ import annotations
import json
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v7 as v7
import materialize_pr19c_digital_v10 as v10

CANDIDATE_REVISION='v11-act-rpu-pump-local-corridor'

class RouterV11(v10.RouterV10):
    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'R_ACT_FAULT_PU','U_PUMP_DRV'}:
            # RPU exacto está en F.Cu. Se cruza x203.5 en F.Cu y se cambia
            # a B.Cu solo al este; luego se retorna a F.Cu para entrar al pad18.
            nodes=[
                (200.75,50.00,pcbnew.F_Cu),
                (204.75,50.00,pcbnew.F_Cu),
                (204.75,50.00,pcbnew.B_Cu),
                (204.75,20.50,pcbnew.B_Cu),
                (213.50,20.50,pcbnew.B_Cu),
                (213.50,20.50,pcbnew.F_Cu),
                (213.50,17.75,pcbnew.F_Cu),
                (212.25,17.75,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes)
            return p if a['ref']=='R_ACT_FAULT_PU' else list(reversed(p))
        return super()._astar(net,a,z)
    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r.setdefault('planner',{})['act_fault_rpu_pump_corridor']='F x200.75-204.75@y50; B x204.75 down y20.5 then x213.5; F entry U_PUMP_DRV.18'
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV11(board,placement,routing,batches); manifest=r.route_all(); core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V11',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
