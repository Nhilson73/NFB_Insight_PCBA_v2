#!/usr/bin/env python3
"""Gate PR18: congela las reglas y verifica routing posterior contra lotes autorizados."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "hardware" / "routing_contract.json"
PLACEMENT = ROOT / "hardware" / "placement_manifest.json"
POWER_BASELINE = ROOT / "hardware" / "power_netclasses.json"
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
PR19A_MANIFEST = ROOT / "hardware" / "pr19a_local_routing_manifest.json"
NETLISTS = [
    ROOT / "hardware" / "z1_production_netlist.json",
    ROOT / "hardware" / "z2_production_netlist.json",
    ROOT / "hardware" / "power_production_netlist.json",
    ROOT / "hardware" / "z4_production_netlist.json",
]


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def load(path: Path):
    if not path.exists():
        fail(f"falta {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def collect_production_nets() -> set[str]:
    nets: set[str] = set()
    for path in NETLISTS:
        data = load(path)
        entries = data.get("nets")
        if not isinstance(entries, list):
            fail(f"{path.name} no contiene lista nets")
        for item in entries:
            name = item.get("name")
            if not isinstance(name, str) or not name:
                fail(f"net inválida en {path.name}: {item!r}")
            nets.add(name)
    return nets


def main() -> int:
    c = load(CONTRACT)
    p = load(PLACEMENT)
    baseline = load(POWER_BASELINE)

    if c.get("status") != "ROUTING_READINESS_PR18":
        fail("status de routing_contract no es ROUTING_READINESS_PR18")
    scope = c.get("scope", {})
    if scope.get("routing_allowed_in_pr18") is not False:
        fail("PR18 debe mantener routing_allowed_in_pr18=false")
    if scope.get("routing_allowed_after_pr18_merge") is not True:
        fail("PR18 debe habilitar routing únicamente después de su merge")
    for key in ("placement_changes_allowed", "board_geometry_changes_allowed", "netlist_changes_allowed"):
        if scope.get(key) is not False:
            fail(f"PR18 no puede habilitar {key}")

    if p.get("status") != "PRODUCTION_PLACEMENT_PR17":
        fail("placement_manifest no corresponde a PR17 cerrado")
    board = p.get("board", {})
    frozen = c.get("board_frozen", {})
    for key in ("width_mm", "height_mm", "growth_only"):
        if board.get(key) != frozen.get(key):
            fail(f"board_frozen.{key} difiere del placement PR17: {frozen.get(key)} != {board.get(key)}")
    if board.get("origin_mm") != frozen.get("origin_mm"):
        fail("origen PR17 no preservado")
    if p.get("policies", {}).get("routing_allowed") is not False:
        fail("placement_manifest PR17 histórico debe preservar routing_allowed=false")

    production_nets = collect_production_nets()
    expected_count = int(scope.get("expected_production_net_count", -1))
    if len(production_nets) != expected_count:
        fail(f"conteo de nets producción cambió: {len(production_nets)} != {expected_count}")

    classes = c.get("routing_classes")
    if not isinstance(classes, list) or not classes:
        fail("routing_classes vacío")
    assignments: list[str] = []
    class_by_name = {}
    for rc in classes:
        name = rc.get("name")
        if not isinstance(name, str) or not name:
            fail("routing class sin nombre")
        if name in class_by_name:
            fail(f"routing class duplicada: {name}")
        class_by_name[name] = rc
        nets = rc.get("nets")
        if not isinstance(nets, list) or not nets:
            fail(f"routing class {name} sin nets")
        assignments.extend(nets)
        for num_key in ("track_width_mm_min", "clearance_mm_min", "via_diameter_mm_min", "via_drill_mm_min"):
            val = rc.get(num_key)
            if not isinstance(val, (int, float)) or val <= 0:
                fail(f"{name}.{num_key} inválido: {val}")
        if rc["via_drill_mm_min"] >= rc["via_diameter_mm_min"]:
            fail(f"{name}: via drill debe ser menor que diámetro")

    dup = sorted(n for n, count in Counter(assignments).items() if count != 1)
    if dup:
        fail(f"nets con asignación duplicada/no única: {dup}")
    assigned = set(assignments)
    missing = sorted(production_nets - assigned)
    extra = sorted(assigned - production_nets)
    if missing or extra:
        fail(f"cobertura routing classes inválida; missing={missing}; extra={extra}")

    forbidden = set(c.get("forbidden_production_nets", []))
    present_forbidden = sorted(production_nets & forbidden)
    if present_forbidden:
        fail(f"nets prohibidas reaparecieron: {present_forbidden}")

    base_by_name = {item["name"]: item for item in baseline.get("classes", [])}
    for name in ("PWR_INPUT_5A", "PWR_12V_BRANCH", "PWR_5V", "PWR_3V3"):
        old = base_by_name.get(name)
        new = class_by_name.get(name)
        if not old or not new:
            fail(f"falta clase heredada {name}")
        if set(old.get("nets", [])) != set(new.get("nets", [])):
            fail(f"{name}: cambió membresía respecto PR10")
        for key in ("track_width_mm_min", "clearance_mm_min", "via_diameter_mm_min", "via_drill_mm_min"):
            if float(new[key]) < float(old[key]):
                fail(f"{name}.{key} debilitado: {new[key]} < {old[key]}")

    layer = c.get("layer_policy", {})
    if layer.get("in1_signal_routing_allowed") is not False or layer.get("in1_plane_net") != "GND":
        fail("In1.Cu debe permanecer GND continuo sin signal routing")
    if "CONTINUOUS_GND_REFERENCE_NO_SIGNAL_ROUTING" not in str(layer.get("In1.Cu", "")):
        fail("intent de In1.Cu no está congelado")

    cross = c.get("cross_class_rules", {})
    sensitive = set(cross.get("sensitive_nets", []))
    dirty = set(cross.get("dirty_nets", []))
    if not sensitive <= production_nets or not dirty <= production_nets:
        fail("sensitive_nets/dirty_nets contiene nets fuera de producción")
    if sensitive & dirty:
        fail("una net no puede ser simultáneamente sensitive y dirty")
    if float(cross.get("minimum_parallel_spacing_sensitive_to_dirty_mm", 0)) < 1.0:
        fail("spacing sensitive↔dirty no puede ser menor de 1.00 mm")

    pcb_text = PCB.read_text(encoding="utf-8")
    counts = {
        "tracks": len(re.findall(r"(?m)^\s*\(segment\b", pcb_text)),
        "vias": len(re.findall(r"(?m)^\s*\(via\b", pcb_text)),
        "zones": len(re.findall(r"(?m)^\s*\(zone\b", pcb_text)),
    }
    pre_routing = {
        "tracks": int(scope.get("expected_tracks_pr18", -1)),
        "vias": int(scope.get("expected_vias_pr18", -1)),
        "zones": int(scope.get("expected_copper_zones_pr18", -1)),
    }
    if PR19A_MANIFEST.exists():
        rb = load(BATCHES)
        rm = load(PR19A_MANIFEST)
        batches = {x["id"]: x for x in rb.get("batches", [])}
        if set(batches) != {"PR19A", "PR19B", "PR19C", "PR20A", "PR20B"}:
            fail("partición incremental de routing inválida")
        allowed = set(batches["PR19A"]["nets"])
        routed = set(rm.get("routed_nets", []))
        deferred = set(rm.get("deferred_nets", []))
        if rm.get("status") != "LOCAL_ROUTING_PR19A" or routed != allowed or len(routed) != 28:
            fail("manifest PR19A no acredita 28/28")
        if deferred != (production_nets - allowed) or len(deferred) != 31:
            fail("manifest PR19A no preserva exactamente las 31 nets futuras")
        expected_now = {
            "tracks": len(rm.get("segments", [])),
            "vias": len(rm.get("vias", [])),
            "zones": 0,
        }
        if counts != expected_now:
            fail(f"PCB no coincide con manifest PR19A: actual={counts}, esperado={expected_now}")
    elif counts != pre_routing:
        fail(f"cobre presente sin manifest de lote autorizado: actual={counts}, esperado PR18={pre_routing}")

    if set(class_by_name["ANALOG_SENSITIVE"]["nets"]) != {
        "PH_ADC", "ORP_ADC", "DO_ADC", "LOAD_A_POS", "LOAD_A_NEG", "HX_VBG", "PUMP_CURRENT_ADC"
    }:
        fail("ANALOG_SENSITIVE cambió sin revisión explícita")
    if set(class_by_name["ACTUATOR_OUTPUT"]["nets"]) != {"PUMP_OUT1", "PUMP_OUT2", "CO2_SOL_POS"}:
        fail("ACTUATOR_OUTPUT cambió sin revisión explícita")
    if set(class_by_name["CHILLER_DRY_CONTACT"]["nets"]) != {"CHILLER_CONTACT_A", "CHILLER_CONTACT_B"}:
        fail("frontera dry-contact cambió")

    print("OK: routing readiness PR18 preservado y fase posterior gobernada")
    print(f"- production nets: {len(production_nets)}/{expected_count}, cobertura exacta y única")
    print(f"- routing classes: {len(classes)}")
    print("- In1.Cu = GND continuo; signal routing prohibido")
    print("- board/placement congelados: 242.34 x 68.58 mm")
    print(f"- cobre actual: tracks={counts['tracks']} vias={counts['vias']} zones={counts['zones']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
