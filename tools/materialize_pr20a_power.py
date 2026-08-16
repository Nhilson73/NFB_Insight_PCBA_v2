#!/usr/bin/env python3
"""Materializa candidato PR20A sobre PR19D sin tocar placement, outline, zones ni GND.

Arquitectura de capas:
- In2.Cu: troncales de distribución 5V/3V3/12V protegida/host/logic y salidas Z4.
- F.Cu: entrada local, ramas locales y 12V_ACT dirty en Z3/Z4.
- In1.Cu: reservado; no se usa.
Los neck-downs existen solo como escapes cortos de pads SMD más estrechos que
el ancho de distribución; no reducen el clearance ni la sección de las troncales.
"""
from __future__ import annotations
import json
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
OUT=ROOT/'hardware'/'pr20a_power_routing_manifest.json'
TARGET=["12V_IN_RAW","12V_PROTECTED","12V_HOST_VIN","12V_LOGIC","12V_ACT","5V_RAIL","3V3_RAIL","PUMP_OUT1","PUMP_OUT2","CO2_SOL_POS"]
BASE_SEG=924; BASE_VIA=121

def iu(x): return pcbnew.FromMM(float(x))
def V(x,y): return pcbnew.VECTOR2I(iu(x),iu(y))
def fail(m): raise SystemExit('ERROR: '+m)

def netmap(board):
    out={}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() and p.GetNetname() not in out:
                out[p.GetNetname()]=p.GetNet()
    return out

def main():
    b=pcbnew.LoadBoard(str(PCB)); nets=netmap(b)
    seg0=sum(not isinstance(t,pcbnew.PCB_VIA) for t in b.GetTracks()); via0=sum(isinstance(t,pcbnew.PCB_VIA) for t in b.GetTracks())
    if (seg0,via0)!=(BASE_SEG,BASE_VIA): fail(f'baseline PR19D inesperado {(seg0,via0)}')
    if len(b.Zones())!=0: fail('PR20A requiere zones=0 antes de PR20B')
    touched={t.GetNetname() for t in b.GetTracks()}
    early=sorted(set(TARGET)&touched)
    if early: fail(f'PR20A debe iniciar sin cobre propio: {early}')
    if 'GND' in touched: fail('GND fue adelantado antes de PR20B')
    missing=[n for n in TARGET if n not in nets]
    if missing: fail(f'nets PR20A ausentes del PCB: {missing}')

    new_segments=[]; new_vias=[]
    def S(net,layer,a,z,w,role='distribution'):
        t=pcbnew.PCB_TRACK(b); t.SetNet(nets[net]); t.SetLayer(layer); t.SetWidth(iu(w)); t.SetStart(V(*a)); t.SetEnd(V(*z)); b.Add(t)
        new_segments.append({'net':net,'layer':b.GetLayerName(layer),'start_mm':[float(a[0]),float(a[1])],'end_mm':[float(z[0]),float(z[1])],'width_mm':float(w),'role':role})
    def VIA(net,p,d,drill,role='distribution'):
        v=pcbnew.PCB_VIA(b); v.SetNet(nets[net]); v.SetPosition(V(*p)); v.SetWidth(iu(d)); v.SetDrill(iu(drill)); b.Add(v)
        new_vias.append({'net':net,'at_mm':[float(p[0]),float(p[1])],'diameter_mm':float(d),'drill_mm':float(drill),'role':role})

    # --- 12V_IN_RAW: spine 2 mm, stubs diagnósticos/sense pad-compatible.
    n='12V_IN_RAW'
    S(n,pcbnew.F_Cu,(168.405,3.325),(168.405,11.5),2.0)
    S(n,pcbnew.F_Cu,(168.405,11.5),(175.0,11.5),2.0)
    S(n,pcbnew.F_Cu,(175.0,11.5),(175.0,17.975),2.0)
    S(n,pcbnew.F_Cu,(175.0,17.975),(177.525,17.975),0.30,'smd_escape')
    S(n,pcbnew.F_Cu,(168.405,11.5),(168.405,18.775),2.0)
    S(n,pcbnew.F_Cu,(168.405,18.775),(165.865,18.775),2.0)
    S(n,pcbnew.F_Cu,(173.22,17.255),(173.22,15.0),0.50,'passive_stub')
    S(n,pcbnew.F_Cu,(173.22,15.0),(168.405,15.0),0.50,'passive_stub')
    S(n,pcbnew.F_Cu,(165.865,18.775),(164.0,18.775),0.40,'sense_stub')
    S(n,pcbnew.F_Cu,(164.0,18.775),(164.0,22.345),0.40,'sense_stub')
    S(n,pcbnew.F_Cu,(164.0,22.345),(164.785,22.345),0.40,'sense_stub')
    S(n,pcbnew.F_Cu,(164.0,22.345),(164.0,64.0),0.40,'test_stub')
    S(n,pcbnew.F_Cu,(164.0,64.0),(165.365,64.0),0.40,'test_stub')
    S(n,pcbnew.F_Cu,(165.365,64.0),(165.365,58.025),0.40,'test_stub')

    # --- 12V_PROTECTED: transición robusta a In2 y estrella Z3.
    n='12V_PROTECTED'
    S(n,pcbnew.F_Cu,(178.025,17.975),(180.0,17.975),0.30,'smd_escape')
    S(n,pcbnew.F_Cu,(180.0,17.975),(182.8,17.975),2.0)
    VIA(n,(181.4,17.3),1.2,0.6,'current_array')
    VIA(n,(181.4,18.7),1.2,0.6,'current_array')
    VIA(n,(182.8,17.975),1.2,0.6,'current_array')
    S(n,pcbnew.In2_Cu,(181.4,17.3),(182.8,17.975),2.0)
    S(n,pcbnew.In2_Cu,(181.4,18.7),(182.8,17.975),2.0)
    S(n,pcbnew.In2_Cu,(182.8,17.975),(182.8,43.0),2.0)
    S(n,pcbnew.In2_Cu,(182.8,43.0),(168.0,43.0),2.0)
    # bulk: subir a F desde la estrella para no cruzar troncales 5V/3V3 en In2
    VIA(n,(168.0,43.0),1.2,0.6)
    S(n,pcbnew.F_Cu,(168.0,43.0),(168.0,35.0),2.0)
    S(n,pcbnew.F_Cu,(168.0,35.0),(166.615,28.065),2.0)
    # net-ties: escape angosto solo junto al pad; vía ya fuera del par de pads
    S(n,pcbnew.F_Cu,(164.59,52.25),(164.2,50.0),0.40,'nettie_escape')
    VIA(n,(164.2,50.0),1.2,0.6)
    S(n,pcbnew.In2_Cu,(164.2,50.0),(164.2,45.0),2.0)
    S(n,pcbnew.In2_Cu,(164.2,45.0),(168.0,43.0),2.0)
    S(n,pcbnew.F_Cu,(166.89,52.25),(166.0,49.0),0.40,'nettie_escape')
    VIA(n,(166.0,49.0),1.2,0.6)
    S(n,pcbnew.In2_Cu,(166.0,49.0),(166.0,45.0),2.0)
    S(n,pcbnew.In2_Cu,(166.0,45.0),(168.0,43.0),2.0)
    S(n,pcbnew.F_Cu,(170.213,53.875),(170.213,49.0),2.0)
    VIA(n,(170.213,49.0),1.2,0.6)
    S(n,pcbnew.In2_Cu,(170.213,49.0),(170.213,43.0),2.0)
    S(n,pcbnew.F_Cu,(170.213,53.875),(170.213,56.0),0.50,'test_stub')
    S(n,pcbnew.F_Cu,(170.213,56.0),(168.215,56.0),0.50,'test_stub')
    S(n,pcbnew.F_Cu,(168.215,56.0),(168.215,58.025),0.50,'test_stub')

    # --- 12V_HOST_VIN: long-haul In2 desde la estrella hacia J_UNOQ.
    n='12V_HOST_VIN'
    S(n,pcbnew.F_Cu,(165.59,52.25),(165.59,54.5),0.50,'nettie_escape')
    VIA(n,(165.59,54.5),0.9,0.45)
    S(n,pcbnew.In2_Cu,(165.59,54.5),(165.59,51.5),1.0)
    S(n,pcbnew.In2_Cu,(165.59,51.5),(50.8,51.5),1.0)
    S(n,pcbnew.In2_Cu,(50.8,51.5),(50.8,45.72),1.0)

    # --- 12V_LOGIC: corredor In2 por borde derecho de Z3, lejos de troncales bajas.
    n='12V_LOGIC'
    S(n,pcbnew.F_Cu,(167.89,52.25),(168.8,55.0),0.50,'nettie_escape')
    VIA(n,(168.8,55.0),0.9,0.45)
    S(n,pcbnew.In2_Cu,(168.8,55.0),(197.8,55.0),1.0)
    S(n,pcbnew.In2_Cu,(197.8,55.0),(197.8,20.0),1.0)
    S(n,pcbnew.In2_Cu,(197.8,20.0),(184.5,20.0),1.0)
    VIA(n,(184.5,20.0),0.9,0.45)
    S(n,pcbnew.F_Cu,(184.5,20.0),(186.075,19.075),1.0)
    S(n,pcbnew.F_Cu,(186.075,19.075),(190.0,18.425),1.0)
    S(n,pcbnew.F_Cu,(190.0,18.425),(191.675,18.425),0.30,'smd_escape')
    S(n,pcbnew.F_Cu,(189.725,19.075),(189.725,18.75),0.50,'passive_stub')
    S(n,pcbnew.F_Cu,(189.725,18.75),(190.0,18.425),0.50,'passive_stub')
    S(n,pcbnew.F_Cu,(167.89,52.25),(171.065,55.5),0.50,'test_stub')
    S(n,pcbnew.F_Cu,(171.065,55.5),(171.065,58.025),0.50,'test_stub')

    # --- 5V_RAIL: isla buck en F, troncal horizontal In2 a Z1, TP por F.
    n='5V_RAIL'
    S(n,pcbnew.F_Cu,(191.875,20.075),(191.42,23.875),0.75)
    S(n,pcbnew.F_Cu,(191.42,23.875),(187.245,25.5),0.75)
    S(n,pcbnew.F_Cu,(187.245,25.5),(187.245,26.785),0.50,'passive_stub')
    S(n,pcbnew.F_Cu,(187.245,26.785),(182.19,27.925),0.75)
    S(n,pcbnew.F_Cu,(182.19,27.925),(179.5,28.0),0.75)
    VIA(n,(179.5,28.0),0.8,0.4)
    S(n,pcbnew.In2_Cu,(179.5,28.0),(57.315,28.0),0.75)
    S(n,pcbnew.In2_Cu,(57.315,28.0),(57.315,3.635),0.75)
    S(n,pcbnew.In2_Cu,(69.265,28.0),(69.265,3.635),0.75)
    S(n,pcbnew.In2_Cu,(99.815,28.0),(99.815,3.635),0.75)
    # TP: salir a F antes de cruzar la futura troncal 3V3
    VIA(n,(126.0,28.0),0.8,0.4,'test_branch')
    S(n,pcbnew.F_Cu,(126.0,28.0),(126.0,55.0),0.75,'test_branch')
    S(n,pcbnew.F_Cu,(126.0,55.0),(113.715,55.0),0.75,'test_branch')
    S(n,pcbnew.F_Cu,(113.715,55.0),(113.715,58.025),0.75,'test_branch')
    # feedback/pull-up y entrada LDO como stubs locales del rail
    S(n,pcbnew.F_Cu,(191.6,15.9),(191.6,18.7),0.40,'passive_stub')
    S(n,pcbnew.F_Cu,(191.6,18.7),(191.875,20.075),0.40,'passive_stub')
    S(n,pcbnew.F_Cu,(192.615,26.795),(191.42,25.5),0.40,'passive_stub')
    S(n,pcbnew.F_Cu,(182.19,27.925),(182.07,31.105),0.75)
    S(n,pcbnew.F_Cu,(182.07,31.105),(186.088,31.125),0.75)

    # --- 3V3_RAIL: fuente local F, troncal In2 solo hacia la izquierda; bus Z4 en F.
    n='3V3_RAIL'
    S(n,pcbnew.F_Cu,(188.363,31.125),(190.83,31.105),0.40)
    S(n,pcbnew.F_Cu,(190.83,31.105),(194.365,30.835),0.40)
    S(n,pcbnew.F_Cu,(194.365,30.835),(194.365,36.0),0.40)
    S(n,pcbnew.F_Cu,(194.365,36.0),(179.0,36.0),0.40)
    VIA(n,(179.0,36.0),0.7,0.35)
    S(n,pcbnew.In2_Cu,(179.0,36.0),(80.0,36.0),0.40)
    # Z1 TEMP
    VIA(n,(82.0,36.0),0.7,0.35)
    S(n,pcbnew.F_Cu,(82.0,36.0),(82.0,16.995),0.40)
    S(n,pcbnew.F_Cu,(82.0,16.995),(80.835,16.995),0.40)
    S(n,pcbnew.F_Cu,(82.0,16.995),(81.215,3.635),0.40)
    # Z1 CO2/pull-ups
    VIA(n,(96.5,36.0),0.7,0.35)
    S(n,pcbnew.F_Cu,(96.5,36.0),(96.5,18.5),0.40)
    S(n,pcbnew.F_Cu,(96.5,18.5),(88.5,18.5),0.40)
    for x,y in [(89.02,16.985),(91.68,16.995),(94.39,16.995)]: S(n,pcbnew.F_Cu,(x,18.5),(x,y),0.40,'passive_stub')
    S(n,pcbnew.F_Cu,(96.5,18.5),(96.5,5.0),0.40)
    S(n,pcbnew.F_Cu,(96.5,5.0),(95.115,2.355),0.30,'smd_escape')
    # Z2 TP + watchdog
    VIA(n,(109.5,36.0),0.7,0.35)
    S(n,pcbnew.F_Cu,(109.5,36.0),(109.5,54.0),0.40)
    S(n,pcbnew.F_Cu,(109.5,54.0),(110.865,58.025),0.40)
    S(n,pcbnew.F_Cu,(109.5,54.0),(118.5,54.0),0.40)
    for x,y in [(113.052,50.275),(115.235,49.995),(117.955,49.985)]: S(n,pcbnew.F_Cu,(x,54.0),(x,y),0.40,'passive_stub')
    # Z2 HX711 + loadcell
    VIA(n,(125.0,36.0),0.7,0.35)
    S(n,pcbnew.F_Cu,(125.0,36.0),(125.0,23.0),0.40)
    S(n,pcbnew.F_Cu,(125.0,23.0),(109.5,23.0),0.40)
    S(n,pcbnew.F_Cu,(111.028,23.0),(111.028,17.53),0.40)
    S(n,pcbnew.F_Cu,(111.028,20.07),(111.028,17.53),0.40)
    for x,y in [(117.203,17.53),(119.645,16.985),(122.635,17.505)]: S(n,pcbnew.F_Cu,(x,23.0),(x,y),0.40,'passive_stub')
    S(n,pcbnew.F_Cu,(109.5,23.0),(109.5,8.0),0.40)
    S(n,pcbnew.F_Cu,(109.5,8.0),(113.905,3.325),0.40)
    # Z2 I2C/GNSS
    VIA(n,(145.5,36.0),0.7,0.35)
    S(n,pcbnew.F_Cu,(145.5,36.0),(145.5,19.0),0.40)
    S(n,pcbnew.F_Cu,(145.5,19.0),(135.5,19.0),0.40)
    for x,y in [(136.775,16.995),(139.485,16.995)]: S(n,pcbnew.F_Cu,(x,19.0),(x,y),0.40,'passive_stub')
    S(n,pcbnew.F_Cu,(145.5,19.0),(144.685,3.635),0.40)
    # Z2 HMI lado 3V3
    VIA(n,(160.5,36.0),0.7,0.35)
    S(n,pcbnew.F_Cu,(160.5,36.0),(160.5,20.5),0.40)
    S(n,pcbnew.F_Cu,(160.5,20.5),(153.935,20.5),0.40)
    for x,y in [(153.935,18.275),(157.035,18.275),(158.965,16.985)]: S(n,pcbnew.F_Cu,(x,20.5),(x,y),0.30 if '15' else 0.40,'smd_escape' if x in (153.935,157.035) else 'passive_stub')
    # Z4 bus: continuar en F desde la fuente, separado de 12V_ACT dirty (y=63/40)
    S(n,pcbnew.F_Cu,(194.365,36.0),(234.0,36.0),0.40)
    S(n,pcbnew.F_Cu,(199.785,36.0),(199.785,49.995),0.40)
    # pump pin16: fanout por la derecha evitando vías existentes
    S(n,pcbnew.F_Cu,(211.0,36.0),(211.0,28.0),0.40)
    S(n,pcbnew.F_Cu,(211.0,28.0),(215.5,28.0),0.40)
    S(n,pcbnew.F_Cu,(215.5,28.0),(215.5,23.0),0.40)
    S(n,pcbnew.F_Cu,(215.5,23.0),(214.5,20.0),0.40)
    S(n,pcbnew.F_Cu,(214.5,20.0),(213.6,18.825),0.40)
    S(n,pcbnew.F_Cu,(213.6,18.825),(212.325,18.825),0.20,'smd_escape')
    # CO2 open-load pull-up pad1 desde la izquierda
    S(n,pcbnew.F_Cu,(215.0,36.0),(215.0,20.045),0.40)
    S(n,pcbnew.F_Cu,(215.0,20.045),(216.415,20.045),0.40)
    # chiller LED resistor pad1
    S(n,pcbnew.F_Cu,(232.635,36.0),(232.635,29.0),0.40)
    S(n,pcbnew.F_Cu,(232.635,29.0),(232.635,23.445),0.40)

    # --- 12V_ACT: dirty trunk F, solo Z3/Z4; top corridor preserva sensible PUMP_CURRENT_ADC.
    n='12V_ACT'
    S(n,pcbnew.F_Cu,(175.118,53.875),(175.118,63.0),1.0)
    S(n,pcbnew.F_Cu,(173.915,58.025),(175.118,58.025),0.50,'test_stub')
    S(n,pcbnew.F_Cu,(175.118,63.0),(198.8,63.0),1.0)
    S(n,pcbnew.F_Cu,(198.8,63.0),(198.8,40.0),1.0)
    S(n,pcbnew.F_Cu,(198.8,40.0),(222.0,40.0),1.0)
    # pump left power pin6 + caps
    S(n,pcbnew.F_Cu,(207.5,40.0),(207.5,19.325),1.0)
    S(n,pcbnew.F_Cu,(207.5,19.325),(209.025,19.325),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(207.5,27.0),(205.52,17.255),1.0)
    S(n,pcbnew.F_Cu,(205.52,17.255),(200.19,18.125),1.0)
    # pump pin15 por fanout corto a la derecha
    S(n,pcbnew.F_Cu,(213.5,40.0),(213.5,19.325),1.0)
    S(n,pcbnew.F_Cu,(213.5,19.325),(212.325,19.325),0.20,'smd_escape')
    # CO2 pin8 por la derecha
    S(n,pcbnew.F_Cu,(220.5,40.0),(220.5,19.5),1.0)
    S(n,pcbnew.F_Cu,(220.5,19.5),(220.5,18.375),0.30,'smd_escape')
    S(n,pcbnew.F_Cu,(220.5,18.375),(218.82,18.375),0.20,'smd_escape')
    # bypass CO2 desde rama segura a la izquierda de la vía sensible
    S(n,pcbnew.F_Cu,(213.5,19.325),(213.0,19.325),0.40,'passive_stub')
    S(n,pcbnew.F_Cu,(213.0,19.325),(213.0,17.255),0.40,'passive_stub')
    S(n,pcbnew.F_Cu,(213.0,17.255),(213.99,17.255),0.40,'passive_stub')

    # --- PUMP_OUT1: salida dirty por In2; F solo fanout/TP.
    n='PUMP_OUT1'
    S(n,pcbnew.F_Cu,(209.025,19.825),(207.5,19.825),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(209.025,20.325),(207.5,20.325),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(207.5,19.825),(207.5,20.325),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(207.5,20.075),(205.5,20.075),0.75)
    VIA(n,(205.5,20.075),0.9,0.45)
    S(n,pcbnew.In2_Cu,(205.5,20.075),(202.0,20.075),0.75)
    S(n,pcbnew.In2_Cu,(202.0,8.0),(202.0,56.0),0.75)
    S(n,pcbnew.In2_Cu,(202.0,8.0),(203.405,3.325),0.75)
    S(n,pcbnew.In2_Cu,(202.0,56.0),(204.0,56.0),0.75)
    VIA(n,(204.0,56.0),0.9,0.45)
    S(n,pcbnew.F_Cu,(204.0,56.0),(203.465,58.275),0.75)

    # --- PUMP_OUT2
    n='PUMP_OUT2'
    S(n,pcbnew.F_Cu,(212.325,19.825),(214.0,19.825),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(212.325,20.325),(214.0,20.325),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(214.0,19.825),(214.0,20.325),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(214.0,20.075),(216.5,20.075),0.75)
    VIA(n,(216.5,20.075),0.9,0.45)
    S(n,pcbnew.In2_Cu,(216.5,20.075),(206.5,20.075),0.75)
    S(n,pcbnew.In2_Cu,(206.5,8.0),(206.5,56.0),0.75)
    S(n,pcbnew.In2_Cu,(206.5,8.0),(208.485,3.325),0.75)
    VIA(n,(206.5,56.0),0.9,0.45)
    S(n,pcbnew.F_Cu,(206.5,56.0),(206.815,58.275),0.75)

    # --- CO2_SOL_POS
    n='CO2_SOL_POS'
    S(n,pcbnew.F_Cu,(218.82,17.875),(219.5,17.875),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(219.5,17.875),(219.5,16.8),0.20,'smd_escape')
    S(n,pcbnew.F_Cu,(219.5,16.8),(221.0,16.8),0.75)
    VIA(n,(221.0,16.8),0.9,0.45)
    S(n,pcbnew.In2_Cu,(221.0,8.0),(221.0,56.0),0.75)
    S(n,pcbnew.In2_Cu,(221.0,8.0),(217.625,3.325),0.75)
    S(n,pcbnew.In2_Cu,(221.0,56.0),(214.5,56.0),0.75)
    VIA(n,(214.5,56.0),0.9,0.45)
    S(n,pcbnew.F_Cu,(214.5,56.0),(213.015,58.275),0.75)

    manifest={
      'schema_version':1,'status':'CANDIDATE_POWER_ROUTING_PR20A','target_nets':TARGET,
      'baseline':{'segments':BASE_SEG,'vias':BASE_VIA,'zones':0},
      'new_segment_count':len(new_segments),'new_via_count':len(new_vias),
      'new_segments':new_segments,'new_vias':new_vias,
      'policies':{'in1_signal_tracks':0,'zones_added':0,'gnd_copper_added':0,'future_batch_copper':0,'placement_change':0,'outline_change':0},
      'distribution_width_mm':{'12V_IN_RAW':2.0,'12V_PROTECTED':2.0,'12V_HOST_VIN':1.0,'12V_LOGIC':1.0,'12V_ACT':1.0,'5V_RAIL':0.75,'3V3_RAIL':0.40,'PUMP_OUT1':0.75,'PUMP_OUT2':0.75,'CO2_SOL_POS':0.75},
      'escape_policy':'Pad-compatible local neck-down only; trunks retain frozen PR18 widths; no clearance relaxation.'
    }
    pcbnew.SaveBoard(str(PCB),b); OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'PR20A candidate: +{len(new_segments)} segments +{len(new_vias)} vias => {BASE_SEG+len(new_segments)}/{BASE_VIA+len(new_vias)}')

if __name__=='__main__': main()
