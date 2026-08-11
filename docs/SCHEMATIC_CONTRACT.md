# NFB Insight PCBA v2 — Contrato de Esquemático

**Estado:** línea base corregida por PR #5  
**Producto objetivo:** NFB Insight  
**Fuente mecánica:** `docs/MECHANICAL_CONVENTION.md`  
**Firmware de referencia:** `Nhilson73/Nebula_ArduinoAPPLab_UNOQ`  
**Fuente de verdad de interfaces de sensores:** `hardware/sensor_interface_contract.json`

## 1. Principio

El esquemático V2 no copiará literalmente la jerarquía ni la hoja raíz del Q-Shield anterior. El primer gate eléctrico es un contrato explícito entre el conector del Arduino UNO Q y las señales que realmente pertenecen a Insight.

La migración de circuitos se realiza por bloques funcionales contra este contrato: sensores/interfaz, digital/bajo ruido, potencia y actuadores. Desde PR #5, el Q-Shield conserva valor como **donante de trazabilidad**, pero sus front-end de electrodo crudo no constituyen la fuente de verdad de producción.

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
| 9 | A0 | PH_ADC | Activo | Entrada acondicionada de pH, 0–3 V. |
| 10 | A1 | ORP_ADC | Activo | Entrada ORP acondicionada y escalada a ≤3.05 V. |
| 11 | A2/D16 | TEMP_1WIRE | Activo digital | KIT0021/DS18B20, bus 1-Wire a 3.3 V. No es `TEMP_ADC`. |
| 12 | A3 | NC | DNP/Reserva | Humedad eliminada de la línea base Insight. |
| 13 | A4 | CO2_ADC | Activo | Presión CO₂ analógica; sensor final pendiente de selección, siempre escalada a ≤3.05 V. |
| 14 | A5 | DO_ADC | Activo | Entrada acondicionada de DO, 0–3 V. |
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

## 3. Contrato real de sensores — corrección PR #5

La revisión contra documentación oficial de los módulos elegidos cambia la interpretación del bloque analógico:

- **pH A0:** la PCBA recibe la salida acondicionada del módulo DFRobot `SEN0161-V2` o del `SEN0169-V2` preferido para operación continua. El BNC permanece en el módulo acondicionador; la PCBA recibe 3 conductores y 0–3 V.
- **ORP A1:** la PCBA recibe la salida acondicionada del `SEN0464`. Al ser un dominio de hasta aproximadamente 4.5 V, V2 exige divisor de precisión 10 kΩ / 20 kΩ para llevar el peor caso a 3.0 V.
- **Temperatura A2/D16:** `KIT0021` usa `DS18B20`; por ello A2 se utiliza como GPIO digital 1-Wire y la net contractual pasa de `TEMP_ADC` a `TEMP_1WIRE`.
- **Presión CO₂ A4:** `MPX5700AP` se conserva únicamente como referencia legacy de pruebas. Requiere escalamiento y debe sustituirse por un sensor vigente antes de fabricación.
- **DO A5:** la PCBA recibe la salida acondicionada 0–3 V del `SEN0237-A`; el BNC permanece en el módulo DFRobot.

El detalle eléctrico, fuentes oficiales y cálculos se encuentran en `docs/FASE2_PR5_SENSOR_INTERFACES.md` y `hardware/sensor_interface_contract.json`.

## 4. Aislamiento y conectores

El baseline V2 **no incorpora tres cadenas obligatorias SN6501 + transformador + AMC1301** para pH/ORP/DO. Esas cadenas pertenecen a la arquitectura donante y no se justifican cuando la PCBA recibe las señales ya acondicionadas de los módulos comerciales.

Cuando las pruebas con múltiples sondas en el mismo medio evidencien acoplamiento por tierra, se podrá incorporar un aislador analógico inline `DFR0504` o equivalente a nivel de sistema. No forma parte del placement base de la PCBA.

Todos los conectores de sensores pertenecen al borde `Y=0` y salen hacia `-Y`. Los BNC de las sondas no se montan en la PCBA principal.

## 5. Diferencias detectadas contra firmware `main`

El firmware snapshot `cf100b38df890f61aed472e934241e145425569b` todavía compila con `NEBULA_TIER_SIGNATURE` y define explícitamente:

- `A2` como `PIN_TEMPERATURE_ANALOG`, mientras V2 usa `TEMP_1WIRE` para DS18B20;
- `A3` como `PIN_HUMIDITY_ANALOG`, mientras A3 es DNP/Reserva en Insight V2;
- `D9` como `PIN_CO2_FLOW_PWM`, mientras D9 es DNP/Reserva en Insight V2;
- chiller como función de Signature, mientras V2 conserva D8 solo como salida de control.

Los siguientes pines siguen coincidiendo en función general con firmware: A0 pH, A1 ORP, A4 presión CO₂, A5 DO, D2/D3 HX711, D4 watchdog, D5/D6 bomba, D7 solenoide CO₂ y D8 chiller.

La migración de temperatura a DS18B20/1-Wire se hará en un PR separado del repositorio de firmware después de aprobar este contrato de hardware.

## 6. Reglas para la siguiente migración

1. Ningún bloque eléctrico podrá cambiar este pinout sin actualizar simultáneamente `hardware/insight_pin_contract.json`, `hardware/sensor_interface_contract.json`, este documento y los validadores automáticos.
2. A3 y D9 se consideran físicamente disponibles pero eléctricamente no poblados en Insight.
3. D10 es una reserva de expansión; no se poblará el bridge RS485 en la línea base Insight salvo decisión explícita posterior.
4. `12V_RAIL` en VIN permanece bajo revisión hasta congelar la separación entre potencia limpia y potencia de actuadores.
5. A0/A1/A4/A5 deben respetar el dominio analógico del UNO Q; V2 fija objetivo de diseño ≤3.05 V para entradas externas.
6. A2/D16 es digital 1-Wire y no debe volver a materializarse como divisor NTC/ADC.
7. El esquemático debe mantener ERC = 0 antes de incorporarse a `main`.
