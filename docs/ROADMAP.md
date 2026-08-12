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

### PR #3 — contrato UNO Q
- [x] 32 pads machine-readable + ERC + snapshot firmware.

### PR #4/#5 — donante e interfaces reales
- [x] Trazabilidad analog donor.
- [x] pH/ORP/DO acondicionados; TEMP DS18B20; humedad eliminada.

### PR #6 — Z1
- [x] MPR `0x28`; CO2 pressure retirado de A4.
- [x] ESD/filtros/JST/pull-up TEMP + netlist/BOM/gates.
- [x] PR #11 cerró footprint MPR Honeywell Issue L.
- [x] PR #12 reutiliza A4 exclusivamente como `PUMP_CURRENT_ADC`; `CO2_ADC` sigue prohibido.
- [ ] Validar ruido/filtros durante HIL.

### PR #7 — Z2
- [x] HX711 D2/D3, DFR1103 `0x66`, I²C 4.7 kΩ.
- [x] HMI TXU0202 + watchdog TPS3823-30.
- [x] Netlist/BOM/gates.
- [ ] Calificar fuente/lifecycle HX711 y cargas reales HIL.

### PR #8 — EU Compliance Design Gate
- [x] Frontera shield/carrier UNO Q y RF host preservada.
- [x] EMC / RoHS 3 / WEEE / RED / REACH / CE.
- [x] CI y reglas de plano GND, ESD, ruido, retornos.
- [ ] Archivar certificados/DoC SKU UNO Q final.
- [ ] Confirmar normas/plan de laboratorio final.

## Fase 3 — Potencia e integración eléctrica

### PR #9 — power tree
- [x] Arduino/GitHub revalidado.
- [x] 12 V protegido -> VIN UNO Q.
- [x] Rails locales `5V_RAIL` / `3V3_RAIL` sin back-feed.
- [x] `TPS259470ARPWR`, `SMBJ15A`, `TPSM33625RDNR`, `TLV75533PDBVR`.
- [x] Split `12V_HOST_VIN / 12V_LOGIC / 12V_ACT`; chiller potencia externa.

### PR #10 — potencia de producción
- [x] Phoenix 1757242, SMBJ15A-TR, bulk 100 µF.
- [x] eFuse: `470k/11k/47k`, `R_ILIM=750 Ω`, `C_DVDT=3.3 nF`, `C_ITIMER=2.2 nF`.
- [x] `F_ACT=045401.5MR` 1.5 A Slo-Blo.
- [x] TPSM33625 1 MHz, `40.2k/10k`, capacitores/PGOOD.
- [x] TLV75533 1 µF/1 µF, EN por PGOOD.
- [x] Netlist/BOM/netclasses + `power.kicad_sch` + ERC.
- [ ] DC-bias efectivo de 2×22 µF ≥25 µF.
- [ ] Termografía/HIL 60 °C y validar `F_ACT` con inrush real.

### PR #11 — footprints + integración Z1/Z2/Z3
- [x] `hardware/footprint_audit.json` y gate de placement.
- [x] MPR CLOSED.
- [x] RPW0010A y RDN-11 identificados y bloqueados hasta CAD exacto.
- [x] `electrical_integration_contract.json` + hoja/CI integración.

### PR #12 — Z4 actuadores
- [x] Revalidar UNO Q 3.3-V MCU I/O contra `arduino/docs-content` actual.
- [x] Bomba: `DRV8242HQRHLRQ1`, PH/EN D5/D6, reemplaza IR2104/IRLZ44N.
- [x] `IPROPI -> A4/PUMP_CURRENT_ADC`, 1.5 kΩ + 100 nF.
- [x] Solenoide CO₂: `TPS1HC120CQDYCRQ1`, D7, ILIM 27 kΩ ~0.5 A, clamp integrado.
- [x] Chiller: `AQY212EHAX` + `2N7002,215`, dry contact aislado **SELV <=48 V / NO MAINS**.
- [x] D10=`ACT_FAULT_N` wired-OR bomba + solenoide; deja reserva RS485.
- [x] Fail-safe pull-downs en PWM/DIR/solenoide/chiller.
- [x] Netlist/BOM/hoja Z4 + gate numérico/CI.
- [x] Integración global extendida a Z4 y audit extendido a RHL20/DYC8/AQY.
- [ ] Cerrar footprints RHL20, DYC8 y AQY antes de placement.
- [ ] Migrar firmware para A4 current diagnostic y D10 fault.

### PR #13 — cierre de footprints críticos
- [ ] Cerrar RPW0010A exacto contra TI.
- [ ] Cerrar RDN-11 exacto contra CAD autorizado TI.
- [ ] Cerrar RHL20 DRV8242 contra TI.
- [ ] Cerrar DYC8 TPS1HC120 contra TI.
- [ ] Cerrar AQY212EHAX DIP4 SMD contra Panasonic.
- [ ] Auditar conectores/footprints restantes de alto riesgo.

### Integración EDA final
- [ ] Root real Z1+Z2+Z3+Z4 con símbolos/netlist de producción.
- [ ] ERC = 0 y contratos JSON↔EDA coherentes.

## Fase 4 — Placement

- [ ] Z0 UNO Q bloqueado + keepout RF confirmado.
- [ ] Todos los footprints requeridos `CLOSED`.
- [ ] Z1/Z2 conectores hacia `Y=0/-Y`.
- [ ] Z3 loops potencia mínimos.
- [ ] Z4 drivers/conectores/retornos sucios junto al borde de campo.
- [ ] PhotoMOS clearance SELV deliberado; nunca mains.
- [ ] Revisión 3D y ancho final.

## Fase 5 — Routing

- [ ] Aplicar netclasses reales.
- [ ] Plano referencia continuo; In1.Cu GND si se congela así.
- [ ] No cruzar keepout RF.
- [ ] SW buck confinado Z3.
- [ ] `PUMP_CURRENT_ADC` lejos de switching y referenciado a GND.
- [ ] Retornos `12V_ACT` a estrella sin atravesar Z1/Z2.
- [ ] DRC=0; 0 desconectados inesperados.

## Fase 6 — Fabricación / compliance

- [ ] Lifecycle y fuentes calificadas.
- [ ] Todos los footprints auditados.
- [ ] RoHS3/REACH de BOM, PCB y ensamblaje.
- [ ] Evidencia UNO Q archivada.
- [ ] Pre-compliance EMC/ESD/inmunidad.
- [ ] Gerbers/drill + BOM + CPL + stackup.
- [ ] `v2.0-RC1` tras gates.

## Fase 7 — Bring-up / HIL

- [ ] Rails, secuencia y ausencia de back-feed.
- [ ] Termografía a 60 °C.
- [ ] Sensores Z1 + Z2.
- [ ] Bomba: PWM/DIR, corriente IPROPI, stall/inrush/fault.
- [ ] Solenoide: corriente, open-load, fault y clamp.
- [ ] Chiller: contacto seco aislado SELV y fail-safe.
- [ ] D10 `ACT_FAULT_N` y firmware failsafe.
- [ ] Pre-scan EMC con cables/actuadores reales.
- [ ] Fixture HIL repetible de producción.
