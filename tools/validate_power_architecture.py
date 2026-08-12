#!/usr/bin/env python3
"""Valida arquitectura de potencia PR #9 y frontera eléctrica con UNO Q."""
from __future__ import annotations
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POWER=ROOT/"hardware"/"power_architecture_contract.json"; PIN=ROOT/"hardware"/"insight_pin_contract.json"; Z1=ROOT/"hardware"/"z1_production_netlist.json"; Z2=ROOT/"hardware"/"z2_production_netlist.json"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"; README=ROOT/"README.md"; ROADMAP=ROOT/"docs"/"ROADMAP.md"; SOURCES=ROOT/"docs"/"SOURCE_OF_TRUTH.md"; POWERDOC=ROOT/"docs"/"POWER_ARCHITECTURE.md"
ARDUINO_SNAPSHOT="196feda03787005572a059f030677b8a1de9bcd2"
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for x in (POWER,PIN,Z1,Z2,PCB,README,ROADMAP,SOURCES,POWERDOC):
        if not x.exists(): fail(f"falta {x.relative_to(ROOT)}")
    c=json.loads(POWER.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); z1=json.loads(Z1.read_text(encoding="utf-8")); z2=json.loads(Z2.read_text(encoding="utf-8"))
    if c.get("schema_version")!=2 or c.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9": fail("contrato potencia no es PR9 schema v2")
    if c.get("design_object")!="SHIELD_CARRIER_FOR_ARDUINO_UNO_Q": fail("objeto de diseño incorrecto")
    sh=c["source_hierarchy"]
    prim=" ".join(sh["uno_q_primary"]).lower()
    if "github.com/arduino" not in prim or "arduino/docs-content" not in prim: fail("GitHub Arduino no es fuente primaria")
    snap=sh.get("arduino_docs_content_snapshot",{})
    if snap.get("commit")!=ARDUINO_SNAPSHOT: fail("snapshot docs-content Arduino cambió sin revisión")
    required_files={"content/hardware/02.uno/boards/uno-q/datasheet/datasheet.md","content/hardware/02.uno/boards/uno-q/tutorials/03.power-specification/content.md","content/hardware/02.uno/carriers/uno-breakout-carrier/datasheet/datasheet.md"}
    if set(snap.get("files",[]))!=required_files: fail("snapshot Arduino no contiene las tres fuentes PR9")
    official=set(c["host_power"]["official_supported_inputs"])
    required={"USB-C 5 V / up to 3 A","VIN 7-24 V","regulated 5 V through JANALOG 5 V pin / up to 3 A"}
    if not required<=official: fail("faltan métodos oficiales alimentación UNO Q")
    if c["host_power"]["preferred_method_for_nfb"]!="VIN_7_TO_24V": fail("NFB no usa VIN como baseline")
    vin=c["input"]; lo,hi=map(float,vin["allowed_v"])
    if not (lo<=12.0<=hi and hi<23.0): fail("ventana entrada NFB incompatible con eFuse")
    ef=c["input_protection"]["efuse"]
    if ef["mpn"]!="TPS259470ARPWR" or ef["vin_range_v"]!=[2.7,23.0] or float(ef["current_capability_a"])<5.5: fail("eFuse no congelado")
    if not (0.5<=float(ef["target_current_limit_a"])<=5.5): fail("ILIM objetivo fuera de rango")
    tvs=c["input_protection"]["tvs"]
    if tvs["family"]!="SMBJ15A" or float(tvs["vrwm_v"])!=15.0: fail("TVS entrada no congelado")
    split={b["net"]:b for b in c["star_split"]["branches"]}
    if set(split)!={"12V_HOST_VIN","12V_LOGIC","12V_ACT"}: fail("split estrella incorrecto")
    if c["star_split"]["chiller_power_on_pcba"] is not False or c["actuator_policy"]["chiller"]!="external power; control only": fail("chiller power reapareció")
    r5=c["shield_5v"]; u5=r5["regulator"]
    if r5.get("host_5v_tied") is not False: fail("5V_RAIL unido host")
    if u5["mpn"]!="TPSM33625RDNR" or u5["vin_range_v"]!=[3.0,36.0] or float(u5["rated_current_a"])!=2.5 or float(u5["design_continuous_limit_a"])>1.5: fail("buck 5V baseline incorrecto")
    if r5["enable"]["source"]!="UNO_IOREF_3V3" or int(r5["enable"]["uno_q_pad"])!=2: fail("secuencia 5V no usa IOREF")
    r3=c["shield_3v3"]; u3=r3["regulator"]
    if r3.get("host_3v3_tied") is not False: fail("3V3_RAIL unido host")
    if u3["mpn"]!="TLV75533PDBVR" or float(u3["rated_current_a"])!=0.5 or float(u3["vout_v"])!=3.3 or float(u3["design_continuous_limit_a"])>0.25: fail("LDO 3V3 baseline incorrecto")
    b=c["power_budget"]; total=float(b["host_branch_w_design"])+float(b["shield_5v_w_design"])+float(b["actuator_12v_w_design"])
    if not math.isclose(total,float(b["total_w_design"]),abs_tol=1e-9): fail("suma presupuesto incorrecta")
    if float(b["recommended_supply_w"])<total*1.25: fail("fuente sin >=25% margen")
    if p.get("schema_version")!=5 or p.get("power_architecture_source_of_truth")!="hardware/power_architecture_contract.json": fail("pin contract no enlaza PR9")
    pins={int(x["pad"]):x for x in p["pins"]}
    if (pins[2]["net"],pins[2]["status"])!=("UNO_IOREF_3V3","ACTIVE_CONTROL_OUTPUT"): fail("IOREF contractual incorrecto")
    if pins[4]["net"] is not None or pins[5]["net"] is not None: fail("rails host unidos a rails locales")
    if pins[5]["status"]!="NC_HOST_5V_SUPPORTED_INPUT": fail("pad 5 no reconoce entrada 5V oficial")
    if (pins[8]["net"],pins[8]["status"])!=("12V_HOST_VIN","ACTIVE_POWER_INPUT"): fail("VIN contractual incorrecto")
    for nz,name in ((z1,"Z1"),(z2,"Z2")):
        nets={x["name"]:set(x["nodes"]) for x in nz["nets"]}
        if "J_UNOQ.4" in nets.get("3V3_RAIL",set()) or "J_UNOQ.5" in nets.get("5V_RAIL",set()): fail(f"{name} conserva back-feed host")
    pcb=PCB.read_text(encoding="utf-8"); premature=[r for r in ("U_EFUSE","U_5V","U_3V3","D_IN_TVS","C_IN_BULK") if f'"{r}"' in pcb]
    if premature: fail(f"arquitectura/PR10 no debe hacer placement: {premature}")
    src=SOURCES.read_text(encoding="utf-8")
    for marker in ("https://github.com/Arduino","arduino/docs-content","Regla de conflicto"):
        if marker not in src: fail(f"SOURCE_OF_TRUTH sin {marker}")
    readme=README.read_text(encoding="utf-8"); road=ROADMAP.read_text(encoding="utf-8"); pd=POWERDOC.read_text(encoding="utf-8")
    for marker in ("PR #9","TPS259470ARPWR","TPSM33625RDNR","TLV75533PDBVR","12V_HOST_VIN"):
        if marker not in readme and marker not in pd: fail(f"docs sin {marker}")
    if "Fuente primaria UNO Q" not in readme: fail("README no declara fuente primaria")
    # PR #10 amplía la Fase 3, por lo que el gate PR9 debe aceptar el roadmap
    # evolucionado sin exigir un título textual antiguo.
    if "PR #9" not in road or "Fase 3" not in road or "Power tree y frontera UNO Q" not in road: fail("ROADMAP no conserva arquitectura PR9")
    if "PR #10" not in road or "Esquemático de potencia de producción" not in road: fail("ROADMAP no refleja continuación PR10")
    print("OK: arquitectura de potencia PR #9 preservada bajo baseline PR #10")
    print(f"- Arduino docs-content snapshot {ARDUINO_SNAPSHOT[:12]}…")
    print("- 12V protegido -> VIN; 5V/3V3 locales sin back-feed")
    print("- TPS259470A + TPSM33625 + TLV75533; chiller externo")
    print(f"- presupuesto {total:.1f}W; fuente {float(b['recommended_supply_w']):.0f}W")
    return 0
if __name__=="__main__": raise SystemExit(main())
