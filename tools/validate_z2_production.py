#!/usr/bin/env python3
"""Gate de producción Z2 con corrección de potencia PR #9."""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "hardware" / "z2_digital_contract.json"
NETLIST = ROOT / "hardware" / "z2_production_netlist.json"
PIN = ROOT / "hardware" / "insight_pin_contract.json"
Z1 = ROOT / "hardware" / "z1_production_netlist.json"
POWER = ROOT / "hardware" / "power_architecture_contract.json"
BOM = ROOT / "bom" / "insight_z2_production_bom.csv"
SCH = ROOT / "kicad" / "z2_digital_contract.kicad_sch"
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"

def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)

def main() -> int:
    for path in (CONTRACT, NETLIST, PIN, Z1, POWER, BOM, SCH, PCB):
        if not path.exists(): fail(f"falta {path.relative_to(ROOT)}")
    c=json.loads(CONTRACT.read_text(encoding="utf-8")); n=json.loads(NETLIST.read_text(encoding="utf-8")); p=json.loads(PIN.read_text(encoding="utf-8")); z1=json.loads(Z1.read_text(encoding="utf-8")); power=json.loads(POWER.read_text(encoding="utf-8"))
    if c.get("status") != "Z2_PRODUCTION_BASELINE_PR7": fail("contrato Z2 no es baseline PR7")
    if n.get("status") != "FROZEN_Z2_NETLIST_PR7_POWER_CORRECTED_PR9": fail("netlist Z2 no refleja corrección PR9")
    if n.get("schema_version") != 2: fail("netlist Z2 no es schema v2")
    if n.get("power_source_contract") != "hardware/power_architecture_contract.json": fail("Z2 no declara contrato de potencia")
    if p.get("schema_version") != 5: fail("pin contract no es schema v5")
    if p.get("z2_contract_source_of_truth") != "hardware/z2_digital_contract.json": fail("pin contract no declara contrato Z2")
    if p.get("z2_netlist_source_of_truth") != "hardware/z2_production_netlist.json": fail("pin contract no declara netlist Z2")
    if p.get("power_architecture_source_of_truth") != "hardware/power_architecture_contract.json": fail("pin contract no declara potencia")
    if power.get("status") != "POWER_ARCHITECTURE_BASELINE_PR9": fail("contrato potencia no es PR9")
    pins={int(x["pad"]):x for x in p["pins"]}
    expected={3:"MCU_NRST",15:"HMI_RX",16:"HMI_TX",17:"HX711_DOUT",18:"HX711_SCK",19:"MCU_WDI",28:"LED_STATUS",31:"I2C_SDA",32:"I2C_SCL"}
    for pad,net in expected.items():
        if pins[pad].get("net")!=net: fail(f"pad {pad} no conserva {net}")
    if pins[4].get("net") is not None or pins[5].get("net") is not None: fail("Z2 no debe tomar rails locales del host")
    if pins[8].get("net")!="12V_HOST_VIN": fail("VIN host no congelado")
    i2c=c["i2c"]; pu=i2c["pullups"]
    if pu["ohm"]!=4700 or pu["population"]!="POPULATE": fail("pull-ups globales I2C deben ser 4.7k poblados")
    active={d["address_hex"].lower():d["device"] for d in i2c["devices"] if d["status"]=="ACTIVE"}
    if active!={"0x28":"MPRLS0030PA00002A","0x66":"DFR1103"}: fail(f"mapa I2C activo inesperado: {active}")
    if {"0x42","0x68"}&set(active): fail("direcciones GPS/RTC legacy siguen activas")
    gnss=c["gnss_rtc"]
    if gnss["module"]!="DFR1103" or gnss["i2c_address_hex"].lower()!="0x66": fail("GNSS/RTC final no es DFR1103 0x66")
    if gnss["connector"]["pinout"]!={"1":"I2C_SDA","2":"I2C_SCL","3":"GND","4":"3V3_RAIL"}: fail("pinout J_GNSS_RTC incorrecto")
    if set(gnss["supersedes"])!={"GPS_SAM-M8Q_0x42","RTC_DS3231_0x68"}: fail("DFR1103 no supersede ambos módulos legacy")
    hx=c["hx711"]
    if hx["part"]!="HX711" or hx["supply_mode"]!="EXTERNAL_3V3_NO_INTERNAL_REGULATOR": fail("baseline HX711 incorrecto")
    if hx["rate_sps"]!=10 or hx["gain_channel_a"]!=128: fail("HX711 debe quedar a 10 SPS / gain 128")
    if hx["uno_q"]!={"dout_pad":17,"dout_net":"HX711_DOUT","sck_pad":18,"sck_net":"HX711_SCK"}: fail("pines UNO Q de HX711 cambiaron")
    expected_hx={"1":"3V3_RAIL","2":"NC","3":"3V3_RAIL","4":"GND","5":"GND","6":"HX_VBG","7":"LOAD_A_NEG","8":"LOAD_A_POS","9":"NC","10":"NC","11":"HX711_SCK","12":"HX711_DOUT","13":"NC","14":"GND","15":"GND","16":"3V3_RAIL"}
    if hx["pinout"]!=expected_hx: fail("pinout HX711 no coincide con baseline")
    hmi=c["hmi_uart"]; tr=hmi["translator"]
    if tr["mpn"]!="TXU0202DCUR": fail("traductor HMI no es TXU0202DCUR")
    expected_txu={"1":"HMI_FIELD_TX","2":"GND","3":"3V3_RAIL","4":"HMI_RX","5":"HMI_TX","6":"3V3_RAIL","7":"5V_RAIL","8":"HMI_FIELD_RX"}
    if tr["pinout"]!=expected_txu: fail("pinout TXU0202 incorrecto")
    if hmi["connector"]["pinout"]!={"1":"5V_RAIL","2":"GND","3":"HMI_FIELD_RX","4":"HMI_FIELD_TX"}: fail("pinout J_HMI incorrecto")
    if hmi["esd"]["mpn"]!="PESD5V0U1UL,315" or hmi["esd"]["common_net"]!="GND": fail("ESD HMI no congelado a GND")
    wdt=c["watchdog"]
    if wdt["mpn"]!="TPS3823-30DBVR" or float(wdt["watchdog_timeout_s"])!=1.6: fail("watchdog final incorrecto")
    if int(wdt["firmware_feed_interval_ms"])!=400: fail("feed watchdog debe conservar 400 ms")
    if wdt["pinout"]!={"1":"MCU_NRST","2":"GND","3":"WDT_MR_N","4":"MCU_WDI","5":"3V3_RAIL"}: fail("pinout watchdog incorrecto")
    comps={x["ref"]:x for x in n["components"]}; net_nodes={x["name"]:set(x["nodes"]) for x in n["nets"]}
    for ref,comp in comps.items():
        for pin,net in comp["pins"].items():
            if net=="NC": continue
            node=f"{ref}.{pin}"
            if net not in net_nodes or node not in net_nodes[net]: fail(f"{node} no aparece en net {net}")
    if "J_UNOQ.4" in net_nodes.get("3V3_RAIL",set()): fail("3V3_RAIL Z2 unido al host")
    if "J_UNOQ.5" in net_nodes.get("5V_RAIL",set()): fail("5V_RAIL Z2 unido al host")
    forbidden=tuple(n["forbidden_production_tokens"])
    for comp in comps.values():
        token=(str(comp.get("value",""))+" "+str(comp.get("mpn",""))).upper()
        if any(x.upper() in token for x in forbidden): fail(f"bloque legacy/Signature activo en Z2: {comp['ref']}")
    with BOM.open(newline="",encoding="utf-8") as fh: rows=list(csv.DictReader(fh))
    if {r["ref"] for r in rows}!=set(comps): fail("refs BOM Z2 != refs netlist Z2")
    if len(rows)!=len(comps): fail("BOM Z2 contiene refs duplicadas")
    required_tps=set(c["testpoints"])
    if not required_tps<=set(comps): fail("faltan test points de bring-up")
    z1c={x["ref"]:x for x in z1["components"]}
    for ref in ("R_CO2_SDA_PU","R_CO2_SCL_PU"):
        if z1c[ref]["population"]!="DNP" or z1c[ref]["value"]!="10k": fail(f"{ref} debe permanecer 10k DNP")
    sch=SCH.read_text(encoding="utf-8")
    for marker in ("PR #7","Z2 DIGITAL / BAJO RUIDO","DFR1103","0x66","HX711_DOUT","HX711_SCK","TXU0202DCUR","TPS3823-30DBVR"):
        if marker not in sch: fail(f"schematic Z2 sin marcador {marker}")
    for ref in comps:
        if ref not in sch: fail(f"schematic Z2 no indexa {ref}")
    pcb=PCB.read_text(encoding="utf-8"); placed=[ref for ref in comps if f'"{ref}"' in pcb]
    if placed: fail(f"PR7/9 no debe colocar Z2 en PCB todavía: {placed[:5]}")
    print("OK: Z2 PR #7 preservado + power correction PR #9")
    print("- I2C: MPR 0x28 + DFR1103 0x66; HX711/HMI/WDT intactos")
    print("- 3V3_RAIL/5V_RAIL son locales al shield; no J_UNOQ.4/.5")
    print(f"- {len(comps)} refs Z2; BOM/netlist coinciden; placement PCB = 0")
    return 0

if __name__=="__main__": raise SystemExit(main())
