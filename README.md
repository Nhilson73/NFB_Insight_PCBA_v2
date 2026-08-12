# NFB Insight PCBA v2

PCBA **shield/carrier** diseñada desde cero para **Nebula Fermentation Insight®**, construida alrededor del factor de forma mecánico inmutable del **Arduino UNO Q**.

El repositorio `Nhilson73/nebula_qshield_pcb` se conserva como **donante de ingeniería y trazabilidad**. No gobierna placement, routing ni topología eléctrica de producción de V2.

## Frontera del producto

NFB Insight PCBA v2 es un **shield/carrier del Arduino UNO Q**, no un rediseño de su plataforma radio.

- El UNO Q aporta la computación, MCU y conectividad Wi‑Fi/Bluetooth.
- El shield base **no añade transmisores intencionales, antenas, matching ni amplificación RF**.
- Se preservarán los keepouts y condiciones de integración RF del UNO Q durante placement y routing.
- Arduino publica certificaciones del UNO Q, incluyendo CE; esa evidencia del host se archivará en el expediente técnico del producto.
- La evidencia del host no sustituye la calificación de materiales/BOM del shield ni la evaluación aplicable de la configuración final integrada.

Fuentes oficiales de referencia:

- Arduino UNO Q: `https://docs.arduino.cc/hardware/uno-q/`
- Arduino Product Compliance: `https://docs.arduino.cc/certifications/`

El contrato normativo de diseño del shield está en `docs/EU_COMPLIANCE_GATE.md` y `compliance/eu_compliance_contract.json`.

## Convención mecánica congelada

- Origen global `(0,0)` en la esquina inferior izquierda de la envolvente rotada del UNO Q.
- USB-C hacia `-Y`.
- Envolvente UNO Q: `53.34 × 68.58 mm`.
- Altura de la board fija: `68.58 mm`.
- Crecimiento únicamente hacia `+X`.
- `Y=0` = FIELD I/O EDGE.
- Gradiente funcional: UNO Q → sensores/interfaz → digital/bajo ruido → potencia → actuadores.

## Baseline Z1 de producción — PR #6

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
- **Conectores eléctricos de campo:** JST XH `S3B-XH-A(LF)(SN)` side-entry, con intención mecánica hacia `-Y`.
- Los BNC permanecen en los módulos acondicionadores OEM.
- El aislamiento inline `DFR0504` o equivalente sigue siendo una opción de sistema, no un placement base.

`hardware/analog_insight_manifest.json` y `bom/insight_analog_inheritance.csv` permanecen únicamente como historial del Q-Shield.

## Baseline Z2 digital / bajo ruido — PR #7

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

## EU Compliance Design Gate — PR #8

Desde PR #8, las decisiones posteriores deben preservar:

- frontera de RF del UNO Q;
- plano/retornos adecuados para EMC;
- protección ESD de interfaces externas;
- separación Z1/Z2 frente a Z3/Z4;
- trazabilidad RoHS 3 y REACH de la BOM del shield;
- preparación del expediente técnico y pre-compliance antes de liberar producción.

El workflow `EU Compliance Gate` protege estas reglas a nivel de repositorio. La edición final de normas armonizadas y el plan de ensayo se confirmarán con el laboratorio antes de la liberación RC.

## Estado

Z0 mecánico, Z1 sensores y Z2 digital/bajo ruido están congelados contractualmente y protegidos por CI/ERC. El siguiente frente eléctrico es **Fase 3 — arquitectura de potencia**; placement y routing permanecen fuera de alcance hasta cerrar la potencia y los gates de cumplimiento asociados.
