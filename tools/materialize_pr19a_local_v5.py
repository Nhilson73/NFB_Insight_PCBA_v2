#!/usr/bin/env python3
"""PR19A v5: topología estrella 5V_VCC + escape RT hacia corredor libre.

No añade reglas DRC ni reduce clearances. El objetivo es comprobar primero si
una geometría de escape mejor elegida basta bajo las reglas existentes.
"""
from __future__ import annotations

import materialize_pr19a_local as impl
import materialize_pr19a_local_v3 as v3
import materialize_pr19a_local_v4 as v4  # noqa: F401 - instala MST estrella 5V_VCC


class RouterPR19AV5(v3.RouterPR19APhysical):
    def _escape_endpoint(self, net: str, ep: dict) -> dict:
        if net == "5V_VCC" and ep.get("ref") == "U_5V" and str(ep.get("pad")) == "11":
            # U_5V está congelado por PR17/PR22. El target queda justo bajo el
            # borde inferior del módulo y centrado en el corredor físico entre
            # R_5V_FBT y R_5V_FBB, evitando prolongar el escape por la garganta.
            fp = self._placement_by_ref["U_5V"]
            out = dict(ep)
            out["x_mm"] = float(fp["x_mm"]) - 0.775
            out["y_mm"] = float(fp["y_mm"]) - 2.505
            print(
                "ESCAPE 5V_VCC RT",
                (ep["x_mm"], ep["y_mm"]),
                "->",
                (out["x_mm"], out["y_mm"]),
            )
            return out
        return super()._escape_endpoint(net, ep)


impl.RouterPR19A = RouterPR19AV5

if __name__ == "__main__":
    raise SystemExit(impl.main())
