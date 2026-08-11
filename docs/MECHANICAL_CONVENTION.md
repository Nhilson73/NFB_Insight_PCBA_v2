# NFB Insight PCBA v2 — Convención Mecánica

**Estado:** CONGELADO para el arranque de V2  
**Fuente donante:** `Nhilson73/nebula_qshield_pcb/docs/UNO_Q_FORM_FACTOR.md`

## 1. Sistema global de coordenadas

La nueva PCBA utiliza una convención cartesiana explícita y única:

- Origen global `(0,0)` = esquina inferior izquierda de la **envolvente rotada del UNO Q**.
- `+X` = dirección de expansión de la PCBA.
- `+Y` = dirección superior dentro del enclosure.
- `-Y` = dirección de salida de cables y servicio.
- El USB-C del Arduino UNO Q apunta hacia `-Y`.

La board no deberá crecer hacia X negativo ni Y negativo.

## 2. Envolvente inmutable del UNO Q

Envolvente oficial del UNO Q antes de rotarlo:

- Ancho: 68.58 mm
- Alto: 53.34 mm

Después de rotar el UNO Q para que el USB-C apunte hacia `-Y`, la envolvente inmutable queda:

- `X = 0.00 ... 53.34 mm`
- `Y = 0.00 ... 68.58 mm`

Por tanto:

- **La altura de la NFB Insight PCBA v2 queda congelada en 68.58 mm.**
- El ancho total de la board es variable y crecerá únicamente hacia `+X`, según lo determine el placement real.

## 3. Transformación de coordenadas desde la referencia donante

El repositorio donante expresa las coordenadas mecánicas del UNO Q en la orientación anterior. Para la orientación V2 se utilizará:

```text
X_v2 = 53.34 - Y_donor
Y_v2 = X_donor
```

### Centros de los agujeros de montaje rotados

| Agujero | X_v2 (mm) | Y_v2 (mm) |
|---|---:|---:|
| H1 | 50.80 | 13.97 |
| H2 | 45.72 | 66.04 |
| H3 | 17.78 | 66.04 |
| H4 | 2.54 | 15.24 |

Estas cuatro posiciones son inmutables mientras no cambie la especificación mecánica oficial del Arduino UNO Q.

## 4. Keepouts del UNO Q

El diseño V2 debe preservar acceso físico y clearance para todas las funciones del UNO Q, incluyendo como mínimo:

- USB-C
- botón de power
- JCTL
- SPI2 / JSPI
- QWIIC
- JMEDIA / JMISC cuando aplique
- volumen de acople de headers/shield
- tornillería, standoffs y elementos de montaje

Los keepouts son restricciones mecánicas obligatorias, no sugerencias de placement.

## 5. Borde de I/O de campo

Todo el borde inferior de la board en `Y = 0` queda designado como:

> **FIELD I/O EDGE**

Reglas:

1. Todos los conectores cableados de campo deberán ubicarse sobre el borde `Y=0` o inmediatamente adyacentes a él.
2. La dirección de conexión de los cables deberá apuntar hacia `-Y` siempre que la geometría del conector lo permita.
3. Los conectores de sensores deberán quedar directamente debajo, o tan cerca como sea práctico, de su circuito de front-end correspondiente.
4. No se rutearán señales de sensores de alta impedancia por largas distancias antes de su acondicionamiento.
5. Las cargas mecánicas de cables pesados o coaxiales deberán terminar preferiblemente en el panel del enclosure y no directamente en la PCBA.

## 6. Zonificación funcional hacia +X

El orden previsto de izquierda a derecha es:

```text
X = 0
│
├── Z0  UNO Q INMUTABLE
├── Z1  ANALÓGICO / FRONT-END DE SENSORES / AISLAMIENTO GALVÁNICO
├── Z2  DIGITAL / BAJO RUIDO / HX711 / I2C / HMI / RTC / GPS
├── Z3  GESTIÓN DE POTENCIA
└── Z4  ACTUADORES / POTENCIA RUIDOSA / SALIDAS DE CAMPO
                                      → +X
```

Los anchos de las zonas **no quedan congelados** en esta fase. Se determinarán a partir del placement real y de la manufacturabilidad.

## 7. Principios de placement

- Los circuitos analógicos sensibles permanecerán lo más cerca posible de su conector de campo.
- Los loops de conmutación del buck y los nodos de conmutación de actuadores se mantendrán alejados de los front-end de pH, ORP y DO.
- Se preservará un plano de referencia continuo bajo señales de bajo nivel.
- La congestión del autorouter nunca justificará violar la arquitectura de zonas.
- La ubicación del GPS deberá revisarse considerando antena, cobre y enclosure.
- Los test points deberán continuar accesibles para servicio después del ensamblaje del enclosure.

## 8. Criterio de liberación

Ningún routing se considerará con intención de producción hasta cumplir:

- coordenadas transformadas del UNO Q verificadas contra la referencia mecánica oficial;
- todos los keepouts representados en KiCad;
- orientación de los conectores del borde `Y=0` revisada en 3D;
- salida de cables del enclosure confirmada;
- límites de zonas revisados a partir del placement real y no de dibujos estimados.
