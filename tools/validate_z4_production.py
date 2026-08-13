#!/usr/bin/env python3
"""Valida Z4 PR12 + footprints PR13 y habilita placement solo bajo gate PR17."""
from __future__ import annotations
import csv,json,math,re
from pathlib import Path
from validate_routing_phase import assert_authorized_phase
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"hardware"/"z4_actuator_contract.json"; N=ROOT/"hardware"/"z4_production_netlist.json"; P=ROOT/"hardware"/"insight_pin_contract.json"; A=ROOT/"hardware"/"footprint_audit.json"; B=ROOT/"bom"/"insight_z4_production_bom.csv"; S=ROOT/"kicad"/"z4_actuators.kicad_sch"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"; PLACEMENT=ROOT/"hardware"/"placement_manifest.json"
def fail(m): raise SystemExit("ERROR: "+m)
def close(a,b,t=1e-4): return math.isclose(float(a),float(b),rel_tol=t,abs_tol=t)
def main():
    for f in (C,N,P,A,B,S,PCB):
        if not f.exists(): fail(f"falta {f.relative_to(ROOT)}")
    c=json.loads(C.read_text(encoding="utf-8")); n=json.loads(N.read_text(encoding="utf-8")); p=json.loads(P.read_text(encoding="utf-8")); audit=json.loads(A.read_text(encoding="utf-8"))
    if c.get("schema_version")!=1 or c.get("status")!="Z4_PRODUCTION_BASELINE_PR12": fail("contrato Z4 no es PR12")
    if n.get("schema_version")!=2 or n.get("status")!="FROZEN_Z4_NETLIST_PR12_FOOTPRINTS_CLOSED_PR13" or n.get("footprint_audit_source")!="hardware/footprint_audit.json": fail("netlist Z4 no enlaza PR13")
    if audit.get("schema_version")!=3 or audit.get("status")!="FOOTPRINT_AUDIT_CLOSED_PR13": fail("audit no es PR13")
    if p.get("schema_version")!=6 or p.get("z4_contract_source_of_truth")!="hardware/z4_actuator_contract.json" or p.get("z4_netlist_source_of_truth")!="hardware/z4_production_netlist.json": fail("pin contract no enlaza Z4")
    if c["design_policy"]["placement_in_scope"] or c["design_policy"]["routing_in_scope"] or n["placement_in_scope"] or n["routing_in_scope"]: fail("PR12/13 no deben reescribir su alcance histórico")
    pins={int(x["pad"]):x for x in p["pins"]}
    expected={13:("PUMP_CURRENT_ADC","ACTIVE_ANALOG_DIAGNOSTIC"),20:("PUMP_PWM","ACTIVE"),21:("PUMP_DIR","ACTIVE"),22:("CO2_SOL_CTL","ACTIVE"),23:("CHILLER_CTL","ACTIVE_CONTROL_ONLY"),25:("ACT_FAULT_N","ACTIVE_DIAGNOSTIC")}
    for pad,(net,status) in expected.items():
        if (pins[pad].get("net"),pins[pad].get("status"))!=(net,status): fail(f"pad {pad} incorrecto")
    if pins[24].get("net") is not None or pins[24].get("status")!="DNP_RESERVE": fail("D9 debe permanecer DNP")
    if any(x.get("net")=="CO2_ADC" for x in p["pins"]): fail("CO2_ADC reapareció")
    pump=c["pump"]
    if pump["driver"]["mpn"]!="DRV8242HQRHLRQ1" or pump["driver"]["control_mode"]!="PH_EN": fail("driver bomba final incorrecto")
    cfg=pump["driver"]["configuration"]
    for key,val in {"MODE":"GND_LVL1_PH_EN","SR":"22k_to_GND_LVL3_approx_15_to_17_V_per_us","DIAG":"GND_LVL1_retry_offstate_diag_disabled","ITRIP":"GND_LVL1_internal_regulation_disabled","DRVOFF":"GND","nSLEEP":"3V3_RAIL","IPROPI":"ACTIVE_CURRENT_TELEMETRY"}.items():
        if cfg.get(key)!=val: fail(f"config bomba {key} cambió")
    t=pump["current_telemetry"]; r=float(t["r_ipropi_ohm"]); typ=float(t["a_ipropi_typ_a_per_a"]); amin=float(t["a_ipropi_min_top_range_a_per_a"]); inom=float(t["nominal_pump_a"])
    vnom=inom*r/typ; imax=3.05*amin/r
    if not close(vnom,t["nominal_adc_v_typ"],5e-4) or not close(imax,t["max_current_for_3p05v_using_min_ratio_a"],5e-4) or not (vnom<1.0 and imax>2.7): fail("cálculo IPROPI incorrecto")
    co=c["co2_solenoid"]
    if co["driver"]["mpn"]!="TPS1HC120CQDYCRQ1" or co["driver"]["variant"]!="C" or not co["driver"]["integrated_inductive_clamp"]: fail("driver CO2 final incorrecto")
    ilim=13.5/float(co["current_limit"]["r_ilim_ohm"])*1000.0
    if not close(ilim,0.5,1e-5) or co["driver"]["external_flyback_diode"]!="NOT_POPULATED_BASELINE": fail("CO2 ILIM/flyback cambió")
    ch=c["chiller"]
    if ch["photomos"]["mpn"]!="AQY212EHAX" or ch["interface"]!="ISOLATED_DRY_CONTACT_SELV_ONLY" or ch["power_on_pcba"] is not False or ch["mains_switching_allowed"] is not False: fail("frontera chiller incorrecta")
    if float(ch["max_recommended_external_contact_voltage_v"])>48 or float(ch["photomos"]["load_voltage_rating_v"])<60 or float(ch["photomos"]["io_isolation_vrms"])<5000: fail("rating PhotoMOS incorrecto")
    d=ch["input_driver"]; iworst=(3.3-1.5)/float(d["led_series_ohm"])*1000; ityp=(3.3-1.25)/float(d["led_series_ohm"])*1000
    if iworst<5.0-1e-6 or not close(ityp,d["led_current_ma_typ_vf1p25"],5e-3) or not close(iworst,d["led_current_ma_worst_vf1p5"],5e-3): fail("corriente LED PhotoMOS fuera de contrato")
    diag=c["diagnostic_bus"]
    if diag["net"]!="ACT_FAULT_N" or diag["uno_q_pad"]!=25 or diag["pullup_ohm"]!=10000: fail("bus diagnóstico incorrecto")
    comps={x["ref"]:x for x in n["components"]}; nets={x["name"]:set(x["nodes"]) for x in n["nets"]}
    for ref,x in comps.items():
        for pin,net in x["pins"].items():
            if net!="NC" and f"{ref}.{pin}" not in nets.get(net,set()): fail(f"{ref}.{pin} no aparece en {net}")
    with B.open(newline="",encoding="utf-8") as fh: rows=list(csv.DictReader(fh))
    if {x["ref"] for x in rows}!=set(comps) or len(rows)!=len(comps): fail("BOM Z4 != netlist")
    for x in comps.values():
        token=(str(x.get("value",""))+" "+str(x.get("mpn",""))).upper()
        if any(t.upper() in token for t in n["forbidden_production_tokens"]): fail(f"legacy activo en Z4: {x['ref']}")
    if "U_PUMP_DRV.17" not in nets["PUMP_CURRENT_ADC"] or "J_UNOQ.13" not in nets["PUMP_CURRENT_ADC"]: fail("IPROPI no llega a A4")
    if not {"U_PUMP_DRV.18","U_CO2_DRV.1","J_UNOQ.25"}<=nets["ACT_FAULT_N"]: fail("wired-OR fault incompleto")
    if comps["U_PUMP_DRV"]["pins"].get("21")!="GND" or "U_PUMP_DRV.21" not in nets["GND"]: fail("thermal pad 21 DRV8242 debe ir a GND")
    if "U_CHILLER.3" in nets.get("GND",set()) or "U_CHILLER.4" in nets.get("GND",set()) or "U_CHILLER.3" in nets.get("12V_ACT",set()) or "U_CHILLER.4" in nets.get("12V_ACT",set()): fail("contactos chiller no flotantes")
    expected_fp={"U_PUMP_DRV":"NFB:TI_RHL0020B_DRV8242","U_CO2_DRV":"NFB:TI_DYC0008A_TPS1HC120","U_CHILLER":"NFB:Panasonic_AQY212EHAX_DIP4_SMD"}
    for ref,fp in expected_fp.items():
        if comps[ref]["footprint"]!=fp: fail(f"{ref} no usa footprint PR13")
    if n.get("open_placement_gates")!=[]: fail("Z4 conserva gate de footprint abierto")
    a={x["id"]:x for x in audit["audits"]}
    for aid in ("DRV8242_RHL20","TPS1HC120_DYC8","AQY212EHAX_DIP4_SMD"):
        if a[aid]["placement_allowed"] is not True or not str(a[aid]["status"]).startswith("CLOSED_PRIMARY_SOURCE"): fail(f"audit {aid} no cerrado")
    pcb=PCB.read_text(encoding="utf-8"); placed=[r for r in comps if f'"{r}"' in pcb]
    phase=assert_authorized_phase(pcb,"Z4")
    if placed:
        if not PLACEMENT.exists(): fail(f"Z4 colocado sin manifest PR17: {placed[:5]}")
        pm=json.loads(PLACEMENT.read_text(encoding="utf-8"))
        if pm.get("status")!="PRODUCTION_PLACEMENT_PR17" or pm.get("policies",{}).get("routing_allowed") is not False: fail("Z4 colocado sin gate PR17 válido")
        pmap={x["ref"]:x for x in pm.get("placements",[])}
        bad=[ref for ref in placed if ref not in pmap or pmap[ref].get("zone")!="Z4"]
        if bad: fail(f"Z4 placement no trazado en manifest: {bad[:5]}")
    sch=S.read_text(encoding="utf-8")
    for m in ("PR #12","DRV8242HQRHLRQ1","TPS1HC120CQDYCRQ1","AQY212EHAX","PUMP_CURRENT_ADC","ACT_FAULT_N","NO MAINS"):
        if m not in sch: fail(f"schematic Z4 sin {m}")
    print(f"OK: Z4 PR12 + footprints PR13; placement PR17={len(placed)} refs, fase={phase}")
    print(f"- Pump telemetry: {vnom:.3f}V @0.8A; ~{imax:.2f}A at 3.05V worst scale")
    print("- RHL0020B/DYC0008A/AQY212EHAX cerrados contra fuentes primarias")
    return 0
if __name__=="__main__": raise SystemExit(main())
