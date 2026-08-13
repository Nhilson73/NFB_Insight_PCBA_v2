#!/usr/bin/env python3
"""PR19 v10: v9 + escape corto del pin 4 TPS1HC120 (CO2_EN_DRV)."""
from __future__ import annotations

import materialize_pr19_routing as base
import materialize_pr19_routing_v9 as v9

ESCAPE_MM = 0.60


class RouterV10(v9.RouterV9):
    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        s = start_ep
        g = goal_ep
        if net == "CO2_EN_DRV":
            if s.get("ref") == "U_CO2_DRV" and str(s.get("pad")) == "4":
                s = dict(s)
                s["y_mm"] = float(s["y_mm"]) - ESCAPE_MM
            if g.get("ref") == "U_CO2_DRV" and str(g.get("pad")) == "4":
                g = dict(g)
                g["y_mm"] = float(g["y_mm"]) - ESCAPE_MM
        return super()._astar(net, cls, s, g, xmin, xmax)


base.Router = RouterV10

if __name__ == "__main__":
    raise SystemExit(base.main())
