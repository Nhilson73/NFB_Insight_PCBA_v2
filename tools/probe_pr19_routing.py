#!/usr/bin/env python3
"""Inventaría endpoints físicos y propone estrategia determinista para PR19.

No modifica el PCB. Usa el placement PR17 y el contrato PR18 para clasificar cada
net no-GND como local F.Cu, canal B.Cu o potencia In2.Cu.
"""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
PLACEMENT = ROOT / "hardware" / "placement_manifest.json"
CONTRACT = ROOT / "hardware" / "routing_contract.json"
OUT = ROOT / "hardware" / "pr19_routing_probe.json"


def mm(v: int) -> float:
    return round(pcbnew.ToMM(v), 4)


def main() -> int:
    board = pcbnew.LoadBoard(str(PCB))
    placement = json.loads(PLACEMENT.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    zones = {p["ref"]: p["zone"] for p in placement["placements"]}
    zones["J_UNOQ"] = "Z0"

    class_by_net = {}
    for cls in contract["routing_classes"]:
        for net in cls["nets"]:
            if net in class_by_net:
                raise SystemExit(f"ERROR: net duplicada en clases: {net}")
            class_by_net[net] = cls["name"]

    endpoints: dict[str, list[dict]] = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            pos = pad.GetPosition()
            endpoints.setdefault(net, []).append({
                "ref": ref,
                "pad": str(pad.GetNumber()),
                "x_mm": mm(pos.x),
                "y_mm": mm(pos.y),
                "zone": zones.get(ref, "UNKNOWN"),
                "on_fcu": bool(pad.IsOnLayer(pcbnew.F_Cu)),
                "on_bcu": bool(pad.IsOnLayer(pcbnew.B_Cu)),
                "on_in2": bool(pad.IsOnLayer(pcbnew.In2_Cu)),
            })

    expected = set(class_by_net)
    actual = set(endpoints)
    if expected != actual:
        raise SystemExit(f"ERROR: nets PCB/contract divergen missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

    power_classes = {"PWR_INPUT_5A", "PWR_12V_BRANCH", "PWR_5V", "PWR_3V3"}
    local_classes = {"FIELD_ANALOG_LOCAL", "CONTROL_SENSITIVE", "CHILLER_DRY_CONTACT", "ACTUATOR_OUTPUT"}
    channel_nets = []
    routes = []
    for net in sorted(expected):
        eps = endpoints[net]
        zset = sorted({e["zone"] for e in eps})
        cls = class_by_net[net]
        has_host = any(e["ref"] == "J_UNOQ" for e in eps)
        if net == "GND":
            mode = "DEFER_GND_PR20"
        elif cls in power_classes:
            mode = "POWER_IN2"
        elif cls in local_classes and len(zset) == 1:
            mode = "LOCAL_F"
        elif cls == "ANALOG_SENSITIVE" and len(zset) == 1:
            mode = "LOCAL_F_QUIET"
        elif len(zset) == 1 and not has_host:
            mode = "LOCAL_F"
        else:
            mode = "CHANNEL_B"
            channel_nets.append(net)
        routes.append({
            "net": net,
            "class": cls,
            "mode": mode,
            "zones": zset,
            "endpoint_count": len(eps),
            "endpoints": eps,
        })

    # Canales horizontales B.Cu únicos, dejando 8 mm libres arriba/abajo.
    y0, y1 = 12.0, 58.0
    n = max(1, len(channel_nets))
    pitch = (y1 - y0) / max(1, n - 1)
    lane = {net: round(y0 + i * pitch, 3) for i, net in enumerate(channel_nets)}
    for r in routes:
        if r["mode"] == "CHANNEL_B":
            r["trunk_y_mm"] = lane[r["net"]]

    result = {
        "schema_version": 1,
        "status": "PR19_ROUTING_PROBE",
        "board_mm": [placement["board"]["width_mm"], placement["board"]["height_mm"]],
        "net_count": len(routes),
        "channel_count": len(channel_nets),
        "routes": routes,
    }
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    modes = {}
    for r in routes:
        modes[r["mode"]] = modes.get(r["mode"], 0) + 1
    print("PR19_NETS", len(routes))
    print("PR19_MODES", json.dumps(modes, sort_keys=True))
    print("PR19_CHANNELS", len(channel_nets), "pitch_mm", round(pitch, 3))
    for r in routes:
        if r["mode"] == "CHANNEL_B":
            print("CHANNEL", r["net"], r["trunk_y_mm"], r["zones"], r["endpoint_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
