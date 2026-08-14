# PR19D — cierre ECO de potencia HMI

## Resultado

PR19D introduce una sola net de producción: `5V_HMI`, creada para separar la alimentación de la HMI Nextion del `5V_RAIL` sensible de la NFB PCBA v2.

## Arquitectura

`12V sistema → Littelfuse 0FHM0001ZXJ + 0997002.WXN 2 A → RECOM R-78K5.0-2.0L → 5V_HMI`.

La pantalla `NX8048P050-011C-Y` y el BOX Speaker consumen desde el subensamble externo. En la PCBA `5V_HMI` solo conecta `J_HMI.1`, `U_HMI_LVL.7` y `C_HMI_B.1`.

## Evidencia de routing

- lote: PR19D, ALL_OR_NOTHING 1/1;
- delta: 7 segmentos + 2 vías;
- acumulado: 924 segmentos + 121 vías;
- nets de producción vigentes: 60;
- nets ruteadas: 49/60;
- `In1.Cu`: 0 señales;
- zones: 0;
- DRC KiCad 10.0.5: 0 errores;
- warnings: 255, exactamente los históricos de silk/texto;
- unconnected: 151;
- ERC root: 0 violaciones.

## Escape VSSOP

`U_HMI_LVL.7` usa 0.20 mm por ≤1.20 mm únicamente en el fan-out inmediato del VSSOP. El clearance contractual permanece ≥0.20 mm y la distribución de `5V_HMI` retorna a 0.40 mm.

## Invariantes preservados

- placement congelado;
- outline 242.34 × 68.58 mm congelado;
- routing UART HMI previo sin cambio;
- ningún cobre de PR20A/PR20B adelantado;
- `5V_RAIL` no se une a `5V_HMI`;
- PR20A conserva sus 10 nets históricas.

## First article pendiente

El ECO queda cerrado en diseño, pero release de producto exige medir corriente/inrush, temperatura del RECOM, comportamiento del fusible 2 A, mating del arnés y EMC del conjunto HMI final.
