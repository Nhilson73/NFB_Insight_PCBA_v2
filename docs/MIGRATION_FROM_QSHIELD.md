# Migración desde `nebula_qshield_pcb`

El repositorio anterior del Q-Shield se considera un **donante de ingeniería**, no una plantilla de layout de PCB.

## Heredar

- Selecciones de componentes y MPN ya validados.
- Símbolos y footprints de KiCad ya verificados contra la pieza física.
- Patrón de headers/shield del UNO Q y su referencia mecánica oficial.
- Nombres de nets que ya coinciden con el contrato del firmware Insight.
- Conceptos de protección ESD para interfaces de sensores.
- Intención de diseño de los front-end analógicos para pH, ORP, temperatura, presión de CO2 y DO.
- Interfaz HX711/celda de carga.
- Arquitectura RTC, GPS, HMI UART e I2C.
- Arquitectura de watchdog.
- Metadata BOM/DNP que siga siendo aplicable a Insight.
- Scripts existentes de validación, incluyendo paridad esquemático↔PCB.
- Modelos 3D y documentación de enclosure/cables que resulten útiles después de revisión.

## Revisar antes de heredar

Estos elementos no se copiarán sin una nueva aprobación:

- cadena de protección de entrada de 12 V y ratings de corriente;
- dimensionamiento de F1 PTC;
- dimensionamiento/topología de D2 para polaridad inversa;
- margen térmico y de corriente del buck;
- distribución de potencia de actuadores;
- arquitectura de potencia del chiller;
- uso de contactos de relé y clasificación de clearances;
- familias de conectores y estrategia panel vs. PCBA;
- implementación del aislamiento galvánico e islas de potencia aisladas;
- cualquier componente cuya asignación Tier/DNP sea inconsistente en la documentación donante.

## No heredar

- Coordenadas de componentes de la PCB anterior.
- Tracks, vias ni salida del autorouter.
- Pours/zones de cobre.
- `Edge.Cuts` de la board donante.
- Dimensiones de la board donante.
- Compromisos de routing relacionados con `In1.Cu`.
- Clearances reducidos únicamente para lograr pasar el routing.
- Estado de nets desconectadas.

## Contrato de señales Insight congelado para el arranque

La V2 adopta el siguiente mapeo como fuente de verdad inicial, pendiente de una comprobación directa contra el firmware:

| Pin UNO Q | Función V2 | Tier |
|---|---|---|
| A0 | PH_ADC | Insight |
| A1 | ORP_ADC | Insight |
| A2 | TEMP_ADC | Insight |
| A3 | RESERVADO / humedad eliminada | DNP |
| A4 | CO2_ADC | Insight |
| A5 | DO_ADC | Insight |
| D0 | HMI_RX | Insight |
| D1 | HMI_TX | Insight |
| D2 | HX711_DOUT | Insight |
| D3 | HX711_SCK | Insight |
| D4 | MCU_WDI | Insight |
| D5 | PUMP_PWM | Insight |
| D6 | PUMP_DIR | Insight |
| D7 | CO2_SOL_CTL | Insight |
| D8 | CHILLER_CTL | Solo control Insight |
| D9 | RESERVADO / válvula proporcional eliminada | DNP |
| D10 | RS485_IRQ | Reserva para futura ruta Signature |
| D13 | LED_STATUS | Insight |
| D20 | I2C_SDA | Insight |
| D21 | I2C_SCL | Insight |

## Principio de producto V2

La V2 se diseña primero como **NFB Insight**, no como una board universal congestionada para todos los tiers futuros.

La futura capacidad Signature deberá habilitarse mediante puntos de expansión deliberados, interfaces reservadas o una daughterboard opcional cuando esa solución sea eléctrica y mecánicamente más limpia que poblar circuitería no utilizada en cada PCBA Insight.
