#!/usr/bin/env python3
"""PR19A v10: v9 + endpoints lógicos para pads compuestos del TPS259470A.

El footprint RPW0010A usa más de un shape SMD con el mismo número de pin para
algunos terminales (1/7/10). KiCad los interpreta como un único pin eléctrico;
un árbol de routing no debe convertir esos shapes solapados en nodos distintos.

Regla:
- todos los shapes siguen participando en ocupación/DRC;
- para construir el árbol se conserva un solo endpoint por (ref, pin);
- en U_EFUSE se elige como breakout el shape cuyo centro está más alejado del
  centro del footprint, es decir, el shape exterior;
- ninguna net, clearance, footprint o placement cambia.
"""
from __future__ import annotations

import json

import materialize_pr19a_local as impl
import materialize_pr19a_local_v9 as v9  # noqa: F401 - instala orden eFuse + clase v8
import pr19a_router_core as base

ORIGINAL_BUILD_PROBE = impl.build_probe
PINS_COMPOUND_REF = "U_EFUSE"


def build_probe_logical(board, placement: dict, routing: dict, batch: dict) -> dict:
    probe = ORIGINAL_BUILD_PROBE(board, placement, routing, batch)
    wanted = set(batch["nets"])
    counts = {n: set() for n in wanted}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNetname() or ""
            if net in wanted:
                counts[net].add((ref, str(pad.GetNumber())))
    for route in probe["routes"]:
        route["physical_pad_shape_count"] = int(route["endpoint_count"])
        route["endpoint_count"] = len(counts[route["net"]])
    impl.PROBE_OUT.write_text(json.dumps(probe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return probe


class RouterPR19AV10(impl.RouterPR19A):
    def __init__(self, board, placement, contract, probe, batch):
        super().__init__(board, placement, contract, probe, batch)
        by_ref = {p["ref"]: p for p in placement["placements"]}
        center = by_ref[PINS_COMPOUND_REF]
        cx, cy = float(center["x_mm"]), float(center["y_mm"])

        for net, eps in list(self.pads_by_net.items()):
            groups: dict[tuple[str, str], list[dict]] = {}
            order = []
            for ep in eps:
                key = (str(ep["ref"]), str(ep["pad"]))
                if key not in groups:
                    groups[key] = []
                    order.append(key)
                groups[key].append(ep)

            logical = []
            for key in order:
                choices = groups[key]
                if key[0] == PINS_COMPOUND_REF and len(choices) > 1:
                    choices = sorted(
                        choices,
                        key=lambda e: (
                            -((float(e["x_mm"])-cx)**2 + (float(e["y_mm"])-cy)**2),
                            float(e["x_mm"]),
                            float(e["y_mm"]),
                        ),
                    )
                    chosen = choices[0]
                    print(
                        "COMPOUND_PAD",
                        net,
                        f"{key[0]}.{key[1]}",
                        "shapes", len(groups[key]),
                        "breakout", (round(chosen["x_mm"], 4), round(chosen["y_mm"], 4)),
                    )
                    logical.append(chosen)
                else:
                    # Fuera del caso compuesto explícito, conservar exactamente
                    # la semántica previa; si aparecen duplicados inesperados se
                    # elige el primero determinísticamente y queda visible en probe.
                    logical.append(choices[0])
            self.pads_by_net[net] = logical


impl.build_probe = build_probe_logical
impl.RouterPR19A = RouterPR19AV10

if __name__ == "__main__":
    raise SystemExit(impl.main())
