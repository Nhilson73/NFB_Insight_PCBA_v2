#!/usr/bin/env python3
"""Gate de aceptación para PR19A: 28 nets locales o nada."""
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
TOL = 1e-3


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
            yield from strings(k)
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def mentions_net(item, net: str) -> bool:
    for s in strings(item):
        if s == net or re.search(rf"(?<![A-Za-z0-9_]){re.escape(net)}(?![A-Za-z0-9_])", s):
            return True
    return False


def check_frozen_geometry(board, placement: dict) -> None:
    placements = {p["ref"]: p for p in placement["placements"]}
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if set(fps) != ({"J_UNOQ"} | set(placements)):
        fail("refs del PCB cambiaron respecto placement PR17")

    text = PCB.read_text(encoding="utf-8")
    x0, y0, x1, y1 = p17.edge_bbox(text)
    if not (
        p17.near(x0, 0.0) and p17.near(y0, 0.0)
        and p17.near(x1, float(placement["board"]["width_mm"]))
        and p17.near(y1, float(placement["board"]["height_mm"]))
    ):
        fail(f"outline cambió: {(x0,y0,x1,y1)}")

    host = fps["J_UNOQ"]
    hp = host.GetPosition()
    if not (p17.near(p17.mm(hp.x), 0.0) and p17.near(p17.mm(hp.y), 0.0) and p17.near(host.GetOrientationDegrees(), 0.0)):
        fail("J_UNOQ se movió/rotó")

    for ref, expected in placements.items():
        fp = fps[ref]
        pos = fp.GetPosition()
        actual = (p17.mm(pos.x), p17.mm(pos.y), fp.GetOrientationDegrees())
        target = (float(expected["x_mm"]), float(expected["y_mm"]), float(expected["rotation_deg"]))
        if not all(p17.near(a, b) for a, b in zip(actual, target)):
            fail(f"{ref}: XY/rot cambió actual={actual} target={target}")
        if p17.fpid_text(fp) != expected["footprint"]:
            fail(f"{ref}: footprint cambió")

    if re.search(r'^\s*\(zone\b', text, re.M):
        fail("PR19A no puede añadir copper zones")


def main() -> int:
    if len(sys.argv) != 2:
        fail("uso: validate_pr19a_local.py <drc.json>")
    drc_path = Path(sys.argv[1])
    for path in (PCB, PLACEMENT, BATCHES, MANIFEST, BASE_DRC, drc_path):
        if not path.exists():
            fail(f"falta {path}")

    placement = load(PLACEMENT)
    batches = load(BATCHES)
    b = batch(batches)
    manifest = load(MANIFEST)
    baseline = load(BASE_DRC)
    drc = load(drc_path)

    expected = set(b["nets"])
    if int(b["expected_net_count"]) != 28 or len(expected) != 28:
        fail("contrato PR19A ya no es 28 nets únicas")
    if manifest.get("status") != "LOCAL_ROUTING_PR19A":
        fail("manifest PR19A inválido")
    routed = set(manifest.get("routed_nets", []))
    if routed != expected or len(manifest.get("routed_nets", [])) != 28:
        fail(f"routed_nets != PR19A; faltan={sorted(expected-routed)} sobran={sorted(routed-expected)}")
    future = set().union(*(set(x["nets"]) for x in batches["batches"] if x["id"] != "PR19A"))
    if routed & future:
        fail(f"PR19A tocó lote futuro: {sorted(routed & future)}")

    stats = manifest.get("net_stats", [])
    if {x["net"] for x in stats} != expected or len(stats) != 28:
        fail("net_stats no cubre exactamente 28 nets")
    for s in stats:
        if int(s["segment_count"]) > 220:
            fail(f"{s['net']}: ruta local excesivamente fragmentada ({s['segment_count']} segmentos)")
        if int(s["via_count"]) > 4:
            fail(f"{s['net']}: demasiadas vías para lote local ({s['via_count']})")

    board = pcbnew.LoadBoard(str(PCB))
    check_frozen_geometry(board, placement)

    touched = set()
    in1_items = []
    track_count = 0
    via_count = 0
    for item in board.GetTracks():
        net = item.GetNetname()
        if not net:
            fail("track/vía sin net")
        touched.add(net)
        track_count += 1
        try:
            if isinstance(item, pcbnew.PCB_VIA):
                via_count += 1
        except TypeError:
            pass
        if item.GetLayer() == pcbnew.In1_Cu:
            in1_items.append(net)
    if touched != expected:
        fail(f"cobre PCB != lote PR19A; faltan={sorted(expected-touched)} sobran={sorted(touched-expected)}")
    if in1_items:
        fail(f"PR19A usó In1.Cu para signal routing: {sorted(set(in1_items))}")

    violations = drc.get("violations", [])
    allowed_warning_types = set(baseline["allowed_warning_types_exact"])
    forbidden_types = set(baseline["forbidden_violation_types"])
    unexpected = []
    errors = []
    warning_types = {}
    for v in violations:
        typ = v.get("type", "?")
        sev = v.get("severity", "?")
        warning_types[typ] = warning_types.get(typ, 0) + 1
        if sev == "error":
            errors.append(v)
        if typ in forbidden_types or typ not in allowed_warning_types:
            unexpected.append(v)
    if errors:
        fail(f"DRC contiene errores: {len(errors)}; primero={errors[0]}")
    if unexpected:
        fail(f"DRC contiene tipo nuevo/prohibido: {unexpected[0]}")

    unconnected = drc.get("unconnected_items", [])
    leaking = []
    for item in unconnected:
        for net in expected:
            if mentions_net(item, net):
                leaking.append((net, item))
                break
    if leaking:
        fail(f"PR19A no cerró 28/28; unconnected en {leaking[0][0]}: {leaking[0][1]}")
    if len(unconnected) >= int(baseline["expected_unconnected_items"]):
        fail(f"routing no redujo unconnected: {len(unconnected)} >= baseline {baseline['expected_unconnected_items']}")

    worst = sorted(stats, key=lambda x: (int(x["segment_count"]), int(x["via_count"])), reverse=True)[:5]
    print("OK: PR19A lote local aceptable")
    print(f"- 28/28 nets con cobre; tracks/vías items={track_count}, vías={via_count}")
    print(f"- 0 nets futuras; In1.Cu signal tracks=0; zones=0")
    print(f"- DRC errors=0; tipos warning={warning_types}")
    print(f"- unconnected restantes={len(unconnected)}; ninguno pertenece a PR19A")
    print("- rutas más fragmentadas:")
    for s in worst:
        print(f"  {s['net']}: seg={s['segment_count']} vias={s['via_count']} len={s['length_mm']} mm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
