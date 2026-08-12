#!/usr/bin/env python3
"""Genera el manifest XY de PR17 desde BOM, contratos y courtyards KiCad 10.0.5.

El manifest congela placement, no routing. La fila de campo sigue exactamente
`placement_readiness_contract.json`; el resto se agrupa por bloque funcional.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
STD = Path("/usr/share/kicad/footprints")
LOCAL = ROOT / "kicad" / "lib" / "nfb_footprints.pretty"
READINESS = json.loads((ROOT / "hardware" / "placement_readiness_contract.json").read_text(encoding="utf-8"))

ZONE_SOURCES = {
    "Z1": (ROOT / "hardware" / "z1_production_netlist.json", ROOT / "bom" / "insight_z1_production_bom.csv"),
    "Z2": (ROOT / "hardware" / "z2_production_netlist.json", ROOT / "bom" / "insight_z2_production_bom.csv"),
    "Z3": (ROOT / "hardware" / "power_production_netlist.json", ROOT / "bom" / "insight_power_production_bom.csv"),
    "Z4": (ROOT / "hardware" / "z4_production_netlist.json", ROOT / "bom" / "insight_z4_production_bom.csv"),
}

FIELD_BLOCK_ANCHOR = {
    "Z1": {"PH": "J_PH", "ORP": "J_ORP", "TEMP": "J_TEMP", "CO2": "U_CO2", "DO": "J_DO"},
    "Z2": {"HX711": "J_LOADCELL", "I2C_GNSS_RTC": "J_GNSS_RTC", "HMI": "J_HMI"},
    "Z4": {"PUMP": "J_PUMP", "CO2_SOL": "J_CO2_SOL", "CHILLER": "J_CHILLER_CTL"},
}

ORDER_OVERRIDES = {
    ("Z2", "HX711"): ["U_HX", "C_HX_100N", "C_HX_10U", "C_HX_VBG"],
    ("Z2", "I2C_GNSS_RTC"): ["D_GNSS_SDA", "D_GNSS_SCL", "R_I2C_SDA", "R_I2C_SCL"],
    ("Z2", "HMI"): ["D_HMI_RX", "D_HMI_TX", "U_HMI_LVL", "C_HMI_A", "C_HMI_B"],
    ("Z2", "WATCHDOG"): ["U_WDT", "R_WDT_MR", "C_WDT"],
    ("Z3", "ENTRADA_PROTECCION"): [
        "D_IN_TVS", "C_IN_HF", "U_EFUSE", "R_UVOV_R1", "R_UVOV_R2", "R_UVOV_R3",
        "R_EFUSE_ILIM", "C_EFUSE_DVDT", "C_EFUSE_ITIMER", "C_IN_BULK",
    ],
    ("Z3", "SPLIT_ESTRELLA"): ["NT_HOST", "NT_LOGIC", "F_ACT"],
    ("Z3", "BUCK_5V"): [
        "C_5V_IN_4U7", "C_5V_IN_100N", "U_5V", "C_5V_VCC", "R_5V_FBT", "R_5V_FBB",
        "C_5V_OUT1", "C_5V_OUT2", "C_5V_HF", "R_5V_EN_PD", "R_5V_PG_PU",
    ],
    ("Z3", "LDO_3V3"): ["C_3V3_IN", "U_3V3", "C_3V3_OUT", "C_3V3_HF"],
    ("Z4", "PUMP"): [
        "C_PUMP_BULK", "C_PUMP_VM", "U_PUMP_DRV", "R_PUMP_SR", "R_PUMP_PWM_SER",
        "R_PUMP_PWM_PD", "R_PUMP_DIR_SER", "R_PUMP_DIR_PD", "R_PUMP_IPROPI", "C_PUMP_IPROPI",
    ],
    ("Z4", "CO2_SOL"): [
        "C_CO2_DRV", "U_CO2_DRV", "R_CO2_ILIM", "R_CO2_EN_SER", "R_CO2_EN_PD", "R_CO2_OPENLOAD_PU",
    ],
    ("Z4", "CHILLER"): ["U_CHILLER", "Q_CHILLER", "R_CH_LED", "R_CH_GATE", "R_CH_GATE_PD"],
}

BOTTOM_MARGIN = 0.80
ZONE_MARGIN = 1.00
FIELD_GAP = 1.00
INTERNAL_GAP = 0.80
INTERNAL_Y0 = 16.50
ANCHOR_Y1 = 49.00
UNANCHORED_Y0 = 49.50
TESTPOINT_Y0 = 56.00
TOP_Y1 = 67.30
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
    return x0, y0, x0 + mm(bb.GetWidth()), y0 + mm(bb.GetHeight())


def union(boxes):
    return (
        min(b[0] for b in boxes), min(b[1] for b in boxes),
        max(b[2] for b in boxes), max(b[3] for b in boxes),
    )


def footprint_bbox(fp):
    c = []
    for item in fp.GraphicalItems():
        try:
            if item.GetLayer() == pcbnew.F_CrtYd:
                c.append(rect_tuple(item.GetBoundingBox()))
        except Exception:
            pass
    if c:
        return union(c), "F.CrtYd"
    pads = [rect_tuple(p.GetBoundingBox()) for p in fp.Pads()]
    if pads:
        return union(pads), "PAD_FALLBACK"
    raise ValueError(f"sin bbox para {fp.GetFPID().Format()}")


def load_zone(zone: str):
    net_path, bom_path = ZONE_SOURCES[zone]
    net = json.loads(net_path.read_text(encoding="utf-8"))
    with bom_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    byref = {c["ref"]: c for c in net["components"]}
    bomref = {r["ref"]: r for r in rows}
    if set(byref) != set(bomref):
        raise SystemExit(f"{zone}: refs JSON/BOM divergen")
    return net, rows, byref, bomref


def ordered_members(zone: str, block: str, refs: list[str]) -> list[str]:
    override = ORDER_OVERRIDES.get((zone, block), [])
    out = [r for r in override if r in refs]
    out.extend(r for r in refs if r not in out)
    return out


def place_from_min(ref: str, geom: dict, x_min: float, y_min: float, zone: str, block: str, role: str, placements: dict):
    b = geom[ref]["bbox"]
    x = x_min - b[0]
    y = y_min - b[1]
    placements[ref] = {
        "ref": ref, "zone": zone, "block": block, "role": role,
        "x_mm": round(x, 3), "y_mm": round(y, 3), "rotation_deg": 0.0,
        "courtyard_global_mm": [round(x + b[0], 3), round(y + b[1], 3), round(x + b[2], 3), round(y + b[3], 3)],
    }


def pack_rect(zone: str, block: str, refs: list[str], rect: tuple[float, float, float, float], geom: dict, placements: dict, role="internal"):
    if not refs:
        return
    x0, y0, x1, y1 = rect
    x = x0
    y = y0
    row_h = 0.0
    for ref in refs:
        if ref in placements:
            continue
        b = geom[ref]["bbox"]
        w = b[2] - b[0]
        h = b[3] - b[1]
        if x > x0 and x + w > x1 + 1e-9:
            y += row_h + INTERNAL_GAP
            x = x0
            row_h = 0.0
        if x + w > x1 + 1e-9 or y + h > y1 + 1e-9:
            raise SystemExit(f"{zone}/{block}: {ref} no cabe en rect {rect}; cursor=({x:.2f},{y:.2f}) wh=({w:.2f},{h:.2f})")
        place_from_min(ref, geom, x, y, zone, block, role, placements)
        x += w + INTERNAL_GAP
        row_h = max(row_h, h)


def main() -> int:
    field_order = [item["ref"] for item in READINESS["field_io_sequence_left_to_right"]]
    zones = {}
    all_comps = {}
    bommeta = {}
    geom = {}

    for zone in ("Z1", "Z2", "Z3", "Z4"):
        net, rows, byref, bomref = load_zone(zone)
        zones[zone] = {"net": net, "rows": rows, "byref": byref, "bomref": bomref}
        for ref, comp in byref.items():
            all_comps[ref] = comp
            bommeta[ref] = bomref[ref]
            b, source = footprint_bbox(load_fp(comp["footprint"]))
            geom[ref] = {"bbox": b, "source": source, "footprint": comp["footprint"]}

    # Derivar anchos mínimos por fila de campo; Z3 conserva su ancho PR16 si es mayor.
    current = READINESS["zone_guides"]
    widths = {}
    for zone in ("Z1", "Z2", "Z3", "Z4"):
        refs = [r for r in field_order if r in all_comps and bommeta[r].get("ref") and next(z for z in zones if r in zones[z]["byref"]) == zone]
        req = 2 * ZONE_MARGIN + sum(geom[r]["bbox"][2] - geom[r]["bbox"][0] for r in refs) + FIELD_GAP * max(0, len(refs) - 1)
        cur = float(current[zone]["x_max"]) - float(current[zone]["x_min"])
        widths[zone] = max(cur, math.ceil(req * 2.0) / 2.0)

    bounds = {"Z0": [0.0, 53.34]}
    cursor = 53.34
    for zone in ("Z1", "Z2", "Z3", "Z4"):
        bounds[zone] = [round(cursor, 2), round(cursor + widths[zone], 2)]
        cursor += widths[zone]
    board_width = round(cursor, 2)

    placements = {}
    field_global = {}
    # Fila de campo: cada zone arranca con margen propio; orden global ya está congelado por PR16.
    for zone in ("Z1", "Z2", "Z3", "Z4"):
        x = bounds[zone][0] + ZONE_MARGIN
        refs = [r for r in field_order if r in zones[zone]["byref"]]
        for ref in refs:
            block = bommeta[ref][next(iter(bommeta[ref].keys()))]
            b = geom[ref]["bbox"]
            place_from_min(ref, geom, x, BOTTOM_MARGIN, zone, block, "field_io", placements)
            field_global[ref] = placements[ref]["courtyard_global_mm"]
            x += (b[2] - b[0]) + FIELD_GAP
        if refs and x - FIELD_GAP > bounds[zone][1] - ZONE_MARGIN + 1e-6:
            raise SystemExit(f"{zone}: fila de campo excede zone bound")

    # Bloques anclados a conectores: celdas delimitadas por puntos medios de los conectores.
    for zone, anchors in FIELD_BLOCK_ANCHOR.items():
        anchor_items = []
        for block, ref in anchors.items():
            g = field_global[ref]
            anchor_items.append((block, ref, (g[0] + g[2]) / 2.0))
        anchor_items.sort(key=lambda x: x[2])
        centers = [x[2] for x in anchor_items]
        for i, (block, anchor_ref, center) in enumerate(anchor_items):
            left = bounds[zone][0] + ZONE_MARGIN if i == 0 else (centers[i - 1] + center) / 2.0 + 0.2
            right = bounds[zone][1] - ZONE_MARGIN if i == len(anchor_items) - 1 else (center + centers[i + 1]) / 2.0 - 0.2
            rows = zones[zone]["rows"]
            key0 = next(iter(rows[0].keys()))
            members = [r["ref"] for r in rows if r[key0] == block and r["ref"] != anchor_ref and r.get("funcion") != "testpoint"]
            members = ordered_members(zone, block, members)
            pack_rect(zone, block, members, (left, INTERNAL_Y0, right, ANCHOR_Y1), geom, placements)

    # Bloques no anclados Z2/Z4.
    for zone, blocks in {"Z2": ["WATCHDOG"], "Z4": ["DIAGNOSTIC"]}.items():
        rows = zones[zone]["rows"]
        key0 = next(iter(rows[0].keys()))
        refs = []
        for block in blocks:
            br = [r["ref"] for r in rows if r[key0] == block and r.get("funcion") != "testpoint"]
            refs.extend(ordered_members(zone, block, br))
        pack_rect(zone, "+".join(blocks), refs, (bounds[zone][0] + ZONE_MARGIN, UNANCHORED_Y0, bounds[zone][1] - ZONE_MARGIN, TESTPOINT_Y0 - 0.5), geom, placements)

    # Z3: separar explícitamente entrada/protección de buck/LDO; estrella arriba entre ambos.
    z3l, z3r = bounds["Z3"]
    rows = zones["Z3"]["rows"]
    key0 = next(iter(rows[0].keys()))
    byblock = {}
    for r in rows:
        byblock.setdefault(r[key0], []).append(r)
    entry = [r["ref"] for r in byblock["ENTRADA_PROTECCION"] if r["ref"] != "J_PWR_IN" and r.get("funcion") != "testpoint"]
    right_refs = [r["ref"] for b in ("BUCK_5V", "LDO_3V3") for r in byblock[b] if r.get("funcion") != "testpoint"]
    split = [r["ref"] for r in byblock["SPLIT_ESTRELLA"] if r.get("funcion") != "testpoint"]
    pack_rect("Z3", "ENTRADA_PROTECCION", ordered_members("Z3", "ENTRADA_PROTECCION", entry), (z3l + 1.0, INTERNAL_Y0, z3l + 17.0, 51.5), geom, placements)
    ordered_right = ordered_members("Z3", "BUCK_5V", [r for r in right_refs if r in [x["ref"] for x in byblock["BUCK_5V"]]]) + ordered_members("Z3", "LDO_3V3", [r for r in right_refs if r in [x["ref"] for x in byblock["LDO_3V3"]]])
    pack_rect("Z3", "BUCK_5V+LDO_3V3", ordered_right, (z3l + 18.0, INTERNAL_Y0, z3r - 1.0, 51.5), geom, placements)
    pack_rect("Z3", "SPLIT_ESTRELLA", ordered_members("Z3", "SPLIT_ESTRELLA", split), (z3l + 1.0, 52.0, z3r - 1.0, TESTPOINT_Y0 - 0.3), geom, placements)

    # Test points siempre accesibles en la banda superior de su zona.
    for zone in ("Z2", "Z3", "Z4"):
        rows = zones[zone]["rows"]
        tps = [r["ref"] for r in rows if r.get("funcion") == "testpoint"]
        pack_rect(zone, "TESTPOINTS", tps, (bounds[zone][0] + ZONE_MARGIN, TESTPOINT_Y0, bounds[zone][1] - ZONE_MARGIN, TOP_Y1), geom, placements, role="testpoint")

    missing = sorted(set(all_comps) - set(placements))
    if missing:
        raise SystemExit(f"refs sin placement: {missing}")

    # Guardrails geométricos básicos del manifest antes de tocar PCB.
    for ref, p in placements.items():
        x0, y0, x1, y1 = p["courtyard_global_mm"]
        zl, zr = bounds[p["zone"]]
        if x0 < zl - 1e-6 or x1 > zr + 1e-6:
            raise SystemExit(f"{ref}: courtyard sale de {p['zone']}: {p['courtyard_global_mm']} vs {bounds[p['zone']]}")
        if y0 < -1e-6 or y1 > 68.58 + 1e-6:
            raise SystemExit(f"{ref}: courtyard sale de altura board")

    manifest = {
        "schema_version": 1,
        "status": "PRODUCTION_PLACEMENT_PR17",
        "product": "NFB Insight PCBA v2",
        "source": "PR16 placement readiness + production JSON/BOM + KiCad 10.0.5 F.CrtYd",
        "board": {"origin_mm": [0.0, 0.0], "width_mm": board_width, "height_mm": 68.58, "growth_only": "+X"},
        "zone_bounds_mm": {z: {"x_min": b[0], "x_max": b[1]} for z, b in bounds.items()},
        "field_io_sequence_left_to_right": field_order,
        "policies": {
            "routing_allowed": False,
            "all_field_connectors_face": "-Y",
            "field_courtyard_bottom_margin_mm": BOTTOM_MARGIN,
            "z0_production_placement_allowed": False,
            "in1_cu_signal_routing_allowed": False,
            "manual_xy_override_allowed": False,
        },
        "placements": [placements[r] | {"footprint": geom[r]["footprint"], "bbox_source": geom[r]["source"]} for r in sorted(placements)],
    }
    out = ROOT / "hardware" / "placement_manifest.json"
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if "--check" in __import__("sys").argv:
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            raise SystemExit("ERROR: placement_manifest.json no reproduce byte-for-byte")
        print("OK: placement_manifest.json reproducible")
        return 0
    out.write_text(text, encoding="utf-8")
    print(f"WROTE {out.relative_to(ROOT)} refs={len(placements)} board={board_width}x68.58")
    for z in ("Z0", "Z1", "Z2", "Z3", "Z4"):
        print(z, bounds[z])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
