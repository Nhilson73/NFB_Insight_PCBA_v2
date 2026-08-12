#!/usr/bin/env python3
"""Valida que PR14 solo conserve la deuda ERC intencional de interfaces abstractas.

PR14 no materializa símbolos internos. Por ello KiCad reporta label_dangling en
labels/hierarchical labels que terminan en la frontera EDA. Este gate NO cambia
la severidad global: exige exactamente el conteo congelado y rechaza cualquier
otro tipo de violación. PR15 debe eliminar esta deuda y llegar a ERC=0.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "hardware" / "root_eda_contract.json"

def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)

def main() -> int:
    if len(sys.argv) != 2:
        fail("uso: validate_pr14_erc_report.py <erc-report.rpt>")
    rpt = Path(sys.argv[1])
    if not rpt.exists():
        fail(f"no existe reporte ERC: {rpt}")
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    p = c.get("erc_interzone_policy", {})
    if c.get("schema_version") != 2 or p.get("mode") != "BOUNDED_INTENTIONAL_INTERFACE_DEBT_PR14":
        fail("contrato root no congela política ERC PR14")
    expected_type = p.get("expected_violation_type")
    expected_count = int(p.get("expected_violation_count", -1))
    if expected_type != "label_dangling" or expected_count <= 0 or int(p.get("unexpected_violation_count_allowed", -1)) != 0:
        fail("política ERC PR14 inválida")
    text = rpt.read_text(encoding="utf-8-sig", errors="replace")
    kinds = re.findall(r"^\[([^\]]+)\]:", text, flags=re.MULTILINE)
    if len(kinds) != expected_count:
        fail(f"conteo ERC cambió: esperado {expected_count}, observado {len(kinds)}")
    unexpected = sorted({k for k in kinds if k != expected_type})
    if unexpected:
        fail(f"violaciones ERC inesperadas: {unexpected}")
    summary = re.search(r"ERC messages:\s*(\d+)\s+Errors\s+(\d+)\s+Warnings\s+(\d+)", text)
    if not summary:
        fail("reporte ERC sin resumen parseable")
    total, errors, warnings = map(int, summary.groups())
    if (total, errors, warnings) != (expected_count, expected_count, 0):
        fail(f"resumen ERC inesperado: total={total}, errors={errors}, warnings={warnings}")
    if "label_dangling" not in text:
        fail("reporte no contiene label_dangling")
    print(f"OK: PR14 conserva exactamente {expected_count} label_dangling intencionales y 0 violaciones inesperadas")
    print("- severidades KiCad no fueron relajadas; PR15 debe eliminar esta deuda y alcanzar ERC=0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
