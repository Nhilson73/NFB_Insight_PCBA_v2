#!/usr/bin/env python3
"""Gate de producción Z2 con potencia PR #9, contrato UNO Q schema v6 y placement PR17."""
from __future__ import annotations
import csv, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"hardware"/"z2_digital_contract.json"; NETLIST=ROOT/"hardware"/"z2_production_netlist.json"; PIN=ROOT/"hardware"/"insight_pin_contract.json"; Z1=ROOT/"hardware"/"z1_production_netlist.json"; POWER=ROOT/"hardware"/"power_architecture_contract.json"; BOM=ROOT/"bom"/"insight_z2_production_bom.csv"; SCH=ROOT/"kicad"/"z2_digital_contract.kicad_sch"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"; PLACEMENT=ROOT/"hardware"/"placement_manifest.json"
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for path in (CONTRACT,NETLIST,PIN,Z1,POWER,BOM,SCH,PCB):
        if not path.exists(): fail(f"falta {path.relative_to(ROOT)}")
    c=json.loads(CONTRACT.read_text(encoding="utf-8")); n=json.loads(NETLIST.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); z1=json.loads(Z1.read_text(encoding="utf-8")); power=json.loads(POWER.read_text(encoding="utf-8"))
    if c.get("schema_version")!=2 or c.get("status")!="Z2_PRODUCTION_BASELINE_PR7_POWER_LINKED_PR9": fail("contrato Z2 no refleja enlace de potencia PR9")
    if c.get("power_source_contract")!="hardware/power_architecture_contract.json": fail("contrato Z2 no enlaza potencia")
    if n.get("status")!="FROZEN_Z2_NETLIST_PR7_POWER_CORRECTED_PR9" or n.get("schema_version")!=2: fail("netlist Z2 no refleja corrección PR9")
    if n.get("power_source_contract")!="hardware/power_architecture_contract.json": fail("Z2 netlist no declara potencia")
    if p.get("schema_version")!=6 or p.get("power_architecture_source_of_truth")!="hardware/power_architecture_contract.json": fail("pin contract no enlaza PR9/PR12")
    if power.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9": fail("contrato potencia no es PR9")
    pins={int(x["pad"]):x for x in p["pins"]}
    for pad,net in {3:"MCU_NRST",15:"HMI_RX",16:"HMI_TX",17:"HX711_DOUT",18:"HX711_SCK",19:"MCU_WDI",28:"LED_STATUS",31:"I2C_SDA",32:"I2C_SCL"}.items():
        if pins[pad].get("net")!=net: fail(f"pad {pad} no conserva {net}")
    if pins[4].get("net") is not None or pins[5].get("net") is not None: fail("Z2 no debe tomar rails locales del host")
    if pins[8].get("net")!="12V_HOST_VIN": fail("VIN host no congelado")
    i2c=c["i2c"]; pu=i2c["pullups"]
    if pu["ohm"]!=4700 or pu["population"]!="POPULATE": fail("pull-ups I2C deben ser 4.7k")
    active={d["address_hex"].lower():d["device"] for d in i2c["devices"] if d["status"]=="ACTIVE"}
    if active!={"0x28":"MPRLS0030PA00002A","0x66":"DFR1103"}: fail(f"mapa I2C inesperado: {active}")
    gnss=c["gnss_rtc"]
    if gnss["module"]!="DFR1103" or gnss["i2c_address_hex"].lower()!="0x66": fail("GNSS/RTC final incorrecto")
    if gnss["connector"]["pinout"]!={"1":"I2C_SDA","2":"I2C_SCL","3":"GND","4":"3V3_RAIL"}: fail("J_GNSS_RTC incorrecto")
    hx=c["hx711"]
    if hx["part"]!="HX711" or hx["rate_sps"]!=10 or hx["gain_channel_a"]!=128: fail("HX711 baseline incorrecto")
    if hx["uno_q"]!={"dout_pad":17,"dout_net":"HX711_DOUT","sck_pad":18,"sck_net":"HX711_SCK"}: fail("pines HX711 cambiaron")
    hmi=c["hmi_uart"]; tr=hmi["translator"]
    if tr["mpn"]!="TXU0202DCUR": fail("traductor HMI incorrecto")
    if "TPSM33625RDNR" not in hmi.get("phase3_resolution","") or "1.5 A" not in hmi.get("phase3_resolution",""): fail("HMI no registra resolución de potencia PR9")
    wdt=c["watchdog"]
    if wdt["mpn"]!="TPS3823-30DBVR" or float(wdt["watchdog_timeout_s"])!=1.6: fail("watchdog incorrecto")
    comps={x["ref"]:x for x in n["components"]}; net_nodes={x["name"]:set(x["nodes"]) for x in n["nets"]}
    for ref,comp in comps.items():
        for pin,net in comp["pins"].items():
            if net=="NC": continue
            node=f"{ref}.{pin}"
            if node not in net_nodes.get(net,set()): fail(f"{node} no aparece en {net}")
    if "J_UNOQ.4" in net_nodes.get("3V3_RAIL",set()) or "J_UNOQ.5" in net_nodes.get("5V_RAIL",set()): fail("rails Z2 unidos al host")
    for comp in comps.values():
        token=(str(comp.get("value",""))+" "+str(comp.get("mpn",""))).upper()
        if any(x.upper() in token for x in n["forbidden_production_tokens"]): fail(f"bloque legacy activo: {comp['ref']}")
    with BOM.open(newline="",encoding="utf-8") as fh: rows=list(csv.DictReader(fh))
    if {r["ref"] for r in rows}!=set(comps) or len(rows)!=len(comps): fail("BOM Z2 != netlist Z2")
    if not set(c["testpoints"])<=set(comps): fail("faltan test points Z2")
    z1c={x["ref"]:x for x in z1["components"]}
    for ref in ("R_CO2_SDA_PU","R_CO2_SCL_PU"):
        if z1c[ref]["population"]!="DNP" or z1c[ref]["value"]!="10k": fail(f"{ref} debe ser 10k DNP")
    sch=SCH.read_text(encoding="utf-8")
    for marker in ("PR #7","Z2 DIGITAL / BAJO RUIDO","DFR1103","0x66","HX711_DOUT","HX711_SCK","TXU0202DCUR","TPS3823-30DBVR"):
        if marker not in sch: fail(f"schematic Z2 sin {marker}")
    for ref in comps:
        if ref not in sch: fail(f"schematic Z2 no indexa {ref}")
    pcb=PCB.read_text(encoding="utf-8"); placed=[ref for ref in comps if f'"{ref}"' in pcb]
    if placed:
        if not PLACEMENT.exists(): fail(f"Z2 colocado sin manifest PR17: {placed[:5]}")
        pm=json.loads(PLACEMENT.read_text(encoding="utf-8"))
        if pm.get("status")!="PRODUCTION_PLACEMENT_PR17" or pm.get("policies",{}).get("routing_allowed") is not False: fail("Z2 colocado sin gate PR17 válido")
        pmap={x["ref"]:x for x in pm.get("placements",[])}
        bad=[ref for ref in placed if ref not in pmap or pmap[ref].get("zone")!="Z2"]
        if bad: fail(f"Z2 placement no trazado en manifest: {bad[:5]}")
        if re.search(r'^\s*\((segment|arc|via|zone)\b',pcb,re.M): fail("PR17: Z2 contiene routing/cobre prematuro")
    print(f"OK: Z2 PR #7 preservado; placement PR17={len(placed)} refs, routing=0")
    return 0
if __name__=="__main__": raise SystemExit(main())
