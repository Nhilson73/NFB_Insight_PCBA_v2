#!/usr/bin/env python3
"""Materializa routing de señales/control PR19 sobre el placement congelado PR17.

PR19 enruta únicamente clases de señal/control. GND, rails de potencia y salidas
de actuadores se difieren a PR20 para poder diseñar explícitamente planos,
troncales de corriente y stitching sin contaminar la revisión de señales.

El router es determinista: A* sobre rejilla 0.5 mm, F.Cu/B.Cu, sin In1.Cu.
"""
from __future__ import annotations

import heapq
import json
import math
from pathlib import Path
from typing import Iterable

import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
PLACEMENT = ROOT / "hardware" / "placement_manifest.json"
ROUTING = ROOT / "hardware" / "routing_contract.json"
PROBE = ROOT / "hardware" / "pr19_routing_probe.json"
MANIFEST = ROOT / "hardware" / "pr19_routing_manifest.json"

STEP = 0.5
EDGE = 0.8
PAD_HALO = 0.25
MAX_EXPANSIONS = 350_000

LAYER_IDS = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}
LAYER_NAMES = {v: k for k, v in LAYER_IDS.items()}

ROUTE_CLASSES = {
    "ANALOG_SENSITIVE",
    "FIELD_ANALOG_LOCAL",
    "CONTROL_SENSITIVE",
    "DIGITAL_LOW_SPEED",
    "CHILLER_DRY_CONTACT",
}
DEFER_CLASSES = {
    "GND_REFERENCE",
    "PWR_INPUT_5A",
    "PWR_12V_BRANCH",
    "PWR_5V",
    "PWR_3V3",
    "ACTUATOR_OUTPUT",
}


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def mm(iu: int) -> float:
    return pcbnew.ToMM(iu)


def iu(v: float) -> int:
    return pcbnew.FromMM(float(v))


def gcoord(v: float) -> int:
    return int(round(v / STEP))


def xy(ix: int, iy: int) -> tuple[float, float]:
    return ix * STEP, iy * STEP


def point(ix: int, iy: int) -> "pcbnew.VECTOR2I":
    x, y = xy(ix, iy)
    return pcbnew.VECTOR2I(iu(x), iu(y))


def pad_rect(pad, extra: float) -> tuple[float, float, float, float]:
    bb = pad.GetBoundingBox()
    x0 = mm(bb.GetX()) - extra
    y0 = mm(bb.GetY()) - extra
    return x0, y0, x0 + mm(bb.GetWidth()) + 2 * extra, y0 + mm(bb.GetHeight()) + 2 * extra


def cells_for_rect(rect: tuple[float, float, float, float]) -> Iterable[tuple[int, int]]:
    x0, y0, x1, y1 = rect
    for ix in range(math.floor(x0 / STEP), math.ceil(x1 / STEP) + 1):
        for iy in range(math.floor(y0 / STEP), math.ceil(y1 / STEP) + 1):
            x, y = xy(ix, iy)
            if x0 - 1e-9 <= x <= x1 + 1e-9 and y0 - 1e-9 <= y <= y1 + 1e-9:
                yield ix, iy


def class_maps(contract: dict) -> tuple[dict[str, dict], dict[str, str]]:
    by_name = {c["name"]: c for c in contract["routing_classes"]}
    by_net: dict[str, str] = {}
    for c in contract["routing_classes"]:
        for net in c["nets"]:
            if net in by_net:
                fail(f"net duplicada en routing_contract: {net}")
            by_net[net] = c["name"]
    return by_name, by_net


def allowed_layers(cls: str) -> list[int]:
    if cls in {"FIELD_ANALOG_LOCAL", "CONTROL_SENSITIVE", "CHILLER_DRY_CONTACT"}:
        return [pcbnew.F_Cu]
    if cls == "ANALOG_SENSITIVE":
        return [pcbnew.F_Cu, pcbnew.B_Cu]
    if cls == "DIGITAL_LOW_SPEED":
        return [pcbnew.B_Cu, pcbnew.F_Cu]
    fail(f"clase no enrutable en PR19: {cls}")


def layer_penalty(cls: str, layer: int) -> float:
    if cls == "DIGITAL_LOW_SPEED":
        return 1.0 if layer == pcbnew.B_Cu else 1.18
    if cls == "ANALOG_SENSITIVE":
        return 1.0 if layer == pcbnew.F_Cu else 1.08
    return 1.0


def route_bounds(route: dict, placement: dict) -> tuple[float, float]:
    zb = placement["zone_bounds_mm"]
    if route["mode"].startswith("LOCAL_F"):
        z = route["zones"][0]
        return float(zb[z]["x_min"]), float(zb[z]["x_max"])
    zmins = [float(zb[z]["x_min"]) for z in route["zones"]]
    zmaxs = [float(zb[z]["x_max"]) for z in route["zones"]]
    return min(zmins), max(zmaxs)


def mst_edges(eps: list[dict]) -> list[tuple[int, int]]:
    if len(eps) < 2:
        return []
    used = {0}
    edges: list[tuple[int, int]] = []
    while len(used) < len(eps):
        best = None
        for i in sorted(used):
            a = eps[i]
            for j, b in enumerate(eps):
                if j in used:
                    continue
                d = abs(a["x_mm"] - b["x_mm"]) + abs(a["y_mm"] - b["y_mm"])
                key = (round(d, 6), i, j)
                if best is None or key < best[0]:
                    best = (key, i, j)
        assert best is not None
        _, i, j = best
        used.add(j)
        edges.append((i, j))
    return edges


class Router:
    def __init__(self, board, placement: dict, contract: dict, probe: dict):
        self.board = board
        self.placement = placement
        self.contract = contract
        self.probe = probe
        self.by_class, self.by_net = class_maps(contract)
        self.width = float(placement["board"]["width_mm"])
        self.height = float(placement["board"]["height_mm"])
        self.pad_occ = {pcbnew.F_Cu: {}, pcbnew.B_Cu: {}}
        self.track_occ = {pcbnew.F_Cu: {}, pcbnew.B_Cu: {}}
        self.via_occ: dict[tuple[int, int], set[str]] = {}
        self.pads_by_net: dict[str, list[dict]] = {}
        self.netinfo: dict[str, object] = {}
        self.segments: list[dict] = []
        self.vias: list[dict] = []
        self._index_pads()

    def _own(self, table: dict, key, net: str) -> None:
        table.setdefault(key, set()).add(net)

    def _index_pads(self) -> None:
        for fp in self.board.GetFootprints():
            ref = fp.GetReference()
            for pad in fp.Pads():
                net = pad.GetNetname() or "__NC__"
                if net != "__NC__":
                    pos = pad.GetPosition()
                    ep = {
                        "ref": ref,
                        "pad": str(pad.GetNumber()),
                        "pad_obj": pad,
                        "x_mm": mm(pos.x),
                        "y_mm": mm(pos.y),
                    }
                    self.pads_by_net.setdefault(net, []).append(ep)
                    self.netinfo.setdefault(net, pad.GetNet())
                for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if not pad.IsOnLayer(layer):
                        continue
                    for cell in cells_for_rect(pad_rect(pad, PAD_HALO)):
                        self._own(self.pad_occ[layer], cell, net)

    def _inside(self, ix: int, iy: int, xmin: float, xmax: float) -> bool:
        x, y = xy(ix, iy)
        return (
            max(EDGE, xmin + 0.05) <= x <= min(self.width - EDGE, xmax - 0.05)
            and EDGE <= y <= self.height - EDGE
        )

    def _blocked(self, state: tuple[int, int, int], net: str, xmin: float, xmax: float) -> bool:
        ix, iy, layer = state
        if not self._inside(ix, iy, xmin, xmax):
            return True
        owners = self.pad_occ[layer].get((ix, iy), set())
        if any(owner != net for owner in owners):
            return True
        owners = self.track_occ[layer].get((ix, iy), set())
        if any(owner != net for owner in owners):
            return True
        viaowners = self.via_occ.get((ix, iy), set())
        if any(owner != net for owner in viaowners):
            return True
        return False

    def _pad_states(self, ep: dict, layers: list[int]) -> list[tuple[int, int, int]]:
        ix, iy = gcoord(ep["x_mm"]), gcoord(ep["y_mm"])
        pad = ep["pad_obj"]
        out = [(ix, iy, layer) for layer in layers if pad.IsOnLayer(layer)]
        if not out and pad.IsOnLayer(pcbnew.F_Cu) and pcbnew.F_Cu in layers:
            out = [(ix, iy, pcbnew.F_Cu)]
        if not out:
            fail(f"{ep['ref']}.{ep['pad']}: sin capa compatible para routing")
        return out

    def _heuristic(self, s: tuple[int, int, int], goals: set[tuple[int, int, int]]) -> float:
        ix, iy, layer = s
        best = float("inf")
        for gx, gy, gl in goals:
            h = abs(ix - gx) + abs(iy - gy)
            if layer != gl:
                h += 8
            best = min(best, h)
        return best

    def _astar(self, net: str, cls: str, start_ep: dict, goal_ep: dict, xmin: float, xmax: float) -> list[tuple[int, int, int]]:
        layers = allowed_layers(cls)
        starts = self._pad_states(start_ep, layers)
        goals = set(self._pad_states(goal_ep, layers))
        goal_cells = {(g[0], g[1]) for g in goals}
        openq: list[tuple[float, float, tuple[int, int, int]]] = []
        dist: dict[tuple[int, int, int], float] = {}
        prev: dict[tuple[int, int, int], tuple[int, int, int] | None] = {}
        for s in starts:
            dist[s] = 0.0
            prev[s] = None
            heapq.heappush(openq, (self._heuristic(s, goals), 0.0, s))
        expansions = 0
        reached = None
        while openq:
            _, g, cur = heapq.heappop(openq)
            if g != dist.get(cur):
                continue
            if cur in goals:
                reached = cur
                break
            expansions += 1
            if expansions > MAX_EXPANSIONS:
                break
            ix, iy, layer = cur
            nbrs = [
                (ix + 1, iy, layer), (ix - 1, iy, layer),
                (ix, iy + 1, layer), (ix, iy - 1, layer),
            ]
            if len(layers) > 1:
                for other in layers:
                    if other != layer:
                        nbrs.append((ix, iy, other))
            for nxt in nbrs:
                nx, ny, nl = nxt
                is_goal_cell = (nx, ny) in goal_cells
                if not is_goal_cell and self._blocked(nxt, net, xmin, xmax):
                    continue
                if nl != layer:
                    # No vía dentro de pads ajenos ni encima de un pad SMD propio.
                    owners = self.pad_occ[pcbnew.F_Cu].get((ix, iy), set()) | self.pad_occ[pcbnew.B_Cu].get((ix, iy), set())
                    if owners:
                        continue
                    step_cost = 8.0
                else:
                    step_cost = layer_penalty(cls, nl)
                    x, y = xy(nx, ny)
                    if net == "PUMP_CURRENT_ADC" and 163.34 <= x <= 198.34 and 8.0 <= y <= 58.0:
                        step_cost += 5.0
                ng = g + step_cost
                if ng + 1e-12 < dist.get(nxt, float("inf")):
                    dist[nxt] = ng
                    prev[nxt] = cur
                    heapq.heappush(openq, (ng + self._heuristic(nxt, goals), ng, nxt))
        if reached is None:
            fail(f"sin ruta A*: {net} {start_ep['ref']}.{start_ep['pad']} -> {goal_ep['ref']}.{goal_ep['pad']} expansions={expansions}")
        path = []
        cur = reached
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path

    def _mark_track(self, net: str, layer: int, cells: list[tuple[int, int]], halo: int = 1) -> None:
        for ix, iy in cells:
            for dx in range(-halo, halo + 1):
                for dy in range(-halo, halo + 1):
                    self._own(self.track_occ[layer], (ix + dx, iy + dy), net)

    def _mark_via(self, net: str, ix: int, iy: int, halo: int = 1) -> None:
        for dx in range(-halo, halo + 1):
            for dy in range(-halo, halo + 1):
                self._own(self.via_occ, (ix + dx, iy + dy), net)

    def _add_track(self, net: str, layer: int, width: float, a: tuple[float, float], b: tuple[float, float]) -> None:
        if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
            return
        t = pcbnew.PCB_TRACK(self.board)
        t.SetNet(self.netinfo[net])
        t.SetLayer(layer)
        t.SetWidth(iu(width))
        t.SetStart(pcbnew.VECTOR2I(iu(a[0]), iu(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(iu(b[0]), iu(b[1])))
        self.board.Add(t)
        self.segments.append({
            "net": net, "layer": LAYER_NAMES[layer], "width_mm": width,
            "start_mm": [round(a[0], 4), round(a[1], 4)],
            "end_mm": [round(b[0], 4), round(b[1], 4)],
        })

    def _add_via(self, net: str, clsinfo: dict, ix: int, iy: int) -> None:
        x, y = xy(ix, iy)
        v = pcbnew.PCB_VIA(self.board)
        v.SetNet(self.netinfo[net])
        v.SetPosition(point(ix, iy))
        v.SetWidth(iu(float(clsinfo["via_diameter_mm_min"])))
        v.SetDrill(iu(float(clsinfo["via_drill_mm_min"])))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        self.board.Add(v)
        self.vias.append({
            "net": net, "x_mm": round(x, 4), "y_mm": round(y, 4),
            "diameter_mm": float(clsinfo["via_diameter_mm_min"]),
            "drill_mm": float(clsinfo["via_drill_mm_min"]),
        })
        self._mark_via(net, ix, iy)

    def _materialize_path(self, net: str, cls: str, clsinfo: dict, path: list[tuple[int, int, int]], start_ep: dict, goal_ep: dict) -> None:
        width = float(clsinfo["track_width_mm_min"])
        # Conectar pad exacto al nodo de rejilla inicial/final.
        sx, sy, sl = path[0]
        gx, gy, gl = path[-1]
        self._add_track(net, sl, width, (start_ep["x_mm"], start_ep["y_mm"]), xy(sx, sy))

        run_start = 0
        for i in range(1, len(path) + 1):
            split = i == len(path) or path[i][2] != path[i - 1][2]
            if not split:
                continue
            layer = path[run_start][2]
            pts = [(path[j][0], path[j][1]) for j in range(run_start, i)]
            if len(pts) >= 2:
                # comprimir segmentos colineales
                keep = [pts[0]]
                for k in range(1, len(pts) - 1):
                    a, b, c = keep[-1], pts[k], pts[k + 1]
                    if (b[0] - a[0], b[1] - a[1]) == (c[0] - b[0], c[1] - b[1]):
                        continue
                    keep.append(b)
                keep.append(pts[-1])
                for a, b in zip(keep, keep[1:]):
                    self._add_track(net, layer, width, xy(*a), xy(*b))
                self._mark_track(net, layer, pts)
            if i < len(path):
                ix, iy, _ = path[i - 1]
                self._add_via(net, clsinfo, ix, iy)
                run_start = i

        self._add_track(net, gl, width, xy(gx, gy), (goal_ep["x_mm"], goal_ep["y_mm"]))

    def route(self) -> dict:
        routes_by_net = {r["net"]: r for r in self.probe["routes"]}
        to_route = []
        deferred = []
        for net, cls in sorted(self.by_net.items()):
            if cls in ROUTE_CLASSES:
                to_route.append(net)
            elif cls in DEFER_CLASSES:
                deferred.append(net)
            else:
                fail(f"clase sin política PR19: {cls}")

        # Orden de riesgo: local analógico/control, analógico largo, digital local/largo.
        priority = {
            "FIELD_ANALOG_LOCAL": 0,
            "CONTROL_SENSITIVE": 1,
            "ANALOG_SENSITIVE": 2,
            "CHILLER_DRY_CONTACT": 3,
            "DIGITAL_LOW_SPEED": 4,
        }
        to_route.sort(key=lambda n: (priority[self.by_net[n]], 0 if routes_by_net[n]["mode"].startswith("LOCAL") else 1, n))

        net_stats = []
        for net in to_route:
            cls = self.by_net[net]
            clsinfo = self.by_class[cls]
            route = routes_by_net[net]
            eps = self.pads_by_net.get(net, [])
            if len(eps) != int(route["endpoint_count"]):
                fail(f"{net}: endpoints board/probe divergen {len(eps)} != {route['endpoint_count']}")
            # Orden determinista idéntico al probe: ref/pad/posición.
            eps.sort(key=lambda e: (e["ref"], e["pad"], round(e["x_mm"], 4), round(e["y_mm"], 4)))
            xmin, xmax = route_bounds(route, self.placement)
            edges = mst_edges(eps)
            before_s, before_v = len(self.segments), len(self.vias)
            for i, j in edges:
                path = self._astar(net, cls, eps[i], eps[j], xmin, xmax)
                self._materialize_path(net, cls, clsinfo, path, eps[i], eps[j])
            net_stats.append({
                "net": net,
                "class": cls,
                "mode": route["mode"],
                "edge_count": len(edges),
                "segment_count": len(self.segments) - before_s,
                "via_count": len(self.vias) - before_v,
            })
            print("ROUTED", net, cls, route["mode"], "edges", len(edges), "segments", len(self.segments)-before_s, "vias", len(self.vias)-before_v)

        return {
            "schema_version": 1,
            "status": "SIGNAL_ROUTING_PR19",
            "scope": "SIGNALS_CONTROL_ONLY_POWER_GND_DEFERRED_PR20",
            "grid_mm": STEP,
            "board_mm": [self.width, self.height],
            "routed_classes": sorted(ROUTE_CLASSES),
            "deferred_classes": sorted(DEFER_CLASSES),
            "routed_nets": to_route,
            "deferred_nets": deferred,
            "net_stats": net_stats,
            "segments": self.segments,
            "vias": self.vias,
        }


def main() -> int:
    board = pcbnew.LoadBoard(str(PCB))
    if len(list(board.GetTracks())) != 0:
        fail("materializador PR19 requiere board PR17/PR18 sin tracks/vías")
    try:
        if len(list(board.Zones())) != 0:
            fail("materializador PR19 no parte de board con copper zones")
    except AttributeError:
        pass

    placement = json.loads(PLACEMENT.read_text(encoding="utf-8"))
    contract = json.loads(ROUTING.read_text(encoding="utf-8"))
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    if placement.get("status") != "PRODUCTION_PLACEMENT_PR17":
        fail("placement no es PR17")
    if contract.get("status") != "ROUTING_READINESS_PR18":
        fail("routing contract no es PR18")
    if probe.get("status") != "PR19_ROUTING_PROBE":
        fail("probe PR19 ausente/no válido")

    router = Router(board, placement, contract, probe)
    manifest = router.route()
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    pcbnew.SaveBoard(str(PCB), board)
    print("PR19_DONE", "routed_nets", len(manifest["routed_nets"]), "deferred_nets", len(manifest["deferred_nets"]), "segments", len(manifest["segments"]), "vias", len(manifest["vias"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
