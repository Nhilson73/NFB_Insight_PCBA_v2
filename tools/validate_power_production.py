#!/usr/bin/env python3
"""Valida baseline de producción de potencia PR10 bajo integración Z4 PR12."""
from __future__ import annotations
import csv,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NET=ROOT/"hardware"/"power_production_netlist.json"; ARCH=ROOT/"hardware"/"power_architecture_contract.json"; PIN=ROOT/"hardware"/"insight_pin_contract.json"; CLASSES=ROOT/"hardware"/"power_netclasses.json"; BOM=ROOT/"bom"/"insight_power_production_bom.csv"; SCH=ROOT/"kicad"/"power.kicad_sch"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"; README=ROOT/"README.md"; ROADMAP=ROOT/"docs"/"ROADMAP.md"; Z4=ROOT/"hardware"/"z4_production_netlist.json"
def fail(m): raise SystemExit("ERROR: "+m)
def close(a,b,t=1e-6): return math.isclose(float(a),float(b),rel_tol=t,abs_tol=t)
def main():
    for f in (NET,ARCH,PIN,CLASSES,BOM,SCH,PCB,README,ROADMAP,Z4):
        if not f.exists(): fail(f"falta {f.relative_to(ROOT)}")
    n=json.loads(NET.read_text(encoding="utf-8")); a=json.loads(ARCH.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); nc=json.loads(CLASSES.read_text(encoding="utf-8")); z4=json.loads(Z4.read_text(encoding="utf-8"))
    if n.get("schema_version")!=1 or n.get("status")!="FROZEN_POWER_NETLIST_PR10" or n.get("source_architecture")!="hardware/power_architecture_contract.json": fail("netlist potencia no es PR10")
    if a.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9" or a.get("production_status")!="POWER_PRODUCTION_BASELINE_PR10" or a.get("production_netlist_source_of_truth")!="hardware/power_production_netlist.json": fail("arquitectura no declara PR10")
    if p.get("schema_version")!=6 or p.get("power_production_netlist_source_of_truth")!="hardware/power_production_netlist.json": fail("pin contract no enlaza PR10/schema6")
    comps={x["ref"]:x for x in n["components"]}; nets={x["name"]:set(x["nodes"]) for x in n["nets"]}
    if len(comps)!=34: fail(f"refs potencia esperadas 34, hay {len(comps)}")
    for ref,c in comps.items():
        for pin,net in c["pins"].items():
            if net!="NC" and f"{ref}.{pin}" not in nets.get(net,set()): fail(f"{ref}.{pin} no aparece en {net}")
    with BOM.open(newline="",encoding="utf-8") as fh: rows=list(csv.DictReader(fh))
    if {r["ref"] for r in rows}!=set(comps) or len(rows)!=len(comps): fail("BOM potencia != netlist")
    if comps["J_PWR_IN"]["mpn"]!="1757242" or comps["D_IN_TVS"]["mpn"]!="SMBJ15A-TR": fail("entrada/TVS final cambió")
    ef=comps["U_EFUSE"]; expected_ef={"1":"EFUSE_EN_UVLO","2":"EFUSE_OVLO","3":"NC","4":"NC","5":"12V_IN_RAW","6":"12V_PROTECTED","7":"EFUSE_DVDT","8":"GND","9":"EFUSE_ILM","10":"EFUSE_ITIMER"}
    if ef["mpn"]!="TPS259470ARPWR" or ef["pins"]!=expected_ef: fail("eFuse/pinout cambió")
    dv=n["design_values"]["efuse"]; r=dv["uvov_ladder_ohm"]
    if (r["r1"],r["r2"],r["r3"])!=(470000,11000,47000): fail("ladder UV/OV cambió")
    uv=1.2*(r["r1"]+r["r2"]+r["r3"])/(r["r2"]+r["r3"]); ov=1.2*(r["r1"]+r["r2"]+r["r3"])/r["r3"]
    if not (10.5<=uv<=11.3 and 13<=ov<=13.8) or dv["rilm_ohm"]!=750 or not close(dv["dvdt_cap_f"],3.3e-9) or not close(dv["itimer_cap_f"],2.2e-9): fail("valores eFuse incorrectos")
    if comps["NT_HOST"]["pins"]!={"1":"12V_PROTECTED","2":"12V_HOST_VIN"} or comps["NT_LOGIC"]["pins"]!={"1":"12V_PROTECTED","2":"12V_LOGIC"}: fail("star split cambió")
    act=n["design_values"]["actuator_branch"]
    if comps["F_ACT"]["mpn"]!="045401.5MR" or float(act["fuse_rating_a"])!=1.5 or act.get("hil_revalidation_required") is not True: fail("F_ACT baseline cambió")
    u5=comps["U_5V"]; expected_u5={"1":"5V_PGOOD","2":"UNO_IOREF_3V3","3":"12V_LOGIC","4":"5V_RAIL","5":"NC","6":"NC","7":"NC","8":"5V_VCC","9":"5V_FB","10":"GND","11":"5V_VCC"}
    if u5["mpn"]!="TPSM33625RDNR" or u5["pins"]!=expected_u5: fail("TPSM/pinout cambió")
    b=n["design_values"]["buck_5v"]
    if b["switching_frequency_hz"]!=1000000 or b["rt_configuration"]!="PIN11_RT_TO_PIN8_VCC" or (b["feedback_top_ohm"],b["feedback_bottom_ohm"])!=(40200,10000): fail("TPSM config cambió")
    if b["output_cap_count"]!=2 or not close(b["output_nominal_total_f"],44e-6) or float(b["minimum_effective_output_f"])<25e-6 or b["pgood_pullup_ohm"]!=47000: fail("TPSM capacitores/PGOOD cambió")
    u3=comps["U_3V3"]
    if u3["mpn"]!="TLV75533PDBVR" or u3["pins"]!={"1":"5V_RAIL","2":"GND","3":"5V_PGOOD","4":"NC","5":"3V3_RAIL"}: fail("TLV75533 cambió")
    l=n["design_values"]["ldo_3v3"]
    if not close(l["input_cap_f"],1e-6) or not close(l["output_cap_f"],1e-6): fail("LDO caps cambió")
    if "J_UNOQ.4" in nets.get("3V3_RAIL",set()) or "J_UNOQ.5" in nets.get("5V_RAIL",set()) or "J_UNOQ.8" not in nets.get("12V_HOST_VIN",set()) or "J_UNOQ.2" not in nets.get("UNO_IOREF_3V3",set()): fail("frontera host potencia rota")
    if nc.get("status")!="POWER_NETCLASS_BASELINE_PR10": fail("netclasses no PR10")
    classes={x["name"]:x for x in nc["classes"]}
    if set(classes)!={"PWR_INPUT_5A","PWR_12V_BRANCH","PWR_5V","PWR_3V3","PWR_CONTROL"} or float(classes["PWR_INPUT_5A"]["track_width_mm_min"])<2.0: fail("netclasses potencia incorrectas")
    th=n["design_values"]["thermal_screen_60c"]
    if th["status"]!="ANALYTICAL_SCREEN_ONLY_HIL_REQUIRED" or float(th["ldo_estimated_tj_at_60c_c"])>=125: fail("thermal screen cambió")
    # Z4 must remain downstream of F_ACT and chiller outside power branch.
    n4={x["name"]:set(x["nodes"]) for x in z4["nets"]}
    if "12V_ACT" not in n4 or "U_PUMP_DRV.6" not in n4["12V_ACT"] or "U_CO2_DRV.8" not in n4["12V_ACT"]: fail("Z4 no usa rama 12V_ACT")
    if "U_CHILLER.3" in n4["12V_ACT"] or "U_CHILLER.4" in n4["12V_ACT"]: fail("chiller no debe consumir 12V_ACT")
    sch=SCH.read_text(encoding="utf-8")
    for m in ("PR #10","TPS259470ARPWR","TPSM33625RDNR","TLV75533PDBVR","12V_HOST_VIN","PENDING_DATASHEET_AUDIT_BEFORE_PLACEMENT"):
        if m not in sch: fail(f"power schematic sin {m}")
    for ref in comps:
        if ref not in sch: fail(f"power schematic no indexa {ref}")
    pcb=PCB.read_text(encoding="utf-8"); placed=[r for r in list(comps)+["U_PUMP_DRV","U_CO2_DRV","U_CHILLER"] if f'"{r}"' in pcb]
    if placed: fail(f"placement prematuro: {placed[:5]}")
    for ref in ("U_EFUSE","U_5V"):
        if comps[ref]["footprint"]!="PENDING_DATASHEET_AUDIT_BEFORE_PLACEMENT": fail(f"{ref} perdió gate footprint")
    readme=README.read_text(encoding="utf-8"); road=ROADMAP.read_text(encoding="utf-8")
    for m in ("PR #10","power_production_netlist.json","TPS259470ARPWR","045401.5MR"):
        if m not in readme: fail(f"README sin {m}")
    if "PR #10" not in road: fail("ROADMAP sin PR10")
    print("OK: power production PR10 preservado bajo integración Z4 PR12")
    return 0
if __name__=="__main__": raise SystemExit(main())
