# PR #13 — Cierre de footprints críticos antes de placement

**Estado:** baseline físico previo a integración EDA raíz.  
**Fuente machine-readable:** `hardware/footprint_audit.json`.

## Objetivo

Eliminar los placeholders físicos que bloqueaban Z3/Z4 sin adelantar placement ni routing. Cada land pattern se congela únicamente cuando una fuente primaria permite reproducir cobre, máscara/paste y orientación con suficiente precisión.

## Auditor independiente: Gemini Spark

Se proporcionó a Gemini Spark un brief específico con la regla **NO INVENTAR LAND PATTERNS**. Spark devolvió un informe y coordenadas para cinco componentes, todos marcados por Spark como `CLOSED_PRIMARY_SOURCE`.

NFB utilizó esa salida solo como cross-check. Las decisiones finales se tomaron contra TI/Panasonic oficiales. La revisión secundaria fue útil porque reveló exactamente dónde era necesario revisar con mayor profundidad.

### Correcciones realizadas a la salida Spark

1. **TPS259470A / RPW0010A:** Spark representó los diez pads como rectángulos independientes. El drawing TI muestra cuatro lands HotRod en L; PR #13 los materializa con primitives múltiples bajo los mismos números lógicos 1/4/7/10.
2. **TPSM33625 / RDN0011A:** se reemplazó la tabla simplificada por la geometría completa de `4226623/F`, incluyendo mask/paste del fabricante.
3. **DRV8242HQRHLRQ1:** Spark utilizó `RHL0020A / 4219071/A`. El MPN de producción se congeló contra **`RHL0020B / 4226154/B`**.
4. **TPS1HC120CQDYCRQ1 / DYC0008A:** Spark reportó un PowerPAD 9. El drawing TI `4226548/B` define exactamente ocho pads; PR #13 no crea pad 9.
5. **AQY212EHAX:** la geometría de Spark se aceptó solo después de confirmar el MPN exacto y su terminal surface-mount en Panasonic.

## Footprints congelados

### U_EFUSE — TPS259470ARPWR

Footprint: `NFB:TI_RPW0010A_TPS259470A`.

Fuente: Texas Instruments `MPQF568 / RPW0010A / 4225183/A`.

Características:
- VQFN-HR HotRod;
- 10 pads lógicos;
- lands en L: 1/4/7/10;
- lands longitudinales 5/6;
- NSMD preferido;
- stencil 0.100 mm;
- paste reducido en lands específicos según ejemplo TI.

### U_5V — TPSM33625RDNR

Footprint: `NFB:TI_RDN0011A_TPSM33625`.

Fuente: Texas Instruments `qfnd871 / RDN0011A / 4226623/F`.

Características:
- QFN-FCMOD 11 pines;
- 4.5 × 3.5 mm;
- geometría de cobre completa del drawing TI;
- solder-mask-defined preferido;
- stencil 0.125 mm;
- windowing de paste para pads de potencia 4/5, objetivo 72%;
- thermal vias opcionales: no se bloquean dentro del footprint.

### U_PUMP_DRV — DRV8242HQRHLRQ1

Footprint: `NFB:TI_RHL0020B_DRV8242`.

Fuente: Texas Instruments DRV8242-Q1 + `RHL0020B / 4226154/B`.

Características:
- 20 pines eléctricos + thermal pad 21;
- 3.5 × 4.5 mm;
- signal lands 0.25 × 0.60 mm;
- EP21 2.05 × 3.05 mm;
- stencil 0.125 mm;
- cuatro ventanas de paste sobre EP, aproximando el 79% publicado;
- thermal vias opcionales, a resolver en layout.

NFB conecta pad 21 a `GND` por desempeño térmico/EMI. Los pines GND eléctricos 9–12 permanecen obligatorios.

### U_CO2_DRV — TPS1HC120CQDYCRQ1

Footprint: `NFB:TI_DYC0008A_TPS1HC120`.

Fuente: Texas Instruments `MPSS142A / DYC0008A / 4226548/B`.

Características:
- SOT-5X3;
- 8 pads exclusivamente;
- pitch 0.5 mm;
- land 0.85 × 0.22 mm;
- sin exposed pad / sin pad 9.

### U_CHILLER — AQY212EHAX

Footprint: `NFB:Panasonic_AQY212EHAX_DIP4_SMD`.

Fuente: Panasonic Industry, MPN exacto `AQY212EHAX`.

Características:
- GE DIP4 1 Form A;
- surface-mount terminal;
- packing style `X`;
- 4 pads;
- pin pitch 2.54 mm;
- row spacing 8.30 mm;
- land baseline 1.50 × 1.50 mm.

La restricción de sistema NFB sigue siendo **dry contact SELV ≤48 V / NO MAINS**.

## Cambios de contratos

- `hardware/footprint_audit.json` → schema 3 / `FOOTPRINT_AUDIT_CLOSED_PR13`.
- `hardware/power_production_netlist.json` → schema 2 / footprints RPW y RDN reales.
- `hardware/z4_production_netlist.json` → schema 2 / RHL, DYC y AQY reales.
- BOM Z3/Z4 elimina los cinco tokens `PENDING_*`.
- `U_PUMP_DRV.21` se incorpora a `GND` en el netlist Z4.

## Lo que PR #13 NO hace

- no modifica `.kicad_pcb`;
- no asigna XY;
- no rutea;
- no congela ancho final;
- no decide thermal vias opcionales RDN/RHL;
- no reemplaza HIL/termografía/EMC pre-scan.

## Gate de aceptación

PR #13 requiere:

- los cinco audits en estado `CLOSED_PRIMARY_SOURCE_PR13`;
- footprints custom presentes;
- BOM/netlist apuntando a esos footprints;
- ningún placeholder crítico;
- checks geométricos específicos por package;
- integración Z1/Z2/Z3/Z4 coherente;
- ERC existente sin regresiones;
- `.kicad_pcb` sin placement de los cinco componentes.

## Siguiente PR

**PR #14 — integración EDA raíz de producción**: materializar Z1 + Z2 + Z3 + Z4 bajo una jerarquía KiCad real, cruzada contra los contratos JSON/BOM y con ERC = 0 antes de iniciar placement.
