#!/usr/bin/env python3
"""Valida que PR22 sea un ECO local de exactamente cinco refs Z3."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ECO = ROOT / "hardware" / "z3_buck_placement_eco.json"
MANIFEST = ROOT / "hardware" / "placement_manifest.json"
TOL = 1e-3


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def near(a: float, b: float) -> bool:
    return abs(float(a) - float(b)) <= TOL


def main() -> int:
    if len(sys.argv) != 2:
        fail("uso: validate_z3_buck_placement_eco.py <base_manifest.json>")
    base_path = Path(sys.argv[1])
    if not base_path.exists():
        fail(f"falta base manifest {base_path}")
    base = json.loads(base_path.read_text(encoding="utf-8"))
    now = json.loads(MANIFEST.read_text(encoding="utf-8"))
    eco = json.loads(ECO.read_text(encoding="utf-8"))

    if base.get("status") != "PRODUCTION_PLACEMENT_PR17" or now.get("status") != "PRODUCTION_PLACEMENT_PR17":
        fail("status PR17 no preservado")
    if base["board"] != now["board"] or base["zone_bounds_mm"] != now["zone_bounds_mm"]:
        fail("ECO alteró board o zonas")
    if now.get("eco_revision") != 1:
        fail("eco_revision != 1")

    b = {p["ref"]: p for p in base["placements"]}
    n = {p["ref"]: p for p in now["placements"]}
    if set(b) != set(n):
        fail("refs cambiaron")
    moved = set(eco["scope"]["moved_refs_only"])
    if len(moved) != 5:
        fail("ECO debe mover exactamente cinco refs")

    changed = set()
    for ref in sorted(b):
        old, new = b[ref], n[ref]
        xyrot_old = (float(old["x_mm"]), float(old["y_mm"]), float(old.get("rotation_deg", 0.0)))
        xyrot_new = (float(new["x_mm"]), float(new["y_mm"]), float(new.get("rotation_deg", 0.0)))
        if not all(near(x, y) for x, y in zip(xyrot_old, xyrot_new)):
            changed.add(ref)
        for key in ("zone", "block", "role", "footprint"):
            if old.get(key) != new.get(key):
                fail(f"{ref}: ECO cambió {key}")

    if changed != moved:
        fail(f"refs XY cambiadas != contrato: changed={sorted(changed)} expected={sorted(moved)}")

    for ref, target in eco["targets"].items():
        p = n[ref]
        if not (near(p["x_mm"], target["x_mm"]) and near(p["y_mm"], target["y_mm"]) and near(p.get("rotation_deg",0), target.get("rotation_deg",0))):
            fail(f"{ref}: target ECO no coincide")
        if p.get("placement_eco") != "PR22_Z3_BUCK":
            fail(f"{ref}: falta marca placement_eco")

    print("OK: ECO Z3/TPSM33625 localizado")
    print("MOVED_REFS", " ".join(sorted(changed)))
    print("UNCHANGED_REFS", len(n) - len(changed))
    print("BOARD", now["board"], "Z3", now["zone_bounds_mm"]["Z3"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
