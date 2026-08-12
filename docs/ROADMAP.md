# NFB Insight PCBA v2 — Hoja de Ruta de Desarrollo

## Regla transversal — fuentes de verdad

- [x] Para cualquier decisión del **Arduino UNO Q**, revisar primero repositorios oficiales `arduino/*` en GitHub.
- [x] Jerarquía documentada en `docs/SOURCE_OF_TRUTH.md`.
- [x] Resolver contradicciones por revisión/commit/especificidad antes de congelar producción.
- [x] No inventar land patterns: footprint crítico requiere drawing/CAD primario reproducible.

## Fase 0 — Arquitectura

- [x] Repositorio limpio y herencia selectiva desde Q-Shield.
- [x] Sistema global de coordenadas.
- [x] UNO Q USB-C hacia `-Y`.
- [x] Altura PCB `68.58 mm`; crecimiento solo `+X`.
- [x] `Y=0` como FIELD I/O EDGE.
- [x] Zonas Z0–Z4.

## Fase 1 — Mecánica UNO Q

- [x] Footprint mecánico inmutable del UNO Q rotado.
- [x] Cuatro agujeros transformados y referencias mecánicas.
- [x] Contorno inicial `68.58 mm × 220 mm` provisional.
- [x] Validación automática mecánica/DRC.
- [ ] Convertir keepouts definitivos tras contrastar CAD/STEP/enclosure.
- [ ] Confirmar keepout RF/antena contra fuentes oficiales Arduino antes de placement.
- [ ] Verificar UNO Q + carrier en 3D Viewer.
- [ ] Congelar ancho final después del placement.

## Fase 2 — Arquitectura eléctrica Insight

### PR #3 — Contrato UNO Q
- [x] Contrato machine-readable de 32 pads + ERC.
- [x] A3/D9 DNP; D10 reserva.
- [x] Snapshot de firmware.

### PR #4 — Trazabilidad analógica
- [x] Manifiesto/BOM donante `INHERIT/REVIEW`.
- [x] Humedad descartada.

### PR #5 — Interfaces reales de sensores
- [x] pH/ORP/DO acondicionados.
- [x] TEMP corregida a DS18B20/1-Wire.
- [x] BNC/front-end de electrodo crudo fuera del shield base.

### PR #6 — Z1 producción
- [x] MPR `0x28`; A4/CO2_ADC DNP.
- [x] ESD/filtros/JST/pull-up TEMP congelados.
- [x] Netlist/BOM/gates Z1.
- [x] PR #9 corrige 5V/3V3 a rails locales del shield.
- [x] PR #11 audita footprint MPR contra Honeywell 32332628 Issue L / Fig.10.
- [ ] Validar filtros frente a ruido real durante HIL.

### PR #7 — Z2 digital / bajo ruido
- [x] HX711 D2/D3, 10 SPS.
- [x] DFR1103 GNSS+RTC `0x66`.
- [x] I²C pull-ups 4.7 kΩ.
- [x] HMI TXU0202 y watchdog TPS3823-30.
- [x] Netlist/BOM/gates Z2.
- [x] PR #9 corrige 5V/3V3 a rails locales del shield.
- [ ] Calificar fuente/lifecycle HX711 y medir cargas reales en HIL.

### PR #8 — EU Compliance Design Gate
- [x] Frontera shield/carrier UNO Q.
- [x] Sin RF añadido por el shield base.
- [x] Matriz EMC / RoHS 3 / WEEE / RED / REACH / CE.
- [x] Gate CI y reglas EMC/ESD/retornos.
- [ ] Archivar certificados/DoC del SKU UNO Q final.
- [ ] Confirmar con laboratorio normas armonizadas y plan final de ensayos.

## Fase 3 — Arquitectura y producción de potencia

### PR #9 — Power tree y frontera UNO Q
- [x] Revisar repos oficiales Arduino/GitHub como fuente primaria.
- [x] Confirmar USB-C 5 V, VIN 7–24 V y 5 V regulados por JANALOG.
- [x] Elegir **12 V protegido → VIN** como método NFB.
- [x] Separar `5V_RAIL`/`3V3_RAIL` del host.
- [x] `IOREF` solo referencia/salida; no back-feed.
- [x] Entrada 12 V; fuente recomendada 12 V / 5 A / 60 W.
- [x] `TPS259470ARPWR` + `SMBJ15A`.
- [x] Split `12V_HOST_VIN` / `12V_LOGIC` / `12V_ACT`.
- [x] Chiller con potencia externa.
- [x] `TPSM33625RDNR` y `TLV75533PDBVR`.
- [x] Power gate + README.

### PR #10 — Esquemático de potencia de producción
- [x] Revalidar frontera UNO Q contra `arduino/docs-content`.
- [x] Congelar `J_PWR_IN = Phoenix 1757242`.
- [x] `SMBJ15A-TR` + `EEEFK1E101P`.
- [x] TPS259470A: UV/OV `470k / 11k / 47k`.
- [x] TPS259470A: `R_ILIM = 750 Ω`, `C_DVDT = 3.3 nF`, `C_ITIMER = 2.2 nF`.
- [x] `F_ACT = Littelfuse 045401.5MR`, 1.5 A Slo-Blo; HIL requerido.
- [x] TPSM33625: 1 MHz, RT→VCC, feedback `40.2k / 10k`.
- [x] TPSM33625: 4.7 µF + 100 nF entrada; 1 µF VCC; 2×22 µF + 100 nF salida; PGOOD 47 kΩ.
- [x] TLV75533: 1 µF entrada, 1 µF + 100 nF salida, `EN=5V_PGOOD`.
- [x] `hardware/power_production_netlist.json` + BOM + netclasses.
- [x] `kicad/power.kicad_sch` contractual + ERC.
- [x] Screening térmico analítico 60 °C.
- [x] Filtro LC serie abierto hasta pre-scan EMC.
- [ ] Validar DC-bias de 2×22 µF para garantizar ≥25 µF efectivos.
- [ ] Cerrar MPN exacto del capacitor dV/dt 3.3 nF en BOM release.
- [ ] Termografía/HIL a 60 °C y cargas reales antes de RC.

### PR #11 — Footprints críticos + integración eléctrica
- [x] Crear `hardware/footprint_audit.json` con gate de placement.
- [x] Auditar/corregir `Honeywell_MPR_LongPort_12Pad` contra Honeywell Issue L Fig.10.
- [x] Revisar TI `MPQF568 / RPW0010A / 4225183-A` como fuente primaria del eFuse.
- [x] Bloquear placement de `TPS259470A` hasta cerrar land pattern HotRod exacto.
- [x] Verificar RDN-11: 11 pines, 4.5 × 3.5 mm, pitch 0.5 mm.
- [x] Bloquear placement de `TPSM33625` hasta importar/verificar CAD autorizado por TI.
- [x] Crear `hardware/electrical_integration_contract.json` para Z1 + Z2 + Z3.
- [x] Congelar nets compartidas, ownership de pines UNO Q y no-backfeed.
- [x] Crear `kicad/integration_contract.kicad_sch` y CI específico.
- [x] Actualizar README.
- [ ] Cerrar footprint RPW0010A exacto antes de placement Z3.
- [ ] Cerrar footprint RDN-11 exacto antes de placement Z3.

### Integración eléctrica posterior
- [ ] Construir hoja/netlist de actuadores Insight Z4.
- [ ] Integrar root EDA final Z1 + Z2 + Z3 + Z4 con ERC = 0.
- [ ] Actualizar firmware contract cuando se ejecute migración TEMP/MPR/DFR1103.

## Fase 4 — Placement

- [ ] Z0 UNO Q bloqueado.
- [ ] Keepout RF/antena confirmado y bloqueado.
- [ ] Todos los footprints críticos requeridos en placement con auditoría `CLOSED`.
- [ ] Z1 sensores con conectores sobre `Y=0`, salida `-Y`.
- [ ] U_CO2 accesible al tubing.
- [ ] Z2 digital/bajo ruido hacia borde de servicio.
- [ ] Z3 entrada/eFuse/buck/LDO con loops mínimos y footprints auditados.
- [ ] Z4 actuadores/retornos sucios.
- [ ] TVS junto a entradas de cable.
- [ ] Revisión 3D completa.
- [ ] Congelar ancho final.

## Fase 5 — Routing

- [ ] Aplicar `hardware/power_netclasses.json` físicamente en KiCad.
- [ ] Plano de referencia continuo; In1.Cu sin señales si se congela como GND.
- [ ] Sensores → I²C/HX711 → potencia → actuadores.
- [ ] SW del buck confinado a Z3.
- [ ] No atravesar keepout RF UNO Q.
- [ ] `12V_ACT` y retorno sin cruzar Z1/Z2.
- [ ] Stitching vias/test points deliberados.
- [ ] 0 desconectados inesperados; DRC = 0.

## Fase 6 — Fabricación

- [ ] Lifecycle/disponibilidad BOM y fuentes calificadas.
- [ ] Auditoría de todos los footprints contra datasheet/CAD primario.
- [ ] Evidencia RoHS 3 / REACH de MPN, PCB y ensamblaje.
- [ ] Declaración PCB: laminado, máscara, serigrafía, ENIG.
- [ ] Declaración ensamblaje SAC305 o alternativa aprobada.
- [ ] Evidencia conformidad UNO Q archivada.
- [ ] Pre-compliance EMC/ESD/inmunidad.
- [ ] Gerbers/drill + BOM + CPL + stackup.
- [ ] Tag `v2.0-RC1` después de todos los gates.

## Fase 7 — Bring-up / HIL

- [ ] Rails sin UNO Q y encendido limitado en corriente.
- [ ] Secuencia `12V_PROTECTED → UNO Q → IOREF → 5V_RAIL → 3V3_RAIL`.
- [ ] Ausencia de back-feed con combinaciones USB/fuente principal.
- [ ] Termografía de eFuse/buck/LDO a 60 °C objetivo.
- [ ] Medir consumo ABX00173 bajo Wi‑Fi/App Lab.
- [ ] Medir inrush pump/solenoide y validar `F_ACT`.
- [ ] pH/ORP/DO, DS18B20, MPR `0x28`, DFR1103 `0x66`, HX711, HMI y watchdog.
- [ ] Pre-scan EMC con cables/actuadores representativos.
- [ ] Fixture HIL repetible de producción.
