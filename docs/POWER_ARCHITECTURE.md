# NFB Insight PCBA v2 — Arquitectura de Potencia

**Baseline:** PR #9 — Fase 3  
**Objeto:** shield/carrier del Arduino UNO Q  
**Entrada nominal del sistema:** 12 VDC  
**Fuente de verdad:** `hardware/power_architecture_contract.json`

## 1. Corrección de frontera de potencia

El Q-Shield donante asumía que los rails de 5 V y 3.3 V de la PCBA podían tratarse como si fueran directamente los rails del UNO Q. Para V2 esa suposición se elimina.

El datasheet oficial del Arduino UNO Q establece:

- `VIN` del header JANALOG admite **7–24 VDC**;
- USB-C negocia **5 V / 3 A**;
- `IOREF` refleja el rail de 3.3 V y es **salida únicamente**; no debe retroalimentarse;
- `+3V3 OUT` es una salida de potencia del host;
- `+5V USB VBUS` es un pass-through de VBUS USB.

Por tanto, el shield no conecta su `5V_RAIL` a J_UNOQ.5 ni su `3V3_RAIL` a J_UNOQ.4.

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
3. `12V_HOST_VIN` alimenta el UNO Q por VIN; el UNO Q utiliza su propio power tree certificado.
4. Cuando el host levanta `IOREF` a 3.3 V, esa señal de alta impedancia habilita el buck de 5 V del shield.
5. `5V_PGOOD` habilita el LDO de 3.3 V.
6. Sensores de campo, HMI y lógica del shield quedan energizados después del host.

La secuencia evita alimentar entradas del UNO Q desde sensores externos mientras el host está apagado.

## 4. Protección de entrada

### TPS259470ARPWR

Se selecciona como baseline de protección porque integra:

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

- entrada hasta 36 V;
- salida ajustable a 5 V;
- 2.5 A nominales;
- inductor y elementos de potencia integrados;
- spread spectrum;
- arquitectura orientada a bajo EMI;
- TI la especifica como CISPR 11 Class B compliant-capable bajo condiciones de diseño adecuadas.

Para Insight se limita por diseño a **1.5 A continuos**, suficiente para HMI, módulos pH/ORP/DO y alimentación del LDO 3.3 V con margen.

## 6. Rail 3.3 V del shield

Se selecciona **TLV75533PDBVR**:

- 500 mA nominales;
- alto PSRR;
- enable;
- soft-start;
- límite de corriente y protección térmica.

El diseño limita `3V3_RAIL` a **250 mA continuos**. Cargas principales: MPR, DS18B20, HX711, DFR1103, pull-ups I²C, lado A del TXU0202, watchdog y lógica auxiliar.

Este rail es independiente de `PWR_3P3V` del UNO Q.

## 7. Presupuesto de potencia de diseño

| Rama | Presupuesto de diseño |
|---|---:|
| UNO Q por `12V_HOST_VIN` | 18 W |
| Shield `5V_RAIL` | 7.5 W |
| `12V_ACT` pump + solenoide | 18 W |
| **Total de diseño** | **43.5 W** |
| Fuente recomendada | **12 V / 5 A = 60 W** |

El presupuesto no implica consumo constante de 43.5 W; es un envelope de diseño con margen. La potencia del chiller no atraviesa la PCBA.

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
- Mantener `J_UNOQ.4` y `J_UNOQ.5` sin conexión eléctrica al power tree del shield.
- `IOREF` se utiliza exclusivamente como referencia/enable de alta impedancia.
- La selección final del filtro de entrada se hará con medición de emisiones conducidas y surge/ESD pre-compliance.

## 10. Pendientes para el siguiente PR de potencia

- calcular y congelar `R_ILIM`, OVLO y soft-start del TPS25947;
- seleccionar MPN exacto del conector de entrada y fusible `F_ACT`;
- calcular feedback/capacitores del TPSM33625 para 5.0 V;
- congelar capacitores de TLV75533;
- materializar `power.kicad_sch` con ERC = 0;
- crear netclasses reales de `12V_HOST`, `12V_ACT`, `5V_RAIL` y `3V3_RAIL`;
- validar térmicamente eFuse/buck a 60 °C ambiente objetivo de diseño;
- medir secuencia de encendido y ausencia de back-feed durante HIL.

## Fuentes primarias

- Arduino UNO Q datasheet `ABX00162-ABX00173`.
- Texas Instruments `TPS25947` datasheet/product page.
- Texas Instruments `TPSM33625` datasheet/product page.
- Texas Instruments `TLV755P` datasheet/product page.
