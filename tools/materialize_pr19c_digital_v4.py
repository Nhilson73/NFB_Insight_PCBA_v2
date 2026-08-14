#!/usr/bin/env python3
"""PR19C v4: router direccional 0.25 mm con carriles B.Cu.

Transfiere aprendizaje del PR19 experimental sin reutilizar su cobre:
- rejilla 0.25 mm para escapes finos;
- ramas cortas se resuelven localmente;
- long-haul prefiere B.Cu y un carril por net;
- penalización fuerte de giros y vías;
- micro-route UNO_IOREF_3V3 conservado;
- In1.Cu nunca participa y DRC no se relaja.
"""
from __future__ import annotations

import heapq
import json

import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v3 as v3

# Planner más fino; no cambia reglas KiCad ni contratos.
core.STEP = 0.25
core.PAD_HALO = 0.05
core.MAX_EXPANSIONS = 1_500_000

TURN_PENALTY = 2.50
VIA_COST = 12.0
LANE_WEIGHT = 0.045
LOCAL_EDGE_MM = 24.0

# Carriles preferentes, no exclusivos. El A* puede desviarse ante cobre real.
LANES = {
    'I2C_SDA': 6.0,
    'I2C_SCL': 7.0,
    'TEMP_1WIRE': 8.5,
    'ACT_FAULT_N': 9.5,
    'CHILLER_CTL': 10.5,
    'CO2_SOL_CTL': 11.5,
    'PUMP_DIR': 12.5,
    'PUMP_PWM': 13.5,
    'LED_STATUS': 59.75,
    'UNO_IOREF_3V3': 62.25,
    'HX711_DOUT': 64.0,
    'HX711_SCK': 64.5,
    'HMI_RX': 65.0,
    'HMI_TX': 65.5,
    'MCU_WDI': 66.5,
    'MCU_NRST': 67.0,
}


class RouterV4(v3.RouterV3):
    def _astar(self, net: str, a: dict, z: dict):
        layers = self._allowed_layers(net)
        span = abs(a['x_mm']-z['x_mm']) + abs(a['y_mm']-z['y_mm'])
        channel = span >= LOCAL_EDGE_MM
        trunk_y = LANES.get(net)
        starts = self._pad_states(a, layers)
        goals = set(self._pad_states(z, layers))
        goal_cells = {(g[0], g[1]) for g in goals}

        def heuristic(st):
            ix, iy, layer, _ = st
            return min(abs(ix-gx)+abs(iy-gy)+(12 if layer != gl else 0) for gx,gy,gl,_ in goals)

        q=[]; dist={}; prev={}
        for ix,iy,layer,_ in starts:
            st=(ix,iy,layer,-1); dist[st]=0.0; prev[st]=None
            heapq.heappush(q,(heuristic(st),0.0,st))
        reached=None; expansions=0
        moves=((1,0,0),(-1,0,1),(0,1,2),(0,-1,3))
        while q:
            _,g,cur=heapq.heappop(q)
            if abs(g-dist.get(cur,float('inf'))) > 1e-12: continue
            ix,iy,layer,pdir=cur
            if any(ix==gx and iy==gy and layer==gl for gx,gy,gl,_ in goals):
                reached=cur; break
            expansions += 1
            if expansions > core.MAX_EXPANSIONS: break
            for dx,dy,ndir in moves:
                nx,ny=ix+dx,iy+dy
                if (nx,ny) not in goal_cells and self._blocked(nx,ny,layer,net): continue
                x,y=core.xy(nx,ny)
                if channel:
                    step = 1.0 if layer==pcbnew.B_Cu else 1.75
                    if trunk_y is not None and layer==pcbnew.B_Cu:
                        step += LANE_WEIGHT*abs(y-trunk_y)
                else:
                    # Ramas cortas: F.Cu preferente, B.Cu disponible para cruce.
                    step = 1.0 if layer==pcbnew.F_Cu else 1.25
                if pdir not in (-1,4) and ndir != pdir:
                    step += TURN_PENALTY
                nxt=(nx,ny,layer,ndir); ng=g+step
                if ng+1e-12 < dist.get(nxt,float('inf')):
                    dist[nxt]=ng; prev[nxt]=cur
                    heapq.heappush(q,(ng+heuristic(nxt),ng,nxt))
            for other in layers:
                if other==layer: continue
                owners=self.pad_occ[pcbnew.F_Cu].get((ix,iy),set()) | self.pad_occ[pcbnew.B_Cu].get((ix,iy),set())
                if owners: continue
                if self._blocked(ix,iy,other,net): continue
                nxt=(ix,iy,other,4); ng=g+VIA_COST
                if ng+1e-12 < dist.get(nxt,float('inf')):
                    dist[nxt]=ng; prev[nxt]=cur
                    heapq.heappush(q,(ng+heuristic(nxt),ng,nxt))
        if reached is None:
            core.fail(f"sin ruta A* v4: {net} {a['ref']}.{a['pad']}->{z['ref']}.{z['pad']} span={span:.2f} expansions={expansions}")
        path=[]; cur=reached
        while cur is not None:
            path.append(cur); cur=prev[cur]
        path.reverse()
        # Materializador espera estado 4-tupla; deduplicar xyz conservando dir.
        out=[]
        for p in path:
            if not out or p[:3] != out[-1][:3]: out.append(p)
        return out

    def route_all(self) -> dict:
        result = super().route_all()
        result['candidate_revision'] = 'v4-directional-lanes-025'
        result['planner'] = {
            'grid_mm': core.STEP,
            'pad_halo_mm': core.PAD_HALO,
            'turn_penalty': TURN_PENALTY,
            'via_cost': VIA_COST,
            'lane_weight': LANE_WEIGHT,
            'local_edge_threshold_mm': LOCAL_EDGE_MM,
            'preferred_lanes_mm': LANES,
        }
        return result


def main() -> int:
    board=pcbnew.LoadBoard(str(core.PCB))
    try:
        if len(list(board.Zones())) != 0: core.fail('PR19C no parte de board con copper zones')
    except AttributeError:
        pass
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8'))
    routing=json.loads(core.ROUTING.read_text(encoding='utf-8'))
    batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    if placement.get('status')!='PRODUCTION_PLACEMENT_PR17': core.fail('placement no es PR17')
    if routing.get('status')!='ROUTING_READINESS_PR18': core.fail('routing contract no es PR18')
    r=RouterV4(board,placement,routing,batches)
    manifest=r.route_all()
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V4',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count'])
    return 0


if __name__=='__main__':
    raise SystemExit(main())
