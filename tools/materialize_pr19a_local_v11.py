#!/usr/bin/env python3
"""PR19A v11: v10 + orden topológico completo de la isla TPS259470A.

Después de colapsar pads compuestos, el bloqueo EN/UVLO persistía porque ILM y
DVDT, al salir del lado derecho hacia pasivos ubicados a la izquierda/superior,
ocupaban antes el corredor del divisor UV/OV. Se conserva ITIMER primero por su
garganta confinada y después se cierra el lado izquierdo del eFuse antes de las
ramas cruzadas.
"""
from __future__ import annotations

import materialize_pr19a_local as impl
import materialize_pr19a_local_v10 as v10  # noqa: F401 - instala endpoints lógicos

CONTROL_ORDER_V11 = [
    "5V_FB", "5V_VCC", "5V_PGOOD",
    "EFUSE_ITIMER",
    "EFUSE_EN_UVLO", "EFUSE_OVLO",
    "EFUSE_ILM", "EFUSE_DVDT",
    "CO2_ILIM", "PUMP_SR_CFG",
]
impl.CONTROL_RANK = {n: i for i, n in enumerate(CONTROL_ORDER_V11)}

if __name__ == "__main__":
    print("CONTROL_ORDER_V11", CONTROL_ORDER_V11)
    raise SystemExit(impl.main())
