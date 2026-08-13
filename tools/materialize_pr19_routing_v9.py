#!/usr/bin/env python3
"""PR19 v9: v8 + escape determinista del pin 5 TPS1HC120.

El pad 5 (CO2_OPENLOAD_N) está en el borde inferior derecho del DYC0008A.
El planificador A* usa una rejilla que no puede alcanzar su centro sin considerar
ocupada toda la garganta del footprint. Para ese único pin se desplaza el objetivo
0.60 mm hacia -Y, fuera del courtyard; `_materialize_path` conserva la conexión
recta desde ese waypoint al centro real del pad. No se relaja ningún clearance.
KiCad DRC sigue siendo la autoridad final.
"""
from __future__ import annotations

import materialize_pr19_routing as base
import materialize_pr19_routing_v8 as v8

ESCAPE_MM = 0.60


class RouterV9(v8.RouterV8):
    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        s = start_ep
        g = goal_ep
        if net == "CO2_OPENLOAD_N":
            if s.get("ref") == "U_CO2_DRV" and str(s.get("pad")) == "5":
                s = dict(s)
                s["y_mm"] = float(s["y_mm"]) + ESCAPE_MM
                # La función se reutiliza en ambos sentidos; +Y cuando el pin es start
                # mantiene el waypoint fuera del pad sin alterar el endpoint real.
            if g.get("ref") == "U_CO2_DRV" and str(g.get("pad")) == "5":
                g = dict(g)
                g["y_mm"] = float(g["y_mm"]) + ESCAPE_MM
        return super()._astar(net, cls, s, g, xmin, xmax)


base.Router = RouterV9

if __name__ == "__main__":
    raise SystemExit(base.main())
