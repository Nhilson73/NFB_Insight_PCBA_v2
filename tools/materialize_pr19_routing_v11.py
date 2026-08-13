#!/usr/bin/env python3
"""PR19 v11: router direccional por carriles para routing de producción.

Mejoras frente al A* inicial:
- rejilla 0.25 mm para pitch fino;
- estado incluye dirección previa y penaliza giros innecesarios;
- nets CHANNEL_B siguen el carril `trunk_y_mm` calculado por el probe;
- B.Cu se prefiere fuertemente para troncales inter-zona;
- escapes locales de TPS1HC120 pins 4/5 se mantienen deterministas hacia -Y;
- In1.Cu nunca participa.

No relaja DRC, footprints, anchos ni clearances.
"""
from __future__ import annotations

import heapq

import pcbnew  # type: ignore
import materialize_pr19_routing as base

base.STEP = 0.25
base.PAD_HALO = 0.05
base.MAX_EXPANSIONS = 1_200_000

TURN_PENALTY = 0.70
VIA_COST = 10.0
LANE_WEIGHT = 0.025
ESCAPE_MM = 0.60

CONTROL_ORDER = [
    "5V_VCC", "5V_FB", "5V_PGOOD",
    "EFUSE_ILM", "EFUSE_ITIMER", "EFUSE_DVDT", "EFUSE_EN_UVLO", "EFUSE_OVLO",
    "CO2_ILIM", "PUMP_SR_CFG",
]
CONTROL_RANK = {n: i for i, n in enumerate(CONTROL_ORDER)}
EARLY_LOCAL = ["CO2_OPENLOAD_N", "CO2_EN_DRV"]
EARLY_RANK = {n: i for i, n in enumerate(EARLY_LOCAL)}
DIGITAL_LOCAL_ORDER = [
    "PUMP_DIR_DRV", "PUMP_PWM_DRV",
    "CHILLER_GATE", "CHILLER_LED_A", "CHILLER_LED_K",
    "HMI_FIELD_RX", "HMI_FIELD_TX", "WDT_MR_N",
]
DIGITAL_LOCAL_RANK = {n: i for i, n in enumerate(DIGITAL_LOCAL_ORDER)}


class RouterV11(base.Router):
    def _escape_endpoint(self, net: str, ep: dict) -> dict:
        if ep.get("ref") != "U_CO2_DRV":
            return ep
        pin = str(ep.get("pad"))
        if (net, pin) not in {("CO2_OPENLOAD_N", "5"), ("CO2_EN_DRV", "4")}:
            return ep
        out = dict(ep)
        out["y_mm"] = float(out["y_mm"]) - ESCAPE_MM
        return out

    def _layers_for(self, net: str, cls: str, channel: bool) -> list[int]:
        if channel:
            # PR18: B.Cu = secondary low-speed + long-haul control/telemetry.
            # Analog sensitive puede usar F/B; se prefiere B solo durante el troncal.
            return [pcbnew.B_Cu, pcbnew.F_Cu]
        return base.allowed_layers(cls)

    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        route = next(r for r in self.probe["routes"] if r["net"] == net)
        channel = route["mode"] == "CHANNEL_B"
        trunk_y = float(route.get("trunk_y_mm", 0.0)) if channel else None

        s_ep = self._escape_endpoint(net, start_ep)
        g_ep = self._escape_endpoint(net, goal_ep)
        layers = self._layers_for(net, cls, channel)
        starts3 = self._pad_states(s_ep, layers)
        goals3 = self._pad_states(g_ep, layers)
        goal_xyz = set(goals3)
        goal_cells = {(g[0], g[1]) for g in goals3}

        # state=(ix,iy,layer,dir); dir 0=+x,1=-x,2=+y,3=-y,4=via,-1=start
        openq = []
        dist = {}
        prev = {}

        def heuristic(st):
            ix, iy, layer, _ = st
            best = float("inf")
            for gx, gy, gl in goals3:
                h = abs(ix-gx) + abs(iy-gy) + (8 if layer != gl else 0)
                best = min(best, h)
            return best

        for ix, iy, layer in starts3:
            st = (ix, iy, layer, -1)
            dist[st] = 0.0
            prev[st] = None
            heapq.heappush(openq, (heuristic(st), 0.0, st))

        reached = None
        expansions = 0
        moves = [(1,0,0),(-1,0,1),(0,1,2),(0,-1,3)]
        while openq:
            _, g, cur = heapq.heappop(openq)
            if g != dist.get(cur):
                continue
            ix, iy, layer, pdir = cur
            if (ix, iy, layer) in goal_xyz:
                reached = cur
                break
            expansions += 1
            if expansions > base.MAX_EXPANSIONS:
                break

            nbrs = []
            for dx, dy, ndir in moves:
                nbrs.append((ix+dx, iy+dy, layer, ndir))
            if len(layers) > 1:
                for other in layers:
                    if other != layer:
                        nbrs.append((ix, iy, other, 4))

            for nxt in nbrs:
                nx, ny, nl, ndir = nxt
                is_goal = (nx, ny) in goal_cells
                if not is_goal and self._blocked((nx, ny, nl), net, xmin, xmax):
                    continue

                if nl != layer:
                    owners = self.pad_occ[pcbnew.F_Cu].get((ix,iy),set()) | self.pad_occ[pcbnew.B_Cu].get((ix,iy),set())
                    if owners:
                        continue
                    step = VIA_COST
                else:
                    if channel:
                        # Long-haul prefiere B.Cu; F.Cu queda para escape/detour.
                        step = 1.0 if nl == pcbnew.B_Cu else 1.55
                        _, y = base.xy(nx, ny)
                        step += LANE_WEIGHT * abs(y - trunk_y)
                    else:
                        step = base.layer_penalty(cls, nl)
                    if pdir not in (-1,4) and ndir != pdir:
                        step += TURN_PENALTY
                    x, y = base.xy(nx, ny)
                    if net == "PUMP_CURRENT_ADC" and 163.34 <= x <= 198.34 and 8.0 <= y <= 42.0:
                        step += 5.0

                ng = g + step
                if ng + 1e-12 < dist.get(nxt, float("inf")):
                    dist[nxt] = ng
                    prev[nxt] = cur
                    heapq.heappush(openq, (ng + heuristic(nxt), ng, nxt))

        if reached is None:
            base.fail(f"sin ruta A* v11: {net} {start_ep['ref']}.{start_ep['pad']} -> {goal_ep['ref']}.{goal_ep['pad']} expansions={expansions}")

        path4 = []
        cur = reached
        while cur is not None:
            path4.append(cur)
            cur = prev[cur]
        path4.reverse()
        # Quitar dirección para el materializador base y deduplicar estados iguales.
        path3 = []
        for ix, iy, layer, _ in path4:
            p = (ix, iy, layer)
            if not path3 or p != path3[-1]:
                path3.append(p)
        return path3

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

        def key(net: str):
            cls = self.by_net[net]
            route = routes_by_net[net]
            local = route["mode"].startswith("LOCAL")
            if cls == "FIELD_ANALOG_LOCAL":
                return (0, 0, 0, net)
            if cls == "CONTROL_SENSITIVE" and local:
                return (1, CONTROL_RANK.get(net,1000), 0, net)
            if net in EARLY_RANK:
                return (2, EARLY_RANK[net], 0, net)
            if cls == "ANALOG_SENSITIVE" and local:
                return (3, 0, 0, net)
            if cls == "CHILLER_DRY_CONTACT":
                return (4, 0, 0, net)
            if cls == "DIGITAL_LOW_SPEED" and local:
                return (4, DIGITAL_LOCAL_RANK.get(net,1000), 1, net)
            if route["mode"] == "CHANNEL_B":
                return (5, round(float(route["trunk_y_mm"]),3), 0, net)
            return (6, 0, 0, net)

        to_route.sort(key=key)
        net_stats = []
        for net in to_route:
            cls = self.by_net[net]
            clsinfo = self.by_class[cls]
            route = routes_by_net[net]
            eps = self.pads_by_net.get(net, [])
            if len(eps) != int(route["endpoint_count"]):
                base.fail(f"{net}: endpoints board/probe divergen {len(eps)} != {route['endpoint_count']}")
            eps.sort(key=lambda e:(e["ref"],e["pad"],round(e["x_mm"],4),round(e["y_mm"],4)))
            xmin, xmax = base.route_bounds(route, self.placement)
            edges = base.mst_edges(eps)
            bs,bv = len(self.segments),len(self.vias)
            for i,j in edges:
                path = self._astar(net,cls,eps[i],eps[j],xmin,xmax)
                self._materialize_path(net,cls,clsinfo,path,eps[i],eps[j])
            stats = {
                "net":net,"class":cls,"mode":route["mode"],"edge_count":len(edges),
                "segment_count":len(self.segments)-bs,"via_count":len(self.vias)-bv,
            }
            net_stats.append(stats)
            print("ROUTED",net,cls,route["mode"],"edges",stats["edge_count"],"segments",stats["segment_count"],"vias",stats["via_count"])

        return {
            "schema_version":1,
            "status":"SIGNAL_ROUTING_PR19",
            "scope":"SIGNALS_CONTROL_ONLY_POWER_GND_DEFERRED_PR20",
            "router":"DIRECTIONAL_ASTAR_LANES_V11",
            "grid_mm":base.STEP,
            "board_mm":[self.width,self.height],
            "routed_classes":sorted(base.ROUTE_CLASSES),
            "deferred_classes":sorted(base.DEFER_CLASSES),
            "routed_nets":to_route,
            "deferred_nets":deferred,
            "net_stats":net_stats,
            "segments":self.segments,
            "vias":self.vias,
            "policies":{
                "in1_signal_routing":False,
                "channel_b_lane_weight":LANE_WEIGHT,
                "turn_penalty":TURN_PENALTY,
                "fine_pitch_escape_mm":ESCAPE_MM,
            },
        }


base.Router = RouterV11

if __name__ == "__main__":
    raise SystemExit(base.main())
