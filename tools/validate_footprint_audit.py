#!/usr/bin/env python3
"""Valida el gate de footprints antes de autorizar placement, extendido a Z4 PR12."""
from __future__ import annotations
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"hardware"/"footprint_audit.json"; MPR=ROOT/"kicad"/"lib"/"nfb_footprints.pretty"/"Honeywell_MPR_LongPort_12Pad.kicad_mod"; POWER=ROOT/"hardware"/"power_production_netlist.json"; Z1=ROOT/"hardware"/"z1_production_netlist.json"; Z4=ROOT/"hardware"/"z4_production_netlist.json"; PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"
def fail(m): raise SystemExit("ERROR: "+m)
def close(a,b,t=1e-6): return abs(float(a)-float(b))<=t
def main():
    for p in (AUDIT,MPR,POWER,Z1,Z4,PCB):
        if not p.exists(): fail(f"falta {p.relative_to(ROOT)}")
    audit=json.loads(AUDIT.read_text(encoding="utf-8"))
    if audit.get("schema_version")!=2 or audit.get("status")!="FOOTPRINT_AUDIT_EXTENDED_PR12": fail("audit no es baseline extendido PR12")
    if audit.get("policy",{}).get("do_not_invent_land_patterns") is not True or audit["policy"].get("placement_requires_closed_audit") is not True: fail("política de footprints debilitada")
    by={x["id"]:x for x in audit["audits"]}
    required={"UNO_Q_CARRIER_ROTATED","MPR_LONG_PORT_12PAD","TPS25947_RPW0010A","TPSM33625_RDN11","DRV8242_RHL20","TPS1HC120_DYC8","AQY212EHAX_DIP4_SMD"}
    if set(by)!=required: fail(f"conjunto auditorías inesperado: {set(by)}")
    m=by["MPR_LONG_PORT_12PAD"]
    if m["status"]!="CLOSED_PRIMARY_DATASHEET" or not m["placement_allowed"] or "32332628" not in m["source"] or "Issue L" not in m["source"]: fail("MPR no está cerrado contra Honeywell Issue L")
    g=m["verified_geometry"]
    if g["pad_count"]!=12 or not close(g["pitch_mm"],1.27) or not close(g["recommended_layout_outer_span_mm"],4.20): fail("geometría contractual MPR incorrecta")
    txt=MPR.read_text(encoding="utf-8")
    pads=re.findall(r'\(pad\s+"(\d+)"\s+smd\s+rect\s+\(at\s+([-0-9.]+)\s+([-0-9.]+)\)\s+\(size\s+([-0-9.]+)\s+([-0-9.]+)\)',txt)
    if len(pads)!=12 or {int(x[0]) for x in pads}!=set(range(1,13)): fail("footprint MPR pads incorrectos")
    data={int(n):tuple(map(float,(x,y,sx,sy))) for n,x,y,sx,sy in pads}
    exp={1:(1.27,1.775,.70,.65),2:(0,1.775,.70,.65),3:(-1.27,1.775,.70,.65),4:(1.775,1.27,.65,.70),5:(1.775,0,.65,.70),6:(1.775,-1.27,.65,.70),7:(-1.27,-1.775,.70,.65),8:(0,-1.775,.70,.65),9:(1.27,-1.775,.70,.65),10:(-1.775,-1.27,.65,.70),11:(-1.775,0,.65,.70),12:(-1.775,1.27,.65,.70)}
    for n,e in exp.items():
        if any(not close(a,b) for a,b in zip(data[n],e)): fail(f"pad MPR {n} fuera de baseline")
    if "ISSUE L FIG.10" not in txt: fail("MPR sin trazabilidad gráfica")
    z1=json.loads(Z1.read_text(encoding="utf-8")); uco2=next(x for x in z1["components"] if x["ref"]=="U_CO2")
    if uco2["footprint"]!="NFB:Honeywell_MPR_LongPort_12Pad": fail("Z1 no usa MPR auditado")
    power={x["ref"]:x for x in json.loads(POWER.read_text(encoding="utf-8"))["components"]}
    z4={x["ref"]:x for x in json.loads(Z4.read_text(encoding="utf-8"))["components"]}
    blocked=[
      ("U_EFUSE","TPS25947_RPW0010A",power,"PENDING_DATASHEET_AUDIT_BEFORE_PLACEMENT"),
      ("U_5V","TPSM33625_RDN11",power,"PENDING_DATASHEET_AUDIT_BEFORE_PLACEMENT"),
      ("U_PUMP_DRV","DRV8242_RHL20",z4,"PENDING_VENDOR_CAD_AUDIT_RHL20"),
      ("U_CO2_DRV","TPS1HC120_DYC8",z4,"PENDING_VENDOR_CAD_AUDIT_DYC8"),
      ("U_CHILLER","AQY212EHAX_DIP4_SMD",z4,"PENDING_PANASONIC_CAD_AUDIT_DIP4_SMD")]
    for ref,aid,comps,placeholder in blocked:
        a=by[aid]
        if a["placement_allowed"] is not False or not str(a["status"]).startswith(("BLOCKED","PRIMARY_DRAWING")): fail(f"{ref} no conserva bloqueo de audit")
        if comps[ref]["footprint"]!=placeholder: fail(f"{ref} obtuvo footprint antes del cierre de audit")
    if by["TPS25947_RPW0010A"]["verified_geometry"]["pin_count"]!=10 or by["TPS25947_RPW0010A"]["verified_geometry"]["pitch_mm"]!=0.45: fail("metadata RPW incorrecta")
    if by["TPSM33625_RDN11"]["verified_geometry"]["pin_count"]!=11 or by["TPSM33625_RDN11"]["verified_geometry"]["body_mm"]!=[4.5,3.5]: fail("metadata RDN incorrecta")
    if by["DRV8242_RHL20"]["verified_geometry"]["pin_count"]!=20 or by["DRV8242_RHL20"]["verified_geometry"]["body_mm"]!=[4.5,3.5]: fail("metadata RHL20 incorrecta")
    if by["TPS1HC120_DYC8"]["verified_geometry"]["pin_count"]!=8: fail("metadata DYC8 incorrecta")
    if by["AQY212EHAX_DIP4_SMD"]["verified_geometry"]["pin_count"]!=4 or by["AQY212EHAX_DIP4_SMD"]["verified_geometry"]["recommended_system_use_v_max"]!=48: fail("metadata PhotoMOS incorrecta")
    pcb=PCB.read_text(encoding="utf-8"); premature=[ref for ref,_,_,_ in blocked if f'"{ref}"' in pcb]
    if premature: fail(f"placement prematuro de footprints abiertos: {premature}")
    print("OK: audit footprints PR12 extendido")
    print("- MPR CLOSED; RPW/RDN/RHL/DYC/AQY bloqueados hasta CAD/drawing exacto")
    return 0
if __name__=="__main__": raise SystemExit(main())
