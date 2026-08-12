#!/usr/bin/env python3
"""Gate de producción Z1 con corrección de potencia PR #9 y audit físico PR #11."""
from __future__ import annotations
import csv, json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENSOR = ROOT / "hardware" / "sensor_interface_contract.json"
NETLIST = ROOT / "hardware" / "z1_production_netlist.json"
PIN = ROOT / "hardware" / "insight_pin_contract.json"
POWER = ROOT / "hardware" / "power_architecture_contract.json"
AUDIT = ROOT / "hardware" / "footprint_audit.json"
BOM = ROOT / "bom" / "insight_z1_production_bom.csv"
SCH = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_sch"
MPR_FP = ROOT / "kicad" / "lib" / "nfb_footprints.pretty" / "Honeywell_MPR_LongPort_12Pad.kicad_mod"

def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)

def close(a,b,tol=1e-6):
    return math.isclose(float(a),float(b),rel_tol=tol,abs_tol=tol)

def main() -> int:
    for p in (SENSOR,NETLIST,PIN,POWER,AUDIT,BOM,SCH,MPR_FP):
        if not p.exists(): fail(f"falta {p.relative_to(ROOT)}")
    s=json.loads(SENSOR.read_text(encoding="utf-8")); n=json.loads(NETLIST.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); power=json.loads(POWER.read_text(encoding="utf-8")); audit=json.loads(AUDIT.read_text(encoding="utf-8"))
    if s.get("status")!="Z1_PRODUCTION_BASELINE_PR6": fail("sensor contract no es PR6")
    if n.get("status")!="FROZEN_Z1_NETLIST_PR6_POWER_CORRECTED_PR9": fail("netlist Z1 no refleja corrección PR9")
    if n.get("schema_version")!=2: fail("netlist Z1 no es schema v2")
    if n.get("power_source_contract")!="hardware/power_architecture_contract.json": fail("Z1 no declara contrato de potencia")
    if p.get("schema_version")!=5: fail("pin contract no es schema v5")
    if power.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9": fail("contrato potencia no es PR9")
    if audit.get("status")!="FOOTPRINT_AUDIT_BASELINE_PR11": fail("audit de footprints no es PR11")
    aud={x["id"]:x for x in audit["audits"]}
    mpr_a=aud.get("MPR_LONG_PORT_12PAD",{})
    if mpr_a.get("status")!="CLOSED_PRIMARY_DATASHEET" or mpr_a.get("placement_allowed") is not True: fail("MPR no está cerrado por auditoría PR11")
    if mpr_a.get("verified_geometry",{}).get("recommended_layout_outer_span_mm")!=4.20: fail("audit MPR no congela span 4.20 mm")
    ch={x["id"]:x for x in s["channels"]}
    if set(ch)!={"PH","ORP","TEMP","CO2","DO"}: fail("canales Z1 incorrectos")
    co2=ch["CO2"]
    if co2["sensor"]!="MPRLS0030PA00002A": fail("sensor CO2 no es MPRLS0030PA00002A")
    if co2["interface_class"]!="ONBOARD_DIGITAL_PRESSURE_I2C": fail("CO2 no es I2C")
    if co2["electrical"]["i2c_address_hex"].lower()!="0x28": fail("dirección MPR debe ser 0x28")
    if float(co2["pressure"]["max_kpa"]) <= 180.0: fail("rango CO2 no cubre emergencia firmware 180 kPa")
    expected_kpa=30.0*6.894757293168361
    if not close(co2["pressure"]["max_kpa"],expected_kpa,1e-7): fail("conversión 30 psi a kPa incorrecta")
    if co2["pinout"] != {"1":"NC","2":"I2C_SDA","3":"I2C_SCL","4":"NC_DIGITAL_ONLY","5":"NC","6":"NC_DIGITAL_ONLY","7":"NC","8":"NC_OPTIONAL_EOC","9":"NC_OPTIONAL_RES","10":"GND","11":"NC","12":"3V3_RAIL"}: fail("pinout MPR no coincide con baseline I2C")
    if co2["legacy"]["status"]!="REMOVED_FROM_PRODUCTION": fail("MPX5700 no fue retirado")
    pins={int(x["pad"]):x for x in p["pins"]}
    if pins[13].get("net") is not None or pins[13].get("status")!="DNP_RESERVE": fail("A4 debe quedar DNP/Reserva")
    if pins[31].get("net")!="I2C_SDA" or pins[32].get("net")!="I2C_SCL": fail("bus I2C UNO Q incorrecto")
    if pins[4].get("net") is not None or pins[5].get("net") is not None: fail("Z1 no debe tomar rails locales del host")
    active={x.get("net") for x in p["pins"] if str(x.get("status","")).startswith("ACTIVE")}
    if "CO2_ADC" in active: fail("CO2_ADC reapareció activo")
    for name in ("PH","DO"):
        c=ch[name]
        if max(c["conditioned_output_v"])>3.05: fail(f"{name} excede objetivo ADC")
        if c["filter"]["series_ohm"]!=1000 or not close(c["filter"]["cap_f"],1e-7): fail(f"{name} RC no congelado 1k/100n")
        fc=1/(2*math.pi*1000*1e-7)
        if not close(c["filter"]["cutoff_hz"],fc,1e-7): fail(f"{name} fc incorrecta")
    orp=ch["ORP"]; d=orp["divider"]
    if (d["top_ohm"],d["bottom_ohm"])!=(10000,20000): fail("ORP divisor no es 10k/20k")
    if not close(d["input_max_v"]*d["bottom_ohm"]/(d["top_ohm"]+d["bottom_ohm"]),3.0): fail("ORP no escala a 3.0 V")
    if orp["protection"]["placement_net"]!="ORP_ADC": fail("ESD ORP debe estar después del divisor")
    temp=ch["TEMP"]
    if temp["pullup"]["population"]!="POPULATE" or temp["pullup"]["ohm"]!=4700: fail("TEMP requiere 4.7k onboard poblado")
    cp=s["common_parts"]
    if cp["field_connector"]["mpn"]!="S3B-XH-A(LF)(SN)": fail("conector de campo no congelado")
    if cp["field_connector"]["footprint"]!="Connector_JST:JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal": fail("footprint JST incorrecto")
    if cp["signal_esd"]["mpn"]!="PESD3V3U1UL,315": fail("ESD no congelado")
    if cp["filter_cap"]["mpn"]!="GRM155R71E104KE14D": fail("100nF no congelado")
    comps={x["ref"]:x for x in n["components"]}; net_nodes={x["name"]:set(x["nodes"]) for x in n["nets"]}
    for ref,c in comps.items():
        for pin,net in c["pins"].items():
            if net=="NC": continue
            node=f"{ref}.{pin}"
            if net not in net_nodes or node not in net_nodes[net]: fail(f"nodo {node} no aparece en net {net}")
    if "J_UNOQ.4" in net_nodes.get("3V3_RAIL",set()): fail("3V3_RAIL Z1 unido al host")
    if "J_UNOQ.5" in net_nodes.get("5V_RAIL",set()): fail("5V_RAIL Z1 unido al host")
    forbidden=("BNC","MPX5700AP","SN6501","AMC1301","750315371")
    for c in comps.values():
        token=(str(c.get("value",""))+" "+str(c.get("mpn",""))).upper()
        if any(x.upper() in token for x in forbidden): fail(f"componente legacy en producción: {c['ref']}")
    with BOM.open(newline="",encoding="utf-8") as fh: rows=list(csv.DictReader(fh))
    if {r["ref"] for r in rows} != set(comps): fail("refs BOM != refs netlist")
    if any("BNC" in (r["valor"]+" "+r["mpn_o_familia"]).upper() for r in rows): fail("BOM contiene BNC")
    if not any(r["ref"]=="U_CO2" and r["mpn_o_familia"]=="MPRLS0030PA00002A" for r in rows): fail("BOM sin U_CO2 final")
    fp=MPR_FP.read_text(encoding="utf-8"); pads={int(x) for x in re.findall(r'\(pad "(\d+)" smd',fp)}
    if pads != set(range(1,13)): fail("footprint MPR no tiene pads 1..12")
    for marker in ('(at 1.27 1.775)','(at -1.775 -1.27)','(at -1.775 1.27)','HONEYWELL 32332628 ISSUE L FIG.10'):
        if marker not in fp: fail(f"footprint MPR sin geometría/trazabilidad PR11 esperada {marker}")
    sch=SCH.read_text(encoding="utf-8")
    for ref in comps:
        if f'"{ref}"' not in sch: fail(f"schematic no contiene {ref}")
    for marker in ("MPRLS0030PA00002A","I2C_SDA","I2C_SCL","TEMP_1WIRE","A4/CO2_ADC DNP"):
        if marker not in sch: fail(f"schematic sin marcador {marker}")
    print("OK: Z1 PR #6 + power PR #9 + footprint audit PR #11")
    print(f"- CO2: MPRLS0030PA00002A I2C 0x28, 0-30 psi abs = {expected_kpa:.3f} kPa")
    print("- MPR footprint cerrado contra Honeywell Issue L Fig.10, span 4.20 mm")
    print("- 3V3_RAIL/5V_RAIL son locales al shield; no J_UNOQ.4/.5")
    print(f"- {len(comps)} placements Z1; BOM y netlist coinciden")
    return 0

if __name__=="__main__": raise SystemExit(main())
