#!/usr/bin/env python3
"""Valida el baseline de producción de potencia PR #10."""
from __future__ import annotations
import csv, json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NET=ROOT/"hardware"/"power_production_netlist.json"
ARCH=ROOT/"hardware"/"power_architecture_contract.json"
PIN=ROOT/"hardware"/"insight_pin_contract.json"
CLASSES=ROOT/"hardware"/"power_netclasses.json"
BOM=ROOT/"bom"/"insight_power_production_bom.csv"
SCH=ROOT/"kicad"/"power.kicad_sch"
PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"
README=ROOT/"README.md"
ROADMAP=ROOT/"docs"/"ROADMAP.md"

def fail(m): raise SystemExit("ERROR: "+m)
def close(a,b,t=1e-6): return math.isclose(float(a),float(b),rel_tol=t,abs_tol=t)

def main():
    for f in (NET,ARCH,PIN,CLASSES,BOM,SCH,PCB,README,ROADMAP):
        if not f.exists(): fail(f"falta {f.relative_to(ROOT)}")
    n=json.loads(NET.read_text(encoding="utf-8")); a=json.loads(ARCH.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); nc=json.loads(CLASSES.read_text(encoding="utf-8"))
    if n.get("schema_version")!=1 or n.get("status")!="FROZEN_POWER_NETLIST_PR10": fail("netlist potencia no es PR10")
    if n.get("source_architecture")!="hardware/power_architecture_contract.json": fail("netlist no enlaza arquitectura")
    if a.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9" or a.get("production_status")!="POWER_PRODUCTION_BASELINE_PR10": fail("arquitectura no declara production baseline PR10")
    if a.get("production_netlist_source_of_truth")!="hardware/power_production_netlist.json": fail("arquitectura no declara netlist PR10")
    if p.get("schema_version")!=5 or p.get("power_production_netlist_source_of_truth")!="hardware/power_production_netlist.json": fail("pin contract no enlaza netlist potencia PR10")
    comps={x["ref"]:x for x in n["components"]}; nets={x["name"]:set(x["nodes"]) for x in n["nets"]}
    if len(comps)!=34: fail(f"se esperaban 34 refs potencia, hay {len(comps)}")
    for ref,c in comps.items():
        for pin,net in c["pins"].items():
            if net=="NC": continue
            node=f"{ref}.{pin}"
            if node not in nets.get(net,set()): fail(f"nodo {node} no aparece en {net}")
    with BOM.open(newline="",encoding="utf-8") as fh: rows=list(csv.DictReader(fh))
    if {r["ref"] for r in rows}!=set(comps) or len(rows)!=len(comps): fail("BOM potencia != refs netlist")
    # Entrada / eFuse
    if comps["J_PWR_IN"]["mpn"]!="1757242": fail("conector entrada no es Phoenix 1757242")
    if comps["D_IN_TVS"]["mpn"]!="SMBJ15A-TR": fail("TVS final no es SMBJ15A-TR")
    ef=comps["U_EFUSE"]
    expected_ef={"1":"EFUSE_EN_UVLO","2":"EFUSE_OVLO","3":"NC","4":"NC","5":"12V_IN_RAW","6":"12V_PROTECTED","7":"EFUSE_DVDT","8":"GND","9":"EFUSE_ILM","10":"EFUSE_ITIMER"}
    if ef["mpn"]!="TPS259470ARPWR" or ef["pins"]!=expected_ef: fail("TPS259470A/pinout incorrecto")
    dv=n["design_values"]["efuse"]; r=dv["uvov_ladder_ohm"]
    if (r["r1"],r["r2"],r["r3"])!=(470000,11000,47000): fail("ladder UV/OV no es 470k/11k/47k")
    uv=1.2*(r["r1"]+r["r2"]+r["r3"])/(r["r2"]+r["r3"])
    ov=1.2*(r["r1"]+r["r2"]+r["r3"])/r["r3"]
    if not (10.5<=uv<=11.3 and 13.0<=ov<=13.8): fail(f"thresholds UV/OV inesperados: {uv:.3f}/{ov:.3f}")
    if not close(dv["nominal_uvlo_from_1p2v_v"],uv,1e-8) or not close(dv["nominal_ovlo_from_1p2v_v"],ov,1e-8): fail("thresholds almacenados no cuadran")
    if dv["rilm_ohm"]!=750 or comps["R_EFUSE_ILIM"]["value"]!="750R 1%": fail("RILM debe ser 750R")
    if not close(dv["ilim_formula_typ_a"],3334/750,1e-8): fail("cálculo ILIM formula incorrecto")
    if not close(dv["dvdt_cap_f"],3.3e-9) or not close(dv["itimer_cap_f"],2.2e-9): fail("dVdt/ITIMER no congelados")
    # Split estrella / actuadores
    if comps["NT_HOST"]["pins"]!={"1":"12V_PROTECTED","2":"12V_HOST_VIN"}: fail("net tie host incorrecto")
    if comps["NT_LOGIC"]["pins"]!={"1":"12V_PROTECTED","2":"12V_LOGIC"}: fail("net tie lógica incorrecto")
    act=n["design_values"]["actuator_branch"]
    if comps["F_ACT"]["mpn"]!="045401.5MR" or float(act["fuse_rating_a"])!=1.5: fail("F_ACT final incorrecto")
    if float(act["combined_expected_peak_a"])>=float(act["fuse_rating_a"]): fail("peak nominal actuadores no deja margen contra rating fuse")
    if act.get("hil_revalidation_required") is not True: fail("F_ACT debe revalidarse HIL")
    # Buck 5 V
    u5=comps["U_5V"]; expected_u5={"1":"5V_PGOOD","2":"UNO_IOREF_3V3","3":"12V_LOGIC","4":"5V_RAIL","5":"NC","6":"NC","7":"NC","8":"5V_VCC","9":"5V_FB","10":"GND","11":"5V_VCC"}
    if u5["mpn"]!="TPSM33625RDNR" or u5["pins"]!=expected_u5: fail("TPSM33625/pinout incorrecto")
    b=n["design_values"]["buck_5v"]
    if b["switching_frequency_hz"]!=1000000 or b["rt_configuration"]!="PIN11_RT_TO_PIN8_VCC": fail("TPSM no congelado a 1MHz")
    if (b["feedback_top_ohm"],b["feedback_bottom_ohm"])!=(40200,10000): fail("feedback TPSM no 40.2k/10k")
    if not close(b["input_cap_nominal_f"],4.7e-6) or not close(b["input_hf_cap_f"],1e-7): fail("capacitores entrada TPSM incorrectos")
    if b["output_cap_count"]!=2 or not close(b["output_nominal_total_f"],44e-6): fail("salida TPSM no tiene 2x22uF")
    if float(b["minimum_effective_output_f"])<25e-6: fail("mínimo efectivo TPSM inferior a 25uF")
    if b["pgood_pullup_ohm"]!=47000 or comps["R_5V_PG_PU"]["pins"]!={"1":"5V_RAIL","2":"5V_PGOOD"}: fail("PGOOD pull-up incorrecto")
    if comps["C_5V_IN_4U7"]["mpn"]!="C3225X7R1H475K250AB": fail("4.7uF/50V no usa MPN vigente congelado")
    if comps["C_5V_OUT1"]["mpn"]!="GCM32ER71C226ME19L" or comps["C_5V_OUT2"]["mpn"]!="GCM32ER71C226ME19L": fail("output caps 5V no congelados")
    # LDO 3.3 V
    u3=comps["U_3V3"]; expected_u3={"1":"5V_RAIL","2":"GND","3":"5V_PGOOD","4":"NC","5":"3V3_RAIL"}
    if u3["mpn"]!="TLV75533PDBVR" or u3["pins"]!=expected_u3: fail("TLV75533/pinout incorrecto")
    l=n["design_values"]["ldo_3v3"]
    if not close(l["input_cap_f"],1e-6) or not close(l["output_cap_f"],1e-6): fail("LDO requiere 1uF entrada/salida")
    # Frontera host / secuencia
    if "J_UNOQ.4" in nets.get("3V3_RAIL",set()) or "J_UNOQ.5" in nets.get("5V_RAIL",set()): fail("back-feed host reapareció")
    if "J_UNOQ.8" not in nets.get("12V_HOST_VIN",set()): fail("VIN UNO Q no conectado a rama host")
    if "J_UNOQ.2" not in nets.get("UNO_IOREF_3V3",set()): fail("IOREF no aparece como referencia host")
    if comps["U_5V"]["pins"]["2"]!="UNO_IOREF_3V3" or comps["U_3V3"]["pins"]["3"]!="5V_PGOOD": fail("secuencia host→5V→3V3 rota")
    # Netclasses
    if nc.get("status")!="POWER_NETCLASS_BASELINE_PR10": fail("netclasses no son PR10")
    classes={x["name"]:x for x in nc["classes"]}
    if set(classes)!={"PWR_INPUT_5A","PWR_12V_BRANCH","PWR_5V","PWR_3V3","PWR_CONTROL"}: fail("set netclasses potencia incorrecto")
    if float(classes["PWR_INPUT_5A"]["track_width_mm_min"])<2.0: fail("troncal entrada demasiado estrecha")
    # Thermal screen
    th=n["design_values"]["thermal_screen_60c"]
    if th["status"]!="ANALYTICAL_SCREEN_ONLY_HIL_REQUIRED": fail("thermal screen no conserva gate HIL")
    if float(th["ldo_estimated_tj_at_60c_c"])>=125: fail("screen térmico LDO excede 125C")
    # EDA/documentación
    sch=SCH.read_text(encoding="utf-8")
    for marker in ("PR #10","TPS259470ARPWR","TPSM33625RDNR","TLV75533PDBVR","12V_HOST_VIN","PENDING_DATASHEET_AUDIT_BEFORE_PLACEMENT"):
        if marker not in sch: fail(f"power.kicad_sch sin {marker}")
    for ref in comps:
        if ref not in sch: fail(f"power.kicad_sch no indexa {ref}")
    pcb=PCB.read_text(encoding="utf-8")
    placed=[r for r in comps if f'"{r}"' in pcb]
    if placed: fail(f"PR10 no debe colocar potencia en PCB: {placed[:5]}")
    for ref in ("U_EFUSE","U_5V"):
        if comps[ref]["footprint"]!="PENDING_DATASHEET_AUDIT_BEFORE_PLACEMENT": fail(f"{ref} no conserva gate de footprint")
    readme=README.read_text(encoding="utf-8"); road=ROADMAP.read_text(encoding="utf-8")
    for marker in ("PR #10","power_production_netlist.json","TPS259470ARPWR","045401.5MR"):
        if marker not in readme: fail(f"README no sincronizado: {marker}")
    if "PR #10 — Esquemático de potencia de producción" not in road: fail("ROADMAP sin PR10")
    print("OK: power production PR #10 congelado y coherente")
    print(f"- 34 refs / {len(n['nets'])} nets; BOM = netlist")
    print(f"- UVLO nominal {uv:.3f} V; OVLO nominal {ov:.3f} V; ILIM ~{3334/750:.3f} A")
    print("- TPSM 1MHz 40.2k/10k, 2x22uF; TLV75533 1uF/1uF")
    print("- 0 placement potencia; footprints RPW/RDN bloqueados a auditoría")
    return 0

if __name__=="__main__": raise SystemExit(main())
