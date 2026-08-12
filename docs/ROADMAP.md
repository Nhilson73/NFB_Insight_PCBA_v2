# NFB Insight PCBA v2 — Hoja de Ruta de Desarrollo

## Regla transversal — fuentes de verdad

- [x] Para cualquier decisión del **Arduino UNO Q**, revisar primero repositorios oficiales `arduino/*` en GitHub.
- [x] Documentar la jerarquía en `docs/SOURCE_OF_TRUTH.md`.
- [x] Resolver contradicciones por revisión/commit/especificidad antes de congelar producción.

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
- [ ] Confirmar específicamente keepout RF/antena del UNO Q contra fuentes oficiales Arduino antes de placement.
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
- [x] Honeywell `MPRLS0030PA00002A` para presión CO₂.
- [x] Presión CO₂ por I²C `0x28`; A4/CO2_ADC DNP/Reserva.
- [x] JST XH side-entry para pH/ORP/TEMP/DO.
- [x] ESD `PESD3V3U1UL,315`.
- [x] Filtros pH/DO `1 kΩ + 100 nF`.
- [x] ORP `10 kΩ / 20 kΩ + 100 nF`.
- [x] Pull-up `4.7 kΩ` de `TEMP_1WIRE`.
- [x] Footprint MPR propio.
- [x] Netlist/BOM/gates automáticos.
- [x] PR #9 corrige `3V3_RAIL`/`5V_RAIL` para que sean rails locales del shield, sin J_UNOQ.4/.5.
- [ ] Verificar filtros frente a ruido real durante bring-up/HIL.
- [ ] Validar footprint MPR contra STEP/3D antes del placement definitivo.

### PR #7 — Z2 digital / bajo ruido
- [x] HX711 onboard a 3.3 V, DOUT/SCK en D2/D3 y 10 SPS.
- [x] Conector de celda de carga y test points diferenciales.
- [x] DFR1103 GNSS+RTC I²C `0x66` reemplaza GPS/RTC legacy separados.
- [x] I²C global con pull-ups de `4.7 kΩ`.
- [x] HMI D0/D1 con `TXU0202DCUR` 3.3 V↔5 V.
- [x] ESD individual de UART de campo.
- [x] Watchdog `TPS3823-30DBVR`, WDI=D4, reset por `MCU_NRST`.
- [x] Test points de bring-up Z2.
- [x] Netlist/BOM/hoja contractual/gates Z2.
- [x] PR #9 corrige `3V3_RAIL`/`5V_RAIL` para que sean rails locales del shield, sin J_UNOQ.4/.5.
- [ ] Calificar fuente/lifecycle del HX711 antes de fabricación.
- [ ] Medir consumo real de HMI y DFR1103 durante bring-up.
- [ ] Validar HX711 con celda real durante bring-up/HIL.

### PR #8 — EU Compliance Design Gate del shield
- [x] Definir NFB Insight PCBA v2 como shield/carrier del Arduino UNO Q.
- [x] Shield base sin transmisor/antena/matching/amplificación RF añadidos.
- [x] Exigir preservación de keepout/condiciones RF del UNO Q.
- [x] Matriz EMC / RoHS 3 / WEEE / RED / REACH / CE.
- [x] Reglas EMC de plano GND, retornos, ruido, ESD e interfaces externas.
- [x] Evidencia RoHS/REACH de BOM, PCB y ensamblaje antes de producción.
- [x] Workflow `EU Compliance Gate`.
- [x] README actualizado.
- [ ] Archivar certificados/DoC oficiales específicos del SKU UNO Q utilizado antes de release RC.
- [ ] Confirmar con laboratorio edición exacta de normas armonizadas y plan final de ensayo.

## Fase 3 — Arquitectura de potencia

### PR #9 — Power tree y frontera UNO Q
- [x] Revisar repos oficiales Arduino/GitHub como fuente primaria del power tree UNO Q.
- [x] Confirmar métodos oficiales UNO Q: USB-C 5 V, VIN 7–24 V y 5 V regulados por JANALOG.
- [x] Elegir **12 V protegido → VIN** como método NFB preferido.
- [x] Separar `5V_RAIL` y `3V3_RAIL` locales del shield de J_UNOQ.5/J_UNOQ.4.
- [x] Usar `IOREF` solo como salida/referencia de alta impedancia; prohibir back-feed.
- [x] Congelar entrada nominal 12 V y fuente recomendada 12 V / 5 A / 60 W.
- [x] Congelar eFuse `TPS259470ARPWR` y familia TVS `SMBJ15A`.
- [x] Congelar split estrella `12V_HOST_VIN` / `12V_LOGIC` / `12V_ACT`.
- [x] Congelar chiller con potencia externa y solo señal de control por PCBA.
- [x] Congelar buck local `TPSM33625RDNR` para `5V_RAIL`.
- [x] Congelar LDO `TLV75533PDBVR` para `3V3_RAIL`.
- [x] Congelar envelope de diseño de 43.5 W sobre fuente de 60 W.
- [x] Crear `hardware/power_architecture_contract.json`.
- [x] Crear `docs/POWER_ARCHITECTURE.md` y `docs/SOURCE_OF_TRUTH.md`.
- [x] Elevar contrato UNO Q a schema v5 y corregir netlists Z1/Z2.
- [x] Crear `Validación arquitectura de potencia Insight` en CI.
- [x] Actualizar README.

### PR #10 — Esquemático de potencia de producción
- [ ] Revisar nuevamente schematic/power docs oficiales Arduino antes de materializar conexiones UNO Q.
- [ ] Calcular y congelar `R_ILIM`, OVLO, dV/dt/soft-start del TPS25947.
- [ ] Seleccionar MPN exacto del conector de entrada y `F_ACT`.
- [ ] Calcular feedback, frecuencia, capacitores y filtro EMI del TPSM33625 para 5.0 V.
- [ ] Congelar capacitores/enable del TLV75533.
- [ ] Materializar `power.kicad_sch` con ERC = 0.
- [ ] Crear BOM/netlist machine-readable de potencia.
- [ ] Definir netclasses de `12V_HOST_VIN`, `12V_ACT`, `5V_RAIL`, `3V3_RAIL`.
- [ ] Revisión térmica a 60 °C ambiente objetivo.
- [ ] Pasar EU Compliance Gate + power gate + gates Z1/Z2.

### Integración eléctrica posterior
- [ ] Integrar jerarquía Z1 + Z2 + potencia preservando contratos machine-readable.
- [ ] Construir hoja de actuadores Insight.
- [ ] Integrar jerarquía completa y mantener ERC = 0.

## Fase 4 — Placement

- [ ] Z0 UNO Q bloqueado.
- [ ] Keepout RF/antena UNO Q confirmado contra GitHub/CAD oficial y bloqueado.
- [ ] Z1 sensores con conectores sobre `Y=0`, salida `-Y`.
- [ ] U_CO2 accesible al tubing desde borde de servicio.
- [ ] Z2 digital/bajo ruido con J_LOADCELL, J_GNSS_RTC y J_HMI hacia borde de servicio.
- [ ] TVS próximos a entradas de cable.
- [ ] Z3: entrada/eFuse/buck/LDO con loops mínimos y lejos de Z1/RF.
- [ ] Z4: actuadores/retornos sucios.
- [ ] Revisión 3D completa.
- [ ] Congelar ancho final.

## Fase 5 — Routing

- [ ] Plano de referencia continuo.
- [ ] Prioridad: sensores → I²C/HX711 → potencia → actuadores.
- [ ] No usar In1.Cu como señales si se congela como GND.
- [ ] No atravesar keepout RF del UNO Q con cobre/señales/componentes del shield.
- [ ] Confinar nodo SW del buck a Z3.
- [ ] Retornos `12V_ACT` a región de entrada/estrella sin cruzar Z1/Z2.
- [ ] Stitching vias y test points deliberados.
- [ ] Revisar retornos EMC de cada interfaz externa.
- [ ] 0 desconectados inesperados.
- [ ] DRC = 0.

## Fase 6 — Fabricación

- [ ] Lifecycle/disponibilidad BOM.
- [ ] Calificar fabricante/fuente de HX711.
- [ ] Auditoría footprint vs datasheet/CAD primario.
- [ ] Conectores y alivio de tensión.
- [ ] Evidencia RoHS 3 de todos los MPN/materiales poblados.
- [ ] Evidencia REACH/SVHC de proveedores relevantes.
- [ ] Declaración del fabricante PCB: laminado, máscara, serigrafía y ENIG.
- [ ] Declaración del ensamblador/proceso SAC305 o alternativa aprobada.
- [ ] Archivar evidencia de conformidad/certificación del UNO Q utilizado.
- [ ] Plan de pre-compliance EMC/ESD/inmunidad.
- [ ] Gerbers/drill.
- [ ] BOM + CPL.
- [ ] Variante Insight.
- [ ] Stackup/notas de fabricación.
- [ ] Tag `v2.0-RC1` después de todos los gates.

## Fase 7 — Bring-up y HIL

- [ ] Rails antes de instalar UNO Q.
- [ ] Encendido limitado en corriente.
- [ ] Medir secuencia `12V_PROTECTED → UNO Q → IOREF → 5V_RAIL → 3V3_RAIL`.
- [ ] Verificar ausencia de back-feed con UNO Q apagado/USB conectado/desconectado.
- [ ] Medir consumo real ABX00173 bajo Wi‑Fi/App Lab/carga representativa.
- [ ] Inyección de pH/ORP/DO.
- [ ] DS18B20/1-Wire.
- [ ] MPR I²C `0x28` y prueba de presión.
- [ ] Ruido/interferencia de sensores y decisión final sobre aislamiento inline.
- [ ] DFR1103 I²C `0x66`: GNSS + RTC.
- [ ] HX711/celda real: cero, span, ruido y estabilidad.
- [ ] HMI UART con TXU0202 3.3 V↔5 V.
- [ ] Bomba/solenoide/chiller control.
- [ ] Watchdog/failsafe.
- [ ] Fixture HIL y prueba repetible de producción.
- [ ] Pre-scan EMC del conjunto con UNO Q, cables y actuadores representativos.
