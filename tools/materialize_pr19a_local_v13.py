#!/usr/bin/env python3
"""PR19A v13: v12 + DVDT antes de la micro-ruta superior ILM.

v12 confirmó que la micro-ruta ILM es viable, pero al materializarse primero
ocupaba espacio que el planner necesitaba para DVDT. DVDT se dirige desde U_EFUSE.7
hacia C_EFUSE_DVDT a la izquierda; se cierra antes y luego ILM conserva su
corredor superior fijo. No cambia ninguna regla eléctrica/DRC.
"""
from __future__ import annotations

import materialize_pr19a_local as impl
import materialize_pr19a_local_v12 as v12  # noqa: F401 - instala micro-ruta ILM

CONTROL_ORDER_V13 = [
    "5V_FB", "5V_VCC", "5V_PGOOD",
    "EFUSE_ITIMER",
    "EFUSE_EN_UVLO", "EFUSE_OVLO",
    "EFUSE_DVDT", "EFUSE_ILM",
    "CO2_ILIM", "PUMP_SR_CFG",
]
impl.CONTROL_RANK = {n: i for i, n in enumerate(CONTROL_ORDER_V13)}

if __name__ == "__main__":
    print("CONTROL_ORDER_V13", CONTROL_ORDER_V13)
    raise SystemExit(impl.main())
