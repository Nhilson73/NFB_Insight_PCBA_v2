# NFB Insight PCBA v2

PCBA **shield/carrier** para **Nebula Fermentation Insight®**, diseñada alrededor del factor de forma inmutable del **Arduino UNO Q**. El repositorio `Nhilson73/nebula_qshield_pcb` es únicamente donante de ingeniería/trazabilidad; no gobierna placement, routing ni topología de producción V2.

## Fuente primaria UNO Q

Toda decisión dependiente del Arduino UNO Q se contrasta primero contra repositorios oficiales Arduino en GitHub (`github.com/Arduino`, especialmente `arduino/docs-content`), luego `docs.arduino.cc` y finalmente datasheets oficiales. La jerarquía completa vive en `docs/SOURCE_OF_TRUTH.md`.

## Frontera del producto / compliance

NFB Insight PCBA v2 es un **shield/carrier del UNO Q**, no un rediseño de su radio. No añade transmisores, antena, matching ni amplificación RF; debe preservar sus keepouts y condiciones de integración. El **EU Compliance Design Gate** vive en `docs/EU_COMPLIANCE_GATE.md` / `compliance/eu_compliance_contract.json` y cubre la estrategia EMC, RoHS 3, REACH, WEEE, RED/CE del producto integrado.

## Mecánica congelada

- UNO Q rotado; origen global `(0,0)`; USB-C hacia `-Y`.
- Envolvente UNO Q `53.34 × 68.58 mm`.
- Altura total PCB fija `68.58 mm`; crecimiento solo `+X`.
- `Y=0` = FIELD I/O EDGE.
- Gradiente: Z0 UNO Q → Z1 sensores → Z2 digital → Z3 potencia → Z4 actuadores.
- Ancho actual `220 mm` **provisional** hasta placement.

## Z1 sensores — PR #6 / #9 / #11 / #12

Fuentes: `hardware/sensor_interface_contract.json`, `hardware/z1_production_netlist.json`, BOM Z1.

- pH/A0 y DO/A5: señales acondicionadas 0–3 V, ESD + `1 kΩ / 100 nF`.
- ORP/A1: divisor `10 kΩ / 20 kΩ`, máximo 3.0 V.
- TEMP/A2-D16: DS18B20 `TEMP_1WIRE`, pull-up 4.7 kΩ.
- CO₂ pressure: Honeywell `MPRLS0030PA00002A`, I²C `0x28`; `CO2_ADC` retirado.
- A4/pad13 = `PUMP_CURRENT_ADC` desde PR #12.

## Z2 digital / bajo ruido — PR #7 / #9

- I²C 3.3 V con MPR `0x28` + DFR1103 `0x66`.
- HX711 3.3 V / 10 SPS en D2/D3.
- HMI D0/D1 mediante `TXU0202DCUR`.
- Watchdog `TPS3823-30DBVR`, WDI=D4.
- GPS/RTC legacy separados y RS485 Signature quedan fuera de Insight.

## Z3 potencia — PR #9 / #10 / #13 / #15

Fuentes: `hardware/power_architecture_contract.json`, `hardware/power_production_netlist.json`, BOM potencia y `hardware/power_netclasses.json`.

- Entrada nominal 12 VDC; fuente objetivo `12 V / 5 A / 60 W` certificada.
- UNO Q se alimenta por **12 V protegido → VIN**.
- `5V_RAIL` y `3V3_RAIL` son rails locales del shield; no se unen a J_UNOQ.5/J_UNOQ.4.
- Protección `SMBJ15A-TR + TPS259470ARPWR`.
- Split `12V_HOST_VIN / 12V_LOGIC / 12V_ACT`.
- `F_ACT=045401.5MR` 1.5 A Slo-Blo.
- 5 V: `TPSM33625RDNR`; 3.3 V: `TLV75533PDBVR`.
- La potencia del chiller permanece externa.

## Z4 actuadores — PR #12 / #13

- Bomba: `DRV8242HQRHLRQ1`, D5/D6 PH/EN, IPROPI → A4 `PUMP_CURRENT_ADC`.
- Solenoide CO₂: `TPS1HC120CQDYCRQ1`, D7, `R_ILIM=27 kΩ` (~0.5 A), clamp integrado.
- Chiller: `AQY212EHAX` PhotoMOS + `2N7002`; **dry contact SELV ≤48 V / NO MAINS**.
- D10/pad25=`ACT_FAULT_N`; D9 permanece DNP/Reserva.

## Footprints críticos — PR #13

PR #13 cerró contra fuentes primarias los footprints de `TPS259470A/RPW0010A`, `TPSM33625/RDN0011A`, `DRV8242/RHL0020B`, `TPS1HC120/DYC0008A`, `AQY212EHAX` y previamente el Honeywell MPR. Gemini Spark se utilizó como cross-check, nunca como autoridad.

## Hierarchy EDA — PR #14 / PR #15

`kicad/NFB_Insight_PCBA_v2.kicad_sch` es el root jerárquico con cinco hojas Z0–Z4. PR #14 materializó las fronteras inter-zona y dejó una deuda transitoria controlada de 125 `label_dangling` porque aún no existían símbolos internos.

**PR #15 elimina completamente esa deuda.** Los child sheets ahora se generan de forma determinista desde JSON/BOM mediante:

- `tools/generate_production_schematics.py`
- `tools/normalize_pr15_schematics.py`
- `tools/migrate_pr15_verified_footprints.py`

Los JSON/BOM siguen siendo fuente de verdad; los child sheets generados no deben editarse manualmente para alterar conectividad. `kicad/lib/nfb_generated.kicad_sym` contiene los carriers EDA reproducibles.

### ERC de producción PR #15

KiCad **10.0.5** sobre el hierarchy completo alcanzó:

- **0 Errors**
- **0 Warnings**
- **0 violations**

El gate usa `--severity-all --exit-code-violations`; no se relajan severidades.

### Links físicos adicionales cerrados en PR #15

- `U_HMI_LVL / TXU0202DCUR` → `NFB:TI_DCU0008A_TXU0202`.
- `J_PWR_IN`, `J_PUMP`, `J_CO2_SOL`, `J_CHILLER_CTL` / Phoenix `1757242` → footprint MSTBA exacto de KiCad 10.0.5.
- `F_ACT / 045401.5MR` → `NFB:Littelfuse_0454_NANO2`, basado en land pattern 452/454; no se reutiliza por analogía 451/453.

Detalle técnico: `docs/FASE3_PR15_PRODUCTION_HIERARCHY.md`. Contratos: `hardware/root_eda_contract.json` y `hardware/eda_materialization_contract.json`.

## Estado actual

Arquitectura Z0–Z4, potencia, actuadores, compliance, footprints críticos y **hierarchy EDA materializado con ERC=0/0** están protegidos por CI. El `.kicad_pcb` continúa sin placement de referencias de producción y sin routing nuevo.

**Siguiente frente: PR #16 — pre-placement readiness:** cerrar keepouts RF/mecánicos del UNO Q contra fuentes oficiales Arduino, auditar footprints restantes con riesgo físico y congelar el contrato de placement antes de introducir coordenadas XY.
