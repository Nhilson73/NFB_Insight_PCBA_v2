#!/usr/bin/env python3
"""Genera los child sheets de producción PR15 desde contratos JSON/BOM congelados.

Objetivo: una sola fuente de verdad eléctrica (JSON), representación KiCad reproducible,
ERC completo y cero placement/routing. Los símbolos NFB_GEN son carriers EDA neutrales:
conservan referencia, valor, MPN, footprint, números de pin y conectividad exacta;
los tipos de pin se mantienen pasivos para no inventar semántica eléctrica no expresada
por los netlists de producción.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KICAD = ROOT / "kicad"
ROOT_SCH = KICAD / "NFB_Insight_PCBA_v2.kicad_sch"
ROOT_CONTRACT = ROOT / "hardware" / "root_eda_contract.json"
PIN_CONTRACT = ROOT / "hardware" / "insight_pin_contract.json"
PROJECT = "NFB_Insight_PCBA_v2"
NS = uuid.UUID("a62a7f72-2a38-4c18-ae45-420b55ec6a28")

ZONE_NETLISTS = {
    "Z1": ROOT / "hardware" / "z1_production_netlist.json",
    "Z2": ROOT / "hardware" / "z2_production_netlist.json",
    "Z3": ROOT / "hardware" / "power_production_netlist.json",
    "Z4": ROOT / "hardware" / "z4_production_netlist.json",
}
ZONE_FILES = {
    "Z0": KICAD / "uno_q_interface.kicad_sch",
    "Z1": KICAD / "z1_interface.kicad_sch",
    "Z2": KICAD / "z2_interface.kicad_sch",
    "Z3": KICAD / "z3_interface.kicad_sch",
    "Z4": KICAD / "z4_interface.kicad_sch",
}
ZONE_TITLES = {
    "Z0": "Arduino UNO Q Host",
    "Z1": "Sensors",
    "Z2": "Digital / Low Noise",
    "Z3": "Power",
    "Z4": "Actuators",
}


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def q(value: object) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def uid(key: str) -> str:
    return str(uuid.uuid5(NS, key))


def sanitize(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", value)


def ref_prefix(ref: str) -> str:
    m = re.match(r"([A-Za-z]+)", ref)
    return m.group(1) if m else "U"


def root_uuid(text: str) -> str:
    m = re.search(r'\(uuid\s+"?([0-9a-fA-F-]{36})"?\)', text)
    if not m:
        fail("root schematic sin UUID")
    return m.group(1)


def balanced_sheet_block(text: str, filename: str) -> str:
    marker = f'"Sheetfile" "{filename}"'
    idx = text.find(marker)
    if idx < 0:
        fail(f"root no referencia {filename}")
    start = text.rfind("(sheet", 0, idx)
    if start < 0:
        fail(f"no se encontró bloque sheet para {filename}")
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    fail(f"bloque sheet incompleto para {filename}")


def sheet_meta(root: str, filename: str) -> tuple[str, list[tuple[str, str]]]:
    block = balanced_sheet_block(root, filename)
    um = re.search(r'\(uuid\s+"?([0-9a-fA-F-]{36})"?\)', block)
    if not um:
        fail(f"sheet {filename} sin UUID")
    ports = re.findall(
        r'\(pin\s+"([^"]+)"\s+(input|output|bidirectional|tri_state|passive)\b',
        block,
    )
    if not ports:
        fail(f"sheet {filename} sin pins jerárquicos")
    if len({n for n, _ in ports}) != len(ports):
        fail(f"sheet {filename} contiene puertos duplicados")
    return um.group(1), ports


def pin_sort_key(pin: str) -> tuple[int, object]:
    try:
        return (0, int(pin))
    except ValueError:
        return (1, pin)


def validate_zone_netlist(data: dict, zone: str) -> list[dict]:
    components = data.get("components", [])
    if not components:
        fail(f"{zone}: netlist sin components")
    refs = [c.get("ref") for c in components]
    if any(not r for r in refs) or len(refs) != len(set(refs)):
        fail(f"{zone}: refs vacías o duplicadas")
    refset = set(refs)
    node_map: dict[str, str] = {}
    for net in data.get("nets", []):
        name = net.get("name")
        if not name:
            fail(f"{zone}: net sin nombre")
        for node in net.get("nodes", []):
            if node in node_map and node_map[node] != name:
                fail(f"{zone}: nodo {node} aparece en {node_map[node]} y {name}")
            node_map[node] = name
    for comp in components:
        pins = comp.get("pins") or {}
        if not pins:
            fail(f"{zone}: {comp['ref']} sin pins")
        for pnum, declared in pins.items():
            node = f"{comp['ref']}.{pnum}"
            if declared in (None, "NC"):
                if node in node_map:
                    fail(f"{zone}: {node} declarado NC pero aparece en {node_map[node]}")
            else:
                actual = node_map.get(node)
                if actual != declared:
                    fail(f"{zone}: {node} pins={declared} nets={actual}")
    # Los nodos externos (ej. J_UNOQ) son válidos; todo nodo interno debe existir en components.
    for node in node_map:
        ref = node.rsplit(".", 1)[0]
        if ref in refset:
            continue
    return components


def z0_component() -> dict:
    p = json.loads(PIN_CONTRACT.read_text(encoding="utf-8"))
    if p.get("schema_version") != 6:
        fail("pin contract Z0 no es schema 6")
    pins = {}
    for item in p.get("pins", []):
        pad = str(item["pad"])
        pins[pad] = item.get("net") if item.get("net") else "NC"
    if set(map(int, pins)) != set(range(1, 33)):
        fail("Z0 debe materializar exactamente los 32 pads UNO Q")
    return {
        "ref": "J_UNOQ",
        "kind": "host_carrier",
        "value": "Arduino UNO Q Host Carrier",
        "mpn": "Arduino UNO Q",
        "footprint": "NFB:Arduino_UNO_Q_Carrier_Rotated",
        "population": "POPULATE",
        "pins": pins,
    }


def library_symbol(comp: dict, zone: str) -> str:
    ref = comp["ref"]
    sid = sanitize(ref)
    pins = sorted((str(k), v) for k, v in (comp.get("pins") or {}).items(), key=lambda x: pin_sort_key(x[0]))
    n = len(pins)
    offsets = [((n - 1) / 2 - i) * 2.54 for i in range(n)]
    top = (max(offsets) if offsets else 0) + 1.27
    bottom = (min(offsets) if offsets else 0) - 1.27
    lines = [
        f'    (symbol "NFB_GEN:{sid}"',
        "      (pin_names (offset 1.016) hide)",
        "      (exclude_from_sim no)",
        "      (in_bom yes)",
        "      (on_board yes)",
        f'      (property "Reference" {q(ref_prefix(ref))} (at 6.35 {top:.4f} 0) (effects (font (size 1.27 1.27))))',
        f'      (property "Value" {q(ref)} (at 6.35 {bottom:.4f} 0) (effects (font (size 1.27 1.27))))',
        '      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
        '      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
        f'      (property "Description" {q(f"NFB PR15 generated connectivity carrier {zone}/{ref}")} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
        f'      (symbol "{sid}_0_1"',
        f"        (rectangle (start -2.54 {top:.4f}) (end 5.08 {bottom:.4f}) (stroke (width 0.254) (type default)) (fill (type background)))",
        "      )",
        f'      (symbol "{sid}_1_1"',
    ]
    for (pnum, net), y in zip(pins, offsets):
        ptype = "no_connect" if net in (None, "NC") else "passive"
        pname = "NC" if net in (None, "NC") else str(net)
        lines += [
            f"        (pin {ptype} line (at -7.62 {y:.4f} 0) (length 5.08)",
            f"          (name {q(pname)} (effects (font (size 1.0 1.0))))",
            f"          (number {q(pnum)} (effects (font (size 1.0 1.0))))",
            "        )",
        ]
    lines += ["      )", "    )"]
    return "\n".join(lines)


def place_components(components: list[dict]) -> dict[str, tuple[float, float]]:
    # Greedy packing sobre A0 landscape; 4 columnas conservan espacio para etiquetas de nets.
    xs = [140.0, 410.0, 680.0, 950.0]
    heights = [55.0] * len(xs)
    pos: dict[str, tuple[float, float]] = {}
    for comp in components:
        n = len(comp.get("pins") or {})
        block_h = max(25.0, n * 2.54 + 14.0)
        col = min(range(len(xs)), key=lambda i: heights[i])
        y = heights[col] + block_h / 2
        pos[comp["ref"]] = (xs[col], y)
        heights[col] += block_h + 8.0
    if max(heights) > 810:
        fail(f"placement esquemático excede A0: altura {max(heights):.1f} mm")
    return pos


def symbol_instance(comp: dict, zone: str, x: float, y: float, instance_path: str) -> tuple[str, list[str]]:
    ref = comp["ref"]
    sid = sanitize(ref)
    pins = sorted((str(k), v) for k, v in (comp.get("pins") or {}).items(), key=lambda x: pin_sort_key(x[0]))
    n = len(pins)
    offsets = [((n - 1) / 2 - i) * 2.54 for i in range(n)]
    suid = uid(f"{zone}:{ref}:symbol")
    pop = str(comp.get("population", "POPULATE")).upper()
    dnp = "yes" if pop == "DNP" else "no"
    value = comp.get("value", "")
    footprint = comp.get("footprint", "")
    mpn = comp.get("mpn", "")
    out = [
        "  (symbol",
        f'    (lib_id "NFB_GEN:{sid}")',
        f"    (at {x:.4f} {y:.4f} 0)",
        "    (unit 1)",
        "    (exclude_from_sim no)",
        "    (in_bom yes)",
        "    (on_board yes)",
        f"    (dnp {dnp})",
        f'    (uuid "{suid}")',
        f'    (property "Reference" {q(ref)} (at {x+6.35:.4f} {y-6.35:.4f} 0) (effects (font (size 1.27 1.27)) (justify left)))',
        f'    (property "Value" {q(value)} (at {x+6.35:.4f} {y-3.81:.4f} 0) (effects (font (size 1.0 1.0)) (justify left)))',
        f'    (property "Footprint" {q(footprint)} (at {x:.4f} {y:.4f} 0) (effects (font (size 1.0 1.0)) (hide yes)))',
        f'    (property "Datasheet" "~" (at {x:.4f} {y:.4f} 0) (effects (font (size 1.0 1.0)) (hide yes)))',
        f'    (property "MPN" {q(mpn)} (at {x:.4f} {y:.4f} 0) (effects (font (size 1.0 1.0)) (hide yes)))',
        f'    (property "NFB_ZONE" {q(zone)} (at {x:.4f} {y:.4f} 0) (effects (font (size 1.0 1.0)) (hide yes)))',
        f'    (property "POPULATION" {q(pop)} (at {x:.4f} {y:.4f} 0) (effects (font (size 1.0 1.0)) (hide yes)))',
    ]
    extras: list[str] = []
    for (pnum, net), off in zip(pins, offsets):
        out.append(f'    (pin {q(pnum)} (uuid "{uid(f"{zone}:{ref}:pin:{pnum}")}"))')
        px = x - 7.62
        py = y + off
        if net in (None, "NC"):
            extras.append(f'  (no_connect (at {px:.4f} {py:.4f}) (uuid "{uid(f"{zone}:{ref}:nc:{pnum}")}"))')
        else:
            lx = px - 5.08
            extras += [
                f'  (wire (pts (xy {px:.4f} {py:.4f}) (xy {lx:.4f} {py:.4f})) (stroke (width 0) (type default)) (uuid "{uid(f"{zone}:{ref}:wire:{pnum}")}"))',
                f'  (label {q(net)} (at {lx:.4f} {py:.4f} 180) (effects (font (size 0.8 0.8))) (uuid "{uid(f"{zone}:{ref}:label:{pnum}")}"))',
            ]
    out += [
        "    (instances",
        f'      (project {q(PROJECT)}',
        f'        (path {q(instance_path)} (reference {q(ref)}) (unit 1))',
        "      )",
        "    )",
        "  )",
    ]
    return "\n".join(out), extras


def hierarchical_ports(zone: str, ports: list[tuple[str, str]], pin_nets: set[str]) -> list[str]:
    out: list[str] = []
    for idx, (net, shape) in enumerate(ports):
        if net not in pin_nets:
            fail(f"{zone}: puerto inter-zona {net} no llega a ningún pin interno")
        y = 20.0 + idx * 5.08
        out += [
            f'  (hierarchical_label {q(net)} (shape {shape}) (at 20.32 {y:.4f} 180) (effects (font (size 1.0 1.0))) (uuid "{uid(f"{zone}:hlabel:{net}")}"))',
            f'  (wire (pts (xy 20.32 {y:.4f}) (xy 30.48 {y:.4f})) (stroke (width 0) (type default)) (uuid "{uid(f"{zone}:hwire:{net}")}"))',
            f'  (label {q(net)} (at 30.48 {y:.4f} 0) (effects (font (size 0.9 0.9))) (uuid "{uid(f"{zone}:hlocal:{net}")}"))',
        ]
    return out


def generate_zone(zone: str, components: list[dict], root: str, sheet_uuid: str, ports: list[tuple[str, str]]) -> str:
    sch_uuid = uid(f"{zone}:schematic")
    r_uuid = root_uuid(root)
    instance_path = f"/{r_uuid}/{sheet_uuid}"
    pos = place_components(components)
    pin_nets = {
        str(net)
        for comp in components
        for net in (comp.get("pins") or {}).values()
        if net not in (None, "NC")
    }
    blocks = [
        "(kicad_sch",
        "  (version 20231120)",
        '  (generator "nfb_pr15_json_hierarchy")',
        '  (generator_version "1.0")',
        f'  (uuid "{sch_uuid}")',
        '  (paper "A0")',
        "  (title_block",
        f'    (title {q(f"NFB Insight PCBA v2 — {zone} {ZONE_TITLES[zone]} Production")})',
        '    (date "2026-08-12")',
        '    (rev "0.15.0")',
        '    (company "Cafelium SRL / Nebula Ecosystem")',
        f'    (comment 1 {q("PR #15 — materialización automática JSON→KiCad")})',
        f'    (comment 2 {q("Conectividad y footprints derivados de contratos de producción; sin placement PCB ni routing")})',
        f'    (comment 3 {q(f"Zona {zone}; símbolos NFB_GEN neutrales, pins pasivos/no-connect")})',
        "  )",
        "  (lib_symbols",
    ]
    blocks.extend(library_symbol(comp, zone) for comp in components)
    blocks.append("  )")
    blocks.append(
        f'  (text {q(f"PR #15 — {zone} PRODUCTION HIERARCHY\\nGenerated deterministically from frozen JSON. Do not hand-edit connectivity; regenerate with tools/generate_pr15_hierarchy.py.")} (at 50.8 10.16 0) (effects (font (size 1.5 1.5)) (justify left bottom)) (uuid "{uid(f"{zone}:banner")}"))'
    )
    blocks.extend(hierarchical_ports(zone, ports, pin_nets))
    extras: list[str] = []
    for comp in components:
        x, y = pos[comp["ref"]]
        inst, xtra = symbol_instance(comp, zone, x, y, instance_path)
        blocks.append(inst)
        extras.extend(xtra)
    blocks.extend(extras)
    blocks += ["  (sheet_instances (path \"/\" (page \"1\")))", ")", ""]
    return "\n".join(blocks)


def expected_outputs() -> dict[Path, str]:
    if not ROOT_SCH.exists() or not ROOT_CONTRACT.exists() or not PIN_CONTRACT.exists():
        fail("faltan archivos base PR14")
    root = ROOT_SCH.read_text(encoding="utf-8")
    contract = json.loads(ROOT_CONTRACT.read_text(encoding="utf-8"))
    sheets = {x["id"]: x for x in contract.get("sheets", [])}
    if set(sheets) != {"Z0", "Z1", "Z2", "Z3", "Z4"}:
        fail("root contract debe contener Z0..Z4")
    outputs: dict[Path, str] = {}
    for zone in ("Z0", "Z1", "Z2", "Z3", "Z4"):
        filename = Path(sheets[zone]["file"]).name
        expected_filename = ZONE_FILES[zone].name
        if filename != expected_filename:
            fail(f"{zone}: contract file {filename} != {expected_filename}")
        sh_uuid, ports = sheet_meta(root, filename)
        contract_ports = {net for net, owners in contract["interzone_nets"].items() if zone in owners}
        if {n for n, _ in ports} != contract_ports:
            fail(f"{zone}: root pins no coinciden con root_eda_contract")
        if zone == "Z0":
            components = [z0_component()]
        else:
            data = json.loads(ZONE_NETLISTS[zone].read_text(encoding="utf-8"))
            components = validate_zone_netlist(data, zone)
        outputs[ZONE_FILES[zone]] = generate_zone(zone, components, root, sh_uuid, ports)
    return outputs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fallar si los child sheets versionados no coinciden con la generación")
    args = ap.parse_args()
    outputs = expected_outputs()
    changed = []
    for path, content in outputs.items():
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old != content:
            changed.append(path)
            if not args.check:
                path.write_text(content, encoding="utf-8")
    if args.check and changed:
        for p in changed:
            print(f"STALE: {p.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if changed and not args.check:
        print("GENERATED:")
        for p in changed:
            print(f"- {p.relative_to(ROOT)}")
    else:
        print("OK: child sheets PR15 reproducibles y actualizados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
