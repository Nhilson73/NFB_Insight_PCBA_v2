#!/usr/bin/env python3
"""PR19A v15: v14 + micro-ruta local para PUMP_DIR_DRV.

El planner v14 cierra las islas TPSM33625/eFuse y el par LOAD_A post-PR24,
pero la arista R_PUMP_DIR_SER.2 -> U_PUMP_DRV.3 queda confinada por el borde
izquierdo del DRV8242. Se reserva un corredor exterior simple en F.Cu.

No cambia netclass, clearance, placement ni capas permitidas. Cero vías.
KiCad DRC sigue siendo la autoridad final.
"""
from __future__ import annotations

import pcbnew  # type: ignore
import materialize_pr19a_local as impl
import materialize_pr19a_local_v14 as v14

PUMP_DIR_ESCAPE_X_MM = 0.875


def _key(ep: dict) -> tuple[str, str]:
    return str(ep.get("ref")), str(ep.get("pad"))


class RouterPR19AV15(v14.RouterPR19AV14):
    def _is_pump_dir_edge(self, net: str, start_ep: dict, goal_ep: dict) -> bool:
        return net == "PUMP_DIR_DRV" and {_key(start_ep), _key(goal_ep)} == {
            ("R_PUMP_DIR_SER", "2"), ("U_PUMP_DRV", "3")
        }

    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        if self._is_pump_dir_edge(net, start_ep, goal_ep):
            return [(0, 0, pcbnew.F_Cu)]
        return super()._astar(net, cls, start_ep, goal_ep, xmin, xmax)

    def _materialize_path(self, net, cls, clsinfo, path, start_ep, goal_ep):
        if not self._is_pump_dir_edge(net, start_ep, goal_ep):
            return super()._materialize_path(net, cls, clsinfo, path, start_ep, goal_ep)

        if _key(start_ep) == ("U_PUMP_DRV", "3"):
            u, r = start_ep, goal_ep
        else:
            u, r = goal_ep, start_ep

        width = float(clsinfo["track_width_mm_min"])
        corridor_x = float(u["x_mm"]) - PUMP_DIR_ESCAPE_X_MM
        points = [
            (float(u["x_mm"]), float(u["y_mm"])),
            (corridor_x, float(u["y_mm"])),
            (corridor_x, float(r["y_mm"])),
            (float(r["x_mm"]), float(r["y_mm"])),
        ]
        print("MICROROUTE PUMP_DIR_DRV", points)
        for a, b in zip(points, points[1:]):
            self._add_track(net, pcbnew.F_Cu, width, a, b)
            self._mark_continuous_segment_v14(net, a, b)


impl.RouterPR19A = RouterPR19AV15

if __name__ == "__main__":
    raise SystemExit(impl.main())
