#!/usr/bin/env python3
"""Gate de cumplimiento europeo de diseño para NFB Insight PCBA v2 como shield UNO Q."""
from __future__ import annotations
import csv,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"compliance"/"eu_compliance_contract.json"; MATRIX=ROOT/"compliance"/"EU_COMPLIANCE_MATRIX.csv"; DOC=ROOT/"docs"/"EU_COMPLIANCE_GATE.md"; SOURCE_POLICY=ROOT/"docs"/"SOURCE_OF_TRUTH.md"; POWER=ROOT/"hardware"/"power_architecture_contract.json"; README=ROOT/"README.md"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for p in (CONTRACT,MATRIX,DOC,SOURCE_POLICY,POWER,README,PCB):
        if not p.exists(): fail(f"falta {p.relative_to(ROOT)}")
    c=json.loads(CONTRACT.read_text(encoding="utf-8"))
    if c.get("schema_version")!=1 or c.get("status")!="EU_COMPLIANCE_DESIGN_GATE_PR8" or c.get("design_object")!="SHIELD_CARRIER_FOR_ARDUINO_UNO_Q": fail("contrato compliance PR8 cambió")
    b=c["compliance_boundary"]
    for k in ("shield_adds_intentional_radiator","shield_modifies_host_rf_chain","shield_modifies_host_antenna","shield_modifies_host_rf_matching","shield_modifies_host_regulatory_firmware"):
        if b.get(k) is not False: fail(f"frontera RF violada: {k}")
    if b.get("final_integrated_product_assessment_required") is not True: fail("evaluación producto integrado debe permanecer obligatoria")
    rf=c["rf_design_rules"]
    for k in ("preserve_host_rf_keepout","no_added_rf_transceiver","no_added_antenna","no_added_rf_power_amplifier","no_added_rf_matching_network","rf_boundary_change_requires_compliance_pr"):
        if rf.get(k) is not True: fail(f"regla RF no activa: {k}")
    emc=c["emc_layout_rules"]
    if emc.get("continuous_ground_reference_required") is not True or emc.get("field_io_edge")!="Y=0" or emc.get("field_connector_facing")!="-Y" or emc.get("in1_signal_routing_allowed_if_frozen_as_gnd") is not False: fail("guardrails EMC/layout cambiaron")
    if emc.get("functional_noise_gradient")!=["Z0_UNO_Q","Z1_SENSORS_ANALOG","Z2_DIGITAL_LOW_NOISE","Z3_POWER","Z4_ACTUATORS"]: fail("gradiente EMC cambió")
    if {x["id"] for x in c.get("eu_targets",[])}!={"EMC","ROHS3","WEEE","RED","REACH","CE"}: fail("targets UE incompletos")
    if c["production_evidence_gate"].get("missing_evidence_blocks_production_release") is not True: fail("evidencia faltante debe bloquear release")
    with MATRIX.open(encoding="utf-8",newline="") as f: mids={r["marco"] for r in csv.DictReader(f)}
    if not {"EMC","RoHS 3","WEEE","RED","REACH","CE","RF_HOST"}.issubset(mids): fail("matriz compliance incompleta")
    src=SOURCE_POLICY.read_text(encoding="utf-8")
    for m in ("https://github.com/Arduino","https://github.com/orgs/arduino/repositories","arduino/docs-content","Prioridad 1 — GitHub oficial Arduino"):
        if m not in src: fail(f"SOURCE_OF_TRUTH sin {m}")
    power=json.loads(POWER.read_text(encoding="utf-8"))
    if power.get("design_object")!="SHIELD_CARRIER_FOR_ARDUINO_UNO_Q" or power.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9": fail("power contract cambió frontera")
    if power["star_split"].get("chiller_power_on_pcba") is not False: fail("chiller power no debe atravesar PCBA")
    rules=" ".join(power.get("compliance_rules",[])).lower()
    for t in ("reference plane","rf keepout","tvs","efuse","iec 61000-4-5"):
        if t not in rules: fail(f"power contract sin guardrail {t}")
    readme=README.read_text(encoding="utf-8")
    # El README evoluciona por fases. Proteger conceptos/links, no títulos literales históricos.
    for m in ("shield/carrier","docs/EU_COMPLIANCE_GATE.md","compliance/eu_compliance_contract.json","Arduino UNO Q","Fuente primaria UNO Q","hardware/power_architecture_contract.json"):
        if m not in readme: fail(f"README sin marcador requerido: {m}")
    readme_l=readme.lower()
    if "compliance" not in readme_l or not any(t in readme for t in ("gate europeo","EU Compliance","cumplimiento europeo")): fail("README no preserva frontera/gate europeo")
    if not re.search(r"(?m)^##\s+Z3(?:\s*[—-]\s*|\s+)potencia\b",readme,re.IGNORECASE): fail("README no conserva sección Z3 potencia")
    for m in ("12 V protegido → VIN","TPS259470ARPWR","TPSM33625RDNR","TLV75533PDBVR"):
        if m not in readme: fail(f"README no preserva arquitectura de potencia: {m}")
    doc=DOC.read_text(encoding="utf-8")
    for m in ("RoHS 3","REACH","WEEE","RED","Marcado CE","keepout","SAC305","ENIG"):
        if m not in doc: fail(f"EU compliance doc sin {m}")
    pcb=PCB.read_text(encoding="utf-8")
    if "J_UNOQ" not in pcb: fail("PCB perdió J_UNOQ")
    forbidden=("ESP32","NRF52","NRF53","SX127","SX126","CC1101","SIM7000","SIM7600","LORA","WIFI MODULE","BLUETOOTH MODULE","PCB ANTENNA","CHIP ANTENNA")
    for bom in sorted((ROOT/"bom").glob("insight_*_production_bom.csv")):
        text=bom.read_text(encoding="utf-8").upper()
        for token in forbidden:
            if token in text: fail(f"{bom.name} introduce RF '{token}' sin compliance PR")
    print("OK: EU Compliance Design Gate PR8 preservado bajo PR15")
    print("- RF host, GND/EMC, SELV/no-mains y evidencia UE permanecen activos")
    return 0
if __name__=="__main__": raise SystemExit(main())
