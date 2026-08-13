# ECO Z2 — testpoints de LOAD_A_POS / LOAD_A_NEG

## Trigger

PR23 / PR19A mostró que la red `LOAD_A_NEG` podía cerrarse únicamente mediante una ruta extremadamente fragmentada (`198 segmentos / 97.795 mm / 4 vías`) mientras `LOAD_A_POS` quedaba sin ruta. El problema no se trató como un simple fallo del router porque ambas nets forman el par analógico más sensible de Z2.

## Qué soporta la fuente del dispositivo

El HX711 es un ADC de precisión de 24 bits para básculas/puentes con PGA de bajo ruido. En Channel A, el rango diferencial de escala completa es del orden de decenas de milivoltios (por ejemplo ±20 mV a gain 128 con AVDD=5 V).

La fuente del dispositivo **no prescribe la posición de los testpoints de NFB Insight**. Por tanto, no se atribuye al fabricante una regla que no publicó.

## Inferencia de ingeniería NFB

`hardware/routing_contract.json` ya exige que `LOAD_A_POS` y `LOAD_A_NEG` se enruten como un **par quieto acoplado** desde `J_LOADCELL` hasta `U_HX`, sin retorno de actuadores entre ambas.

Los testpoints `TP_LOAD_A_POS` y `TP_LOAD_A_NEG` estaban en la banda superior genérica a `Y=58.025 mm`, mientras los pines 7/8 de `U_HX` están alrededor de `Y=25–26 mm`. Mantener esos testpoints obliga a generar ramas largas sobre las entradas crudas del puente.

La inferencia de ingeniería es: para estas dos nets, la integridad analógica domina sobre la regla genérica de “testpoints en banda superior”. Los TP permanecen accesibles en F.Cu, pero se colocan inmediatamente sobre `U_HX` para reducir la longitud de las ramas de prueba.

## Alcance exacto PR24

Solo se mueven:

| Ref | X mm | Y mm | Rotación |
|---|---:|---:|---:|
| `TP_LOAD_A_POS` | 110.250 | 29.300 | 0° |
| `TP_LOAD_A_NEG` | 112.750 | 29.300 | 0° |

No cambian `U_HX`, `J_LOADCELL`, netlist, footprints, zonas, outline, arquitectura ni routing.

## Objetivo de routing posterior

Después del merge del ECO:

1. `J_LOADCELL.3 LOAD_A_POS` y `J_LOADCELL.4 LOAD_A_NEG` deben ir directamente hacia `U_HX.8/.7` como par quieto;
2. los dos TP deben convertirse en **ramas cortas** junto al ADC, no en parte del recorrido principal;
3. el par se revisará conjuntamente por longitud, paralelismo, vías, separación a HMI/I²C y ausencia de dirty-return;
4. PR19A sigue bajo política `28/28 o 0/28`.

## Regla derivada

Una regla mecánica/genérica de accesibilidad de testpoints puede abrir un ECO local cuando routing demuestra que genera una penalización eléctrica desproporcionada sobre una net sensible. Para admitirlo se requiere:

- evidencia de sensibilidad de la interfaz;
- distinción explícita entre dato de fuente e inferencia propia;
- mínimo número de referencias movidas;
- DRC físico completo;
- cero cambio silencioso de arquitectura/netlist;
- conocimiento incorporado al repositorio antes de reanudar routing.
