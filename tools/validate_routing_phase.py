#!/usr/bin/env python3
"""Guardrail reusable para fases incrementales de routing autorizadas.

No valida calidad eléctrica completa; eso corresponde a los gates específicos
de cada lote. Impide que validadores históricos confundan cobre autorizado con
regresión y rechaza cualquier cobre que no coincida exactamente con los
manifests y contratos versionados.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
PR19A_MANIFEST = ROOT / "hardware" / "pr19a_local_routing_manifest.json"
PR19B_MANIFEST = ROOT / "hardware" / "pr19b_analog_routing_manifest.json"
PR19C_MANIFEST = ROOT / "hardware" / "pr19c_digital_routing_manifest.json"


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
    """Retorna PRE_ROUTING, PR19A, PR19B o PR19C; falla fuera de checkpoints."""
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
    pr19c = set(batches["PR19C"]["nets"])
    future_after_a = pr19b | pr19c | set(batches["PR20A"]["nets"]) | set(batches["PR20B"]["nets"])
    future_after_b = pr19c | set(batches["PR20A"]["nets"]) | set(batches["PR20B"]["nets"])
    future_after_c = set(batches["PR20A"]["nets"]) | set(batches["PR20B"]["nets"])

    routed_a = set(rm_a.get("routed_nets", []))
    deferred_a = set(rm_a.get("deferred_nets", []))
    if rm_a.get("status") != "LOCAL_ROUTING_PR19A":
        _fail(context, "manifest PR19A no tiene status LOCAL_ROUTING_PR19A")
    if routed_a != pr19a or len(routed_a) != 28:
        _fail(context, f"routed_nets PR19A no coincide con contrato: {len(routed_a)}")
    if deferred_a != future_after_a or len(deferred_a) != 31:
        _fail(context, f"deferred_nets PR19A no coincide con las 31 nets futuras: {len(deferred_a)}")

    expected_a = {"segments": len(rm_a.get("segments", [])), "vias": len(rm_a.get("vias", [])), "zones": 0}
    if expected_a != {"segments": 523, "vias": 24, "zones": 0}:
        _fail(context, f"checkpoint PR19A inesperado: {expected_a}")
    if not PR19B_MANIFEST.exists():
        if counts != expected_a:
            _fail(context, f"PCB no coincide con PR19A: actual={counts} esperado={expected_a}")
        return "PR19A"

    rm_b = _load(PR19B_MANIFEST)
    targets_b = rm_b.get("target_nets", [])
    if rm_b.get("status") != "ANALOG_ROUTING_PR19B":
        _fail(context, "manifest PR19B no tiene status ANALOG_ROUTING_PR19B")
    if set(targets_b) != pr19b or len(targets_b) != 4:
        _fail(context, f"target_nets PR19B no coincide con contrato: {targets_b}")
    if rm_b.get("baseline_pr19a", {}) != {"segments": 523, "vias": 24}:
        _fail(context, "baseline PR19B no coincide con PR19A")
    seg_b = rm_b.get("new_segments", []); via_b = rm_b.get("new_vias", [])
    if int(rm_b.get("new_segment_count", -1)) != len(seg_b) or len(seg_b) != 32:
        _fail(context, f"PR19B no contiene 32 segmentos: {len(seg_b)}")
    if int(rm_b.get("new_via_count", -1)) != len(via_b) or len(via_b) != 7:
        _fail(context, f"PR19B no contiene 7 vías: {len(via_b)}")
    touched_b = {x.get("net") for x in seg_b + via_b}
    if touched_b != pr19b or touched_b & future_after_b:
        _fail(context, f"cobre PR19B fuera de alcance: {sorted(touched_b)}")
    if rm_b.get("policies", {}) != {"in1_signal_tracks": 0, "zones_added": 0, "future_batch_copper": 0}:
        _fail(context, f"políticas PR19B inesperadas: {rm_b.get('policies')}")
    expected_b = {"segments": 555, "vias": 31, "zones": 0}
    if not PR19C_MANIFEST.exists():
        if counts != expected_b:
            _fail(context, f"PCB no coincide con PR19B: actual={counts} esperado={expected_b}")
        return "PR19B"

    rm_c = _load(PR19C_MANIFEST)
    targets_c = rm_c.get("target_nets", [])
    if rm_c.get("status") != "DIGITAL_ROUTING_PR19C":
        _fail(context, "manifest PR19C no tiene status DIGITAL_ROUTING_PR19C")
    if set(targets_c) != pr19c or len(targets_c) != 16:
        _fail(context, f"target_nets PR19C no coincide con contrato: {targets_c}")
    if rm_c.get("baseline", {}) != {"segments": 555, "vias": 31}:
        _fail(context, f"baseline PR19C no coincide con PR19B: {rm_c.get('baseline')}")
    seg_c = rm_c.get("new_segments", []); via_c = rm_c.get("new_vias", [])
    if int(rm_c.get("new_segment_count", -1)) != len(seg_c) or len(seg_c) != 362:
        _fail(context, f"PR19C no contiene exactamente 362 segmentos nuevos: {len(seg_c)}")
    if int(rm_c.get("new_via_count", -1)) != len(via_c) or len(via_c) != 88:
        _fail(context, f"PR19C no contiene exactamente 88 vías nuevas: {len(via_c)}")
    touched_c = {x.get("net") for x in seg_c + via_c}
    if touched_c != pr19c:
        _fail(context, f"cobre PR19C no cubre exactamente sus 16 nets: {sorted(touched_c)}")
    if touched_c & future_after_c:
        _fail(context, f"PR19C adelanta lotes PR20: {sorted(touched_c & future_after_c)}")
    if rm_c.get("policies", {}) != {"in1_signal_tracks": 0, "zones_added": 0, "future_batch_copper": 0}:
        _fail(context, f"políticas PR19C inesperadas: {rm_c.get('policies')}")
    stats = rm_c.get("net_stats", [])
    if len(stats) != 16 or {x.get("net") for x in stats} != pr19c:
        _fail(context, "net_stats PR19C no cubre 16/16")
    if any(int(x.get("via_count", 999)) > 10 or int(x.get("segment_count", 999)) > 140 for x in stats):
        _fail(context, "PR19C excede límites de calidad geométrica")

    expected_c = {"segments": 917, "vias": 119, "zones": 0}
    if counts != expected_c:
        _fail(context, f"PCB no coincide con PR19C: actual={counts} esperado={expected_c}")
    return "PR19C"
