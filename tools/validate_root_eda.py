#!/usr/bin/env python3
"""Valida el root EDA PR15 materializado contra contratos JSON/BOM de producción."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "hardware" / "root_eda_contract.json"
MATERIAL = ROOT / "hardware" / "eda_materialization_contract.json"
PIN = ROOT / "hardware" / "insight_pin_contract.json"
Z1 = ROOT / "hardware" / "z1_production_netlist.json"
Z2 = ROOT / "hardware" / "z2_production_netlist.json"
POWER = ROOT / "hardware" / "power_production_netlist.json"
Z4 = ROOT / "hardware" / "z4_production_netlist.json"
AUDIT = ROOT / "hardware" / "footprint_audit.json"
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
ROOTSCH = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_sch"
NORMALIZER = ROOT / "tools" / "normalize_pr15_schematics.py"
MIGRATOR = ROOT / "tools" / "migrate_pr15_verified_footprints.py"
GENLIB = ROOT / "kicad" / "lib" / "nfb_generated.kicad_sym"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def labels(text: str, kind: str) -> list[str]:
    if kind == "hier":
        return re.findall(r'\(hierarchical_label "([^"]+)"', text)
    if kind == "local":
        return re.findall(r'\(label "([^"]+)"', text)
    if kind == "pin":
        return re.findall(
            r'\(pin "([^"]+)"\s+(?:input|output|bidirectional|tri_state|passive)',
            text,
        )
    raise ValueError(kind)


def run_check(path: Path) -> None:
    cp = subprocess.run(
        [sys.executable, str(path), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if cp.returncode:
        fail(f"{path.name} --check falló:\n{cp.stdout}{cp.stderr}".rstrip())


def component_map(*netlists: dict) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for data in netlists:
        for comp in data["components"]:
            ref = comp["ref"]
            if ref in result:
                fail(f"referencia duplicada entre zonas: {ref}")
            result[ref] = comp
    return result


def materialization_fixes(material: dict) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for item in material.get("footprint_link_closures", []):
        refs = item.get("references") or [item.get("reference")]
        for ref in refs:
            if not ref:
                fail("eda_materialization_contract tiene closure sin referencia")
            if ref in result:
                fail(f"closure duplicado en eda_materialization_contract: {ref}")
            result[ref] = (item["mpn"], item["footprint"])
    return result


def main() -> int:
    required = (
        CONTRACT,
        MATERIAL,
        PIN,
        Z1,
        Z2,
        POWER,
        Z4,
        AUDIT,
        PCB,
        ROOTSCH,
        NORMALIZER,
        MIGRATOR,
        GENLIB,
    )
    for path in required:
        if not path.exists():
            fail(f"falta {path.relative_to(ROOT)}")

    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    material = json.loads(MATERIAL.read_text(encoding="utf-8"))
    pin = json.loads(PIN.read_text(encoding="utf-8"))
    z1 = json.loads(Z1.read_text(encoding="utf-8"))
    z2 = json.loads(Z2.read_text(encoding="utf-8"))
    power = json.loads(POWER.read_text(encoding="utf-8"))
    z4 = json.loads(Z4.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))

    if c.get("schema_version") != 3:
        fail("root EDA contract no es schema 3")
    if c.get("status") != "ROOT_EDA_PRODUCTION_MATERIALIZED_PR15":
        fail("root EDA contract no está cerrado como PR15")
    if material.get("schema_version") != 1 or material.get("status") != "PRODUCTION_EDA_MATERIALIZED_PR15":
        fail("eda_materialization_contract no está cerrado como PR15/schema1")

    scope = c.get("scope", {})
    expected_scope = {
        "interzone_hierarchy": True,
        "zone_internal_component_symbols": True,
        "generated_from_production_contracts": True,
        "placement": False,
        "routing": False,
        "pcb_geometry_change": False,
    }
    if scope != expected_scope:
        fail(f"scope PR15 inesperado: {scope}")

    erc = c.get("erc_policy", {})
    if (
        erc.get("mode") != "ZERO_VIOLATIONS_REQUIRED_PR15"
        or int(erc.get("expected_errors", -1)) != 0
        or int(erc.get("expected_warnings", -1)) != 0
        or int(erc.get("expected_total_violations", -1)) != 0
        or erc.get("severity_relaxation_allowed") is not False
    ):
        fail("política ERC PR15 no exige cero violaciones")

    merc = material.get("erc_gate", {})
    if (
        merc.get("root") != "kicad/NFB_Insight_PCBA_v2.kicad_sch"
        or int(merc.get("required_errors", -1)) != 0
        or int(merc.get("required_warnings", -1)) != 0
        or merc.get("severity_all") is not True
        or merc.get("exit_code_violations") is not True
        or merc.get("pr14_debt_eliminated") is not True
    ):
        fail("eda_materialization_contract no exige ERC 0/0 real")

    toolchain = material.get("toolchain", {})
    expected_tools = {
        "generator": "tools/generate_production_schematics.py",
        "normalizer": "tools/normalize_pr15_schematics.py",
        "verified_footprint_migrator": "tools/migrate_pr15_verified_footprints.py",
        "kicad_ci_version": "10.0.5",
    }
    for key, value in expected_tools.items():
        if toolchain.get(key) != value:
            fail(f"toolchain PR15 cambió: {key}")

    expected_outputs = {
        "kicad/uno_q_interface.kicad_sch",
        "kicad/z1_interface.kicad_sch",
        "kicad/z2_interface.kicad_sch",
        "kicad/z3_interface.kicad_sch",
        "kicad/z4_interface.kicad_sch",
        "kicad/lib/nfb_generated.kicad_sym",
    }
    if set(material.get("outputs", [])) != expected_outputs:
        fail("outputs de materialización PR15 cambiaron")

    if pin.get("schema_version") != 6:
        fail("pin contract no es schema 6")
    if z1.get("status") != "FROZEN_Z1_NETLIST_PR6_POWER_CORRECTED_PR9":
        fail("Z1 baseline cambió")
    if z2.get("status") != "FROZEN_Z2_NETLIST_PR7_POWER_CORRECTED_PR9":
        fail("Z2 baseline cambió")
    if power.get("status") != "FROZEN_POWER_NETLIST_PR10_FOOTPRINTS_CLOSED_PR13":
        fail("power no conserva PR10+PR13")
    if z4.get("status") != "FROZEN_Z4_NETLIST_PR12_FOOTPRINTS_CLOSED_PR13":
        fail("Z4 no conserva PR12+PR13")
    if audit.get("status") != "FOOTPRINT_AUDIT_CLOSED_PR13":
        fail("footprints críticos PR13 no están cerrados")

    # Paridad y reproducibilidad son parte del gate, no documentación opcional.
    run_check(MIGRATOR)
    run_check(NORMALIZER)

    sheets = {item["id"]: item for item in c["sheets"]}
    if set(sheets) != {"Z0", "Z1", "Z2", "Z3", "Z4"}:
        fail("deben existir exactamente Z0..Z4")
    for item in sheets.values():
        path = ROOT / item["file"]
        if not path.exists():
            fail(f"falta child sheet {item['file']}")

    inter = {net: set(zones) for net, zones in c["interzone_nets"].items()}
    forbidden = {"CO2_ADC", "TEMP_ADC", "HUM_ADC", "CO2_PWM", "CO2_FLOW_PWM", "RS485_IRQ_RSVD"}
    bad = forbidden & set(inter)
    if bad:
        fail(f"nets prohibidas en root: {sorted(bad)}")

    active_host = {
        item.get("net")
        for item in pin["pins"]
        if str(item.get("status", "")).startswith("ACTIVE") and item.get("net")
    }
    if any(item.get("net") == "GND" for item in pin["pins"]):
        active_host.add("GND")
    z0 = {net for net, zones in inter.items() if "Z0" in zones}
    if active_host != z0:
        fail(
            "Z0 root != endpoints activos pin contract + GND; "
            f"falta={sorted(active_host-z0)} sobra={sorted(z0-active_host)}"
        )
    if "GND" not in z0:
        fail("UNO Q debe participar en GND común")
    if "3V3_RAIL" in z0 or "5V_RAIL" in z0:
        fail("host no puede alimentar rails locales")

    for zid, item in sheets.items():
        expected = {net for net, zones in inter.items() if zid in zones}
        text = (ROOT / item["file"]).read_text(encoding="utf-8")
        got = set(labels(text, "hier"))
        if got != expected:
            fail(
                f"{zid} hierarchical labels difieren; "
                f"falta={sorted(expected-got)} sobra={sorted(got-expected)}"
            )
        if '(global_label "' in text:
            fail(f"{zid} contiene global labels internos; PR15 exige alcance local")

    root = ROOTSCH.read_text(encoding="utf-8")
    for item in sheets.values():
        if Path(item["file"]).name not in root or item["name"] not in root:
            fail(f"root no instancia {item['id']}")

    pin_counts = Counter(labels(root, "pin"))
    label_counts = Counter(labels(root, "local"))
    for net, zones in inter.items():
        expected = len(zones)
        if pin_counts[net] != expected:
            fail(f"root sheet-pin count {net}={pin_counts[net]} esperado {expected}")
        if label_counts[net] != expected:
            fail(f"root local-label count {net}={label_counts[net]} esperado {expected}")
    extra_pins = set(pin_counts) - set(inter)
    extra_labels = set(label_counts) - set(inter)
    if extra_pins or extra_labels:
        fail(
            "root tiene nets no contractuales "
            f"pins={sorted(extra_pins)} labels={sorted(extra_labels)}"
        )

    if inter["I2C_SDA"] != {"Z0", "Z1", "Z2"} or inter["I2C_SCL"] != {"Z0", "Z1", "Z2"}:
        fail("I2C root ownership cambió")
    if inter["GND"] != {"Z0", "Z1", "Z2", "Z3", "Z4"}:
        fail("GND debe abarcar Z0..Z4")
    if inter["3V3_RAIL"] != {"Z1", "Z2", "Z3", "Z4"}:
        fail("3V3_RAIL ownership incorrecto")
    if inter["5V_RAIL"] != {"Z1", "Z2", "Z3"}:
        fail("5V_RAIL ownership incorrecto")

    comps = component_map(z1, z2, power, z4)
    root_fixes = {
        item["ref"]: (item["mpn"], item["footprint"])
        for item in c.get("pr15_verified_footprint_corrections", [])
    }
    material_fixes = materialization_fixes(material)
    if len(root_fixes) != 6 or root_fixes != material_fixes:
        fail("root contract y materialization contract divergen en footprints PR15")
    for ref, (mpn, footprint) in root_fixes.items():
        comp = comps.get(ref)
        if comp is None:
            fail(f"corrección PR15 apunta a ref inexistente: {ref}")
        if comp.get("mpn") != mpn:
            fail(f"{ref}: MPN no coincide con contratos PR15")
        if comp.get("footprint") != footprint:
            fail(f"{ref}: footprint no coincide con contratos PR15")

    pcb = PCB.read_text(encoding="utf-8")
    production_refs = [
        comp["ref"]
        for data in (z1, z2, power, z4)
        for comp in data["components"]
    ]
    placed = [ref for ref in production_refs if f'"{ref}"' in pcb]
    if placed:
        fail(f"PR15 no debe hacer placement; refs encontradas: {placed[:10]}")

    print("OK: root EDA PR15 materializado y reproducible")
    print(f"- {len(inter)} nets inter-zona / 5 sheets / JSON-BOM-KiCad parity")
    print("- root contract + materialization contract sincronizados")
    print("- placement/routing=0; ERC contractual requerido=0 errores/0 warnings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
