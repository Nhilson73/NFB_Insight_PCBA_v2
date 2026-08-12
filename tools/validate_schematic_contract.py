#!/usr/bin/env python3
"""Valida contrato UNO Q, Z1 y esquemático KiCad después de PR #6."""
from __future__ import annotations
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN=ROOT/"hardware"/"insight_pin_contract.json"; SENSOR=ROOT/"hardware"/"sensor_interface_contract.json"; NETLIST=ROOT/"hardware"/"z1_production_netlist.json"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"; SCH=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_sch"
FW="cf100b38df890f61aed472e934241e145425569b"
EXPECTED={9:("A0","PH_ADC","ACTIVE"),10:("A1","ORP_ADC","ACTIVE"),11:("A2/D16","TEMP_1WIRE","ACTIVE_DIGITAL"),12:("A3",None,"DNP_RESERVE"),13:("A4",None,"DNP_RESERVE"),14:("A5","DO_ADC","ACTIVE"),17:("D2","HX711_DOUT","ACTIVE"),18:("D3","HX711_SCK","ACTIVE"),19:("D4","MCU_WDI","ACTIVE"),20:("D5","PUMP_PWM","ACTIVE"),21:("D6","PUMP_DIR","ACTIVE"),22:("D7","CO2_SOL_CTL","ACTIVE"),23:("D8","CHILLER_CTL","ACTIVE_CONTROL_ONLY"),24:("D9",None,"DNP_RESERVE"),25:("D10","RS485_IRQ_RSVD","RESERVE"),31:("D20/SDA","I2C_SDA","ACTIVE"),32:("D21/SCL","I2C_SCL","ACTIVE")}
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for f in (PIN,SENSOR,NETLIST,PCB,SCH):
        if not f.exists(): fail(f"falta {f.relative_to(ROOT)}")
    p=json.loads(PIN.read_text(encoding="utf-8"))
    if p.get("schema_version")!=3: fail("pin contract no es schema v3")
    if p["firmware_reference"]["commit"]!=FW: fail("snapshot firmware cambió")
    if p.get("z1_netlist_source_of_truth")!="hardware/z1_production_netlist.json": fail("falta declarar netlist Z1")
    pins={int(x["pad"]):x for x in p["pins"]}
    if set(pins)!=set(range(1,33)): fail("contrato no contiene pads 1..32")
    for pad,e in EXPECTED.items():
        a=pins[pad]; got=(a.get("arduino"),a.get("net"),a.get("status"))
        if got!=e: fail(f"pad {pad}: {got} != {e}")
    active={x.get("net") for x in p["pins"] if str(x.get("status","")).startswith("ACTIVE")}
    bad={"TEMP_ADC","CO2_ADC","HUM_ADC","CO2_PWM","CO2_FLOW_PWM"} & active
    if bad: fail(f"nets prohibidas activas: {sorted(bad)}")
    s=json.loads(SENSOR.read_text(encoding="utf-8")); co2={c["id"]:c for c in s["channels"]}["CO2"]
    if co2["electrical"]["sda_net"]!="I2C_SDA" or co2["electrical"]["scl_net"]!="I2C_SCL": fail("MPR no enlaza al I2C contractual")
    if co2["electrical"]["i2c_address_hex"].lower()!="0x28": fail("MPR no usa 0x28")
    pcb=PCB.read_text(encoding="utf-8"); physical={int(x) for x in re.findall(r'\(pad "(\d+)" thru_hole',pcb)}
    if set(range(1,33))-physical: fail("faltan pads físicos UNO Q")
    sch=SCH.read_text(encoding="utf-8")
    for marker in ("J_UNOQ","MPRLS0030PA00002A","I2C_SDA","I2C_SCL","TEMP_1WIRE","A4/CO2_ADC DNP"):
        if marker not in sch: fail(f"schematic sin {marker}")
    print("OK: contrato UNO Q + Z1 PR #6 verificado")
    print("- A4 DNP; MPR 0x28 en D20/D21")
    print("- TEMP_1WIRE en A2/D16; 32 pads físicos intactos")
    return 0
if __name__=="__main__": raise SystemExit(main())
