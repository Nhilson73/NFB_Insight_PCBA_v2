#!/usr/bin/env python3
"""PR19A v8: v7 + escape dirigido de PGOOD por el lateral izquierdo de U_5V.

U_5V.1 está en el borde inferior-izquierdo del RDN0011A, pero los demás
endpoints de `5V_PGOOD` están hacia +Y dentro de Z3. El escape genérico de
pitch fino empujaba el pin hacia -Y, dentro de la isla FB/VCC. Esta versión
sale primero por -X, fuera del módulo, y después devuelve el control a A* con
el clearance normal de CONTROL_SENSITIVE.
"""
from __future__ import annotations

import materialize_pr19a_local as impl
import materialize_pr19a_local_v7 as v7

PGOOD_LEFT_ESCAPE_MM = 1.55


class RouterPR19AV8(v7.RouterPR19AV7):
    def _escape_endpoint(self, net: str, ep: dict) -> dict:
        if net == "5V_PGOOD" and ep.get("ref") == "U_5V" and str(ep.get("pad")) == "1":
            out = dict(ep)
            out["x_mm"] = float(ep["x_mm"]) - PGOOD_LEFT_ESCAPE_MM
            print(
                "ESCAPE 5V_PGOOD U_5V.1",
                (ep["x_mm"], ep["y_mm"]),
                "->",
                (out["x_mm"], out["y_mm"]),
            )
            return out
        return super()._escape_endpoint(net, ep)


impl.RouterPR19A = RouterPR19AV8

if __name__ == "__main__":
    raise SystemExit(impl.main())
