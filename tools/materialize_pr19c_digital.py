#!/usr/bin/env python3
"""Materializa únicamente PR19C sobre el checkpoint acumulado PR19A+PR19B.

Router determinista A* sobre rejilla de 0.5 mm. Indexa pads y cobre existente,
prefiere B.Cu para DIGITAL_LOW_SPEED, nunca usa In1.Cu y no toca PR20A/PR20B.
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
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
OUT = ROOT / "hardware" / "pr19c_digital_routing_manifest.json"

TARGET = [
    "ACT_FAULT_N", "CHILLER_CTL", "CO2_SOL_CTL",
    "HMI_RX", "HMI_TX", "HX711_DOUT", "HX711_SCK",
    "I2C_SCL", "I2C_SDA", "LED_STATUS", "MCU_NRST", "MCU_WDI",
    "PUMP_DIR", "PUMP_PWM", "TEMP_1WIRE", "UNO_IOREF_3V3",
]
PRIOR_SEGMENTS = 555
PRIOR_VIAS = 31
STEP = 0.5
EDGE = 0.8
PAD_HALO = 0.25
MAX_EXPANSIONS = 650_000
LAYERS = (pcbnew.B_Cu, pcbnew.F_Cu)
LAYER_NAMES = {pcbnew.F_Cu: "F.Cu", pcbnew.B_Cu: "B.Cu"}


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def mm(iu: int) -> float:
    return float(pcbnew.ToMM(iu))


def iu(v: float) -> int:
    return pcbnew.FromMM(float(v))


def gcoord(v: float) -> int:
    return int(round(v / STEP))


def xy(ix: int, iy: int) -> tuple[float, float]:
    return ix * STEP, iy * STEP


def point(ix: int, iy: int):
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


def mst_edges(eps: list[dict]) -> list[tuple[int, int]]:
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
        if best is None:
            fail("MST incompleto")
        _, i, j = best
        used.add(j)
        edges.append((i, j))
    return edges


class Router:
    def __init__(self, board, placement: dict, routing: dict, batches: dict):
        self.board = board
        self.placement = placement
        self.routing = routing
        self.batches = {b["id"]: b for b in batches["batches"]}
        self.width = float(placement["board"]["width_mm"])
        self.height = float(placement["board"]["height_mm"])
        self.class_by_net = {}
        self.class_info = {}
        for c in routing["routing_classes"]:
            self.class_info[c["name"]] = c
            for n in c["nets"]:
                self.class_by_net[n] = c["name"]
        self.pad_occ = {pcbnew.F_Cu: {}, pcbnew.B_Cu: {}}
        self.track_occ = {pcbnew.F_Cu: {}, pcbnew.B_Cu: {}}
        self.via_occ: dict[tuple[int, int], set[str]] = {}
        self.pads_by_net: dict[str, list[dict]] = {}
        self.netinfo = {}
        self.new_segments: list[dict] = []
        self.new_vias: list[dict] = []
        self.net_stats: list[dict] = []
        self._index_pads()
        self._index_existing_copper()

    def _own(self, table: dict, key, net: str) -> None:
        table.setdefault(key, set()).add(net)

    def _index_pads(self) -> None:
        seen = set()
        for fp in self.board.GetFootprints():
            ref = fp.GetReference()
            for pad in fp.Pads():
                net = pad.GetNetname() or "__NC__"
                if net != "__NC__":
                    key = (net, ref, str(pad.GetNumber()))
                    if key not in seen:
                        seen.add(key)
                        pos = pad.GetPosition()
                        self.pads_by_net.setdefault(net, []).append({
                            "ref": ref, "pad": str(pad.GetNumber()), "pad_obj": pad,
                            "x_mm": mm(pos.x), "y_mm": mm(pos.y),
                        })
                    self.netinfo.setdefault(net, pad.GetNet())
                for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if pad.IsOnLayer(layer):
                        for cell in cells_for_rect(pad_rect(pad, PAD_HALO)):
                            self._own(self.pad_occ[layer], cell, net)

    def _mark_track_cells(self, table: dict, net: str, layer: int, a: tuple[float,float], b: tuple[float,float], halo: int = 1) -> None:
        dist = math.hypot(b[0]-a[0], b[1]-a[1])
        steps = max(1, int(math.ceil(dist / (STEP / 3.0))))
        for k in range(steps + 1):
            t = k / steps
            ix = gcoord(a[0] + (b[0]-a[0]) * t)
            iy = gcoord(a[1] + (b[1]-a[1]) * t)
            for dx in range(-halo, halo + 1):
                for dy in range(-halo, halo + 1):
                    self._own(table[layer], (ix+dx, iy+dy), net)

    def _mark_via(self, net: str, x: float, y: float, halo: int = 1) -> None:
        ix, iy = gcoord(x), gcoord(y)
        for dx in range(-halo, halo + 1):
            for dy in range(-halo, halo + 1):
                self._own(self.via_occ, (ix+dx, iy+dy), net)

    def _index_existing_copper(self) -> None:
        seg = via = 0
        routed = set()
        for item in self.board.GetTracks():
            net = item.GetNetname() or "__NC__"
            routed.add(net)
            if isinstance(item, pcbnew.PCB_VIA):
                via += 1
                p = item.GetPosition()
                self._mark_via(net, mm(p.x), mm(p.y), halo=1)
            else:
                seg += 1
                layer = item.GetLayer()
                if layer in self.track_occ:
                    a, z = item.GetStart(), item.GetEnd()
                    self._mark_track_cells(self.track_occ, net, layer, (mm(a.x),mm(a.y)), (mm(z.x),mm(z.y)), halo=1)
        if (seg, via) != (PRIOR_SEGMENTS, PRIOR_VIAS):
            fail(f"baseline PR19B inesperado: segments/vias={(seg,via)}")
        prior = set(self.batches["PR19A"]["nets"]) | set(self.batches["PR19B"]["nets"])
        actual = {n for n in routed if n != "__NC__"}
        if actual != prior:
            fail(f"cobre previo fuera de PR19A+PR19B: faltan={sorted(prior-actual)} sobran={sorted(actual-prior)}")
        if any(x.GetNetname() in TARGET for x in self.board.GetTracks()):
            fail("PR19C debe iniciar sin cobre propio")

    def _inside(self, ix: int, iy: int) -> bool:
        x, y = xy(ix, iy)
        return EDGE <= x <= self.width - EDGE and EDGE <= y <= self.height - EDGE

    def _blocked(self, ix: int, iy: int, layer: int, net: str) -> bool:
        if not self._inside(ix, iy):
            return True
        if any(o != net for o in self.pad_occ[layer].get((ix,iy), set())):
            return True
        if any(o != net for o in self.track_occ[layer].get((ix,iy), set())):
            return True
        if any(o != net for o in self.via_occ.get((ix,iy), set())):
            return True
        return False

    def _allowed_layers(self, net: str) -> tuple[int,...]:
        cls = self.class_by_net[net]
        if cls == "DIGITAL_LOW_SPEED":
            return (pcbnew.B_Cu, pcbnew.F_Cu)
        if net == "UNO_IOREF_3V3" and cls == "CONTROL_SENSITIVE":
            return (pcbnew.F_Cu, pcbnew.B_Cu)
        fail(f"PR19C contiene clase inesperada: {net}={cls}")

    def _layer_cost(self, net: str, layer: int, x: float, y: float) -> float:
        if net == "UNO_IOREF_3V3":
            base = 1.0 if layer == pcbnew.F_Cu else 1.10
        else:
            base = 1.0 if layer == pcbnew.B_Cu else 1.28
        # Preservar F.Cu de Z1 para front-end analógico salvo nets que terminan allí.
        if layer == pcbnew.F_Cu and 53.34 <= x <= 108.84 and y <= 28.0 and net not in {"I2C_SDA","I2C_SCL","TEMP_1WIRE"}:
            base += 1.8
        # Alejar clock/data de HX711 de la banda inferior de analógica Z1.
        if net in {"HX711_SCK","HX711_DOUT"} and 53.34 <= x <= 108.84 and y <= 30.0:
            base += 2.0
        return base

    def _pad_states(self, ep: dict, layers: tuple[int,...]) -> list[tuple[int,int,int,int]]:
        ix, iy = gcoord(ep["x_mm"]), gcoord(ep["y_mm"])
        pad = ep["pad_obj"]
        out = [(ix,iy,l,0) for l in layers if pad.IsOnLayer(l)]
        if not out:
            fail(f"{ep['ref']}.{ep['pad']}: sin capa compatible")
        return out

    def _heuristic(self, s, goals) -> float:
        ix, iy, layer, _ = s
        return min(abs(ix-gx)+abs(iy-gy)+(8 if layer != gl else 0) for gx,gy,gl,_ in goals)

    def _astar(self, net: str, a: dict, z: dict) -> list[tuple[int,int,int,int]]:
        layers = self._allowed_layers(net)
        starts = self._pad_states(a, layers)
        goals = set(self._pad_states(z, layers))
        goal_cells = {(g[0],g[1]) for g in goals}
        q=[]; dist={}; prev={}
        for s in starts:
            dist[s]=0.0; prev[s]=None
            heapq.heappush(q,(self._heuristic(s,goals),0.0,s))
        reached=None; expansions=0
        # direction: 0 inicio/layer switch, 1 +x, 2 -x, 3 +y, 4 -y
        moves=((1,0,1),(-1,0,2),(0,1,3),(0,-1,4))
        while q:
            _,g,cur=heapq.heappop(q)
            if abs(g-dist.get(cur,float('inf'))) > 1e-12:
                continue
            ix,iy,layer,pdir=cur
            if any(ix==gx and iy==gy and layer==gl for gx,gy,gl,_ in goals):
                reached=cur; break
            expansions += 1
            if expansions > MAX_EXPANSIONS:
                break
            for dx,dy,ndir in moves:
                nx,ny=ix+dx,iy+dy
                if (nx,ny) not in goal_cells and self._blocked(nx,ny,layer,net):
                    continue
                x,y=xy(nx,ny)
                step=self._layer_cost(net,layer,x,y)
                if pdir and pdir != ndir:
                    step += 0.22
                nxt=(nx,ny,layer,ndir)
                ng=g+step
                if ng+1e-12 < dist.get(nxt,float('inf')):
                    dist[nxt]=ng; prev[nxt]=cur
                    heapq.heappush(q,(ng+self._heuristic(nxt,goals),ng,nxt))
            # Cambio de capa solo fuera de pads y cobre ajeno.
            for other in layers:
                if other == layer:
                    continue
                owners = self.pad_occ[pcbnew.F_Cu].get((ix,iy),set()) | self.pad_occ[pcbnew.B_Cu].get((ix,iy),set())
                if owners:
                    continue
                if self._blocked(ix,iy,other,net):
                    continue
                nxt=(ix,iy,other,0); ng=g+9.0
                if ng+1e-12 < dist.get(nxt,float('inf')):
                    dist[nxt]=ng; prev[nxt]=cur
                    heapq.heappush(q,(ng+self._heuristic(nxt,goals),ng,nxt))
        if reached is None:
            fail(f"sin ruta A*: {net} {a['ref']}.{a['pad']}->{z['ref']}.{z['pad']} expansions={expansions}")
        path=[]; cur=reached
        while cur is not None:
            path.append(cur); cur=prev[cur]
        path.reverse()
        return path

    def _add_track(self, net: str, layer: int, width: float, a, z) -> None:
        if abs(a[0]-z[0])<1e-9 and abs(a[1]-z[1])<1e-9: return
        t=pcbnew.PCB_TRACK(self.board); t.SetNet(self.netinfo[net]); t.SetLayer(layer); t.SetWidth(iu(width))
        t.SetStart(pcbnew.VECTOR2I(iu(a[0]),iu(a[1]))); t.SetEnd(pcbnew.VECTOR2I(iu(z[0]),iu(z[1]))); self.board.Add(t)
        self.new_segments.append({"net":net,"layer":LAYER_NAMES[layer],"width_mm":width,
                                  "start_mm":[round(a[0],4),round(a[1],4)],"end_mm":[round(z[0],4),round(z[1],4)]})

    def _add_via(self, net: str, clsinfo: dict, ix: int, iy: int) -> None:
        x,y=xy(ix,iy); v=pcbnew.PCB_VIA(self.board); v.SetNet(self.netinfo[net]); v.SetPosition(point(ix,iy))
        v.SetWidth(iu(float(clsinfo["via_diameter_mm_min"]))); v.SetDrill(iu(float(clsinfo["via_drill_mm_min"])))
        v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); self.board.Add(v)
        self.new_vias.append({"net":net,"x_mm":round(x,4),"y_mm":round(y,4),
                              "diameter_mm":float(clsinfo["via_diameter_mm_min"]),"drill_mm":float(clsinfo["via_drill_mm_min"])})
        self._mark_via(net,x,y,halo=1)

    def _materialize(self, net: str, path, a: dict, z: dict) -> tuple[int,int,int,float]:
        clsinfo=self.class_info[self.class_by_net[net]]; width=float(clsinfo["track_width_mm_min"])
        before_s=len(self.new_segments); before_v=len(self.new_vias)
        sx,sy,sl,_=path[0]; gx,gy,gl,_=path[-1]
        self._add_track(net,sl,width,(a["x_mm"],a["y_mm"]),xy(sx,sy))
        run=0; bends=0; total=0.0
        for i in range(1,len(path)+1):
            split=i==len(path) or path[i][2] != path[i-1][2]
            if not split: continue
            layer=path[run][2]; pts=[(path[j][0],path[j][1]) for j in range(run,i)]
            if len(pts)>=2:
                keep=[pts[0]]
                for k in range(1,len(pts)-1):
                    aa,bb,cc=keep[-1],pts[k],pts[k+1]
                    if (bb[0]-aa[0],bb[1]-aa[1]) == (cc[0]-bb[0],cc[1]-bb[1]): continue
                    keep.append(bb)
                keep.append(pts[-1]); bends += max(0,len(keep)-2)
                for aa,bb in zip(keep,keep[1:]):
                    pa,pb=xy(*aa),xy(*bb); self._add_track(net,layer,width,pa,pb)
                    total += math.hypot(pb[0]-pa[0],pb[1]-pa[1])
                self._mark_track_cells(self.track_occ,net,layer,xy(*pts[0]),xy(*pts[-1]),halo=1)
                # Marcar cada tramo de rejilla para obstáculos futuros.
                for aa,bb in zip(pts,pts[1:]):
                    self._mark_track_cells(self.track_occ,net,layer,xy(*aa),xy(*bb),halo=1)
            if i < len(path):
                ix,iy,_,_=path[i-1]; self._add_via(net,clsinfo,ix,iy); run=i
        self._add_track(net,gl,width,xy(gx,gy),(z["x_mm"],z["y_mm"]))
        return len(self.new_segments)-before_s, len(self.new_vias)-before_v, bends, total

    def route_all(self) -> dict:
        batch=self.batches["PR19C"]
        if batch["nets"] != TARGET or int(batch["expected_net_count"]) != 16:
            fail("contrato PR19C divergente")
        order=[
            "UNO_IOREF_3V3", "I2C_SDA", "I2C_SCL", "TEMP_1WIRE",
            "HX711_DOUT", "HX711_SCK", "MCU_NRST", "MCU_WDI",
            "HMI_RX", "HMI_TX", "ACT_FAULT_N", "PUMP_PWM", "PUMP_DIR",
            "CO2_SOL_CTL", "CHILLER_CTL", "LED_STATUS",
        ]
        for net in order:
            eps=self.pads_by_net.get(net,[])
            eps.sort(key=lambda e:(e["x_mm"],e["y_mm"],e["ref"],e["pad"]))
            if len(eps)<2: fail(f"{net}: endpoints insuficientes")
            edges=mst_edges(eps); bs=len(self.new_segments); bv=len(self.new_vias); bends=0; length=0.0
            for i,j in edges:
                path=self._astar(net,eps[i],eps[j])
                _,_,b,l=self._materialize(net,path,eps[i],eps[j]); bends+=b; length+=l
            stat={"net":net,"class":self.class_by_net[net],"endpoint_count":len(eps),"edge_count":len(edges),
                  "segment_count":len(self.new_segments)-bs,"via_count":len(self.new_vias)-bv,
                  "bend_count":bends,"grid_length_mm":round(length,3)}
            self.net_stats.append(stat)
            print("ROUTED",stat)
        return {
            "schema_version":1,
            "status":"PR19C_DIGITAL_ROUTING_CANDIDATE",
            "batch":"PR19C",
            "target_nets":TARGET,
            "baseline":{"segments":PRIOR_SEGMENTS,"vias":PRIOR_VIAS},
            "net_stats":self.net_stats,
            "new_segments":self.new_segments,
            "new_vias":self.new_vias,
            "new_segment_count":len(self.new_segments),
            "new_via_count":len(self.new_vias),
            "policies":{"in1_signal_tracks":0,"zones_added":0,"future_batch_copper":0},
        }


def main() -> int:
    board=pcbnew.LoadBoard(str(PCB))
    try:
        if len(list(board.Zones())) != 0: fail("PR19C no parte de board con copper zones")
    except AttributeError:
        pass
    placement=json.loads(PLACEMENT.read_text(encoding="utf-8"))
    routing=json.loads(ROUTING.read_text(encoding="utf-8"))
    batches=json.loads(BATCHES.read_text(encoding="utf-8"))
    if placement.get("status") != "PRODUCTION_PLACEMENT_PR17": fail("placement no es PR17")
    if routing.get("status") != "ROUTING_READINESS_PR18": fail("routing contract no es PR18")
    r=Router(board,placement,routing,batches)
    manifest=r.route_all()
    OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    pcbnew.SaveBoard(str(PCB),board)
    print("PR19C_CANDIDATE",len(manifest["target_nets"]),manifest["new_segment_count"],manifest["new_via_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
