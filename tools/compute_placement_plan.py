#!/usr/bin/env python3
"""Calcula el envelope mínimo de placement PR17 con geometría real de KiCad 10.0.5.

Usa F.CrtYd de cada footprint cuando existe y cae a bounding-box de pads para
features sin courtyard (test points / net-ties). No modifica el PCB.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
STD = Path("/usr/share/kicad/footprints")
LOCAL = ROOT / "kicad" / "lib" / "nfb_footprints.pretty"
READINESS = json.loads((ROOT / "hardware" / "placement_readiness_contract.json").read_text(encoding="utf-8"))
ZONE_FILES = {
    "Z1": ROOT / "hardware" / "z1_production_netlist.json",
    "Z2": ROOT / "hardware" / "z2_production_netlist.json",
    "Z3": ROOT / "hardware" / "power_production_netlist.json",
    "Z4": ROOT / "hardware" / "z4_production_netlist.json",
}
FIELD = [item["ref"] for item in READINESS["field_io_sequence_left_to_right"]]

FIELD_GAP = 1.0
ZONE_MARGIN = 1.0
INTERNAL_GAP = 0.8
INTERNAL_Y_START = 18.0
INTERNAL_Y_MAX = 67.0
NM_PER_MM = 1_000_000.0


def mm(iu: int) -> float:
    return float(iu) / NM_PER_MM


def load_fp(fid: str):
    lib, name = fid.split(":", 1)
    libdir = LOCAL if lib == "NFB" else STD / f"{lib}.pretty"
    fp = pcbnew.FootprintLoad(str(libdir), name)
    if fp is None:
        raise FileNotFoundError(f"{fid} en {libdir}")
    return fp


def rect_tuple(bb) -> tuple[float, float, float, float]:
    x0 = mm(bb.GetX())
    y0 = mm(bb.GetY())
    return (x0, y0, x0 + mm(bb.GetWidth()), y0 + mm(bb.GetHeight()))


def bbox_union(boxes: list[tuple[float, float, float, float]]) -> tuple[float, float, float, float]:
    if not boxes:
        raise ValueError("sin geometría")
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def footprint_bbox(fp) -> tuple[tuple[float, float, float, float], str]:
    courtyard = []
    for item in fp.GraphicalItems():
        try:
            if item.GetLayer() == pcbnew.F_CrtYd:
                courtyard.append(rect_tuple(item.GetBoundingBox()))
        except Exception:
            continue
    if courtyard:
        return bbox_union(courtyard), "F.CrtYd"

    pads = [rect_tuple(pad.GetBoundingBox()) for pad in fp.Pads()]
    if pads:
        return bbox_union(pads), "PAD_FALLBACK"
    raise ValueError(f"footprint {fp.GetFPID().Format()} sin courtyard ni pads")


def shelf_height(items: list[dict], width_mm: float) -> float:
    usable = width_mm - 2 * ZONE_MARGIN
    x = 0.0
    row_h = 0.0
    total = 0.0
    for item in items:
        w = item["w_mm"] + INTERNAL_GAP
        h = item["h_mm"] + INTERNAL_GAP
        if w > usable + 1e-9:
            return float("inf")
        if x > 0 and x + w > usable:
            total += row_h
            x = 0.0
            row_h = 0.0
        x += w
        row_h = max(row_h, h)
    return total + row_h


def main() -> int:
    zones = {z: json.loads(path.read_text(encoding="utf-8")) for z, path in ZONE_FILES.items()}
    refinfo: dict[str, dict] = {}

    for zone, data in zones.items():
        for comp in data["components"]:
            fp = load_fp(comp["footprint"])
            b, source = footprint_bbox(fp)
            refinfo[comp["ref"]] = {
                "zone": zone,
                "footprint": comp["footprint"],
                "bbox_mm": [round(v, 4) for v in b],
                "bbox_source": source,
                "w_mm": round(b[2] - b[0], 4),
                "h_mm": round(b[3] - b[1], 4),
            }

    result = {
        "schema_version": 2,
        "source": "KiCad 10.0.5 pcbnew F.CrtYd with pad fallback",
        "field_gap_mm": FIELD_GAP,
        "zone_margin_mm": ZONE_MARGIN,
        "internal_gap_mm": INTERNAL_GAP,
        "zones": {},
        "field_sequence": [],
    }

    for ref in FIELD:
        if ref not in refinfo:
            raise SystemExit(f"FIELD ref ausente de netlists: {ref}")
        result["field_sequence"].append({"ref": ref, **refinfo[ref]})

    current = READINESS["zone_guides"]
    total = 53.34
    for zone in ("Z1", "Z2", "Z3", "Z4"):
        fieldrefs = [ref for ref in FIELD if refinfo[ref]["zone"] == zone]
        field_required = (
            2 * ZONE_MARGIN
            + sum(refinfo[ref]["w_mm"] for ref in fieldrefs)
            + FIELD_GAP * max(0, len(fieldrefs) - 1)
        )

        order = [c["ref"] for c in zones[zone]["components"] if c["ref"] not in FIELD]
        internal = [{"ref": ref, **refinfo[ref]} for ref in order]
        current_width = float(current[zone]["x_max"]) - float(current[zone]["x_min"])
        width = max(current_width, math.ceil(field_required * 2) / 2)

        while shelf_height(internal, width) > INTERNAL_Y_MAX - INTERNAL_Y_START and width < 120.0:
            width += 0.5
        internal_height = shelf_height(internal, width)
        if internal_height > INTERNAL_Y_MAX - INTERNAL_Y_START:
            raise SystemExit(f"{zone}: componentes internos no caben incluso con 120 mm")

        result["zones"][zone] = {
            "current_width_mm": round(current_width, 2),
            "field_required_width_mm": round(field_required, 2),
            "planned_width_mm": round(width, 2),
            "internal_shelf_height_mm": round(internal_height, 2),
            "field_refs": fieldrefs,
            "internal_ref_count": len(internal),
            "pad_fallback_refs": [x["ref"] for x in internal if x["bbox_source"] == "PAD_FALLBACK"],
        }
        total += width

    result["planned_board_width_mm"] = round(total, 2)
    result["current_board_width_mm"] = 220.0
    result["board_height_mm"] = 68.58
    result["growth_only"] = "+X"

    out = ROOT / "hardware" / "placement_plan_probe.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
