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

## Z1 sensores — PR #6 / corrección PR #9

Fuentes: `hardware/sensor_interface_contract.json`, `hardware/z1_production_netlist.json` y `bom/insight_z1_production_bom.csv`.

- pH/A0 y DO/A5: señal acondicionada 0–3 V, ESD + `1 kΩ / 100 nF`.
- ORP/A1: divisor `10 kΩ / 20 kΩ`, máximo 3.0 V.
- TEMP/A2-D16: DS18B20 `TEMP_1WIRE`, pull-up 4.7 kΩ.
- CO₂: Honeywell `MPRLS0030PA00002A`, I²C `0x28`; A4 queda DNP/Reserva.
- BNC permanece en módulos OEM.
- `5V_RAIL` y `3V3_RAIL` son rails locales del shield.

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

Fuentes de verdad nuevas:

- `hardware/power_production_netlist.json`
- `bom/insight_power_production_bom.csv`
- `hardware/power_netclasses.json`
- `kicad/power.kicad_sch`

Baseline congelado:

- Conector 12 V: Phoenix Contact **1757242**, 2 polos / 5.08 mm.
- TVS: `SMBJ15A-TR`; bulk: `EEEFK1E101P` 100 µF / 25 V.
- eFuse `TPS259470ARPWR`: ladder UV/OV **470 kΩ / 11 kΩ / 47 kΩ**, `R_ILIM=750 Ω`, `C_DVDT=3.3 nF`, `C_ITIMER=2.2 nF`.
- Split estrella materializado contractualmente mediante `NT_HOST`, `NT_LOGIC` y `F_ACT`.
- `F_ACT`: Littelfuse **045401.5MR**, 1.5 A Slo-Blo; inrush real se revalida en HIL.
- `TPSM33625RDNR`: **1 MHz**, RT→VCC, feedback **40.2 kΩ / 10 kΩ**, entrada 4.7 µF + 100 nF, VCC 1 µF, salida 2×22 µF nominal + 100 nF, PGOOD pull-up 47 kΩ.
- `TLV75533PDBVR`: 1 µF de entrada, 1 µF + 100 nF de salida; `EN=5V_PGOOD`.
- Secuencia contractual: `12V_PROTECTED → UNO Q → IOREF → 5V_RAIL/PGOOD → 3V3_RAIL`.
- Netclasses de potencia definidas antes del routing.
- Screening térmico analítico a 60 °C documentado; termografía/HIL sigue siendo obligatoria antes de RC.
- **No se congela un filtro LC serie sin medición**: la red adicional de EMI se decidirá con pre-scan de emisiones conducidas/surge.

### Gates aún abiertos antes de placement

Los footprints de `TPS259470A` RPW-10 y `TPSM33625` RDN-11 deben auditarse/crearse desde los drawings TI. PR #10 **no coloca ni routea** componentes de potencia. La verificación de DC-bias de los 2×22 µF y la calificación final de pasivos/MPN permanecen como gates de liberación.

## Estado

Z0 mecánico, Z1, Z2, EU Compliance, arquitectura PR #9 y **baseline de potencia PR #10** están protegidos por CI/ERC. El siguiente paso, después de revisión del PR #10, es preparar la integración eléctrica/footprints auditados y posteriormente el placement por zonas; el routing continúa bloqueado hasta cerrar esos gates.
