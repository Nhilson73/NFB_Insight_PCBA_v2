#!/usr/bin/env python3
"""Valida el contrato de interfaces reales de sensores definido en PR #5."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "hardware" / "sensor_interface_contract.json"
PIN_CONTRACT = ROOT / "hardware" / "insight_pin_contract.json"
BOM = ROOT / "bom" / "insight_sensor_interface_bom.csv"
DOC = ROOT / "docs" / "FASE2_PR5_SENSOR_INTERFACES.md"

EXPECTED = {
    "PH": (9, "PH_ADC", "CONDITIONED_ANALOG"),
    "ORP": (10, "ORP_ADC", "CONDITIONED_ANALOG_SCALED"),
    "TEMP": (11, "TEMP_1WIRE", "DIGITAL_1WIRE"),
    "CO2": (13, "CO2_ADC", "CONDITIONED_ANALOG_SCALED_SENSOR_TBD"),
    "DO": (14, "DO_ADC", "CONDITIONED_ANALOG"),
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def almost(a: float, b: float, tol: float = 1e-6) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def divider_ratio(top: float, bottom: float) -> float:
    return bottom / (top + bottom)


def main() -> int:
    for path in (CONTRACT, PIN_CONTRACT, BOM, DOC):
        if not path.exists():
            fail(f"falta archivo requerido: {path.relative_to(ROOT)}")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if data.get("status") != "PRODUCTION_INTERFACE_BASELINE_PR5":
        fail("status de sensor_interface_contract no es baseline PR5")

    adc_domain = float(data["uno_q"]["analog_domain_v"])
    target_max = float(data["uno_q"]["external_analog_design_target_max_v"])
    if not almost(adc_domain, 3.3):
        fail(f"dominio analógico UNO Q inesperado: {adc_domain}")
    if not (0 < target_max < adc_domain):
        fail("objetivo máximo externo debe quedar por debajo del dominio ADC")

    mech = data.get("mechanical_policy", {})
    if mech.get("field_io_edge") != "Y=0" or mech.get("connector_facing") != "-Y":
        fail("contrato de sensores viola FIELD I/O EDGE Y=0 / -Y")
    if mech.get("bypass_raw_probe_bnc_on_pcba") is not True:
        fail("PR5 debe prohibir BNC de electrodo crudo en PCBA base")

    channels = {c["id"]: c for c in data.get("channels", [])}
    if set(channels) != set(EXPECTED):
        fail(f"canales incorrectos: {sorted(channels)}")

    for name, (pad, net, interface_class) in EXPECTED.items():
        c = channels[name]
        if int(c["uno_q_pad"]) != pad or c["net"] != net or c["interface_class"] != interface_class:
            fail(f"{name}: contrato esperado {pad}/{net}/{interface_class}")
        if "BNC" in c.get("production_connector", "").upper():
            fail(f"{name}: BNC no puede ser production_connector de PCBA")

    for name in ("PH", "DO"):
        c = channels[name]
        vmax = float(c["scaling"]["max_to_uno_q_v"])
        if c["scaling"].get("required") is not False:
            fail(f"{name}: no debe necesitar divisor con salida 0-3 V")
        if vmax > target_max:
            fail(f"{name}: {vmax:.4f} V supera objetivo {target_max:.4f} V")

    ph = channels["PH"]
    if ph.get("preferred_continuous_sensor") != "SEN0169-V2":
        fail("pH debe documentar SEN0169-V2 como opción preferida para operación continua")

    orp = channels["ORP"]["scaling"]
    orp_k = divider_ratio(float(orp["top_ohm"]), float(orp["bottom_ohm"]))
    orp_v = float(orp["input_max_v"]) * orp_k
    if not almost(orp_k, float(orp["ratio"]), 1e-5):
        fail("ORP: ratio documentado no coincide con resistencias")
    if not almost(orp_v, float(orp["max_to_uno_q_v"]), 1e-5):
        fail("ORP: Vadc documentado no coincide con divisor")
    if orp_v > target_max:
        fail(f"ORP: {orp_v:.4f} V supera objetivo {target_max:.4f} V")
    if not almost(float(orp["firmware_inverse_gain"]), 1.0 / orp_k, 1e-5):
        fail("ORP: firmware_inverse_gain no invierte el divisor")

    temp = channels["TEMP"]
    if temp.get("sensor") != "DS18B20" or temp.get("analog") is not False:
        fail("TEMP debe ser DS18B20 digital")
    if float(temp["logic_domain_v"]) != 3.3:
        fail("TEMP_1WIRE debe usar lógica/pull-up de 3.3 V")
    if temp.get("firmware_migration_required") is not True:
        fail("debe quedar registrada la migración pendiente de firmware para DS18B20")

    co2 = channels["CO2"]
    if co2.get("legacy_sensor_lifecycle") != "REPLACE_BEFORE_FAB":
        fail("MPX5700AP debe quedar bloqueado para reemplazo antes de fabricación")
    co2s = co2["scaling_for_legacy_validation_only"]
    co2_k = divider_ratio(float(co2s["top_ohm"]), float(co2s["bottom_ohm"]))
    co2_v = float(co2s["input_max_v"]) * co2_k
    if not almost(co2_k, float(co2s["ratio"]), 1e-5):
        fail("CO2: ratio legacy documentado no coincide con resistencias")
    if not almost(co2_v, float(co2s["max_to_uno_q_v"]), 1e-5):
        fail("CO2: Vadc legacy documentado no coincide con divisor")
    if co2_v > target_max:
        fail(f"CO2 legacy: {co2_v:.4f} V supera objetivo {target_max:.4f} V")

    for name in ("PH", "ORP", "DO"):
        iso = channels[name].get("isolation", {})
        if iso.get("pcb_placement") is not False:
            fail(f"{name}: aislamiento inline no puede aparecer como placement base")
        if "DFR0504" not in iso.get("system_strategy", ""):
            fail(f"{name}: falta estrategia de aislamiento inline")
        if iso.get("onboard_legacy_chain") != "DO_NOT_POPULATE_AS_BASELINE":
            fail(f"{name}: cadena legacy no está explícitamente descartada del baseline")

    pin_data = json.loads(PIN_CONTRACT.read_text(encoding="utf-8"))
    by_pad = {int(p["pad"]): p for p in pin_data["pins"]}
    for name, (pad, net, _) in EXPECTED.items():
        if by_pad[pad].get("net") != net:
            fail(f"{name}: net {net} no coincide con insight_pin_contract.json")

    with BOM.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if {r["canal"] for r in rows} != set(EXPECTED):
        fail("BOM PR5 no cubre exactamente cinco canales")
    if any("BNC" in r.get("valor_objetivo", "").upper() for r in rows):
        fail("BOM PR5 contiene BNC de PCBA")
    if any(r.get("mpn") in {"SN6501DBVR", "AMC1301DWVR", "750315371"} for r in rows):
        fail("BOM PR5 contiene aislamiento legacy onboard")

    doc = DOC.read_text(encoding="utf-8")
    for marker in ("TEMP_1WIRE", "10.0 kΩ", "20.0 kΩ", "18.0 kΩ", "30.0 kΩ", "REPLACE_BEFORE_FAB", "DFR0504"):
        if marker not in doc:
            fail(f"documentación PR5 no contiene marcador: {marker}")

    print("OK: contrato de interfaces de sensores PR #5 verificado")
    print(f"- dominio ADC UNO Q: {adc_domain:.2f} V; objetivo externo: <= {target_max:.2f} V")
    print(f"- ORP worst-case después del divisor: {orp_v:.3f} V")
    print(f"- CO2/MPX5700 legacy worst-case después del divisor: {co2_v:.3f} V")
    print("- PH y DO acondicionados: <= 3.000 V")
    print("- A2/D16: DS18B20 digital TEMP_1WIRE")
    print("- BNC y aislamiento de electrodo crudo fuera del placement base")
    print("- MPX5700AP: REPLACE_BEFORE_FAB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
