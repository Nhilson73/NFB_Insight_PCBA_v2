#!/usr/bin/env python3
"""Guardrail reusable para distinguir PRE_ROUTING de PR19A materializado.

No valida calidad eléctrica completa; eso corresponde a validate_pr19a_local.py.
Su misión es impedir que validadores históricos confundan cobre autorizado con
regresión y, a la vez, rechazar cualquier cobre que no coincida exactamente con
el lote PR19A versionado.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
MANIFEST = ROOT / "hardware" / "pr19a_local_routing_manifest.json"


def _fail(context: str, msg: str) -> None:
    raise SystemExit(f"ERROR: {context}: {msg}")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def copper_counts(pcb_text: str) -> dict[str, int]:
    return {
        "segments": len(re.findall(r"(?m)^\s*\(segment\b", pcb_text)),
        "vias": len(re.findall(r"(?m)^\s*\(via\b", pcb_text)),
        "zones": len(re.findall(r"(?m)^\s*\(zone\b", pcb_text)),
    }


def assert_authorized_phase(pcb_text: str, context: str = "routing phase") -> str:
    """Retorna PRE_ROUTING o PR19A; falla si el cobre no está autorizado."""
    counts = copper_counts(pcb_text)
    if counts == {"segments": 0, "vias": 0, "zones": 0}:
        return "PRE_ROUTING"

    if not BATCHES.exists() or not MANIFEST.exists():
        _fail(context, f"cobre presente sin contrato/manifest incremental: {counts}")

    rb = _load(BATCHES)
    rm = _load(MANIFEST)
    batches = {x["id"]: x for x in rb.get("batches", [])}
    expected_ids = {"PR19A", "PR19B", "PR19C", "PR20A", "PR20B"}
    if set(batches) != expected_ids:
        _fail(context, f"partición de routing inesperada: {sorted(batches)}")

    pr19a = set(batches["PR19A"]["nets"])
    future = set().union(*(set(batches[x]["nets"]) for x in ("PR19B", "PR19C", "PR20A", "PR20B")))
    routed = set(rm.get("routed_nets", []))
    deferred = set(rm.get("deferred_nets", []))

    if rm.get("status") != "LOCAL_ROUTING_PR19A":
        _fail(context, "manifest no tiene status LOCAL_ROUTING_PR19A")
    if routed != pr19a or len(routed) != 28:
        _fail(context, f"routed_nets no coincide con PR19A: {len(routed)}")
    if deferred != future or len(deferred) != 31:
        _fail(context, f"deferred_nets no coincide con las 31 nets futuras: {len(deferred)}")
    if routed & future:
        _fail(context, f"nets futuras adelantadas: {sorted(routed & future)}")

    expected_counts = {
        "segments": len(rm.get("segments", [])),
        "vias": len(rm.get("vias", [])),
        "zones": 0,
    }
    if expected_counts != {"segments": 523, "vias": 24, "zones": 0}:
        _fail(context, f"checkpoint PR19A inesperado en manifest: {expected_counts}")
    if counts != expected_counts:
        _fail(context, f"PCB no coincide con manifest PR19A: actual={counts} esperado={expected_counts}")

    return "PR19A"
