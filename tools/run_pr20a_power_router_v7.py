#!/usr/bin/env python3
"""Runner PR20A: reserva primero el corredor dirty Z3/Z4."""
from __future__ import annotations
import materialize_pr20a_power_router as m
import run_pr20a_power_router_v6  # instala todas las islas locales previas

m.ORDER=['12V_IN_RAW','12V_PROTECTED','12V_ACT','PUMP_OUT1','PUMP_OUT2','CO2_SOL_POS','12V_LOGIC','12V_HOST_VIN','5V_RAIL','3V3_RAIL']

if __name__=='__main__': m.main()
