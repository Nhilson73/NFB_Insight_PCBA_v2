#!/usr/bin/env python3
"""Valida cierre físico PR13 y su uso de placement únicamente bajo gate PR17."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"hardware"/"footprint_audit.json"
POWER=ROOT/"hardware"/"power_production_netlist.json"
Z4=ROOT/"hardware"/"z4_production_netlist.json"
PCB=ROOT/"kicad"/"NFB_Insight_PCBA_v2.kicad_pcb"
PLACEMENT=ROOT/"hardware"/"placement_manifest.json"
FPDIR=ROOT/"kicad"/"lib"/"nfb_footprints.pretty"
FPS={"RPW":FPDIR/"TI_RPW0010A_TPS259470A.kicad_mod","RDN":FPDIR/"TI_RDN0011A_TPSM33625.kicad_mod","RHL":FPDIR/"TI_RHL0020B_DRV8242.kicad_mod","DYC":FPDIR/"TI_DYC0008A_TPS1HC120.kicad_mod","AQY":FPDIR/"Panasonic_AQY212EHAX_DIP4_SMD.kicad_mod","MPR":FPDIR/"Honeywell_MPR_LongPort_12Pad.kicad_mod"}
def fail(m): raise SystemExit("ERROR: "+m)
def main():
    for p in (AUDIT,POWER,Z4,PCB,*FPS.values()):
        if not p.exists(): fail(f"falta {p.relative_to(ROOT)}")
    a=json.loads(AUDIT.read_text(encoding="utf-8"))
    if a.get("schema_version")!=3 or a.get("status")!="FOOTPRINT_AUDIT_CLOSED_PR13": fail("audit no es cierre PR13")
    pol=a.get("policy",{})
    if not pol.get("primary_source_required") or not pol.get("do_not_invent_land_patterns") or not pol.get("placement_requires_closed_audit"): fail("política audit debilitada")
    if pol.get("secondary_ai_audit_is_crosscheck_only") is not True: fail("Spark debe permanecer cross-check, no autoridad")
    by={x["id"]:x for x in a["audits"]}; required={"UNO_Q_CARRIER_ROTATED","MPR_LONG_PORT_12PAD","TPS25947_RPW0010A","TPSM33625_RDN11","DRV8242_RHL20","TPS1HC120_DYC8","AQY212EHAX_DIP4_SMD"}
    if set(by)!=required: fail("set de auditorías incompleto")
    for aid in required:
        if by[aid].get("placement_allowed") is not True: fail(f"{aid} no quedó autorizado")
    expected_fp={"TPS25947_RPW0010A":"NFB:TI_RPW0010A_TPS259470A","TPSM33625_RDN11":"NFB:TI_RDN0011A_TPSM33625","DRV8242_RHL20":"NFB:TI_RHL0020B_DRV8242","TPS1HC120_DYC8":"NFB:TI_DYC0008A_TPS1HC120","AQY212EHAX_DIP4_SMD":"NFB:Panasonic_AQY212EHAX_DIP4_SMD"}
    for aid,fp in expected_fp.items():
        if by[aid].get("footprint")!=fp or not str(by[aid].get("status","")).startswith("CLOSED_PRIMARY_SOURCE"): fail(f"{aid} no cerrado")
    rpw=FPS["RPW"].read_text(encoding="utf-8"); nums=[int(x) for x in re.findall(r'\(pad "(\d+)"',rpw)]
    if set(nums)!=set(range(1,11)) or len(nums)!=14: fail("RPW debe tener 10 pads lógicos / 14 primitives")
    for n in (1,4,7,10):
        if nums.count(n)!=2: fail(f"RPW pad {n} no forma land L")
    for marker in ("TI MPQF568 / 4225183/A","(size 0.300 2.400)","0.094461"):
        if marker not in rpw: fail(f"RPW sin {marker}")
    rdn=FPS["RDN"].read_text(encoding="utf-8")
    for marker in ("4226623/F","(pad \"4\"","(pad \"5\"","(size 1.600 2.150)","0.125mm stencil","72% paste"):
        if marker not in rdn: fail(f"RDN sin {marker}")
    if rdn.count('(pad "" smd rect')<10: fail("RDN sin ventanas de paste dedicadas")
    rhl=FPS["RHL"].read_text(encoding="utf-8"); nums=[int(x) for x in re.findall(r'\(pad "(\d+)"',rhl)]
    if set(nums)!=set(range(1,22)) or nums.count(21)!=1: fail("RHL no contiene pads 1..21")
    if "RHL0020B / 4226154/B" not in rhl or "RHL0020A" in rhl: fail("RHL no usa revisión B")
    if '(pad "21" smd rect (at 0 0) (size 2.050 3.050)' not in rhl: fail("RHL EP21 incorrecto")
    if rhl.count('(pad "" smd roundrect')!=4: fail("RHL EP sin 4 ventanas paste")
    dyc=FPS["DYC"].read_text(encoding="utf-8"); nums=[int(x) for x in re.findall(r'\(pad "(\d+)"',dyc)]
    if nums!=list(range(1,9)) or '(pad "9"' in dyc: fail("DYC debe tener exactamente pads 1..8")
    for marker in ("4226548/B","EXACTLY 8 PADS / NO EP","(size 0.850 0.220)"):
        if marker not in dyc: fail(f"DYC sin {marker}")
    aqy=FPS["AQY"].read_text(encoding="utf-8"); nums=[int(x) for x in re.findall(r'\(pad "(\d+)"',aqy)]
    if nums!=[1,2,3,4]: fail("AQY no tiene 4 pads")
    for marker in ("AQY212EHAX","STYLE X","(at -4.150 1.270)","(at 4.150 -1.270)","(size 1.500 1.500)","SELV <=48V ONLY / NO MAINS"):
        if marker not in aqy: fail(f"AQY sin {marker}")
    power=json.loads(POWER.read_text(encoding="utf-8")); z4=json.loads(Z4.read_text(encoding="utf-8")); pc={x["ref"]:x for x in power["components"]}; zc={x["ref"]:x for x in z4["components"]}
    if power.get("schema_version")!=2 or power.get("status")!="FROZEN_POWER_NETLIST_PR10_FOOTPRINTS_CLOSED_PR13": fail("power no enlaza cierre PR13")
    if z4.get("schema_version")!=2 or z4.get("status")!="FROZEN_Z4_NETLIST_PR12_FOOTPRINTS_CLOSED_PR13": fail("Z4 no enlaza cierre PR13")
    actual={"U_EFUSE":pc["U_EFUSE"]["footprint"],"U_5V":pc["U_5V"]["footprint"],"U_PUMP_DRV":zc["U_PUMP_DRV"]["footprint"],"U_CO2_DRV":zc["U_CO2_DRV"]["footprint"],"U_CHILLER":zc["U_CHILLER"]["footprint"]}
    if set(actual.values())!=set(expected_fp.values()): fail(f"netlists no usan footprints cerrados: {actual}")
    if any("PENDING_" in x for x in actual.values()): fail("quedó placeholder crítico")
    if z4.get("open_placement_gates")!=[]: fail("Z4 conserva placement gates abiertos")
    pcb=PCB.read_text(encoding="utf-8"); placed=[r for r in actual if f'"{r}"' in pcb]
    if placed:
        if not PLACEMENT.exists(): fail(f"footprints críticos colocados sin manifest PR17: {placed}")
        pm=json.loads(PLACEMENT.read_text(encoding="utf-8"))
        if pm.get("status")!="PRODUCTION_PLACEMENT_PR17" or pm.get("policies",{}).get("routing_allowed") is not False: fail("placement crítico sin gate PR17 válido")
        pmap={x["ref"]:x for x in pm.get("placements",[])}
        if any(r not in pmap for r in placed): fail("footprint crítico colocado sin trazabilidad PR17")
        if re.search(r'^\s*\((segment|arc|via|zone)\b',pcb,re.M): fail("PR17 contiene routing/cobre prematuro")
    print("OK: footprint closure PR13 — 5/5 críticos cerrados contra fuentes primarias")
    print(f"- placement PR17 trazado={len(placed)} críticos; routing=0")
    print("- Spark archivado como cross-check; correcciones TI/Panasonic prevalecen")
    return 0
if __name__=="__main__": raise SystemExit(main())
