# Fase 2 — PR #7: Z2 Digital / Bajo Ruido

## Estado

**Baseline eléctrico Z2 congelado**, con ECO posterior de potencia HMI PR19D. Este documento conserva la intención original de PR #7 y registra las decisiones posteriores que afectan Z2 sin reescribir su historia.

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

## 4. HMI UART — Nextion + ECO de potencia PR19D

D0/D1 mantienen el contrato lógico:

- D0 = `HMI_RX`
- D1 = `HMI_TX`

La HMI seleccionada es **Nextion Intelligent Series `NX8048P050-011C-Y`**, 5.0" capacitiva con enclosure, 800×480. La interfaz lógica sigue usando **TI `TXU0202DCUR`**:

- UNO `HMI_TX` 3.3 V → `HMI_FIELD_RX` → RX de Nextion.
- TX de Nextion → `HMI_FIELD_TX` → UNO `HMI_RX` 3.3 V.

`J_HMI` conserva `S4B-XH-A(LF)(SN)` y su footprint side-entry; no se movieron pads para el ECO. El mating del arnés Nextion `XH2.54 4P` debe verificarse en first article.

### Alimentación final

El BOX Speaker añade 0.5 A al requisito de 1 A del display. Para evitar consumir todo el presupuesto histórico de `5V_RAIL`, PR19D cierra el ECO con un rail externo dedicado:

`12V sistema → fuse 2 A → RECOM R-78K5.0-2.0L → 5V_HMI`

En la PCBA:

1. `J_HMI.1 = 5V_HMI`
2. `U_HMI_LVL.7 / VCCB = 5V_HMI`
3. `C_HMI_B.1 = 5V_HMI`
4. `5V_HMI` **no** puede unirse a `5V_RAIL` ni a `J_UNOQ.5`.

La corriente de pantalla/audio permanece en el subensamble externo. La PCBA solo toma de `5V_HMI` la corriente de soporte del lado B del TXU0202.

PR19D cerró `5V_HMI` 1/1 con DRC=0, sin modificar placement, outline ni el cobre UART previo. Fuente de verdad: `hardware/hmi_system_contract.json`, `hardware/hmi_power_eco.json` y `docs/HMI_POWER_ECO_PR19D.md`.

## 5. Watchdog / supervisión

Se congela **TPS3823-30DBVR**:

- `RESET` → `MCU_NRST` / pad 3.
- `WDI` ← D4 / `MCU_WDI`.
- `MR_n` con pull-up de 10 kΩ.
- VDD = 3V3.
- timeout nominal: 1.6 s.
- firmware alimenta WDI cada 400 ms.

## 6. LED de estado

No se añade un LED externo. D13 / `LED_STATUS` conserva el LED integrado del UNO Q y se mantiene `TP_LED_STATUS`.

## 7. Test points de bring-up

Se congelan:

- `TP_3V3`, `TP_5V`, `TP_GND`
- `TP_I2C_SDA`, `TP_I2C_SCL`
- `TP_HX_DOUT`, `TP_HX_SCK`
- `TP_LOAD_A_POS`, `TP_LOAD_A_NEG`
- `TP_HMI_TX`, `TP_HMI_RX`
- `TP_WDI`, `TP_NRST`, `TP_WDT_MR`
- `TP_LED_STATUS`

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

1. DFR1103 `0x66` sustituye GPS `0x42` + RTC `0x68`.
2. HX711 permanece sobre D2/D3.
3. watchdog permanece D4 con feed de 400 ms.
4. HMI UART permanece sobre TXU0202; la alimentación de campo es `5V_HMI` desde PR19D.

## 10. Gates vigentes

- contrato UNO Q + Z1 + Z2;
- referencias BOM = referencias netlist Z2;
- HX711 y DFR1103 congelados;
- TXU0202 preservado;
- `J_HMI.1/U_HMI_LVL.7/C_HMI_B.1 = 5V_HMI`;
- ausencia de puente `5V_HMI ↔ 5V_RAIL`;
- watchdog TPS3823-30;
- ERC del root = 0;
- DRC físico = 0;
- placement/outline congelados.
