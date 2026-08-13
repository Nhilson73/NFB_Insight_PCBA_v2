# ECO de placement Z3 — TPSM33625

## Contexto

Durante PR19A, el routing de las 28 nets locales reveló que la micro-isla del convertidor `U_5V = TPSM33625RDNR` había sido organizada por el empaquetador geométrico PR17, pero no suficientemente por prioridad eléctrica. El síntoma fue reproducible: `5V_FB` y `5V_VCC` podían rutearse individualmente, pero se bloqueaban mutuamente al intentar cerrar ambas con clearances físicos conservadores.

La decisión fue **no forzar routing alrededor de un placement subóptimo** y no relajar DRC. Se abrió un ECO local de placement antes de continuar el lote.

## Fuente primaria

Autoridad primaria: **Texas Instruments, TPSM33625, datasheet SNVSCB1D Rev. D, sección 8.5.1 — Layout Guidelines**.

La intención relevante de TI es:

- capacitores de entrada tan cerca como sea posible de `VIN/GND`;
- capacitor bypass de `VCC` cerca del pin `VCC`, con conexiones cortas y anchas a `VCC/GND`;
- divisor `R_FBT/R_FBB` tan cerca como sea posible de `FB`, con recorridos `FB/GND` cortos.

El ECO traduce esas prioridades a coordenadas reproducibles dentro de Z3.

## Alcance

Solo se mueven/rotan cinco referencias:

- `C_5V_IN_4U7`
- `C_5V_IN_100N`
- `C_5V_VCC`
- `R_5V_FBT`
- `R_5V_FBB`

`U_5V` permanece fijo. No cambian:

- outline `242.34 × 68.58 mm`;
- altura `68.58 mm`;
- zonas Z0–Z4;
- netlist;
- footprints;
- secuencia FIELD I/O;
- arquitectura de potencia;
- routing/cobre.

El contrato machine-readable es `hardware/z3_buck_placement_eco.json`.

## Targets congelados

| Ref | X mm | Y mm | Rotación | Intención |
|---|---:|---:|---:|---|
| `C_5V_IN_4U7` | 184.600 | 19.075 | 180° | VIN bulk, pad VIN orientado hacia la isla |
| `C_5V_IN_100N` | 188.950 | 19.075 | 180° | bypass HF de entrada más próximo a U_5V |
| `R_5V_FBT` | 191.600 | 15.390 | 90° | divisor FB vertical bajo el borde FB |
| `R_5V_FBB` | 193.000 | 15.390 | 270° | divisor FB vertical bajo FB/GND |
| `C_5V_VCC` | 195.300 | 15.600 | 0° | bypass VCC inmediatamente bajo VCC/GND |

## Validación

El flujo PR22 exige:

1. regenerar el placement base PR17;
2. aplicar exactamente cinco movimientos;
3. demostrar que las otras **114 referencias** no cambian;
4. reconstruir el PCB desde la base KiCad;
5. validar XY/rotación/footprints/nets y courtyards;
6. exigir `tracks/vías/zones = 0`;
7. ejecutar DRC completo de KiCad.

Resultado físico observado antes de persistencia:

- referencias movidas: 5;
- referencias sin cambio: 114;
- courtyard overlaps: 0;
- DRC errors: 0;
- shorts/clearance/courtyard violations: 0;
- unconnected: 250, esperado por placement-only;
- deuda silk/text: 259 warnings, todos tipificados; el incremento respecto PR17 fue `+13 silk_over_copper` y debe eliminarse antes de artwork/Gerbers.

## Regla de ingeniería derivada

**El placement global está congelado, pero el routing puede abrir un ECO local cuando descubre una debilidad física/electromagnética que no debe resolverse con trazas artificiales.** Para admitir el ECO deben cumplirse simultáneamente:

- evidencia técnica primaria;
- mínimo número de referencias afectadas;
- cero cambios de arquitectura/netlist/outline salvo necesidad explícitamente aprobada;
- regeneración determinista;
- DRC físico sin errores;
- aprendizaje documentado antes de continuar routing.

PR19A solo se reinicia después de que este ECO quede mergeado y reproducible desde `main`.
