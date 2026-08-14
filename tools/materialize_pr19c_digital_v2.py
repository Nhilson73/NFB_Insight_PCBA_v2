#!/usr/bin/env python3
"""Iteración PR19C v2: enruta ramas locales antes de troncales long-haul."""
from __future__ import annotations

import json
import pcbnew  # type: ignore

import materialize_pr19c_digital as core

CANDIDATE_REVISION = "v2-local-first"


def edge_len(eps, edge):
    i, j = edge
    a, b = eps[i], eps[j]
    return abs(a['x_mm']-b['x_mm']) + abs(a['y_mm']-b['y_mm'])


class RouterV2(core.Router):
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
            edges = core.mst_edges(eps)
            # La topología eléctrica puede ser MST, pero el orden físico debe
            # cerrar primero micro-islas/ramas cortas para no bloquearlas con
            # la troncal long-haul de la misma net.
            edges.sort(key=lambda e: (round(edge_len(eps, e), 6), e[0], e[1]))
            bs = len(self.new_segments); bv = len(self.new_vias); bends = 0; length = 0.0
            for i, j in edges:
                path = self._astar(net, eps[i], eps[j])
                _, _, b, l = self._materialize(net, path, eps[i], eps[j])
                bends += b; length += l
            stat = {
                'net': net, 'class': self.class_by_net[net],
                'endpoint_count': len(eps), 'edge_count': len(edges),
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
    r = RouterV2(board, placement, routing, batches)
    manifest = r.route_all()
    core.OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    pcbnew.SaveBoard(str(core.PCB), board)
    print('PR19C_CANDIDATE_V2', len(manifest['target_nets']), manifest['new_segment_count'], manifest['new_via_count'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
