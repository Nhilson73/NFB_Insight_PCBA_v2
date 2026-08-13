#!/usr/bin/env python3
"""PR19A v6: v5 + neckdown físico estrictamente local para 5V_VCC/U_5V.

El `.kicad_dru` permite 0.125 mm únicamente cuando una pista `5V_VCC`
intersecta el courtyard de `U_5V` frente a objetos pertenecientes a `U_5V`.
Este planner replica esa misma geometría para poder encontrar el breakout, pero
fuera de la microzona vuelve al clearance normal de CONTROL_SENSITIVE.
"""
from __future__ import annotations

import materialize_pr19a_local as impl
import materialize_pr19a_local_v5 as v5
import pr19a_router_core as base

NECKDOWN_CLEARANCE_MM = 0.125
TRACK_WIDTH_5V_VCC_MM = 0.20
NECKDOWN_CENTER_MARGIN_MM = NECKDOWN_CLEARANCE_MM + TRACK_WIDTH_5V_VCC_MM / 2.0


class RouterPR19AV6(v5.RouterPR19AV5):
    def __init__(self, board, placement, contract, probe, batch):
        super().__init__(board, placement, contract, probe, batch)
        u5 = self._placement_by_ref["U_5V"]
        self._u5_courtyard = tuple(float(x) for x in u5["courtyard_global_mm"])

    def _inside_u5_courtyard(self, x: float, y: float) -> bool:
        x0, y0, x1, y1 = self._u5_courtyard
        return x0 <= x <= x1 and y0 <= y <= y1

    def _blocked(self, state, net: str, xmin: float, xmax: float) -> bool:
        ix, iy, layer = state
        if not self._inside(ix, iy, xmin, xmax):
            return True
        x, y = base.xy(ix, iy)
        normal_margin = self._class_margin(net)
        in_neckdown = net == "5V_VCC" and self._inside_u5_courtyard(x, y)

        for owner, ref, _pad, rect in self._foreign_pads[layer]:
            if owner == net:
                continue
            margin = (
                NECKDOWN_CENTER_MARGIN_MM
                if in_neckdown and ref == "U_5V"
                else normal_margin
            )
            if self._inside_expanded(x, y, rect, margin):
                return True

        owners = self.track_occ[layer].get((ix, iy), set())
        if any(owner != net for owner in owners):
            return True
        viaowners = self.via_occ.get((ix, iy), set())
        if any(owner != net for owner in viaowners):
            return True
        return False


impl.RouterPR19A = RouterPR19AV6

if __name__ == "__main__":
    print(
        "NECKDOWN 5V_VCC/U_5V",
        "clearance_mm", NECKDOWN_CLEARANCE_MM,
        "planner_center_margin_mm", NECKDOWN_CENTER_MARGIN_MM,
    )
    raise SystemExit(impl.main())
