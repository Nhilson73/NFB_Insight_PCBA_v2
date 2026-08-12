#!/usr/bin/env python3
"""Valida la jerarquía EDA inter-zona PR #14 contra contratos de producción."""
from __future__ import annotations
import json,re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"hardware"/"root_eda_contract.json"
PIN=ROOT/"hardware"/"insight_pin_contract.json"
Z1=ROOT/"hardware"/"z1_production_netlist.json"
Z2=ROOT/"hardware"/"z2_production_netlist.json"
POWER=ROOT/"hardware"/"power_production_netlist.json"
Z4=ROOT/"hardware"/"z4_production_netlist.json"
AUDIT=ROOT/"hardware"/"footprint_audit.json"
PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"
ROOTSCH=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_sch"
def fail(m): raise SystemExit("ERROR: "+m)
def labels(text,kind):
    if kind=="hier": return re.findall(r'\(hierarchical_label "([^"]+)"',text)
    if kind=="local": return re.findall(r'\(label "([^"]+)"',text)
    if kind=="pin": return re.findall(r'\(pin "([^"]+)"\s+(?:input|output|bidirectional|tri_state|passive)',text)
    raise ValueError(kind)
def main():
    for p in (CONTRACT,PIN,Z1,Z2,POWER,Z4,AUDIT,PCB,ROOTSCH):
        if not p.exists(): fail(f"falta {p.relative_to(ROOT)}")
    c=json.loads(CONTRACT.read_text(encoding="utf-8")); pin=json.loads(PIN.read_text(encoding="utf-8")); z1=json.loads(Z1.read_text(encoding="utf-8")); z2=json.loads(Z2.read_text(encoding="utf-8")); power=json.loads(POWER.read_text(encoding="utf-8")); z4=json.loads(Z4.read_text(encoding="utf-8")); audit=json.loads(AUDIT.read_text(encoding="utf-8"))
    if c.get("schema_version")!=2 or c.get("status")!="ROOT_EDA_INTERZONE_BASELINE_PR14": fail("root EDA contract no es PR14/schema2")
    scope=c.get("scope",{})
    if scope!={"interzone_hierarchy":True,"zone_internal_component_symbols":False,"placement":False,"routing":False,"pcb_geometry_change":False}: fail(f"scope PR14 inesperado: {scope}")
    erc=c.get("erc_interzone_policy",{})
    if erc.get("mode")!="BOUNDED_INTENTIONAL_INTERFACE_DEBT_PR14" or erc.get("expected_violation_type")!="label_dangling" or int(erc.get("expected_violation_count",0))!=125 or int(erc.get("unexpected_violation_count_allowed",-1))!=0: fail("política ERC PR14 no está congelada")
    if pin.get("schema_version")!=6: fail("pin contract no es schema6")
    if z1.get("status")!="FROZEN_Z1_NETLIST_PR6_POWER_CORRECTED_PR9": fail("Z1 baseline cambió")
    if z2.get("status")!="FROZEN_Z2_NETLIST_PR7_POWER_CORRECTED_PR9": fail("Z2 baseline cambió")
    if power.get("status")!="FROZEN_POWER_NETLIST_PR10_FOOTPRINTS_CLOSED_PR13": fail("power no conserva PR10+PR13")
    if z4.get("status")!="FROZEN_Z4_NETLIST_PR12_FOOTPRINTS_CLOSED_PR13": fail("Z4 no conserva PR12+PR13")
    if audit.get("status")!="FOOTPRINT_AUDIT_CLOSED_PR13": fail("footprints no están cerrados PR13")
    sheets={x["id"]:x for x in c["sheets"]}
    if set(sheets)!={"Z0","Z1","Z2","Z3","Z4"}: fail("deben existir exactamente Z0..Z4")
    for s in sheets.values():
        path=ROOT/s["file"]
        if not path.exists(): fail(f"falta child sheet {s['file']}")
    inter={k:set(v) for k,v in c["interzone_nets"].items()}
    forbidden={"CO2_ADC","TEMP_ADC","HUM_ADC","CO2_PWM","CO2_FLOW_PWM","RS485_IRQ_RSVD"}
    if forbidden & set(inter): fail(f"nets prohibidas en root: {sorted(forbidden & set(inter))}")
    active_host={x.get("net") for x in pin["pins"] if str(x.get("status","")).startswith("ACTIVE") and x.get("net")}
    if any(x.get("net")=="GND" for x in pin["pins"]): active_host.add("GND")
    z0={net for net,zones in inter.items() if "Z0" in zones}
    if active_host!=z0: fail(f"Z0 root != endpoints activos pin contract + GND; falta={sorted(active_host-z0)} sobra={sorted(z0-active_host)}")
    if "GND" not in z0: fail("UNO Q debe participar en GND común")
    if "3V3_RAIL" in z0 or "5V_RAIL" in z0: fail("host no puede alimentar rails locales")
    for zid,s in sheets.items():
        expected={net for net,zones in inter.items() if zid in zones}
        text=(ROOT/s["file"]).read_text(encoding="utf-8")
        got=set(labels(text,"hier"))
        if got!=expected: fail(f"{zid} hierarchical labels difieren; falta={sorted(expected-got)} sobra={sorted(got-expected)}")
    root=ROOTSCH.read_text(encoding="utf-8")
    for s in sheets.values():
        if Path(s["file"]).name not in root or s["name"] not in root: fail(f"root no instancia {s['id']}")
    pin_counts=Counter(labels(root,"pin")); label_counts=Counter(labels(root,"local"))
    for net,zones in inter.items():
        expected=len(zones)
        if pin_counts[net]!=expected: fail(f"root sheet-pin count {net}={pin_counts[net]} esperado {expected}")
        if label_counts[net]!=expected: fail(f"root local-label count {net}={label_counts[net]} esperado {expected}")
    extra_pins=set(pin_counts)-set(inter); extra_labels=set(label_counts)-set(inter)
    if extra_pins or extra_labels: fail(f"root tiene nets no contractuales pins={sorted(extra_pins)} labels={sorted(extra_labels)}")
    if inter["I2C_SDA"]!={"Z0","Z1","Z2"} or inter["I2C_SCL"]!={"Z0","Z1","Z2"}: fail("I2C root ownership cambió")
    if inter["GND"]!={"Z0","Z1","Z2","Z3","Z4"}: fail("GND debe abarcar Z0..Z4")
    if inter["3V3_RAIL"]!={"Z1","Z2","Z3","Z4"} or inter["5V_RAIL"]!={"Z1","Z2","Z3"}: fail("rails locales tienen ownership incorrecto")
    pcb=PCB.read_text(encoding="utf-8")
    refs=[]
    for nz in (z1,z2,power,z4): refs.extend(x["ref"] for x in nz["components"])
    placed=[r for r in refs if f'"{r}"' in pcb]
    if placed: fail(f"PR14 no debe hacer placement; refs encontradas: {placed[:10]}")
    for token in ("PR #14","No placement / no routing","Z0 — Arduino UNO Q Host","Z1 — Sensors","Z2 — Digital / Low Noise","Z3 — Power","Z4 — Actuators"):
        if token not in root: fail(f"root sin marcador {token}")
    print("OK: root EDA inter-zona PR14 coherente")
    print(f"- {len(inter)} nets inter-zona / 5 sheets / GND incluye host")
    print("- 3V3/5V locales excluyen Z0; I2C compartido Z0/Z1/Z2")
    print("- placement/routing=0; deuda ERC intencional PR14=125 label_dangling; 0 inesperadas")
    return 0
if __name__=="__main__": raise SystemExit(main())
