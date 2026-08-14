#!/usr/bin/env python3
"""Gate de la decisión HMI Nextion y su integración con Z2/potencia."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'hardware'/'hmi_system_contract.json'
Z2=ROOT/'hardware'/'z2_digital_contract.json'
POWER=ROOT/'hardware'/'power_architecture_contract.json'
BOM=ROOT/'bom'/'insight_hmi_system_bom.csv'
Z2BOM=ROOT/'bom'/'insight_z2_production_bom.csv'
FP_DIR=ROOT/'kicad'/'lib'/'nfb_footprints.pretty'
FOOTPRINTS={
    'HMI_DISPLAY':('Nextion_NX8048P050_011C_Y_Enclosure.kicad_mod','NFB:Nextion_NX8048P050_011C_Y_Enclosure','160.04','107.07'),
    'HMI_SD_EXT':('Nextion_SDExtender_External.kicad_mod','NFB:Nextion_SDExtender_External','17.1','41.48'),
    'HMI_SPEAKER':('Nextion_BOX_Speaker_External.kicad_mod','NFB:Nextion_BOX_Speaker_External','31','28'),
    'HMI_FOCA_MAX':('Nextion_Foca_Max_Service.kicad_mod','NFB:Nextion_Foca_Max_Service','50','50'),
}
DOC=ROOT/'docs'/'HMI_NEXTION_NX8048P050.md'
PCB=ROOT/'kicad'/'NFB_Insight_PCBA_v2.kicad_pcb'


def fail(msg): raise SystemExit('ERROR: '+msg)
def load(p):
    if not p.exists(): fail(f'falta {p.relative_to(ROOT)}')
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    for p in (CONTRACT,Z2,POWER,BOM,Z2BOM,DOC,PCB):
        if not p.exists(): fail(f'falta {p.relative_to(ROOT)}')
    for filename,_,_,_ in FOOTPRINTS.values():
        p=FP_DIR/filename
        if not p.exists(): fail(f'falta {p.relative_to(ROOT)}')

    c=load(CONTRACT); z2=load(Z2); power=load(POWER)
    if c.get('status')!='HMI_SYSTEM_DECISION_NEXTION_NX8048P050_011C_Y': fail('status HMI incorrecto')
    d=c['selected_display']
    if d['mpn']!='NX8048P050-011C-Y' or d['sku']!='6920075776553': fail('display exacto no congelado')
    if d['touch']!='CAPACITIVE' or not d['enclosure'] or d['resolution_px']!=[800,480]: fail('variante HMI incorrecta')
    if d['input_power']!={'voltage_v':5.0,'current_a_recommended':1.0}: fail('potencia display inesperada')
    if d['usart_connector_vendor_description']!='XH2.54 4P': fail('interfaz serial Nextion no congelada')
    mech=d['mechanical']
    if mech['front_envelope_mm']!=[160.04,107.07] or float(mech['max_depth_mm'])!=21.2: fail('envelope mecánico HMI incorrecto')

    a={x['id']:x for x in c['selected_accessories']}
    if set(a)!={'HMI_SD_EXT','HMI_SPEAKER','HMI_FOCA_MAX'}: fail('set de accesorios HMI incompleto')
    if a['HMI_SD_EXT']['model']!='SDExtender': fail('SDExtender no exacto')
    if float(a['HMI_SPEAKER']['power_increment_a'])!=0.5: fail('incremento de corriente speaker no congelado')
    if a['HMI_FOCA_MAX']['model']!='Foca Max' or a['HMI_FOCA_MAX']['classification']!='SERVICE_PROGRAMMING_TOOL_NOT_INSTALLED': fail('Foca Max mal clasificado')

    iface=c['pcba_interface']
    if iface['board_connector_mpn']!='S4B-XH-A(LF)(SN)': fail('J_HMI board-side cambió')
    if iface['board_connector_footprint']!='Connector_JST:JST_XH_S4B-XH-A_1x04_P2.50mm_Horizontal': fail('footprint J_HMI cambió')
    if iface['footprint_change_on_pcba'] is not False or iface['routing_frozen'] is not True: fail('PR19C no está protegido')

    h=z2['hmi_uart']
    if h.get('system_contract')!='hardware/hmi_system_contract.json': fail('Z2 no enlaza contrato HMI')
    if h.get('selected_display_mpn')!='NX8048P050-011C-Y': fail('Z2 no congela display')
    if h['connector']['mpn']!='S4B-XH-A(LF)(SN)' or h['connector']['footprint']!=iface['board_connector_footprint']: fail('Z2/J_HMI divergente')
    if h['translator']['mpn']!='TXU0202DCUR': fail('traductor UART HMI cambió')

    pin=c['power_integration']; p5=power['shield_5v']
    if float(pin['reserved_hmi_current_a_with_audio'])!=1.5: fail('reserva HMI+audio debe ser 1.5 A')
    if float(p5['regulator']['design_continuous_limit_a'])!=1.5: fail('baseline 5V cambió sin ECO explícito')
    if p5.get('hmi_integration',{}).get('status')!='POWER_ECO_REQUIRED_BEFORE_PRODUCT_RELEASE': fail('power gate HMI no registrado')
    if power['power_budget'].get('hmi_power_gate')!='OPEN_POWER_ECO_REQUIRED': fail('power budget no refleja gate abierto')

    with BOM.open(newline='',encoding='utf-8') as fh: rows=list(csv.DictReader(fh))
    items={r['item_id']:r for r in rows}
    if set(items)!={'HMI_DISPLAY','HMI_SD_EXT','HMI_SPEAKER','HMI_FOCA_MAX','J_HMI'}: fail('BOM sistema HMI no es exacto')
    if items['HMI_DISPLAY']['mpn_modelo']!='NX8048P050-011C-Y': fail('BOM no contiene display exacto')
    for item_id,(_,expected_fp,dim_a,dim_b) in FOOTPRINTS.items():
        if items[item_id]['footprint_o_mecanica']!=expected_fp: fail(f'{item_id}: BOM no enlaza {expected_fp}')
        text=(FP_DIR/FOOTPRINTS[item_id][0]).read_text(encoding='utf-8')
        if '(pad ' in text: fail(f'{item_id}: huella externa no debe tener pads de PCBA')
        if dim_a not in text or dim_b not in text: fail(f'{item_id}: huella no documenta envelope esperado')
    if items['HMI_FOCA_MAX']['rol_producto']!='SERVICE_PROGRAMMING_TOOL_NOT_INSTALLED': fail('Foca Max no debe poblar producto')

    with Z2BOM.open(newline='',encoding='utf-8') as fh: zrows=list(csv.DictReader(fh))
    j=next((r for r in zrows if r['ref']=='J_HMI'),None)
    if not j or j['mpn_o_familia']!='S4B-XH-A(LF)(SN)' or 'NX8048P050-011C-Y' not in j['nota']: fail('BOM Z2 no traza J_HMI al sistema seleccionado')

    if PCB.stat().st_size < 100000: fail('PCB production checkpoint demasiado pequeño/no reconocible')

    print('OK HMI: NX8048P050-011C-Y + SDExtender + BOX Speaker + Foca Max trazados')
    print('- 4 huellas mecánicas externas cargables; J_HMI PCBA preservado post-PR19C')
    print('- potencia: 5 V/1.5 A reservados para HMI+audio; POWER ECO sigue ABIERTO antes de PR20A/release')
    return 0

if __name__=='__main__': raise SystemExit(main())
