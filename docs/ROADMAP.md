# NFB Insight PCBA v2 — Hoja de Ruta de Desarrollo

## Regla transversal

- [x] UNO Q: repos oficiales `arduino/*` en GitHub = fuente primaria.
- [x] Jerarquía en `docs/SOURCE_OF_TRUTH.md`.
- [x] No inventar land patterns; footprint crítico requiere drawing/CAD primario reproducible.
- [x] README se actualiza cuando cambia arquitectura, BOM, compliance o estado.

## Fase 0 — Arquitectura

- [x] Herencia selectiva desde Q-Shield.
- [x] UNO Q rotado, USB-C `-Y`, altura `68.58 mm`, crecimiento `+X`.
- [x] `Y=0` FIELD I/O EDGE y zonas Z0–Z4.

## Fase 1 — Mecánica UNO Q

- [x] Footprint mecánico, agujeros y referencias UNO Q.
- [x] Contorno inicial `68.58 × 220 mm` provisional.
- [x] DRC/validación mecánica automática.
- [ ] Keepouts definitivos CAD/STEP/enclosure.
- [ ] Keepout RF/antena confirmado contra Arduino oficial.
- [ ] Revisión 3D y ancho final después del placement.

## Fase 2 — Arquitectura eléctrica Insight

### PR #3–#7 — contratos Z0/Z1/Z2
- [x] 32 pads UNO Q + snapshot firmware.
- [x] Interfaces reales pH/ORP/DO, TEMP DS18B20, MPR `0x28`.
- [x] Z1 netlist/BOM/gates.
- [x] Z2 HX711, DFR1103 `0x66`, HMI TXU0202, watchdog.
- [x] A4 reutilizado en PR #12 como `PUMP_CURRENT_ADC`; `CO2_ADC` continúa prohibido.

### PR #8 — EU Compliance Design Gate
- [x] Frontera shield/carrier y RF UNO Q preservada.
- [x] EMC / RoHS 3 / WEEE / RED / REACH / CE.
- [x] CI para GND, ESD, ruido, RF keepout y evidencia.
- [ ] Archivar certificados/DoC del SKU UNO Q final.
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

### PR #11 — auditoría/integración inicial
- [x] `hardware/footprint_audit.json`.
- [x] MPR cerrado contra Honeywell.
- [x] Contrato de integración Z1/Z2/Z3 y CI.

### PR #12 — Z4 actuadores
- [x] Bomba `DRV8242HQRHLRQ1`, D5/D6, IPROPI→A4.
- [x] Solenoide `TPS1HC120CQDYCRQ1`, D7, ILIM ~0.5 A.
- [x] Chiller `AQY212EHAX`, dry contact SELV ≤48 V / NO MAINS.
- [x] D10=`ACT_FAULT_N` wired-OR.
- [x] Netlist/BOM/contrato/gates Z4.
- [ ] Migrar firmware A4/D10.

### PR #13 — cierre de footprints críticos
- [x] Spark como cross-check independiente, no autoridad.
- [x] RPW0010A HotRod — TI `4225183/A`.
- [x] RDN0011A — TI `4226623/F`.
- [x] DRV8242 package vigente RHL0020B — TI `4226154/B`.
- [x] DYC0008A — TI `4226548/B`, 8 pads sin PowerPAD.
- [x] AQY212EHAX surface-mount — Panasonic exacto.
- [x] BOM/netlists sin placeholders críticos.
- [x] 9/9 gates verdes; sin placement/routing.

### PR #14 — root EDA inter-zona
- [x] Separar el antiguo contrato textual Z1 a `kicad/z1_sensor_contract.kicad_sch`.
- [x] Crear child interfaces Z0/Z1/Z2/Z3/Z4 con `hierarchical_label`.
- [x] Convertir `kicad/NFB_Insight_PCBA_v2.kicad_sch` en root jerárquico real.
- [x] Congelar `hardware/root_eda_contract.json`.
- [x] GND común Z0–Z4; 3V3/5V locales excluyen Z0.
- [x] I²C Z0/Z1/Z2; `12V_ACT` Z3/Z4; controles/diagnóstico Z0/Z4.
- [x] Gate `tools/validate_root_eda.py` + workflow root.
- [x] Mantener `zone_internal_component_symbols=false`: no duplicar manualmente >100 refs.
- [x] Congelar deuda ERC intencional de interfaz: exactamente 125 `label_dangling`, cero tipos inesperados y sin bajar severidades KiCad.
- [ ] CI PR #14 totalmente verde y merge.

### PR #15 — materialización interna de símbolos de producción
- [ ] Crear/generar símbolos y conectividad interna Z1 desde `z1_production_netlist.json` + BOM.
- [ ] Crear/generar símbolos y conectividad interna Z2 desde `z2_production_netlist.json` + BOM.
- [ ] Crear/generar símbolos y conectividad interna Z3 desde `power_production_netlist.json` + BOM.
- [ ] Crear/generar símbolos y conectividad interna Z4 desde `z4_production_netlist.json` + BOM.
- [ ] Paridad refs/pines/nets/footprints JSON↔KiCad.
- [ ] Eliminar completamente la deuda ERC PR #14.
- [ ] ERC = 0 del hierarchy completo.
- [ ] Mantener placement/routing fuera de alcance hasta cerrar paridad.

## Fase 4 — Placement

- [ ] Z0 UNO Q bloqueado + keepout RF confirmado.
- [x] MPR + cinco footprints críticos PR #13 cerrados.
- [ ] Todos los símbolos internos de producción materializados y paridad EDA cerrada.
- [ ] Auditar footprints restantes de riesgo antes de colocarlos.
- [ ] Z1/Z2 conectores hacia `Y=0/-Y`.
- [ ] Z3 loops de potencia mínimos.
- [ ] Z4 drivers/conectores/retornos sucios junto al borde de campo.
- [ ] PhotoMOS SELV deliberado; nunca mains.
- [ ] Revisión 3D y ancho final.

## Fase 5 — Routing

- [ ] Aplicar netclasses reales.
- [ ] Plano de referencia continuo; In1.Cu GND si se congela así.
- [ ] No cruzar RF keepout.
- [ ] SW buck confinado Z3.
- [ ] `PUMP_CURRENT_ADC` lejos de switching.
- [ ] Retornos `12V_ACT` a estrella sin atravesar Z1/Z2.
- [ ] DRC=0; 0 desconectados inesperados.

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
