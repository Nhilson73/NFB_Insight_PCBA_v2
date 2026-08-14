#!/usr/bin/env python3
"""Gate del sistema Nextion después del ECO de alimentación PR19D."""
from __future__ import annotations
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'hardware'/'hmi_system_contract.json'; Z2=ROOT/'hardware'/'z2_digital_contract.json'; P=ROOT/'hardware'/'power_architecture_contract.json'; B=ROOT/'bom'/'insight_hmi_system_bom.csv'; ZB=ROOT/'bom'/'insight_z2_production_bom.csv'; FP=ROOT/'kicad'/'lib'/'nfb_footprints.pretty'; PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'
MECH={
'HMI_DISPLAY':('Nextion_NX8048P050_011C_Y_Enclosure.kicad_mod','NFB:Nextion_NX8048P050_011C_Y_Enclosure','160.04','107.07'),
'HMI_SD_EXT':('Nextion_SDExtender_External.kicad_mod','NFB:Nextion_SDExtender_External','17.1','41.48'),
'HMI_SPEAKER':('Nextion_BOX_Speaker_External.kicad_mod','NFB:Nextion_BOX_Speaker_External','31','28'),
'HMI_FOCA_MAX':('Nextion_Foca_Max_Service.kicad_mod','NFB:Nextion_Foca_Max_Service','50','50'),
'HMI_PWR_REG':('RECOM_R78K5_0_2_0L_External.kicad_mod','NFB:RECOM_R78K5_0_2_0L_External','17.5','11.5'),
}
def fail(m): raise SystemExit('ERROR: '+m)
def load(p):
    if not p.exists(): fail(f'falta {p.relative_to(ROOT)}')
    return json.loads(p.read_text(encoding='utf-8'))
def main():
    c=load(C); z=load(Z2); p=load(P)
    if c.get('status')!='HMI_SYSTEM_DECISION_NEXTION_NX8048P050_011C_Y': fail('status HMI incorrecto')
    d=c['selected_display']
    if (d['mpn'],d['sku'],d['resolution_px'],d['touch'],d['enclosure'])!=('NX8048P050-011C-Y','6920075776553',[800,480],'CAPACITIVE',True): fail('display exacto no congelado')
    if d['input_power']!={'voltage_v':5.0,'current_a_recommended':1.0}: fail('potencia display cambió')
    a={x['id']:x for x in c['selected_accessories']}
    if set(a)!={'HMI_SD_EXT','HMI_SPEAKER','HMI_FOCA_MAX'} or a['HMI_SD_EXT']['model']!='SDExtender' or float(a['HMI_SPEAKER']['power_increment_a'])!=0.5: fail('accesorios HMI incompletos')
    if a['HMI_FOCA_MAX']['classification']!='SERVICE_PROGRAMMING_TOOL_NOT_INSTALLED': fail('Foca Max no es service tool')
    i=c['pcba_interface']
    if i['board_connector_mpn']!='S4B-XH-A(LF)(SN)' or i['board_connector_footprint']!='Connector_JST:JST_XH_S4B-XH-A_1x04_P2.50mm_Horizontal': fail('J_HMI board-side cambió')
    if i['pinout_board']['1']!='5V_HMI' or i['signal_mapping']['power']!='5V_HMI': fail('J_HMI no usa 5V_HMI')
    if i.get('routing_frozen') is not True or i.get('routing_checkpoint')!='PR19D_5V_HMI': fail('routing HMI no congelado en PR19D')
    da=c.get('dedicated_power_assembly',{})
    if da.get('status')!='SELECTED_POWER_ECO_CLOSED': fail('subensamble de potencia HMI no cerrado')
    conv=da.get('converter',{})
    if conv.get('mpn')!='R-78K5.0-2.0L' or conv.get('vin_v')!=[6.5,36.0] or float(conv.get('vout_v',0))!=5.0 or float(conv.get('iout_a',0))!=2.0: fail('RECOM exacto no congelado')
    if da.get('fuse_holder',{}).get('mpn')!='0FHM0001ZXJ' or da.get('fuse',{}).get('mpn')!='0997002.WXN' or float(da['fuse']['rating_a'])!=2.0: fail('protección rama HMI incorrecta')
    if c['power_integration']['status']!='POWER_ECO_CLOSED_EXTERNAL_5V_HMI': fail('power ECO HMI no cerrado')
    hz=z['hmi_uart']
    if hz['connector']['pinout']['1']!='5V_HMI' or hz['translator']['vccb_net']!='5V_HMI' or hz['translator']['pinout']['7']!='5V_HMI': fail('Z2 HMI no migró a 5V_HMI')
    if hz.get('power_eco',{}).get('status')!='CLOSED_PR19D': fail('Z2 no registra PR19D')
    if p['shield_5v'].get('hmi_integration',{}).get('status')!='CLOSED_EXTERNAL_DEDICATED_5V_HMI' or 'HMI' in p['shield_5v']['loads']: fail('5V_RAIL aún reclama HMI')
    if p['power_budget'].get('hmi_power_gate')!='CLOSED_EXTERNAL_DEDICATED_5V_HMI': fail('power budget HMI abierto')
    with B.open(newline='',encoding='utf-8') as f: items={r['item_id']:r for r in csv.DictReader(f)}
    required={'HMI_DISPLAY':'NX8048P050-011C-Y','HMI_SD_EXT':'SDExtender','HMI_SPEAKER':'Nextion BOX Speaker','HMI_FOCA_MAX':'Foca Max','HMI_PWR_REG':'R-78K5.0-2.0L','HMI_PWR_FUSE_HOLDER':'0FHM0001ZXJ','HMI_PWR_FUSE':'0997002.WXN','J_HMI':'S4B-XH-A(LF)(SN)'}
    for k,v in required.items():
        if items.get(k,{}).get('mpn_modelo')!=v: fail(f'BOM HMI sin {k}/{v}')
    for item,(fn,expect,da_,db_) in MECH.items():
        if items[item]['footprint_o_mecanica']!=expect: fail(f'{item} no enlaza {expect}')
        text=(FP/fn).read_text(encoding='utf-8')
        if '(pad ' in text or da_ not in text or db_ not in text: fail(f'huella mecánica {item} inválida')
    with ZB.open(newline='',encoding='utf-8') as f: zr={r['ref']:r for r in csv.DictReader(f)}
    if '5V_HMI' not in zr['J_HMI']['nota'] or '5V_HMI' not in zr['U_HMI_LVL']['nota'] or '5V_HMI' not in zr['C_HMI_B']['nota']: fail('BOM Z2 no traza 5V_HMI')
    if PCB.stat().st_size<100000: fail('PCB no reconocible')
    print('OK HMI: Nextion + accesorios + RECOM/fuse exactos; power ECO CLOSED en PR19D')
if __name__=='__main__': main()
