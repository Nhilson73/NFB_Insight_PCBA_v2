#!/usr/bin/env python3
"""Valida la migración controlada del bloque analógico de Insight V2."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "hardware" / "analog_insight_manifest.json"
CONTRACT = ROOT / "hardware" / "insight_pin_contract.json"
BOM = ROOT / "bom" / "insight_analog_inheritance.csv"
SCH = ROOT / "kicad" / "analog_insight.kicad_sch"

EXPECTED = {
    "PH": ("A0", "PH_ADC", True),
    "ORP": ("A1", "ORP_ADC", True),
    "TEMP": ("A2", "TEMP_ADC", False),
    "CO2": ("A4", "CO2_ADC", False),
    "DO": ("A5", "DO_ADC", True),
}
REQUIRED_ISOLATION_SIGNATURE = {"SN6501DBVR", "AMC1301DWVR", "750315371", "BAT54,115"}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def main() -> int:
    for path in (MANIFEST, CONTRACT, BOM, SCH):
        if not path.exists():
            fail(f"falta archivo requerido: {path.relative_to(ROOT)}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    channels = {c["id"]: c for c in manifest["channels"]}
    if set(channels) != set(EXPECTED):
        fail(f"canales activos incorrectos: {sorted(channels)}")

    contract_by_arduino = {p["arduino"]: p for p in contract["pins"]}
    for channel, (arduino, net, isolated) in EXPECTED.items():
        item = channels[channel]
        if item["arduino"] != arduino or item["output_net"] != net:
            fail(f"{channel}: contrato analógico no coincide con {arduino}/{net}")
        if bool(item["isolated"]) != isolated:
            fail(f"{channel}: atributo isolated incorrecto")
        pin = contract_by_arduino.get(arduino)
        if not pin or pin.get("net") != net or not str(pin.get("status", "")).startswith("ACTIVE"):
            fail(f"{channel}: {arduino} no coincide con insight_pin_contract.json")

        connector = item["field_connector"]
        if connector.get("service_edge") != "Y=0" or connector.get("facing") != "-Y":
            fail(f"{channel}: conector no respeta FIELD I/O EDGE / -Y")

        mpns = {c.get("mpn") for c in item["donor_components"] if c.get("mpn")}
        if isolated and not REQUIRED_ISOLATION_SIGNATURE.issubset(mpns):
            missing = REQUIRED_ISOLATION_SIGNATURE - mpns
            fail(f"{channel}: cadena de aislamiento incompleta, faltan {sorted(missing)}")

    if set(manifest["design_policy"]["wet_sensor_isolation_channels"]) != {"PH", "ORP", "DO"}:
        fail("lista de canales aislados no es PH/ORP/DO")
    if set(manifest["design_policy"]["shared_ground_channels"]) != {"TEMP", "CO2"}:
        fail("lista de canales GND compartido no es TEMP/CO2")
    if set(manifest["design_policy"]["active_outputs"]) != {v[1] for v in EXPECTED.values()}:
        fail("active_outputs no coincide con los cinco canales Insight")
    if manifest["design_policy"].get("excluded_outputs") != ["HUM_ADC"]:
        fail("HUM_ADC debe quedar explícitamente excluido")

    exclusions = manifest.get("explicitly_not_inherited", [])
    if len(exclusions) != 1 or exclusions[0].get("arduino") != "A3":
        fail("A3/HUM debe existir solo como exclusión explícita")
    if set(exclusions[0].get("donor_refs", [])) != {"J7", "D8", "R17", "R18", "C23"}:
        fail("lista de refs HUM descartadas no coincide con el donante")

    with BOM.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        fail("BOM analógica vacía")
    bom_channels = {row["canal"] for row in rows}
    if bom_channels != set(EXPECTED):
        fail(f"BOM contiene canales inesperados: {sorted(bom_channels)}")
    if any(row["donor_ref"] in {"J7", "D8", "R17", "R18", "C23"} for row in rows):
        fail("BOM activa contiene referencias del canal HUM eliminado")
    if not any(row["disposicion"] == "REVIEW" for row in rows):
        fail("la BOM heredada debe conservar gates REVIEW")

    schematic = SCH.read_text(encoding="utf-8")
    for _, (arduino, net, _) in EXPECTED.items():
        if arduino not in schematic or net not in schematic:
            fail(f"hoja KiCad no documenta {arduino}/{net}")
    if "A3 / HUM_ADC: NO MIGRAR" not in schematic:
        fail("hoja KiCad no deja explícita la exclusión A3/HUM_ADC")
    if "Y=0" not in schematic or "-Y" not in schematic:
        fail("hoja KiCad no documenta orientación de conectores")

    print("OK: migración analógica Insight V2 verificada")
    print("- 5 canales activos alineados con el contrato PR #3")
    print("- PH/ORP/DO mantienen arquitectura de aislamiento heredada")
    print("- TEMP/CO2 permanecen en dominio GND compartido")
    print("- A3/HUM y refs J7/D8/R17/R18/C23 excluidos")
    print(f"- {len(rows)} filas de BOM analógica trazables al donante")
    print("- todos los conectores de campo obligados a Y=0 / -Y")
    return 0


if __name__ == "__main__":
    sys.exit(main())
