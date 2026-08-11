# NFB Insight PCBA v2 — Revisión de Herencia de BOM

Este archivo registra qué componentes del diseño donante pueden heredarse al arranque de la V2 y cuáles requieren una nueva selección o validación eléctrica/mecánica antes de congelar el esquemático.

## Leyenda de estado

- `ACEPTAR` — puede heredarse al conjunto de esquemático/footprints de la V2.
- `REVISAR` — candidato útil del diseño donante, pero selección, rating o footprint deben aprobarse nuevamente.
- `DESCARTAR` — no forma parte de la línea base Insight V2.
- `RESERVA` — capacidad futura; no debe provocar congestión en el placement de la V2.

## Potencia y protección

| Ref. donante | Parte | Valor donante | Estado V2 | Razón |
|---|---|---|---|---|
| D1 | SMAJ15A | TVS 15 V | REVISAR | El concepto de protección es útil; clamp y energía deben corresponder a la arquitectura final de 12 V. |
| F1 | MF-MSMF110/24X-2 | 1.1 A hold / 2.2 A trip | REVISAR | El rating donante es incompatible con algunos escenarios de corriente Insight documentados. Redimensionar después de congelar los dominios de corriente. |
| D2 | SS34 | Schottky 3 A | REVISAR | Un camino de 3 A puede ser insuficiente si transporta corriente de actuadores. Evaluar cambio de arquitectura antes de simplemente aumentar el diodo. |
| U1 | TPS54302DDCR | buck 12→5 V / 3 A | REVISAR | La función es adecuada; recalcular margen térmico/carga y demanda real del UNO Q/HMI. |
| L1 | 744043004700 | 4.7 µH / 4 A | REVISAR | Revalidar con el punto de operación definitivo del buck y el objetivo de ripple. |
| U2 | AMS1117-3.3 | 3.3 V / 800 mA | REVISAR | Es utilizable, pero deben considerarse eficiencia, térmica y alternativas modernas. |
| FB1 | BLM31PG601SN1L | 600 Ω @ 100 MHz / 2 A | REVISAR | Mantener solo si continúa siendo necesaria la segmentación/filtrado de rails. |

## Analógico / front-end de sensores

| Elemento donante | Estado V2 | Notas |
|---|---|---|
| Op-amps MCP6002-I/SN | ACEPTAR | Mantener para buffering de bajo voltaje cuando la interfaz final del sensor continúe requiriendo acondicionamiento analógico. |
| ESD PESD5V0 / PESD3V3 | ACEPTAR | Mantener concepto y footprints; verificar tensión de trabajo exacta por interfaz. |
| Redes RC antialias | ACEPTAR | Los valores son punto de partida; ajustar con pruebas reales de ancho de banda/ruido. |
| Front-end pH | ACEPTAR | Ubicar directamente sobre el conector PH de campo; minimizar longitud de pista de alta impedancia. |
| Front-end ORP | ACEPTAR | Misma regla de placement que pH. |
| Front-end TEMP | ACEPTAR | Mapeo fuente de verdad: A2. |
| Front-end presión CO2 | ACEPTAR | Mapeo fuente de verdad: A4. |
| Front-end DO | ACEPTAR | Mapeo fuente de verdad: A5; revalidar estrategia de aislamiento. |
| Canal analógico de humedad | DESCARTAR | A3 reservado/DNP en Insight V2. |

## Digital / interfaces

| Elemento donante | Estado V2 | Notas |
|---|---|---|
| Pull-ups I2C 4.7 kΩ | ACEPTAR | Bus D20/D21; el pull-up equivalente final deberá considerar todos los módulos conectados. |
| HX711 | ACEPTAR | Mantener como interfaz Insight para celda de carga. |
| RTC DS3231 | ACEPTAR | Mantener si sigue siendo necesario después de revisar arquitectura de firmware/sistema. |
| Ruta GPS SAM-M8Q | ACEPTAR | El placement deberá considerar antena, cobre y restricciones del enclosure. |
| Interfaz/conector HMI UART | ACEPTAR | Conector de campo sobre borde `Y=0`, orientado hacia `-Y`. |
| Concepto de watchdog externo TPS3823 | ACEPTAR | Se conserva el contrato D4 `MCU_WDI`. |
| Bridge RS485 SC16IS740 + SN74LVC1G04 | RESERVA | No permitir que la futura ruta Signature/RS485 congestione Insight salvo necesidad explícita en V2. |

## Actuadores

| Elemento donante | Estado V2 | Notas |
|---|---|---|
| Control bomba PWM/DIR | ACEPTAR | Mantener función de control; revisar etapa de potencia en zona de potencia ruidosa. |
| Control solenoide CO2 | ACEPTAR | Mantener función de control; salida de campo en `Y=0`. |
| Control chiller | ACEPTAR | Solo señal de control en línea base; la energía de alta potencia del chiller debe permanecer preferiblemente externa a la PCBA. |
| Etapa IR2104 + IRLZ44N | REVISAR | Reevaluar topología, encapsulado y carga real de bomba antes de copiar. |
| Relés HF46F | REVISAR | Definir si conmutan 12 V SELV o cargas externas/red; los clearances dependen de ello. |
| Optoacopladores PC817 | REVISAR | Mantener intención de aislamiento, pero revisar CTR, envejecimiento, velocidad y necesidad real de aislamiento por salida. |
| Ruta PWM válvula proporcional CO2 | DESCARTAR | D9 reservado/DNP en la línea base Insight V2. |

## Conectores

Los números de parte de conectores del BOM donante **no quedan congelados automáticamente** para V2. La selección deberá responder a la nueva arquitectura de enclosure y cableado.

Principio preferido para V2:

- todos los conectores cableados de campo sobre `Y=0` y orientados hacia `-Y`;
- esfuerzos mecánicos de cables pesados/coaxiales terminados en el panel del enclosure cuando sea práctico;
- familias de conectores elegidas por facilidad de servicio, polarización/keying y requisitos ambientales;
- conexiones internas cortas desde interfaces pH/ORP/DO montadas en panel hasta sus front-end analógicos.

## Antes de congelar el esquemático

1. Congelar dominios de 12 V y determinar qué cargas se alimentarán a través de la board.
2. Recalcular corriente máxima continua y de pico por dominio.
3. Seleccionar conector de entrada, protección, ancho de cobre y fusible/PTC según esas corrientes.
4. Congelar estrategia de conectores panel vs. PCBA.
5. Verificar todos los componentes aceptados contra disponibilidad y lifecycle actuales.
6. Generar BOM legible por máquina únicamente después de completar estas revisiones.
