# NFB Insight PCBA v2 — Auditoría de Footprints PR #11 / extensión PR #12

**Fuente machine-readable:** `hardware/footprint_audit.json`  
**Regla:** ningún componente con auditoría abierta puede colocarse en el PCB.

## Principio

No se aproximarán land patterns a partir del tamaño exterior del encapsulado. Un footprint crítico necesita drawing del fabricante, CAD enlazado/publicado por el fabricante o geometría explícita de PCB en datasheet primario. El precio no es criterio de cierre: prevalecen confiabilidad, manufacturabilidad, EMC, térmica y trazabilidad.

## CLOSED

### Honeywell MPR

`MPRLS0030PA00002A` / `NFB:Honeywell_MPR_LongPort_12Pad`.

Cerrado contra Honeywell `32332628 Issue L`, Figure 10:

- cuerpo 5 × 5 mm;
- 12 pads, pitch 1.27 mm;
- span metálico recomendado 4.20 mm;
- pads top/bottom 0.70 × 0.65 mm;
- pads laterales 0.65 × 0.70 mm;
- puerto largo Ø2.50 mm.

PR #11 corrigió centros exteriores a ±1.775 mm. El modelo seleccionado es absolute, por lo que no se perfora el orificio de referencia aplicable a variantes gage.

## BLOQUEADOS — Z3

### TPS259470A — RPW0010A

`TPS259470ARPWR`, TI `MPQF568 / RPW0010A / 4225183-A`.

- VQFN-HR, 10 pines, cuerpo nominal 2 × 2 mm, pitch 0.45 mm.
- TI publica land pattern no trivial HotRod/NSMD.
- **Placement bloqueado** hasta recrear/importar y comparar cobre, máscara y paste con la fuente TI.

### TPSM33625 — RDN-11

`TPSM33625RDNR`.

- QFN-FCMOD RDN, 11 pines, 4.5 × 3.5 mm, pitch 0.5 mm, altura ~2 mm.
- TI enlaza recursos CAD.
- **Placement bloqueado** hasta importar/verificar CAD autorizado; body + pitch no bastan para reconstruir el patrón.

## BLOQUEADOS — Z4 PR #12

### DRV8242H-Q1 — RHL-20

`DRV8242HQRHLRQ1`.

- TI RHL VQFN, 20 pines, cuerpo 4.5 × 3.5 mm.
- Driver de bomba con paths de potencia/thermal-pad que exigen land pattern exacto.
- **Placement bloqueado** hasta comparar RHL20 contra CAD/drawing TI.

### TPS1HC120C-Q1 — DYC-8

`TPS1HC120CQDYCRQ1`.

- TI DYC / SOT-5X3, 8 pines.
- **Placement bloqueado** hasta verificar land pattern y orientación pin 1 contra CAD/drawing TI.

### Panasonic AQY212EHAX — GE DIP4 SMD

`AQY212EHAX`.

- PhotoMOS 1 Form A, 4 pines, SMD.
- rating componente 60 V; uso NFB limitado a **SELV ≤48 V / NO MAINS**.
- **Placement bloqueado** hasta verificar terminal layout, gull-wing geometry, courtyard y CAD Panasonic.

## Consecuencia

La integración eléctrica Z1+Z2+Z3+Z4 puede cerrarse contractualmente sin autorizar coordenadas físicas. Actualmente continúan bloqueados para placement:

- `U_EFUSE`;
- `U_5V`;
- `U_PUMP_DRV`;
- `U_CO2_DRV`;
- `U_CHILLER`.

El workflow de auditoría impide que estos componentes aparezcan en `.kicad_pcb` mientras sus estados no sean `CLOSED`.

## Próximo cierre — PR #13

Cerrar RPW0010A, RDN-11, RHL20, DYC8 y AQY212EHAX contra fuentes primarias reproducibles. Solo después se habilitará placement de Z3/Z4.
