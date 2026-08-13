#!/usr/bin/env python3
"""PR19 v5: rejilla 0.25 mm + orden de escape por borde de IC.

TPSM33625: VCC -> FB -> PGOOD.
TPS259470A: ILM/ITIMER salen antes de DVDT y del divisor EN/OVLO.
No modifica clearances ni anchos; KiCad DRC sigue siendo autoridad.
"""
import materialize_pr19_routing as base

base.STEP = 0.25
base.PAD_HALO = 0.05
base.MAX_EXPANSIONS = 900_000

NET_ORDER = [
    "5V_VCC", "5V_FB", "5V_PGOOD",
    "EFUSE_ILM", "EFUSE_ITIMER", "EFUSE_DVDT", "EFUSE_EN_UVLO", "EFUSE_OVLO",
    "CO2_ILIM", "PUMP_SR_CFG",
]
NET_RANK = {n: i for i, n in enumerate(NET_ORDER)}


class RouterV5(base.Router):
    def route(self) -> dict:
        routes_by_net = {r["net"]: r for r in self.probe["routes"]}
        to_route, deferred = [], []
        for net, cls in sorted(self.by_net.items()):
            if cls in base.ROUTE_CLASSES:
                to_route.append(net)
            elif cls in base.DEFER_CLASSES:
                deferred.append(net)
            else:
                base.fail(f"clase sin política PR19: {cls}")

        class_priority = {
            "FIELD_ANALOG_LOCAL": 0,
            "CONTROL_SENSITIVE": 1,
            "ANALOG_SENSITIVE": 2,
            "CHILLER_DRY_CONTACT": 3,
            "DIGITAL_LOW_SPEED": 4,
        }
        to_route.sort(key=lambda net: (
            class_priority[self.by_net[net]],
            0 if routes_by_net[net]["mode"].startswith("LOCAL") else 1,
            NET_RANK.get(net, 1000),
            net,
        ))

        net_stats = []
        for net in to_route:
            cls = self.by_net[net]
            clsinfo = self.by_class[cls]
            route = routes_by_net[net]
            eps = self.pads_by_net.get(net, [])
            if len(eps) != int(route["endpoint_count"]):
                base.fail(f"{net}: endpoints board/probe divergen {len(eps)} != {route['endpoint_count']}")
            eps.sort(key=lambda e: (e["ref"], e["pad"], round(e["x_mm"], 4), round(e["y_mm"], 4)))
            xmin, xmax = base.route_bounds(route, self.placement)
            edges = base.mst_edges(eps)
            before_s, before_v = len(self.segments), len(self.vias)
            for i, j in edges:
                path = self._astar(net, cls, eps[i], eps[j], xmin, xmax)
                self._materialize_path(net, cls, clsinfo, path, eps[i], eps[j])
            net_stats.append({
                "net": net, "class": cls, "mode": route["mode"],
                "edge_count": len(edges),
                "segment_count": len(self.segments) - before_s,
                "via_count": len(self.vias) - before_v,
            })
            print("ROUTED", net, cls, route["mode"], "edges", len(edges), "segments", len(self.segments)-before_s, "vias", len(self.vias)-before_v)

        return {
            "schema_version": 1,
            "status": "SIGNAL_ROUTING_PR19",
            "scope": "SIGNALS_CONTROL_ONLY_POWER_GND_DEFERRED_PR20",
            "grid_mm": base.STEP,
            "board_mm": [self.width, self.height],
            "routed_classes": sorted(base.ROUTE_CLASSES),
            "deferred_classes": sorted(base.DEFER_CLASSES),
            "routed_nets": to_route,
            "deferred_nets": deferred,
            "net_stats": net_stats,
            "segments": self.segments,
            "vias": self.vias,
        }


base.Router = RouterV5

if __name__ == "__main__":
    raise SystemExit(base.main())
