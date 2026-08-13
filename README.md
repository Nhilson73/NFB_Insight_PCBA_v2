# NFB Insight PCBA v2

PCBA **shield/carrier** para **Nebula Fermentation Insight®**, diseñada alrededor del factor de forma inmutable del **Arduino UNO Q**. El repositorio `Nhilson73/nebula_qshield_pcb` es únicamente donante de ingeniería/trazabilidad; no gobierna placement, routing ni topología de producción V2.

## Fuente primaria UNO Q

Toda decisión dependiente del Arduino UNO Q se contrasta primero contra repositorios oficiales Arduino en GitHub (`github.com/Arduino`, especialmente `arduino/docs-content`), luego `docs.arduino.cc` y finalmente datasheets oficiales. La jerarquía y snapshots revisados viven en `docs/SOURCE_OF_TRUTH.md`.

## Frontera del producto / compliance

NFB Insight PCBA v2 es un **shield/carrier del UNO Q**, no un rediseño de su radio. No añade transmisores, antena, matching ni amplificación RF. El **EU Compliance Design Gate** vive en `docs/EU_COMPLIANCE_GATE.md` / `compliance/eu_compliance_contract.json` y cubre EMC, RoHS 3, REACH, WEEE, RED/CE del producto integrado.

## Mecánica y placement — PR #16 / #17

- UNO Q rotado; origen global `(0,0)`; USB-C hacia `-Y`.
- Envolvente UNO Q / Z0: `53.34 × 68.58 mm`.
- Altura total PCB fija `68.58 mm`; crecimiento solo `+X`.
- `Y=0` = FIELD I/O EDGE; cables hacia `-Y`.
- Gradiente: Z0 UNO Q → Z1 sensores → Z2 digital → Z3 potencia → Z4 actuadores.
- **Ancho final de placement PR17: `242.34 mm`.**
- Z0 `0.00→53.34 mm`.
- Z1 `53.34→108.84 mm` = `55.50 mm`.
- Z2 `108.84→163.34 mm` = `54.50 mm`.
- Z3 `163.34→198.34 mm` = `35.00 mm`.
- Z4 `198.34→242.34 mm` = `44.00 mm`.
- 119 footprints de producción + `J_UNOQ` = 120 footprints.
- 59 nets materializadas.
- PR17 cerró courtyard overlaps y fallos físicos de placement; routing permaneció en cero.

## Z1 sensores

- pH/A0 y DO/A5: 0–3 V acondicionados, ESD + `1 kΩ / 100 nF`.
- ORP/A1: divisor `10 kΩ / 20 kΩ`, máximo 3.0 V.
- TEMP/A2-D16: DS18B20 `TEMP_1WIRE`.
- CO₂: Honeywell `MPRLS0030PA00002A`, I²C `0x28`; `CO2_ADC` retirado.
- A4/pad13 = `PUMP_CURRENT_ADC`.

## Z2 digital / bajo ruido

- I²C: MPR `0x28` + DFR1103 `0x66`.
- HX711 3.3 V / 10 SPS en D2/D3.
- HMI D0/D1 mediante `TXU0202DCUR`.
- Watchdog `TPS3823-30DBVR`, WDI=D4.
- `J_LOADCELL`: Phoenix Contact **1757268 / MSTBA 2,5/4-G-5,08**.

## Z3 potencia

Fuentes: `hardware/power_architecture_contract.json`, `hardware/power_production_netlist.json`, `hardware/power_netclasses.json` y `bom/insight_power_production_bom.csv`.

- 12 V protegido → VIN del UNO Q.
- `5V_RAIL` y `3V3_RAIL` son locales del shield; no se unen a J_UNOQ.5/J_UNOQ.4.
- Protección `SMBJ15A-TR + TPS259470ARPWR`.
- Split `12V_HOST_VIN / 12V_LOGIC / 12V_ACT`.
- `F_ACT=045401.5MR`.
- 5 V `TPSM33625RDNR`; 3.3 V `TLV75533PDBVR`.
- Potencia del chiller externa.

## Z4 actuadores

- Bomba `DRV8242HQRHLRQ1`, D5/D6, IPROPI → A4.
- Solenoide `TPS1HC120CQDYCRQ1`, D7, ILIM ~0.5 A.
- Chiller `AQY212EHAX` + `2N7002`, **dry contact SELV ≤48 V / NO MAINS**.
- D10=`ACT_FAULT_N`; D9 DNP/Reserva.

## Hierarchy EDA — PR #14 / #15

`kicad/NFB_Insight_PCBA_v2.kicad_sch` es el root Z0–Z4. PR #15 materializó las hojas desde JSON/BOM de forma determinista y eliminó completamente la deuda ERC del PR #14.

KiCad **10.0.5** sobre el hierarchy completo:

- **0 Errors**
- **0 Warnings**
- **0 violations**

Los JSON/BOM siguen siendo autoridad; las hojas generadas no deben editarse manualmente para alterar conectividad.

## Routing readiness — PR #18

Fuente: `hardware/routing_contract.json`; narrativa: `docs/FASE5_PR18_ROUTING_READINESS.md`.

PR #18 **no añadió cobre**. Su función fue congelar las reglas antes de rutear:

- exactamente **59/59 nets** cubiertas una sola vez por 11 clases;
- mínimos de potencia heredados de PR #10 no pueden debilitarse;
- `In1.Cu` = **GND continuo; signal routing prohibido**;
- `In2.Cu` = distribución de potencia, sin analógica sensible;
- pH/ORP/DO, load-cell/HX711 y `PUMP_CURRENT_ADC` forman dominio sensible;
- `12V_ACT`, `PUMP_OUT1/2` y `CO2_SOL_POS` forman dominio dirty;
- separación contractual sensitive↔dirty ≥ `1.00 mm` en recorridos paralelos;
- `12V_ACT` y retornos high-current no atraviesan Z1/Z2;
- contactos de chiller permanecen aislados, SELV ≤48 V y sin tie a GND;
- `SW`, `CO2_ADC`, `TEMP_ADC`, `HUM_ADC`, `CO2_PWM`, `CO2_FLOW_PWM` y `RS485_IRQ_RSVD` están prohibidas como nets de producción.

El `TPSM33625` es un módulo integrado y no expone una net SW externa. Su entrada/salida/feedback deben permanecer compactos en Z3.

## Routing incremental — divide y vencerás

El PR #19 monolítico fue usado como **laboratorio de routing** y se cerró sin merge. Demostró que mezclar señales locales, long-haul, potencia y GND en un solo PR aumenta la congestión y dificulta auditar la calidad geométrica.

La base de conocimiento vive en `docs/ROUTING_KNOWLEDGE_BASE.md` y la partición machine-readable en `hardware/routing_batches_contract.json`.

Las 59 nets quedan divididas exhaustivamente y sin solapes:

- **28** nets locales — primer lote.
- **4** nets analógicas inter-zona: `PH_ADC`, `ORP_ADC`, `DO_ADC`, `PUMP_CURRENT_ADC`.
- **16** nets digital/control inter-zona.
- **10** nets de potencia + salidas de actuadores.
- **1** net GND, tratada como plano `In1.Cu` + stitching; el probe experimental identificó 83 endpoints.

Total: **28 + 4 + 16 + 10 + 1 = 59**.

Política de merge: **ALL_OR_NOTHING por lote**. No se mergea progreso parcial de un lote: todas sus nets deben estar conectadas, ninguna net futura puede ser tocada, no puede haber shorts/clearance/courtyard nuevos y placement/outline deben permanecer congelados.

La calidad de routing se evalúa también por longitud, segmentos, vías y cambios de dirección. Una ruta meandriforme no se acepta únicamente porque pase conectividad.

## ECOs de placement previos al routing

El routing experimental reveló dos microtopologías que convenía corregir antes de persistir cobre:

- **PR22 / Z3 TPSM33625:** mueve únicamente cinco pasivos críticos (`C_5V_IN_4U7`, `C_5V_IN_100N`, `C_5V_VCC`, `R_5V_FBT`, `R_5V_FBB`) con `U_5V` fijo. DRC físico = 0.
- **PR24 / Z2 HX711:** mueve únicamente `TP_LOAD_A_POS` y `TP_LOAD_A_NEG` cerca de `U_HX` para mantener el par principal `J_LOADCELL → U_HX` quieto y los testpoint stubs cortos. DRC físico = 0.

Los ECOs posteriores a PR17 deben ser mínimos, reproducibles, contractuales y mergearse antes de reiniciar el lote de routing afectado.

## Tooling KiCad y memoria operativa

Antes de escribir o ejecutar scripts `pcbnew` / `kicad-cli`, leer:

- **`docs/KICAD_TOOLING_NOTES.md`** — gotchas verificados de KiCad 10.0.5 y reglas de tooling;
- **`docs/ROUTING_KNOWLEDGE_BASE.md`** — decisiones de ingeniería y lecciones de routing;
- `hardware/routing_contract.json` y `hardware/routing_batches_contract.json` — autoridad machine-readable del cobre;
- `hardware/placement_manifest.json` — placement vigente + cadena ECO.

Reglas operativas destacadas:

- el triplete `.kicad_pcb + .kicad_pro + .kicad_dru` debe conservar el mismo basename en cualquier sandbox DRC;
- `.kicad_pro` contiene preferencias de proyecto; `.kicad_dru` puede imponer reglas efectivas diferentes;
- courtyard real se obtiene de las capas `*.Courtyard`, no de `footprint.GetBoundingBox()`;
- pad-shapes con el mismo `ref.pin` son un solo endpoint eléctrico lógico;
- equivalencia de PCB regenerado es semántica porque `pcbnew` puede regenerar UUIDs;
- workflows finales de validación son read-only para evitar bucles de auto-commit;
- KiCad DRC es la autoridad física final.

El repo donor `Nhilson73/nebula_qshield_pcb` aporta aprendizaje de tooling, **no geometría ni cobre** para NFB Insight.

## RF / enclosure

La fuente primaria Arduino revisada no publicó un antenna keepout numérico textual. NFB no inventa una distancia. Z0 permanece libre de footprints NFB y, durante routing, solo se permiten escapes mínimos hacia/desde `J_UNOQ`; la revisión final de cobre/enclosure/stacking/RF sigue siendo un gate de release.

## Estado actual

PR17 dejó el placement físico mergeado y revisado visualmente. PR18 congeló el contrato de routing. PR19/21/23 fueron laboratorios de routing cerrados sin merge. PR22 y PR24 corrigieron únicamente micro-islas de placement con DRC físico = 0.

**Siguiente checkpoint de producción: PR19A limpio, lote local 28/28, construido sobre el `main` post-PR24 y bajo las notas de tooling versionadas.**
