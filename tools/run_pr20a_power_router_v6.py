#!/usr/bin/env python3
"""Runner PR20A: backbones terminan en desacoplos; QFN usa fan-out local."""
from __future__ import annotations
import pcbnew
import materialize_pr20a_power_router as m
import run_pr20a_power_router_v5  # eFuse + isla TPSM33625

# 12V_ACT se distribuye entre fusible y capacitores de potencia. Los pines VM
# de los drivers se unen como stubs locales, no como extremos de troncal.
m.BACKBONE['12V_ACT']=['F_ACT.2','C_PUMP_BULK.1','C_CO2_DRV.1']
for k,w in {
    'TP_12V_ACT.1':0.50,'C_PUMP_VM.1':0.50,
    'U_PUMP_DRV.6':0.20,'U_PUMP_DRV.15':0.20,'U_CO2_DRV.8':0.20,
}.items(): m.TAP_WIDTH.setdefault('12V_ACT',{})[k]=w

fallback=m.Router.prepare_escape

def driver_fanout(self,n,e,w,role):
    key=f"{e['ref']}.{e['pad']}"
    fixed={
      ('12V_ACT','U_PUMP_DRV.6'): ((209.025,19.325),(208.35,19.325),(207.50,18.60),0.20),
      ('12V_ACT','U_PUMP_DRV.15'):((212.325,19.325),(213.00,19.325),(213.85,18.85),0.20),
      ('12V_ACT','U_CO2_DRV.8'):  ((218.82,18.375),(219.35,18.375),(220.10,19.10),0.20),
    }
    cfg=fixed.get((n,key))
    if cfg:
        a,b,c,ew=cfg
        self.add_seg(n,pcbnew.F_Cu,a,b,ew,'smd_escape')
        self.add_seg(n,pcbnew.F_Cu,b,c,ew,'smd_escape')
        return {'net':n,'ref':key.replace('.','_')+'_PORTAL','pad':e['pad'],'obj':None,'x':c[0],'y':c[1],'sx':ew,'sy':ew,'virtual':True,'layer':pcbnew.F_Cu,'source':key,'escape_width':ew}
    return fallback(self,n,e,w,role)

m.Router.prepare_escape=driver_fanout

if __name__=='__main__': m.main()
