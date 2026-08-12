#!/usr/bin/env python3
"""Valida placement PR17 contra manifest, JSON y guardrails PR16.

No evalúa routing porque PR17 lo prohíbe: exige explícitamente tracks/vías/zones=0.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
MANIFEST = ROOT / "hardware" / "placement_manifest.json"
READINESS = ROOT / "hardware" / "placement_readiness_contract.json"
PIN = ROOT / "hardware" / "insight_pin_contract.json"
ZONE_FILES = [
    ROOT / "hardware" / "z1_production_netlist.json",
    ROOT / "hardware" / "z2_production_netlist.json",
    ROOT / "hardware" / "power_production_netlist.json",
    ROOT / "hardware" / "z4_production_netlist.json",
]
FIELD_CONNECTORS = {
    "J_PH", "J_ORP", "J_TEMP", "J_DO", "J_LOADCELL", "J_GNSS_RTC", "J_HMI",
    "J_PWR_IN", "J_PUMP", "J_CO2_SOL", "J_CHILLER_CTL",
}
TOL = 1e-3


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def mm(iu: int) -> float:
    return float(iu) / 1_000_000.0


def near(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) <= tol


def fpid_text(fp) -> str:
    """Serializa LIB_ID sin depender del overload SWIG de Format() en KiCad 10."""
    fid = fp.GetFPID()
    lib = str(fid.GetLibNickname())
    item = str(fid.GetLibItemName())
    return f"{lib}:{item}" if lib else item


def component_map() -> dict[str, dict]:
    out = {}
    for path in ZONE_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for comp in data["components"]:
            ref = comp["ref"]
            if ref in out:
                fail(f"ref duplicada entre netlists: {ref}")
            out[ref] = comp
    return out


def edge_bbox(text: str) -> tuple[float, float, float, float]:
    boxes = []
    pattern = re.compile(
        r'\(gr_line\s+\(start\s+([-0-9.]+)\s+([-0-9.]+)\)\s+'
        r'\(end\s+([-0-9.]+)\s+([-0-9.]+)\).*?\(layer\s+"Edge\.Cuts"\)',
        re.S,
    )
    for a, b, c, d in pattern.findall(text):
        boxes.append((float(a), float(b), float(c), float(d)))
    if len(boxes) != 4:
        fail(f"se esperaban 4 líneas Edge.Cuts rectangulares; encontradas={len(boxes)}")
    xs = [v for line in boxes for v in (line[0], line[2])]
    ys = [v for line in boxes for v in (line[1], line[3])]
    return min(xs), min(ys), max(xs), max(ys)


def overlaps(a, b, eps=1e-6) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > eps and min(a[3], b[3]) - max(a[1], b[1]) > eps


def main() -> int:
    for p in (PCB, MANIFEST, READINESS, PIN, *ZONE_FILES):
        if not p.exists():
            fail(f"falta {p.relative_to(ROOT)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS.read_text(encoding="utf-8"))
    pins = json.loads(PIN.read_text(encoding="utf-8"))
    comps = component_map()

    if manifest.get("status") != "PRODUCTION_PLACEMENT_PR17":
        fail("placement manifest no está cerrado como PR17")
    if manifest["policies"].get("routing_allowed") is not False:
        fail("PR17 no puede habilitar routing")
    if readiness.get("status") != "PREPLACEMENT_READINESS_PR16":
        fail("PR16 readiness cambió")

    placements = {p["ref"]: p for p in manifest["placements"]}
    if set(placements) != set(comps):
        fail("refs del manifest no coinciden con los 4 netlists de producción")
    if len(placements) != 119:
        fail(f"se esperan 119 refs de producción; actual={len(placements)}")

    board = pcbnew.LoadBoard(str(PCB))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    expected_refs = {"J_UNOQ"} | set(comps)
    if set(fps) != expected_refs:
        fail(f"refs PCB difieren; falta={sorted(expected_refs-set(fps))[:10]} sobra={sorted(set(fps)-expected_refs)[:10]}")
    if len(fps) != 120:
        fail(f"PCB debe tener 120 footprints incluido J_UNOQ; actual={len(fps)}")

    text = PCB.read_text(encoding="utf-8")
    x0, y0, x1, y1 = edge_bbox(text)
    target_w = float(manifest["board"]["width_mm"])
    if not (near(x0, 0.0) and near(y0, 0.0) and near(x1, target_w) and near(y1, 68.58)):
        fail(f"Edge.Cuts != manifest: {(x0,y0,x1,y1)} target=(0,0,{target_w},68.58)")

    host = fps["J_UNOQ"]
    hp = host.GetPosition()
    if not (near(mm(hp.x), 0.0) and near(mm(hp.y), 0.0) and near(host.GetOrientationDegrees(), 0.0)):
        fail("J_UNOQ se movió/rotó; Z0 es inmutable")

    zone_bounds = manifest["zone_bounds_mm"]
    for ref, comp in comps.items():
        fp = fps[ref]
        p = placements[ref]
        pos = fp.GetPosition()
        actual = (mm(pos.x), mm(pos.y), fp.GetOrientationDegrees())
        expected = (float(p["x_mm"]), float(p["y_mm"]), float(p["rotation_deg"]))
        if not all(near(a, e) for a, e in zip(actual, expected)):
            fail(f"{ref}: XY/rot difiere actual={actual} expected={expected}")
        actual_fpid = fpid_text(fp)
        if actual_fpid != comp["footprint"]:
            fail(f"{ref}: footprint PCB={actual_fpid} JSON={comp['footprint']}")

        zl = float(zone_bounds[p["zone"]]["x_min"])
        zr = float(zone_bounds[p["zone"]]["x_max"])
        c = p["courtyard_global_mm"]
        if c[0] < zl - TOL or c[2] > zr + TOL or c[1] < -TOL or c[3] > 68.58 + TOL:
            fail(f"{ref}: courtyard fuera de zone/board")
        if c[0] < 53.34 - TOL:
            fail(f"{ref}: producción invade Z0")

        pinmap = {str(k): v for k, v in comp["pins"].items()}
        for pad in fp.Pads():
            num = str(pad.GetNumber())
            if not num:
                continue
            if num not in pinmap:
                fail(f"{ref}: pad físico {num} no está en JSON")
            wanted = pinmap[num]
            got = pad.GetNetname()
            if wanted == "NC" or not wanted:
                if got:
                    fail(f"{ref}.{num}: debía quedar NC pero tiene net {got}")
            elif got != wanted:
                fail(f"{ref}.{num}: net PCB={got!r}, JSON={wanted!r}")

    hostmap = {str(p["pad"]): p.get("net") for p in pins["pins"]}
    for pad in host.Pads():
        num = str(pad.GetNumber())
        wanted = hostmap.get(num)
        got = pad.GetNetname()
        if wanted:
            if got != wanted:
                fail(f"J_UNOQ.{num}: net PCB={got!r} expected={wanted!r}")
        elif got:
            fail(f"J_UNOQ.{num}: debía quedar sin net, tiene {got}")

    frozen = [x["ref"] for x in readiness["field_io_sequence_left_to_right"]]
    if manifest["field_io_sequence_left_to_right"] != frozen:
        fail("secuencia FIELD I/O cambió respecto PR16")
    last_x = -1e9
    for ref in frozen:
        p = placements[ref]
        c = p["courtyard_global_mm"]
        cx = (float(c[0]) + float(c[2])) / 2.0
        if cx <= last_x:
            fail(f"orden FIELD I/O no crece en +X en {ref}")
        last_x = cx
        if not near(float(c[1]), float(manifest["policies"]["field_courtyard_bottom_margin_mm"]), 0.01):
            fail(f"{ref}: no está en la fila inferior congelada")
        if ref in FIELD_CONNECTORS and not near(float(p["rotation_deg"]), 0.0):
            fail(f"{ref}: side-entry debe mantener orientación 0° hacia -Y")

    items = sorted(placements.items())
    collisions = []
    for i, (ra, pa) in enumerate(items):
        for rb, pb in items[i + 1 :]:
            if overlaps(pa["courtyard_global_mm"], pb["courtyard_global_mm"]):
                collisions.append((ra, rb))
                if len(collisions) >= 10:
                    break
        if len(collisions) >= 10:
            break
    if collisions:
        fail(f"courtyard overlaps PR17: {collisions}")

    if len(list(board.GetTracks())) != 0:
        fail("PR17 contiene tracks/vías: routing sigue prohibido")
    if re.search(r'^\s*\(zone\b', text, re.M):
        fail("PR17 contiene copper zones; routing/copper sigue prohibido")

    print("OK: placement PR17 verificado")
    print(f"- board {target_w:.2f} x 68.58 mm; crecimiento solo +X")
    print("- 119 refs producción + J_UNOQ; XY/rot/footprints/nets = manifest+JSON")
    print("- FIELD I/O ordenado en Y=0/-Y; Z0 sin producción")
    print("- courtyard overlaps=0; tracks/vías/zones=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
