#!/usr/bin/env python3
"""Materializa el ECO de alimentación dedicada 5V_HMI sin tocar placement/routing.

La alimentación de potencia de la Nextion pasa a un subensamble externo protegido.
La PCBA recibe 5V_HMI únicamente para el lado B del TXU0202 y su desacoplo local.
"""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECOM_URL='https://recom-power.com/en/products/switching-regulators/switching-regulators-sip/rec-p-R-78K5.0-2.0L.html'
RECOM_SERIES='https://recom-power.com/en/rec-s-R-78K-2.0.html'
FUSE_URL='https://www.littelfuse.com/products/fuses-overcurrent-protection/fuses/automotive-fuses/blade-fuses-shunt/mini/997/0997002-wxn'
HOLDER_URL='https://www.littelfuse.com/products/fuses-overcurrent-protection/fuse-holders-fuse-blocks-accessories/fuse-holders/in-line-fuse-holders/mini-fhm/0fhm0001zxj'

def loadj(rel): return json.loads((ROOT/rel).read_text(encoding='utf-8'))
def savej(rel,d): (ROOT/rel).write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def fail(m): raise SystemExit('ERROR: '+m)

def replace_net_nodes(netlist, old, new, nodes):
    by={n['name']:n for n in netlist['nets']}
    if old not in by: fail(f'falta net {old}')
    old_nodes=list(by[old]['nodes'])
    for node in nodes:
        if node not in old_nodes: fail(f'{node} no estaba en {old}')
        old_nodes.remove(node)
    by[old]['nodes']=old_nodes
    if new in by: fail(f'{new} ya existía antes del ECO')
    netlist['nets'].append({'name':new,'nodes':nodes})

# 1) Contrato HMI
h=loadj('hardware/hmi_system_contract.json')
if h.get('status')!='HMI_SYSTEM_DECISION_NEXTION_NX8048P050_011C_Y': fail('baseline HMI inesperado')
iface=h['pcba_interface']
iface['pinout_board']['1']='5V_HMI'
iface['signal_mapping']['power']='5V_HMI'
iface['power_origin']='EXTERNAL_HMI_POWER_ASSEMBLY'
iface['routing_frozen']=False
iface['routing_note']='PR19D autoriza exclusivamente el nuevo net local 5V_HMI; HMI UART PR19A/PR19C permanece congelado.'
h['dedicated_power_assembly']={
  'status':'SELECTED_POWER_ECO_CLOSED',
  'architecture':'12V_SYSTEM -> 2A branch fuse -> RECOM R-78K5.0-2.0L -> 5V_HMI -> Nextion + BOX Speaker; 5V_HMI also returns low-current to J_HMI.1',
  'location':'external, adjacent to HMI inside product enclosure; not populated on NFB main PCBA',
  'input':{'nominal_v':12.0,'source':'same certified system PSU, branch split upstream of NFB PCBA eFuse'},
  'fuse_holder':{'manufacturer':'Littelfuse','mpn':'0FHM0001ZXJ','series':'MINI-FHM','rating_v_max':58,'wire_awg':14,'ip_rating':'IP67','status':'ACTIVE','source':HOLDER_URL},
  'fuse':{'manufacturer':'Littelfuse','mpn':'0997002.WXN','series':'997 MINI','rating_v':58,'rating_a':2.0,'status':'ACTIVE','source':FUSE_URL},
  'converter':{
    'manufacturer':'RECOM','mpn':'R-78K5.0-2.0L','series':'R-78K-2.0(L)','topology':'non-isolated switching regulator','vin_v':[6.5,36.0],
    'vout_v':5.0,'iout_a':2.0,'power_w':10.0,'efficiency_max_pct':96.0,'mounting':'THT, pre-formed 90 degree leads, horizontal','low_profile_height_mm':8.5,
    'body_reference_mm':[11.5,8.5,17.5],'certifications':['CB','EN 62368-1'],'protection':['undervoltage','short-circuit'],'source':RECOM_URL,'series_source':RECOM_SERIES,
    'mechanical_footprint':'NFB:RECOM_R78K5_0_2_0L_External'
  },
  'output':{'net':'5V_HMI','design_load_a':1.5,'converter_rating_a':2.0,'headroom_a':0.5,'headroom_pct':33.333},
  'grounding':'non-isolated converter; common system GND; no separate ground island',
  'release_checks':['verify 5V_HMI at J_HMI under display+speaker worst case','thermal check of external converter at enclosure ambient','verify 2A branch fuse does not nuisance-trip during HMI startup','EMC/pre-compliance with final harness']
}
p=h['power_integration']
p['status']='POWER_ECO_CLOSED_EXTERNAL_5V_HMI'
p['decision']='HMI+speaker no longer load NFB 5V_RAIL. Dedicated external R-78K5.0-2.0L provides 5V_HMI/2A, protected by a 2A MINI branch fuse.'
p['current_5v_rail_also_feeds']=['pH module','ORP module','DO module','3.3V LDO input']
p['pcba_5v_hmi_load']='TXU0202 VCCB + C_HMI_B only; HMI display/audio current bypasses main PCBA.'
p['acceptable_closure']=['CLOSED: external dedicated 5V_HMI assembly selected and versioned.']
h['release_gates']=[g for g in h['release_gates'] if 'Cerrar power ECO' not in g]
h['release_gates'].insert(1,'Validar 5V_HMI externo: R-78K5.0-2.0L + 0FHM0001ZXJ + 0997002.WXN, incluyendo prueba térmica/corriente y arranque.')
savej('hardware/hmi_system_contract.json',h)

# 2) Z2 contract, conservando status histórico para compatibilidad de baseline
z=loadj('hardware/z2_digital_contract.json')
hz=z['hmi_uart']
hz['connector']['pinout']['1']='5V_HMI'
hz['translator']['vccb_net']='5V_HMI'
hz['translator']['pinout']['7']='5V_HMI'
hz['power_eco']={'status':'CLOSED_PR19D','system_contract':'hardware/hmi_system_contract.json','field_power_net':'5V_HMI','rule':'5V_HMI must never tie to 5V_RAIL or J_UNOQ.5'}
hz['phase3_resolution']='PR #9 historical: TPSM33625RDNR local 5V_RAIL was limited to 1.5 A continuous. PR19D closes HMI power ECO by moving J_HMI/TXU0202 VCCB to dedicated external 5V_HMI; 5V_RAIL no longer powers the display/audio.'
savej('hardware/z2_digital_contract.json',z)

# 3) Z2 production netlist: only three existing endpoints migrate to new local net
n=loadj('hardware/z2_production_netlist.json')
cm={c['ref']:c for c in n['components']}
for ref,pin in [('J_HMI','1'),('U_HMI_LVL','7'),('C_HMI_B','1')]:
    if cm[ref]['pins'][pin]!='5V_RAIL': fail(f'{ref}.{pin} baseline != 5V_RAIL')
    cm[ref]['pins'][pin]='5V_HMI'
replace_net_nodes(n,'5V_RAIL','5V_HMI',['J_HMI.1','U_HMI_LVL.7','C_HMI_B.1'])
n['hmi_power_eco']={'status':'PR19D_5V_HMI','new_local_net':'5V_HMI','removed_from_5V_RAIL':['J_HMI.1','U_HMI_LVL.7','C_HMI_B.1'],'display_power_on_pcba':False}
savej('hardware/z2_production_netlist.json',n)

# 4) BOM Z2: refs intact, notas explícitas
zp=ROOT/'bom/insight_z2_production_bom.csv'
with zp.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f)); fields=f.fieldnames
for r in rows:
    if r['ref']=='J_HMI': r['nota']='5V_HMI/GND/RX/TX; side-entry -Y. 5V_HMI proviene del subensamble externo RECOM; display/audio NO cargan 5V_RAIL.'
    elif r['ref']=='U_HMI_LVL': r['nota']='TXU0202: VCCA=3V3_RAIL, VCCB=5V_HMI dedicado; UART D0/D1 preservado.'
    elif r['ref']=='C_HMI_B': r['nota']='Desacoplo VCCB del TXU0202 sobre 5V_HMI dedicado.'
with zp.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

# 5) BOM sistema HMI: componentes exactos del subensamble de potencia
bp=ROOT/'bom/insight_hmi_system_bom.csv'
with bp.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f)); fields=f.fieldnames
rows=[r for r in rows if r['item_id'] not in {'HMI_PWR_REG','HMI_PWR_FUSE_HOLDER','HMI_PWR_FUSE'}]
rows += [
 {'categoria':'HMI_POWER','item_id':'HMI_PWR_REG','qty':'1','rol_producto':'PRODUCTION_EXTERNAL_POWER_ASSEMBLY','fabricante':'RECOM','mpn_modelo':'R-78K5.0-2.0L','sku':'','footprint_o_mecanica':'NFB:RECOM_R78K5_0_2_0L_External','poblacion_pcba':'NO','alimentacion':'6.5-36V -> 5V/2A, 10W','interfaz':'SIP3 / harness externo','fuente':RECOM_URL,'nota':'No aislado; versión L horizontal 8.5mm; alimenta 5V_HMI.'},
 {'categoria':'HMI_POWER','item_id':'HMI_PWR_FUSE_HOLDER','qty':'1','rol_producto':'PRODUCTION_EXTERNAL_POWER_ASSEMBLY','fabricante':'Littelfuse','mpn_modelo':'0FHM0001ZXJ','sku':'','footprint_o_mecanica':'INLINE HARNESS IP67','poblacion_pcba':'NO','alimentacion':'58V max / 20A holder','interfaz':'MINI fuse / 14AWG leads','fuente':HOLDER_URL,'nota':'Holder inline IP67 dedicado a rama 12V_HMI.'},
 {'categoria':'HMI_POWER','item_id':'HMI_PWR_FUSE','qty':'1','rol_producto':'PRODUCTION_EXTERNAL_POWER_ASSEMBLY','fabricante':'Littelfuse','mpn_modelo':'0997002.WXN','sku':'','footprint_o_mecanica':'MINI blade','poblacion_pcba':'NO','alimentacion':'58VDC / 2A','interfaz':'MINI blade fuse','fuente':FUSE_URL,'nota':'Fusible 2A activo para rama HMI antes del RECOM.'},
]
with bp.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

# 6) Power architecture: 5V_RAIL queda limpio y el HMI se deriva antes del eFuse de PCBA
pa=loadj('hardware/power_architecture_contract.json')
pa['input']['recommended_external_supply']='12 V / 6 A certified external PSU (12 V / 5 A minimum analytical baseline only after system-current validation)'
pa['shield_5v']['loads']=[x for x in pa['shield_5v']['loads'] if x!='HMI']
pa['shield_5v']['hmi_integration']={'status':'CLOSED_EXTERNAL_DEDICATED_5V_HMI','main_pcba_5v_rail_feeds_hmi':False,'field_net':'5V_HMI','system_contract':'hardware/hmi_system_contract.json'}
pa['external_hmi_power']={'split_point':'system 12V harness upstream of NFB PCBA eFuse','branch_fuse':'Littelfuse 0997002.WXN 2A in 0FHM0001ZXJ','converter':'RECOM R-78K5.0-2.0L 5V/2A','output_net':'5V_HMI','main_pcba_high_current_path':False}
pa['power_budget']['hmi_power_gate']='CLOSED_EXTERNAL_DEDICATED_5V_HMI'
pa['power_budget']['external_hmi_w_design']=7.5
pa['power_budget']['external_hmi_input_w_screen_at_90pct']=round(7.5/0.90,3)
pa['power_budget']['system_total_w_screen_with_hmi']=round(float(pa['power_budget']['total_w_design'])+7.5/0.90,3)
pa['power_budget']['recommended_supply_w']=72.0
pa['power_budget']['note']='12V/6A (72W) recomendado para recuperar margen de sistema. Rama HMI se divide antes del eFuse de PCBA y lleva fusible 2A propio.'
savej('hardware/power_architecture_contract.json',pa)

# 7) Routing contract: nuevo net local 5V_HMI, sin alterar clases PR10 heredadas
rc=loadj('hardware/routing_contract.json')
rc['scope']['expected_production_net_count']=60
if not any(x['name']=='HMI_FIELD_POWER' for x in rc['routing_classes']):
    insert_at=next(i for i,x in enumerate(rc['routing_classes']) if x['name']=='PWR_3V3')
    rc['routing_classes'].insert(insert_at,{
      'name':'HMI_FIELD_POWER','nets':['5V_HMI'],'track_width_mm_min':0.40,'clearance_mm_min':0.25,'via_diameter_mm_min':0.80,'via_drill_mm_min':0.40,
      'preferred_layers':['In2.Cu','F.Cu'],'rules':['External dedicated 5 V enters at J_HMI.1 and only feeds TXU0202 VCCB/C_HMI_B on PCBA.','Never tie 5V_HMI to 5V_RAIL or J_UNOQ.5.','Display/audio high current stays in external HMI harness; PCBA branch is low-current only.']})
rc['cross_class_rules']['hmi_power_policy']='5V_HMI is isolated by net identity from 5V_RAIL; no copper bridge/net-tie permitted.'
savej('hardware/routing_contract.json',rc)

# 8) Routing batches: PR19D = único net ECO, PR20A se conserva 10 nets
rb=loadj('hardware/routing_batches_contract.json')
rb['total_production_nets']=60
if not any(x['id']=='PR19D' for x in rb['batches']):
    idx=next(i for i,x in enumerate(rb['batches']) if x['id']=='PR20A')
    rb['batches'].insert(idx,{'id':'PR19D','name':'hmi_dedicated_power_eco','expected_net_count':1,'nets':['5V_HMI'],'preferred_scope':'LOCAL_Z2_POWER_ECO','merge_gate':'5V_HMI_1_OF_1_CONNECTED_DRC0'})
rb['partition_checks']['expected_batch_counts']=[28,4,16,1,10,1]
rb['partition_checks']['expected_sum']=60
rb['eco_note']='PR19D introduced after HMI selection PR #32; historical PR19A/B/C manifests remain immutable and do not retroactively list 5V_HMI.'
savej('hardware/routing_batches_contract.json',rb)

# 9) ECO contract y mecánica del módulo externo
eco={
 'schema_version':1,'status':'HMI_POWER_ECO_PR19D','product':'NFB Insight PCBA v2','decision_date':'2026-08-14',
 'trigger':'NX8048P050-011C-Y + BOX Speaker reserve 5V/1.5A, equal to the entire historical 5V_RAIL continuous design limit.',
 'decision':'Move display/audio power off main PCBA. Use protected external 12V->5V/2A HMI branch and introduce local PCBA net 5V_HMI.',
 'external_components':{'converter':'R-78K5.0-2.0L','fuse_holder':'0FHM0001ZXJ','fuse':'0997002.WXN'},
 'pcba_change':{'new_net':'5V_HMI','endpoints':['J_HMI.1','U_HMI_LVL.7','C_HMI_B.1'],'removed_from_net':'5V_RAIL','placement_change':False,'outline_change':False,'existing_routing_removed':False,'uart_routing_change':False},
 'routing_batch':'PR19D','baseline_copper':{'segments':917,'vias':119,'zones':0},
 'gates':['5V_RAIL had zero copper before split','PR19D routes only 5V_HMI','In1.Cu remains signal-free','DRC errors=0','HMI_FIELD_RX/TX and HMI_RX/TX copper unchanged','placement and outline unchanged']
}
savej('hardware/hmi_power_eco.json',eco)

fp='''(footprint "RECOM_R78K5_0_2_0L_External"\n  (version 20240108)\n  (generator pcbnew)\n  (layer "F.Cu")\n  (descr "EXTERNAL MECHANICAL REFERENCE ONLY - RECOM R-78K5.0-2.0L horizontal low-profile HMI power module; body reference 17.5 x 11.5 mm; installed height 8.5 mm. Not on NFB main PCBA.")\n  (tags "RECOM R-78K5.0-2.0L external HMI power")\n  (attr exclude_from_pos_files exclude_from_bom)\n  (fp_rect (start -8.75 -5.75) (end 8.75 5.75) (stroke (width 0.25) (type default)) (fill none) (layer "F.Fab"))\n  (fp_rect (start -8.75 -5.75) (end 8.75 5.75) (stroke (width 0.20) (type dash)) (fill none) (layer "Dwgs.User"))\n  (fp_text reference "HMI_PWR_EXT" (at 0 -7) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))\n  (fp_text value "R-78K5.0-2.0L" (at 0 7) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))\n  (fp_text user "EXTERNAL 5V_HMI - NOT MAIN PCBA" (at 0 0) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))\n)\n'''
(ROOT/'kicad/lib/nfb_footprints.pretty/RECOM_R78K5_0_2_0L_External.kicad_mod').write_text(fp,encoding='utf-8')

# 10) Narrativa española y README
doc='''# ECO de potencia HMI — PR19D / 5V_HMI\n\n## Decisión\n\nLa Nextion `NX8048P050-011C-Y` y el `Nextion BOX Speaker` dejan de consumir desde `5V_RAIL` de la PCBA principal. El sistema adopta una rama externa dedicada, próxima a la HMI:\n\n`12V sistema → 0FHM0001ZXJ + 0997002.WXN (2 A) → RECOM R-78K5.0-2.0L → 5V_HMI`\n\n`5V_HMI` alimenta la pantalla y el speaker en el arnés externo. Ese mismo rail vuelve a `J_HMI.1` únicamente para `U_HMI_LVL.VCCB` y `C_HMI_B`; por ello la corriente de 1.5 A de display/audio **no atraviesa la NFB PCBA v2**.\n\n## Componentes congelados\n\n- RECOM `R-78K5.0-2.0L`: 5 V / 2 A / 10 W; Vin 6.5–36 V; no aislado; versión L horizontal de bajo perfil.\n- Littelfuse holder `0FHM0001ZXJ`: MINI inline, 58 V máx., 14 AWG, IP67.\n- Littelfuse fuse `0997002.WXN`: MINI 58 VDC / 2 A.\n\n## Impacto EDA\n\n- Nuevo net de producción: `5V_HMI` (59 → 60 nets).\n- Nuevo lote `PR19D`: 1/1 net local en Z2.\n- `J_HMI.1`, `U_HMI_LVL.7` y `C_HMI_B.1` migran de `5V_RAIL` a `5V_HMI`.\n- `5V_RAIL` no tenía cobre en PR19C, por lo que el ECO no retira routing previo.\n- HMI UART (`HMI_FIELD_RX/TX`, `HMI_RX/TX`) queda congelado.\n- Placement, outline e In1.Cu no cambian.\n\n## Potencia de sistema\n\nLa rama HMI reserva 7.5 W de salida. Como cribado conservador a 90 % de eficiencia equivale a ~8.33 W de entrada. Se recomienda 12 V / 6 A (72 W) para recuperar margen de sistema; la rama HMI queda protegida de forma independiente antes del convertidor.\n\n## Release gates\n\nEl ECO eléctrico se considera cerrado en diseño cuando PR19D sea DRC=0. El producto aún requiere first article: corriente/arranque, temperatura del RECOM dentro del enclosure, no nuisance-trip del fusible 2 A, mating del arnés XH y EMC del cable final.\n'''
(ROOT/'docs/HMI_POWER_ECO_PR19D.md').write_text(doc,encoding='utf-8')
readme=ROOT/'README.md'; text=readme.read_text(encoding='utf-8')
marker='## HMI power ECO — PR19D'
section='''\n\n## HMI power ECO — PR19D\n\nLa HMI Nextion `NX8048P050-011C-Y` + BOX Speaker usa alimentación externa dedicada `5V_HMI`: Littelfuse `0FHM0001ZXJ` + `0997002.WXN` 2 A → RECOM `R-78K5.0-2.0L` 5 V/2 A. La corriente de display/audio no atraviesa `5V_RAIL` de la PCBA. En la placa, `5V_HMI` solo alimenta `J_HMI.1`, `TXU0202 VCCB` y `C_HMI_B`. Nuevo lote de routing `PR19D` 1/1 antes de PR20A. Ver `docs/HMI_POWER_ECO_PR19D.md`.\n'''
if marker not in text: readme.write_text(text.rstrip()+section+'\n',encoding='utf-8')
print('OK: contratos/BOM/docs del ECO 5V_HMI materializados; PCB aún sin cambios')
