#!/usr/bin/env python3
"""Congela el routing y la política de escape del ECO HMI PR19D."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

p=ROOT/'hardware/hmi_system_contract.json'; d=load(p)
d['pcba_interface']['routing_frozen']=True
d['pcba_interface']['routing_checkpoint']='PR19D_5V_HMI'
d['pcba_interface']['routing_note']='PR19D cerró exclusivamente 5V_HMI. HMI UART PR19A/PR19C y placement permanecen congelados.'
save(p,d)

e=ROOT/'hardware/hmi_power_eco.json'; x=load(e)
x['routing_status']='5V_HMI_1_OF_1_ROUTED'; x['design_closure']='CLOSED'
x['smd_escape_policy']={
  'ref_pad':'U_HMI_LVL.7',
  'package':'VSSOP-8_DCU',
  'escape_width_mm':0.20,
  'max_escape_length_mm':1.20,
  'distribution_width_mm':0.40,
  'clearance_mm':0.20,
  'reason':'El pitch VSSOP no admite 0.40 mm entre pads adyacentes conservando 0.20 mm de clearance; el neck-down termina al liberar el encapsulado.'
}
save(e,x)

r=ROOT/'hardware/routing_contract.json'; rc=load(r)
cls=next((c for c in rc['routing_classes'] if c['name']=='HMI_FIELD_POWER'),None)
if cls is None: raise SystemExit('ERROR: falta routing class HMI_FIELD_POWER')
cls['smd_escape_exception']={
  'allowed_refs_pads':['U_HMI_LVL.7'],
  'width_mm':0.20,
  'max_length_mm':1.20,
  'clearance_mm_min':0.20,
  'distribution_width_mm_min':0.40,
  'scope':'fanout inmediato del VSSOP únicamente'
}
cls['rules']=[r for r in cls['rules'] if not r.startswith('SMD escape:')]
cls['rules'].append('SMD escape: U_HMI_LVL.7 puede usar 0.20 mm por <=1.20 mm; clearance permanece >=0.20 mm y luego retorna a 0.40 mm.')
save(r,rc)
print('OK: ECO HMI conserva status PR19D; routing y escape VSSOP quedan CLOSED')
