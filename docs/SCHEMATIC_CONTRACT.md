# NFB Insight PCBA v2 — Contrato de Esquemático

**Estado:** línea base para PR #3  
**Producto objetivo:** NFB Insight  
**Fuente mecánica:** `docs/MECHANICAL_CONVENTION.md`  
**Firmware de referencia:** `Nhilson73/Nebula_ArduinoAPPLab_UNOQ`

## 1. Principio

El esquemático V2 no copiará literalmente la jerarquía ni la hoja raíz del Q-Shield anterior. El primer gate eléctrico es un contrato explícito entre el conector del Arduino UNO Q y las señales que realmente pertenecen a Insight.

La migración de circuitos se realizará posteriormente por bloques funcionales contra este contrato: analógico/aislamiento, digital/bajo ruido, potencia y actuadores.

## 2. Contrato de pines Insight

| Pad UNO Q | Pin Arduino | Net V2 | Estado Insight | Observación |
|---:|---|---|---|---|
| 1 | BOOT | NC | No usado | No conectar en la PCBA. |
| 2 | IOREF | NC | No usado | No conectar en la PCBA. |
| 3 | ~RESET | MCU_NRST | Activo | Reset desde watchdog/supervisión. |
| 4 | 3V3 | 3V3_RAIL | Activo | Alimentación lógica. |
| 5 | 5V | 5V_RAIL | Activo | Alimentación 5 V. |
| 6 | GND | GND | Activo | Tierra. |
| 7 | GND | GND | Activo | Tierra. |
| 8 | VIN | 12V_RAIL | REVISAR | Se mantiene como contrato del donante hasta congelar arquitectura de potencia en Fase 3. |
| 9 | A0 | PH_ADC | Activo | pH. |
| 10 | A1 | ORP_ADC | Activo | ORP. |
| 11 | A2 | TEMP_ADC | Activo | Temperatura. |
| 12 | A3 | NC | DNP/Reserva | Humedad eliminada de la línea base Insight. |
| 13 | A4 | CO2_ADC | Activo | Presión CO₂. |
| 14 | A5 | DO_ADC | Activo | Oxígeno disuelto. |
| 15 | D0 | HMI_RX | Activo | UART HMI. |
| 16 | D1 | HMI_TX | Activo | UART HMI. |
| 17 | D2 | HX711_DOUT | Activo | Celda de carga. |
| 18 | D3 | HX711_SCK | Activo | Celda de carga. |
| 19 | D4 | MCU_WDI | Activo | Watchdog externo. |
| 20 | D5 | PUMP_PWM | Activo | Control bomba. |
| 21 | D6 | PUMP_DIR | Activo | Dirección bomba. |
| 22 | D7 | CO2_SOL_CTL | Activo | Solenoide CO₂. |
| 23 | D8 | CHILLER_CTL | Activo control | Solo señal de control; energía del chiller fuera de la PCBA por defecto. |
| 24 | D9 | NC | DNP/Reserva | PWM de válvula proporcional fuera de la línea base Insight. |
| 25 | D10 | RS485_IRQ_RSVD | Reserva | Reservado para expansión Signature; no debe forzar placement Insight. |
| 26 | D11 | NC | No usado | Disponible para expansión futura. |
| 27 | D12 | NC | No usado | Disponible para expansión futura. |
| 28 | D13 | LED_STATUS | Activo | Estado. |
| 29 | GND | GND | Activo | Tierra. |
| 30 | AREF | NC | No usado | No conectar por defecto. |
| 31 | D20/SDA | I2C_SDA | Activo | Bus I²C de la PCBA. |
| 32 | D21/SCL | I2C_SCL | Activo | Bus I²C de la PCBA. |

## 3. Diferencias detectadas contra firmware `main`

El firmware actual todavía compila con `NEBULA_TIER_SIGNATURE` y define explícitamente:

- `A3` como `PIN_HUMIDITY_ANALOG`;
- `D9` como `PIN_CO2_FLOW_PWM`;
- chiller como función de Signature.

Para NFB Insight V2 estos recursos no se poblarán como funciones base. La divergencia queda documentada de forma intencional; no se modifica el repositorio de firmware dentro de este PR.

Los siguientes pines sí coinciden directamente con firmware: A0 pH, A1 ORP, A2 temperatura, A4 CO₂, A5 DO, D2/D3 HX711, D4 watchdog, D5/D6 bomba, D7 solenoide CO₂ y D8 chiller.

## 4. Reglas para la siguiente migración

1. Ningún bloque eléctrico podrá cambiar este pinout sin actualizar simultáneamente este documento y el validador automático.
2. A3 y D9 se consideran físicamente disponibles pero eléctricamente no poblados en Insight.
3. D10 es una reserva de expansión; no se poblará el bridge RS485 en la línea base Insight salvo decisión explícita posterior.
4. `12V_RAIL` en VIN permanece bajo revisión hasta congelar la separación entre potencia limpia y potencia de actuadores.
5. El esquemático debe mantener ERC = 0 antes de incorporarse a `main`.
