#!/usr/bin/env python3
"""Runner PR20A con portales eFuse congelados por micro-DRC."""
from __future__ import annotations
import pcbnew
import materialize_pr20a_power_router as m
import run_pr20a_power_router_v2 as v2

fallback=v2.prepare_escape

def fixed_efuse(self,n,e,w,role):
    key=f"{e['ref']}.{e['pad']}"
    if key=='U_EFUSE.5' and n=='12V_IN_RAW':
        self.add_seg(n,pcbnew.F_Cu,(177.525,17.975),(177.525,14.0),0.25,'smd_escape')
        self.add_seg(n,pcbnew.F_Cu,(177.525,14.0),(175.5,12.0),0.25,'smd_escape')
        self.add_via(n,m.gc(175.5),m.gc(12.0),'smd_escape')
        return {'net':n,'ref':'U_EFUSE_PORTAL_RAW','pad':'5','obj':None,'x':175.5,'y':12.0,'sx':w,'sy':w,'virtual':True,'layer':pcbnew.In2_Cu,'source':key,'escape_width':0.25}
    if key=='U_EFUSE.6' and n=='12V_PROTECTED':
        self.add_seg(n,pcbnew.F_Cu,(178.025,17.975),(178.025,14.0),0.25,'smd_escape')
        self.add_seg(n,pcbnew.F_Cu,(178.025,14.0),(181.0,12.0),0.25,'smd_escape')
        self.add_via(n,m.gc(181.0),m.gc(12.0),'smd_escape')
        return {'net':n,'ref':'U_EFUSE_PORTAL_PROT','pad':'6','obj':None,'x':181.0,'y':12.0,'sx':w,'sy':w,'virtual':True,'layer':pcbnew.In2_Cu,'source':key,'escape_width':0.25}
    return fallback(self,n,e,w,role)

m.Router.prepare_escape=fixed_efuse

if __name__=='__main__': m.main()
