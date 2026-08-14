#!/usr/bin/env python3
"""Guardrail reusable para checkpoints incrementales PRE_ROUTING→PR19D.

PR19D es un ECO posterior a PR19C que introduce únicamente 5V_HMI. Los
manifests PR19A/B/C permanecen históricos e inmutables; no se reescriben para
hacer parecer que conocían una net creada después.
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BATCHES=ROOT/'hardware'/'routing_batches_contract.json'
MA=ROOT/'hardware'/'pr19a_local_routing_manifest.json'
MB=ROOT/'hardware'/'pr19b_analog_routing_manifest.json'
MC=ROOT/'hardware'/'pr19c_digital_routing_manifest.json'
MD=ROOT/'hardware'/'pr19d_hmi_power_routing_manifest.json'

def _fail(ctx,msg): raise SystemExit(f'ERROR: {ctx}: {msg}')
def _load(p): return json.loads(p.read_text(encoding='utf-8'))
def copper_counts(text):
    return {'segments':len(re.findall(r'(?m)^\s*\(segment\b',text)),'vias':len(re.findall(r'(?m)^\s*\(via\b',text)),'zones':len(re.findall(r'(?m)^\s*\(zone\b',text))}

def assert_authorized_phase(pcb_text:str, context:str='routing phase')->str:
    counts=copper_counts(pcb_text)
    if counts=={'segments':0,'vias':0,'zones':0}: return 'PRE_ROUTING'
    if not BATCHES.exists() or not MA.exists(): _fail(context,f'cobre presente sin contrato/manifest: {counts}')
    rb=_load(BATCHES); batches={x['id']:x for x in rb.get('batches',[])}
    expected_ids=['PR19A','PR19B','PR19C','PR19D','PR20A','PR20B']
    if list(batches)!=expected_ids: _fail(context,f'partición inesperada: {list(batches)}')
    a=set(batches['PR19A']['nets']); b=set(batches['PR19B']['nets']); c=set(batches['PR19C']['nets']); d=set(batches['PR19D']['nets'])
    p20=set(batches['PR20A']['nets'])|set(batches['PR20B']['nets'])
    if (len(a),len(b),len(c),len(d),len(p20))!=(28,4,16,1,11): _fail(context,'conteos de lotes inesperados')
    if d!={'5V_HMI'}: _fail(context,'PR19D debe contener solo 5V_HMI')

    ma=_load(MA)
    if ma.get('status')!='LOCAL_ROUTING_PR19A' or set(ma.get('routed_nets',[]))!=a: _fail(context,'manifest PR19A inválido')
    # Histórico: PR19A difería 31 nets; 5V_HMI aún no existía.
    historical_future_a=b|c|p20
    if set(ma.get('deferred_nets',[]))!=historical_future_a or len(historical_future_a)!=31: _fail(context,'deferred PR19A histórico cambió')
    if (len(ma.get('segments',[])),len(ma.get('vias',[])))!=(523,24): _fail(context,'checkpoint PR19A cambió')
    exp_a={'segments':523,'vias':24,'zones':0}
    if not MB.exists():
        if counts!=exp_a: _fail(context,f'PCB != PR19A {counts}')
        return 'PR19A'

    mb=_load(MB)
    if mb.get('status')!='ANALOG_ROUTING_PR19B' or set(mb.get('target_nets',[]))!=b: _fail(context,'manifest PR19B inválido')
    if mb.get('baseline_pr19a')!={'segments':523,'vias':24}: _fail(context,'baseline PR19B cambió')
    if (mb.get('new_segment_count'),mb.get('new_via_count'))!=(32,7): _fail(context,'conteos PR19B cambiaron')
    if {x.get('net') for x in mb.get('new_segments',[])+mb.get('new_vias',[])}!=b: _fail(context,'cobre PR19B fuera de alcance')
    if mb.get('policies')!={'in1_signal_tracks':0,'zones_added':0,'future_batch_copper':0}: _fail(context,'políticas PR19B cambiaron')
    exp_b={'segments':555,'vias':31,'zones':0}
    if not MC.exists():
        if counts!=exp_b: _fail(context,f'PCB != PR19B {counts}')
        return 'PR19B'

    mc=_load(MC)
    if mc.get('status')!='DIGITAL_ROUTING_PR19C' or set(mc.get('target_nets',[]))!=c: _fail(context,'manifest PR19C inválido')
    if mc.get('baseline')!={'segments':555,'vias':31}: _fail(context,'baseline PR19C cambió')
    if (mc.get('new_segment_count'),mc.get('new_via_count'))!=(362,88): _fail(context,'conteos PR19C cambiaron')
    if {x.get('net') for x in mc.get('new_segments',[])+mc.get('new_vias',[])}!=c: _fail(context,'cobre PR19C fuera de alcance')
    if mc.get('policies')!={'in1_signal_tracks':0,'zones_added':0,'future_batch_copper':0}: _fail(context,'políticas PR19C cambiaron')
    exp_c={'segments':917,'vias':119,'zones':0}
    if not MD.exists():
        if counts!=exp_c: _fail(context,f'PCB != PR19C {counts}')
        return 'PR19C'

    md=_load(MD)
    if md.get('status')!='HMI_POWER_ROUTING_PR19D' or set(md.get('target_nets',[]))!=d: _fail(context,'manifest PR19D inválido')
    if md.get('baseline')!={'segments':917,'vias':119}: _fail(context,'baseline PR19D cambió')
    if (md.get('new_segment_count'),md.get('new_via_count'))!=(7,2): _fail(context,'PR19D debe ser 7 segmentos/2 vías')
    touched={x.get('net') for x in md.get('new_segments',[])+md.get('new_vias',[])}
    if touched!=d: _fail(context,f'cobre PR19D fuera de alcance: {touched}')
    expected_policy={'in1_signal_tracks':0,'zones_added':0,'existing_routing_removed':0,'uart_routing_changed':0,'future_batch_copper':0}
    if md.get('policies')!=expected_policy: _fail(context,'políticas PR19D cambiaron')
    exp_d={'segments':924,'vias':121,'zones':0}
    if counts!=exp_d: _fail(context,f'PCB != PR19D actual={counts} esperado={exp_d}')
    return 'PR19D'
