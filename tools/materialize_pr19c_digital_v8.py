#!/usr/bin/env python3
"""PR19C v8: planner conservador de clearance + corredor ACT sin cruce I2C.

No modifica ninguna regla KiCad. Endurece el modelo interno de obstáculos para
aproximar centro-a-centro pista/vía/pad con margen positivo antes del DRC.
"""
from __future__ import annotations
import json
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v7 as v7

core.STEP=0.25
core.PAD_HALO=0.45
CANDIDATE_REVISION='v8-conservative-clearance-model'

class RouterV8(v7.RouterV7):
    def _mark_track_cells(self, table, net, layer, a, b, halo=1):
        # 0.50 mm de halo de centro: > 0.20 clearance + 0.10 radio de pista.
        return super()._mark_track_cells(table,net,layer,a,b,halo=max(2,halo))

    def _mark_via(self, net, x, y, halo=1):
        # Vía 0.60 mm: radio 0.30 + 0.20 clearance => >=0.50 mm.
        # 3 celdas = 0.75 mm, deliberadamente conservador.
        return super()._mark_via(net,x,y,halo=max(3,halo))

    def _astar(self,net,a,z):
        if net=='ACT_FAULT_N' and {a['ref'],z['ref']}=={'J_UNOQ','R_ACT_FAULT_PU'}:
            # Bypass adicional F.Cu x89-99 para cruzar las bajadas I2C en B.Cu.
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),(8.00,36.50,pcbnew.B_Cu),(8.00,9.50,pcbnew.B_Cu),
                (89.00,9.50,pcbnew.B_Cu),(89.00,9.50,pcbnew.F_Cu),(99.00,9.50,pcbnew.F_Cu),(99.00,9.50,pcbnew.B_Cu),
                (104.50,9.50,pcbnew.B_Cu),(104.50,9.50,pcbnew.F_Cu),(112.50,9.50,pcbnew.F_Cu),(112.50,9.50,pcbnew.B_Cu),
                (157.50,9.50,pcbnew.B_Cu),(157.50,9.50,pcbnew.F_Cu),(161.00,9.50,pcbnew.F_Cu),(161.00,9.50,pcbnew.B_Cu),
                (196.00,9.50,pcbnew.B_Cu),(196.00,50.50,pcbnew.B_Cu),(199.00,50.50,pcbnew.B_Cu),
                (199.00,50.50,pcbnew.F_Cu),(200.75,50.50,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes)
            return list(reversed(p)) if a['ref']=='R_ACT_FAULT_PU' else p
        return super()._astar(net,a,z)

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r.setdefault('planner',{}).update({
            'pad_halo_mm':core.PAD_HALO,
            'track_cell_halo':2,
            'via_cell_halo':3,
            'clearance_model':'CONSERVATIVE_POSITIVE_MARGIN',
            'act_fault_corridor':'B y9.5 with F bypasses x89-99, x104.5-112.5, x157.5-161; B rise x196',
        })
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB))
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV8(board,placement,routing,batches); manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V8',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
