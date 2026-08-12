#!/usr/bin/env python3
"""Valida invariantes mecánicas V2 y la expansión +X autorizada por PR17."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
FP = ROOT / "kicad" / "lib" / "nfb_footprints.pretty" / "Arduino_UNO_Q_Carrier_Rotated.kicad_mod"
PLACEMENT = ROOT / "hardware" / "placement_manifest.json"

EXPECTED_HOLES = {(50.80, 13.97),(45.72, 66.04),(17.78, 66.04),(2.54, 15.24)}
EXPECTED_PADS = {"1": (50.80, 27.94),"14": (50.80, 63.50),"32": (2.54, 18.80),"15": (2.54, 63.50)}

def fail(msg: str) -> None:
    print(f"ERROR: {msg}"); sys.exit(1)
def near(a: float, b: float, tol: float = 1e-3) -> bool: return abs(a-b)<=tol

def edge_bbox(pcb: str):
    lines=[]
    pat=re.compile(r'\(gr_line\s+\(start\s+([-0-9.]+)\s+([-0-9.]+)\)\s+\(end\s+([-0-9.]+)\s+([-0-9.]+)\).*?\(layer\s+"Edge\.Cuts"\)',re.S)
    for a,b,c,d in pat.findall(pcb): lines.append(tuple(map(float,(a,b,c,d))))
    if len(lines)!=4: fail(f"Edge.Cuts rectangular esperado con 4 líneas; encontradas={len(lines)}")
    xs=[v for ln in lines for v in (ln[0],ln[2])]; ys=[v for ln in lines for v in (ln[1],ln[3])]
    return min(xs),min(ys),max(xs),max(ys)

def main() -> int:
    if not PCB.exists() or not FP.exists(): fail("faltan archivos mecánicos KiCad")
    pcb=PCB.read_text(encoding="utf-8"); fp=FP.read_text(encoding="utf-8")
    target_w=220.0; mode="PREPLACEMENT"
    if PLACEMENT.exists():
        pm=json.loads(PLACEMENT.read_text(encoding="utf-8"))
        if pm.get("status")=="PRODUCTION_PLACEMENT_PR17":
            if pm.get("policies",{}).get("routing_allowed") is not False: fail("manifest PR17 habilita routing")
            if pm.get("board",{}).get("growth_only")!="+X": fail("PR17 perdió crecimiento solo +X")
            target_w=float(pm["board"]["width_mm"]); mode="PR17"
    x0,y0,x1,y1=edge_bbox(pcb)
    if not (near(x0,0) and near(y0,0) and near(x1,target_w) and near(y1,68.58)): fail(f"Edge.Cuts {(x0,y0,x1,y1)} != (0,0,{target_w},68.58)")
    if target_w<53.34: fail("ancho board invade envolvente UNO Q")
    if "FIELD I/O EDGE" not in pcb: fail("falta la identificación FIELD I/O EDGE")
    if "USB-C -> -Y" not in fp and "USB-C → -Y" not in pcb: fail("falta orientación USB-C hacia -Y")
    holes={(float(x),float(y)) for x,y in re.findall(r'\(pad \"\" np_thru_hole circle \(at ([0-9.]+) ([0-9.]+)\)',fp)}
    for e in EXPECTED_HOLES:
        if not any(near(e[0],x) and near(e[1],y) for x,y in holes): fail(f"agujero UNO Q ausente o movido: {e}")
    found={n:(float(x),float(y)) for n,x,y in re.findall(r'\(pad \"([0-9]+)\" thru_hole \w+ \(at ([0-9.]+) ([0-9.]+)\)',fp)}
    for n,e in EXPECTED_PADS.items():
        a=found.get(n)
        if a is None or not (near(a[0],e[0]) and near(a[1],e[1])): fail(f"pad {n} fuera de posición: esperado {e}, actual {a}")
    for label in ["Z0 UNO Q INMUTABLE","Z1 ANALÓGICO / AISLAMIENTO","Z2 DIGITAL / BAJO RUIDO","Z3 POTENCIA","Z4 ACTUADORES"]:
        if label not in pcb: fail(f"falta guía funcional: {label}")
    for label in ["EXCLUSIÓN USB-C / PMIC","EXCLUSIÓN JCTL","EXCLUSIÓN SPI2 / JSPI","EXCLUSIÓN QWIIC"]:
        if label not in pcb: fail(f"falta referencia mecánica: {label}")
    if mode=="PR17":
        pm=json.loads(PLACEMENT.read_text(encoding="utf-8")); zb=pm["zone_bounds_mm"]
        if not near(float(zb["Z0"]["x_min"]),0) or not near(float(zb["Z0"]["x_max"]),53.34): fail("Z0 PR17 cambió")
        if not near(float(zb["Z4"]["x_max"]),target_w): fail("Z4 no termina en borde +X")
    print("OK: invariantes mecánicas V2 verificadas")
    print("- origen global UNO Q: (0,0); envolvente 53.34 x 68.58 mm")
    print(f"- board: {target_w:.2f} x 68.58 mm; modo={mode}; crecimiento solo +X")
    print("- USB-C hacia -Y; 4 agujeros y extremos de headers verificados")
    return 0
if __name__ == "__main__": raise SystemExit(main())
