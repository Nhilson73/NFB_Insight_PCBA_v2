#!/usr/bin/env python3
"""Valida DRC PR17 bajo deuda acotada y machine-readable.

PR17 es placement-only. Exige cero errores y cero tipos de violación fuera del
contrato. Las advertencias de serigrafía/rotulación y los unconnected se aceptan
solo con conteos exactos, bloqueando cualquier crecimiento silencioso de deuda.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "hardware" / "placement_manifest.json"
CONTRACT = ROOT / "hardware" / "placement_drc_contract.json"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def main() -> int:
    if len(sys.argv) != 2:
        fail("uso: validate_pr17_drc.py <reporte-drc.json>")
    report_path = Path(sys.argv[1])
    for path in (report_path, MANIFEST, CONTRACT):
        if not path.exists():
            fail(f"no existe {path}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if manifest.get("status") != "PRODUCTION_PLACEMENT_PR17":
        fail("manifest no está cerrado como PRODUCTION_PLACEMENT_PR17")
    if manifest.get("policies", {}).get("routing_allowed") is not False:
        fail("PR17 no puede habilitar routing")
    if contract.get("schema_version") != 1 or contract.get("status") != "BOUNDED_PLACEMENT_DRC_DEBT_PR17":
        fail("contrato DRC no está cerrado como PR17")
    if contract.get("scope") != "PLACEMENT_ONLY_NO_ROUTING":
        fail("scope DRC PR17 inesperado")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    violations = report.get("violations")
    unconnected = report.get("unconnected_items")
    if not isinstance(violations, list):
        fail("reporte KiCad JSON no contiene lista 'violations'")
    if not isinstance(unconnected, list):
        fail("reporte KiCad JSON no contiene lista 'unconnected_items'")

    severity_counts = Counter(str(item.get("severity", "?")) for item in violations)
    type_counts = Counter(str(item.get("type", "?")) for item in violations)
    expected_types = Counter({str(k): int(v) for k, v in contract["allowed_warning_types_exact"].items()})
    expected_errors = int(contract["expected_error_count"])
    expected_warnings = int(contract["expected_warning_count"])
    expected_unconnected = int(contract["expected_unconnected_items"])

    print("DRC_TYPE_COUNTS", dict(sorted(type_counts.items())))
    print("DRC_SEVERITY_COUNTS", dict(sorted(severity_counts.items())))

    actual_errors = int(severity_counts.get("error", 0))
    if actual_errors != expected_errors:
        fail(f"errores DRC PR17: actual={actual_errors}, esperado={expected_errors}")

    non_warning = {sev: count for sev, count in severity_counts.items() if sev != "warning" and count}
    if non_warning:
        fail(f"severidades DRC no autorizadas: {non_warning}")

    if type_counts != expected_types:
        missing = expected_types - type_counts
        extra = type_counts - expected_types
        fail(
            "deuda warning PR17 cambió: "
            f"actual={dict(sorted(type_counts.items()))}; "
            f"esperado={dict(sorted(expected_types.items()))}; "
            f"faltante={dict(missing)}; extra={dict(extra)}"
        )

    if sum(type_counts.values()) != expected_warnings:
        fail(f"warning count PR17: actual={sum(type_counts.values())}, esperado={expected_warnings}")

    forbidden = set(contract.get("forbidden_violation_types", []))
    forbidden_seen = forbidden & set(type_counts)
    if forbidden_seen:
        fail(f"tipos físicos/eléctricos prohibidos reaparecieron: {sorted(forbidden_seen)}")

    if len(unconnected) != expected_unconnected:
        fail(f"deuda unconnected PR17 cambió: actual={len(unconnected)}, esperado={expected_unconnected}")

    print("OK: DRC PR17 dentro de deuda acotada")
    print(f"- errors={actual_errors}; warnings={expected_warnings} exactos y solo de silk/text")
    print(f"- unconnected_items={len(unconnected)} exactos; routing=0")
    print("- sin clearance/short/courtyard ni otros tipos físicos prohibidos")
    print("- warnings silk/text deben eliminarse antes de artwork/Gerbers; unconnected durante routing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
