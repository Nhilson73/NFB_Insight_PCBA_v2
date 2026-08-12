#!/usr/bin/env python3
"""Valida contrato global UNO Q + Z1 + Z2 + Z4 y frontera de potencia."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PIN=ROOT/"hardware"/"insight_pin_contract.json"; SENSOR=ROOT/"hardware"/"sensor_interface_contract.json"; Z1=ROOT/"hardware"/"z1_production_netlist.json"; Z2=ROOT/"hardware"/"z2_production_netlist.json"; Z2C=ROOT/"hardware"/"z2_digital_contract.json"; Z4=ROOT/"hardware"/"z4_production_netlist.json"; Z4C=ROOT/"hardware"/"z4_actuator_contract.json"; POWER=ROOT/"hardware"/"power_architecture_contract.json"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"; SCH=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_sch"; Z2SCH=ROOT/"kicad"/"z2_digital_contract.kicad_sch"
FW="cf100b38df890f61aed472e934241e145425569b"
EXPECTED={2:("IOREF","UNO_IOREF_3V3","ACTIVE_CONTROL_OUTPUT"),3:("~RESET","MCU_NRST","ACTIVE"),4:("3V3 OUT",None,"NC_HOST_POWER_OUT"),5:("5V JANALOG",None,"NC_HOST_5V_SUPPORTED_INPUT"),8:("VIN","12V_HOST_VIN","ACTIVE_POWER_INPUT"),9:("A0","PH_ADC","ACTIVE"),10:("A1","ORP_ADC","ACTIVE"),11:("A2/D16","TEMP_1WIRE","ACTIVE_DIGITAL"),12:("A3",None,"DNP_RESERVE"),13:("A4","PUMP_CURRENT_ADC","ACTIVE_ANALOG_DIAGNOSTIC"),14:("A5","DO_ADC","ACTIVE"),15:("D0","HMI_RX","ACTIVE"),16:("D1","HMI_TX","ACTIVE"),17:("D2","HX711_DOUT","ACTIVE"),18:("D3","HX711_SCK","ACTIVE"),19:("D4","MCU_WDI","ACTIVE"),20:("D5","PUMP_PWM","ACTIVE"),21:("D6","PUMP_DIR","ACTIVE"),22:("D7","CO2_SOL_CTL","ACTIVE"),23:("D8","CHILLER_CTL","ACTIVE_CONTROL_ONLY"),24:("D9",None,"DNP_RESERVE"),25:("D10","ACT_FAULT_N","ACTIVE_DIAGNOSTIC"),28:("D13","LED_STATUS","ACTIVE"),31:("D20/SDA","I2C_SDA","ACTIVE"),32:("D21/SCL","I2C_SCL","ACTIVE")}
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for f in (PIN,SENSOR,Z1,Z2,Z2C,Z4,Z4C,POWER,PCB,SCH,Z2SCH):
        if not f.exists(): fail(f"falta {f.relative_to(ROOT)}")
    p=json.loads(PIN.read_text(encoding="utf-8"))
    if p.get("schema_version")!=6: fail("pin contract no es schema v6")
    if p["firmware_reference"]["commit"]!=FW: fail("snapshot firmware cambió")
    for key,val in (("z1_netlist_source_of_truth","hardware/z1_production_netlist.json"),("z2_netlist_source_of_truth","hardware/z2_production_netlist.json"),("z2_contract_source_of_truth","hardware/z2_digital_contract.json"),("z4_netlist_source_of_truth","hardware/z4_production_netlist.json"),("z4_contract_source_of_truth","hardware/z4_actuator_contract.json"),("power_architecture_source_of_truth","hardware/power_architecture_contract.json")):
        if p.get(key)!=val: fail(f"{key} incorrecto")
    pins={int(x["pad"]):x for x in p["pins"]}
    if set(pins)!=set(range(1,33)): fail("contrato no contiene pads 1..32")
    for pad,e in EXPECTED.items():
        a=pins[pad]; got=(a.get("arduino"),a.get("net"),a.get("status"))
        if got!=e: fail(f"pad {pad}: {got} != {e}")
    pi=p.get("power_interface",{})
    if pi.get("vin",{}).get("range_v") != [7.0,24.0]: fail("VIN UNO Q no conserva 7-24V")
    if pi.get("host_5v",{}).get("official_capability") != "REGULATED_5V_HOST_INPUT_UP_TO_3A": fail("5V JANALOG oficial no reconocido")
    if pi.get("host_5v",{}).get("shield_connection")!="NC" or pi.get("host_3v3",{}).get("shield_connection")!="NC" or not pi.get("backfeed_forbidden"): fail("frontera rails host cambió")
    active={x.get("net") for x in p["pins"] if str(x.get("status","")).startswith("ACTIVE")}
    bad={"TEMP_ADC","CO2_ADC","HUM_ADC","CO2_PWM","CO2_FLOW_PWM","5V_RAIL","3V3_RAIL","RS485_IRQ_RSVD"}&active
    if bad: fail(f"nets prohibidas activas: {sorted(bad)}")
    s=json.loads(SENSOR.read_text(encoding="utf-8")); co2={c["id"]:c for c in s["channels"]}["CO2"]
    if co2["electrical"]["sda_net"]!="I2C_SDA" or co2["electrical"]["scl_net"]!="I2C_SCL" or co2["electrical"]["i2c_address_hex"].lower()!="0x28": fail("MPR no enlaza I2C 0x28")
    z2c=json.loads(Z2C.read_text(encoding="utf-8")); amap={d["address_hex"].lower():d["device"] for d in z2c["i2c"]["devices"] if d["status"]=="ACTIVE"}
    if amap!={"0x28":"MPRLS0030PA00002A","0x66":"DFR1103"}: fail(f"mapa I2C incorrecto: {amap}")
    impl=p.get("z2_implementation",{})
    if impl.get("hmi_uart",{}).get("translator")!="TXU0202DCUR" or impl.get("watchdog",{}).get("supervisor")!="TPS3823-30DBVR" or impl.get("i2c",{}).get("global_pullup_ohm")!=4700: fail("baseline Z2 cambió")
    z4c=json.loads(Z4C.read_text(encoding="utf-8")); z4=json.loads(Z4.read_text(encoding="utf-8"))
    if z4c.get("status")!="Z4_PRODUCTION_BASELINE_PR12": fail("contrato Z4 no es PR12")
    if z4.get("schema_version")!=2 or z4.get("status")!="FROZEN_Z4_NETLIST_PR12_FOOTPRINTS_CLOSED_PR13": fail("netlist Z4 no preserva PR12 + cierre físico PR13")
    if z4c["pump"]["driver"]["mpn"]!="DRV8242HQRHLRQ1" or z4c["co2_solenoid"]["driver"]["mpn"]!="TPS1HC120CQDYCRQ1" or z4c["chiller"]["photomos"]["mpn"]!="AQY212EHAX": fail("drivers Z4 finales cambiaron")
    z4i=p.get("z4_implementation",{})
    if z4i.get("fault",{}).get("net")!="ACT_FAULT_N" or z4i.get("pump",{}).get("current_adc_pad")!=13: fail("diagnóstico Z4 no congelado")
    power=json.loads(POWER.read_text(encoding="utf-8"))
    if power.get("status")!="POWER_ARCHITECTURE_BASELINE_PR9" or power["host_power"]["preferred_method_for_nfb"]!="VIN_7_TO_24V": fail("potencia host cambió")
    z1=json.loads(Z1.read_text(encoding="utf-8")); z2=json.loads(Z2.read_text(encoding="utf-8"))
    for nz,name in ((z1,"Z1"),(z2,"Z2"),(z4,"Z4")):
        nets={x["name"]:set(x["nodes"]) for x in nz["nets"]}
        if "J_UNOQ.4" in nets.get("3V3_RAIL",set()) or "J_UNOQ.5" in nets.get("5V_RAIL",set()): fail(f"{name} back-feed host")
    pcb=PCB.read_text(encoding="utf-8"); physical={int(x) for x in re.findall(r'\(pad "(\d+)" thru_hole',pcb)}
    if set(range(1,33))-physical: fail("faltan pads físicos UNO Q")
    sch=SCH.read_text(encoding="utf-8")
    for marker in ("J_UNOQ","MPRLS0030PA00002A","I2C_SDA","I2C_SCL","TEMP_1WIRE"):
        if marker not in sch: fail(f"root Z1 sin {marker}")
    z2sch=Z2SCH.read_text(encoding="utf-8")
    for marker in ("PR #7","DFR1103","0x66","HX711","TXU0202DCUR","TPS3823-30DBVR"):
        if marker not in z2sch: fail(f"Z2 schematic sin {marker}")
    print("OK: contrato UNO Q + Z1 + Z2 + Z4(PR12/footprints PR13) + potencia verificado")
    print("- A4=PUMP_CURRENT_ADC; D10=ACT_FAULT_N; CO2 pressure=MPR I2C 0x28")
    return 0
if __name__=="__main__": raise SystemExit(main())
