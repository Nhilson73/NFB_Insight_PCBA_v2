# NFB Insight PCBA v2 — Auditoría de footprints críticos

**Estado vigente:** `FOOTPRINT_AUDIT_CLOSED_PR13`  
**Fuente machine-readable:** `hardware/footprint_audit.json`  
**Regla:** ningún land pattern crítico se aproxima a partir del body; se exige fuente primaria reproducible.

## Política

Para cada footprint crítico prevalece este orden: drawing/datasheet oficial del fabricante → CAD enlazado/publicado por el fabricante → documentación oficial de manufactura. Fuentes comunitarias e IA se usan únicamente como contraste.

Gemini Spark participó en PR #13 como auditor independiente y produjo coordenadas útiles para acelerar la búsqueda. **No fue autoridad de liberación.** La revisión NFB contra TI/Panasonic corrigió cuatro discrepancias antes de congelar cobre.

## Honeywell MPR — cerrado desde PR #11

`MPRLS0030PA00002A` → `NFB:Honeywell_MPR_LongPort_12Pad`.

Fuente: Honeywell `32332628 Issue L`, Figure 10. El patrón conserva 12 pads, pitch 1.27 mm y span metálico recomendado 4.20 mm.

## PR #13 — cinco cierres físicos

### TPS259470A — RPW0010A

`TPS259470ARPWR` → `NFB:TI_RPW0010A_TPS259470A`.

Fuente primaria: TI `MPQF568 / 4225183/A`, 08/2019.

Decisiones:

- VQFN-HR/HotRod, cuerpo nominal 2 × 2 mm.
- 10 números de pad lógicos.
- Los pads 1/4/7/10 son lands en **L**, materializados mediante dos primitives con el mismo número lógico.
- Los pads 5/6 son lands longitudinales.
- NSMD preferido por TI.
- stencil 0.100 mm; reducción de paste según el land-pattern/stencil example TI.

**Corrección a Spark:** su tabla rectangular de 10 filas era insuficiente para representar las cuatro geometrías HotRod en L.

### TPSM33625 — RDN0011A

`TPSM33625RDNR` → `NFB:TI_RDN0011A_TPSM33625`.

Fuente primaria: TI `qfnd871 / 4226623/F`, 09/2025.

Decisiones:

- QFN-FCMOD de 11 pines, 4.5 × 3.5 mm.
- Se usa la geometría completa de cobre del drawing TI, no una reconstrucción desde body/pitch.
- solder-mask-defined preferido por TI.
- stencil 0.125 mm.
- pads de potencia 4/5 con patrón de paste windowed, objetivo 72%.
- thermal vias son opcionales según TI y no se fijan dentro del footprint; se decidirán durante layout térmico.

**Corrección a Spark:** se rechazó la tabla simplificada de coordenadas y se congeló el land pattern completo TI.

### DRV8242H-Q1 — RHL0020B

`DRV8242HQRHLRQ1` → `NFB:TI_RHL0020B_DRV8242`.

Fuente primaria: datasheet TI DRV8242-Q1 + package drawing **`RHL0020B / 4226154/B`**, 06/2021.

Decisiones:

- 20 pads eléctricos + thermal pad 21.
- cuerpo 3.5 × 4.5 mm.
- signal lands 0.25 × 0.60 mm.
- exposed/thermal pad 21 = 2.05 × 3.05 mm.
- stencil 0.125 mm; cuatro ventanas de paste aproximan el 79% publicado.
- thermal vias no se incorporan al footprint porque TI las trata como opcionales.
- NFB conecta pad 21 a GND por desempeño térmico/EMI; no sustituye los GND eléctricos 9–12.

**Corrección a Spark:** Spark reportó `RHL0020A / 4219071/A`; el MPN seleccionado se congeló contra la revisión vigente `RHL0020B / 4226154/B`.

### TPS1HC120C-Q1 — DYC0008A

`TPS1HC120CQDYCRQ1` → `NFB:TI_DYC0008A_TPS1HC120`.

Fuente primaria: TI `MPSS142A / 4226548/B`, 12/2021.

Decisiones:

- SOT-5X3 / DYC0008A.
- **exactamente 8 pads**.
- pitch 0.5 mm.
- land 0.85 × 0.22 mm.
- **no existe exposed PowerPAD/pad 9** en este package.

**Corrección a Spark:** se eliminó el PowerPAD 9 que aparecía en su informe; no está soportado por el drawing TI.

### Panasonic AQY212EHAX — GE DIP4 surface mount

`AQY212EHAX` → `NFB:Panasonic_AQY212EHAX_DIP4_SMD`.

Fuente primaria: Panasonic Industry para el MPN exacto `AQY212EHAX`.

Decisiones:

- GE DIP4 1 Form A con terminal surface-mount.
- sufijo/packing style `X` confirmado.
- 4 pads, pitch longitudinal 2.54 mm y row spacing 8.30 mm.
- land baseline 1.50 × 1.50 mm.
- rating del componente 60 V; **contrato NFB permanece SELV ≤48 V / NO MAINS**.

La geometría propuesta por Spark se conservó únicamente después de contrastarla con la documentación Panasonic del MPN exacto.

## Gate de producción

`tools/validate_footprint_audit.py` comprueba que:

- los siete audits vigentes están autorizados;
- los cinco footprints PR #13 existen;
- no quedan placeholders `PENDING_*` en los cinco componentes críticos;
- RPW conserva sus L-lands;
- RDN conserva paste windowing;
- RHL usa revisión `0020B`, EP21 y paste segmentado;
- DYC contiene solo pads 1..8;
- AQY conserva el package exacto y la restricción SELV/no-mains;
- `.kicad_pcb` todavía no contiene estos componentes, porque PR #13 **cierra geometría, no placement**.

## Próximo gate

El siguiente paso es integrar el root EDA completo Z1 + Z2 + Z3 + Z4 con ERC = 0. Solo después se inicia placement físico y revisión 3D.
