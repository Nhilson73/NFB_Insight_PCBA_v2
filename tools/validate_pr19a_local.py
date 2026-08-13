#!/usr/bin/env python3
"""Gate composicional para PR19A: sus 28 nets deben permanecer válidas aunque existan lotes posteriores."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pcbnew  # type: ignore
import validate_pr17_placement as p17

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
PLACEMENT = ROOT / "hardware" / "placement_manifest.json"
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
MANIFEST = ROOT / "hardware" / "pr19a_local_routing_manifest.json"
BASE_DRC = ROOT / "hardware" / "placement_drc_contract.json"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def batch(data: dict) -> dict:
    xs = [b for b in data["batches"] if b["id"] == "PR19A"]
    if len(xs) != 1:
        fail("contrato PR19A ausente/duplicado")
    return xs[0]


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings(k); yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def mentions_net(item, net: str) -> bool:
    return any(s == net or re.search(rf"(?<![A-Za-z0-9_]){re.escape(net)}(?![A-Za-z0-9_])", s) for s in strings(item))


def angle_near(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(((a - b + 180.0) % 360.0) - 180.0) <= tol


def check_frozen_geometry(board, placement: dict) -> None:
    placements = {p["ref"]: p for p in placement["placements"]}
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if set(fps) != ({"J_UNOQ"} | set(placements)):
        fail("refs del PCB cambiaron respecto placement")
    text = PCB.read_text(encoding="utf-8")
    x0, y0, x1, y1 = p17.edge_bbox(text)
    if not (p17.near(x0,0.0) and p17.near(y0,0.0) and p17.near(x1,float(placement["board"]["width_mm"])) and p17.near(y1,float(placement["board"]["height_mm"]))):
        fail(f"outline cambió: {(x0,y0,x1,y1)}")
    host=fps["J_UNOQ"]; hp=host.GetPosition()
    if not (p17.near(p17.mm(hp.x),0.0) and p17.near(p17.mm(hp.y),0.0) and angle_near(host.GetOrientationDegrees(),0.0)):
        fail("J_UNOQ se movió/rotó")
    for ref, expected in placements.items():
        fp=fps[ref]; pos=fp.GetPosition()
        if not (p17.near(p17.mm(pos.x),float(expected["x_mm"])) and p17.near(p17.mm(pos.y),float(expected["y_mm"])) and angle_near(fp.GetOrientationDegrees(),float(expected["rotation_deg"]))):
            fail(f"{ref}: XY/rot cambió")
        if p17.fpid_text(fp) != expected["footprint"]:
            fail(f"{ref}: footprint cambió")
    if re.search(r'^\s*\(zone\b', text, re.M):
        fail("no se permiten copper zones antes de PR20B")


def main() -> int:
    if len(sys.argv) != 2:
        fail("uso: validate_pr19a_local.py <drc.json>")
    drc_path=Path(sys.argv[1])
    for path in (PCB,PLACEMENT,BATCHES,MANIFEST,BASE_DRC,drc_path):
        if not path.exists(): fail(f"falta {path}")
    placement=load(PLACEMENT); batches=load(BATCHES); b=batch(batches); manifest=load(MANIFEST); baseline=load(BASE_DRC); drc=load(drc_path)
    expected=set(b["nets"])
    production=set().union(*(set(x["nets"]) for x in batches["batches"]))
    if int(b["expected_net_count"])!=28 or len(expected)!=28: fail("contrato PR19A ya no es 28 nets únicas")
    if manifest.get("status")!="LOCAL_ROUTING_PR19A": fail("manifest PR19A inválido")
    routed=set(manifest.get("routed_nets",[]))
    if routed!=expected or len(manifest.get("routed_nets",[]))!=28: fail("manifest PR19A no cubre exactamente 28 nets")
    stats=manifest.get("net_stats",[])
    if {x["net"] for x in stats}!=expected or len(stats)!=28: fail("net_stats PR19A incompleto")
    for s in stats:
        if int(s["segment_count"])>220: fail(f"{s['net']}: ruta excesivamente fragmentada")
        if int(s["via_count"])>4: fail(f"{s['net']}: demasiadas vías")

    board=pcbnew.LoadBoard(str(PCB)); check_frozen_geometry(board,placement)
    touched=set(); in1=[]
    for item in board.GetTracks():
        net=item.GetNetname()
        if not net: fail("track/vía sin net")
        touched.add(net)
        if item.GetLayer()==pcbnew.In1_Cu: in1.append(net)
    missing=expected-touched
    if missing: fail(f"PR19A perdió cobre en {sorted(missing)}")
    invalid=touched-production
    if invalid: fail(f"cobre en net no productiva: {sorted(invalid)}")
    if in1: fail(f"signal routing en In1.Cu: {sorted(set(in1))}")

    violations=drc.get("violations",[]); allowed=set(baseline["allowed_warning_types_exact"]); forbidden=set(baseline["forbidden_violation_types"])
    errors=[v for v in violations if v.get("severity")=="error"]
    unexpected=[v for v in violations if v.get("type") in forbidden or v.get("type") not in allowed]
    if errors: fail(f"DRC contiene errores: {len(errors)}; primero={errors[0]}")
    if unexpected: fail(f"DRC contiene tipo nuevo/prohibido: {unexpected[0]}")

    leaking=[]
    for item in drc.get("unconnected_items",[]):
        for net in expected:
            if mentions_net(item,net): leaking.append((net,item)); break
    if leaking: fail(f"PR19A dejó unconnected en {leaking[0][0]}")

    extras=sorted(touched-expected)
    print("OK: PR19A preservado de forma composicional")
    print(f"- 28/28 nets PR19A con cobre; lotes posteriores presentes={len(extras)}")
    print(f"- In1.Cu signal tracks=0; zones=0; DRC errors=0")
    print(f"- unconnected restantes={len(drc.get('unconnected_items',[]))}; ninguno pertenece a PR19A")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
