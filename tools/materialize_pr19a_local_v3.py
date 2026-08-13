#!/usr/bin/env python3
"""PR19A v3: planner físico por clase con escape local de pitch fino.

Principio:
- KiCad DRC sigue siendo autoridad final.
- No se aumenta un halo global que cierre gargantas de ICs finos.
- Cada net evalúa pads ajenos con margen = ancho/2 + clearance de su clase.
- Los pads de ICs densos salen primero con un stub corto hacia el exterior del
  encapsulado; después se aplica la exclusión física completa.
"""
from __future__ import annotations

import math

import pcbnew  # type: ignore
import materialize_pr19a_local as impl
import pr19a_router_core as base

base.PAD_HALO = 0.05
impl.TURN_PENALTY = 2.50
impl.VIA_COST = 14.0

# El lazo FB es eléctricamente más crítico y geométricamente más confinado que
# VCC/PGOOD. Sale primero; las otras nets se acomodan después alrededor de él.
CONTROL_ORDER_V3 = [
    "5V_FB", "5V_VCC", "5V_PGOOD",
    "EFUSE_ILM", "EFUSE_ITIMER", "EFUSE_DVDT", "EFUSE_EN_UVLO", "EFUSE_OVLO",
    "CO2_ILIM", "PUMP_SR_CFG",
]
impl.CONTROL_RANK = {n: i for i, n in enumerate(CONTROL_ORDER_V3)}

FINE_PITCH_REFS = {"U_5V", "U_EFUSE", "U_CO2_DRV", "U_HX"}
MIN_ESCAPE_MM = 0.85

# RDN0011A: pads 9/10/11 están en el borde inferior del módulo. La salida
# perpendicular -Y evita pasar entre pads adyacentes antes de aplicar el
# clearance normal de CONTROL_SENSITIVE.
U5V_BOTTOM_ESCAPE_MM = 1.60
U5V_BOTTOM_PADS = {"9", "10", "11"}


class RouterPR19APhysical(impl.RouterPR19A):
    def __init__(self, board, placement, contract, probe, batch):
        super().__init__(board, placement, contract, probe, batch)
        self._placement_by_ref = {p["ref"]: p for p in placement["placements"]}
        self._foreign_pads = {pcbnew.F_Cu: [], pcbnew.B_Cu: []}
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            for pad in fp.Pads():
                net = pad.GetNetname() or "__NC__"
                bb = pad.GetBoundingBox()
                rect = (
                    base.mm(bb.GetX()),
                    base.mm(bb.GetY()),
                    base.mm(bb.GetX() + bb.GetWidth()),
                    base.mm(bb.GetY() + bb.GetHeight()),
                )
                for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
                    if pad.IsOnLayer(layer):
                        self._foreign_pads[layer].append((net, ref, str(pad.GetNumber()), rect))

    def _class_margin(self, net: str) -> float:
        cls = self.by_net[net]
        ci = self.by_class[cls]
        return float(ci["track_width_mm_min"]) / 2.0 + float(ci["clearance_mm_min"])

    @staticmethod
    def _inside_expanded(x: float, y: float, rect, margin: float) -> bool:
        x0, y0, x1, y1 = rect
        return x0 - margin <= x <= x1 + margin and y0 - margin <= y <= y1 + margin

    def _blocked(self, state, net: str, xmin: float, xmax: float) -> bool:
        ix, iy, layer = state
        if not self._inside(ix, iy, xmin, xmax):
            return True
        x, y = base.xy(ix, iy)
        margin = self._class_margin(net)

        for owner, _ref, _pad, rect in self._foreign_pads[layer]:
            if owner != net and self._inside_expanded(x, y, rect, margin):
                return True

        owners = self.track_occ[layer].get((ix, iy), set())
        if any(owner != net for owner in owners):
            return True
        viaowners = self.via_occ.get((ix, iy), set())
        if any(owner != net for owner in viaowners):
            return True
        return False

    def _escape_endpoint(self, net: str, ep: dict) -> dict:
        ref = ep.get("ref")
        pin = str(ep.get("pad"))

        if ref == "U_5V" and pin in U5V_BOTTOM_PADS:
            out = dict(ep)
            out["y_mm"] = float(out["y_mm"]) - U5V_BOTTOM_ESCAPE_MM
            return out

        if ref == "U_CO2_DRV" and (net, pin) in {
            ("CO2_OPENLOAD_N", "5"), ("CO2_EN_DRV", "4")
        }:
            out = dict(ep)
            out["y_mm"] = float(out["y_mm"]) - 0.90
            return out

        if ref not in FINE_PITCH_REFS or ref not in self._placement_by_ref:
            return ep

        fp = self._placement_by_ref[ref]
        cx, cy = float(fp["x_mm"]), float(fp["y_mm"])
        px, py = float(ep["x_mm"]), float(ep["y_mm"])
        dx, dy = px - cx, py - cy
        distance = max(MIN_ESCAPE_MM, self._class_margin(net) + 0.55)
        out = dict(ep)
        if abs(dx) >= abs(dy) and abs(dx) > 1e-6:
            out["x_mm"] = px + math.copysign(distance, dx)
        elif abs(dy) > 1e-6:
            out["y_mm"] = py + math.copysign(distance, dy)
        else:
            return ep
        return out

    def _mark_track(self, net, layer, cells, halo=2):
        return super()._mark_track(net, layer, cells, halo=2)

    def _mark_via(self, net, ix, iy, halo=3):
        return super()._mark_via(net, ix, iy, halo=3)


impl.RouterPR19A = RouterPR19APhysical

if __name__ == "__main__":
    raise SystemExit(impl.main())
