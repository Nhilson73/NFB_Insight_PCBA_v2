#!/usr/bin/env python3
"""Valida arquitectura PR9/PR10 bajo contrato UNO Q schema v6 PR12."""
from __future__ import annotations
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POWER=ROOT/"hardware"/"power_architecture_contract.json"; PIN=ROOT/"hardware"/"insight_pin_contract.json"; Z1=ROOT/"hardware"/"z1_production_netlist.json"; Z2=ROOT/"hardware"/"z2_production_netlist.json"; Z4=ROOT/"hardware"/"z4_production_netlist.json"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"; README=ROOT/"README.md"; ROADMAP=ROOT/"docs"/"ROADMAP.md"; SOURCES=ROOT/"docs"/"SOURCE_OF_TRUTH.md"; POWERDOC=ROOT/"docs"/"POWER_ARCHITECTURE.md"
ARDUINO_SNAPSHOT="196feda03787005572a059f030677b8a1de9bcd2"
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for x in (POWER,PIN,Z1,Z2,Z4,PCB,README,ROADMAP,SOURCES,POWERDOC):
        if not x.exists(): fail(f"falta {x.relative_to(ROOT)}")
    c=json.loads(POWER.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); z1=json.loads(Z1.read_text(encoding="utf-8")); z2=json.loads(Z2.read_text(encoding="utf-8")); z4=json.loads(Z4.read_text(encoding="utf-8"))
    if c.get("schema_version")!=2 or c.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9" or c.get("production_status")!="POWER_PRODUCTION_BASELINE_PR10": fail("baseline potencia PR9/10 cambió")
    if c.get("design_object")!="SHIELD_CARRIER_FOR_ARDUINO_UNO_Q": fail("objeto diseño incorrecto")
    sh=c["source_hierarchy"]; prim=" ".join(sh["uno_q_primary"]).lower(); snap=sh.get("arduino_docs_content_snapshot",{})
    if "github.com/arduino" not in prim or "arduino/docs-content" not in prim or snap.get("commit")!=ARDUINO_SNAPSHOT: fail("fuente primaria Arduino PR9 cambió")
    required_files={"content/hardware/02.uno/boards/uno-q/datasheet/datasheet.md","content/hardware/02.uno/boards/uno-q/tutorials/03.power-specification/content.md","content/hardware/02.uno/carriers/uno-breakout-carrier/datasheet/datasheet.md"}
    if set(snap.get("files",[]))!=required_files: fail("snapshot Arduino incompleto")
    official=set(c["host_power"]["official_supported_inputs"])
    if not {"USB-C 5 V / up to 3 A","VIN 7-24 V","regulated 5 V through JANALOG 5 V pin / up to 3 A"}<=official: fail("métodos alimentación UNO Q incompletos")
    if c["host_power"]["preferred_method_for_nfb"]!="VIN_7_TO_24V": fail("NFB no usa VIN")
    lo,hi=map(float,c["input"]["allowed_v"])
    if not (lo<=12<=hi and hi<23): fail("ventana 12V incompatible")
    ef=c["input_protection"]["efuse"]
    if ef["mpn"]!="TPS259470ARPWR" or ef["vin_range_v"]!=[2.7,23.0] or float(ef["current_capability_a"])<5.5 or not 0.5<=float(ef["target_current_limit_a"])<=5.5: fail("eFuse baseline incorrecto")
    if c["input_protection"]["tvs"]["family"]!="SMBJ15A": fail("TVS baseline incorrecto")
    split={b["net"]:b for b in c["star_split"]["branches"]}
    if set(split)!={"12V_HOST_VIN","12V_LOGIC","12V_ACT"}: fail("split estrella incorrecto")
    if c["star_split"]["chiller_power_on_pcba"] is not False or c["actuator_policy"]["chiller"]!="external power; control only": fail("chiller power reapareció")
    u5=c["shield_5v"]["regulator"]; u3=c["shield_3v3"]["regulator"]
    if c["shield_5v"]["host_5v_tied"] or u5["mpn"]!="TPSM33625RDNR" or float(u5["design_continuous_limit_a"])>1.5: fail("5V baseline incorrecto")
    if c["shield_5v"]["enable"]["source"]!="UNO_IOREF_3V3": fail("5V no secuenciado por IOREF")
    if c["shield_3v3"]["host_3v3_tied"] or u3["mpn"]!="TLV75533PDBVR" or float(u3["design_continuous_limit_a"])>0.25: fail("3V3 baseline incorrecto")
    b=c["power_budget"]; total=float(b["host_branch_w_design"])+float(b["shield_5v_w_design"])+float(b["actuator_12v_w_design"])
    if not math.isclose(total,float(b["total_w_design"]),abs_tol=1e-9) or float(b["recommended_supply_w"])<total*1.25: fail("budget potencia sin margen")
    if p.get("schema_version")!=6 or p.get("power_architecture_source_of_truth")!="hardware/power_architecture_contract.json": fail("pin contract no enlaza potencia")
    pins={int(x["pad"]):x for x in p["pins"]}
    if (pins[2]["net"],pins[2]["status"])!=("UNO_IOREF_3V3","ACTIVE_CONTROL_OUTPUT") or (pins[8]["net"],pins[8]["status"])!=("12V_HOST_VIN","ACTIVE_POWER_INPUT"): fail("frontera IOREF/VIN incorrecta")
    if pins[4]["net"] is not None or pins[5]["net"] is not None or pins[5]["status"]!="NC_HOST_5V_SUPPORTED_INPUT": fail("frontera rails host incorrecta")
    for nz,name in ((z1,"Z1"),(z2,"Z2"),(z4,"Z4")):
        nets={x["name"]:set(x["nodes"]) for x in nz["nets"]}
        if "J_UNOQ.4" in nets.get("3V3_RAIL",set()) or "J_UNOQ.5" in nets.get("5V_RAIL",set()): fail(f"{name} back-feed host")
    n4={x["name"]:set(x["nodes"]) for x in z4["nets"]}
    if "12V_ACT" not in n4 or "U_PUMP_DRV.6" not in n4["12V_ACT"] or "U_CO2_DRV.8" not in n4["12V_ACT"]: fail("Z4 no consume rama 12V_ACT")
    if any(x in n4["12V_ACT"] for x in ("U_CHILLER.3","U_CHILLER.4")): fail("chiller conectado a potencia PCBA")
    pcb=PCB.read_text(encoding="utf-8"); premature=[r for r in ("U_EFUSE","U_5V","U_3V3","D_IN_TVS","U_PUMP_DRV","U_CO2_DRV","U_CHILLER") if f'"{r}"' in pcb]
    if premature: fail(f"placement prematuro: {premature}")
    src=SOURCES.read_text(encoding="utf-8")
    for m in ("https://github.com/Arduino","arduino/docs-content","Regla de conflicto"):
        if m not in src: fail(f"SOURCE_OF_TRUTH sin {m}")
    readme=README.read_text(encoding="utf-8"); road=ROADMAP.read_text(encoding="utf-8"); pd=POWERDOC.read_text(encoding="utf-8")
    for m in ("PR #9","TPS259470ARPWR","TPSM33625RDNR","TLV75533PDBVR","12V_HOST_VIN"):
        if m not in readme and m not in pd: fail(f"docs potencia sin {m}")
    if "Fuente primaria UNO Q" not in readme: fail("README perdió jerarquía de fuentes")
    required_road=("PR #9","PR #10","potencia de producción","12 V protegido → VIN UNO Q","TPS259470ARPWR","TPSM33625RDNR","TLV75533PDBVR")
    if any(m not in road for m in required_road): fail("roadmap no preserva arquitectura PR9/PR10")
    print("OK: arquitectura potencia PR9/10 preservada bajo root EDA PR14")
    return 0
if __name__=="__main__": raise SystemExit(main())
