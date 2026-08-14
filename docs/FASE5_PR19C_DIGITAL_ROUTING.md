# Fase 5 — PR19C: routing digital/control inter-zona

## Propósito

PR19C cierra el tercer lote incremental de routing de NFB Insight PCBA v2 bajo la política **ALL_OR_NOTHING** definida en `hardware/routing_batches_contract.json`.

El lote contiene exactamente 16 nets digital/control inter-zona:

- `ACT_FAULT_N`
- `CHILLER_CTL`
- `CO2_SOL_CTL`
- `HMI_RX`
- `HMI_TX`
- `HX711_DOUT`
- `HX711_SCK`
- `I2C_SCL`
- `I2C_SDA`
- `LED_STATUS`
- `MCU_NRST`
- `MCU_WDI`
- `PUMP_DIR`
- `PUMP_PWM`
- `TEMP_1WIRE`
- `UNO_IOREF_3V3`

PR20A y PR20B quedan expresamente fuera de alcance.

## Baseline de entrada

PR19C parte del checkpoint PR19B mergeado en PR #30:

- PR19A: 28/28 nets locales.
- PR19B: 4/4 nets analógicas long-haul.
- PCB acumulado: **555 segmentos / 31 vías**.
- DRC KiCad 10.0.5: **0 errores**.
- warnings conocidos: **255**, todos de serigrafía/texto.
- unconnected: **192**.
- `In1.Cu`: 0 signal tracks.
- copper zones: 0.
- 27 nets futuras sin cobre.

Antes de materializar PR19C se ejecutó un probe read-only para congelar endpoints, zonas y ocupación real del cobre existente.

## Política de routing aplicada

- `DIGITAL_LOW_SPEED`: preferencia por `B.Cu` en recorridos long-haul.
- `F.Cu`: escapes locales y bypasses puntuales donde la geometría lo exige.
- `UNO_IOREF_3V3`: conserva la clase `CONTROL_SENSITIVE`.
- `In1.Cu`: reservado a referencia GND; no se utiliza para señales.
- `In2.Cu`: no se utiliza para estas 16 señales.
- placement, outline, netlist y netclasses permanecen congelados.
- no se relaja ninguna regla DRC.

## Desarrollo del candidato

La familia de candidatos v13–v18 se trató como laboratorio efímero de Actions; ningún candidato parcial fue persistido como cobre de producción.

Principales aprendizajes:

1. **v13** consiguió conectividad 16/16, pero dejó 22 errores físicos y exceso de vías.
2. **v14** redujo el DRC a 5 errores, demostrando que los problemas estaban concentrados en microzonas y no en la estrategia general de capas.
3. Una penalización global de cambios de capa no resultó adecuada: algunas nets mejoraban, pero `PUMP_DIR` perdía resolubilidad.
4. La estrategia correcta fue optimizar el costo de vía por net/corredor y después corregir únicamente las microzonas físicas restantes.
5. **v18** alcanzó simultáneamente conectividad, DRC y calidad geométrica.

## ECO de routing previo: `CO2_ILIM`

El routing de `ACT_FAULT_N` reveló que los cuatro segmentos PR19A de `CO2_ILIM` formaban una garganta geométrica alrededor de `U_CO2_DRV.1`.

Se aplicó un ECO exclusivamente de geometría de cobre:

- net: `CO2_ILIM`;
- segmentos: **4 → 4**;
- vías: **0 → 0**;
- conectividad: sin cambios;
- netclass: sin cambios;
- placement: sin cambios;
- outline: sin cambios.

El recorrido final usa un muro en `x=216.20 mm`, conservando margen frente a `PUMP_CURRENT_ADC` y al escape de `ACT_FAULT_N`.

## ECO de spacing I²C

El candidato previo dejó dos vías `I2C_SDA` demasiado próximas entre taladros. La vía `(92.75, 15.50)` se desplazó a `(93.25, 15.50)` y se reanclaron sus dos segmentos adyacentes.

- conteo de vías: sin cambios;
- topología: sin cambios;
- conectividad: sin cambios;
- warning `hole_to_hole`: eliminado.

## Candidato aceptado — v18

Resultado del gate KiCad 10.0.5:

- **PR19C 16/16 conectado**.
- cobre nuevo PR19C: **362 segmentos / 88 vías**.
- acumulado PR19A+PR19B+PR19C: **917 segmentos / 119 vías**.
- DRC: **0 errores**.
- warnings: **255**, exactamente los históricos:
  - `silk_edge_clearance`: 13;
  - `text_height`: 1;
  - `silk_overlap`: 173;
  - `silk_over_copper`: 68.
- unconnected restantes: **154**.
- PR20A/PR20B: **0 nets con cobre adelantado**.
- `In1.Cu`: **0 signal tracks**.
- copper zones: **0**.
- placement y outline: congelados.

La caída de unconnected `192 → 154` coincide con las **38 conexiones lógicas** requeridas por el MST de las 16 nets del lote.

## Métricas geométricas por net

| Net | Segmentos | Vías | Giros | Longitud aprox. mm |
|---|---:|---:|---:|---:|
| `ACT_FAULT_N` | 41 | 8 | 20 | 397.733 |
| `CHILLER_CTL` | 20 | 4 | 13 | 296.208 |
| `CO2_SOL_CTL` | 22 | 8 | 11 | 278.925 |
| `HMI_RX` | 22 | 9 | 6 | 225.595 |
| `HMI_TX` | 21 | 8 | 7 | 227.908 |
| `HX711_DOUT` | 18 | 2 | 9 | 181.695 |
| `HX711_SCK` | 20 | 5 | 9 | 195.092 |
| `I2C_SCL` | 44 | 9 | 16 | 260.025 |
| `I2C_SDA` | 38 | 9 | 11 | 251.061 |
| `LED_STATUS` | 13 | 4 | 6 | 177.336 |
| `MCU_NRST` | 14 | 3 | 5 | 121.948 |
| `MCU_WDI` | 17 | 3 | 8 | 180.325 |
| `PUMP_DIR` | 23 | 8 | 12 | 276.892 |
| `PUMP_PWM` | 20 | 4 | 13 | 265.369 |
| `TEMP_1WIRE` | 17 | 2 | 6 | 91.013 |
| `UNO_IOREF_3V3` | 12 | 2 | 7 | 156.360 |

Todas las nets cumplen el gate de calidad PR19C de **≤10 vías por net** y permanecen holgadamente por debajo del límite de fragmentación de segmentos.

## Gate de aceptación

PR19C solo puede mergearse cuando el PCB persistido reproduce el candidato v18 y cumple simultáneamente:

- 16/16 nets PR19C conectadas;
- PR19A y PR19B preservados;
- exactamente 48 nets de los tres lotes con cobre;
- 11 nets PR20A/PR20B todavía diferidas;
- DRC errors = 0;
- warnings = los 255 históricos, sin tipos nuevos;
- unconnected = 154;
- `In1.Cu` sin señales;
- copper zones = 0;
- placement/outline sin cambios;
- workflows finales `contents: read`.

## Siguiente checkpoint

Después del merge de PR19C, el siguiente lote autorizado es **PR20A — 10 nets de potencia + salidas de actuadores**. No se inicia PR20A dentro de este PR.
