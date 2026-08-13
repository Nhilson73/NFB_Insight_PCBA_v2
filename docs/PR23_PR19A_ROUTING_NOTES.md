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

## Micro-ruta RT y límite de resolución del planner

Después del ECO PR22 existía un corredor físico válido para el strap `RT→VCC`, pero el ancho disponible para la **centrolinea** de la pista no coincidía con la rejilla A* de `0.25 mm`. Reducir la rejilla de todo el board habría multiplicado la complejidad del algoritmo sin aportar valor al resto del lote.

PR23 resolvió únicamente esa arista con una micro-ruta continua determinista en F.Cu, sin vías. El resultado observado fue `5V_VCC = 9 segmentos / 11.388 mm / 0 vías`. El resto de la net y del board sigue bajo el planner estándar y el DRC completo de KiCad.

**Regla derivada:** cuando una garganta válida es menor que la resolución de la rejilla, no se degrada globalmente todo el router; se puede usar una micro-ruta local explícita si está acotada, documentada y validada por DRC.

## Hallazgo: pad-shape no equivale a endpoint eléctrico

El footprint `TI_RPW0010A_TPS259470A` usa pads compuestos: algunos pines (`1`, `7`, `10`) están construidos con más de un shape SMD que comparte **el mismo número de pad**. Esos shapes sirven para reproducir el land pattern físico, pero eléctricamente KiCad los interpreta como un solo pin.

El router inicial trataba cada shape como un endpoint independiente. Eso hacía que un MST intentara crear cobre adicional entre partes que ya pertenecen al mismo pin y elevaba artificialmente la congestión de `EFUSE_EN_UVLO`, `EFUSE_DVDT` y `EFUSE_ITIMER`.

PR23 v10 separa dos conceptos:

- **ocupación física:** todos los shapes continúan presentes y bloquean espacio según clearance;
- **conectividad lógica:** el árbol usa un solo endpoint por `(referencia, número de pin)`; para `U_EFUSE` se selecciona el shape exterior como breakout.

**Regla derivada:** en footprints compuestos, el router debe deduplicar endpoints por pin lógico sin eliminar ningún shape de la geometría física ni del DRC.

## Evidencia incremental tras ECO PR22

El routing limpio ya consiguió, entre otras, las siguientes redes antes del cierre del lote:

- `DO_FIELD_SIG`, `ORP_FIELD_SIG`, `PH_FIELD_SIG`;
- `5V_FB`: **9 segmentos / 4.56 mm / 0 vías**;
- `5V_VCC`: **9 segmentos / 11.388 mm / 0 vías**;
- `5V_PGOOD`: conectada, aunque su geometría todavía debe simplificarse antes del merge;
- `EFUSE_ITIMER`: **15 segmentos / 7.79 mm / 0 vías**;
- `EFUSE_ILM` y `EFUSE_DVDT`: conectadas.

Esto demuestra que la estrategia de resolver primero las sub-islas más confinadas está desplazando el bloqueo hacia las nets menos críticas, en vez de ocultarlo mediante reducción de reglas.

## Estado

PR23 permanece abierto y **no es mergeable por criterio de ingeniería** hasta que:

- las 28/28 nets locales estén conectadas;
- no exista cobre de lotes futuros;
- DRC físico no presente shorts/clearance/courtyard nuevos;
- `In1.Cu` permanezca sin signal routing;
- la calidad geométrica del lote sea revisada, especialmente rutas largas/fragmentadas como `5V_PGOOD`.
