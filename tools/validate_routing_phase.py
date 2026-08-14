#!/usr/bin/env python3
"""Guardrail reusable para fases incrementales de routing autorizadas.

No valida calidad eléctrica completa; eso corresponde a los gates específicos
de cada lote. Su misión es impedir que validadores históricos confundan cobre
autorizado con regresión y rechazar cualquier cobre que no coincida exactamente
con los manifests y contratos versionados.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
PR19A_MANIFEST = ROOT / "hardware" / "pr19a_local_routing_manifest.json"
PR19B_MANIFEST = ROOT / "hardware" / "pr19b_analog_routing_manifest.json"


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
    """Retorna PRE_ROUTING, PR19A o PR19B; falla si el cobre no está autorizado."""
    counts = copper_counts(pcb_text)
    if counts == {"segments": 0, "vias": 0, "zones": 0}:
        return "PRE_ROUTING"

    if not BATCHES.exists() or not PR19A_MANIFEST.exists():
        _fail(context, f"cobre presente sin contrato/manifest incremental: {counts}")

    rb = _load(BATCHES)
    rm_a = _load(PR19A_MANIFEST)
    batches = {x["id"]: x for x in rb.get("batches", [])}
    expected_ids = {"PR19A", "PR19B", "PR19C", "PR20A", "PR20B"}
    if set(batches) != expected_ids:
        _fail(context, f"partición de routing inesperada: {sorted(batches)}")

    pr19a = set(batches["PR19A"]["nets"])
    pr19b = set(batches["PR19B"]["nets"])
    future_after_a = set().union(*(set(batches[x]["nets"]) for x in ("PR19B", "PR19C", "PR20A", "PR20B")))
    future_after_b = set().union(*(set(batches[x]["nets"]) for x in ("PR19C", "PR20A", "PR20B")))

    routed_a = set(rm_a.get("routed_nets", []))
    deferred_a = set(rm_a.get("deferred_nets", []))
    if rm_a.get("status") != "LOCAL_ROUTING_PR19A":
        _fail(context, "manifest PR19A no tiene status LOCAL_ROUTING_PR19A")
    if routed_a != pr19a or len(routed_a) != 28:
        _fail(context, f"routed_nets PR19A no coincide con contrato: {len(routed_a)}")
    if deferred_a != future_after_a or len(deferred_a) != 31:
        _fail(context, f"deferred_nets PR19A no coincide con las 31 nets futuras: {len(deferred_a)}")
    if routed_a & future_after_a:
        _fail(context, f"PR19A adelanta nets futuras: {sorted(routed_a & future_after_a)}")

    expected_a = {
        "segments": len(rm_a.get("segments", [])),
        "vias": len(rm_a.get("vias", [])),
        "zones": 0,
    }
    if expected_a != {"segments": 523, "vias": 24, "zones": 0}:
        _fail(context, f"checkpoint PR19A inesperado en manifest: {expected_a}")

    if not PR19B_MANIFEST.exists():
        if counts != expected_a:
            _fail(context, f"PCB no coincide con manifest PR19A: actual={counts} esperado={expected_a}")
        return "PR19A"

    rm_b = _load(PR19B_MANIFEST)
    targets = rm_b.get("target_nets", [])
    target_set = set(targets)
    if rm_b.get("status") != "ANALOG_ROUTING_PR19B":
        _fail(context, "manifest PR19B no tiene status ANALOG_ROUTING_PR19B")
    if target_set != pr19b or len(targets) != 4 or len(target_set) != 4:
        _fail(context, f"target_nets PR19B no coincide con contrato: {targets}")

    baseline = rm_b.get("baseline_pr19a", {})
    if baseline != {"segments": 523, "vias": 24}:
        _fail(context, f"baseline PR19B no coincide con checkpoint PR19A: {baseline}")

    new_segments = rm_b.get("new_segments", [])
    new_vias = rm_b.get("new_vias", [])
    if int(rm_b.get("new_segment_count", -1)) != len(new_segments) or len(new_segments) != 32:
        _fail(context, f"PR19B debe contener exactamente 32 segmentos nuevos: {len(new_segments)}")
    if int(rm_b.get("new_via_count", -1)) != len(new_vias) or len(new_vias) != 7:
        _fail(context, f"PR19B debe contener exactamente 7 vías nuevas: {len(new_vias)}")

    touched_b = {x.get("net") for x in new_segments + new_vias}
    if touched_b != pr19b:
        _fail(context, f"cobre PR19B no cubre exactamente sus 4 nets: {sorted(touched_b)}")
    if touched_b & future_after_b:
        _fail(context, f"PR19B adelanta lotes futuros: {sorted(touched_b & future_after_b)}")

    policies = rm_b.get("policies", {})
    expected_policies = {"in1_signal_tracks": 0, "zones_added": 0, "future_batch_copper": 0}
    if policies != expected_policies:
        _fail(context, f"políticas PR19B inesperadas: {policies}")

    expected_b = {
        "segments": expected_a["segments"] + len(new_segments),
        "vias": expected_a["vias"] + len(new_vias),
        "zones": 0,
    }
    if expected_b != {"segments": 555, "vias": 31, "zones": 0}:
        _fail(context, f"checkpoint PR19B inesperado: {expected_b}")
    if counts != expected_b:
        _fail(context, f"PCB no coincide con checkpoint PR19B: actual={counts} esperado={expected_b}")

    return "PR19B"
