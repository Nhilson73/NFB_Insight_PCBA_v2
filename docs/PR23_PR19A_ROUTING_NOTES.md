# PR23 / PR19A — notas de routing local

## Alcance

PR23 materializa únicamente las **28 nets locales** definidas en `hardware/routing_batches_contract.json`. La política es `ALL_OR_NOTHING`: 28/28 o no merge.

## Hallazgo: `5V_VCC` no debe tratarse como MST geométrico genérico

`5V_VCC` tiene tres endpoints con funciones físicas distintas:

- `U_5V.8` = `VCC`, salida del LDO interno del TPSM33625;
- `C_5V_VCC.1` = bypass local de VCC;
- `U_5V.11` = `RT` en la variante TPSM33625RDNR.

La configuración congelada del proyecto es `PIN11_RT_TO_PIN8_VCC`. La documentación primaria de TI para TPSM33625 establece que, en la variante con pin RT, **RT conectado a VCC selecciona 1 MHz**; TI también recomienda 1 MHz para el ejemplo de salida a 5 V usado por la arquitectura del proyecto.

Por tanto, el objetivo físico no es “conectar tres nodos equivalentes con el árbol Manhattan más corto”. La topología intencional es:

1. `C_5V_VCC → U_5V.8` como lazo de bypass VCC crítico y corto;
2. `C_5V_VCC → U_5V.11` como strap de configuración RT→VCC.

El intento anterior dejaba al MST elegir `C_VCC→pin8` y luego `pin8→pin11`; el segundo tramo quedaba atrapado por la geometría fina del RDN0011A. PR23 v4 congela explícitamente la topología estrella con el capacitor como centro físico.

## Regla derivada

**Las nets multipunto con endpoints de roles eléctricos distintos no se deben optimizar exclusivamente con MST geométrico.** Primero se identifica el nodo físico crítico (bypass, feedback, estrella, terminación, etc.) y después se define el árbol de conexión que preserve esa función.

Ejemplos donde esta regla deberá revisarse en lotes futuros:

- rails multipunto `3V3_RAIL` / `5V_RAIL`;
- `ACT_FAULT_N` wired-OR;
- I²C con múltiples dispositivos;
- GND/retornos y estrella Z3/Z4.

## Clearances locales y KiCad

El proyecto ya contiene una regla local para el land pattern RDN0011A porque TI requiere una separación interna de cobre de `0.125 mm` dentro del footprint. Esa regla aplica solo entre objetos del propio `U_5V`; el routing externo conserva los clearances del board.

Antes de añadir cualquier excepción adicional, PR23 debe intentar primero resolver la topología con el clearance normal. Si una garganta del breakout demostrada por DRC requiere neckdown, la excepción deberá ser:

- específica a `5V_VCC`;
- limitada al courtyard de `U_5V`;
- nunca global;
- validada por KiCad DRC;
- documentada aquí y en el `.dru`.

KiCad soporta reglas custom por net/footprint y reglas de neckdown acotadas dentro de un courtyard; esa capacidad solo se utilizará si la topología estrella por sí sola no basta.

## Evidencia inicial tras ECO PR22

El primer run de PR23 sobre el placement corregido ya consiguió:

- `DO_FIELD_SIG` ruteada;
- `ORP_FIELD_SIG` ruteada;
- `PH_FIELD_SIG` ruteada;
- `5V_FB` ruteada en **9 segmentos, 4.56 mm y 0 vías**.

Esto confirma que el ECO de placement Z3 eliminó la congestión principal del lazo FB. El bloqueo siguiente se aisló a la selección del árbol de `5V_VCC`, no a `5V_FB`.

## Estado

PR23 permanece abierto y **no es mergeable por criterio de ingeniería** hasta que:

- las 28/28 nets locales estén conectadas;
- no exista cobre de lotes futuros;
- DRC físico no presente shorts/clearance/courtyard nuevos;
- `In1.Cu` permanezca sin signal routing;
- la calidad geométrica del lote sea revisada.
