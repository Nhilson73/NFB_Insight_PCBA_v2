#!/usr/bin/env python3
"""Runner PR20A: portales eFuse + isla local de entrada TPSM33625."""
from __future__ import annotations
import materialize_pr20a_power_router as m
import run_pr20a_power_router_v3  # instala portales eFuse validados

# El backbone 12V_LOGIC termina en el bulk de entrada. El pin VIN del módulo y
# el bypass HF son stubs locales; no se fuerza una vía de 1 mm junto al pad fino.
m.BACKBONE['12V_LOGIC']=['NT_LOGIC.2','C_5V_IN_4U7.1']
m.TAP_WIDTH.setdefault('12V_LOGIC',{})['U_5V.3']=0.25
m.TAP_WIDTH.setdefault('12V_LOGIC',{})['C_5V_IN_100N.1']=0.50

if __name__=='__main__': m.main()
