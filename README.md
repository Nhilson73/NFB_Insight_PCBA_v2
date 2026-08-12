# NFB Insight PCBA v2

PCBA **shield/carrier** para **Nebula Fermentation Insight®**, diseñada alrededor del factor de forma inmutable del **Arduino UNO Q**. El repositorio `Nhilson73/nebula_qshield_pcb` se conserva únicamente como donante de ingeniería y trazabilidad; no gobierna placement, routing ni topología de producción V2.

## Fuente primaria UNO Q

Toda decisión dependiente del **Arduino UNO Q** se contrasta primero contra los repositorios oficiales de Arduino en GitHub:

- `https://github.com/Arduino`
- `https://github.com/orgs/arduino/repositories`
- especialmente `arduino/docs-content` y repos oficiales UNO Q aplicables.

Después se contrastan `docs.arduino.cc` y datasheets/PDF oficiales. La jerarquía está en `docs/SOURCE_OF_TRUTH.md` y es obligatoria para pinout, potencia, mecánica, firmware, RF e interfaces.

## Frontera del producto / compliance

NFB Insight PCBA v2 es un **shield/carrier del Arduino UNO Q**, no un rediseño de su plataforma radio.

- UNO Q aporta computación, MCU y Wi‑Fi/Bluetooth.
- El shield base no añade transmisores, antenas, matching ni amplificación RF.
- Se preservarán keepouts y condiciones RF del UNO Q.
- El **EU Compliance Design Gate** vive en `docs/EU_COMPLIANCE_GATE.md` y `compliance/eu_compliance_contract.json`.
- La evidencia regulatoria del host no sustituye la calificación EMC/RoHS3/REACH/WEEE/CE del shield y del producto integrado.

## Mecánica congelada

- UNO Q rotado, origen global `(0,0)`, USB‑C hacia `-Y`.
- Envolvente UNO Q: `53.34 × 68.58 mm`.
- Altura PCB fija: `68.58 mm`; crecimiento solo `+X`.
- `Y=0` = FIELD I/O EDGE.
- Gradiente: Z0 UNO Q → Z1 sensores → Z2 digital → Z3 potencia → Z4 actuadores.
- Ancho actual `220 mm` **provisional** hasta placement.

## Z1 sensores — PR #6 / #9 / #11 / #12

Fuentes: `hardware/sensor_interface_contract.json`, `hardware/z1_production_netlist.json`, `bom/insight_z1_production_bom.csv`.

- pH/A0 y DO/A5: 0–3 V acondicionados, ESD + `1 kΩ / 100 nF`.
- ORP/A1: divisor `10 kΩ / 20 kΩ`, máximo 3.0 V.
- TEMP/A2-D16: DS18B20 `TEMP_1WIRE`, pull-up 4.7 kΩ.
- CO₂ pressure: Honeywell `MPRLS0030PA00002A`, I²C `0x28`; **CO2_ADC permanece retirado**.
- PR #11 cerró el footprint MPR contra Honeywell `32332628 Issue L / Fig.10`.
- PR #12 reutiliza A4/pad13 como `PUMP_CURRENT_ADC` desde IPROPI del driver de bomba.
- Desde PR #14 el contrato textual Z1 vive en `kicad/z1_sensor_contract.kicad_sch`; el root ya no se usa como hoja Z1.

## Z2 digital / bajo ruido — PR #7 / #9

- I²C 3.3 V con pull-ups 4.7 kΩ; MPR `0x28` + DFR1103 `0x66`.
- HX711 3.3 V, 10 SPS, D2/D3.
- HMI D0/D1 mediante `TXU0202DCUR`.
- Watchdog `TPS3823-30DBVR`, WDI=D4.
- GPS/RTC legacy separados y RS485 Signature quedan fuera del baseline Insight.

## Z3 potencia — PR #9 / #10 / #13

Fuentes: `hardware/power_architecture_contract.json`, `hardware/power_production_netlist.json`, `bom/insight_power_production_bom.csv`, `hardware/power_netclasses.json`, `kicad/power.kicad_sch`.

- Entrada nominal **12 VDC**; fuente recomendada **12 V / 5 A / 60 W** certificada.
- NFB alimenta UNO Q por **12 V protegido → VIN**.
- `5V_RAIL` y `3V3_RAIL` son rails locales del shield y no se unen a J_UNOQ.5/J_UNOQ.4.
- Protección: `SMBJ15A-TR` + `TPS259470ARPWR`.
- eFuse: ladder UV/OV `470 kΩ / 11 kΩ / 47 kΩ`, `R_ILIM=750 Ω`, `C_DVDT=3.3 nF`, `C_ITIMER=2.2 nF`.
- Split: `12V_HOST_VIN`, `12V_LOGIC`, `12V_ACT`; `F_ACT=045401.5MR` 1.5 A Slo-Blo.
- 5 V: `TPSM33625RDNR`, 1 MHz, feedback `40.2 kΩ / 10 kΩ`.
- 3.3 V: `TLV75533PDBVR`.
- Chiller no toma potencia de la PCBA.

## Cierre de footprints críticos — PR #13

Fuente: `hardware/footprint_audit.json`; detalle: `docs/FASE3_PR13_FOOTPRINT_CLOSURE.md`.

- `U_EFUSE` → `NFB:TI_RPW0010A_TPS259470A` — TI `MPQF568 / 4225183/A`.
- `U_5V` → `NFB:TI_RDN0011A_TPSM33625` — TI `qfnd871 / 4226623/F`.
- `U_PUMP_DRV` → `NFB:TI_RHL0020B_DRV8242` — TI `RHL0020B / 4226154/B`, thermal pad 21.
- `U_CO2_DRV` → `NFB:TI_DYC0008A_TPS1HC120` — TI `DYC0008A / 4226548/B`, 8 pads y sin PowerPAD.
- `U_CHILLER` → `NFB:Panasonic_AQY212EHAX_DIP4_SMD` — Panasonic MPN exacto `AQY212EHAX`.

Gemini Spark fue auditor independiente/cross-check, no fuente de verdad. La revisión NFB contra TI/Panasonic corrigió geometrías simplificadas del RPW/RDN, la revisión de package del DRV8242 y un PowerPAD inexistente reportado para DYC-8.

## Z4 actuadores — PR #12 / footprints PR #13

Fuentes: `hardware/z4_actuator_contract.json`, `hardware/z4_production_netlist.json`, `bom/insight_z4_production_bom.csv`, `kicad/z4_actuators.kicad_sch`.

- Bomba: `DRV8242HQRHLRQ1`, D5/D6 PH/EN, `IPROPI → 1.5 kΩ/100 nF → A4=PUMP_CURRENT_ADC`, nFAULT al bus diagnóstico.
- Solenoide CO₂: `TPS1HC120CQDYCRQ1`, D7, `R_ILIM=27 kΩ` (~0.5 A), clamp inductivo integrado.
- Chiller: `AQY212EHAX` PhotoMOS mediante `2N7002,215`; **dry contact SELV ≤48 V / NO MAINS**; potencia externa.
- D10/pad25=`ACT_FAULT_N` wired-OR; D9 continúa DNP/Reserva.

## Root EDA inter-zona — PR #14

Fuente machine-readable: `hardware/root_eda_contract.json`; detalle: `docs/FASE3_PR14_ROOT_EDA.md`.

`kicad/NFB_Insight_PCBA_v2.kicad_sch` es ahora un **root jerárquico inter-zona** con cinco hojas:

- Z0 → `uno_q_interface.kicad_sch`
- Z1 → `z1_interface.kicad_sch`
- Z2 → `z2_interface.kicad_sch`
- Z3 → `z3_interface.kicad_sch`
- Z4 → `z4_interface.kicad_sch`

Las fronteras entre zonas se materializan como sheet pins/nets KiCad. `GND` incluye Z0–Z4; `5V_RAIL` y `3V3_RAIL` son exclusivamente rails locales del shield y **no incluyen Z0**. I²C se comparte Z0/Z1/Z2; `12V_ACT` enlaza Z3/Z4; controles y diagnóstico de actuadores enlazan Z0/Z4.

**Alcance deliberado de PR #14:** `zone_internal_component_symbols=false`. La conectividad interna de Z1/Z2/Z3/Z4 continúa gobernada por los netlists JSON/BOM de producción; no se duplican manualmente >100 referencias dentro de KiCad.

### Gate ERC de transición PR #14

Como las hojas de interfaz aún no contienen sus símbolos internos, KiCad 10.0.5 reporta una deuda transitoria y reproducible de **125 `label_dangling`**. Esta deuda está congelada en `hardware/root_eda_contract.json` y el CI exige simultáneamente:

- exactamente 125 eventos `label_dangling`;
- **0 violaciones de cualquier otro tipo**;
- 0 warnings adicionales;
- severidades ERC de KiCad **sin relajar**.

Por tanto, PR #14 no se presenta como ERC=0. El requisito del siguiente gate es eliminar completamente esta deuda al materializar los símbolos/conexiones internos: **PR #15 debe alcanzar ERC=0 del hierarchy completo antes de placement**.

## Estado

Z0 mecánico, Z1, Z2, Z3, Z4, EU Compliance, footprints críticos y la jerarquía EDA inter-zona Z0–Z4 están protegidos por contratos y CI. El `.kicad_pcb` continúa sin placement de los bloques de producción y no existe routing nuevo.

Siguiente frente: **PR #15 — materialización reproducible de símbolos/conectividad interna de producción Z1+Z2+Z3+Z4**, con paridad JSON/BOM↔KiCad y ERC=0 antes de Fase 4 placement.
