# NFB Insight PCBA v2

PCBA **shield/carrier** para **Nebula Fermentation Insight®**, diseñada alrededor del factor de forma inmutable del **Arduino UNO Q**. El repositorio `Nhilson73/nebula_qshield_pcb` se conserva únicamente como donante de ingeniería y trazabilidad; no gobierna placement, routing ni topología de producción V2.

## Fuente primaria UNO Q

Toda decisión dependiente del **Arduino UNO Q** se contrasta primero contra los repositorios oficiales de Arduino en GitHub:

- `https://github.com/Arduino`
- `https://github.com/orgs/arduino/repositories`
- especialmente `arduino/docs-content` y repos oficiales UNO Q aplicables.

Después se contrastan `docs.arduino.cc` y datasheets/PDF oficiales. La jerarquía está en `docs/SOURCE_OF_TRUTH.md` y es obligatoria para pinout, potencia, mecánica, firmware, RF e interfaces.

## Frontera del producto / compliance

NFB Insight PCBA v2 es un **shield/carrier del Arduino UNO Q**, no un rediseño de su plataforma radio.

- UNO Q aporta computación, MCU y Wi‑Fi/Bluetooth.
- El shield base no añade transmisores, antenas, matching ni amplificación RF.
- Se preservarán keepouts y condiciones RF del UNO Q.
- El **EU Compliance Design Gate** vive en `docs/EU_COMPLIANCE_GATE.md` y `compliance/eu_compliance_contract.json`.
- La evidencia regulatoria del host no sustituye la calificación EMC/RoHS3/REACH/WEEE/CE del shield y del producto integrado.

## Mecánica congelada

- UNO Q rotado, origen global `(0,0)`, USB‑C hacia `-Y`.
- Envolvente UNO Q: `53.34 × 68.58 mm`.
- Altura PCB fija: `68.58 mm`; crecimiento solo `+X`.
- `Y=0` = FIELD I/O EDGE.
- Gradiente: Z0 UNO Q → Z1 sensores → Z2 digital → Z3 potencia → Z4 actuadores.
- Ancho actual `220 mm` **provisional** hasta placement.

## Z1 sensores — PR #6 / #9 / #11 / #12

Fuentes: `hardware/sensor_interface_contract.json`, `hardware/z1_production_netlist.json`, `bom/insight_z1_production_bom.csv`.

- pH/A0 y DO/A5: 0–3 V acondicionados, ESD + `1 kΩ / 100 nF`.
- ORP/A1: divisor `10 kΩ / 20 kΩ`, máximo 3.0 V.
- TEMP/A2-D16: DS18B20 `TEMP_1WIRE`, pull-up 4.7 kΩ.
- CO₂ pressure: Honeywell `MPRLS0030PA00002A`, I²C `0x28`; **CO2_ADC permanece retirado**.
- PR #11 cerró el footprint MPR contra Honeywell `32332628 Issue L / Fig.10`.
- PR #12 reutiliza A4/pad13 como `PUMP_CURRENT_ADC` desde IPROPI del driver de bomba.

## Z2 digital / bajo ruido — PR #7 / #9

- I²C 3.3 V con pull-ups 4.7 kΩ; MPR `0x28` + DFR1103 `0x66`.
- HX711 3.3 V, 10 SPS, D2/D3.
- HMI D0/D1 mediante `TXU0202DCUR`.
- Watchdog `TPS3823-30DBVR`, WDI=D4.
- GPS/RTC legacy separados y RS485 Signature quedan fuera del baseline Insight.

## Z3 potencia — PR #9 / #10 / #13

Fuentes: `hardware/power_architecture_contract.json`, `hardware/power_production_netlist.json`, `bom/insight_power_production_bom.csv`, `hardware/power_netclasses.json`, `kicad/power.kicad_sch`.

- Entrada nominal **12 VDC**; fuente recomendada **12 V / 5 A / 60 W** certificada.
- NFB alimenta UNO Q por **12 V protegido → VIN**.
- `5V_RAIL` y `3V3_RAIL` son rails locales del shield y no se unen a J_UNOQ.5/J_UNOQ.4.
- Protección: `SMBJ15A-TR` + `TPS259470ARPWR`.
- eFuse: ladder UV/OV `470 kΩ / 11 kΩ / 47 kΩ`, `R_ILIM=750 Ω`, `C_DVDT=3.3 nF`, `C_ITIMER=2.2 nF`.
- Split: `12V_HOST_VIN`, `12V_LOGIC`, `12V_ACT`; `F_ACT=045401.5MR` 1.5 A Slo-Blo.
- 5 V: `TPSM33625RDNR`, 1 MHz, feedback `40.2 kΩ / 10 kΩ`.
- 3.3 V: `TLV75533PDBVR`.
- Chiller no toma potencia de la PCBA.
- PR #13 sustituye los placeholders físicos de `U_EFUSE` y `U_5V` por footprints auditados contra drawings TI.

## Cierre de footprints críticos — PR #13

Fuente machine-readable: `hardware/footprint_audit.json`. Detalle: `docs/FASE3_PR13_FOOTPRINT_CLOSURE.md`.

Se materializaron y congelaron cinco land patterns críticos:

- `U_EFUSE` → `NFB:TI_RPW0010A_TPS259470A` — HotRod VQFN-HR `RPW0010A`, TI `MPQF568 / 4225183/A`.
- `U_5V` → `NFB:TI_RDN0011A_TPSM33625` — QFN-FCMOD `RDN0011A`, TI `qfnd871 / 4226623/F`.
- `U_PUMP_DRV` → `NFB:TI_RHL0020B_DRV8242` — VQFN `RHL0020B`, TI `4226154/B`, con thermal pad 21.
- `U_CO2_DRV` → `NFB:TI_DYC0008A_TPS1HC120` — `DYC0008A`, TI `MPSS142A / 4226548/B`, exactamente 8 pads y **sin PowerPAD**.
- `U_CHILLER` → `NFB:Panasonic_AQY212EHAX_DIP4_SMD` — Panasonic GE DIP4 surface-mount del MPN exacto `AQY212EHAX`.

Gemini Spark se utilizó como **auditor independiente/cross-check**. Sus resultados no son fuente de verdad. La revisión NFB contra TI/Panasonic corrigió geometrías simplificadas del RPW/RDN, la revisión de package del DRV8242 y un PowerPAD inexistente reportado para DYC-8.

El gate PR #13 exige fuentes primarias, prohíbe placeholders críticos y bloquea cambios silenciosos de geometría.

## Z4 actuadores — PR #12 / footprints PR #13

Fuentes: `hardware/z4_actuator_contract.json`, `hardware/z4_production_netlist.json`, `bom/insight_z4_production_bom.csv`, `kicad/z4_actuators.kicad_sch`, `docs/Z4_ACTUATORS.md`.

### Bomba

- Driver **TI `DRV8242HQRHLRQ1`**, H-bridge automotriz integrado; sustituye `IR2104 + IRLZ44N`.
- D5=`PUMP_PWM`, D6=`PUMP_DIR`, modo PH/EN.
- SR=22 kΩ para limitar slew/EMI; 100 nF + 22 µF local en `12V_ACT`.
- IPROPI + `1.5 kΩ / 100 nF` → **A4=`PUMP_CURRENT_ADC`**.
- ~0.842 V esperados a 0.8 A típico; margen ADC hasta ~2.75 A usando el factor mínimo contractual.
- PR #13 usa el package actual `RHL0020B`; thermal pad 21 se conecta a GND por decisión de ingeniería NFB para desempeño térmico/EMI, sin sustituir los pines GND eléctricos 9–12.

### Solenoide CO₂

- Driver **TI `TPS1HC120CQDYCRQ1`**, smart high-side protegido.
- D7=`CO2_SOL_CTL`.
- `R_ILIM=27 kΩ` → límite objetivo ~0.5 A.
- Clamp inductivo integrado; no se puebla flyback discreto legacy.
- FLT1 comparte diagnóstico común; FLT2 queda como `CO2_OPENLOAD_N`.

### Chiller

- D8 controla **Panasonic `AQY212EHAX` PhotoMOS** mediante `2N7002,215`.
- Salida = **contacto seco aislado**, separado de GND/rails del shield.
- Uso contractual **SELV ≤48 V exclusivamente; NO MAINS**.
- La potencia del chiller permanece externa.

### Diagnóstico

- **D10/pad25 = `ACT_FAULT_N`**, active-low wired-OR de bomba + solenoide.
- D10 deja de ser reserva RS485 en Insight.
- D9 continúa DNP/Reserva.

## Estado

Z0 mecánico, Z1, Z2, Z3, Z4, EU Compliance y los **cinco footprints críticos del PR #13** están contractualmente definidos. El `.kicad_pcb` todavía no recibe placement de estos bloques: PR #13 cierra geometría física, no coordenadas XY.

El siguiente frente es **PR #14 — integración EDA raíz Z1 + Z2 + Z3 + Z4 con ERC = 0**. Después de esa jerarquía integrada se habilitará el placement por zonas, la revisión 3D y el congelamiento del ancho final del PCB.
