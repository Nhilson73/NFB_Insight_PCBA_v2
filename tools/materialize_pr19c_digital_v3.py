#!/usr/bin/env python3
"""PR19C v3: micro-route explícito para UNO_IOREF_3V3 + A* para el resto.

La rejilla de 0.5 mm no representa la garganta entre R_5V_EN_PD y U_5V.2.
Se usa un cruce B.Cu local con dos vías; no se modifican clearances ni reglas.
KiCad 10.0.5 DRC sigue siendo la autoridad física final.
"""
from __future__ import annotations

import json
import math
import pcbnew  # type: ignore

import materialize_pr19c_digital as core

CANDIDATE_REVISION = "v3-uno-ioref-microroute-grid-aligned"


def edge_len(eps, edge):
    i, j = edge
    a, b = eps[i], eps[j]
    return abs(a['x_mm']-b['x_mm']) + abs(a['y_mm']-b['y_mm'])


class RouterV3(core.Router):
    def _manual_segment(self, net: str, layer: int, a: tuple[float,float], b: tuple[float,float]) -> float:
        width = float(self.class_info[self.class_by_net[net]]['track_width_mm_min'])
        self._add_track(net, layer, width, a, b)
        self._mark_track_cells(self.track_occ, net, layer, a, b, halo=1)
        return math.hypot(b[0]-a[0], b[1]-a[1])

    def _manual_uno_ioref_local(self, eps: list[dict]) -> tuple[int,int,int,float]:
        by_ref = {e['ref']: e for e in eps}
        r = by_ref['R_5V_EN_PD']
        u = by_ref['U_5V']
        if r['pad'] != '1' or u['pad'] != '2':
            core.fail('endpoints UNO_IOREF_3V3 inesperados')
        before_s, before_v = len(self.new_segments), len(self.new_vias)
        clsinfo = self.class_info[self.class_by_net['UNO_IOREF_3V3']]
        # Coordenadas de vía alineadas a la rejilla efectiva de 0.5 mm.
        # V1 queda por encima de 5V_PGOOD; V2 queda a la izquierda del RDN.
        v1 = (190.000, 28.000)
        v2 = (190.500, 18.000)
        length = 0.0
        length += self._manual_segment('UNO_IOREF_3V3', pcbnew.F_Cu, (r['x_mm'], r['y_mm']), v1)
        self._add_via('UNO_IOREF_3V3', clsinfo, core.gcoord(v1[0]), core.gcoord(v1[1]))
        length += self._manual_segment('UNO_IOREF_3V3', pcbnew.B_Cu, v1, (v2[0], v1[1]))
        length += self._manual_segment('UNO_IOREF_3V3', pcbnew.B_Cu, (v2[0], v1[1]), v2)
        self._add_via('UNO_IOREF_3V3', clsinfo, core.gcoord(v2[0]), core.gcoord(v2[1]))
        length += self._manual_segment('UNO_IOREF_3V3', pcbnew.F_Cu, v2, (u['x_mm'], u['y_mm']))
        return len(self.new_segments)-before_s, len(self.new_vias)-before_v, 2, length

    def route_all(self) -> dict:
        batch = self.batches['PR19C']
        if batch['nets'] != core.TARGET or int(batch['expected_net_count']) != 16:
            core.fail('contrato PR19C divergente')
        order = [
            'UNO_IOREF_3V3', 'I2C_SDA', 'I2C_SCL', 'TEMP_1WIRE',
            'HX711_DOUT', 'HX711_SCK', 'MCU_NRST', 'MCU_WDI',
            'HMI_RX', 'HMI_TX', 'ACT_FAULT_N', 'PUMP_PWM', 'PUMP_DIR',
            'CO2_SOL_CTL', 'CHILLER_CTL', 'LED_STATUS',
        ]
        for net in order:
            eps = self.pads_by_net.get(net, [])
            eps.sort(key=lambda e: (e['x_mm'], e['y_mm'], e['ref'], e['pad']))
            if len(eps) < 2:
                core.fail(f'{net}: endpoints insuficientes')
            bs = len(self.new_segments); bv = len(self.new_vias); bends = 0; length = 0.0
            if net == 'UNO_IOREF_3V3':
                _, _, b, l = self._manual_uno_ioref_local(eps)
                bends += b; length += l
                j = next(e for e in eps if e['ref'] == 'J_UNOQ')
                r = next(e for e in eps if e['ref'] == 'R_5V_EN_PD')
                path = self._astar(net, j, r)
                _, _, b, l = self._materialize(net, path, j, r)
                bends += b; length += l
                edges_count = 2
            else:
                edges = core.mst_edges(eps)
                edges.sort(key=lambda e: (round(edge_len(eps, e), 6), e[0], e[1]))
                for i, j in edges:
                    path = self._astar(net, eps[i], eps[j])
                    _, _, b, l = self._materialize(net, path, eps[i], eps[j])
                    bends += b; length += l
                edges_count = len(edges)
            stat = {
                'net': net, 'class': self.class_by_net[net],
                'endpoint_count': len(eps), 'edge_count': edges_count,
                'segment_count': len(self.new_segments)-bs,
                'via_count': len(self.new_vias)-bv,
                'bend_count': bends, 'grid_length_mm': round(length, 3),
            }
            self.net_stats.append(stat)
            print('ROUTED', stat)
        return {
            'schema_version': 1,
            'status': 'PR19C_DIGITAL_ROUTING_CANDIDATE',
            'candidate_revision': CANDIDATE_REVISION,
            'batch': 'PR19C',
            'target_nets': core.TARGET,
            'baseline': {'segments': core.PRIOR_SEGMENTS, 'vias': core.PRIOR_VIAS},
            'net_stats': self.net_stats,
            'new_segments': self.new_segments,
            'new_vias': self.new_vias,
            'new_segment_count': len(self.new_segments),
            'new_via_count': len(self.new_vias),
            'policies': {'in1_signal_tracks': 0, 'zones_added': 0, 'future_batch_copper': 0},
        }


def main() -> int:
    board = pcbnew.LoadBoard(str(core.PCB))
    try:
        if len(list(board.Zones())) != 0:
            core.fail('PR19C no parte de board con copper zones')
    except AttributeError:
        pass
    placement = json.loads(core.PLACEMENT.read_text(encoding='utf-8'))
    routing = json.loads(core.ROUTING.read_text(encoding='utf-8'))
    batches = json.loads(core.BATCHES.read_text(encoding='utf-8'))
    if placement.get('status') != 'PRODUCTION_PLACEMENT_PR17': core.fail('placement no es PR17')
    if routing.get('status') != 'ROUTING_READINESS_PR18': core.fail('routing contract no es PR18')
    r = RouterV3(board, placement, routing, batches)
    manifest = r.route_all()
    core.OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    pcbnew.SaveBoard(str(core.PCB), board)
    print('PR19C_CANDIDATE_V3', len(manifest['target_nets']), manifest['new_segment_count'], manifest['new_via_count'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
