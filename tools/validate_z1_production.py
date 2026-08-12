#!/usr/bin/env python3
"""Gate Z1: preserva sensores PR6, potencia PR9, cierre físico PR13 y reasignación A4 PR12."""
from __future__ import annotations
import csv, json, math, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SENSOR=ROOT/"hardware"/"sensor_interface_contract.json"; NETLIST=ROOT/"hardware"/"z1_production_netlist.json"; PIN=ROOT/"hardware"/"insight_pin_contract.json"; POWER=ROOT/"hardware"/"power_architecture_contract.json"; AUDIT=ROOT/"hardware"/"footprint_audit.json"; Z4=ROOT/"hardware"/"z4_actuator_contract.json"; BOM=ROOT/"bom"/"insight_z1_production_bom.csv"; SCH=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_sch"; MPR_FP=ROOT/"kicad"/"lib"/"nfb_footprints.pretty"/"Honeywell_MPR_LongPort_12Pad.kicad_mod"
def fail(m): raise SystemExit("ERROR: "+m)
def close(a,b,tol=1e-6): return math.isclose(float(a),float(b),rel_tol=tol,abs_tol=tol)
def main():
    for x in (SENSOR,NETLIST,PIN,POWER,AUDIT,Z4,BOM,SCH,MPR_FP):
        if not x.exists(): fail(f"falta {x.relative_to(ROOT)}")
    s=json.loads(SENSOR.read_text(encoding="utf-8")); n=json.loads(NETLIST.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); power=json.loads(POWER.read_text(encoding="utf-8")); audit=json.loads(AUDIT.read_text(encoding="utf-8")); z4=json.loads(Z4.read_text(encoding="utf-8"))
    if s.get("status")!="Z1_PRODUCTION_BASELINE_PR6" or n.get("status")!="FROZEN_Z1_NETLIST_PR6_POWER_CORRECTED_PR9": fail("baseline Z1 cambió")
    if n.get("schema_version")!=2 or n.get("power_source_contract")!="hardware/power_architecture_contract.json": fail("netlist Z1 no refleja potencia PR9")
    if p.get("schema_version")!=6: fail("pin contract no es schema v6")
    if power.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9": fail("contrato potencia no es PR9")
    if audit.get("schema_version")!=3 or audit.get("status")!="FOOTPRINT_AUDIT_CLOSED_PR13": fail("audit footprints no es cierre PR13")
    if z4.get("status")!="Z4_PRODUCTION_BASELINE_PR12": fail("Z4 no es PR12")
    aud={x["id"]:x for x in audit["audits"]}; mpr_a=aud.get("MPR_LONG_PORT_12PAD",{})
    if mpr_a.get("status")!="CLOSED_PRIMARY_DATASHEET" or mpr_a.get("placement_allowed") is not True or mpr_a.get("verified_geometry",{}).get("recommended_layout_outer_span_mm")!=4.20: fail("MPR audit no cerrado")
    ch={x["id"]:x for x in s["channels"]}
    if set(ch)!={"PH","ORP","TEMP","CO2","DO"}: fail("canales Z1 incorrectos")
    co2=ch["CO2"]
    if co2["sensor"]!="MPRLS0030PA00002A" or co2["interface_class"]!="ONBOARD_DIGITAL_PRESSURE_I2C" or co2["electrical"]["i2c_address_hex"].lower()!="0x28": fail("CO2 final incorrecto")
    expected_kpa=30.0*6.894757293168361
    if float(co2["pressure"]["max_kpa"])<=180 or not close(co2["pressure"]["max_kpa"],expected_kpa,1e-7): fail("rango MPR incorrecto")
    if co2["legacy"]["status"]!="REMOVED_FROM_PRODUCTION": fail("MPX5700 no retirado")
    pins={int(x["pad"]):x for x in p["pins"]}
    if pins[13].get("net")!="PUMP_CURRENT_ADC" or pins[13].get("status")!="ACTIVE_ANALOG_DIAGNOSTIC": fail("A4 debe ser PUMP_CURRENT_ADC")
    if pins[31].get("net")!="I2C_SDA" or pins[32].get("net")!="I2C_SCL": fail("bus I2C incorrecto")
    if pins[4].get("net") is not None or pins[5].get("net") is not None: fail("rails locales unidos al host")
    if "CO2_ADC" in {x.get("net") for x in p["pins"]}: fail("CO2_ADC reapareció")
    for name in ("PH","DO"):
        cc=ch[name]
        if max(cc["conditioned_output_v"])>3.05 or cc["filter"]["series_ohm"]!=1000 or not close(cc["filter"]["cap_f"],1e-7): fail(f"{name} baseline cambió")
    d=ch["ORP"]["divider"]
    if (d["top_ohm"],d["bottom_ohm"])!=(10000,20000) or not close(d["input_max_v"]*d["bottom_ohm"]/(d["top_ohm"]+d["bottom_ohm"]),3.0): fail("ORP divisor cambió")
    if ch["TEMP"]["pullup"]["population"]!="POPULATE" or ch["TEMP"]["pullup"]["ohm"]!=4700: fail("TEMP pull-up cambió")
    cp=s["common_parts"]
    if cp["field_connector"]["mpn"]!="S3B-XH-A(LF)(SN)" or cp["signal_esd"]["mpn"]!="PESD3V3U1UL,315" or cp["filter_cap"]["mpn"]!="GRM155R71E104KE14D": fail("common parts Z1 cambiaron")
    comps={x["ref"]:x for x in n["components"]}; nets={x["name"]:set(x["nodes"]) for x in n["nets"]}
    for ref,c in comps.items():
        for pin,net in c["pins"].items():
            if net!="NC" and f"{ref}.{pin}" not in nets.get(net,set()): fail(f"{ref}.{pin} no aparece en {net}")
    if "J_UNOQ.4" in nets.get("3V3_RAIL",set()) or "J_UNOQ.5" in nets.get("5V_RAIL",set()): fail("back-feed Z1")
    for c in comps.values():
        token=(str(c.get("value",""))+" "+str(c.get("mpn",""))).upper()
        if any(x in token for x in ("BNC","MPX5700AP","SN6501","AMC1301","750315371")): fail(f"legacy en Z1 {c['ref']}")
    with BOM.open(newline="",encoding="utf-8") as fh: rows=list(csv.DictReader(fh))
    if {r["ref"] for r in rows}!=set(comps): fail("BOM Z1 != netlist")
    fp=MPR_FP.read_text(encoding="utf-8"); pads={int(x) for x in re.findall(r'\(pad "(\d+)" smd',fp)}
    if pads!=set(range(1,13)): fail("footprint MPR incompleto")
    for marker in ('(at 1.27 1.775)','(at -1.775 -1.27)','HONEYWELL 32332628 ISSUE L FIG.10'):
        if marker not in fp: fail(f"MPR sin {marker}")
    print("OK: Z1 preservado bajo cierre físico PR13; A4=PUMP_CURRENT_ADC y CO2 sigue I2C")
    return 0
if __name__=="__main__": raise SystemExit(main())
