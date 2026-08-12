#!/usr/bin/env python3
"""Valida que el readiness PR16 permanezca intacto y que PR17 sea su única transición a XY."""
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/'hardware/placement_readiness_contract.json'; PCB=ROOT/'kicad/NFB_Insight_PCBA_v2.kicad_pcb'; ROOTEDA=ROOT/'hardware/root_eda_contract.json'; AUDIT=ROOT/'hardware/footprint_audit.json'; PLACEMENT=ROOT/'hardware/placement_manifest.json'
FILES={'Z1':ROOT/'hardware/z1_production_netlist.json','Z2':ROOT/'hardware/z2_production_netlist.json','Z3':ROOT/'hardware/power_production_netlist.json','Z4':ROOT/'hardware/z4_production_netlist.json'}
ARDUINO_COMMIT='24445a32e249d410c1e4359bdc99d8c0dcb17bd2'
def fail(m): raise SystemExit('ERROR: '+m)
def close(a,b,t=1e-6): return abs(float(a)-float(b))<=t
def main():
    for p in (C,PCB,ROOTEDA,AUDIT,*FILES.values()):
        if not p.exists(): fail(f'falta {p.relative_to(ROOT)}')
    c=json.loads(C.read_text(encoding='utf-8'))
    if c.get('schema_version')!=1 or c.get('status')!='PREPLACEMENT_READINESS_PR16': fail('contrato readiness no es PR16')
    if c.get('placement_allowed_after_pr16') is not True or c.get('routing_allowed_after_pr16') is not False: fail('scope placement/routing incorrecto')
    src=c['arduino_uno_q_primary_snapshot']
    if src.get('repository')!='arduino/docs-content' or src.get('commit')!=ARDUINO_COMMIT: fail('snapshot Arduino no coincide con revisión PR16')
    req={'content/hardware/02.uno/boards/uno-q/product.md','content/hardware/02.uno/boards/uno-q/datasheet/datasheet.md','content/hardware/02.uno/boards/uno-q/tech-specs.yml'}
    if set(src.get('files',[]))!=req: fail('snapshot Arduino incompleto')
    facts=src.get('verified_facts',{})
    if facts.get('wireless_module')!='WCBN3536A / Qualcomm WCN3980' or facts.get('antenna')!='shared PCB antenna': fail('RF host fact cambió')
    if not {'CE/RED','RoHS','REACH','WEEE'}<=set(facts.get('host_certifications_include',[])): fail('evidencia compliance host incompleta')
    rf=c['rf_policy']
    if rf.get('primary_source_numeric_antenna_keepout_found') is not False or rf.get('numeric_antenna_keepout_mm') is not None or rf.get('policy')!='DO_NOT_INVENT_NUMERIC_RF_KEEPOUT': fail('se inventó/alteró keepout RF numérico')
    env=rf['host_envelope_mm']
    if [env[k] for k in ('x_min','x_max','y_min','y_max')]!=[0.0,53.34,0.0,68.58]: fail('envelope UNO Q cambió')
    if not close(rf['derived_separation_from_host_xmax_to_z3_mm'],145.0-53.34) or not close(rf['derived_separation_from_host_xmax_to_z4_mm'],180.0-53.34): fail('snapshot separación quiet→dirty PR16 cambió')
    mech=c['mechanical']
    if not close(mech['board_height_mm'],68.58) or not close(mech['board_width_mm_current'],220.0) or mech['growth_direction']!='+X' or mech['field_io_direction']!='-Y': fail('snapshot mecánica PR16 cambió')
    holes=[[50.80,13.97],[45.72,66.04],[17.78,66.04],[2.54,15.24]]
    if mech['uno_q_holes_mm']!=holes: fail('agujeros UNO Q cambiaron')
    zones=c['zone_guides']
    if zones['order_fixed']!=['Z0','Z1','Z2','Z3','Z4']: fail('orden de zonas cambió')
    if zones['Z0']['x_max']!=53.34 or zones['Z3']['x_min']!=145.0 or zones['Z4']['x_min']!=180.0: fail('guías históricas quiet/dirty PR16 cambiaron')
    li=c['layer_intent']
    if li.get('layers')!=4 or li.get('In1.Cu')!='CONTINUOUS_GND_REFERENCE_NO_SIGNAL_ROUTING': fail('stack intent no congela L2 GND')
    seq=c['field_io_sequence_left_to_right']
    if [x['order'] for x in seq]!=list(range(1,13)): fail('orden FIELD I/O no es 1..12')
    refs=[x['ref'] for x in seq]; expected=['J_PH','J_ORP','J_TEMP','U_CO2','J_DO','J_LOADCELL','J_GNSS_RTC','J_HMI','J_PWR_IN','J_PUMP','J_CO2_SOL','J_CHILLER_CTL']
    if refs!=expected: fail(f'secuencia FIELD I/O cambió: {refs}')
    if [x['zone'] for x in seq]!=['Z1']*5+['Z2']*3+['Z3']+['Z4']*3: fail('secuencia de zonas FIELD I/O incorrecta')
    for x in seq:
        if x['ref']=='U_CO2':
            if x['orientation']!='VERTICAL_PORT_NEAR_FIELD_EDGE': fail('MPR debe conservar puerto vertical')
        elif x['orientation']!='-Y': fail(f"{x['ref']} no mira a -Y")
    data={z:json.loads(p.read_text(encoding='utf-8')) for z,p in FILES.items()}; comps={}
    for zone,d in data.items():
        for comp in d['components']:
            if comp['ref'] in comps: fail(f"ref duplicada entre zonas: {comp['ref']}")
            comps[comp['ref']]=(zone,comp)
    fp_contract=c['field_io_footprints']
    if set(fp_contract)!=set(expected): fail('footprint contract FIELD I/O incompleto')
    for ref in expected:
        if ref not in comps: fail(f'{ref} no existe en netlists')
        zone,comp=comps[ref]
        if comp.get('footprint')!=fp_contract[ref]: fail(f"{ref}: footprint {comp.get('footprint')} != readiness")
    z2=comps['J_LOADCELL'][1]
    if z2.get('mpn')!='1757268' or z2.get('footprint')!='Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_4-G-5,08_1x04_P5.08mm_Horizontal': fail('J_LOADCELL no está cerrado a Phoenix 1757268')
    root=json.loads(ROOTEDA.read_text(encoding='utf-8'))
    if root.get('schema_version')!=3 or root.get('status')!='ROOT_EDA_PRODUCTION_MATERIALIZED_PR15': fail('root EDA no está cerrado PR15')
    erc=root.get('erc_policy',{})
    if erc.get('expected_errors')!=0 or erc.get('expected_warnings')!=0: fail('root EDA perdió gate ERC cero')
    audit=json.loads(AUDIT.read_text(encoding='utf-8'))
    if audit.get('status')!='FOOTPRINT_AUDIT_CLOSED_PR13': fail('footprints críticos PR13 no cerrados')
    if c.get('preplacement_blockers')!=[]: fail(f"blockers abiertos: {c.get('preplacement_blockers')}")
    pcb=PCB.read_text(encoding='utf-8'); footprint_refs=re.findall(r'\(property "Reference" "([^"]+)"',pcb)
    if footprint_refs!=['J_UNOQ']:
        if not PLACEMENT.exists(): fail(f'producción colocada sin manifest PR17: {footprint_refs[:5]}')
        pm=json.loads(PLACEMENT.read_text(encoding='utf-8'))
        if pm.get('status')!='PRODUCTION_PLACEMENT_PR17' or pm.get('policies',{}).get('routing_allowed') is not False: fail('transición PR16→PR17 inválida')
        pmap={x['ref']:x for x in pm.get('placements',[])}; expected_prod=set(comps)
        if set(footprint_refs)!={'J_UNOQ'}|expected_prod: fail('refs PCB no coinciden con producción autorizada PR17')
        if set(pmap)!=expected_prod: fail('manifest PR17 no contiene exactamente refs Z1-Z4')
        zb=pm.get('zone_bounds_mm',{})
        if float(zb['Z0']['x_min'])!=0.0 or float(zb['Z0']['x_max'])!=53.34 or pm['board']['growth_only']!='+X' or float(pm['board']['height_mm'])!=68.58: fail('PR17 viola mecánica congelada PR16')
    if re.search(r'^\s*\((segment|via|arc|zone)\b',pcb,re.M): fail('routing/cobre no permitido antes de PR18')
    # KiCad 10 renumera IDs internos de capas al serializar; validar semántica, no ID literal.
    if not re.search(r'\(\d+\s+"In1\.Cu"\s+power\)',pcb) or not re.search(r'\(\d+\s+"In2\.Cu"\s+power\)',pcb): fail('PCB no conserva In1/In2 como capas internas power/reference')
    for marker in ('Z0 UNO Q','Z1','Z2','Z3','Z4','FIELD I/O EDGE'):
        if marker not in pcb: fail(f'PCB perdió guía {marker}')
    rules=c['placement_rules']; required_true=['connectors_field_edge_first_row','esd_and_input_protection_immediately_behind_field_connectors','analog_conditioning_stays_in_Z1','loadcell_hx711_cluster_stays_on_Z1_SIDE_OF_Z2','hmi_stays_on_Z3_SIDE_OF_Z2','power_entry_tvs_efuse_cluster_stays_in_Z3','buck_switching_loop_stays_in_Z3','actuator_drivers_and_local_bulk_stay_in_Z4','actuator_connectors_stay_at_field_edge','pump_current_adc_keep_away_from_switch_nodes','high_current_returns_must_not_cross_Z1_Z2']
    if any(rules.get(k) is not True for k in required_true): fail('alguna regla EMC/placement fue debilitada')
    if rules.get('exact_xy_coordinates_frozen_in_pr16') is not False or rules.get('production_footprints_inside_Z0')!='FORBIDDEN': fail('snapshot PR16 adelantó XY o habilitó Z0')
    if 'NO MAINS' not in rules.get('chiller_contact_clearance_policy',''): fail('frontera chiller perdió NO MAINS')
    count=max(0,len(footprint_refs)-1)
    print('OK: PR16 pre-placement readiness preservado y transición PR17 autorizada')
    print('- Arduino snapshot/RF/keepouts/orden FIELD I/O PR16 intactos')
    print(f'- placement producción={count}; Z0 protegido; routing/cobre=0; In1/In2=power/reference')
    return 0
if __name__=='__main__': raise SystemExit(main())
