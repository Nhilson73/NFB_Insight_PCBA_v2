#!/usr/bin/env python3
"""Runner PR20A: eFuse probado + fanout local VIN TPSM33625."""
from __future__ import annotations
import pcbnew
import materialize_pr20a_power_router as m
import run_pr20a_power_router_v4  # instala eFuse y política de isla 12V_LOGIC

fallback=m.Router.prepare_escape

def local_power_fanout(self,n,e,w,role):
    key=f"{e['ref']}.{e['pad']}"
    if n=='12V_LOGIC' and key=='U_5V.3':
        # Salida normal al borde izquierdo del módulo. El stub es de baja
        # longitud; el backbone de 1 mm termina en C_5V_IN_4U7.
        self.add_seg(n,pcbnew.F_Cu,(191.675,18.425),(190.75,18.425),0.25,'smd_escape')
        return {'net':n,'ref':'U_5V_VIN_PORTAL','pad':'3','obj':None,'x':190.75,'y':18.425,'sx':0.25,'sy':0.25,'virtual':True,'layer':pcbnew.F_Cu,'source':key,'escape_width':0.25}
    return fallback(self,n,e,w,role)

m.Router.prepare_escape=local_power_fanout

if __name__=='__main__': m.main()
