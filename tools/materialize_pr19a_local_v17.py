#!/usr/bin/env python3
"""PR19A v17: cierre determinista de sub-islas con errores DRC.

Sobre v16 reemplaza únicamente aristas locales que el A* o las micro-rutas
previas hacían cruzar. Objetivos: eliminar categorías completas de DRC y
simplificar geometría sin cambiar placement, netlist, netclass o clearances.
KiCad DRC sigue siendo la autoridad física final.
"""
from __future__ import annotations

import pcbnew  # type: ignore
import materialize_pr19a_local as impl
import materialize_pr19a_local_v16 as v16
import pr19a_router_core as base


def key(ep: dict) -> tuple[str, str]:
    return str(ep.get("ref")), str(ep.get("pad"))


def pair(a: dict, b: dict, x: tuple[str, str], y: tuple[str, str]) -> bool:
    return {key(a), key(b)} == {x, y}


class RouterPR19AV17(v16.RouterPR19AV16):
    def _special(self, net: str, a: dict, b: dict) -> str | None:
        if net == "5V_FB":
            if pair(a,b,("U_5V","9"),("R_5V_FBB","1")): return "FB_U_FBB"
            if pair(a,b,("R_5V_FBB","1"),("R_5V_FBT","2")): return "FB_DIV"
        if net == "EFUSE_OVLO":
            if pair(a,b,("R_UVOV_R2","2"),("R_UVOV_R3","1")): return "OVLO_DIV"
            if pair(a,b,("U_EFUSE","2"),("R_UVOV_R3","1")): return "OVLO_U"
        if net == "EFUSE_ILM" and pair(a,b,("U_EFUSE","9"),("R_EFUSE_ILIM","1")): return "ILM"
        if net == "EFUSE_DVDT" and pair(a,b,("U_EFUSE","7"),("C_EFUSE_DVDT","1")): return "DVDT"
        if net == "LOAD_A_POS":
            if pair(a,b,("J_LOADCELL","3"),("U_HX","8")): return "LOAD_POS_MAIN"
            if pair(a,b,("U_HX","8"),("TP_LOAD_A_POS","1")): return "LOAD_POS_TP"
        if net == "LOAD_A_NEG":
            if pair(a,b,("J_LOADCELL","4"),("U_HX","7")): return "LOAD_NEG_MAIN"
            if pair(a,b,("U_HX","7"),("TP_LOAD_A_NEG","1")): return "LOAD_NEG_TP"
        if net == "PUMP_SR_CFG" and pair(a,b,("U_PUMP_DRV","1"),("R_PUMP_SR","1")): return "PUMP_SR"
        if net == "PUMP_DIR_DRV" and pair(a,b,("U_PUMP_DRV","3"),("R_PUMP_DIR_SER","2")): return "PUMP_DIR"
        if net == "PUMP_PWM_DRV" and pair(a,b,("U_PUMP_DRV","4"),("R_PUMP_PWM_PD","1")): return "PUMP_PWM"
        if net == "CO2_ILIM" and pair(a,b,("U_CO2_DRV","2"),("R_CO2_ILIM","1")): return "CO2_ILIM"
        if net == "CO2_EN_DRV":
            if pair(a,b,("U_CO2_DRV","4"),("R_CO2_EN_PD","1")): return "CO2_EN_PD"
            if pair(a,b,("U_CO2_DRV","4"),("R_CO2_EN_SER","2")): return "CO2_EN_SER"
        if net == "CO2_OPENLOAD_N":
            if pair(a,b,("U_CO2_DRV","5"),("R_CO2_OPENLOAD_PU","2")): return "CO2_OL_LOCAL"
            if pair(a,b,("R_CO2_OPENLOAD_PU","2"),("TP_CO2_OPENLOAD","1")): return "CO2_OL_TP"
        if net == "HMI_FIELD_TX":
            if pair(a,b,("U_HMI_LVL","1"),("D_HMI_TX","1")): return "HMI_TX_LOCAL"
            if pair(a,b,("U_HMI_LVL","1"),("J_HMI","4")): return "HMI_TX_FIELD"
        if net == "CHILLER_LED_A" and pair(a,b,("U_CHILLER","1"),("R_CH_LED","2")): return "CH_LED_A"
        return None

    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        if self._special(net,start_ep,goal_ep):
            return [(0,0,pcbnew.F_Cu)]
        return super()._astar(net,cls,start_ep,goal_ep,xmin,xmax)

    def _f(self, net: str, width: float, pts: list[tuple[float,float]]) -> None:
        for a,b in zip(pts,pts[1:]):
            self._track(net,pcbnew.F_Cu,width,a,b)

    def _b(self, net: str, width: float, pts: list[tuple[float,float]]) -> None:
        for a,b in zip(pts,pts[1:]):
            self._track(net,pcbnew.B_Cu,width,a,b)

    def _via(self, net: str, clsinfo: dict, p: tuple[float,float]) -> None:
        self._add_via(net,clsinfo,base.gcoord(p[0]),base.gcoord(p[1]))

    def _ends(self, a: dict, b: dict, wanted: tuple[str,str]) -> tuple[dict,dict]:
        return (a,b) if key(a)==wanted else (b,a)

    def _materialize_path(self, net, cls, clsinfo, path, start_ep, goal_ep):
        s=self._special(net,start_ep,goal_ep)
        if not s:
            return super()._materialize_path(net,cls,clsinfo,path,start_ep,goal_ep)
        w=float(clsinfo["track_width_mm_min"])

        if s=="FB_U_FBB":
            u,r=self._ends(start_ep,goal_ep,("U_5V","9"))
            self._f(net,w,[(u["x_mm"],u["y_mm"]),(193.575,16.50),(193.00,16.50),(r["x_mm"],r["y_mm"])])
        elif s=="FB_DIV":
            a,b=self._ends(start_ep,goal_ep,("R_5V_FBB","1"))
            self._f(net,w,[(a["x_mm"],a["y_mm"]),(b["x_mm"],b["y_mm"])])
        elif s=="OVLO_DIV":
            a,b=self._ends(start_ep,goal_ep,("R_UVOV_R2","2")); self._f(net,w,[(a["x_mm"],a["y_mm"]),(b["x_mm"],b["y_mm"])])
        elif s=="OVLO_U":
            u,r=self._ends(start_ep,goal_ep,("U_EFUSE","2"))
            self._f(net,w,[(u["x_mm"],u["y_mm"]),(174.50,18.20),(174.50,21.60),(r["x_mm"],21.60),(r["x_mm"],r["y_mm"])])
        elif s=="ILM":
            u,r=self._ends(start_ep,goal_ep,("U_EFUSE","9"))
            self._f(net,w,[(u["x_mm"],u["y_mm"]),(182.00,18.20),(182.00,24.20),(r["x_mm"],24.20),(r["x_mm"],r["y_mm"])])
        elif s=="DVDT":
            u,c=self._ends(start_ep,goal_ep,("U_EFUSE","7"))
            self._f(net,w,[(u["x_mm"],u["y_mm"]),(181.20,u["y_mm"]),(181.20,23.40),(c["x_mm"],23.40),(c["x_mm"],c["y_mm"])])
        elif s=="LOAD_POS_MAIN":
            j,u=self._ends(start_ep,goal_ep,("J_LOADCELL","3")); v=(110.00,26.50)
            self._b(net,w,[(j["x_mm"],j["y_mm"]),(121.50,7.80),(110.00,7.80),v]); self._via(net,clsinfo,v); self._f(net,w,[v,(u["x_mm"],u["y_mm"])])
        elif s=="LOAD_POS_TP":
            u,tp=self._ends(start_ep,goal_ep,("U_HX","8")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(110.25,u["y_mm"]),(tp["x_mm"],tp["y_mm"])])
        elif s=="LOAD_NEG_MAIN":
            j,u=self._ends(start_ep,goal_ep,("J_LOADCELL","4")); v=(109.25,25.25)
            self._b(net,w,[(j["x_mm"],j["y_mm"]),(123.00,7.00),(109.25,7.00),v]); self._via(net,clsinfo,v); self._f(net,w,[v,(u["x_mm"],u["y_mm"])])
        elif s=="LOAD_NEG_TP":
            u,tp=self._ends(start_ep,goal_ep,("U_HX","7")); v0=(109.25,25.25); v1=(113.25,28.25)
            self._f(net,w,[(u["x_mm"],u["y_mm"]),v0]); self._b(net,w,[v0,(109.00,25.25),(109.00,27.75),(113.25,27.75),v1]); self._via(net,clsinfo,v1); self._f(net,w,[v1,(tp["x_mm"],tp["y_mm"])])
        elif s=="PUMP_SR":
            u,r=self._ends(start_ep,goal_ep,("U_PUMP_DRV","1")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(u["x_mm"],15.75),(r["x_mm"],15.75),(r["x_mm"],r["y_mm"])])
        elif s=="PUMP_DIR":
            u,r=self._ends(start_ep,goal_ep,("U_PUMP_DRV","3")); v1=(207.75,17.25); v2=(207.75,21.75)
            self._f(net,w,[(u["x_mm"],u["y_mm"]),v1]); self._via(net,clsinfo,v1); self._b(net,w,[v1,v2]); self._via(net,clsinfo,v2); self._f(net,w,[v2,(r["x_mm"],r["y_mm"])])
        elif s=="PUMP_PWM":
            u,r=self._ends(start_ep,goal_ep,("U_PUMP_DRV","4")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(206.75,u["y_mm"]),(206.75,21.50),(r["x_mm"],21.50),(r["x_mm"],r["y_mm"])])
        elif s=="CO2_ILIM":
            u,r=self._ends(start_ep,goal_ep,("U_CO2_DRV","2")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(216.75,19.00),(221.25,19.00),(221.25,r["y_mm"]),(r["x_mm"],r["y_mm"])])
        elif s=="CO2_EN_PD":
            u,r=self._ends(start_ep,goal_ep,("U_CO2_DRV","4")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(216.50,u["y_mm"]),(216.50,15.25),(r["x_mm"],15.25),(r["x_mm"],r["y_mm"])])
        elif s=="CO2_EN_SER":
            u,r=self._ends(start_ep,goal_ep,("U_CO2_DRV","4")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(217.67,15.25),(r["x_mm"],15.25),(r["x_mm"],r["y_mm"])])
        elif s=="CO2_OL_LOCAL":
            u,r=self._ends(start_ep,goal_ep,("U_CO2_DRV","5")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(219.50,u["y_mm"]),(219.50,19.50),(r["x_mm"],19.50),(r["x_mm"],r["y_mm"])])
        elif s=="CO2_OL_TP":
            r,tp=self._ends(start_ep,goal_ep,("R_CO2_OPENLOAD_PU","2")); v1=(215.75,21.25); v2=(210.00,56.50)
            self._f(net,w,[(r["x_mm"],r["y_mm"]),v1]); self._via(net,clsinfo,v1); self._b(net,w,[v1,(215.75,56.50),v2]); self._via(net,clsinfo,v2); self._f(net,w,[v2,(tp["x_mm"],tp["y_mm"])])
        elif s=="HMI_TX_LOCAL":
            u,d=self._ends(start_ep,goal_ep,("U_HMI_LVL","1")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(d["x_mm"],d["y_mm"])])
        elif s=="HMI_TX_FIELD":
            u,j=self._ends(start_ep,goal_ep,("U_HMI_LVL","1")); v=(153.25,15.75)
            self._b(net,w,[(j["x_mm"],j["y_mm"]),(159.00,14.50),(153.25,14.50),v]); self._via(net,clsinfo,v); self._f(net,w,[v,(u["x_mm"],u["y_mm"])])
        elif s=="CH_LED_A":
            u,r=self._ends(start_ep,goal_ep,("U_CHILLER","1")); self._f(net,w,[(u["x_mm"],u["y_mm"]),(230.00,u["y_mm"]),(230.00,22.50),(r["x_mm"],22.50),(r["x_mm"],r["y_mm"])])
        else:
            raise RuntimeError(s)


impl.RouterPR19A=RouterPR19AV17

if __name__=="__main__":
    raise SystemExit(impl.main())
