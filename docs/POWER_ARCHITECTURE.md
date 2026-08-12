# NFB Insight PCBA v2 — Arquitectura de Potencia

**Baseline:** PR #9 — Fase 3  
**Objeto:** shield/carrier del Arduino UNO Q  
**Entrada nominal del sistema:** 12 VDC  
**Fuente de verdad NFB:** `hardware/power_architecture_contract.json`  
**Fuente primaria UNO Q:** repositorios oficiales `arduino/*` en GitHub, según `docs/SOURCE_OF_TRUTH.md`

## 1. Corrección de frontera de potencia

El Q-Shield donante asumía que los rails de 5 V y 3.3 V de la PCBA podían tratarse como si fueran directamente los rails del UNO Q. Para V2 esa suposición se elimina.

La revisión de la documentación fuente oficial en `arduino/docs-content` confirma:

- `VIN` admite **7–24 VDC**;
- USB-C trabaja con **5 V / hasta 3 A**;
- el pin de **5 V de JANALOG también puede recibir una fuente regulada de 5 V** para alimentar el UNO Q;
- la salida del buck de VIN y USB-C se combinan mediante diodos sobre `5V_SYS`;
- `PWR_3P3V` es el rail de 3.3 V generado onboard y exportado a headers;
- la potencia del host está secuenciada por su propio power tree.

Por tanto, la separación de `5V_RAIL` y `3V3_RAIL` del shield **no se justifica como una limitación del UNO Q**. Es una decisión deliberada de NFB Insight V2 para:

- aislar transitorios de HMI/sensores del rail del host;
- reducir caminos de back-feed;
- poder secuenciar las cargas del shield después del host;
- facilitar diagnóstico y pre-compliance EMC.

El método preferido del sistema NFB queda **12 V protegido → VIN del UNO Q**. Aunque Arduino soporta oficialmente alimentación directa de 5 V por JANALOG, ese modo no forma parte del baseline V2.

## 2. Árbol de potencia congelado

```text
12V_IN_RAW
    │
    ├─ D_IN_TVS  SMBJ15A
    │
    └─ U_EFUSE  TPS259470ARPWR
         │
         └── 12V_PROTECTED ──┬── 12V_HOST_VIN ──> J_UNOQ.8 VIN
                             │
                             ├── 12V_LOGIC ──> U_5V TPSM33625 ──> 5V_RAIL
                             │                      ▲
                             │                      └─ EN = UNO_IOREF_3V3
                             │
                             │                 5V_PGOOD
                             │                      │
                             │                      ▼
                             │                 U_3V3 TLV75533
                             │                      │
                             │                      └─> 3V3_RAIL
                             │
                             └── 12V_ACT ──> F_ACT ──> Z4 pump + CO2 solenoid

Chiller: alimentación externa; la PCBA entrega solo señal de control.
```

## 3. Secuencia de encendido

1. La fuente externa aplica 12 V al shield.
2. TVS/eFuse generan `12V_PROTECTED`.
3. `12V_HOST_VIN` alimenta el UNO Q por VIN; el UNO Q genera internamente `5V_SYS`, 3.8 V, 3.3 V y sus rails PMIC.
4. Cuando el host levanta `IOREF`/referencia lógica a 3.3 V, esa señal de alta impedancia habilita el buck de 5 V del shield.
5. `5V_PGOOD` habilita el LDO de 3.3 V.
6. Sensores de campo, HMI y lógica del shield quedan energizados después del host.

La secuencia busca evitar que periféricos externos energicen GPIO del UNO Q cuando el host no está listo. La función exacta de `IOREF` se volverá a contrastar contra schematic/pinout oficial de Arduino antes de materializar el esquemático de potencia; el shield nunca lo conducirá como salida.

## 4. Protección de entrada

### TPS259470ARPWR

Se selecciona como baseline de protección porque integra:

- 2.7–23 V de operación;
- FETs back-to-back de baja resistencia;
- protección contra polaridad inversa;
- bloqueo verdadero de corriente inversa;
- limitación/supervisión de corriente;
- protección de sobretensión;
- soft-start;
- protección térmica.

El objetivo de arquitectura es un límite aproximado de **4.5 A**. El valor exacto de `R_ILIM`, temporización y red de OVLO se congelarán al materializar el esquemático de potencia.

### TVS

`SMBJ15A` queda como familia baseline para la entrada nominal de 12 V. El dimensionamiento final frente a IEC 61000-4-5 se verificará mediante pre-compliance; este PR no declara por sí mismo conformidad a surge.

## 5. Rail 5 V del shield

Se selecciona **TPSM33625RDNR**:

- entrada 3–36 V;
- salida ajustable 1–15 V;
- 2.5 A nominales;
- MOSFETs, inductor y bootstrap integrados;
- dual random spread spectrum;
- diseño orientado a bajo EMI;
- TI lo clasifica como **CISPR 11 Class B compliant-capable** con layout/filtro adecuados.

Para Insight se limita por diseño a **1.5 A continuos**, suficiente como envelope para HMI, módulos pH/ORP/DO y alimentación del LDO 3.3 V con margen. El consumo real de HMI y sensores se verificará en bring-up.

`5V_RAIL` **no se conecta** al pin de 5 V del UNO Q en el baseline. Esto es una decisión NFB; Arduino sí permite oficialmente alimentar el UNO Q con 5 V regulados por JANALOG.

## 6. Rail 3.3 V del shield

Se selecciona **TLV75533PDBVR**:

- 500 mA nominales;
- alto PSRR;
- enable;
- soft-start;
- límite de corriente y protección térmica;
- estable con capacitor cerámico de salida desde 1 µF según TI.

El diseño limita `3V3_RAIL` a **250 mA continuos**. Cargas principales: MPR, DS18B20, HX711, DFR1103, pull-ups I²C, lado A del TXU0202, watchdog y lógica auxiliar.

Este rail se mantiene independiente de `PWR_3P3V` del UNO Q para secuenciación y aislamiento de carga, no porque el host carezca de una salida de 3.3 V.

## 7. Presupuesto de potencia de diseño

| Rama | Presupuesto de diseño |
|---|---:|
| UNO Q por `12V_HOST_VIN` | 18 W |
| Shield `5V_RAIL` | 7.5 W |
| `12V_ACT` pump + solenoide | 18 W |
| **Total de diseño** | **43.5 W** |
| Fuente recomendada | **12 V / 5 A = 60 W** |

El presupuesto no implica consumo constante de 43.5 W; es un envelope conservador para arquitectura. La potencia del chiller no atraviesa la PCBA.

La documentación oficial Arduino recomienda dimensionar la fuente VIN de forma que cubra el presupuesto de 5 V del UNO Q con margen; durante HIL mediremos el consumo real del SKU **ABX00173 4 GB / 32 GB** bajo Wi‑Fi, App Lab y cargas representativas.

## 8. Separación limpia / ruidosa

`12V_PROTECTED` se divide en estrella cerca de la entrada:

- `12V_HOST_VIN`: host;
- `12V_LOGIC`: reguladores y cargas limpias;
- `12V_ACT`: cargas inductivas.

Los retornos de pump/solenoide deben regresar a la región de entrada/estrella y no cruzar las rutas de retorno de Z1/Z2. El nodo de switching del buck permanece confinado a Z3 y nunca se utiliza In1.Cu como capa de señales si esa capa queda congelada como GND.

## 9. Reglas de compliance / EMC

- TVS y eFuse adyacentes al conector de entrada.
- Buck y corriente de actuadores alejados de Z1 y del keepout RF del UNO Q.
- Plano de referencia continuo.
- No routear SW bajo señales analógicas, HX711, I²C ni zona RF.
- Mantener `J_UNOQ.4` y `J_UNOQ.5` fuera del power tree local del shield salvo cambio futuro aprobado por PR.
- Usar `IOREF` únicamente como referencia/enable de alta impedancia y nunca retroalimentarlo.
- La selección final del filtro de entrada se hará con medición de emisiones conducidas y surge/ESD pre-compliance.

## 10. Pendientes para el siguiente PR de potencia

- revisar schematic oficial UNO Q desde repos/documentación Arduino antes de congelar conexión exacta de `IOREF`;
- calcular y congelar `R_ILIM`, OVLO y soft-start del TPS25947;
- seleccionar MPN exacto del conector de entrada y fusible `F_ACT`;
- calcular feedback/capacitores del TPSM33625 para 5.0 V;
- congelar capacitores de TLV75533;
- materializar `power.kicad_sch` con ERC = 0;
- crear netclasses reales de `12V_HOST`, `12V_ACT`, `5V_RAIL` y `3V3_RAIL`;
- validar térmicamente eFuse/buck a 60 °C ambiente objetivo de diseño;
- medir secuencia de encendido y ausencia de back-feed durante HIL.

## Fuentes primarias revisadas

### UNO Q — GitHub oficial Arduino

- `arduino/docs-content/content/hardware/02.uno/boards/uno-q/datasheet/datasheet.md`
- `arduino/docs-content/content/hardware/02.uno/boards/uno-q/tutorials/03.power-specification/content.md`
- `arduino/docs-content/content/hardware/02.uno/carriers/uno-breakout-carrier/datasheet/datasheet.md`

### Componentes del shield — fabricante original

- Texas Instruments `TPS259470ARPWR`.
- Texas Instruments `TPSM33625`.
- Texas Instruments `TLV75533PDBVR`.

La jerarquía completa está en `docs/SOURCE_OF_TRUTH.md`.
