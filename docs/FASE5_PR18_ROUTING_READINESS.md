# Fase 5 — PR #18: Routing Readiness

## Objetivo

PR #18 convierte el placement aprobado del PR #17 en una base segura para iniciar routing. **No añade cobre.** Congela clases, capas, dominios de ruido, retornos y reglas de cruce antes de que PR #19 materialice pistas, vías o planos.

## Geometría heredada e inmutable

- Origen global: `(0,0)`.
- USB-C UNO Q: `-Y`.
- FIELD I/O EDGE: `Y=0`, cables hacia `-Y`.
- Board: `242.34 × 68.58 mm`.
- Crecimiento permitido: únicamente `+X`, aunque PR #18 no cambia geometría.
- Z0: `0.00 → 53.34 mm`.
- Z1: `53.34 → 108.84 mm`.
- Z2: `108.84 → 163.34 mm`.
- Z3: `163.34 → 198.34 mm`.
- Z4: `198.34 → 242.34 mm`.

PR #18 no puede modificar XY, rotaciones, footprints, board outline ni netlists.

## Política de capas

| Capa | Intent congelado |
|---|---|
| `F.Cu` | loops locales, front-end analógico y conexiones críticas/cortas |
| `In1.Cu` | **GND continuo; signal routing prohibido** |
| `In2.Cu` | distribución de potencia; sin señales analógicas sensibles |
| `B.Cu` | señales secundarias/low-speed y recorridos largos cuando convenga |

Dentro de Z0 solo se permitirán en PR #19 escapes directos y mínimos desde/hacia pads de `J_UNOQ`. No se permiten loops de switching ni salidas de actuadores en Z0.

La fuente primaria Arduino revisada no publicó una distancia numérica de keepout de antena; por tanto NFB no inventa una. La revisión de cobre/enclosure/RF sigue siendo gate de release.

## Cobertura de nets

`hardware/routing_contract.json` clasifica exactamente las **59 nets de producción**, una sola vez cada una. El gate CI falla ante:

- una net sin clase;
- una net asignada a dos clases;
- una net extra;
- reaparición de nets prohibidas;
- debilitamiento de las clases de potencia congeladas desde PR #10.

## Dominios de routing

### Entrada y potencia

- `12V_IN_RAW` / `12V_PROTECTED`: clase `PWR_INPUT_5A`, mínimo `2.00 mm`, clearance `0.50 mm`.
- `12V_HOST_VIN` / `12V_LOGIC` / `12V_ACT`: `PWR_12V_BRANCH`, mínimo `1.00 mm`.
- `5V_RAIL`: mínimo `0.75 mm`.
- `3V3_RAIL`: mínimo `0.40 mm`.
- `12V_ACT` no atraviesa Z1/Z2.

### Actuadores

`PUMP_OUT1`, `PUMP_OUT2` y `CO2_SOL_POS` forman `ACTUATOR_OUTPUT`. Permanecen en Z4, alejados de analógica sensible, y sus retornos deben cerrar hacia la estrella Z3/Z4 sin cruzar Z1/Z2.

### Analógica sensible

`PH_ADC`, `ORP_ADC`, `DO_ADC`, `LOAD_A_POS`, `LOAD_A_NEG`, `HX_VBG` y `PUMP_CURRENT_ADC` forman `ANALOG_SENSITIVE`.

Reglas especiales:

- referencia continua a `In1.Cu/GND`;
- separación paralela mínima contractual de `1.00 mm` frente a nets dirty;
- load-cell como par quieto desde `J_LOADCELL` hasta `U_HX`;
- `PUMP_CURRENT_ADC`, al cruzar desde Z4 hasta UNO Q, debe usar el corredor más silencioso disponible y evitar los loops de entrada/buck de Z3.

### Front-end de campo

`PH_FIELD_SIG`, `ORP_FIELD_SIG` y `DO_FIELD_SIG` son locales de Z1 y deben permanecer lo más cortos posible entre conector, ESD/protección y acondicionamiento. Vías antes del nodo acondicionado quedan fuertemente desaconsejadas.

### Control sensible

Feedback/programación de eFuse/buck, `PUMP_SR_CFG` y `CO2_ILIM` permanecen locales a sus IC. El `TPSM33625` no expone un nodo SW externo; una net de producción llamada `SW` queda prohibida.

### Chiller

`CHILLER_CONTACT_A/B` forman `CHILLER_DRY_CONTACT`:

- SELV `≤48 V` solamente;
- **NO MAINS**;
- confinadas a Z4/lado aislado del PhotoMOS;
- sin unión intencional a GND ni a rails lógicos.

## Estado DRC heredado

PR #17 cerró errores físicos de placement. PR #18 conserva exactamente el mismo PCB sin routing:

- tracks = `0`;
- vías = `0`;
- copper zones = `0`;
- deuda de `unconnected_items` permanece intencional hasta PR #19;
- warnings de silkscreen/rotulación siguen acotados y no habilitan Gerbers.

## Gate para PR #19

PR #19 podrá materializar cobre únicamente si PR #18 demuestra:

1. 59/59 nets cubiertas una sola vez;
2. netclasses de potencia PR #10 no debilitadas;
3. board y placement PR #17 intactos;
4. `In1.Cu` congelado como GND sin señales;
5. cero tracks/vías/zones introducidos por PR #18;
6. CI completo verde.

PR #19 será el primer PR autorizado para routing físico.
