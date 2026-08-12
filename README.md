# NFB Insight PCBA v2

PCBA/carrier diseñada desde cero para **Nebula Fermentation Insight®**, construida alrededor del factor de forma mecánico inmutable del Arduino UNO Q.

El repositorio `Nhilson73/nebula_qshield_pcb` se conserva como **donante de ingeniería y trazabilidad**. No gobierna placement, routing ni topología eléctrica de producción de V2.

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

## Estado

Z0 mecánico y el netlist de producción de Z1 están congelados y protegidos por CI/ERC. El siguiente bloque eléctrico será **Z2 digital/bajo ruido**; placement y routing continúan fuera de alcance hasta completar los bloques y la arquitectura de potencia.
