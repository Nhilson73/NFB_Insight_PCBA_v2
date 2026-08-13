#!/usr/bin/env python3
"""Aplica el ECO PR24 sobre el placement PR17 + ECO PR22.

Solo mueve TP_LOAD_A_POS y TP_LOAD_A_NEG. No cambia rotación, footprint,
netlist, outline, zonas ni política de routing.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "hardware" / "placement_manifest.json"
ECO = ROOT / "hardware" / "z2_loadcell_tp_placement_eco.json"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    eco = json.loads(ECO.read_text(encoding="utf-8"))

    if manifest.get("status") != "PRODUCTION_PLACEMENT_PR17":
        fail("manifest no preserva placement PR17")
    if eco.get("status") != "Z2_LOADCELL_TP_PLACEMENT_ECO_PR24":
        fail("contrato ECO PR24 inválido")
    if manifest.get("eco_revision") != 1:
        fail("PR24 requiere como base el ECO PR22 ya aplicado")
    prior = manifest.get("eco_revisions", [])
    if len(prior) != 1 or prior[0].get("id") != "PR22_Z3_BUCK":
        fail("base no contiene exactamente PR22_Z3_BUCK")

    board = manifest.get("board", {})
    if (
        board.get("origin_mm") != [0.0, 0.0]
        or abs(float(board.get("width_mm", -1)) - 242.34) > 1e-6
        or abs(float(board.get("height_mm", -1)) - 68.58) > 1e-6
        or board.get("growth_only") != "+X"
    ):
        fail(f"board inesperado: {board}")
    if manifest.get("policies", {}).get("routing_allowed") is not False:
        fail("PR24 solo puede aplicarse sobre placement sin routing")

    targets = eco["targets"]
    moved_refs = set(eco["scope"]["moved_refs_only"])
    if set(targets) != moved_refs or moved_refs != {"TP_LOAD_A_POS", "TP_LOAD_A_NEG"}:
        fail("PR24 debe mover exactamente los dos TP load-cell")

    by_ref = {p["ref"]: p for p in manifest["placements"]}
    moved = []
    for ref in sorted(moved_refs):
        if ref not in by_ref:
            fail(f"ref ausente: {ref}")
        p = by_ref[ref]
        if p.get("zone") != "Z2" or p.get("role") != "testpoint":
            fail(f"{ref}: no es testpoint Z2")
        target = targets[ref]
        old_x, old_y = float(p["x_mm"]), float(p["y_mm"])
        old_rot = float(p.get("rotation_deg", 0.0))
        new_x, new_y = float(target["x_mm"]), float(target["y_mm"])
        new_rot = float(target.get("rotation_deg", 0.0))
        if abs(old_rot - new_rot) > 1e-9:
            fail("PR24 no admite rotación; solo traslación")
        if len(p.get("courtyard_global_mm", [])) != 4:
            fail(f"{ref}: falta courtyard_global_mm")
        dx, dy = new_x-old_x, new_y-old_y
        x0, y0, x1, y1 = map(float, p["courtyard_global_mm"])
        p["x_mm"] = round(new_x, 3)
        p["y_mm"] = round(new_y, 3)
        p["courtyard_global_mm"] = [
            round(x0+dx, 3), round(y0+dy, 3),
            round(x1+dx, 3), round(y1+dy, 3),
        ]
        p["placement_eco"] = "PR24_Z2_LOADCELL_TP"
        moved.append({
            "ref": ref,
            "from_mm": [round(old_x,3), round(old_y,3), old_rot],
            "to_mm": [round(new_x,3), round(new_y,3), new_rot],
            "courtyard_global_mm": p["courtyard_global_mm"],
        })

    manifest["eco_revision"] = 2
    manifest["eco_revisions"] = prior + [{
        "id": "PR24_Z2_LOADCELL_TP",
        "contract": "hardware/z2_loadcell_tp_placement_eco.json",
        "moved_refs": sorted(moved_refs),
        "reason": "Short raw load-cell test branches near HX711; preserve coupled quiet J_LOADCELL->U_HX path.",
    }]
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("ECO_PR24_APPLIED", len(moved))
    for x in moved:
        print(x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
