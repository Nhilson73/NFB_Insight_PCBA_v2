#!/usr/bin/env python3
"""Valida que la herencia PR4 permanezca trazable sin imponerse sobre el contrato PR5."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DONOR_MANIFEST = ROOT / "hardware" / "analog_insight_manifest.json"
SENSOR_CONTRACT = ROOT / "hardware" / "sensor_interface_contract.json"
PIN_CONTRACT = ROOT / "hardware" / "insight_pin_contract.json"
DONOR_BOM = ROOT / "bom" / "insight_analog_inheritance.csv"
PROD_BOM = ROOT / "bom" / "insight_sensor_interface_bom.csv"
SCH = ROOT / "kicad" / "analog_insight.kicad_sch"

EXPECTED_CHANNELS = {"PH", "ORP", "TEMP", "CO2", "DO"}
LEGACY_ISOLATION_MPNS = {"SN6501DBVR", "AMC1301DWVR", "750315371", "BAT54,115"}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    for path in (DONOR_MANIFEST, SENSOR_CONTRACT, PIN_CONTRACT, DONOR_BOM, PROD_BOM, SCH):
        if not path.exists():
            fail(f"falta archivo requerido: {path.relative_to(ROOT)}")

    donor = json.loads(DONOR_MANIFEST.read_text(encoding="utf-8"))
    production = json.loads(SENSOR_CONTRACT.read_text(encoding="utf-8"))
    pins = json.loads(PIN_CONTRACT.read_text(encoding="utf-8"))

    donor_channels = {c["id"] for c in donor.get("channels", [])}
    if donor_channels != EXPECTED_CHANNELS:
        fail(f"trazabilidad PR4 perdió canales: {sorted(donor_channels)}")

    exclusions = donor.get("explicitly_not_inherited", [])
    if len(exclusions) != 1 or exclusions[0].get("arduino") != "A3":
        fail("PR4 debe conservar A3/HUM como exclusión explícita")
    if set(exclusions[0].get("donor_refs", [])) != {"J7", "D8", "R17", "R18", "C23"}:
        fail("lista de refs HUM descartadas cambió")

    if production.get("status") != "PRODUCTION_INTERFACE_BASELINE_PR5":
        fail("sensor_interface_contract.json no está marcado como baseline PR5")
    supersedes = production.get("supersedes_for_production", {})
    if supersedes.get("artifact") != "hardware/analog_insight_manifest.json":
        fail("PR5 debe declarar explícitamente que supersede la topología PR4 para producción")

    prod_channels = {c["id"]: c for c in production.get("channels", [])}
    if set(prod_channels) != EXPECTED_CHANNELS:
        fail(f"baseline PR5 contiene canales inesperados: {sorted(prod_channels)}")

    if prod_channels["TEMP"].get("net") != "TEMP_1WIRE":
        fail("TEMP debe migrar a TEMP_1WIRE")
    if prod_channels["TEMP"].get("interface_class") != "DIGITAL_1WIRE":
        fail("TEMP no está clasificado como 1-Wire digital")

    pin_by_pad = {int(p["pad"]): p for p in pins.get("pins", [])}
    if pin_by_pad[11].get("net") != "TEMP_1WIRE":
        fail("insight_pin_contract.json no refleja TEMP_1WIRE en pad 11")

    donor_rows = read_csv(DONOR_BOM)
    if not donor_rows:
        fail("BOM de herencia PR4 vacía")
    if {row["canal"] for row in donor_rows} != EXPECTED_CHANNELS:
        fail("BOM donante perdió trazabilidad de canales")

    prod_rows = read_csv(PROD_BOM)
    if not prod_rows:
        fail("BOM de interfaces PR5 vacía")
    if {row["canal"] for row in prod_rows} != EXPECTED_CHANNELS:
        fail("BOM PR5 no contiene exactamente los cinco canales")

    # La cadena de aislamiento de electrodo crudo puede permanecer en el archivo histórico,
    # pero no puede reaparecer como placement de producción PR5.
    prod_mpns = {row.get("mpn", "") for row in prod_rows}
    legacy_overlap = LEGACY_ISOLATION_MPNS & prod_mpns
    if legacy_overlap:
        fail(f"BOM PR5 revive cadena de aislamiento legacy: {sorted(legacy_overlap)}")

    if any("BNC" in row.get("valor_objetivo", "").upper() for row in prod_rows):
        fail("BOM PR5 contiene BNC como placement de PCBA")

    schematic = SCH.read_text(encoding="utf-8")
    # La hoja PR4 se conserva tal cual como documentación del donante; no es netlist de producción.
    for marker in ("PH / A0", "ORP / A1", "CO2 / A4", "DO / A5", "A3 / HUM_ADC: NO MIGRAR"):
        if marker not in schematic:
            fail(f"hoja histórica PR4 perdió marcador: {marker}")

    print("OK: trazabilidad analógica PR4 compatible con baseline PR5")
    print("- PR4 conserva los cinco canales y exclusión HUM como historial")
    print("- sensor_interface_contract.json es la fuente de verdad de producción")
    print("- TEMP migra a TEMP_1WIRE")
    print("- cadena SN6501/AMC1301/transformador no aparece en BOM PR5")
    print("- no hay BNC como placement de la PCBA base")
    return 0


if __name__ == "__main__":
    sys.exit(main())
