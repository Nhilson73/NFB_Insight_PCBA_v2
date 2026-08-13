#!/usr/bin/env python3
"""PR19A v4: planner físico v3 + topología explícita para 5V_VCC.

TI define para TPSM33625 (variante RT) que RT conectado a VCC fija 1 MHz.
Por eso `5V_VCC` tiene tres endpoints con roles distintos:
- U_5V.8 = VCC interno / nodo de bypass crítico;
- C_5V_VCC.1 = bypass VCC;
- U_5V.11 = RT, configuración estática a VCC.

No conviene dejar que un MST genérico use U_5V.8 como puente hacia RT. El nodo
físico de referencia es el capacitor: C_VCC -> VCC y C_VCC -> RT. Esta versión
cambia únicamente esa selección de árbol; no cambia netlist, widths, clearance,
capas permitidas ni reglas DRC.
"""
from __future__ import annotations

import materialize_pr19a_local as impl
import materialize_pr19a_local_v3 as v3  # noqa: F401 - instala RouterPR19APhysical
import pr19a_router_core as base

_ORIGINAL_MST = base.mst_edges


def _ep_key(ep: dict) -> tuple[str, str]:
    return str(ep.get("ref")), str(ep.get("pad"))


def mst_pr19a_v4(eps: list[dict]) -> list[tuple[int, int]]:
    keys = [_ep_key(e) for e in eps]
    target = {
        ("C_5V_VCC", "1"),
        ("U_5V", "8"),
        ("U_5V", "11"),
    }
    if len(eps) == 3 and set(keys) == target:
        idx = {key: i for i, key in enumerate(keys)}
        cap = idx[("C_5V_VCC", "1")]
        vcc = idx[("U_5V", "8")]
        rt = idx[("U_5V", "11")]
        edges = [(cap, vcc), (cap, rt)]
        print("TOPOLOGY 5V_VCC STAR", [(keys[a], keys[b]) for a, b in edges])
        return edges
    return _ORIGINAL_MST(eps)


base.mst_edges = mst_pr19a_v4

if __name__ == "__main__":
    raise SystemExit(impl.main())
