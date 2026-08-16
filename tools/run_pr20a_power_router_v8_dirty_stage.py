#!/usr/bin/env python3
"""Diagnóstico read-only: ejecuta solo la etapa dirty/output del router v8."""
from __future__ import annotations
import run_pr20a_power_router_v8 as v8

v8.m.ORDER=['12V_IN_RAW','12V_PROTECTED','12V_ACT','PUMP_OUT1','PUMP_OUT2','CO2_SOL_POS']

if __name__=='__main__':
    v8.main()
