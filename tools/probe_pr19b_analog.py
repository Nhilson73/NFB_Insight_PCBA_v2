#!/usr/bin/env python3
"""Extrae endpoints y ocupación real para PR19B sin modificar el PCB.

El probe se ejecuta sobre el checkpoint PR19A ya persistido. Su propósito es
congelar evidencia antes de materializar las cuatro nets analógicas long-haul.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
PLACEMENT = ROOT / "hardware" / "placement_manifest.json"
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
OUT = ROOT / "hardware" / "pr19b_analog_probe.json"
TARGET = ["PH_ADC", "ORP_ADC", "DO_ADC", "PUMP_CURRENT_ADC"]


def mm(v: int) -> float:
    return round(float(pcbnew.ToMM(v)), 4)


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def main() -> int:
    board = pcbnew.LoadBoard(str(PCB))
    placement = json.loads(PLACEMENT.read_text(encoding="utf-8"))
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    batch = next((b for b in batches["batches"] if b["id"] == "PR19B"), None)
    if not batch or batch["nets"] != TARGET or int(batch["expected_net_count"]) != 4:
        fail("contrato PR19B diverge del alcance esperado")

    by_ref = {p["ref"]: p for p in placement["placements"]}
    endpoints: dict[str, list[dict]] = {n: [] for n in TARGET}
    seen = set()
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNetname() or ""
            if net not in endpoints:
                continue
            key = (net, ref, str(pad.GetNumber()))
            if key in seen:
                continue
            seen.add(key)
            pos = pad.GetPosition()
            ep = {
                "ref": ref,
                "pad": str(pad.GetNumber()),
                "x_mm": mm(pos.x),
                "y_mm": mm(pos.y),
                "zone": by_ref.get(ref, {}).get("zone", "UNKNOWN"),
                "layers": [
                    name for lid, name in ((pcbnew.F_Cu, "F.Cu"), (pcbnew.B_Cu, "B.Cu"))
                    if pad.IsOnLayer(lid)
                ],
            }
            endpoints[net].append(ep)

    for net, eps in endpoints.items():
        if len(eps) < 2:
            fail(f"{net}: menos de dos endpoints lógicos: {eps}")

    copper_by_net = Counter()
    existing_segments = []
    existing_vias = []
    target_copper = Counter()
    for item in board.GetTracks():
        net = item.GetNetname() or ""
        copper_by_net[net] += 1
        if net in TARGET:
            target_copper[net] += 1
        if isinstance(item, pcbnew.PCB_VIA):
            p = item.GetPosition()
            existing_vias.append({
                "net": net,
                "x_mm": mm(p.x),
                "y_mm": mm(p.y),
                "diameter_mm": mm(item.GetWidth()),
                "drill_mm": mm(item.GetDrillValue()),
            })
        else:
            a, b = item.GetStart(), item.GetEnd()
            existing_segments.append({
                "net": net,
                "layer": board.GetLayerName(item.GetLayer()),
                "width_mm": mm(item.GetWidth()),
                "start_mm": [mm(a.x), mm(a.y)],
                "end_mm": [mm(b.x), mm(b.y)],
            })

    if any(target_copper.values()):
        fail(f"PR19B debe iniciar sin cobre propio; encontrado {dict(target_copper)}")

    routed_existing = sorted(n for n, c in copper_by_net.items() if n and c > 0)
    pr19a = next(b for b in batches["batches"] if b["id"] == "PR19A")
    unexpected = sorted(set(routed_existing) - set(pr19a["nets"]))
    if unexpected:
        fail(f"cobre previo fuera de PR19A: {unexpected}")

    route_summary = []
    for net in TARGET:
        eps = sorted(endpoints[net], key=lambda x: (x["x_mm"], x["y_mm"], x["ref"], x["pad"]))
        zones = sorted({e["zone"] for e in eps})
        route_summary.append({
            "net": net,
            "endpoint_count": len(eps),
            "zones": zones,
            "endpoints": eps,
            "manhattan_span_mm": round((max(e["x_mm"] for e in eps)-min(e["x_mm"] for e in eps)) + (max(e["y_mm"] for e in eps)-min(e["y_mm"] for e in eps)), 3),
        })

    out = {
        "schema_version": 1,
        "status": "PR19B_ANALOG_PROBE_PRE_ROUTE",
        "batch": "PR19B",
        "target_nets": TARGET,
        "route_summary": route_summary,
        "baseline": {
            "existing_routed_nets": routed_existing,
            "existing_segment_count": len(existing_segments),
            "existing_via_count": len(existing_vias),
            "copper_items_by_net": dict(sorted(copper_by_net.items())),
            "target_copper_items": dict(target_copper),
        },
        "existing_segments": existing_segments,
        "existing_vias": existing_vias,
        "invariants": {
            "placement_status": placement.get("status"),
            "board_width_mm": placement["board"]["width_mm"],
            "board_height_mm": placement["board"]["height_mm"],
            "in1_signal_routing": False,
            "future_batch_copper_allowed": False,
        },
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PR19B_PROBE_OK")
    for r in route_summary:
        print(r["net"], r["zones"], r["endpoints"])
    print("baseline segments", len(existing_segments), "vias", len(existing_vias))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
