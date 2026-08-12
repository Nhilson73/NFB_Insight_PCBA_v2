#!/usr/bin/env python3
"""Valida coherencia cruzada Z1+Z2+Z3+Z4 y cierre físico PR13."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES={"integration":ROOT/"hardware"/"electrical_integration_contract.json","pins":ROOT/"hardware"/"insight_pin_contract.json","z1":ROOT/"hardware"/"z1_production_netlist.json","z2":ROOT/"hardware"/"z2_production_netlist.json","power":ROOT/"hardware"/"power_production_netlist.json","z4":ROOT/"hardware"/"z4_production_netlist.json","audit":ROOT/"hardware"/"footprint_audit.json","sch":ROOT/"kicad"/"integration_contract.kicad_sch"}
def fail(m): raise SystemExit("ERROR: "+m)
def netmap(n): return {x["name"]:set(x["nodes"]) for x in n["nets"]}
def compmap(n): return {x["ref"]:x for x in n["components"]}
def main():
    for p in FILES.values():
        if not p.exists(): fail(f"falta {p.relative_to(ROOT)}")
    ic=json.loads(FILES["integration"].read_text(encoding="utf-8")); pins=json.loads(FILES["pins"].read_text(encoding="utf-8")); z1=json.loads(FILES["z1"].read_text(encoding="utf-8")); z2=json.loads(FILES["z2"].read_text(encoding="utf-8")); power=json.loads(FILES["power"].read_text(encoding="utf-8")); z4=json.loads(FILES["z4"].read_text(encoding="utf-8")); audit=json.loads(FILES["audit"].read_text(encoding="utf-8"))
    if ic.get("schema_version")!=2 or ic.get("status")!="ELECTRICAL_INTEGRATION_Z4_PR12": fail("integración no es PR12")
    if not ic["scope"].get("actuator_connectivity") or ic["scope"].get("placement") or ic["scope"].get("routing"): fail("scope integración incorrecto")
    if audit.get("schema_version")!=3 or audit.get("status")!="FOOTPRINT_AUDIT_CLOSED_PR13": fail("integración no enlaza cierre físico PR13")
    if power.get("status")!="FROZEN_POWER_NETLIST_PR10_FOOTPRINTS_CLOSED_PR13" or z4.get("status")!="FROZEN_Z4_NETLIST_PR12_FOOTPRINTS_CLOSED_PR13": fail("netlists no enlazan PR13")
    pby={int(x["pad"]):x for x in pins["pins"]}
    expected={2:"UNO_IOREF_3V3",8:"12V_HOST_VIN",9:"PH_ADC",10:"ORP_ADC",11:"TEMP_1WIRE",13:"PUMP_CURRENT_ADC",14:"DO_ADC",15:"HMI_RX",16:"HMI_TX",17:"HX711_DOUT",18:"HX711_SCK",19:"MCU_WDI",20:"PUMP_PWM",21:"PUMP_DIR",22:"CO2_SOL_CTL",23:"CHILLER_CTL",25:"ACT_FAULT_N",28:"LED_STATUS",31:"I2C_SDA",32:"I2C_SCL"}
    for pad,net in expected.items():
        if pby[pad].get("net")!=net: fail(f"J_UNOQ pad {pad} perdió {net}")
    for pad in (4,5,12,24):
        if pby[pad].get("net") is not None: fail(f"pad {pad} debe permanecer sin net")
    n1,n2,np,n4=map(netmap,(z1,z2,power,z4))
    for net in ("GND","3V3_RAIL","5V_RAIL"):
        if net not in n1 or net not in n2 or net not in np: fail(f"net base {net} incompleta")
    if "3V3_RAIL" not in n4 or "12V_ACT" not in n4: fail("Z4 no recibe rails contractuales")
    for net in ("I2C_SDA","I2C_SCL"):
        if net not in n1 or net not in n2: fail(f"bus {net} no compartido")
    if "J_UNOQ.4" in n1["3V3_RAIL"]|n2["3V3_RAIL"]|np["3V3_RAIL"]|n4["3V3_RAIL"]: fail("back-feed 3V3")
    if "J_UNOQ.5" in n1["5V_RAIL"]|n2["5V_RAIL"]|np["5V_RAIL"]|n4.get("5V_RAIL",set()): fail("back-feed 5V")
    cp=compmap(power); c4=compmap(z4)
    if cp["U_5V"]["pins"].get("4")!="5V_RAIL" or cp["U_3V3"]["pins"].get("5")!="3V3_RAIL": fail("productores 5V/3V3 cambiaron")
    if cp["U_5V"]["pins"].get("2")!="UNO_IOREF_3V3" or cp["U_3V3"]["pins"].get("3")!="5V_PGOOD": fail("secuencia power rota")
    if "12V_HOST_VIN" not in np or "12V_ACT" not in np: fail("power perdió rama host/act")
    expected_fp={"U_EFUSE":"NFB:TI_RPW0010A_TPS259470A","U_5V":"NFB:TI_RDN0011A_TPSM33625","U_PUMP_DRV":"NFB:TI_RHL0020B_DRV8242","U_CO2_DRV":"NFB:TI_DYC0008A_TPS1HC120","U_CHILLER":"NFB:Panasonic_AQY212EHAX_DIP4_SMD"}
    actual={"U_EFUSE":cp["U_EFUSE"]["footprint"],"U_5V":cp["U_5V"]["footprint"],"U_PUMP_DRV":c4["U_PUMP_DRV"]["footprint"],"U_CO2_DRV":c4["U_CO2_DRV"]["footprint"],"U_CHILLER":c4["U_CHILLER"]["footprint"]}
    if actual!=expected_fp: fail(f"footprints críticos no integrados: {actual}")
    if c4["U_PUMP_DRV"]["mpn"]!="DRV8242HQRHLRQ1" or c4["U_CO2_DRV"]["mpn"]!="TPS1HC120CQDYCRQ1" or c4["U_CHILLER"]["mpn"]!="AQY212EHAX": fail("drivers Z4 cambiaron")
    if c4["U_PUMP_DRV"]["pins"].get("21")!="GND" or "U_PUMP_DRV.21" not in n4["GND"]: fail("EP21 DRV8242 no unido a GND")
    if "U_CHILLER.3" in n4.get("12V_ACT",set()) or "U_CHILLER.4" in n4.get("12V_ACT",set()) or "GND" in (c4["U_CHILLER"]["pins"]["3"],c4["U_CHILLER"]["pins"]["4"]): fail("contacto chiller perdió aislamiento")
    z1_uno=set(z1["uno_q_interface"]["sensor_endpoints"].values())-{None}; z2_uno=set(z2["uno_q_interface"]["endpoints"].values())
    if z1_uno&z2_uno!={"I2C_SDA","I2C_SCL"}: fail("colisión ownership Z1/Z2")
    for pad,net in {13:"PUMP_CURRENT_ADC",20:"PUMP_PWM",21:"PUMP_DIR",22:"CO2_SOL_CTL",23:"CHILLER_CTL",25:"ACT_FAULT_N"}.items():
        if f"J_UNOQ.{pad}" not in n4.get(net,set()): fail(f"Z4 no conecta pad {pad} a {net}")
    addresses={x["address"].lower():x["device"] for x in ic["i2c_address_map"]}
    if addresses!={"0x28":"MPRLS0030PA00002A","0x66":"DFR1103"}: fail("mapa I2C cambió")
    if "U_CO2.2" not in n1["I2C_SDA"] or "U_CO2.3" not in n1["I2C_SCL"] or "J_GNSS_RTC.1" not in n2["I2C_SDA"] or "J_GNSS_RTC.2" not in n2["I2C_SCL"]: fail("endpoints I2C incompletos")
    sch=FILES["sch"].read_text(encoding="utf-8")
    for marker in ("PR #11","J_UNOQ.4 NO conecta","J_UNOQ.5 NO conecta","MPRLS0030PA00002A = 0x28","DFR1103 GNSS+RTC = 0x66","Routing permanece bloqueado"):
        if marker not in sch: fail(f"hoja integración perdió {marker}")
    print("OK: integración Z1+Z2+Z3+Z4 + footprint closure PR13 coherente; placement/routing siguen fuera de este PR")
    return 0
if __name__=="__main__": raise SystemExit(main())
