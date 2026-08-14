#!/usr/bin/env python3
"""PR19C v18: cierre localizado de DRC/warnings sobre topología low-via v17.

- UNO_IOREF_3V3: desplaza la vía local a y=17.70 para liberar 5V_PGOOD.
- ACT_FAULT_N: bypass doble del par load-cell con 4 transiciones, compensado
  por simplificación RPU→PUMP y deduplicación de vía compartida x202.5/y50.
- I2C_SDA: separa la vía (92.75,15.5) a (93.25,15.5), conservando sus dos tramos.
- CO2_ILIM: conserva ECO v17 4→4, 0 vías.

No modifica placement, outline, netclasses, reglas DRC ni lotes PR20.
"""
from __future__ import annotations
import json
import math
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v7 as v7
import materialize_pr19c_digital_v17 as v17

CANDIDATE_REVISION='v18-local-drc-and-via-spacing-closure'

class RouterV18(v17.RouterV17):
    def _add_via(self,net,clsinfo,ix,iy):
        # Un mismo nodo eléctrico no necesita dos vías coincidentes creadas por
        # aristas MST diferentes. Reutilizarla reduce cobre redundante sin
        # cambiar conectividad ni reglas físicas.
        x,y=core.xy(ix,iy)
        for item in self.board.GetTracks():
            if not isinstance(item,pcbnew.PCB_VIA) or item.GetNetname()!=net: continue
            p=item.GetPosition()
            if abs(core.mm(p.x)-x)<1e-6 and abs(core.mm(p.y)-y)<1e-6:
                self._mark_via(net,x,y,halo=1)
                return
        return super()._add_via(net,clsinfo,ix,iy)

    def _manual_uno_ioref_local(self,eps):
        by={e['ref']:e for e in eps}; r=by['R_5V_EN_PD']; u=by['U_5V']
        before_s,before_v=len(self.new_segments),len(self.new_vias)
        clsinfo=self.class_info[self.class_by_net['UNO_IOREF_3V3']]; length=0.0
        def seg(layer,a,b):
            nonlocal length
            self._manual_segment('UNO_IOREF_3V3',layer,a,b); length+=math.hypot(b[0]-a[0],b[1]-a[1])
        v1=(190.0,28.0); v2=(190.25,17.70)
        seg(pcbnew.F_Cu,(r['x_mm'],r['y_mm']),v1)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v1[0]),core.gcoord(v1[1]))
        seg(pcbnew.B_Cu,v1,(190.25,28.0)); seg(pcbnew.B_Cu,(190.25,28.0),v2)
        self._add_via('UNO_IOREF_3V3',clsinfo,core.gcoord(v2[0]),core.gcoord(v2[1]))
        seg(pcbnew.F_Cu,v2,(u['x_mm'],u['y_mm']))
        return len(self.new_segments)-before_s,len(self.new_vias)-before_v,2,length

    def _astar(self,net,a,z):
        refs={a['ref'],z['ref']}
        if net=='ACT_FAULT_N' and refs=={'J_UNOQ','R_ACT_FAULT_PU'}:
            # B superior sobre I2C; dos micro-bypass F separados para cruzar
            # LOAD_A_POS y LOAD_A_NEG, retornando a B antes del corredor Z2.
            nodes=[
                (2.50,36.50,pcbnew.B_Cu),(8.00,36.50,pcbnew.B_Cu),(8.00,9.50,pcbnew.B_Cu),
                (90.00,9.50,pcbnew.B_Cu),(90.00,19.50,pcbnew.B_Cu),(106.75,19.50,pcbnew.B_Cu),
                (106.75,19.50,pcbnew.F_Cu),(108.50,19.50,pcbnew.F_Cu),(108.50,19.50,pcbnew.B_Cu),
                (108.50,9.50,pcbnew.B_Cu),(108.50,9.50,pcbnew.F_Cu),(110.00,9.50,pcbnew.F_Cu),
                (110.00,9.50,pcbnew.B_Cu),(150.00,9.50,pcbnew.B_Cu),
                (150.00,20.00,pcbnew.B_Cu),(164.00,20.00,pcbnew.B_Cu),(164.00,9.50,pcbnew.B_Cu),
                (197.00,9.50,pcbnew.B_Cu),(197.00,52.00,pcbnew.B_Cu),(202.50,52.00,pcbnew.B_Cu),(202.50,50.00,pcbnew.B_Cu),
                (202.50,50.00,pcbnew.F_Cu),(200.75,50.00,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return list(reversed(p)) if a['ref']=='R_ACT_FAULT_PU' else p

        if net=='ACT_FAULT_N' and refs=={'R_ACT_FAULT_PU','U_PUMP_DRV'}:
            # Reutiliza la vía x202.5/y50 creada por la arista J_UNOQ↔RPU.
            # B baja a la izquierda de PUMP_CURRENT_ADC y cruza por y=25.
            nodes=[
                (200.75,50.00,pcbnew.F_Cu),(202.50,50.00,pcbnew.F_Cu),(202.50,50.00,pcbnew.B_Cu),
                (202.00,50.00,pcbnew.B_Cu),(202.00,25.00,pcbnew.B_Cu),(212.50,25.00,pcbnew.B_Cu),
                (212.50,16.00,pcbnew.B_Cu),(212.50,16.00,pcbnew.F_Cu),(213.00,16.00,pcbnew.F_Cu),
                (213.00,17.75,pcbnew.F_Cu),(212.25,17.75,pcbnew.F_Cu),
            ]
            p=v7.mixed_grid_path(nodes); return p if a['ref']=='R_ACT_FAULT_PU' else list(reversed(p))
        return super()._astar(net,a,z)

    def route_all(self):
        r=super().route_all(); r['candidate_revision']=CANDIDATE_REVISION
        r.setdefault('planner',{}).update({
            'uno_ioref_local':'B→F @190.25,17.70; diagonal a U_5V.2',
            'act_fault_loadcell_bypass':'dos bypass F: x106.75→108.5 @y19.5 y x108.5→110 @y9.5',
            'act_fault_rpu_pump':'vía compartida x202.5/y50; B x202→y25→x212.5; una vía nueva x212.5/y16',
            'via_dedup':'misma net + misma coordenada reutiliza vía existente',
        })
        return r

def _pt(v): return (round(core.mm(v.x),4),round(core.mm(v.y),4))

def eco_i2c_sda_spacing(board,manifest):
    old=(92.75,15.50); new=(93.25,15.50); moved_vias=0; moved_ends=0
    for item in board.GetTracks():
        if item.GetNetname()!='I2C_SDA': continue
        if isinstance(item,pcbnew.PCB_VIA):
            if _pt(item.GetPosition())==old:
                item.SetPosition(pcbnew.VECTOR2I(core.iu(new[0]),core.iu(new[1]))); moved_vias+=1
            continue
        a=_pt(item.GetStart()); b=_pt(item.GetEnd())
        if a==old:
            item.SetStart(pcbnew.VECTOR2I(core.iu(new[0]),core.iu(new[1]))); moved_ends+=1
        if b==old:
            item.SetEnd(pcbnew.VECTOR2I(core.iu(new[0]),core.iu(new[1]))); moved_ends+=1
    if moved_vias!=1 or moved_ends!=2: core.fail(f'ECO I2C_SDA inesperado: vias={moved_vias} endpoints={moved_ends}')
    mv=0; ms=0
    for v in manifest['new_vias']:
        if v['net']=='I2C_SDA' and (float(v['x_mm']),float(v['y_mm']))==old:
            v['x_mm'],v['y_mm']=new; mv+=1
    for s in manifest['new_segments']:
        if s['net']!='I2C_SDA': continue
        if tuple(float(x) for x in s['start_mm'])==old: s['start_mm']=list(new); ms+=1
        if tuple(float(x) for x in s['end_mm'])==old: s['end_mm']=list(new); ms+=1
    if mv!=1 or ms!=2: core.fail(f'manifest ECO I2C_SDA inesperado: vias={mv} endpoints={ms}')
    manifest.setdefault('post_route_ecos',[]).append({
        'net':'I2C_SDA','reason':'cumplir hole-to-hole mínimo sin cambiar topología',
        'via_before_mm':list(old),'via_after_mm':list(new),'segments_reanchored':2,
        'connectivity_changed':False,'via_count_changed':False,
    })
    print('ECO_I2C_SDA_SPACING_OK',old,'->',new)

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); v17.eco_co2_ilim(board)
    placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV18(board,placement,routing,batches); manifest=r.route_all(); eco_i2c_sda_spacing(board,manifest)
    core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V18',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
