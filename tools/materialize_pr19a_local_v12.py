#!/usr/bin/env python3
"""PR19A v12: v11 + micro-ruta ILM por el exterior superior del eFuse.

El orden v11 cerró ITIMER + EN/UVLO + OVLO, pero esas dos últimas redes ocupan
el corredor izquierdo natural de ILM. `EFUSE_ILM` es una red estática de
programación; se le asigna un recorrido local separado:

U_EFUSE.9 -> lateral derecho -> corredor superior -> R_EFUSE_ILIM.1

No cambia clearances, netclass, capas ni placement. Se mantiene F.Cu y 0 vías.
KiCad DRC sigue siendo autoridad final.
"""
from __future__ import annotations

import math

import pcbnew  # type: ignore
import materialize_pr19a_local as impl
import materialize_pr19a_local_v11 as v11
import pr19a_router_core as base

ILM_WAYPOINTS = [
    (180.000, 18.200),
    (180.000, 24.200),
    (172.915, 24.200),
]


def _key(ep: dict) -> tuple[str, str]:
    return str(ep.get("ref")), str(ep.get("pad"))


class RouterPR19AV12(v11.v10.RouterPR19AV10):
    def _is_ilm_edge(self, net: str, start_ep: dict, goal_ep: dict) -> bool:
        return net == "EFUSE_ILM" and {_key(start_ep), _key(goal_ep)} == {
            ("U_EFUSE", "9"), ("R_EFUSE_ILIM", "1")
        }

    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        if self._is_ilm_edge(net, start_ep, goal_ep):
            return [(0, 0, pcbnew.F_Cu)]
        return super()._astar(net, cls, start_ep, goal_ep, xmin, xmax)

    def _mark_continuous_segment(self, net: str, a: tuple[float, float], b: tuple[float, float]) -> None:
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(math.ceil(length / base.STEP)))
        cells = []
        for i in range(n + 1):
            t = i / n
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            c = (base.gcoord(x), base.gcoord(y))
            if not cells or c != cells[-1]:
                cells.append(c)
        self._mark_track(net, pcbnew.F_Cu, cells, halo=2)

    def _materialize_path(self, net, cls, clsinfo, path, start_ep, goal_ep):
        if not self._is_ilm_edge(net, start_ep, goal_ep):
            return super()._materialize_path(net, cls, clsinfo, path, start_ep, goal_ep)

        if _key(start_ep) == ("U_EFUSE", "9"):
            u, r = start_ep, goal_ep
        else:
            u, r = goal_ep, start_ep
        width = float(clsinfo["track_width_mm_min"])
        points = [
            (float(u["x_mm"]), float(u["y_mm"])),
            *ILM_WAYPOINTS,
            (float(r["x_mm"]), float(r["y_mm"])),
        ]
        print("MICROROUTE EFUSE_ILM", points)
        for a, b in zip(points, points[1:]):
            self._add_track(net, pcbnew.F_Cu, width, a, b)
            self._mark_continuous_segment(net, a, b)


# Preservar el orden v11, sustituyendo únicamente la clase router.
impl.CONTROL_RANK = {n: i for i, n in enumerate(v11.CONTROL_ORDER_V11)}
impl.RouterPR19A = RouterPR19AV12

if __name__ == "__main__":
    raise SystemExit(impl.main())
