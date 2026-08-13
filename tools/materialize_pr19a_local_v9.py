#!/usr/bin/env python3
"""PR19A v9: v8 + prioridad física de nets de programación TPS259470A.

En U_EFUSE, ITIMER tiene el corredor más directo/confinado hacia su capacitor.
Se enruta antes que ILM/DVDT/UVLO/OVLO para que las nets menos confinadas se
adapten alrededor, sin cambiar netclasses, DRC o placement.
"""
from __future__ import annotations

import materialize_pr19a_local as impl
import materialize_pr19a_local_v8 as v8  # noqa: F401 - instala RouterPR19AV8

CONTROL_ORDER_V9 = [
    "5V_FB", "5V_VCC", "5V_PGOOD",
    "EFUSE_ITIMER", "EFUSE_ILM", "EFUSE_DVDT", "EFUSE_EN_UVLO", "EFUSE_OVLO",
    "CO2_ILIM", "PUMP_SR_CFG",
]
impl.CONTROL_RANK = {n: i for i, n in enumerate(CONTROL_ORDER_V9)}

if __name__ == "__main__":
    print("CONTROL_ORDER_V9", CONTROL_ORDER_V9)
    raise SystemExit(impl.main())
