# Fase 2 — PR #7: Z2 Digital / Bajo Ruido

## Estado

**Baseline eléctrico Z2 congelado.** Este PR define conectividad, BOM, contratos de bring-up y exclusiones de producto para la zona digital de NFB Insight PCBA v2.

Fuera de alcance: placement, routing, cambios de `Edge.Cuts`, planos de cobre y cambios al firmware.

## 1. I²C global

El bus D20/D21 queda compartido por los dispositivos Insight:

- Honeywell MPRLS0030PA00002A, `0x28` — Z1.
- DFRobot DFR1103 GNSS+RTC, `0x66` — Z2.

`R_I2C_SDA` y `R_I2C_SCL` quedan poblados a **4.7 kΩ / 1 % hacia 3V3**. Los dos pull-ups locales de 10 kΩ reservados junto al MPR permanecen DNP.

No se incluye aislador I²C onboard en la línea base Insight. Las líneas que salen de la PCBA hacia el DFR1103 reciben protección ESD individual `PESD3V3U1UL,315` a GND.

## 2. GNSS + RTC — DFR1103 externo

Se reemplazan los módulos separados SAM-M8Q (`0x42`) y DS3231 (`0x68`) del diseño donante por un único **DFRobot DFR1103** externo.

La PCBA ofrece `J_GNSS_RTC`, JST XH de cuatro vías side-entry:

1. `I2C_SDA`
2. `I2C_SCL`
3. `GND`
4. `3V3_RAIL`

El arnés adapta XH-4 a Gravity 4P. PPS, INT y 32K del módulo no forman parte del baseline PR #7.

Esta decisión mantiene antena GNSS, respaldo RTC y mecánica específica del módulo fuera de la PCBA principal.

## 3. HX711 + celda de carga

`U_HX` se conserva onboard para Insight:

- alimentación analógica y digital desde `3V3_RAIL`;
- `RATE` a GND → 10 SPS;
- ganancia de canal A objetivo: 128;
- `DOUT` → D2 / `HX711_DOUT`;
- `PD_SCK` → D3 / `HX711_SCK`;
- canal B no usado;
- regulador interno no utilizado.

`J_LOADCELL` es un terminal Phoenix de 4 vías:

1. `3V3_RAIL` / E+
2. `GND` / E-
3. `LOAD_A_POS` / A+
4. `LOAD_A_NEG` / A-

El origen comercial concreto del HX711 queda pendiente de calificación de fabricación; la función, encapsulado SOP-16 y topología sí quedan congelados.

## 4. HMI UART

D0/D1 mantienen el contrato lógico:

- D0 = `HMI_RX`
- D1 = `HMI_TX`

La interfaz física a HMI de 5 V se realiza con **TI TXU0202DCUR**, dos canales de dirección fija opuesta:

- UNO `HMI_TX` 3.3 V → `HMI_FIELD_RX` 5 V.
- `HMI_FIELD_TX` 5 V → UNO `HMI_RX` 3.3 V.

`J_HMI` queda como JST XH side-entry de cuatro vías: 5V, GND, RX y TX. Cada línea UART de campo usa un `PESD5V0U1UL,315` individual a GND.

La capacidad de corriente real de `5V_RAIL` para alimentar la HMI se revalidará en Fase 3 antes de fabricar.

## 5. Watchdog / supervisión

Se congela **TPS3823-30DBVR**:

- `RESET` → `MCU_NRST` / pad 3.
- `WDI` ← D4 / `MCU_WDI`.
- `MR_n` con pull-up de 10 kΩ.
- VDD = 3V3.
- timeout nominal de watchdog usado por el contrato: 1.6 s.
- firmware de referencia alimenta WDI cada 400 ms.

Se añade `TP_WDT_MR` para bring-up; no se incluye botón de reset en este PR.

## 6. LED de estado

No se añade un LED externo. D13 / `LED_STATUS` conserva el LED integrado del UNO Q como implementación principal y se añade `TP_LED_STATUS`.

## 7. Test points de bring-up

Se congelan:

- `TP_3V3`, `TP_5V`, `TP_GND`
- `TP_I2C_SDA`, `TP_I2C_SCL`
- `TP_HX_DOUT`, `TP_HX_SCK`
- `TP_LOAD_A_POS`, `TP_LOAD_A_NEG`
- `TP_HMI_TX`, `TP_HMI_RX`
- `TP_WDI`, `TP_NRST`, `TP_WDT_MR`
- `TP_LED_STATUS`

Son features de PCB, no componentes comprados.

## 8. Bloques expresamente excluidos de Insight Z2

No forman parte del baseline:

- MAX3485 / RS485
- SC16IS740
- SN74LVC1G04 del puente RS485
- ISO1541
- SAM-M8Q separado
- DS3231 onboard/separado
- Cell Density / Signature

D10 permanece solo como reserva contractual para una futura expansión deliberada.

## 9. Seguimiento de firmware

El firmware no cambia en este PR. Queda pendiente:

1. reemplazar GPS `0x42` + RTC `0x68` por DFR1103 `0x66`;
2. mantener HX711 sobre D2/D3;
3. mantener watchdog D4 con feed de 400 ms;
4. validar HMI UART física mediante el TXU0202.

## 10. Gates del PR

El PR no puede mergearse si falla alguno de estos puntos:

- contrato UNO Q + Z1 + Z2;
- referencias BOM = referencias netlist Z2;
- topología/pinout contractual de HX711;
- dirección I²C DFR1103 `0x66`;
- pull-ups globales I²C = 4.7 kΩ;
- pinout contractual TXU0202;
- watchdog TPS3823-30;
- ausencia de bloques legacy/Signature en BOM/netlist Z2;
- ERC del root schematic;
- Z1 permanece verde;
- mecánica/DRC permanece sin cambios.
