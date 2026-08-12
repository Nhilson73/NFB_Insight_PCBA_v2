#!/usr/bin/env python3
"""Valida el DRC de placement PR17 sin confundir ausencia de routing con fallos físicos."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "hardware" / "placement_manifest.json"
EXPECTED_UNCONNECTED = 250


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def main() -> int:
    if len(sys.argv) != 2:
        fail("uso: validate_pr17_drc.py <reporte-drc.json>")
    report_path = Path(sys.argv[1])
    if not report_path.exists(): fail(f"no existe reporte DRC: {report_path}")
    if not MANIFEST.exists(): fail("falta hardware/placement_manifest.json")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "PRODUCTION_PLACEMENT_PR17": fail("manifest no está cerrado como PRODUCTION_PLACEMENT_PR17")
    if manifest.get("policies", {}).get("routing_allowed") is not False: fail("PR17 no puede habilitar routing")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    violations = report.get("violations"); unconnected = report.get("unconnected_items")
    if not isinstance(violations, list): fail("reporte KiCad JSON no contiene lista 'violations'")
    if not isinstance(unconnected, list): fail("reporte KiCad JSON no contiene lista 'unconnected_items'")

    counts = Counter(str(item.get("type", "?")) for item in violations)
    sev = Counter(str(item.get("severity", "?")) for item in violations)
    examples = defaultdict(list)
    for item in violations:
        t=str(item.get("type","?"))
        if len(examples[t]) < 2:
            examples[t].append(str(item.get("description","sin descripción")))
    print("DRC_TYPE_COUNTS", dict(sorted(counts.items())))
    print("DRC_SEVERITY_COUNTS", dict(sorted(sev.items())))
    for t in sorted(examples):
        print("DRC_EXAMPLES", t, " | ".join(examples[t]))

    if violations:
        fail(f"DRC PR17 tiene {len(violations)} violaciones inesperadas; tipos={dict(sorted(counts.items()))}")

    if len(unconnected) != EXPECTED_UNCONNECTED:
        fail(f"deuda unconnected PR17 cambió: actual={len(unconnected)}, esperado={EXPECTED_UNCONNECTED}")

    print("OK: DRC PR17 limpio de violaciones físicas/documentales")
    print("- violations=0")
    print(f"- unconnected_items={len(unconnected)} (deuda intencional placement-only; routing=0)")
    return 0


if __name__ == "__main__": raise SystemExit(main())
