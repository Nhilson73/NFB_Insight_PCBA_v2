#!/usr/bin/env python3
"""Gate de cumplimiento europeo de diseño para NFB Insight PCBA v2 como shield UNO Q."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "compliance" / "eu_compliance_contract.json"
MATRIX = ROOT / "compliance" / "EU_COMPLIANCE_MATRIX.csv"
DOC = ROOT / "docs" / "EU_COMPLIANCE_GATE.md"
README = ROOT / "README.md"
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"


def fail(message: str) -> None:
    raise SystemExit("ERROR: " + message)


def main() -> int:
    for path in (CONTRACT, MATRIX, DOC, README, PCB):
        if not path.exists():
            fail(f"falta {path.relative_to(ROOT)}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("schema_version") != 1:
        fail("eu_compliance_contract.json debe ser schema v1")
    if contract.get("status") != "EU_COMPLIANCE_DESIGN_GATE_PR8":
        fail("estado de compliance no corresponde a PR8")
    if contract.get("design_object") != "SHIELD_CARRIER_FOR_ARDUINO_UNO_Q":
        fail("el objeto de diseño debe permanecer como shield/carrier UNO Q")

    boundary = contract["compliance_boundary"]
    for key in (
        "shield_adds_intentional_radiator",
        "shield_modifies_host_rf_chain",
        "shield_modifies_host_antenna",
        "shield_modifies_host_rf_matching",
        "shield_modifies_host_regulatory_firmware",
    ):
        if boundary.get(key) is not False:
            fail(f"frontera RF violada: {key} debe ser false")
    if boundary.get("final_integrated_product_assessment_required") is not True:
        fail("debe conservarse evaluación de la configuración final integrada")

    rf = contract["rf_design_rules"]
    required_true = (
        "preserve_host_rf_keepout",
        "no_added_rf_transceiver",
        "no_added_antenna",
        "no_added_rf_power_amplifier",
        "no_added_rf_matching_network",
        "rf_boundary_change_requires_compliance_pr",
    )
    for key in required_true:
        if rf.get(key) is not True:
            fail(f"regla RF requerida no activa: {key}")

    emc = contract["emc_layout_rules"]
    if emc.get("continuous_ground_reference_required") is not True:
        fail("se requiere referencia GND continua")
    if emc.get("field_io_edge") != "Y=0" or emc.get("field_connector_facing") != "-Y":
        fail("convención FIELD I/O EDGE cambió")
    if emc.get("in1_signal_routing_allowed_if_frozen_as_gnd") is not False:
        fail("In1.Cu no puede aceptar señales si se congela como GND")
    expected_gradient = [
        "Z0_UNO_Q",
        "Z1_SENSORS_ANALOG",
        "Z2_DIGITAL_LOW_NOISE",
        "Z3_POWER",
        "Z4_ACTUATORS",
    ]
    if emc.get("functional_noise_gradient") != expected_gradient:
        fail("gradiente funcional EMC fue modificado")

    targets = {item["id"] for item in contract.get("eu_targets", [])}
    expected_targets = {"EMC", "ROHS3", "WEEE", "RED", "REACH", "CE"}
    if targets != expected_targets:
        fail(f"matriz normativa incompleta: {targets} != {expected_targets}")

    evidence = contract["production_evidence_gate"]
    if evidence.get("missing_evidence_blocks_production_release") is not True:
        fail("la falta de evidencia RoHS/REACH/host debe bloquear release")

    with MATRIX.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    matrix_ids = {row["marco"] for row in rows}
    if not {"EMC", "RoHS 3", "WEEE", "RED", "REACH", "CE", "RF_HOST"}.issubset(matrix_ids):
        fail("EU_COMPLIANCE_MATRIX.csv no contiene todos los marcos requeridos")

    readme = README.read_text(encoding="utf-8")
    for marker in (
        "shield/carrier",
        "EU Compliance Design Gate",
        "docs/EU_COMPLIANCE_GATE.md",
        "compliance/eu_compliance_contract.json",
        "Arduino UNO Q",
    ):
        if marker not in readme:
            fail(f"README sin marcador requerido: {marker}")

    doc = DOC.read_text(encoding="utf-8")
    for marker in ("RoHS 3", "REACH", "WEEE", "RED", "Marcado CE", "keepout", "SAC305", "ENIG"):
        if marker not in doc:
            fail(f"documento compliance sin {marker}")

    pcb = PCB.read_text(encoding="utf-8")
    if "J_UNOQ" not in pcb:
        fail("PCB perdió el footprint anfitrión J_UNOQ")

    # Guardrail simple: las BOM de producción del shield no deben incorporar
    # radios/antenas evidentes sin actualizar primero el contrato de compliance.
    forbidden_rf_tokens = (
        "ESP32",
        "NRF52",
        "NRF53",
        "SX127",
        "SX126",
        "CC1101",
        "SIM7000",
        "SIM7600",
        "LORA",
        "WIFI MODULE",
        "BLUETOOTH MODULE",
        "PCB ANTENNA",
        "CHIP ANTENNA",
    )
    for bom_path in sorted((ROOT / "bom").glob("insight_*_production_bom.csv")):
        text = bom_path.read_text(encoding="utf-8").upper()
        for token in forbidden_rf_tokens:
            if token in text:
                fail(f"{bom_path.name} introduce RF '{token}' sin PR de compliance")

    print("OK: EU Compliance Design Gate PR #8")
    print("- objeto: shield/carrier para Arduino UNO Q")
    print("- RF del host preservada; shield sin transmisor/antena propios")
    print("- EMC/RoHS3/REACH/WEEE/RED/CE trazados")
    print("- README y matriz normativa sincronizados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
