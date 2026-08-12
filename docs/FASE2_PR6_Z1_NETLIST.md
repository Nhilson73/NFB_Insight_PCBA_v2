# Fase 2 — PR #6: cierre de Z1 y netlist de producción

**Producto:** NFB Insight PCBA v2  
**Zona:** Z1 — Sensor Interfaces  
**Estado:** `FROZEN_Z1_NETLIST_PR6`  
**Fecha:** 2026-08-11

## 1. Objetivo

PR #6 convierte las decisiones de interfaz de PR #5 en un **netlist discreto de producción** verificable. El alcance termina en el contrato eléctrico de Z1: no incluye placement, routing ni cambios de geometría de la placa.

Las fuentes de verdad son:

- `hardware/sensor_interface_contract.json`: contrato funcional de sensores;
- `hardware/z1_production_netlist.json`: conexiones y placements eléctricos;
- `bom/insight_z1_production_bom.csv`: BOM de Z1;
- `kicad/NFB_Insight_PCBA_v2.kicad_sch`: representación KiCad del circuito;
- `kicad/lib/nfb_footprints.pretty/Honeywell_MPR_LongPort_12Pad.kicad_mod`: footprint del transductor de presión.

## 2. Decisión de presión CO₂

Se reemplaza definitivamente el `MPX5700AP` legacy por:

**Honeywell `MPRLS0030PA00002A`**

Configuración decodificada del número de parte:

- puerto largo (`L`);
- gel de silicona (`S`);
- rango `0…30 psi absolute` (`0030PA`);
- salida I²C con dirección `0x28` (`2`);
- transfer function A: 10 % a 90 % de `2^24` counts (`A`);
- alimentación nominal de diseño: 3.3 V.

Conversión del fondo de escala:

`30 psi × 6.894757293 = 206.843 kPa absolute`

El firmware de referencia establece 180 kPa como umbral de emergencia; por tanto el fondo de escala seleccionado conserva aproximadamente **26.8 kPa de margen de medición** por encima de ese umbral. El datasheet del MPR especifica además 60 psi de overpressure y 120 psi de burst pressure para el rango 0030PA.

La salida de presión deja de ser analógica. `CO2_ADC` desaparece de producción, **A4 queda DNP/Reserva** y `U_CO2` comparte `I2C_SDA/I2C_SCL` del UNO Q con dirección `0x28`.

### Conexión MPR I²C

| Pin MPR | Función | Net V2 |
|---:|---|---|
| 1 | SS | NC en I²C |
| 2 | SDA | `I2C_SDA` |
| 3 | SCL | `I2C_SCL` |
| 4 | VO+ | NC, salida puente no usada |
| 5 | NC | NC |
| 6 | VO- | NC, salida puente no usada |
| 7 | MISO | NC en I²C |
| 8 | EOC | NC en baseline |
| 9 | RES | NC en baseline |
| 10 | VSS | `GND` |
| 11 | NC | NC |
| 12 | VDD | `3V3_RAIL` |

`C_CO2 = 100 nF` se coloca entre VDD y GND como bypass. Se reservan `R_CO2_SDA_PU` y `R_CO2_SCL_PU` de 10 kΩ como footprints **DNP**; los pull-ups globales se resolverán al integrar Z2 para no duplicar innecesariamente resistencias en el bus.

## 3. Familia de conectores de campo

Se congela para pH, ORP, temperatura y DO:

**JST XH `S3B-XH-A(LF)(SN)`**, 3 posiciones, pitch 2.5 mm, side-entry.

Footprint KiCad:

`Connector_JST:JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal`

La selección side-entry permite que el receptáculo se oriente hacia `-Y` cuando se haga placement sobre el FIELD I/O EDGE. El cableado a los acondicionadores DFRobot se resolverá mediante harness; los BNC de los electrodos siguen fuera de la PCBA.

## 4. Protección ESD

Para las líneas eléctricas externas de Z1 se congela:

**Nexperia `PESD3V3U1UL,315`**

Características relevantes del fabricante: VRWM 3.3 V, capacitancia típica 2.6 pF, corriente de fuga típica 1 nA y encapsulado SOD882/DFN1006-2.

Footprint:

`Diode_SMD:D_SOD-882`

Aplicación:

- `D_PH`: `PH_FIELD_SIG → GND`;
- `D_DO`: `DO_FIELD_SIG → GND`;
- `D_TEMP`: `TEMP_1WIRE → GND`;
- `D_ORP`: **después del divisor**, sobre `ORP_ADC → GND`, para no recortar la salida normal de hasta 4.5 V del módulo ORP.

## 5. Filtros y escalamiento

### pH

`SEN0161-V2/SEN0169-V2 → 0…3.0 V`

- `R_PH = 1.0 kΩ, 1 %`
- `C_PH = 100 nF`
- `fc = 1 / (2πRC) = 1591.5 Hz`

La señal filtrada entra en `PH_ADC / A0`.

### ORP

El módulo puede entregar hasta 4.5 V. Se congela:

- `R_ORP_TOP = 10.0 kΩ, 0.1 %`
- `R_ORP_BOT = 20.0 kΩ, 0.1 %`
- relación = `20 / (10 + 20) = 2/3`
- `4.5 V × 2/3 = 3.000 V`

La resistencia de Thévenin vista por `C_ORP` es:

`10 kΩ || 20 kΩ = 6666.7 Ω`

Con `C_ORP = 100 nF`:

`fc ≈ 238.7 Hz`

La salida entra en `ORP_ADC / A1`.

### Temperatura

`KIT0021 / DS18B20` permanece digital:

- `TEMP_1WIRE / A2-D16`
- `R_TEMP_PU = 4.7 kΩ` a `3V3_RAIL`, **poblado onboard**
- `D_TEMP = PESD3V3U1UL`

La V2 no depende de la resistencia/adaptador de un kit externo para que el bus 1-Wire sea funcional.

### DO

`SEN0237-A → 0…3.0 V`

- `R_DO = 1.0 kΩ, 1 %`
- `C_DO = 100 nF`
- `fc ≈ 1591.5 Hz`

La salida entra en `DO_ADC / A5`.

Los valores RC quedan congelados como **baseline de fabricación**. Su desempeño frente a ruido/interferencia se verificará durante bring-up/HIL; un cambio posterior requerirá PR y nueva validación, no una modificación silenciosa durante placement.

## 6. Capacitor común de 100 nF

Se congela `Murata GRM155R71E104KE14D`:

- 100 nF ±10 %;
- X7R;
- 25 V;
- 0402.

Se usa para `C_PH`, `C_ORP`, `C_DO` y `C_CO2`.

## 7. Footprint del MPR

El footprint propio `NFB:Honeywell_MPR_LongPort_12Pad` sigue la geometría recomendada por Honeywell para el encapsulado de puerto largo:

- cuerpo nominal 5.0 × 5.0 mm;
- 12 pads periféricos;
- pitch 1.27 mm;
- puerto nominal Ø2.50 mm;
- sin taladro de referencia gage, porque la variante seleccionada es **absolute**.

La auditoría 3D/STEP se mantiene como gate mecánico antes de placement definitivo.

## 8. Impacto de firmware

El hardware queda adelantado respecto al snapshot de firmware `cf100b38df890f61aed472e934241e145425569b`.

Un PR separado en `Nhilson73/Nebula_ArduinoAPPLab_UNOQ` deberá:

1. sustituir lectura analógica de temperatura por DS18B20/1-Wire en A2/D16;
2. retirar `analogRead(A4)` para presión CO₂;
3. implementar Honeywell MPR por I²C `0x28`;
4. convertir la salida de 24 bits mediante transfer function A (10–90 % de `2^24` counts para 0–30 psi absolute);
5. conservar los límites de seguridad de presión y validar unidades kPa absolute.

## 9. Fuera de alcance

- placement de Z1;
- orientación física final de footprints sobre la board;
- routing;
- planos/zonas de cobre;
- pull-ups globales del bus I²C de Z2;
- arquitectura de potencia;
- modificación del firmware.

## 10. Gate de aceptación

PR #6 solo puede integrarse si:

- `validate_z1_production.py` pasa;
- `validate_sensor_interfaces.py` pasa con baseline PR6;
- `validate_schematic_contract.py` confirma A4 DNP y MPR en I²C;
- ERC KiCad = 0;
- el footprint MPR contiene pads 1…12 y geometría congelada;
- BOM y netlist tienen exactamente las mismas referencias;
- no reaparecen BNC, MPX5700AP, SN6501, AMC1301 ni transformadores de aislamiento en placements de producción;
- DRC/mecánica previa permanece verde.
