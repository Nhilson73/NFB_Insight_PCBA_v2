#!/usr/bin/env python3
"""Actualiza narrativas vigentes para PR19D preservando checkpoints históricos."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def replace_once(path,old,new):
    p=ROOT/path; s=p.read_text(encoding='utf-8')
    if old not in s: raise SystemExit(f'ERROR: patrón ausente en {path}: {old[:80]}')
    s=s.replace(old,new,1); p.write_text(s,encoding='utf-8')

def append_once(path,marker,text):
    p=ROOT/path; s=p.read_text(encoding='utf-8')
    if marker not in s: p.write_text(s.rstrip()+"\n\n"+text.strip()+"\n",encoding='utf-8')

# README: estado vigente, sin alterar métricas históricas de PR18/PR19A/B/C.
replace_once('README.md','- 59 nets materializadas.','- 60 nets materializadas desde PR19D; `5V_HMI` es la net ECO añadida después de PR19C.')
replace_once('README.md','- HMI+speaker reserva **5 V / 1.5 A**; existe un gate de potencia abierto antes de PR20A/release porque `5V_RAIL` tiene otras cargas. Ver `hardware/hmi_system_contract.json`.','- HMI+speaker reserva **5 V / 1.5 A**. PR19D cerró el ECO con `5V_HMI` dedicado externo (RECOM `R-78K5.0-2.0L` + fusible 2 A); display/audio ya no cargan `5V_RAIL`.')
old='''Las 59 nets quedan divididas exhaustivamente y sin solapes:\n\n- **PR19A: 28** nets locales.\n- **PR19B: 4** nets analógicas inter-zona: `PH_ADC`, `ORP_ADC`, `DO_ADC`, `PUMP_CURRENT_ADC`.\n- **PR19C: 16** nets digital/control inter-zona.\n- **PR20A: 10** nets de potencia + salidas de actuadores.\n- **PR20B: 1** net GND, tratada como plano `In1.Cu` + stitching; el probe experimental identificó 83 endpoints.\n\nTotal: **28 + 4 + 16 + 10 + 1 = 59**.'''
new='''Las **60 nets vigentes** quedan divididas exhaustivamente y sin solapes. Los lotes PR19A/B/C conservan sus manifests históricos; PR19D introduce únicamente la net creada por el ECO HMI:\n\n- **PR19A: 28** nets locales.\n- **PR19B: 4** nets analógicas inter-zona: `PH_ADC`, `ORP_ADC`, `DO_ADC`, `PUMP_CURRENT_ADC`.\n- **PR19C: 16** nets digital/control inter-zona.\n- **PR19D: 1** net ECO local de potencia HMI: `5V_HMI`.\n- **PR20A: 10** nets de potencia + salidas de actuadores.\n- **PR20B: 1** net GND, tratada como plano `In1.Cu` + stitching; el probe experimental identificó 83 endpoints.\n\nTotal vigente: **28 + 4 + 16 + 1 + 10 + 1 = 60**.'''
replace_once('README.md',old,new)
oldstate='''Placement y ECOs PR22/PR24 están congelados. PR18 congeló las reglas de routing. PR25 consolidó tooling KiCad. **PR28 cerró PR19A (28/28), PR30 cerró PR19B (4/4) y PR31 cerró PR19C (16/16). El PCB de producción queda en 48/59 nets ruteadas, 917 segmentos, 119 vías y DRC físico 0 errores.**'''
newstate='''Placement y ECOs PR22/PR24 están congelados. PR18 congeló las reglas de routing y PR25 consolidó tooling KiCad. **PR28 cerró PR19A (28/28), PR30 cerró PR19B (4/4), PR31 cerró PR19C (16/16) y PR19D cerró el ECO HMI `5V_HMI` 1/1. El PCB vigente queda en 49/60 nets ruteadas, 924 segmentos, 121 vías, 0 zones, DRC físico 0 errores y 151 unconnected. PR20A conserva sus 10 nets históricas y queda como siguiente lote de cobre.**'''
replace_once('README.md',oldstate,newstate)

# Routing KB: autoridad/partición vigente y nuevo checkpoint, sin reescribir PR19C.
replace_once('docs/ROUTING_KNOWLEDGE_BASE.md','2. `hardware/routing_batches_contract.json` — partición de las 59 nets en lotes de cierre incremental.','2. `hardware/routing_batches_contract.json` — partición vigente de 60 nets; PR19D añadió `5V_HMI` después de PR19C sin reescribir manifests históricos.')
replace_once('docs/ROUTING_KNOWLEDGE_BASE.md','## Partición de las 59 nets','## Partición vigente de las 60 nets')
marker='### PR19D — 1 net ECO de potencia HMI'
insert='''### PR19D — 1 net ECO de potencia HMI\n\n- `5V_HMI`\n\nPR19D fue insertado después de PR19C para cerrar el ECO abierto por la selección de Nextion + BOX Speaker. `5V_HMI` nace en un subensamble externo 5 V / 2 A y entra a Z2 por `J_HMI.1`; en la PCBA solo alimenta `U_HMI_LVL.7` y `C_HMI_B.1`. No existe net-tie ni puente a `5V_RAIL`.\n\nRouting cerrado: 7 segmentos + 2 vías; acumulado 924/121; DRC=0; `In1.Cu` sin señales; zones=0. El escape de `U_HMI_LVL.7` usa neck-down 0.20 mm por ≤1.20 mm únicamente para liberar el VSSOP, conservando clearance ≥0.20 mm y retornando a 0.40 mm.\n\n**Gate PR19D:** `5V_HMI` 1/1 conectada, UART HMI previa intacta, placement/outline congelados, ninguna net PR20A/PR20B adelantada.\n\n'''
p=ROOT/'docs/ROUTING_KNOWLEDGE_BASE.md'; s=p.read_text(encoding='utf-8')
if marker not in s:
    anchor='### PR20A — 10 nets de potencia + actuadores'
    if anchor not in s: raise SystemExit('ERROR: falta anchor PR20A en KB')
    s=s.replace(anchor,insert+anchor,1); p.write_text(s,encoding='utf-8')

# Power architecture: addendum deliberadamente posterior a PR9/PR10.
append_once('docs/POWER_ARCHITECTURE.md','## 12. Addendum PR19D — alimentación HMI dedicada','''## 12. Addendum PR19D — alimentación HMI dedicada\n\nPR9/PR10 permanece como baseline histórico de la **PCBA principal**. La selección posterior de `NX8048P050-011C-Y` + BOX Speaker reveló que reservar 1.5 A sobre `5V_RAIL` consumiría todo el límite continuo de diseño de ese rail. PR19D resuelve el conflicto fuera de Z3, sin mover el TPSM33625 ni sus pasivos:\n\n```text\n12 V sistema — split externo upstream del eFuse NFB\n  → Littelfuse 0FHM0001ZXJ\n  → Littelfuse 0997002.WXN / 2 A\n  → RECOM R-78K5.0-2.0L / 5 V, 2 A\n  → 5V_HMI\n```\n\nLa corriente de display/audio permanece en el arnés externo. `5V_HMI` entra a la PCBA únicamente por `J_HMI.1` para `TXU0202 VCCB` y `C_HMI_B`; `5V_RAIL` deja de alimentar la HMI. Ambos rails comparten GND de sistema porque el RECOM seleccionado es no aislado, pero **no pueden unirse entre sí**.\n\nEl presupuesto de salida HMI es 7.5 W. Como screening conservador a 90 % de eficiencia equivale a ~8.33 W de entrada; por margen de sistema se recomienda fuente certificada **12 V / 6 A (72 W)**. La rama HMI lleva protección 2 A propia.\n\nEste addendum no altera el eFuse, buck 5 V, LDO 3.3 V, split estrella ni placement de la PCBA principal. El first article debe validar arranque/corriente, temperatura del convertidor, ausencia de nuisance-trip, mating y EMC. Fuente de verdad: `hardware/hmi_power_eco.json`.''')
print('OK: narrativas PR19D actualizadas preservando checkpoints históricos')
