# Fase 2 — PR #5: Interfaces reales de sensores Insight

## 1. Motivo de la corrección

El PR #4 congeló correctamente **qué funciones analógicas pertenecen a Insight** y preservó trazabilidad completa al Q-Shield donante. La revisión eléctrica previa al netlist reveló, sin embargo, que varias topologías del donante partían de una premisa incorrecta para el hardware que Nebula realmente utiliza: trataban pH, ORP y DO como si la PCBA recibiera directamente el electrodo/sonda por BNC.

Los módulos DFRobot seleccionados ya incorporan su propia tarjeta acondicionadora. El BNC de la sonda termina en esa tarjeta y la salida hacia el microcontrolador es una interfaz de 3 conductores ya acondicionada. Por tanto, **NFB Insight V2 no debe duplicar en la placa principal un front-end de electrodo crudo** ni arrastrar como baseline la cadena MCP6002 + SN6501 + transformador + AMC1301 del Q-Shield.

Este PR convierte el PR #4 en **trazabilidad histórica del donante** y crea `hardware/sensor_interface_contract.json` como fuente de verdad de producción para las interfaces de sensores.

## 2. Restricción del Arduino UNO Q

El dominio analógico del UNO Q es 3.3 V. Se adopta un objetivo interno más conservador de **máximo 3.05 V** para señales analógicas externas después del escalamiento.

Fuente oficial:

- Arduino UNO Q datasheet: https://docs.arduino.cc/resources/datasheets/ABX00162-datasheet.pdf

Regla de diseño:

> Ninguna salida externa de sensor debe conectarse a A0/A1/A4/A5 sin demostrar que el peor caso permanece dentro del dominio de 3.3 V; para V2 se diseña a ≤3.05 V.

## 3. pH — A0 / PH_ADC

### Hardware real

- Módulo actual: DFRobot Gravity Analog pH Sensor/Meter Pro Kit V2, `SEN0161-V2`.
- Alimentación del acondicionador: 3.3–5.5 V.
- Salida acondicionada: 0–3.0 V.
- Interfaz hacia controlador: 3 conductores tipo PH2.0.
- El BNC pertenece al acondicionador DFRobot, no a la PCBA NFB.

Fuentes oficiales:

- https://www.dfrobot.com/product-1782.html
- https://wiki.dfrobot.com/Gravity__Analog_pH_Sensor_Meter_Kit_V2_SKU_SEN0161-V2

Para operación prolongada se deja como alternativa preferida el kit industrial `SEN0169-V2`, diseñado para monitoreo continuo:

- https://www.dfrobot.com/product-1110.html

### Baseline V2

`SEN0161/SEN0169 conditioner OUT -> conector 3p -> protección de baja fuga -> filtro RC -> PH_ADC`

No se requiere divisor: 3.0 V máximo está dentro del objetivo de interfaz.

La selección final del clamp ESD se deja abierta porque la corriente de fuga importa en señales de instrumentación.

## 4. ORP — A1 / ORP_ADC

### Hardware real

- Módulo: DFRobot Industrial ORP Sensor `SEN0464`.
- Alimentación nominal del acondicionador: 5 V.
- Rango analógico documentado: aproximadamente 0.5–4.5 V.
- Interfaz: PH2.0-3Pin.

Fuente oficial:

- https://wiki.dfrobot.com/Industrial_ORP_Sensor_SKU_SEN0464

### Escalamiento a UNO Q

Se propone provisionalmente divisor de precisión:

- `Rtop = 10.0 kΩ`, 0.1 %
- `Rbottom = 20.0 kΩ`, 0.1 %

Relación:

`K = Rbottom / (Rtop + Rbottom) = 20 / 30 = 0.6666667`

Peor caso contractual de 4.5 V:

`Vadc_max = 4.5 × 0.6666667 = 3.000 V`

Firmware deberá reconstruir la tensión del acondicionador con ganancia inversa `1/K = 1.5` antes de aplicar la ecuación/calibración ORP.

Baseline:

`SEN0464 OUT -> conector 3p -> protección baja fuga -> 10k/20k -> RC -> ORP_ADC`

## 5. Temperatura — A2/D16 / TEMP_1WIRE

### Corrección contractual

El kit DFRobot `KIT0021` usa un **DS18B20 digital 1-Wire**. Por tanto, A2 no debe seguir modelado como `TEMP_ADC`/NTC.

Fuente oficial:

- https://wiki.dfrobot.com/Waterproof_DS18B20_Digital_Temperature_Sensor__SKU_DFR0198_

La función física A2/D16 del UNO Q se conserva, pero la net pasa a:

`TEMP_1WIRE`

Baseline:

`KIT0021/DS18B20 -> conector 3p -> protección digital 3.3 V -> TEMP_1WIRE`

Se reserva footprint opcional de pull-up 4.7 kΩ a 3.3 V, inicialmente DNP/revisión porque el kit comercial ya incluye módulo de resistencia y no debe duplicarse sin necesidad.

### Divergencia de firmware

El firmware baseline aún define A2 como `PIN_TEMPERATURE_ANALOG`. El cambio a DS18B20/1-Wire se realizará en un PR independiente del repositorio de firmware después de aprobar este contrato de hardware.

## 6. Presión CO₂ — A4 / CO2_ADC

### Hallazgo de lifecycle y rango

El MPX5700AP heredado funciona nominalmente alrededor de 5 V y puede entregar aproximadamente 0.2–4.7 V; el datasheet contempla un máximo de salida de aproximadamente 4.813 V. Además, la familia está archivada/no recomendada como nuevo baseline de producción.

Fuentes oficiales:

- https://www.nxp.com/docs/en/data-sheet/MPX5700.pdf
- https://www.nxp.com/part/MPX5700AP

Por tanto:

1. no puede conectarse directamente a A4 del UNO Q;
2. `MPX5700AP` queda marcado `REPLACE_BEFORE_FAB`;
3. el rango y valores definitivos del front-end se congelarán cuando se seleccione el sensor vigente y apropiado para el rango de presión real del biorreactor.

### Red provisional para validar el legado

Solo como compatibilidad de ingeniería, no como BOM final:

- `Rtop = 18.0 kΩ`, 0.1 %
- `Rbottom = 30.0 kΩ`, 0.1 %
- `K = 30/(18+30) = 0.625`

Con `Vin_max = 4.813 V`:

`Vadc_max = 4.813 × 0.625 = 3.008 V`

Esto demuestra que el sensor legado puede probarse sin sobrepasar el objetivo de 3.05 V, pero **no congela el MPX5700AP para fabricación**.

## 7. Oxígeno disuelto — A5 / DO_ADC

### Hardware real

- Módulo: DFRobot Gravity Analog Dissolved Oxygen Sensor `SEN0237-A`.
- Alimentación: 3.3–5.5 V.
- Salida acondicionada: 0–3.0 V.
- El BNC de la sonda pertenece al acondicionador DFRobot.

Fuente oficial:

- https://www.dfrobot.com/product-1628.html

Baseline:

`SEN0237-A conditioner OUT -> conector 3p -> protección baja fuga -> filtro RC -> DO_ADC`

No se requiere divisor para el rango 0–3 V.

## 8. Estrategia de aislamiento

El Q-Shield intentaba integrar aislamiento independiente mediante `SN6501 + transformer + AMC1301` para pH/ORP/DO. Esa cadena no se adopta como baseline V2 porque estamos recibiendo **salidas acondicionadas de módulos comerciales**, no electrodos crudos.

Para interferencia entre múltiples sensores sumergidos en el mismo medio se adopta una estrategia modular de sistema: aislador analógico inline `DFR0504` o equivalente cuando las pruebas lo requieran. Este elemento queda fuera del placement de la PCBA.

Fuente oficial:

- https://www.dfrobot.com/product-1621.html

Esto permite probar aislamiento donde realmente aporta valor sin cargar la PCBA base con tres fuentes aisladas y tres amplificadores de aislamiento antes de haber demostrado la necesidad y el error total permitido.

## 9. Política mecánica de conectores

Se mantiene la convención global:

- borde de servicio: `Y=0`;
- salida del cable: `-Y`;
- el conector de cada sensor queda directamente debajo de su circuito de interfaz en Z1;
- no se colocan BNC de electrodo en la PCBA NFB;
- la familia final de conectores 3p se congela durante placement considerando enclosure, retención y servicio.

## 10. Alcance y gate del PR #5

Este PR **corrige el contrato de interfaz**; deliberadamente todavía no hace placement ni routing.

Debe dejar:

- cinco sensores Insight coherentes con hardware real;
- A2 convertido a `TEMP_1WIRE`;
- pH/DO ≤3.0 V directos al front-end de protección/filtro;
- ORP escalado 4.5 V -> 3.0 V;
- MPX5700AP marcado para reemplazo antes de fabricación y, mientras exista para pruebas, escalado 4.813 V -> 3.008 V;
- BNC fuera de la PCBA base;
- aislamiento analógico inline como opción de sistema, no como tres cadenas obligatorias en placa;
- validadores automáticos verdes.

El **netlist discreto de producción pasa al PR #6**, después de aprobar esta corrección.
