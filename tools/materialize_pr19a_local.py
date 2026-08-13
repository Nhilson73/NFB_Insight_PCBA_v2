#!/usr/bin/env python3
"""Materializa exclusivamente las 28 nets locales del lote PR19A.

El contrato `hardware/routing_batches_contract.json` es la autoridad del alcance.
No se permite cobre de lotes futuros. In1.Cu permanece reservado a GND.
"""
from __future__ import annotations

import heapq
import json
from pathlib import Path

import pcbnew  # type: ignore
import pr19a_router_core as base

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
PLACEMENT = ROOT / "hardware" / "placement_manifest.json"
ROUTING = ROOT / "hardware" / "routing_contract.json"
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
PROBE_OUT = ROOT / "hardware" / "pr19a_local_probe.json"
MANIFEST_OUT = ROOT / "hardware" / "pr19a_local_routing_manifest.json"

base.STEP = 0.25
base.PAD_HALO = 0.05
base.MAX_EXPANSIONS = 900_000

TURN_PENALTY = 1.50
VIA_COST = 12.0
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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def batch_pr19a(batches: dict) -> dict:
    matches = [b for b in batches["batches"] if b["id"] == "PR19A"]
    if len(matches) != 1:
        base.fail("contrato no contiene exactamente un lote PR19A")
    b = matches[0]
    if int(b["expected_net_count"]) != 28 or len(b["nets"]) != 28:
        base.fail("PR19A no conserva 28 nets")
    if len(set(b["nets"])) != 28:
        base.fail("PR19A contiene nets duplicadas")
    return b


def build_probe(board, placement: dict, routing: dict, batch: dict) -> dict:
    by_ref = {p["ref"]: p for p in placement["placements"]}
    by_class, by_net = base.class_maps(routing)
    wanted = set(batch["nets"])
    endpoints: dict[str, list[dict]] = {n: [] for n in wanted}

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNetname() or ""
            if net not in wanted:
                continue
            pos = pad.GetPosition()
            endpoints[net].append({
                "ref": ref,
                "pad": str(pad.GetNumber()),
                "x_mm": base.mm(pos.x),
                "y_mm": base.mm(pos.y),
            })

    routes = []
    for net in batch["nets"]:
        eps = endpoints[net]
        if len(eps) < 2:
            base.fail(f"{net}: menos de dos endpoints en PCB")
        zones = []
        for ep in eps:
            if ep["ref"] not in by_ref:
                base.fail(f"{net}: ref {ep['ref']} no existe en placement_manifest")
            zones.append(by_ref[ep["ref"]]["zone"])
        uz = sorted(set(zones))
        if len(uz) != 1:
            base.fail(f"{net}: PR19A exige net local a una zona; encontrado {uz}")
        cls = by_net[net]
        mode = "LOCAL_F_QUIET" if cls == "ANALOG_SENSITIVE" else "LOCAL_F"
        routes.append({
            "net": net,
            "class": cls,
            "mode": mode,
            "zones": uz,
            "endpoint_count": len(eps),
        })

    probe = {
        "schema_version": 1,
        "status": "PR19A_LOCAL_ROUTING_PROBE",
        "batch": "PR19A",
        "net_count": len(routes),
        "routes": routes,
    }
    PROBE_OUT.write_text(json.dumps(probe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return probe


class RouterPR19A(base.Router):
    def __init__(self, board, placement, contract, probe, batch):
        self.batch = batch
        super().__init__(board, placement, contract, probe)

    def _escape_endpoint(self, net: str, ep: dict) -> dict:
        if ep.get("ref") != "U_CO2_DRV":
            return ep
        pin = str(ep.get("pad"))
        if (net, pin) not in {("CO2_OPENLOAD_N", "5"), ("CO2_EN_DRV", "4")}:
            return ep
        out = dict(ep)
        out["y_mm"] = float(out["y_mm"]) - ESCAPE_MM
        return out

    def _local_layer_cost(self, cls: str, layer: int) -> float:
        if cls == "DIGITAL_LOW_SPEED":
            return 1.0 if layer == pcbnew.F_Cu else 1.10
        if cls == "ANALOG_SENSITIVE":
            return 1.0 if layer == pcbnew.F_Cu else 1.12
        return 1.0

    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        s_ep = self._escape_endpoint(net, start_ep)
        g_ep = self._escape_endpoint(net, goal_ep)
        layers = base.allowed_layers(cls)
        starts3 = self._pad_states(s_ep, layers)
        goals3 = self._pad_states(g_ep, layers)
        goal_xyz = set(goals3)
        goal_cells = {(g[0], g[1]) for g in goals3}

        # state=(ix,iy,layer,dir), dir: 0/1 X, 2/3 Y, 4 via, -1 start
        openq = []
        dist = {}
        prev = {}

        def heuristic(st):
            ix, iy, layer, _ = st
            best = float("inf")
            for gx, gy, gl in goals3:
                h = abs(ix - gx) + abs(iy - gy) + (10 if layer != gl else 0)
                best = min(best, h)
            return best

        for ix, iy, layer in starts3:
            st = (ix, iy, layer, -1)
            dist[st] = 0.0
            prev[st] = None
            heapq.heappush(openq, (heuristic(st), 0.0, st))

        reached = None
        expansions = 0
        moves = [(1, 0, 0), (-1, 0, 1), (0, 1, 2), (0, -1, 3)]
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

            nbrs = [(ix + dx, iy + dy, layer, ndir) for dx, dy, ndir in moves]
            if len(layers) > 1:
                nbrs += [(ix, iy, other, 4) for other in layers if other != layer]

            for nx, ny, nl, ndir in nbrs:
                is_goal = (nx, ny) in goal_cells
                if not is_goal and self._blocked((nx, ny, nl), net, xmin, xmax):
                    continue

                if nl != layer:
                    owners = (
                        self.pad_occ[pcbnew.F_Cu].get((ix, iy), set())
                        | self.pad_occ[pcbnew.B_Cu].get((ix, iy), set())
                    )
                    if owners:
                        continue
                    step = VIA_COST
                else:
                    step = self._local_layer_cost(cls, nl)
                    if pdir not in (-1, 4) and ndir != pdir:
                        step += TURN_PENALTY

                ng = g + step
                nxt = (nx, ny, nl, ndir)
                if ng + 1e-12 < dist.get(nxt, float("inf")):
                    dist[nxt] = ng
                    prev[nxt] = cur
                    heapq.heappush(openq, (ng + heuristic(nxt), ng, nxt))

        if reached is None:
            base.fail(
                f"sin ruta A* PR19A: {net} {start_ep['ref']}.{start_ep['pad']} -> "
                f"{goal_ep['ref']}.{goal_ep['pad']} expansions={expansions}"
            )

        path4 = []
        cur = reached
        while cur is not None:
            path4.append(cur)
            cur = prev[cur]
        path4.reverse()
        path3 = []
        for ix, iy, layer, _ in path4:
            p = (ix, iy, layer)
            if not path3 or p != path3[-1]:
                path3.append(p)
        return path3

    def route(self) -> dict:
        routes_by_net = {r["net"]: r for r in self.probe["routes"]}
        to_route = list(self.batch["nets"])
        if set(to_route) != set(routes_by_net):
            base.fail("probe y lote PR19A divergen")

        def key(net: str):
            cls = self.by_net[net]
            if cls == "FIELD_ANALOG_LOCAL":
                return (0, 0, net)
            if cls == "CONTROL_SENSITIVE":
                return (1, CONTROL_RANK.get(net, 1000), net)
            if net in EARLY_RANK:
                return (2, EARLY_RANK[net], net)
            if cls == "ANALOG_SENSITIVE":
                return (3, 0, net)
            if cls == "CHILLER_DRY_CONTACT":
                return (4, 0, net)
            if cls == "DIGITAL_LOW_SPEED":
                return (5, DIGITAL_LOCAL_RANK.get(net, 1000), net)
            return (9, 0, net)

        to_route.sort(key=key)
        net_stats = []
        for net in to_route:
            cls = self.by_net[net]
            clsinfo = self.by_class[cls]
            route = routes_by_net[net]
            eps = self.pads_by_net.get(net, [])
            if len(eps) != int(route["endpoint_count"]):
                base.fail(f"{net}: endpoints board/probe divergen")
            eps.sort(key=lambda e: (e["ref"], e["pad"], round(e["x_mm"], 4), round(e["y_mm"], 4)))
            xmin, xmax = base.route_bounds(route, self.placement)
            edges = base.mst_edges(eps)
            before_s, before_v = len(self.segments), len(self.vias)
            for i, j in edges:
                path = self._astar(net, cls, eps[i], eps[j], xmin, xmax)
                self._materialize_path(net, cls, clsinfo, path, eps[i], eps[j])

            segs = self.segments[before_s:]
            length_mm = 0.0
            for s in segs:
                x0, y0 = s["start_mm"]
                x1, y1 = s["end_mm"]
                length_mm += abs(x1 - x0) + abs(y1 - y0)
            stat = {
                "net": net,
                "class": cls,
                "zone": route["zones"][0],
                "edge_count": len(edges),
                "segment_count": len(self.segments) - before_s,
                "via_count": len(self.vias) - before_v,
                "length_mm": round(length_mm, 3),
            }
            net_stats.append(stat)
            print("ROUTED", net, stat)

        all_nets = set(self.by_net)
        deferred = sorted(all_nets - set(to_route))
        return {
            "schema_version": 1,
            "status": "LOCAL_ROUTING_PR19A",
            "batch": "PR19A",
            "merge_policy": "ALL_OR_NOTHING",
            "grid_mm": base.STEP,
            "board_mm": [self.width, self.height],
            "routed_nets": to_route,
            "deferred_nets": deferred,
            "net_stats": net_stats,
            "segments": self.segments,
            "vias": self.vias,
            "policies": {
                "in1_signal_routing": False,
                "turn_penalty": TURN_PENALTY,
                "via_cost": VIA_COST,
                "fine_pitch_escape_mm": ESCAPE_MM,
                "future_batch_copper_allowed": False,
            },
        }


def main() -> int:
    board = pcbnew.LoadBoard(str(PCB))
    if len(list(board.GetTracks())) != 0:
        base.fail("PR19A requiere main PR20 sin tracks/vías previos")
    try:
        if len(list(board.Zones())) != 0:
            base.fail("PR19A requiere board sin copper zones")
    except AttributeError:
        pass

    placement = load_json(PLACEMENT)
    routing = load_json(ROUTING)
    batches = load_json(BATCHES)
    batch = batch_pr19a(batches)
    if placement.get("status") != "PRODUCTION_PLACEMENT_PR17":
        base.fail("placement no es PR17")
    if routing.get("status") != "ROUTING_READINESS_PR18":
        base.fail("routing contract no es PR18")

    probe = build_probe(board, placement, routing, batch)
    router = RouterPR19A(board, placement, routing, probe, batch)
    manifest = router.route()
    if len(manifest["routed_nets"]) != 28:
        base.fail("materializador no cerró 28 nets")

    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pcbnew.SaveBoard(str(PCB), board)
    print(
        "PR19A_DONE",
        "routed_nets", len(manifest["routed_nets"]),
        "segments", len(manifest["segments"]),
        "vias", len(manifest["vias"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
