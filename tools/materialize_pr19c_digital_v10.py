#!/usr/bin/env python3
"""PR19C v10: v9 + árbol ACT_FAULT_N centrado en R_ACT_FAULT_PU."""
from __future__ import annotations
import json
import pcbnew  # type: ignore
import materialize_pr19c_digital as core
import materialize_pr19c_digital_v9 as v9

CANDIDATE_REVISION='v10-act-fault-star-topology-active'

def edge_len(eps,e):
    i,j=e; a,b=eps[i],eps[j]
    return abs(a['x_mm']-b['x_mm'])+abs(a['y_mm']-b['y_mm'])

class RouterV10(v9.RouterV9):
    def route_all(self)->dict:
        batch=self.batches['PR19C']
        if batch['nets']!=core.TARGET or int(batch['expected_net_count'])!=16: core.fail('contrato PR19C divergente')
        order=['UNO_IOREF_3V3','I2C_SDA','I2C_SCL','TEMP_1WIRE','ACT_FAULT_N','PUMP_PWM','PUMP_DIR','CO2_SOL_CTL','CHILLER_CTL','HX711_DOUT','HX711_SCK','MCU_NRST','MCU_WDI','HMI_RX','HMI_TX','LED_STATUS']
        for net in order:
            eps=self.pads_by_net.get(net,[]); eps.sort(key=lambda e:(e['x_mm'],e['y_mm'],e['ref'],e['pad']))
            if len(eps)<2: core.fail(f'{net}: endpoints insuficientes')
            bs=len(self.new_segments); bv=len(self.new_vias); bends=0; length=0.0
            if net=='UNO_IOREF_3V3':
                _,_,b,l=self._manual_uno_ioref_local(eps); bends+=b; length+=l
                j=next(e for e in eps if e['ref']=='J_UNOQ'); r=next(e for e in eps if e['ref']=='R_5V_EN_PD')
                path=self._astar(net,j,r); _,_,b,l=self._materialize(net,path,j,r); bends+=b; length+=l; edges_count=2
            elif net=='ACT_FAULT_N':
                by={e['ref']:e for e in eps}
                pairs=[('U_PUMP_DRV','U_CO2_DRV'),('R_ACT_FAULT_PU','TP_ACT_FAULT'),('R_ACT_FAULT_PU','U_PUMP_DRV'),('J_UNOQ','R_ACT_FAULT_PU')]
                for ra,rb in pairs:
                    a,z=by[ra],by[rb]; path=self._astar(net,a,z); _,_,b,l=self._materialize(net,path,a,z); bends+=b; length+=l
                edges_count=len(pairs)
            else:
                edges=core.mst_edges(eps); edges.sort(key=lambda e:(round(edge_len(eps,e),6),e[0],e[1]))
                for i,j in edges:
                    path=self._astar(net,eps[i],eps[j]); _,_,b,l=self._materialize(net,path,eps[i],eps[j]); bends+=b; length+=l
                edges_count=len(edges)
            stat={'net':net,'class':self.class_by_net[net],'endpoint_count':len(eps),'edge_count':edges_count,'segment_count':len(self.new_segments)-bs,'via_count':len(self.new_vias)-bv,'bend_count':bends,'grid_length_mm':round(length,3)}
            self.net_stats.append(stat); print('ROUTED',stat)
        return {'schema_version':1,'status':'PR19C_DIGITAL_ROUTING_CANDIDATE','candidate_revision':CANDIDATE_REVISION,'batch':'PR19C','target_nets':core.TARGET,'baseline':{'segments':core.PRIOR_SEGMENTS,'vias':core.PRIOR_VIAS},'net_stats':self.net_stats,'new_segments':self.new_segments,'new_vias':self.new_vias,'new_segment_count':len(self.new_segments),'new_via_count':len(self.new_vias),'policies':{'in1_signal_tracks':0,'zones_added':0,'future_batch_copper':0},'planner':{'grid_mm':core.STEP,'pad_halo_mm':core.PAD_HALO,'track_cell_halo':2,'via_cell_halo':3,'act_fault_tree':'J_UNOQ-RPU; RPU-TP; RPU-PUMP; PUMP-CO2'}}

def main()->int:
    board=pcbnew.LoadBoard(str(core.PCB)); placement=json.loads(core.PLACEMENT.read_text(encoding='utf-8')); routing=json.loads(core.ROUTING.read_text(encoding='utf-8')); batches=json.loads(core.BATCHES.read_text(encoding='utf-8'))
    r=RouterV10(board,placement,routing,batches); manifest=r.route_all(); core.OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); pcbnew.SaveBoard(str(core.PCB),board)
    print('PR19C_CANDIDATE_V10',len(manifest['target_nets']),manifest['new_segment_count'],manifest['new_via_count']); return 0
if __name__=='__main__': raise SystemExit(main())
