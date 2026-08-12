#!/usr/bin/env python3
"""Preserva PR4 como trazabilidad sin permitir que reemplace el baseline PR6."""
from __future__ import annotations
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DONOR=ROOT/"hardware"/"analog_insight_manifest.json"; DONOR_BOM=ROOT/"bom"/"insight_analog_inheritance.csv"; PROD=ROOT/"hardware"/"sensor_interface_contract.json"; PROD_BOM=ROOT/"bom"/"insight_z1_production_bom.csv"; SCH=ROOT/"kicad"/"analog_insight.kicad_sch"
EXPECTED={"PH","ORP","TEMP","CO2","DO"}
def fail(m): raise SystemExit("ERROR: "+m)
def rows(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def main():
    d=json.loads(DONOR.read_text(encoding="utf-8")); p=json.loads(PROD.read_text(encoding="utf-8"))
    if {c["id"] for c in d["channels"]}!=EXPECTED: fail("PR4 perdió trazabilidad")
    if p.get("status")!="Z1_PRODUCTION_BASELINE_PR6": fail("PR6 no es baseline")
    ex=d.get("explicitly_not_inherited",[])
    if len(ex)!=1 or ex[0].get("arduino")!="A3": fail("exclusión HUM PR4 cambió")
    db=rows(DONOR_BOM); pb=rows(PROD_BOM)
    if {r["canal"] for r in db}!=EXPECTED or {r["canal"] for r in pb}!=EXPECTED: fail("BOM perdió cobertura de funciones")
    txt=" ".join((r.get("valor","")+" "+r.get("mpn_o_familia","")) for r in pb)
    for token in ("BNC","MPX5700AP","SN6501","AMC1301","750315371"):
        if token.upper() in txt.upper(): fail(f"baseline PR6 revive {token}")
    hist=SCH.read_text(encoding="utf-8")
    for marker in ("PH / A0","ORP / A1","CO2 / A4","DO / A5","A3 / HUM_ADC: NO MIGRAR"):
        if marker not in hist: fail(f"hoja PR4 perdió {marker}")
    print("OK: PR4 preservado como historial y PR6 gobierna producción")
    return 0
if __name__=="__main__": raise SystemExit(main())
