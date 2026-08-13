#!/usr/bin/env python3
"""PR19A v14: v13 + micro-ruta DVDT en corredor exterior separado.

UVLO/OVLO ya ocupan el corredor izquierdo natural de U_EFUSE.7. Reordenar no
resolvió DVDT, por lo que se asigna una ruta local determinista:

U_EFUSE.7 -> lateral derecho -> banda superior baja -> C_EFUSE_DVDT.1

DVDT usa y=23.40 mm; ILM conserva y=24.20 mm. La separación entre ambas bandas
es 0.80 mm, superior al mínimo centro-centro necesario para pistas de 0.20 mm
con clearance 0.25 mm. No se añaden reglas DRC, neckdowns ni vías.
"""
from __future__ import annotations

import math

import pcbnew  # type: ignore
import materialize_pr19a_local as impl
import materialize_pr19a_local_v13 as v13
import pr19a_router_core as base

DVDT_WAYPOINTS = [
    (181.000, 16.950),
    (181.000, 23.400),
    (175.635, 23.400),
]


def _key(ep: dict) -> tuple[str, str]:
    return str(ep.get("ref")), str(ep.get("pad"))


class RouterPR19AV14(v13.v12.RouterPR19AV12):
    def _is_dvdt_edge(self, net: str, start_ep: dict, goal_ep: dict) -> bool:
        return net == "EFUSE_DVDT" and {_key(start_ep), _key(goal_ep)} == {
            ("U_EFUSE", "7"), ("C_EFUSE_DVDT", "1")
        }

    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        if self._is_dvdt_edge(net, start_ep, goal_ep):
            return [(0, 0, pcbnew.F_Cu)]
        return super()._astar(net, cls, start_ep, goal_ep, xmin, xmax)

    def _mark_continuous_segment_v14(self, net: str, a: tuple[float, float], b: tuple[float, float]) -> None:
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
        if not self._is_dvdt_edge(net, start_ep, goal_ep):
            return super()._materialize_path(net, cls, clsinfo, path, start_ep, goal_ep)

        if _key(start_ep) == ("U_EFUSE", "7"):
            u, c = start_ep, goal_ep
        else:
            u, c = goal_ep, start_ep
        width = float(clsinfo["track_width_mm_min"])
        points = [
            (float(u["x_mm"]), float(u["y_mm"])),
            *DVDT_WAYPOINTS,
            (float(c["x_mm"]), float(c["y_mm"])),
        ]
        print("MICROROUTE EFUSE_DVDT", points)
        for a, b in zip(points, points[1:]):
            self._add_track(net, pcbnew.F_Cu, width, a, b)
            self._mark_continuous_segment_v14(net, a, b)


impl.CONTROL_RANK = {n: i for i, n in enumerate(v13.CONTROL_ORDER_V13)}
impl.RouterPR19A = RouterPR19AV14

if __name__ == "__main__":
    raise SystemExit(impl.main())
