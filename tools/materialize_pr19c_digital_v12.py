#!/usr/bin/env python3
"""PR19C v12: correcciones localizadas derivadas del DRC v11.

- entrada limpia a U_5V.2 para UNO_IOREF_3V3;
- I2C_SCL pasa por encima de SDA en F.Cu, sin cruce;
- ACT_FAULT_N: corredor UNO→RPU, RPU→PUMP y PUMP→CO2 rediseñados;
- deduplicación de vías exactas de una misma net.
No se relaja ninguna regla KiCad ni contrato.
"""
from __future__ import annotations
import json
import math
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v5 as v5
import materialize_pr19c_digital_v7 as v7
import materialize_pr19c_digital_v11 as v11

CANDIDATE_REVISION='v12-drc-local-fixes-via-dedup'

class RouterV12(v11.RouterV11):
    def _add_via(self,net,clsinfo,ix,iy):
        x,y=core.xy(ix,iy)
        for v in self.new_vias:
            if v['net']==net and abs(v['x_mm']-x)<1e-9 and abs(v['y_mm']-y)<1e-9:
                self._mark_via(net,x,y,halo=1)
                return
        return super()._add_via(net,clsinfo,ix,iy)

    def _manual_uno_ioref_local(self,eps):
        by={e['ref']:e for e in eps}; r=by['R_5V_EN_PD']; u=by['U_5V']
        before_s,before_v=len(self.new_segments),len(self.new_vias)
        clsinfo=self.class_info[self.class_by_net['UNO_IOREF_3V3']]
        length=0.0
        def seg(layer,a,b):
            nonlocal length
            self._manual_segment('UNO_IOREF_3V3',layer,a,b); length+=math.hypot(b[0]-a[0],b[1]-a[1])
        v1=(190.0,28.0); v2=(190.5,17.5)
        seg(pcbnew.F_Cu,(r['x_mm'],r['y_mm']),v1); self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(*v1) if False else core.gcoord(v1[0]),core.gcoord(v1[1]))
        seg(pcbnew.B_Cu,v1,(190.5,28.0)); seg(pcbnew.B_Cu,(190.5,28.0),v2)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v2[0]),core.gcoord(v2[1]))
        seg(pcbnew.F_Cu,v2,(190.5,17.925)); seg(pcbnew.F_Cu,(190.5,17.925),(u['x_mm'],u['y_mm']))
        return len(self.new_segments)-before_s,len(self.new_vias)-before_v,3,length

    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='I2C_SCL' and refs=={'D_GNSS_SCL','R_I2C_SCL'}:
            d=a if a['ref']=='D_GNSS_SCL' else z; r=z if z['ref']=='R_I2C_SCL' else a
            pts=[(d['x_mm'],d['y_mm']),(134.25,17.25),(134.25,18.50),(141.00,18.50),(141.00,17.00),(r['x_mm'],r['y_mm'])]
            p=v5.grid_path(pts,pcbnew.F_Cu); return p if a['ref']=='D_GNSS_SCL' else list(reversed(p))
        if net=='ACT_FAULT_N' and refs=={'J_UNOQ','R_ACT_FAULT_PU'}:
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),(8.00,36.50,pcbnew.B_Cu),(8.00,9.50,pcbnew.B_Cu),(90.50,9.50,pcbnew.B_Cu),
                (90.50,9.50,pcbnew.F_Cu),(92.25,9.50,pcbnew.F_Cu),(92.25,18.75,pcbnew.F_Cu),(94.00,18.75,pcbnew.F_Cu),
                (94.00,18.75,pcbnew.B_Cu),(94.00,9.50,pcbnew.B_Cu),(104.50,9.50,pcbnew.B_Cu),
                (104.50,9.50,pcbnew.F_Cu),(112.50,9.50,pcbnew.F_Cu),(112.50,9.50,pcbnew.B_Cu),
                (202.50,9.50,pcbnew.B_Cu),(202.50,50.00,pcbnew.B_Cu),(202.50,50.00,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return list(reversed(p)) if a['ref']=='R_ACT_FAULT_PU' else p
        if net=='ACT_FAULT_N' and refs=={'R_ACT_FAULT_PU','U_PUMP_DRV'}:
            nodes=[
                (200.75,50.00,pcbnew.F_Cu),(211.00,50.00,pcbnew.F_Cu),(211.00,50.00,pcbnew.B_Cu),(211.00,28.00,pcbnew.B_Cu),
                (211.00,28.00,pcbnew.F_Cu),(211.00,25.00,pcbnew.F_Cu),(211.00,25.00,pcbnew.B_Cu),(211.00,17.75,pcbnew.B_Cu),
                (211.00,17.75,pcbnew.F_Cu),(212.25,17.75,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return p if a['ref']=='R_ACT_FAULT_PU' else list(reversed(p))
        if net=='ACT_FAULT_N' and refs=={'U_CO2_DRV','U_PUMP_DRV'}:
            nodes=[
                (212.25,17.75,pcbnew.F_Cu),(211.00,17.75,pcbnew.F_Cu),(211.00,17.75,pcbnew.B_Cu),(211.00,22.50,pcbnew.B_Cu),
                (214.50,22.50,pcbnew.B_Cu),(214.50,22.50,pcbnew.F_Cu),(216.50,22.50,pcbnew.F_Cu),(216.50,22.50,pcbnew.B_Cu),
                (219.00,22.50,pcbnew.B_Cu),(219.00,18.50,pcbnew.B_Cu),(219.00,18.50,pcbnew.F_Cu),(217.75,18.50,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return p if a['ref']=='U_PUMP_DRV' else list(reversed(p))
        return super()._astar(net,a,z)

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r.setdefault('planner',{}).update({
            'via_dedup':'SAME_NET_EXACT_XY',
            'uno_ioref_entry':'via x190.5/y17.5; F horizontal into U_5V.2',
            'i2c_scl_local':'F y18.5 above SDA',
            'act_fault_long':'B lane with I2C F detour; direct B through HMI; RPU approached from +X',
            'act_fault_rpu_pump':'shared F y50 -> B x211 with F bypass y28-25 -> B -> pad18',
            'act_fault_pump_co2':'shared via x211 -> B/F bypass PUMP_CURRENT_ADC -> B x219 -> F CO2 pad1',
        })
        return r

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV12(board,placement,routing,batches); manifest=r.route_all(); core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V12',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
