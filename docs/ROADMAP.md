# NFB Insight PCBA v2 — Hoja de Ruta de Desarrollo

## Regla transversal

- [x] UNO Q: repos oficiales `arduino/*` en GitHub = fuente primaria.
- [x] Jerarquía en `docs/SOURCE_OF_TRUTH.md`.
- [x] No inventar land patterns ni keepouts RF no publicados.
- [x] README se actualiza cuando cambia arquitectura, BOM, compliance o estado.
- [x] JSON/BOM permanecen como autoridad eléctrica; KiCad generado es reproducible semánticamente.

## Fase 0 — Arquitectura

- [x] Herencia selectiva desde Q-Shield.
- [x] UNO Q rotado, USB-C `-Y`, altura `68.58 mm`, crecimiento `+X`.
- [x] `Y=0` FIELD I/O EDGE y zonas Z0–Z4.

## Fase 1 — Mecánica UNO Q

- [x] Footprint mecánico, agujeros y referencias UNO Q.
- [x] Contorno inicial `68.58 × 220 mm` provisional.
- [x] DRC/validación mecánica automática.
- [x] PR #16: Z0 completo congelado como host envelope sin footprints NFB.
- [x] PR #16: fuente Arduino revalidada; no se inventa antenna keepout numérico ausente de fuente primaria.
- [x] PR #17: ancho final de placement congelado en `242.34 mm` por courtyards reales.
- [ ] Revisión 3D/enclosure y región RF del host después del routing preliminar.

## Fase 2 — Arquitectura eléctrica Insight

### PR #3–#7 — contratos Z0/Z1/Z2
- [x] 32 pads UNO Q + snapshot firmware.
- [x] Interfaces reales pH/ORP/DO, TEMP DS18B20, MPR `0x28`.
- [x] Z1 netlist/BOM/gates.
- [x] Z2 HX711, DFR1103 `0x66`, HMI TXU0202, watchdog.
- [x] A4=`PUMP_CURRENT_ADC`; `CO2_ADC` continúa prohibido.

### PR #8 — EU Compliance Design Gate
- [x] Frontera shield/carrier y RF UNO Q preservada.
- [x] EMC / RoHS 3 / WEEE / RED / REACH / CE.
- [x] CI para GND, ESD, ruido, RF y evidencia.
- [ ] Archivar certificados/DoC del SKU UNO Q final en expediente release.
- [ ] Confirmar normas/plan de laboratorio final.

## Fase 3 — Potencia, actuadores e integración EDA

### PR #9 / PR #10 — potencia de producción
- [x] PR #9: 12 V protegido → VIN UNO Q.
- [x] PR #9: rails locales 5 V / 3.3 V sin back-feed.
- [x] PR #10: `TPS259470ARPWR` + `SMBJ15A`.
- [x] PR #10: `TPSM33625RDNR` 1 MHz + `TLV75533PDBVR`.
- [x] PR #10: `12V_HOST_VIN / 12V_LOGIC / 12V_ACT`; chiller power externa.
- [x] PR #10: netlist/BOM/netclasses/`power.kicad_sch` + ERC.
- [ ] DC-bias efectivo 2×22 µF ≥25 µF.
- [ ] HIL/termografía 60 °C e inrush `F_ACT`.

### PR #11 / #12 — integración + Z4
- [x] Audit machine-readable de footprints.
- [x] Bomba `DRV8242HQRHLRQ1`, D5/D6, IPROPI→A4.
- [x] Solenoide `TPS1HC120CQDYCRQ1`, D7, ILIM ~0.5 A.
- [x] Chiller `AQY212EHAX`, dry contact SELV ≤48 V / NO MAINS.
- [x] D10=`ACT_FAULT_N`.
- [ ] Migrar firmware A4/D10.

### PR #13 — cierre de footprints críticos
- [x] Spark como cross-check independiente, no autoridad.
- [x] RPW0010A — TI `4225183/A`.
- [x] RDN0011A — TI `4226623/F`.
- [x] RHL0020B — TI `4226154/B`.
- [x] DYC0008A — TI `4226548/B`, 8 pads sin PowerPAD.
- [x] AQY212EHAX SMD — Panasonic exacto.
- [x] 9/9 gates verdes; sin placement/routing.

### PR #14 — root EDA inter-zona
- [x] Root Z0–Z4 real.
- [x] GND Z0–Z4; 3V3/5V locales excluyen Z0.
- [x] I²C Z0/Z1/Z2; `12V_ACT` Z3/Z4; controles Z0/Z4.
- [x] Deuda transitoria controlada 125 `label_dangling`.
- [x] 11/11 gates verdes y merge.

### PR #15 — hierarchy de producción
- [x] Z0–Z4 generados desde pin-contract/netlists/BOM.
- [x] UUIDs deterministas + `NFB_GEN`.
- [x] Paridad refs/pines/nets/footprints JSON↔BOM↔KiCad.
- [x] TXU0202/DCU0008A, Phoenix 1757242 y Littelfuse 045401.5MR cerrados.
- [x] Deuda PR #14 eliminada.
- [x] KiCad 10.0.5: **ERC 0 Errors / 0 Warnings**.
- [x] Placement/routing permanecieron en cero.

## Fase 4 — Placement

### PR #16 — pre-placement readiness
- [x] Revalidar `arduino/docs-content` actual antes del placement.
- [x] Snapshot PR16: `24445a32e249d410c1e4359bdc99d8c0dcb17bd2`.
- [x] Confirmar WCBN3536A/WCN3980 + shared PCB antenna.
- [x] No inventar antenna keepout numérico no publicado.
- [x] Z0 `0…53.34 × 0…68.58 mm` prohibido para production footprints NFB.
- [x] Z1 quiet inmediatamente adyacente; Z3/Z4 ruidosos desplazados a +X.
- [x] Congelar `In1.Cu` como plano GND continuo / no signal routing.
- [x] Congelar orden FIELD I/O izquierda→derecha.
- [x] Cerrar `J_LOADCELL` a Phoenix Contact `1757268` / 5.08 mm.
- [x] Congelar reglas ESD/analog/HX711/HMI/power/actuator proximity.
- [x] `hardware/placement_readiness_contract.json` + CI.
- [x] Mantener production placement=0 y routing=0 durante PR16.
- [x] Full CI PR #16 + merge.

### PR #17 — placement físico
- [x] Colocar Z1 FIELD I/O y front-ends por courtyards reales.
- [x] Colocar Z2 load-cell/GNSS/HMI respetando gradiente quiet→power.
- [x] Colocar Z3 power-entry/eFuse/buck/LDO con loops de placement compactos.
- [x] Colocar Z4 drivers/bulk/conectores junto al FIELD I/O EDGE.
- [x] Mantener Z0 inmutable y libre de production footprints NFB.
- [x] Ajustar ancho exclusivamente hacia +X: `242.34 mm` final de placement.
- [x] Test points accesibles en banda superior.
- [x] Courtyard overlaps = 0; sin shorts/clearance físicos de placement.
- [x] Corrección Honeywell MPR y regla local TPSM33625 verificadas.
- [x] **Routing continuó prohibido: 0 tracks / 0 vías / 0 zones.**
- [x] PR #17 mergeado; layout revisado visualmente antes de seguir.
- [ ] Revisión 3D/enclosure/RF del conjunto físico.

## Fase 5 — Routing

### PR #18 — routing readiness / contrato de cobre
- [x] Congelar board y placement PR17: `242.34 × 68.58 mm`.
- [x] Clasificar exactamente 59/59 nets de producción una sola vez.
- [x] Mantener mínimos de potencia PR10 sin debilitarlos.
- [x] `In1.Cu` = GND continuo; signal routing prohibido.
- [x] `In2.Cu` reservado a distribución de potencia/retornos controlados.
- [x] Congelar analógica sensible: pH/ORP/DO, load-cell/HX711 y `PUMP_CURRENT_ADC`.
- [x] Congelar dirty nets: `12V_ACT`, `PUMP_OUT1/2`, `CO2_SOL_POS`.
- [x] Separación contractual sensitive↔dirty ≥ `1.00 mm` en recorridos paralelos.
- [x] Chiller dry-contact: SELV ≤48 V / NO MAINS / sin tie a GND.
- [x] Prohibir `SW`, `CO2_ADC`, `TEMP_ADC`, `HUM_ADC`, `CO2_PWM`, `CO2_FLOW_PWM`, `RS485_IRQ_RSVD`.
- [x] CI PR18 exige 0 tracks / 0 vías / 0 copper zones.
- [ ] Full CI PR #18 + merge.

### PR #19 — routing físico de producción
- [ ] Aplicar clases/anchos/clearances PR18.
- [ ] Rutear power-entry/eFuse/buck/LDO localmente en Z3.
- [ ] Rutear `12V_ACT` y salidas de actuadores confinadas Z3/Z4.
- [ ] Rutear Z1 front-end con trayectos mínimos antes de acondicionamiento.
- [ ] Rutear load-cell/HX711 quieto y HMI/I²C/low-speed en corredor controlado.
- [ ] Rutear `PUMP_CURRENT_ADC` por corredor silencioso Z4→Z0, lejos de Z3 switching.
- [ ] Mantener `In1.Cu` sin pistas y como referencia GND continua.
- [ ] Añadir distribución `In2.Cu`/stitching sin crear retornos por Z1/Z2.
- [ ] No cruzar región RF del host con loops ruidosos; escapes Z0 mínimos.
- [ ] DRC de cobre = 0; unconnected = 0 esperado al cierre.
- [ ] Revisar retorno/EMC y preparar revisión 3D/RF posterior.

## Fase 6 — Fabricación / compliance

- [ ] Lifecycle y fuentes calificadas.
- [ ] Todos los footprints auditados en release BOM/CPL.
- [ ] RoHS3/REACH PCB+BOM+ensamblaje.
- [ ] Evidencia UNO Q archivada.
- [ ] Pre-compliance EMC/ESD/inmunidad.
- [ ] Gerbers/drill + BOM + CPL + stackup.
- [ ] Tag `v2.0-RC1` tras gates.

## Fase 7 — Bring-up / HIL

- [ ] Rails, secuencia y ausencia de back-feed.
- [ ] Termografía 60 °C.
- [ ] Sensores Z1 + Z2.
- [ ] Bomba PWM/DIR/IPROPI/stall/inrush/fault.
- [ ] Solenoide current/open-load/fault/clamp.
- [ ] Chiller dry contact SELV/fail-safe.
- [ ] D10 `ACT_FAULT_N` y firmware failsafe.
- [ ] Pre-scan EMC con cables/actuadores reales.
- [ ] Fixture HIL repetible.
