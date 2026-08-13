#!/usr/bin/env python3
"""Aplica de forma determinista el ECO local Z3/TPSM33625 al manifest PR17.

El generador PR17 sigue produciendo el placement base. Este paso aplica únicamente
los cinco movimientos aprobados por `hardware/z3_buck_placement_eco.json`, sin
cambiar board, zonas, netlist, footprint o política de routing.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "hardware" / "placement_manifest.json"
ECO = ROOT / "hardware" / "z3_buck_placement_eco.json"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def rotated_courtyard(old_box, old_x: float, old_y: float, old_rot: float, new_x: float, new_y: float, new_rot: float):
    """Transforma el bbox global antiguo a un bbox global nuevo para rotaciones ortogonales.

    El placement PR17 base usa rotación conocida; recuperamos los cuatro vértices
    en el marco local antiguo y aplicamos únicamente el delta de rotación ECO.
    """
    x0, y0, x1, y1 = map(float, old_box)
    corners = [(x0-old_x, y0-old_y), (x0-old_x, y1-old_y), (x1-old_x, y0-old_y), (x1-old_x, y1-old_y)]
    delta = (new_rot - old_rot) % 360.0
    if min(abs(delta-k) for k in (0,90,180,270,360)) > 1e-6:
        fail(f"rotación ECO no ortogonal: {old_rot} -> {new_rot}")
    rad = math.radians(delta)
    c, s = round(math.cos(rad)), round(math.sin(rad))
    pts = [(new_x + c*x - s*y, new_y + s*x + c*y) for x,y in corners]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [round(min(xs),3), round(min(ys),3), round(max(xs),3), round(max(ys),3)]


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    eco = json.loads(ECO.read_text(encoding="utf-8"))

    if manifest.get("status") != "PRODUCTION_PLACEMENT_PR17":
        fail("manifest base no es PR17")
    if eco.get("status") != "Z3_BUCK_PLACEMENT_ECO_PR22":
        fail("contrato ECO inválido")
    board = manifest.get("board", {})
    if (
        board.get("origin_mm") != [0.0, 0.0]
        or abs(float(board.get("width_mm", -1)) - 242.34) > 1e-6
        or abs(float(board.get("height_mm", -1)) - 68.58) > 1e-6
        or board.get("growth_only") != "+X"
    ):
        fail(f"board inesperado: {board}")
    if manifest["policies"].get("routing_allowed") is not False:
        fail("ECO solo puede aplicarse sobre placement sin routing")

    by_ref = {p["ref"]: p for p in manifest["placements"]}
    targets = eco["targets"]
    if set(targets) != set(eco["scope"]["moved_refs_only"]):
        fail("targets ECO != moved_refs_only")
    if len(targets) != int(eco["acceptance"]["moved_ref_count"]):
        fail("conteo de refs ECO diverge")

    moved = []
    for ref, target in targets.items():
        if ref not in by_ref:
            fail(f"ref ECO ausente en manifest: {ref}")
        p = by_ref[ref]
        if p.get("zone") != "Z3":
            fail(f"{ref}: ECO fuera de Z3")
        old_x = float(p["x_mm"])
        old_y = float(p["y_mm"])
        old_rot = float(p.get("rotation_deg", 0.0))
        new_x = float(target["x_mm"])
        new_y = float(target["y_mm"])
        new_rot = float(target.get("rotation_deg", 0.0))
        if "courtyard_global_mm" not in p or len(p["courtyard_global_mm"]) != 4:
            fail(f"{ref}: falta courtyard_global_mm")
        p["courtyard_global_mm"] = rotated_courtyard(
            p["courtyard_global_mm"], old_x, old_y, old_rot, new_x, new_y, new_rot
        )
        p["x_mm"] = round(new_x, 3)
        p["y_mm"] = round(new_y, 3)
        p["rotation_deg"] = new_rot
        p["placement_eco"] = "PR22_Z3_BUCK"
        moved.append({
            "ref": ref,
            "from_mm": [round(old_x, 3), round(old_y, 3), old_rot],
            "to_mm": [round(new_x, 3), round(new_y, 3), new_rot],
            "role": target["role"],
            "courtyard_global_mm": p["courtyard_global_mm"],
        })

    manifest["eco_revision"] = 1
    manifest["eco_revisions"] = [{
        "id": "PR22_Z3_BUCK",
        "contract": "hardware/z3_buck_placement_eco.json",
        "moved_refs": sorted(targets),
        "reason": "TI TPSM33625 layout-critical VCC/FB/VIN proximity",
    }]

    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("ECO_APPLIED", len(moved))
    for item in moved:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
