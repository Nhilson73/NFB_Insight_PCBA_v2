# NFB Insight PCBA v2

PCBA **shield/carrier** diseñada desde cero para **Nebula Fermentation Insight®**, construida alrededor del factor de forma mecánico inmutable del **Arduino UNO Q**.

El repositorio `Nhilson73/nebula_qshield_pcb` se conserva como **donante de ingeniería y trazabilidad**. No gobierna placement, routing ni topología eléctrica de producción de V2.

## Fuente primaria UNO Q

Para cualquier decisión que dependa del **Arduino UNO Q**, se revisan primero los repositorios oficiales de Arduino en GitHub:

- `https://github.com/Arduino`
- `https://github.com/orgs/arduino/repositories`
- especialmente `arduino/docs-content` y los repos oficiales de hardware/software UNO Q que correspondan.

Después se contrastan `docs.arduino.cc`, datasheets/PDF oficiales y demás documentación del fabricante. La política completa y la regla para resolver contradicciones están en `docs/SOURCE_OF_TRUTH.md`.

Esta jerarquía es obligatoria para pinout, potencia, mecánica, interfaces, firmware, RF y restricciones del host.

## Frontera del producto

NFB Insight PCBA v2 es un **shield/carrier del Arduino UNO Q**, no un rediseño de su plataforma radio.

- El UNO Q aporta computación, MCU y conectividad Wi‑Fi/Bluetooth.
- El shield base **no añade transmisores intencionales, antenas, matching ni amplificación RF**.
- Se preservarán los keepouts y condiciones de integración RF del UNO Q durante placement y routing.
- Arduino publica certificaciones del UNO Q; esa evidencia del host se archivará en el expediente técnico del producto.
- La evidencia del host no sustituye la calificación de materiales/BOM del shield ni la evaluación aplicable de la configuración final integrada.

El contrato normativo del shield está en `docs/EU_COMPLIANCE_GATE.md` y `compliance/eu_compliance_contract.json`.

## Convención mecánica congelada

- Origen global `(0,0)` en la esquina inferior izquierda de la envolvente rotada del UNO Q.
- USB-C hacia `-Y`.
- Envolvente UNO Q: `53.34 × 68.58 mm`.
- Altura de la board fija: `68.58 mm`.
- Crecimiento únicamente hacia `+X`.
- `Y=0` = FIELD I/O EDGE.
- Gradiente funcional: UNO Q → sensores/interfaz → digital/bajo ruido → potencia → actuadores.

## Baseline Z1 de producción — PR #6 / corrección de potencia PR #9

Fuentes de verdad:

- `hardware/insight_pin_contract.json`
- `hardware/sensor_interface_contract.json`
- `hardware/z1_production_netlist.json`
- `bom/insight_z1_production_bom.csv`
- `kicad/NFB_Insight_PCBA_v2.kicad_sch`

Decisiones congeladas:

- **pH / A0:** salida acondicionada 0–3 V; `1 kΩ + 100 nF`; ESD `PESD3V3U1UL`.
- **ORP / A1:** divisor `10 kΩ / 20 kΩ`, salida máxima 3.0 V; `100 nF`; ESD en `ORP_ADC`.
- **Temperatura / A2-D16:** `DS18B20`, net `TEMP_1WIRE`, pull-up onboard de `4.7 kΩ`.
- **Presión CO₂:** Honeywell `MPRLS0030PA00002A`, 0–30 psi absolute, I²C `0x28`; **A4/CO2_ADC queda DNP/Reserva**.
- **DO / A5:** salida acondicionada 0–3 V; `1 kΩ + 100 nF`; ESD `PESD3V3U1UL`.
- **Conectores eléctricos de campo:** JST XH side-entry con intención mecánica hacia `-Y`.
- Los BNC permanecen en los módulos acondicionadores OEM.
- `5V_RAIL` y `3V3_RAIL` son ahora **rails locales del shield**; no dependen de J_UNOQ.5/J_UNOQ.4.

`hardware/analog_insight_manifest.json` y `bom/insight_analog_inheritance.csv` permanecen únicamente como historial del Q-Shield.

## Baseline Z2 digital / bajo ruido — PR #7 / corrección de potencia PR #9

Fuentes de verdad:

- `hardware/z2_digital_contract.json`
- `hardware/z2_production_netlist.json`
- `bom/insight_z2_production_bom.csv`
- `kicad/z2_digital_contract.kicad_sch`

Decisiones congeladas:

- I²C global a 3.3 V con pull-ups de `4.7 kΩ`.
- MPR de Z1 en `0x28` + DFRobot DFR1103 GNSS/RTC externo en `0x66`.
- HX711 onboard a 3.3 V y 10 SPS, `DOUT=D2`, `SCK=D3`.
- HMI UART `D0/D1` mediante `TXU0202DCUR` 3.3 V ↔ 5 V.
- Watchdog `TPS3823-30DBVR`, `WDI=D4`, reset por `MCU_NRST`.
- Test points de bring-up definidos antes del placement.
- RS485/SC16IS740/ISO1541, GPS SAM-M8Q y RTC DS3231 separados quedan fuera del baseline Insight.
- `5V_RAIL` y `3V3_RAIL` permanecen locales al shield y secuenciados por la arquitectura de potencia PR #9.

## EU Compliance Design Gate — PR #8

Desde PR #8, las decisiones posteriores deben preservar:

- frontera RF del UNO Q;
- plano/retornos adecuados para EMC;
- protección ESD de interfaces externas;
- separación Z1/Z2 frente a Z3/Z4;
- trazabilidad RoHS 3 y REACH de la BOM del shield;
- preparación del expediente técnico y pre-compliance antes de liberar producción.

El workflow `EU Compliance Gate` protege estas reglas a nivel de repositorio.

## Arquitectura de potencia — PR #9

Fuente de verdad: `hardware/power_architecture_contract.json`. Documento: `docs/POWER_ARCHITECTURE.md`.

Baseline:

- Entrada del sistema: **12 VDC nominal**, fuente recomendada **12 V / 5 A / 60 W** certificada.
- Protección de entrada: `SMBJ15A` + **TPS259470ARPWR** eFuse.
- Split estrella después de protección:
  - `12V_HOST_VIN` → VIN del UNO Q;
  - `12V_LOGIC` → reguladores locales del shield;
  - `12V_ACT` → pump + solenoide CO₂.
- Chiller: **alimentación externa; solo señal de control por la PCBA**.
- `5V_RAIL`: **TPSM33625RDNR**, 2.5 A nominales, límite de diseño 1.5 A.
- `3V3_RAIL`: **TLV75533PDBVR**, 500 mA nominales, límite de diseño 250 mA.
- J_UNOQ.4 (`+3V3 OUT`) y J_UNOQ.5 (`+5V`) no alimentan los rails locales en el baseline.
- `IOREF` se trata como referencia/salida del UNO Q y nunca se retroalimenta; se usa conceptualmente para secuenciar el encendido del shield.

La revisión de `arduino/docs-content` confirmó que UNO Q soporta tres métodos de entrada: USB-C 5 V, VIN 7–24 V y 5 V regulados por JANALOG. NFB elige **12 V protegido → VIN** como método de integración, mientras mantiene los rails del shield separados deliberadamente.

## Estado

Z0 mecánico, Z1 sensores, Z2 digital/bajo ruido, EU Compliance Gate y la **arquitectura de potencia PR #9** están congelados contractualmente y protegidos por CI.

El siguiente frente es **materializar el esquemático de potencia**: valores de eFuse/OVLO/soft-start, feedback y capacitores del TPSM33625, LDO 3.3 V, conector/fusible de `12V_ACT`, netclasses y ERC. Placement y routing siguen fuera de alcance hasta cerrar ese bloque.
