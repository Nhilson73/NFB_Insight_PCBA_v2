#!/usr/bin/env python3
"""Valida la partición incremental de routing 28+4+16+10+1.

El contrato PR18 sigue siendo autoridad sobre clases y reglas eléctricas.
Este gate garantiza que la estrategia incremental cubra exactamente las 59 nets,
sin duplicados ni omisiones, y que cada lote conserve su conteo congelado.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTING = ROOT / "hardware" / "routing_contract.json"
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
KB = ROOT / "docs" / "ROUTING_KNOWLEDGE_BASE.md"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def main() -> int:
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))

    if batches.get("status") != "INCREMENTAL_ROUTING_BATCHES_FROZEN":
        fail("routing_batches_contract no está congelado")
    if batches.get("strategy") != "divide_y_venceras":
        fail("estrategia incremental no preservada")
    if not KB.exists():
        fail("falta docs/ROUTING_KNOWLEDGE_BASE.md")

    production = []
    for cls in routing.get("routing_classes", []):
        production.extend(cls.get("nets", []))
    if len(production) != 59 or len(set(production)) != 59:
        fail(f"routing_contract debe contener 59 nets únicas; obtuvo {len(production)} / {len(set(production))}")

    expected_ids = ["PR19A", "PR19B", "PR19C", "PR20A", "PR20B"]
    expected_counts = [28, 4, 16, 10, 1]
    batch_list = batches.get("batches", [])
    if [b.get("id") for b in batch_list] != expected_ids:
        fail("IDs/orden de lotes divergieron de PR19A→PR20B")
    if [b.get("expected_net_count") for b in batch_list] != expected_counts:
        fail("conteos de lotes divergieron de 28+4+16+10+1")

    seen: list[str] = []
    for b in batch_list:
        nets = b.get("nets", [])
        if len(nets) != b.get("expected_net_count"):
            fail(f"{b['id']}: expected_net_count no coincide con lista real")
        if len(nets) != len(set(nets)):
            fail(f"{b['id']}: contiene nets duplicadas")
        seen.extend(nets)

    if len(seen) != 59:
        fail(f"suma de lotes !=59: {len(seen)}")
    if len(set(seen)) != 59:
        dup = sorted({n for n in seen if seen.count(n) > 1})
        fail(f"nets duplicadas entre lotes: {dup}")

    pset = set(production)
    bset = set(seen)
    missing = sorted(pset - bset)
    extra = sorted(bset - pset)
    if missing or extra:
        fail(f"partición no exhaustiva: missing={missing} extra={extra}")

    inv = batches.get("invariants", {})
    required_false = [
        "placement_changes_allowed",
        "board_geometry_changes_allowed",
        "netlist_changes_allowed",
        "in1_signal_routing_allowed_before_pr20b",
    ]
    for key in required_false:
        if inv.get(key) is not False:
            fail(f"invariante debe ser false: {key}")
    if inv.get("batch_merge_policy") != "ALL_OR_NOTHING":
        fail("batch_merge_policy debe ser ALL_OR_NOTHING")

    print("OK: estrategia incremental de routing validada")
    print("PRODUCTION_NETS=59")
    print("BATCHES=PR19A:28 PR19B:4 PR19C:16 PR20A:10 PR20B:1")
    print("POLICY=ALL_OR_NOTHING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
