# NFB Insight PCBA v2

PCBA **shield/carrier** para **Nebula Fermentation Insight®**, diseñada alrededor del factor de forma inmutable del **Arduino UNO Q**. El repositorio `Nhilson73/nebula_qshield_pcb` es únicamente donante de ingeniería/trazabilidad; no gobierna placement, routing ni topología de producción V2.

## Fuente primaria UNO Q

Toda decisión dependiente del Arduino UNO Q se contrasta primero contra repositorios oficiales Arduino en GitHub (`github.com/Arduino`, especialmente `arduino/docs-content`), luego `docs.arduino.cc` y finalmente datasheets oficiales. La jerarquía y snapshots revisados viven en `docs/SOURCE_OF_TRUTH.md`.

## Frontera del producto / compliance

NFB Insight PCBA v2 es un **shield/carrier del UNO Q**, no un rediseño de su radio. No añade transmisores, antena, matching ni amplificación RF. El **EU Compliance Design Gate** vive en `docs/EU_COMPLIANCE_GATE.md` / `compliance/eu_compliance_contract.json` y cubre EMC, RoHS 3, REACH, WEEE, RED/CE del producto integrado.

## Mecánica y placement — PR #16 / #17 / ECO PR #22 / #24

- UNO Q rotado; origen global `(0,0)`; USB-C hacia `-Y`.
- Envolvente UNO Q / Z0: `53.34 × 68.58 mm`.
- Altura total PCB fija `68.58 mm`; crecimiento solo `+X`.
- `Y=0` = FIELD I/O EDGE; cables hacia `-Y`.
- Gradiente: Z0 UNO Q → Z1 sensores → Z2 digital → Z3 potencia → Z4 actuadores.
- **Ancho final de placement: `242.34 mm`.**
- Z0 `0.00→53.34 mm`.
- Z1 `53.34→108.84 mm` = `55.50 mm`.
- Z2 `108.84→163.34 mm` = `54.50 mm`.
- Z3 `163.34→198.34 mm` = `35.00 mm`.
- Z4 `198.34→242.34 mm` = `44.00 mm`.
- 119 footprints de producción + `J_UNOQ` = 120 footprints.
- 59 nets materializadas.
- PR17 cerró courtyard overlaps y fallos físicos de placement.
- PR22 aplicó el ECO acotado de placement alrededor del `TPSM33625` en Z3.
- PR24 acercó `TP_LOAD_A_POS/NEG` al HX711 en Z2 sin alterar el resto del placement.

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

## Tooling KiCad — PR #25

Las reglas operativas para agentes y automatización KiCad viven en `docs/KICAD_TOOLING_NOTES.md`, `docs/ROUTING_KNOWLEDGE_BASE.md` y `hardware/kicad_tooling_contract.json`.

Principios relevantes:

- `.kicad_pcb + .kicad_pro + .kicad_dru` se tratan como triplete canónico;
- KiCad 10.0.5 DRC es la autoridad física final;
- no se relajan clearances globales para hacer pasar routing;
- pads compuestos se modelan como geometría múltiple pero un endpoint lógico por `(ref,pin)`;
- placement se valida semánticamente, no por identidad textual/UUID del PCB;
- workflows finales de aceptación son `contents: read`.

## Routing incremental — divide y vencerás

El PR #19 monolítico fue usado como **laboratorio de routing** y se cerró sin merge. Demostró que mezclar señales locales, long-haul, potencia y GND en un solo PR aumenta la congestión y dificulta auditar la calidad geométrica.

La base de conocimiento vive en `docs/ROUTING_KNOWLEDGE_BASE.md` y la partición machine-readable en `hardware/routing_batches_contract.json`.

Las 59 nets quedan divididas exhaustivamente y sin solapes:

- **PR19A: 28** nets locales.
- **PR19B: 4** nets analógicas inter-zona: `PH_ADC`, `ORP_ADC`, `DO_ADC`, `PUMP_CURRENT_ADC`.
- **PR19C: 16** nets digital/control inter-zona.
- **PR20A: 10** nets de potencia + salidas de actuadores.
- **PR20B: 1** net GND, tratada como plano `In1.Cu` + stitching; el probe experimental identificó 83 endpoints.

Total: **28 + 4 + 16 + 10 + 1 = 59**.

Política de merge: **ALL_OR_NOTHING por lote**. No se mergea progreso parcial de un lote: todas sus nets deben estar conectadas, ninguna net futura puede ser tocada, no puede haber shorts/clearance/courtyard nuevos y placement/outline deben permanecer congelados.

La calidad de routing se evalúa también por longitud, segmentos, vías y cambios de dirección. Una ruta meandriforme no se acepta únicamente porque pase conectividad.

## PR19A — 28 nets locales / PR #28

El primer lote físico de producción queda materializado y persistido sobre el placement post-PR22/post-PR24.

Estado congelado del checkpoint:

- **28/28 nets PR19A con cobre.**
- **31/31 nets de lotes futuros sin cobre.**
- **523 segmentos.**
- **24 vías.**
- `In1.Cu`: **0 signal tracks**.
- copper zones: **0**.
- KiCad 10.0.5 DRC: **0 errors**.
- DRC warnings conocidos: **255**, exclusivamente deuda de serigrafía/texto:
  - `silk_edge_clearance`: 13;
  - `text_height`: 1;
  - `silk_overlap`: 173;
  - `silk_over_copper`: 68.
- unconnected restantes: **204**; ninguno pertenece a las 28 nets PR19A y corresponden a lotes futuros todavía no rutados.

La pasada de calidad redujo dos rutas excesivamente fragmentadas sin cambiar sus corredores DRC-clean:

- `5V_PGOOD`: **143 → 12 segmentos**.
- `WDT_MR_N`: **100 → 10 segmentos**.

El PCB de este checkpoint está persistido en `kicad/NFB_Insight_PCBA_v2.kicad_pcb`; el manifest de evidencia vive en `hardware/pr19a_local_routing_manifest.json` y el probe en `hardware/pr19a_local_probe.json`.

## PR19B — 4 nets analógicas long-haul / PR #30

PR #30 materializó el segundo lote de producción bajo política **ALL_OR_NOTHING**:

- `PH_ADC`
- `ORP_ADC`
- `DO_ADC`
- `PUMP_CURRENT_ADC`

Checkpoint congelado post-merge:

- **4/4 nets PR19B conectadas.**
- PR19A preservado íntegramente: **523 segmentos / 24 vías**.
- PR19B añadió **32 segmentos / 7 vías**.
- acumulado de producción: **555 segmentos / 31 vías**.
- **27 nets futuras sin cobre** al cierre de PR19B.
- `In1.Cu`: **0 signal tracks**.
- copper zones: **0**.
- KiCad 10.0.5 DRC: **0 errors**.
- warnings conocidos: **255**, sin deuda nueva de cobre.
- unconnected restantes: **192**.
- placement y outline congelados sin cambios.
- workflows finales de aceptación: **15/15 verdes**.

Los guardrails históricos fueron promovidos para reconocer de forma exacta `PRE_ROUTING → PR19A → PR19B` mediante contratos/manifests versionados, sin relajar DRC. Evidencia: `hardware/pr19b_analog_routing_manifest.json`; narrativa: `docs/FASE5_PR19B_ANALOG_ROUTING.md`.

## PR19C — 16 nets digital/control inter-zona / PR #31

PR #31 está en fase de laboratorio sobre el checkpoint PR19B. Antes de materializar cobre se ejecutó un probe **read-only** en KiCad 10.0.5 que revalidó primero el baseline PR19B y luego extrajo endpoints reales de las 16 nets:

`ACT_FAULT_N`, `CHILLER_CTL`, `CO2_SOL_CTL`, `HMI_RX`, `HMI_TX`, `HX711_DOUT`, `HX711_SCK`, `I2C_SCL`, `I2C_SDA`, `LED_STATUS`, `MCU_NRST`, `MCU_WDI`, `PUMP_DIR`, `PUMP_PWM`, `TEMP_1WIRE`, `UNO_IOREF_3V3`.

Baseline confirmado antes de PR19C:

- **555 segmentos / 31 vías**.
- **DRC=0 errors**.
- **192 unconnected**.
- **16/16 nets PR19C sin cobre propio** al iniciar el lote.
- **11 nets PR20A/PR20B sin cobre adelantado**.
- `In1.Cu` sigue reservado a GND, sin signal routing.
- B.Cu permanece como corredor preferente para long-haul low-speed; F.Cu se reserva para escapes locales y conexiones cortas.

El gate de PR19C exige **16/16 conectadas y revisión geométrica**, sin tocar PR20A/PR20B y sin alterar placement/outline.

## RF / enclosure

La fuente primaria Arduino revisada no publicó un antenna keepout numérico textual. NFB no inventa una distancia. Z0 permanece libre de footprints NFB y, durante routing, solo se permiten escapes mínimos hacia/desde `J_UNOQ`; la revisión final de cobre/enclosure/stacking/RF sigue siendo un gate de release.

## Estado actual

Placement y ECOs PR22/PR24 están congelados. PR18 congeló las reglas de routing. PR25 consolidó tooling KiCad. **PR28 cerró PR19A (28/28) y PR30 cerró PR19B (4/4), dejando el PCB de producción en 555 segmentos, 31 vías y DRC físico 0 errores.**

**Checkpoint en curso: PR19C / PR #31 — routing de las 16 nets digital/control inter-zona. El probe read-only ya pasó sobre el baseline PR19B; el siguiente gate es materializar 16/16 bajo política ALL_OR_NOTHING y validar geometría + DRC antes del merge.**
