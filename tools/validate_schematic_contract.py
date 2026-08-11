#!/usr/bin/env python3
"""Valida el contrato eléctrico Insight contra la mecánica UNO Q y PR #5."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "hardware" / "insight_pin_contract.json"
SENSOR_CONTRACT = ROOT / "hardware" / "sensor_interface_contract.json"
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
SCH = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_sch"

EXPECTED = {
    9: ("A0", "PH_ADC", "ACTIVE"),
    10: ("A1", "ORP_ADC", "ACTIVE"),
    11: ("A2/D16", "TEMP_1WIRE", "ACTIVE_DIGITAL"),
    12: ("A3", None, "DNP_RESERVE"),
    13: ("A4", "CO2_ADC", "ACTIVE"),
    14: ("A5", "DO_ADC", "ACTIVE"),
    17: ("D2", "HX711_DOUT", "ACTIVE"),
    18: ("D3", "HX711_SCK", "ACTIVE"),
    19: ("D4", "MCU_WDI", "ACTIVE"),
    20: ("D5", "PUMP_PWM", "ACTIVE"),
    21: ("D6", "PUMP_DIR", "ACTIVE"),
    22: ("D7", "CO2_SOL_CTL", "ACTIVE"),
    23: ("D8", "CHILLER_CTL", "ACTIVE_CONTROL_ONLY"),
    24: ("D9", None, "DNP_RESERVE"),
    25: ("D10", "RS485_IRQ_RSVD", "RESERVE"),
    31: ("D20/SDA", "I2C_SDA", "ACTIVE"),
    32: ("D21/SCL", "I2C_SCL", "ACTIVE"),
}

FIRMWARE_BASELINE = "cf100b38df890f61aed472e934241e145425569b"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def main() -> int:
    for path in (CONTRACT, SENSOR_CONTRACT, PCB, SCH):
        if not path.exists():
            fail(f"falta archivo requerido: {path.relative_to(ROOT)}")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    pins = data.get("pins", [])
    if len(pins) != 32:
        fail(f"el contrato debe contener 32 pads; encontrados {len(pins)}")

    by_pad = {int(item["pad"]): item for item in pins}
    if set(by_pad) != set(range(1, 33)):
        fail("el contrato no contiene exactamente los pads 1..32")

    if data.get("firmware_reference", {}).get("commit") != FIRMWARE_BASELINE:
        fail("el snapshot de firmware cambió sin actualizar el validador")

    if data.get("sensor_interface_source_of_truth") != "hardware/sensor_interface_contract.json":
        fail("falta declarar sensor_interface_contract.json como fuente de verdad")

    for pad, (arduino, net, status) in EXPECTED.items():
        item = by_pad[pad]
        actual = (item.get("arduino"), item.get("net"), item.get("status"))
        expected = (arduino, net, status)
        if actual != expected:
            fail(f"pad {pad}: esperado {expected}, actual {actual}")

    forbidden_active_nets = {"HUM_ADC", "CO2_PWM", "CO2_FLOW_PWM", "TEMP_ADC"}
    active_nets = {
        item["net"]
        for item in pins
        if item.get("net") and item.get("status", "").startswith("ACTIVE")
    }
    overlap = forbidden_active_nets & active_nets
    if overlap:
        fail(f"nets descartadas aparecen activas: {sorted(overlap)}")

    sensor_contract = json.loads(SENSOR_CONTRACT.read_text(encoding="utf-8"))
    sensor_by_pad = {int(c["uno_q_pad"]): c for c in sensor_contract.get("channels", [])}
    for pad in (9, 10, 11, 13, 14):
        if pad not in sensor_by_pad:
            fail(f"sensor_interface_contract no define el pad {pad}")
        if sensor_by_pad[pad]["net"] != by_pad[pad]["net"]:
            fail(f"pad {pad}: net de sensor no coincide con contrato de pines")

    temp = sensor_by_pad[11]
    if temp.get("interface_class") != "DIGITAL_1WIRE" or temp.get("analog") is not False:
        fail("A2/D16 debe ser interfaz digital DS18B20/1-Wire")

    pcb = PCB.read_text(encoding="utf-8")
    physical_pads = {
        int(n)
        for n in re.findall(r'\(pad \"([0-9]+)\" thru_hole', pcb)
    }
    missing = set(range(1, 33)) - physical_pads
    if missing:
        fail(f"faltan pads físicos UNO Q en PCB: {sorted(missing)}")

    sch = SCH.read_text(encoding="utf-8")
    required_markers = [
        "NFB Insight PCBA v2 — Contrato Eléctrico Base",
        "hardware/insight_pin_contract.json",
        "hardware/sensor_interface_contract.json",
        "TEMP_1WIRE",
        "A3 DNP",
        "D9 DNP",
    ]
    for marker in required_markers:
        if marker not in sch:
            fail(f"root schematic no contiene marcador contractual: {marker}")

    print("OK: contrato eléctrico Insight PR #5 verificado")
    print("- 32 pads UNO Q presentes y clasificados")
    print(f"- firmware baseline: {FIRMWARE_BASELINE}")
    print("- A2/D16 = TEMP_1WIRE; TEMP_ADC prohibido")
    print("- A3 y D9 permanecen DNP/Reserva")
    print("- D10 permanece reservado para expansión RS485/Signature")
    print("- contratos de pines y sensores son coherentes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
