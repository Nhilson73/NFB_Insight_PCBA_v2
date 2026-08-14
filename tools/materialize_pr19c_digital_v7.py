#!/usr/bin/env python3
"""PR19C v7: corredor explícito para ACT_FAULT_N.

El long-haul J_UNOQ.25 -> R_ACT_FAULT_PU.2 cruza tres barreras B.Cu ya
materializadas. Se fija un carril B.Cu y dos bypass locales F.Cu, sin cambiar
placement, netclasses, clearances ni In1.Cu. Las ramas locales siguen con A*.
"""
from __future__ import annotations
import json
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v6 as v6

CANDIDATE_REVISION='v7-act-fault-explicit-corridor'


def mixed_grid_path(nodes):
    """nodes=[(x,y,layer), ...], ortogonal; permite cambio de capa mismo XY."""
    out=[]
    for idx,(x,y,layer) in enumerate(nodes):
        gx,gy=core.gcoord(x),core.gcoord(y)
        if idx==0:
            out.append((gx,gy,layer,-1)); continue
        px,py,player,_=out[-1]
        if player!=layer:
            if (px,py)!=(gx,gy): core.fail('cambio de capa ACT debe conservar XY')
            out.append((gx,gy,layer,4)); continue
        if px!=gx and py!=gy: core.fail(f'tramo ACT no ortogonal {(px,py)}->{(gx,gy)}')
        dx=0 if px==gx else (1 if gx>px else -1); dy=0 if py==gy else (1 if gy>py else -1)
        cx,cy=px,py
        while (cx,cy)!=(gx,gy):
            cx+=dx; cy+=dy
            nd=0 if dx>0 else 1 if dx<0 else 2 if dy>0 else 3
            out.append((cx,cy,layer,nd))
    return out


class RouterV7(v6.RouterV6):
    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'J_UNOQ','R_ACT_FAULT_PU'}:
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),
                (8.00,36.50,pcbnew.B_Cu),(8.00,9.50,pcbnew.B_Cu),(105.00,9.50,pcbnew.B_Cu),
                (105.00,9.50,pcbnew.F_Cu),(112.00,9.50,pcbnew.F_Cu),(112.00,9.50,pcbnew.B_Cu),
                (158.00,9.50,pcbnew.B_Cu),(158.00,9.50,pcbnew.F_Cu),(160.50,9.50,pcbnew.F_Cu),(160.50,9.50,pcbnew.B_Cu),
                (196.50,9.50,pcbnew.B_Cu),(196.50,49.50,pcbnew.B_Cu),(199.50,49.50,pcbnew.B_Cu),
                (199.50,49.50,pcbnew.F_Cu),(200.75,49.50,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=mixed_grid_path(nodes)
            if a['ref']=='R_ACT_FAULT_PU':
                # Invertir también la dirección del path; el materializador no usa
                # el código de dirección para geometría, solo XYZ/capa.
                p=list(reversed(p))
            return p
        return super()._astar(net,a,z)

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r.setdefault('planner',{})['act_fault_corridor']='B y=9.5; F bypass x105-112 y x158-160.5; B rise x196.5'
        return r


def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV7(board,placement,routing,batches); manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V7',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
