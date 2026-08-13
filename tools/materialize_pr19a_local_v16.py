#!/usr/bin/env python3
"""PR19A v16: microtopología conjunta PUMP_DIR_DRV / PUMP_PWM_DRV.

Los pines 3/4 del DRV8242 están adyacentes y sus resistores/pulldowns quedan
ordenados de forma que dos corredores F.Cu se cruzan. Se asigna:
- PUMP_DIR_DRV: breakout F.Cu -> B.Cu -> F.Cu, 2 vías;
- PUMP_PWM_DRV: corredor exterior F.Cu, 0 vías.

No cambia placement, netclass ni clearances. KiCad DRC es autoridad final.
"""
from __future__ import annotations

import math
import pcbnew  # type: ignore
import materialize_pr19a_local as impl
import materialize_pr19a_local_v15 as v15
import pr19a_router_core as base


def _key(ep: dict) -> tuple[str, str]:
    return str(ep.get("ref")), str(ep.get("pad"))


class RouterPR19AV16(v15.RouterPR19AV15):
    def _is_dir_edge(self, net: str, a: dict, b: dict) -> bool:
        return net == "PUMP_DIR_DRV" and {_key(a), _key(b)} == {
            ("R_PUMP_DIR_SER", "2"), ("U_PUMP_DRV", "3")
        }

    def _is_pwm_edge(self, net: str, a: dict, b: dict) -> bool:
        return net == "PUMP_PWM_DRV" and {_key(a), _key(b)} == {
            ("R_PUMP_PWM_PD", "1"), ("U_PUMP_DRV", "4")
        }

    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        if self._is_dir_edge(net, start_ep, goal_ep) or self._is_pwm_edge(net, start_ep, goal_ep):
            return [(0, 0, pcbnew.F_Cu)]
        return super()._astar(net, cls, start_ep, goal_ep, xmin, xmax)

    def _mark_segment(self, net: str, layer: int, a: tuple[float, float], b: tuple[float, float]) -> None:
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
        self._mark_track(net, layer, cells, halo=2)

    def _track(self, net: str, layer: int, width: float, a, b) -> None:
        self._add_track(net, layer, width, a, b)
        self._mark_segment(net, layer, a, b)

    def _materialize_path(self, net, cls, clsinfo, path, start_ep, goal_ep):
        if self._is_dir_edge(net, start_ep, goal_ep):
            if _key(start_ep) == ("U_PUMP_DRV", "3"):
                u, r = start_ep, goal_ep
            else:
                u, r = goal_ep, start_ep
            width = float(clsinfo["track_width_mm_min"])
            p0 = (float(u["x_mm"]), float(u["y_mm"]))
            v1 = (208.25, 17.75)
            v2 = (208.25, 21.75)
            p3 = (float(r["x_mm"]), float(r["y_mm"]))
            print("MICROPAIR PUMP_DIR_DRV", [p0, v1, v2, p3])
            self._track(net, pcbnew.F_Cu, width, p0, v1)
            self._add_via(net, clsinfo, base.gcoord(v1[0]), base.gcoord(v1[1]))
            self._track(net, pcbnew.B_Cu, width, v1, v2)
            self._add_via(net, clsinfo, base.gcoord(v2[0]), base.gcoord(v2[1]))
            self._track(net, pcbnew.F_Cu, width, v2, p3)
            return

        if self._is_pwm_edge(net, start_ep, goal_ep):
            if _key(start_ep) == ("U_PUMP_DRV", "4"):
                u, r = start_ep, goal_ep
            else:
                u, r = goal_ep, start_ep
            width = float(clsinfo["track_width_mm_min"])
            points = [
                (float(u["x_mm"]), float(u["y_mm"])),
                (207.50, float(u["y_mm"])),
                (207.50, 21.50),
                (float(r["x_mm"]), 21.50),
                (float(r["x_mm"]), float(r["y_mm"])),
            ]
            print("MICROPAIR PUMP_PWM_DRV", points)
            for a, b in zip(points, points[1:]):
                self._track(net, pcbnew.F_Cu, width, a, b)
            return

        return super()._materialize_path(net, cls, clsinfo, path, start_ep, goal_ep)


impl.RouterPR19A = RouterPR19AV16

if __name__ == "__main__":
    raise SystemExit(impl.main())
