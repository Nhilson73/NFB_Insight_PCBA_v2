#!/usr/bin/env python3
"""Congela el routing del ECO HMI después de materializar PR19D."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'hardware/hmi_system_contract.json'; d=json.loads(p.read_text(encoding='utf-8'))
d['pcba_interface']['routing_frozen']=True
d['pcba_interface']['routing_checkpoint']='PR19D_5V_HMI'
d['pcba_interface']['routing_note']='PR19D cerró exclusivamente 5V_HMI. HMI UART PR19A/PR19C y placement permanecen congelados.'
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
e=ROOT/'hardware/hmi_power_eco.json'; x=json.loads(e.read_text(encoding='utf-8')); x['routing_status']='5V_HMI_1_OF_1_ROUTED'; x['design_closure']='CLOSED'; e.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('OK: ECO HMI conserva status PR19D y routing queda CLOSED')
