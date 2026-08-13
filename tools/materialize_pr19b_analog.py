#!/usr/bin/env python3
"""Añade únicamente el cobre PR19B al PCB PR19A persistido."""
from pathlib import Path
import json
import pcbnew  # type: ignore

ROOT=Path(__file__).resolve().parents[1]
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
OUT=ROOT/'hardware'/'pr19b_analog_routing_manifest.json'
TARGET=('PH_ADC','ORP_ADC','DO_ADC','PUMP_CURRENT_ADC')

def iu(x): return pcbnew.FromMM(float(x))

def main():
    b=pcbnew.LoadBoard(str(PCB))
    seg0=sum(not isinstance(x,pcbnew.PCB_VIA) for x in b.GetTracks())
    via0=sum(isinstance(x,pcbnew.PCB_VIA) for x in b.GetTracks())
    assert (seg0,via0)==(523,24),(seg0,via0)
    ni={}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() in TARGET: ni[p.GetNetname()]=p.GetNet()
    assert set(ni)==set(TARGET)
    assert not any(x.GetNetname() in TARGET for x in b.GetTracks())
    seg=[]; vias=[]
    def tr(n,l,a,c):
        x=pcbnew.PCB_TRACK(b); x.SetNet(ni[n]); x.SetLayer(l); x.SetWidth(iu(.20))
        x.SetStart(pcbnew.VECTOR2I(iu(a[0]),iu(a[1]))); x.SetEnd(pcbnew.VECTOR2I(iu(c[0]),iu(c[1]))); b.Add(x)
        seg.append({'net':n,'layer':b.GetLayerName(l),'start_mm':list(a),'end_mm':list(c),'width_mm':.20})
    def pl(n,l,p):
        for a,c in zip(p,p[1:]): tr(n,l,a,c)
    def va(n,p):
        x=pcbnew.PCB_VIA(b); x.SetNet(ni[n]); x.SetPosition(pcbnew.VECTOR2I(iu(p[0]),iu(p[1])))
        x.SetWidth(iu(.60)); x.SetDrill(iu(.30)); x.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); b.Add(x)
        vias.append({'net':n,'x_mm':p[0],'y_mm':p[1],'diameter_mm':.60,'drill_mm':.30})

    pl('PH_ADC',pcbnew.F_Cu,[(58.255,16.995),(58.255,19.5),(59.955,19.5),(59.955,16.985)])
    va('PH_ADC',(59.955,19.5)); pl('PH_ADC',pcbnew.B_Cu,[(59.955,19.5),(59.955,50.8),(50.8,50.8)])

    for p in [(67.455,16.995),(69.145,16.995),(71.885,17.125),(74.315,16.985)]: pl('ORP_ADC',pcbnew.F_Cu,[p,(p[0],20.5)])
    pl('ORP_ADC',pcbnew.F_Cu,[(67.455,20.5),(74.315,20.5)]); va('ORP_ADC',(74.315,20.5))
    pl('ORP_ADC',pcbnew.B_Cu,[(74.315,20.5),(74.315,53.34),(50.8,53.34)])

    pl('DO_ADC',pcbnew.F_Cu,[(101.78,16.995),(101.78,21.5),(103.48,21.5),(103.48,16.985)])
    va('DO_ADC',(103.48,21.5)); pl('DO_ADC',pcbnew.B_Cu,[(103.48,21.5),(103.48,63.5),(50.8,63.5)])

    pl('PUMP_CURRENT_ADC',pcbnew.F_Cu,[(212.325,18.325),(215.5,18.325)]); va('PUMP_CURRENT_ADC',(215.5,18.325))
    pl('PUMP_CURRENT_ADC',pcbnew.B_Cu,[(215.5,18.325),(215.5,26.5),(203.5,26.5)]); va('PUMP_CURRENT_ADC',(203.5,26.5))
    pl('PUMP_CURRENT_ADC',pcbnew.F_Cu,[(203.5,26.5),(202.505,26.5),(202.505,24.725)])
    pl('PUMP_CURRENT_ADC',pcbnew.F_Cu,[(202.505,26.5),(199.785,26.5),(199.785,24.735)])
    pl('PUMP_CURRENT_ADC',pcbnew.B_Cu,[(203.5,26.5),(203.5,66.0),(105.0,66.0)])
    pl('PUMP_CURRENT_ADC',pcbnew.F_Cu,[(200.365,58.025),(200.365,59.5),(201.5,59.5)]); va('PUMP_CURRENT_ADC',(201.5,59.5))
    pl('PUMP_CURRENT_ADC',pcbnew.B_Cu,[(201.5,59.5),(203.5,59.5)]); va('PUMP_CURRENT_ADC',(105.0,66.0))
    pl('PUMP_CURRENT_ADC',pcbnew.F_Cu,[(105.0,66.0),(53.5,66.0),(53.5,60.96),(50.8,60.96)])

    m={'schema_version':1,'status':'PR19B_ANALOG_ROUTING_CANDIDATE','batch':'PR19B','target_nets':list(TARGET),
       'baseline_pr19a':{'segments':523,'vias':24},'new_segments':seg,'new_vias':vias,
       'new_segment_count':len(seg),'new_via_count':len(vias),'policies':{'in1_signal_tracks':0,'zones_added':0,'future_batch_copper':0}}
    OUT.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    pcbnew.SaveBoard(str(PCB),b); print('PR19B_CANDIDATE',len(seg),len(vias))
if __name__=='__main__': main()
