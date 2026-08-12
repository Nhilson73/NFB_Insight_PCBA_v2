#!/usr/bin/env python3
"""Valida contrato UNO Q, Z1 y Z2 después de PR #7."""
from __future__ import annotations
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN=ROOT/"hardware"/"insight_pin_contract.json"
SENSOR=ROOT/"hardware"/"sensor_interface_contract.json"
Z1=ROOT/"hardware"/"z1_production_netlist.json"
Z2=ROOT/"hardware"/"z2_production_netlist.json"
Z2C=ROOT/"hardware"/"z2_digital_contract.json"
PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"
SCH=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_sch"
Z2SCH=ROOT/"kicad"/"z2_digital_contract.kicad_sch"
FW="cf100b38df890f61aed472e934241e145425569b"
EXPECTED={3:("~RESET","MCU_NRST","ACTIVE"),9:("A0","PH_ADC","ACTIVE"),10:("A1","ORP_ADC","ACTIVE"),11:("A2/D16","TEMP_1WIRE","ACTIVE_DIGITAL"),12:("A3",None,"DNP_RESERVE"),13:("A4",None,"DNP_RESERVE"),14:("A5","DO_ADC","ACTIVE"),15:("D0","HMI_RX","ACTIVE"),16:("D1","HMI_TX","ACTIVE"),17:("D2","HX711_DOUT","ACTIVE"),18:("D3","HX711_SCK","ACTIVE"),19:("D4","MCU_WDI","ACTIVE"),20:("D5","PUMP_PWM","ACTIVE"),21:("D6","PUMP_DIR","ACTIVE"),22:("D7","CO2_SOL_CTL","ACTIVE"),23:("D8","CHILLER_CTL","ACTIVE_CONTROL_ONLY"),24:("D9",None,"DNP_RESERVE"),25:("D10","RS485_IRQ_RSVD","RESERVE"),28:("D13","LED_STATUS","ACTIVE"),31:("D20/SDA","I2C_SDA","ACTIVE"),32:("D21/SCL","I2C_SCL","ACTIVE")}
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for f in (PIN,SENSOR,Z1,Z2,Z2C,PCB,SCH,Z2SCH):
        if not f.exists(): fail(f"falta {f.relative_to(ROOT)}")
    p=json.loads(PIN.read_text(encoding="utf-8"))
    if p.get("schema_version")!=4: fail("pin contract no es schema v4")
    if p["firmware_reference"]["commit"]!=FW: fail("snapshot firmware cambió")
    if p.get("z1_netlist_source_of_truth")!="hardware/z1_production_netlist.json": fail("falta declarar netlist Z1")
    if p.get("z2_netlist_source_of_truth")!="hardware/z2_production_netlist.json": fail("falta declarar netlist Z2")
    if p.get("z2_contract_source_of_truth")!="hardware/z2_digital_contract.json": fail("falta declarar contrato Z2")
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
    z2c=json.loads(Z2C.read_text(encoding="utf-8"))
    amap={d["address_hex"].lower():d["device"] for d in z2c["i2c"]["devices"] if d["status"]=="ACTIVE"}
    if amap!={"0x28":"MPRLS0030PA00002A","0x66":"DFR1103"}: fail(f"mapa I2C Z2 incorrecto: {amap}")
    impl=p.get("z2_implementation",{})
    if impl.get("hmi_uart",{}).get("translator")!="TXU0202DCUR": fail("contrato no congela TXU0202")
    if impl.get("watchdog",{}).get("supervisor")!="TPS3823-30DBVR": fail("contrato no congela TPS3823-30")
    if impl.get("i2c",{}).get("global_pullup_ohm")!=4700: fail("contrato no congela pull-up I2C 4.7k")
    pcb=PCB.read_text(encoding="utf-8"); physical={int(x) for x in re.findall(r'\(pad "(\d+)" thru_hole',pcb)}
    if set(range(1,33))-physical: fail("faltan pads físicos UNO Q")
    sch=SCH.read_text(encoding="utf-8")
    for marker in ("J_UNOQ","MPRLS0030PA00002A","I2C_SDA","I2C_SCL","TEMP_1WIRE","A4/CO2_ADC DNP"):
        if marker not in sch: fail(f"root schematic Z1 sin {marker}")
    z2sch=Z2SCH.read_text(encoding="utf-8")
    for marker in ("PR #7","Z2 DIGITAL / BAJO RUIDO","DFR1103","0x66","HX711","TXU0202DCUR","TPS3823-30DBVR"):
        if marker not in z2sch: fail(f"schematic Z2 sin {marker}")
    print("OK: contrato UNO Q + Z1 + Z2 PR #7 verificado")
    print("- MPR 0x28 + DFR1103 0x66; HMI/HX711/WDT congelados")
    print("- 32 pads físicos UNO Q intactos; Z1 root preservado")
    return 0
if __name__=="__main__": raise SystemExit(main())
