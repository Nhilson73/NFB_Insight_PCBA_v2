# NFB Insight PCBA v2 — Contrato de Esquemático

**Estado:** baseline Z1 congelado por PR #6  
**Producto:** NFB Insight  
**Firmware de referencia:** `Nhilson73/Nebula_ArduinoAPPLab_UNOQ` @ `cf100b38df890f61aed472e934241e145425569b`  
**Fuente de verdad sensores:** `hardware/sensor_interface_contract.json`  
**Netlist Z1:** `hardware/z1_production_netlist.json`

## Principio

La V2 hereda conocimiento del Q-Shield, no su topología. Todo cambio eléctrico debe mantenerse coherente entre contrato de pines, contrato de sensores, netlist, BOM, KiCad y validadores.

## Contrato de pines UNO Q

| Pad | Pin | Net | Estado | Uso |
|---:|---|---|---|---|
| 1 | BOOT | NC | NC | No conectar |
| 2 | IOREF | NC | NC | No conectar |
| 3 | ~RESET | MCU_NRST | Activo | Supervisor |
| 4 | 3V3 | 3V3_RAIL | Activo | Lógica/sensores |
| 5 | 5V | 5V_RAIL | Activo | Módulos acondicionadores |
| 6 | GND | GND | Activo | Tierra |
| 7 | GND | GND | Activo | Tierra |
| 8 | VIN | 12V_RAIL | Revisar | Se resolverá en Fase 3 |
| 9 | A0 | PH_ADC | Activo | pH acondicionado |
| 10 | A1 | ORP_ADC | Activo | ORP escalado |
| 11 | A2/D16 | TEMP_1WIRE | Activo digital | DS18B20 |
| 12 | A3 | NC | DNP/Reserva | Humedad eliminada |
| 13 | A4 | NC | DNP/Reserva | `CO2_ADC` retirado en PR #6 |
| 14 | A5 | DO_ADC | Activo | DO acondicionado |
| 15 | D0 | HMI_RX | Activo | HMI |
| 16 | D1 | HMI_TX | Activo | HMI |
| 17 | D2 | HX711_DOUT | Activo | Celda de carga |
| 18 | D3 | HX711_SCK | Activo | Celda de carga |
| 19 | D4 | MCU_WDI | Activo | Watchdog |
| 20 | D5 | PUMP_PWM | Activo | Bomba |
| 21 | D6 | PUMP_DIR | Activo | Bomba |
| 22 | D7 | CO2_SOL_CTL | Activo | Solenoide CO₂ |
| 23 | D8 | CHILLER_CTL | Activo control | Energía fuera de PCBA |
| 24 | D9 | NC | DNP/Reserva | PWM proporcional fuera de Insight |
| 25 | D10 | RS485_IRQ_RSVD | Reserva | Signature futura |
| 26 | D11 | NC | NC | Reserva física |
| 27 | D12 | NC | NC | Reserva física |
| 28 | D13 | LED_STATUS | Activo | Estado |
| 29 | GND | GND | Activo | Tierra |
| 30 | AREF | NC | NC | No conectar |
| 31 | D20/SDA | I2C_SDA | Activo | Bus digital, incluye MPR `0x28` |
| 32 | D21/SCL | I2C_SCL | Activo | Bus digital, incluye MPR `0x28` |

## Z1 congelado

### pH
`J_PH → PESD3V3U1UL → 1 kΩ → PH_ADC`, con `100 nF` de PH_ADC a GND.

### ORP
`J_ORP → 10 kΩ → ORP_ADC`; desde ORP_ADC: `20 kΩ`, `PESD3V3U1UL` y `100 nF` a GND. El divisor convierte 4.5 V máximo en 3.0 V.

### Temperatura
`J_TEMP → TEMP_1WIRE`; `PESD3V3U1UL` a GND y pull-up onboard `4.7 kΩ` a 3.3 V.

### Presión CO₂
`U_CO2 = MPRLS0030PA00002A`, 0–30 psi absolute, I²C `0x28`, 3.3 V, `100 nF` de bypass. A4 no participa en presión.

### DO
`J_DO → PESD3V3U1UL → 1 kΩ → DO_ADC`, con `100 nF` de DO_ADC a GND.

## Conectores y mecánica de servicio

`J_PH`, `J_ORP`, `J_TEMP` y `J_DO` usan JST XH `S3B-XH-A(LF)(SN)` / footprint `JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal`. El placement deberá orientar la boca hacia `-Y`. El MPR es onboard y recibe presión mediante tubing a su puerto largo.

## Diferencias pendientes de firmware

El snapshot de firmware aún:
- lee temperatura con `analogRead(A2)`;
- lee presión CO₂ con `analogRead(A4)`.

Un PR de firmware deberá migrar a:
- DS18B20 / 1-Wire en A2-D16;
- Honeywell MPR I²C `0x28` en D20/D21.

## Reglas

1. `CO2_ADC` y `TEMP_ADC` están prohibidas como nets activas.
2. A3, A4 y D9 permanecen DNP/Reserva.
3. Ningún BNC, `MPX5700AP`, `SN6501`, `AMC1301` o `750315371` pertenece a la BOM base Z1.
4. Cambios de valores, MPN, footprint o nets requieren actualizar contrato, BOM, netlist, KiCad y CI en el mismo PR.
5. Placement/routing no pueden comenzar a reinterpretar silenciosamente este contrato.
6. ERC debe permanecer en cero antes de integrar a `main`.
