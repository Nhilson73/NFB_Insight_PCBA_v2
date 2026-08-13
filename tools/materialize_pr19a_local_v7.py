#!/usr/bin/env python3
"""PR19A v7: v6 + micro-ruta continua para el strap RT->5V_VCC.

La geometría exacta deja un corredor legal de ~0.13 mm para el *centro* de
pista entre las exclusiones de U_5V.1 y R_5V_FBB. La rejilla A* de 0.25 mm no
puede muestrearlo. En vez de degradar todo el lote a una rejilla 5x más fina,
este archivo congela una micro-ruta determinista solo para C_5V_VCC.1 ->
U_5V.11. KiCad DRC sigue siendo la autoridad física final.
"""
from __future__ import annotations

import math

import pcbnew  # type: ignore
import materialize_pr19a_local as impl
import materialize_pr19a_local_v6 as v6
import pr19a_router_core as base

# Waypoints continuos elegidos desde la geometría real post-ECO PR22.
# - y=16.60 mm atraviesa la ventana entre el borde inferior de U_5V.1
#   (con neckdown local) y la exclusión normal de R_5V_FBT/FBB.
# - x=190.90 mm pasa a la izquierda del divisor FB con clearance normal.
# - y=14.15 mm pasa por debajo de ambos resistores con clearance normal.
RT_STRAP_WAYPOINTS = [
    (194.525, 14.150),
    (190.900, 14.150),
    (190.900, 16.600),
    (192.575, 16.600),
]


def _key(ep: dict) -> tuple[str, str]:
    return str(ep.get("ref")), str(ep.get("pad"))


class RouterPR19AV7(v6.RouterPR19AV6):
    def _is_rt_strap_edge(self, net: str, start_ep: dict, goal_ep: dict) -> bool:
        return net == "5V_VCC" and {_key(start_ep), _key(goal_ep)} == {
            ("C_5V_VCC", "1"), ("U_5V", "11")
        }

    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        if self._is_rt_strap_edge(net, start_ep, goal_ep):
            # Placeholder: _materialize_path maneja esta arista sin rejilla.
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
        if not self._is_rt_strap_edge(net, start_ep, goal_ep):
            return super()._materialize_path(net, cls, clsinfo, path, start_ep, goal_ep)

        # Normalizar dirección CAP -> RT para que el manifest sea determinista.
        if _key(start_ep) == ("C_5V_VCC", "1"):
            cap, rt = start_ep, goal_ep
        else:
            cap, rt = goal_ep, start_ep

        width = float(clsinfo["track_width_mm_min"])
        points = [
            (float(cap["x_mm"]), float(cap["y_mm"])),
            *RT_STRAP_WAYPOINTS,
            (float(rt["x_mm"]), float(rt["y_mm"])),
        ]
        print("MICROROUTE 5V_VCC RT", points)
        for a, b in zip(points, points[1:]):
            self._add_track(net, pcbnew.F_Cu, width, a, b)
            self._mark_continuous_segment(net, a, b)


impl.RouterPR19A = RouterPR19AV7

if __name__ == "__main__":
    raise SystemExit(impl.main())
