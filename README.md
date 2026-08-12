# NFB Insight PCBA v2

PCBA **shield/carrier** para **Nebula Fermentation Insight®**, diseñada alrededor del factor de forma inmutable del **Arduino UNO Q**. El repositorio `Nhilson73/nebula_qshield_pcb` es únicamente donante de ingeniería y trazabilidad; no gobierna placement, routing ni topología de producción de V2.

## Fuente primaria UNO Q

Toda decisión dependiente del **Arduino UNO Q** se contrasta primero contra los repositorios oficiales de Arduino en GitHub:

- `https://github.com/Arduino`
- `https://github.com/orgs/arduino/repositories`
- especialmente `arduino/docs-content` y los repos oficiales UNO Q aplicables.

Después se contrastan `docs.arduino.cc` y datasheets/PDF oficiales. La jerarquía completa está en `docs/SOURCE_OF_TRUTH.md` y es obligatoria para pinout, potencia, mecánica, firmware, RF e interfaces.

## Frontera del producto

NFB Insight PCBA v2 es un **shield/carrier del Arduino UNO Q**, no un rediseño de su plataforma radio.

- UNO Q aporta computación, MCU, Wi‑Fi/Bluetooth y su power tree interno.
- El shield base no añade transmisores, antenas, matching ni amplificación RF.
- Se preservarán keepouts y condiciones de integración RF del UNO Q.
- La evidencia regulatoria del host se archiva en el expediente técnico, pero no reemplaza la calificación del shield ni la evaluación del producto integrado.

El **EU Compliance Design Gate** está definido en `docs/EU_COMPLIANCE_GATE.md` y `compliance/eu_compliance_contract.json`.

## Mecánica congelada

- Origen global `(0,0)` en la esquina inferior izquierda del UNO Q rotado.
- USB-C hacia `-Y`.
- Envolvente UNO Q: `53.34 × 68.58 mm`.
- Altura PCB fija: `68.58 mm`; crecimiento solo hacia `+X`.
- `Y=0` = FIELD I/O EDGE.
- Gradiente: UNO Q → Z1 sensores → Z2 digital/bajo ruido → Z3 potencia → Z4 actuadores.
- El ancho actual de 220 mm continúa **provisional** hasta placement.

## Z1 sensores — PR #6 / corrección PR #9 / audit PR #11

Fuentes: `hardware/sensor_interface_contract.json`, `hardware/z1_production_netlist.json` y `bom/insight_z1_production_bom.csv`.

- pH/A0 y DO/A5: señal acondicionada 0–3 V, ESD + `1 kΩ / 100 nF`.
- ORP/A1: divisor `10 kΩ / 20 kΩ`, máximo 3.0 V.
- TEMP/A2-D16: DS18B20 `TEMP_1WIRE`, pull-up 4.7 kΩ.
- CO₂: Honeywell `MPRLS0030PA00002A`, I²C `0x28`; A4 queda DNP/Reserva.
- BNC permanece en módulos OEM.
- `5V_RAIL` y `3V3_RAIL` son rails locales del shield.
- PR #11 auditó `NFB:Honeywell_MPR_LongPort_12Pad` contra Honeywell `32332628 Issue L / Figure 10` y corrigió el patrón al span recomendado de 4.20 mm.

## Z2 digital / bajo ruido — PR #7 / corrección PR #9

Fuentes: `hardware/z2_digital_contract.json`, `hardware/z2_production_netlist.json` y `bom/insight_z2_production_bom.csv`.

- I²C 3.3 V, pull-ups 4.7 kΩ; MPR `0x28` + DFR1103 `0x66`.
- HX711 a 3.3 V, 10 SPS, D2/D3.
- HMI D0/D1 mediante `TXU0202DCUR` 3.3 V ↔ 5 V.
- Watchdog `TPS3823-30DBVR`, WDI=D4, reset por `MCU_NRST`.
- GPS/RTC legacy separados y RS485 Signature quedan fuera del baseline Insight.

## Arquitectura de potencia — PR #9

Fuente: `hardware/power_architecture_contract.json` y `docs/POWER_ARCHITECTURE.md`.

- Entrada nominal **12 VDC**; fuente recomendada **12 V / 5 A / 60 W** certificada.
- NFB alimenta UNO Q por **12 V protegido → VIN**; Arduino también soporta USB-C 5 V y 5 V regulados por JANALOG, pero no son el baseline NFB.
- `5V_RAIL` y `3V3_RAIL` locales no se conectan a J_UNOQ.5/J_UNOQ.4.
- `IOREF` es salida/referencia del host y nunca se retroalimenta.
- Protección: `SMBJ15A` + `TPS259470ARPWR`.
- Split: `12V_HOST_VIN`, `12V_LOGIC`, `12V_ACT`.
- Chiller con potencia externa; control solamente desde el shield.
- 5 V: `TPSM33625RDNR`; 3.3 V: `TLV75533PDBVR`.

## Esquemático de potencia de producción — PR #10

Fuentes de verdad:

- `hardware/power_production_netlist.json`
- `bom/insight_power_production_bom.csv`
- `hardware/power_netclasses.json`
- `kicad/power.kicad_sch`

Baseline:

- Conector 12 V: Phoenix Contact **1757242**, 2 polos / 5.08 mm.
- TVS: `SMBJ15A-TR`; bulk: `EEEFK1E101P` 100 µF / 25 V.
- eFuse `TPS259470ARPWR`: ladder UV/OV **470 kΩ / 11 kΩ / 47 kΩ**, `R_ILIM=750 Ω`, `C_DVDT=3.3 nF`, `C_ITIMER=2.2 nF`.
- Split estrella mediante `NT_HOST`, `NT_LOGIC` y `F_ACT`.
- `F_ACT`: Littelfuse **045401.5MR**, 1.5 A Slo-Blo; inrush real se revalida en HIL.
- `TPSM33625RDNR`: **1 MHz**, RT→VCC, feedback **40.2 kΩ / 10 kΩ**, entrada 4.7 µF + 100 nF, VCC 1 µF, salida 2×22 µF nominal + 100 nF, PGOOD 47 kΩ.
- `TLV75533PDBVR`: 1 µF de entrada, 1 µF + 100 nF de salida; `EN=5V_PGOOD`.
- Secuencia: `12V_PROTECTED → UNO Q → IOREF → 5V_RAIL/PGOOD → 3V3_RAIL`.
- Netclasses contractuales previas al routing.
- Screening térmico analítico a 60 °C; termografía/HIL obligatoria antes de RC.
- No se congela un filtro LC serie sin pre-scan EMC.

## Auditoría de footprints e integración — PR #11

Fuentes nuevas:

- `hardware/footprint_audit.json`
- `docs/FOOTPRINT_AUDIT.md`
- `hardware/electrical_integration_contract.json`
- `kicad/integration_contract.kicad_sch`

Reglas y estado:

- **Honeywell MPR:** audit cerrado contra datasheet oficial `32332628 Issue L`; placement permitido cuando comience Fase 4.
- **TPS259470A / RPW0010A:** package drawing TI `MPQF568 / 4225183/A` revisado; placement sigue **bloqueado** hasta importar/recrear y verificar exactamente el land pattern HotRod QFN.
- **TPSM33625 / RDN-11:** cuerpo/pitch/pin-count verificados contra TI; placement sigue **bloqueado** hasta CAD autorizado/verificable. No se reconstruye el land pattern a partir de body + pitch.
- El contrato Z1 + Z2 + Z3 congela `GND`, `3V3_RAIL`, `5V_RAIL`, I²C y la frontera de potencia con UNO Q.
- `J_UNOQ.4` nunca pertenece a `3V3_RAIL`; `J_UNOQ.5` nunca pertenece a `5V_RAIL`.
- `UNO_IOREF_3V3` es exclusivamente host→shield.
- I²C integrado: MPR `0x28` + DFR1103 `0x66`.
- Z4 actuadores, placement y routing permanecen fuera de alcance.

El workflow `Validación footprints e integración PR11` impide que un footprint crítico abierto llegue accidentalmente al PCB.

## Estado

Z0 mecánico, Z1, Z2, EU Compliance, arquitectura PR #9, potencia PR #10 y la **integración eléctrica/auditoría PR #11** están protegidos contractualmente por CI/ERC.

El siguiente frente es **Z4 actuadores de Insight** y, en paralelo, cerrar los dos footprints TI pendientes antes de habilitar placement. El routing sigue bloqueado hasta completar jerarquía eléctrica, actuadores y auditorías físicas.
