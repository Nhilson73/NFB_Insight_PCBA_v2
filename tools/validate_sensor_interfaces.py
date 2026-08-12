#!/usr/bin/env python3
"""Valida interfaces de sensores PR #6 preservadas tras potencia PR #9 y reutilización A4 PR #12."""
from __future__ import annotations
import json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"hardware"/"sensor_interface_contract.json"
PIN=ROOT/"hardware"/"insight_pin_contract.json"
NETLIST=ROOT/"hardware"/"z1_production_netlist.json"
Z4=ROOT/"hardware"/"z4_actuator_contract.json"
def fail(m): raise SystemExit("ERROR: "+m)
def close(a,b,t=1e-6): return math.isclose(float(a),float(b),rel_tol=t,abs_tol=t)
def main():
    s=json.loads(CONTRACT.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); n=json.loads(NETLIST.read_text(encoding="utf-8")); z4=json.loads(Z4.read_text(encoding="utf-8"))
    if s.get("status")!="Z1_PRODUCTION_BASELINE_PR6": fail("baseline sensores no es PR6")
    if p.get("schema_version")!=6: fail("pin contract no es schema v6")
    if z4.get("status")!="Z4_PRODUCTION_BASELINE_PR12": fail("Z4 no es baseline PR12")
    ch={c["id"]:c for c in s["channels"]}
    if set(ch)!={"PH","ORP","TEMP","CO2","DO"}: fail("deben existir cinco funciones de sensor")
    if ch["PH"]["net"]!="PH_ADC" or ch["DO"]["net"]!="DO_ADC" or ch["ORP"]["net"]!="ORP_ADC": fail("nets analógicas Z1 cambiaron")
    if ch["TEMP"]["net"]!="TEMP_1WIRE" or ch["TEMP"]["interface_class"]!="DIGITAL_1WIRE": fail("TEMP no es 1-Wire")
    if ch["CO2"]["sensor"]!="MPRLS0030PA00002A" or ch["CO2"]["electrical"]["i2c_address_hex"].lower()!="0x28": fail("CO2 final incorrecto")
    if ch["CO2"]["interface_class"]!="ONBOARD_DIGITAL_PRESSURE_I2C": fail("CO2 debe ser digital I2C")
    by={int(x["pad"]):x for x in p["pins"]}
    if by[13]["net"]!="PUMP_CURRENT_ADC" or by[13]["status"]!="ACTIVE_ANALOG_DIAGNOSTIC": fail("A4 debe estar reutilizado exclusivamente como telemetría de bomba PR12")
    if "CO2_ADC" in {x.get("net") for x in p["pins"]}: fail("CO2_ADC no puede reaparecer al reutilizar A4")
    if z4["pump"]["uno_q"]["current_adc"]!={"pad":13,"arduino":"A4","net":"PUMP_CURRENT_ADC"}: fail("Z4 no gobierna correctamente A4")
    if by[31]["net"]!="I2C_SDA" or by[32]["net"]!="I2C_SCL": fail("MPR requiere bus D20/D21")
    if by[11]["net"]!="TEMP_1WIRE": fail("A2/D16 debe ser TEMP_1WIRE")
    if by[4]["net"] is not None or by[5]["net"] is not None: fail("rails locales de sensores no deben depender de salida host")
    if max(ch["PH"]["conditioned_output_v"])>3.05 or max(ch["DO"]["conditioned_output_v"])>3.05: fail("pH/DO exceden dominio")
    d=ch["ORP"]["divider"]
    if not close(d["input_max_v"]*d["bottom_ohm"]/(d["top_ohm"]+d["bottom_ohm"]),3.0): fail("ORP no escala a 3.0V")
    if ch["TEMP"]["pullup"]["population"]!="POPULATE": fail("pull-up 1-Wire debe poblarse")
    if n.get("status")!="FROZEN_Z1_NETLIST_PR6_POWER_CORRECTED_PR9": fail("netlist Z1 no refleja corrección PR9")
    nets={x["name"]:set(x["nodes"]) for x in n["nets"]}
    if "J_UNOQ.4" in nets.get("3V3_RAIL",set()) or "J_UNOQ.5" in nets.get("5V_RAIL",set()): fail("sensor rails quedaron unidos al host")
    print("OK: interfaces sensores PR #6 preservadas + A4 reasignado a Z4 PR #12")
    print("- pH/ORP/DO acondicionados, TEMP 1-Wire, CO2 MPR I2C 0x28")
    print("- A4 ya no es CO2: PUMP_CURRENT_ADC")
    return 0
if __name__=="__main__": raise SystemExit(main())
