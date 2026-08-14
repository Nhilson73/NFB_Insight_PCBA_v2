# ECO de potencia HMI — PR19D / 5V_HMI

## Decisión

La Nextion `NX8048P050-011C-Y` y el `Nextion BOX Speaker` dejan de consumir desde `5V_RAIL` de la PCBA principal. El sistema adopta una rama externa dedicada, próxima a la HMI:

`12V sistema → 0FHM0001ZXJ + 0997002.WXN (2 A) → RECOM R-78K5.0-2.0L → 5V_HMI`

`5V_HMI` alimenta la pantalla y el speaker en el arnés externo. Ese mismo rail vuelve a `J_HMI.1` únicamente para `U_HMI_LVL.VCCB` y `C_HMI_B`; por ello la corriente de 1.5 A de display/audio **no atraviesa la NFB PCBA v2**.

## Componentes congelados

- RECOM `R-78K5.0-2.0L`: 5 V / 2 A / 10 W; Vin 6.5–36 V; no aislado; versión L horizontal de bajo perfil.
- Littelfuse holder `0FHM0001ZXJ`: MINI inline, 58 V máx., 14 AWG, IP67.
- Littelfuse fuse `0997002.WXN`: MINI 58 VDC / 2 A.

## Impacto EDA

- Nuevo net de producción: `5V_HMI` (59 → 60 nets).
- Nuevo lote `PR19D`: 1/1 net local en Z2.
- `J_HMI.1`, `U_HMI_LVL.7` y `C_HMI_B.1` migran de `5V_RAIL` a `5V_HMI`.
- `5V_RAIL` no tenía cobre en PR19C, por lo que el ECO no retira routing previo.
- HMI UART (`HMI_FIELD_RX/TX`, `HMI_RX/TX`) queda congelado.
- Placement, outline e In1.Cu no cambian.

## Potencia de sistema

La rama HMI reserva 7.5 W de salida. Como cribado conservador a 90 % de eficiencia equivale a ~8.33 W de entrada. Se recomienda 12 V / 6 A (72 W) para recuperar margen de sistema; la rama HMI queda protegida de forma independiente antes del convertidor.

## Release gates

El ECO eléctrico se considera cerrado en diseño cuando PR19D sea DRC=0. El producto aún requiere first article: corriente/arranque, temperatura del RECOM dentro del enclosure, no nuisance-trip del fusible 2 A, mating del arnés XH y EMC del cable final.
