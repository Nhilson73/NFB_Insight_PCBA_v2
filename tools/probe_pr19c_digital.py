#!/usr/bin/env python3
"""Probe read-only del lote PR19C sobre el checkpoint acumulado PR19A+PR19B."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
PLACEMENT = ROOT / "hardware" / "placement_manifest.json"
BATCHES = ROOT / "hardware" / "routing_batches_contract.json"
OUT = ROOT / "hardware" / "pr19c_digital_probe.json"
TARGET = [
    "ACT_FAULT_N", "CHILLER_CTL", "CO2_SOL_CTL",
    "HMI_RX", "HMI_TX", "HX711_DOUT", "HX711_SCK",
    "I2C_SCL", "I2C_SDA", "LED_STATUS", "MCU_NRST", "MCU_WDI",
    "PUMP_DIR", "PUMP_PWM", "TEMP_1WIRE", "UNO_IOREF_3V3",
]
BASELINE_SEGMENTS = 555
BASELINE_VIAS = 31


def mm(v: int) -> float:
    return round(float(pcbnew.ToMM(v)), 4)


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def main() -> int:
    board = pcbnew.LoadBoard(str(PCB))
    placement = json.loads(PLACEMENT.read_text(encoding="utf-8"))
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))
    by_batch = {b["id"]: b for b in batches["batches"]}
    batch = by_batch.get("PR19C")
    if not batch or batch["nets"] != TARGET or int(batch["expected_net_count"]) != 16:
        fail("contrato PR19C diverge del alcance esperado")

    seg0 = sum(not isinstance(x, pcbnew.PCB_VIA) for x in board.GetTracks())
    via0 = sum(isinstance(x, pcbnew.PCB_VIA) for x in board.GetTracks())
    if (seg0, via0) != (BASELINE_SEGMENTS, BASELINE_VIAS):
        fail(f"baseline acumulado inesperado: {(seg0, via0)}")

    authorized_prior = set(by_batch["PR19A"]["nets"]) | set(by_batch["PR19B"]["nets"])
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
                "x_mm": mm(p.x), "y_mm": mm(p.y),
                "diameter_mm": mm(item.GetWidth()),
                "drill_mm": mm(item.GetDrillValue()),
            })
        else:
            a, z = item.GetStart(), item.GetEnd()
            existing_segments.append({
                "net": net,
                "layer": board.GetLayerName(item.GetLayer()),
                "width_mm": mm(item.GetWidth()),
                "start_mm": [mm(a.x), mm(a.y)],
                "end_mm": [mm(z.x), mm(z.y)],
            })
    if any(target_copper.values()):
        fail(f"PR19C debe iniciar sin cobre propio: {dict(target_copper)}")
    routed_existing = sorted(n for n, c in copper_by_net.items() if n and c > 0)
    unexpected = sorted(set(routed_existing) - authorized_prior)
    if unexpected:
        fail(f"cobre previo fuera de PR19A+PR19B: {unexpected}")

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
            endpoints[net].append({
                "ref": ref,
                "pad": str(pad.GetNumber()),
                "x_mm": mm(pos.x), "y_mm": mm(pos.y),
                "zone": by_ref.get(ref, {}).get("zone", "UNKNOWN"),
                "layers": [
                    name for lid, name in ((pcbnew.F_Cu, "F.Cu"), (pcbnew.B_Cu, "B.Cu"))
                    if pad.IsOnLayer(lid)
                ],
            })

    route_summary = []
    for net in TARGET:
        eps = sorted(endpoints[net], key=lambda x: (x["x_mm"], x["y_mm"], x["ref"], x["pad"]))
        if len(eps) < 2:
            fail(f"{net}: menos de dos endpoints lógicos: {eps}")
        route_summary.append({
            "net": net,
            "endpoint_count": len(eps),
            "zones": sorted({e["zone"] for e in eps}),
            "endpoints": eps,
            "manhattan_span_mm": round(
                (max(e["x_mm"] for e in eps)-min(e["x_mm"] for e in eps)) +
                (max(e["y_mm"] for e in eps)-min(e["y_mm"] for e in eps)), 3),
        })

    future = set(by_batch["PR20A"]["nets"]) | set(by_batch["PR20B"]["nets"])
    out = {
        "schema_version": 1,
        "status": "PR19C_DIGITAL_PROBE_PRE_ROUTE",
        "batch": "PR19C",
        "target_nets": TARGET,
        "route_summary": route_summary,
        "baseline": {
            "existing_routed_nets": routed_existing,
            "existing_segment_count": len(existing_segments),
            "existing_via_count": len(existing_vias),
            "target_copper_items": dict(target_copper),
        },
        "existing_segments": existing_segments,
        "existing_vias": existing_vias,
        "invariants": {
            "placement_status": placement.get("status"),
            "board_width_mm": placement["board"]["width_mm"],
            "board_height_mm": placement["board"]["height_mm"],
            "in1_signal_routing": False,
            "future_batch_nets": sorted(future),
            "future_batch_copper_allowed": False,
        },
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PR19C_PROBE_OK")
    for r in route_summary:
        print(r["net"], "eps", r["endpoint_count"], "zones", r["zones"], "span", r["manhattan_span_mm"])
        for ep in r["endpoints"]:
            print("  ", ep)
    print("baseline segments", len(existing_segments), "vias", len(existing_vias))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
