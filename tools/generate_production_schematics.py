#!/usr/bin/env python3
"""Genera las hojas KiCad Z0-Z4 desde contratos JSON/BOM de producción.

PR #15 elimina la transcripción manual de conectividad. Los JSON/BOM siguen
siendo las fuentes de verdad eléctricas; las hojas KiCad son una representación
EDA determinista y regenerable. Los símbolos internos son cajas genéricas NFB
ancladas a ref/value/MPN/footprint/pines reales. La dirección funcional se
conserva en los hierarchical labels de frontera; los pines internos se modelan
passive para que el dibujo genérico no invente semántica eléctrica de silicio.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KICAD = ROOT / "kicad"
ROOT_SCH = KICAD / "NFB_Insight_PCBA_v2.kicad_sch"
ROOT_CONTRACT = ROOT / "hardware" / "root_eda_contract.json"
PIN_CONTRACT = ROOT / "hardware" / "insight_pin_contract.json"
NAMESPACE = uuid.UUID("5d997f1b-94fd-49b9-82aa-1f151dea0015")
PROJECT = "NFB_Insight_PCBA_v2"
PIN_LEN = 2.54
BODY_HALF_W = 7.62
PIN_X = BODY_HALF_W + PIN_LEN
PIN_SPACING = 2.54

ZONE_CONFIG = {
    "Z1": (ROOT / "hardware/z1_production_netlist.json", ROOT / "bom/insight_z1_production_bom.csv", "z1_interface.kicad_sch"),
    "Z2": (ROOT / "hardware/z2_production_netlist.json", ROOT / "bom/insight_z2_production_bom.csv", "z2_interface.kicad_sch"),
    "Z3": (ROOT / "hardware/power_production_netlist.json", ROOT / "bom/insight_power_production_bom.csv", "z3_interface.kicad_sch"),
    "Z4": (ROOT / "hardware/z4_production_netlist.json", ROOT / "bom/insight_z4_production_bom.csv", "z4_interface.kicad_sch"),
}
OUTPUT_FILES = {
    "Z0": "uno_q_interface.kicad_sch", "Z1": "z1_interface.kicad_sch",
    "Z2": "z2_interface.kicad_sch", "Z3": "z3_interface.kicad_sch",
    "Z4": "z4_interface.kicad_sch",
}
HIER_DIRECTIONS = {
    "Z0": {"UNO_IOREF_3V3":"output","12V_HOST_VIN":"input","MCU_NRST":"input","PH_ADC":"input","ORP_ADC":"input","TEMP_1WIRE":"bidirectional","PUMP_CURRENT_ADC":"input","DO_ADC":"input","HMI_RX":"input","HMI_TX":"output","HX711_DOUT":"input","HX711_SCK":"output","MCU_WDI":"output","PUMP_PWM":"output","PUMP_DIR":"output","CO2_SOL_CTL":"output","CHILLER_CTL":"output","ACT_FAULT_N":"input","LED_STATUS":"output","I2C_SDA":"bidirectional","I2C_SCL":"bidirectional","GND":"bidirectional"},
    "Z1": {"5V_RAIL":"input","3V3_RAIL":"input","GND":"bidirectional","PH_ADC":"output","ORP_ADC":"output","TEMP_1WIRE":"bidirectional","DO_ADC":"output","I2C_SDA":"bidirectional","I2C_SCL":"bidirectional"},
    "Z2": {"5V_RAIL":"input","3V3_RAIL":"input","GND":"bidirectional","HMI_RX":"output","HMI_TX":"input","HX711_DOUT":"output","HX711_SCK":"input","MCU_WDI":"input","MCU_NRST":"output","LED_STATUS":"input","I2C_SDA":"bidirectional","I2C_SCL":"bidirectional"},
    "Z3": {"UNO_IOREF_3V3":"input","GND":"bidirectional","12V_HOST_VIN":"output","12V_ACT":"output","5V_RAIL":"output","3V3_RAIL":"output"},
    "Z4": {"12V_ACT":"input","3V3_RAIL":"input","GND":"bidirectional","PUMP_PWM":"input","PUMP_DIR":"input","PUMP_CURRENT_ADC":"output","CO2_SOL_CTL":"input","CHILLER_CTL":"input","ACT_FAULT_N":"output"},
}


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def duid(name: str) -> str:
    return str(uuid.uuid5(NAMESPACE, name))


def esc(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def num(v: float) -> str:
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s not in {"", "-0"} else "0"


def pin_key(value: object):
    s = str(value)
    return (0, int(s)) if s.isdigit() else (1, s)


def balanced_blocks(text: str, marker: str):
    start = 0
    while True:
        i = text.find(marker, start)
        if i < 0:
            return
        depth = 0
        in_string = False
        escaped = False
        for j in range(i, len(text)):
            ch = text[j]
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
                    yield text[i:j + 1]
                    start = j + 1
                    break
        else:
            fail(f"bloque no balanceado: {marker}")


def root_paths() -> tuple[str, dict[str, str]]:
    text = ROOT_SCH.read_text(encoding="utf-8")
    m = re.search(r'^\s*\(uuid "([^"]+)"\)', text, flags=re.MULTILINE)
    if not m:
        fail("root sin UUID")
    root_uuid = m.group(1)
    sheets: dict[str, str] = {}
    for block in balanced_blocks(text, "(sheet\n"):
        fm = re.search(r'\(property "Sheetfile" "([^"]+)"', block)
        um = re.search(r'\(uuid "([^"]+)"\)', block)
        if fm and um:
            sheets[fm.group(1)] = um.group(1)
    if set(sheets) != set(OUTPUT_FILES.values()):
        fail(f"sheet files root inesperados: {sheets}")
    return root_uuid, sheets


def validate_netlist(data: dict, zone: str) -> None:
    comps = {c["ref"]: c for c in data["components"]}
    nets = {n["name"]: set(n["nodes"]) for n in data["nets"]}
    for ref, comp in comps.items():
        if not comp.get("pins"):
            fail(f"{zone}/{ref} sin pins")
        for pin, net in comp["pins"].items():
            if net == "NC":
                continue
            if f"{ref}.{pin}" not in nets.get(net, set()):
                fail(f"{zone}: {ref}.{pin} no aparece en {net}")
    for net, nodes in nets.items():
        for node in nodes:
            ref = node.rsplit(".", 1)[0]
            if ref != "J_UNOQ" and ref not in comps:
                fail(f"{zone}: {net} referencia {ref} inexistente")


def validate_bom(data: dict, bom_path: Path, zone: str) -> None:
    comps = {c["ref"]: c for c in data["components"]}
    with bom_path.open(newline="", encoding="utf-8") as fh:
        by_ref = {r["ref"]: r for r in csv.DictReader(fh)}
    if set(by_ref) != set(comps):
        fail(f"{zone}: refs BOM != JSON")
    for ref, comp in comps.items():
        if by_ref[ref].get("footprint", "") != comp.get("footprint", ""):
            fail(f"{zone}/{ref}: footprint BOM != JSON")


def zone_interzone_nets(contract: dict, zone: str) -> list[str]:
    nets = [net for net, zones in contract["interzone_nets"].items() if zone in zones]
    if set(nets) != set(HIER_DIRECTIONS[zone]):
        fail(f"{zone}: direcciones jerárquicas no cubren ownership root")
    return nets


def z0_component() -> dict:
    data = json.loads(PIN_CONTRACT.read_text(encoding="utf-8"))
    if data.get("schema_version") != 6:
        fail("pin contract UNO Q no es schema6")
    pins = {}
    for item in sorted(data["pins"], key=lambda x: int(x["pad"])):
        net = item.get("net")
        if not net and str(item.get("arduino", "")).upper() == "GND":
            net = "GND"
        pins[str(item["pad"])] = net or "NC"
    return {"ref":"J_UNOQ","value":"Arduino UNO Q Host","mpn":"Arduino UNO Q","footprint":"NFB:Arduino_UNO_Q_Carrier_Rotated","population":"HOST_MODULE","pins":pins}


def pin_geometry(pin_numbers: list[str]):
    ordered = sorted(pin_numbers, key=pin_key)
    split = (len(ordered) + 1) // 2
    left, right = ordered[:split], ordered[split:]
    max_side = max(len(left), len(right), 1)
    half_h = max(5.08, ((max_side - 1) * PIN_SPACING) / 2 + 1.27)
    geo = {}
    for side, pins in (("L", left), ("R", right)):
        offset = (len(pins) - 1) / 2
        for idx, pin in enumerate(pins):
            py = (idx - offset) * PIN_SPACING
            geo[pin] = (-PIN_X, py, 0) if side == "L" else (PIN_X, py, 180)
    return geo, half_h


def lib_symbol(ref: str, pin_numbers: list[str]) -> str:
    name = "SYM_" + re.sub(r"[^A-Za-z0-9_]", "_", ref)
    geo, half_h = pin_geometry(pin_numbers)
    lines = [
        f'    (symbol "NFB_GEN:{name}" (pin_names (offset 0.635)) (in_bom yes) (on_board yes)',
        '      (property "Reference" "U" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))',
        '      (property "Value" "NFB_GENERATED" (at 0 0 0) (effects (font (size 1.27 1.27))))',
        '      (property "Footprint" "" (at 0 2.54 0) (effects (font (size 1.27 1.27)) (hide yes)))',
        '      (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))',
        f'      (symbol "{name}_0_1"',
        f'        (rectangle (start {num(-BODY_HALF_W)} {num(-half_h)}) (end {num(BODY_HALF_W)} {num(half_h)})',
        '          (stroke (width 0.254) (type default)) (fill (type background)))',
        '      )',
        f'      (symbol "{name}_1_1"',
    ]
    for pin in sorted(pin_numbers, key=pin_key):
        px, py, angle = geo[pin]
        lines.extend([
            f'        (pin passive line (at {num(px)} {num(py)} {angle}) (length {num(PIN_LEN)})',
            f'          (name "{esc(pin)}" (effects (font (size 1 1))))',
            f'          (number "{esc(pin)}" (effects (font (size 1 1))))',
            '        )',
        ])
    lines.extend(['      )', '    )'])
    return "\n".join(lines)


def instance_symbol(comp: dict, x: float, y: float, sheet_path: str):
    ref = str(comp["ref"])
    name = "SYM_" + re.sub(r"[^A-Za-z0-9_]", "_", ref)
    pin_numbers = [str(p) for p in comp["pins"]]
    geo, _ = pin_geometry(pin_numbers)
    in_bom = "no" if str(comp.get("population", "")).startswith("PCB_FEATURE") else "yes"
    dnp = "yes" if str(comp.get("population", "")).startswith("DNP") else "no"
    lines = [
        f'  (symbol (lib_id "NFB_GEN:{name}") (at {num(x)} {num(y)} 0) (unit 1)',
        f'    (exclude_from_sim yes) (in_bom {in_bom}) (on_board yes) (dnp {dnp})',
        f'    (uuid "{duid("instance:" + sheet_path + ":" + ref)}")',
        f'    (property "Reference" "{esc(ref)}" (at {num(x)} {num(y-2.54)} 0) (effects (font (size 1 1))))',
        f'    (property "Value" "{esc(comp.get("value", ""))}" (at {num(x)} {num(y)} 0) (effects (font (size 0.9 0.9))))',
        f'    (property "Footprint" "{esc(comp.get("footprint", ""))}" (at {num(x)} {num(y+2.54)} 0) (effects (font (size 0.8 0.8)) (hide yes)))',
        f'    (property "Datasheet" "~" (at {num(x)} {num(y)} 0) (effects (font (size 0.8 0.8)) (hide yes)))',
        f'    (property "MPN" "{esc(comp.get("mpn", ""))}" (at {num(x)} {num(y+5.08)} 0) (effects (font (size 0.8 0.8)) (hide yes)))',
    ]
    abs_pins = {}
    for pin in sorted(pin_numbers, key=pin_key):
        pin_uuid = duid("pin:" + sheet_path + ":" + ref + ":" + pin)
        lines.append(f'    (pin "{esc(pin)}" (uuid "{pin_uuid}"))')
        px, py, _ = geo[pin]
        abs_pins[pin] = (x + px, y + py)
    lines.extend([
        f'    (instances (project "{PROJECT}" (path "{sheet_path}" (reference "{esc(ref)}") (unit 1))))',
        '  )',
    ])
    return "\n".join(lines), abs_pins


def global_label(net: str, x: float, y: float, key: str) -> str:
    uid = duid("global:" + key)
    return (f'  (global_label "{esc(net)}" (shape input) (at {num(x)} {num(y)} 0)\n'
            f'    (effects (font (size 0.9 0.9)) (justify left))\n'
            f'    (uuid "{uid}"))')


def render_zone(zone: str, components: list[dict], source_name: str, root_uuid: str, sheet_uuid: str, contract: dict) -> str:
    child_uuid = duid("child-root:" + zone)
    sheet_path = f"/{root_uuid}/{sheet_uuid}"
    parts = [
        '(kicad_sch', '  (version 20250114)', '  (generator "nfb_pr15_production_generator")',
        '  (generator_version "1.0")', f'  (uuid "{child_uuid}")', '  (paper "A3")',
        f'  (title_block (title "NFB Insight PCBA v2 — {zone} GENERATED PRODUCTION")',
        '    (date "2026-08-12") (rev "0.15.0") (company "Cafelium SRL / Nebula Ecosystem")',
        '    (comment 1 "GENERATED by tools/generate_production_schematics.py — DO NOT EDIT")',
        f'    (comment 2 "Source: {esc(source_name)}")', '    (comment 3 "PR #15 — no placement / no routing"))',
        '  (lib_symbols',
    ]
    for comp in components:
        parts.append(lib_symbol(str(comp["ref"]), [str(p) for p in comp["pins"]]))
    parts.append('  )')
    iy = 20.32
    for net in zone_interzone_nets(contract, zone):
        direction = HIER_DIRECTIONS[zone][net]
        parts.extend([
            f'  (hierarchical_label "{esc(net)}" (shape {direction}) (at 10.16 {num(iy)} 0)',
            '    (effects (font (size 1 1)) (justify left))',
            f'    (uuid "{duid("hier:" + zone + ":" + net)}"))',
            f'  (wire (pts (xy 10.16 {num(iy)}) (xy 15.24 {num(iy)})) (stroke (width 0) (type default)) (uuid "{duid("hier-wire:" + zone + ":" + net)}"))',
            global_label(net, 15.24, iy, "hier:" + zone + ":" + net),
        ])
        iy += 5.08
    xs = [55.88, 114.3, 172.72, 231.14, 289.56, 347.98]
    ys = [35.56, 81.28, 127.0, 172.72, 218.44, 264.16]
    for idx, comp in enumerate(components):
        col, row = idx % len(xs), idx // len(xs)
        x = xs[col]
        y = ys[row] if row < len(ys) else 35.56 + row * 45.72
        block, abs_pins = instance_symbol(comp, x, y, sheet_path)
        parts.append(block)
        for pin in sorted(comp["pins"], key=pin_key):
            pin_s = str(pin)
            net = comp["pins"][pin]
            px, py = abs_pins[pin_s]
            if net == "NC":
                uid = duid("nc:" + zone + ":" + str(comp["ref"]) + ":" + pin_s)
                parts.append(f'  (no_connect (at {num(px)} {num(py)}) (uuid "{uid}"))')
            else:
                key = "pin:" + zone + ":" + str(comp["ref"]) + ":" + pin_s + ":" + str(net)
                parts.append(global_label(str(net), px, py, key))
    marker_uuid = duid("marker:" + zone)
    page = 2 + ["Z0","Z1","Z2","Z3","Z4"].index(zone)
    parts.extend([
        f'  (text "PR #15 GENERATED | zone={zone} | refs={len(components)} | JSON/BOM authoritative" (exclude_from_sim no) (at 20.32 289.56 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{marker_uuid}"))',
        f'  (sheet_instances (path "{sheet_path}" (page "{page}")))', ')',
    ])
    return "\n".join(parts) + "\n"


def load_all():
    contract = json.loads(ROOT_CONTRACT.read_text(encoding="utf-8"))
    zones = {"Z0": [z0_component()]}
    for zone, (net_path, bom_path, _filename) in ZONE_CONFIG.items():
        data = json.loads(net_path.read_text(encoding="utf-8"))
        validate_netlist(data, zone)
        validate_bom(data, bom_path, zone)
        zones[zone] = data["components"]
    return contract, zones


def rendered_outputs() -> dict[Path, str]:
    contract, zones = load_all()
    root_uuid, sheet_uuids = root_paths()
    rendered = {}
    for zone, filename in OUTPUT_FILES.items():
        if filename not in sheet_uuids:
            fail(f"root no contiene {filename}")
        source = "hardware/insight_pin_contract.json" if zone == "Z0" else str(ZONE_CONFIG[zone][0].relative_to(ROOT))
        rendered[KICAD / filename] = render_zone(zone, zones[zone], source, root_uuid, sheet_uuids[filename], contract)
    return rendered


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--output-dir", type=Path, default=None)
    args = ap.parse_args()
    stale = []
    for original, text in rendered_outputs().items():
        target = args.output_dir / original.name if args.output_dir else original
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                stale.append(str(target))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            print(f"wrote {target}")
    if stale:
        fail("generated schematics out of date: " + ", ".join(stale))
    if args.check:
        print("OK: production schematics reproduce byte-for-byte from JSON/BOM")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
