# NFB Insight PCBA v2 — Hoja de Ruta de Desarrollo

## Fase 0 — Congelar arquitectura

- [x] Repositorio limpio y herencia selectiva desde Q-Shield.
- [x] Sistema global de coordenadas.
- [x] UNO Q con USB-C hacia `-Y`.
- [x] Altura de board `68.58 mm`; crecimiento solo `+X`.
- [x] `Y=0` como FIELD I/O EDGE.
- [x] Zonas Z0–Z4 y clasificación BOM donante.

## Fase 1 — Mecánica UNO Q

- [x] Footprint inmutable del UNO Q rotado.
- [x] Cuatro agujeros de montaje transformados.
- [x] Referencias mecánicas USB-C/PMIC/JCTL/SPI/Qwiic.
- [x] Contorno inicial `68.58 mm` alto × `220 mm` ancho provisional.
- [x] Validación automática mecánica/DRC.
- [ ] Convertir keepouts definitivos después de contrastar CAD/STEP y enclosure.
- [ ] Verificar UNO Q + carrier en KiCad 3D Viewer.
- [ ] Congelar ancho final solo después del placement.

## Fase 2 — Arquitectura eléctrica Insight

### PR #3 — Contrato UNO Q
- [x] Root schematic limpio.
- [x] Contrato machine-readable de 32 pads.
- [x] D0–D21 funcionalmente clasificados.
- [x] A3 y D9 DNP/Reserva; D10 reserva Signature.
- [x] Snapshot de firmware congelado.
- [x] ERC automatizado.

### PR #4 — Trazabilidad analógica donante
- [x] Manifiesto de herencia por canal.
- [x] BOM donor `INHERIT/REVIEW`.
- [x] Historial pH/ORP/TEMP/CO2/DO.
- [x] Humedad descartada.
- [x] Hoja KiCad histórica + gate de trazabilidad.

### PR #5 — Interfaces reales de sensores
- [x] pH y DO como señales acondicionadas 0–3 V.
- [x] ORP acondicionado con escalamiento a 3.0 V.
- [x] Temperatura corregida a DS18B20 / `TEMP_1WIRE`.
- [x] BNC y aislamiento de electrodo crudo fuera de PCBA base.
- [x] `MPX5700AP` bloqueado para reemplazo.
- [x] Gates de dominio ADC y coherencia.

### PR #6 — Z1 netlist de producción
- [x] Seleccionar Honeywell `MPRLS0030PA00002A` para presión CO₂.
- [x] Migrar presión CO₂ de `CO2_ADC/A4` a I²C `0x28` sobre D20/D21.
- [x] Dejar A4 DNP/Reserva y prohibir `CO2_ADC` como net activa.
- [x] Congelar JST XH `S3B-XH-A(LF)(SN)` side-entry para pH/ORP/TEMP/DO.
- [x] Congelar `PESD3V3U1UL,315` como ESD de líneas externas.
- [x] Congelar filtros pH/DO `1 kΩ + 100 nF`.
- [x] Congelar ORP `10 kΩ / 20 kΩ + 100 nF`, clamp después del divisor.
- [x] Poblar pull-up `4.7 kΩ` de `TEMP_1WIRE`.
- [x] Congelar `GRM155R71E104KE14D` para 100 nF.
- [x] Crear footprint propio `NFB:Honeywell_MPR_LongPort_12Pad`.
- [x] Crear `hardware/z1_production_netlist.json`.
- [x] Crear `bom/insight_z1_production_bom.csv`.
- [x] Materializar componentes y nets Z1 en el root schematic KiCad.
- [x] Añadir gates automáticos BOM/netlist/footprint/contrato/ERC.
- [ ] Verificar filtros frente a ruido real durante bring-up/HIL; cualquier cambio requerirá PR.
- [ ] Validar footprint MPR contra STEP/3D antes del placement definitivo.

### PR #7 — Z2 digital / bajo ruido
- [ ] HX711 y celda de carga.
- [ ] RTC.
- [ ] GPS.
- [ ] I²C global y pull-ups definitivos.
- [ ] HMI UART.
- [ ] Watchdog/supervisión.
- [ ] Test points y contrato de bring-up.
- [ ] ERC y BOM Z2.

### Integración eléctrica posterior
- [ ] Construir hoja de potencia después de Fase 3.
- [ ] Construir hoja de actuadores Insight.
- [ ] Integrar jerarquía completa y mantener ERC = 0.

## Fase 3 — Arquitectura de potencia

- [ ] Separar lógica/sensores de potencia ruidosa.
- [ ] Decidir qué cargas atraviesan la PCBA.
- [ ] Chiller con energía externa y solo señal de control por defecto.
- [ ] Calcular corrientes continuas/pico.
- [ ] Reseleccionar F1/D2/conector de entrada.
- [ ] Revalidar buck/LDO.
- [ ] Definir netclasses.

## Fase 4 — Placement

- [ ] Z0 UNO Q bloqueado.
- [ ] Z1 sensores con conectores sobre `Y=0`, salida `-Y`.
- [ ] U_CO2 accesible al tubing desde borde de servicio.
- [ ] Z2 digital/bajo ruido.
- [ ] Z3 potencia.
- [ ] Z4 actuadores.
- [ ] Revisión 3D completa.
- [ ] Congelar ancho final.

## Fase 5 — Routing

- [ ] Plano de referencia continuo.
- [ ] Prioridad: sensores → I²C/HX711/clocks → potencia → actuadores.
- [ ] No usar In1.Cu como capa de señales si se congela como GND.
- [ ] Routing de alta corriente solo después de Fase 3.
- [ ] Stitching vias y test points deliberados.
- [ ] 0 desconectados inesperados.
- [ ] DRC = 0.

## Fase 6 — Fabricación

- [ ] Lifecycle/disponibilidad BOM.
- [ ] Auditoría footprint vs datasheet.
- [ ] Conectores y alivio de tensión.
- [ ] Gerbers/drill.
- [ ] BOM + CPL.
- [ ] Variante Insight.
- [ ] Stackup/notas de fabricación.
- [ ] Tag `v2.0-RC1` después de todos los gates.

## Fase 7 — Bring-up y HIL

- [ ] Rails antes de instalar UNO Q.
- [ ] Encendido limitado en corriente.
- [ ] Inyección de pH/ORP/DO.
- [ ] DS18B20/1-Wire.
- [ ] MPR I²C `0x28` y prueba de presión hasta rango de trabajo.
- [ ] Ruido/interferencia de sensores y decisión final sobre aislamiento inline.
- [ ] HX711/HMI/GPS/RTC/I²C.
- [ ] Bomba/solenoide/chiller.
- [ ] Watchdog/failsafe.
- [ ] Fixture HIL y prueba repetible de producción.
