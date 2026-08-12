#!/usr/bin/env python3
"""Valida contrato global UNO Q + zonas y reconoce root EDA inter-zona PR14."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN=ROOT/"hardware"/"insight_pin_contract.json"; SENSOR=ROOT/"hardware"/"sensor_interface_contract.json"; Z1=ROOT/"hardware"/"z1_production_netlist.json"; Z2=ROOT/"hardware"/"z2_production_netlist.json"; Z2C=ROOT/"hardware"/"z2_digital_contract.json"; Z4=ROOT/"hardware"/"z4_production_netlist.json"; Z4C=ROOT/"hardware"/"z4_actuator_contract.json"; POWER=ROOT/"hardware"/"power_architecture_contract.json"; ROOTEDA=ROOT/"hardware"/"root_eda_contract.json"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"; SCH=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_sch"; Z1SCH=ROOT/"kicad"/"z1_sensor_contract.kicad_sch"; Z2SCH=ROOT/"kicad"/"z2_digital_contract.kicad_sch"
FW="cf100b38df890f61aed472e934241e145425569b"
EXPECTED={2:("IOREF","UNO_IOREF_3V3","ACTIVE_CONTROL_OUTPUT"),3:("~RESET","MCU_NRST","ACTIVE"),4:("3V3 OUT",None,"NC_HOST_POWER_OUT"),5:("5V JANALOG",None,"NC_HOST_5V_SUPPORTED_INPUT"),8:("VIN","12V_HOST_VIN","ACTIVE_POWER_INPUT"),9:("A0","PH_ADC","ACTIVE"),10:("A1","ORP_ADC","ACTIVE"),11:("A2/D16","TEMP_1WIRE","ACTIVE_DIGITAL"),12:("A3",None,"DNP_RESERVE"),13:("A4","PUMP_CURRENT_ADC","ACTIVE_ANALOG_DIAGNOSTIC"),14:("A5","DO_ADC","ACTIVE"),15:("D0","HMI_RX","ACTIVE"),16:("D1","HMI_TX","ACTIVE"),17:("D2","HX711_DOUT","ACTIVE"),18:("D3","HX711_SCK","ACTIVE"),19:("D4","MCU_WDI","ACTIVE"),20:("D5","PUMP_PWM","ACTIVE"),21:("D6","PUMP_DIR","ACTIVE"),22:("D7","CO2_SOL_CTL","ACTIVE"),23:("D8","CHILLER_CTL","ACTIVE_CONTROL_ONLY"),24:("D9",None,"DNP_RESERVE"),25:("D10","ACT_FAULT_N","ACTIVE_DIAGNOSTIC"),28:("D13","LED_STATUS","ACTIVE"),31:("D20/SDA","I2C_SDA","ACTIVE"),32:("D21/SCL","I2C_SCL","ACTIVE")}
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for f in (PIN,SENSOR,Z1,Z2,Z2C,Z4,Z4C,POWER,ROOTEDA,PCB,SCH,Z1SCH,Z2SCH):
        if not f.exists(): fail(f"falta {f.relative_to(ROOT)}")
    p=json.loads(PIN.read_text(encoding="utf-8"))
    if p.get("schema_version")!=6 or p["firmware_reference"]["commit"]!=FW: fail("pin contract/firmware snapshot cambió")
    pins={int(x["pad"]):x for x in p["pins"]}
    if set(pins)!=set(range(1,33)): fail("contrato no contiene pads 1..32")
    for pad,e in EXPECTED.items():
        got=(pins[pad].get("arduino"),pins[pad].get("net"),pins[pad].get("status"))
        if got!=e: fail(f"pad {pad}: {got} != {e}")
    pi=p["power_interface"]
    if pi["vin"]["range_v"]!=[7.0,24.0] or pi["host_5v"]["official_capability"]!="REGULATED_5V_HOST_INPUT_UP_TO_3A" or pi["host_5v"]["shield_connection"]!="NC" or pi["host_3v3"]["shield_connection"]!="NC" or not pi["backfeed_forbidden"]: fail("frontera power host cambió")
    active={x.get("net") for x in p["pins"] if str(x.get("status","")).startswith("ACTIVE")}
    bad={"TEMP_ADC","CO2_ADC","HUM_ADC","CO2_PWM","CO2_FLOW_PWM","5V_RAIL","3V3_RAIL","RS485_IRQ_RSVD"}&active
    if bad: fail(f"nets prohibidas activas: {sorted(bad)}")
    s=json.loads(SENSOR.read_text(encoding="utf-8")); co2={c["id"]:c for c in s["channels"]}["CO2"]
    if (co2["electrical"]["sda_net"],co2["electrical"]["scl_net"],co2["electrical"]["i2c_address_hex"].lower())!=("I2C_SDA","I2C_SCL","0x28"): fail("MPR no enlaza I2C 0x28")
    z2c=json.loads(Z2C.read_text(encoding="utf-8")); amap={d["address_hex"].lower():d["device"] for d in z2c["i2c"]["devices"] if d["status"]=="ACTIVE"}
    if amap!={"0x28":"MPRLS0030PA00002A","0x66":"DFR1103"}: fail("mapa I2C cambió")
    z4c=json.loads(Z4C.read_text(encoding="utf-8")); z4=json.loads(Z4.read_text(encoding="utf-8"))
    if z4c.get("status")!="Z4_PRODUCTION_BASELINE_PR12" or z4.get("status")!="FROZEN_Z4_NETLIST_PR12_FOOTPRINTS_CLOSED_PR13": fail("baseline Z4 cambió")
    if (z4c["pump"]["driver"]["mpn"],z4c["co2_solenoid"]["driver"]["mpn"],z4c["chiller"]["photomos"]["mpn"])!=("DRV8242HQRHLRQ1","TPS1HC120CQDYCRQ1","AQY212EHAX"): fail("drivers Z4 cambiaron")
    power=json.loads(POWER.read_text(encoding="utf-8"))
    if power.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9" or power["host_power"]["preferred_method_for_nfb"]!="VIN_7_TO_24V": fail("power host cambió")
    z1=json.loads(Z1.read_text(encoding="utf-8")); z2=json.loads(Z2.read_text(encoding="utf-8"))
    for nz,name in ((z1,"Z1"),(z2,"Z2"),(z4,"Z4")):
        nets={x["name"]:set(x["nodes"]) for x in nz["nets"]}
        if "J_UNOQ.4" in nets.get("3V3_RAIL",set()) or "J_UNOQ.5" in nets.get("5V_RAIL",set()): fail(f"{name} back-feed host")
    rooteda=json.loads(ROOTEDA.read_text(encoding="utf-8"))
    if rooteda.get("status")!="ROOT_EDA_INTERZONE_BASELINE_PR14" or rooteda["scope"].get("placement") or rooteda["scope"].get("routing"): fail("root EDA PR14/scope incorrecto")
    if rooteda["interzone_nets"].get("GND")!=["Z0","Z1","Z2","Z3","Z4"]: fail("GND root no incluye host")
    if "Z0" in rooteda["interzone_nets"]["3V3_RAIL"] or "Z0" in rooteda["interzone_nets"]["5V_RAIL"]: fail("rails locales root incluyen host")
    pcb=PCB.read_text(encoding="utf-8"); physical={int(x) for x in re.findall(r'\(pad "(\d+)" thru_hole',pcb)}
    if set(range(1,33))-physical: fail("faltan pads físicos UNO Q")
    root=SCH.read_text(encoding="utf-8")
    for marker in ("PR #14","Z0 — Arduino UNO Q Host","Z1 — Sensors","Z2 — Digital / Low Noise","Z3 — Power","Z4 — Actuators","uno_q_interface.kicad_sch","z1_interface.kicad_sch","z2_interface.kicad_sch","z3_interface.kicad_sch","z4_interface.kicad_sch"):
        if marker not in root: fail(f"root PR14 sin {marker}")
    z1sch=Z1SCH.read_text(encoding="utf-8"); z2sch=Z2SCH.read_text(encoding="utf-8")
    for marker in ("MPRLS0030PA00002A","PH_ADC","ORP_ADC","TEMP_1WIRE","DO_ADC"):
        if marker not in z1sch: fail(f"Z1 contract sin {marker}")
    for marker in ("PR #7","DFR1103","0x66","HX711","TXU0202DCUR","TPS3823-30DBVR"):
        if marker not in z2sch: fail(f"Z2 contract sin {marker}")
    print("OK: contrato global + root EDA inter-zona PR14 verificado")
    print("- Z0 participa en GND, no en 3V3/5V locales; A4/D10 Z4 preservados")
    return 0
if __name__=="__main__": raise SystemExit(main())
