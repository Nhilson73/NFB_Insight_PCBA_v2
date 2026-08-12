# NFB Insight PCBA v2 — EU Compliance Design Gate del Shield

**Estado:** requisito de diseño congelado desde PR #8  
**Alcance:** NFB Insight PCBA v2 como **shield/carrier para Arduino UNO Q**, no como rediseño de la plataforma radio del UNO Q.

## 1. Frontera de cumplimiento

El NFB Insight PCBA v2 se diseña como un shield que utiliza al Arduino UNO Q como host. La arquitectura V2 no añade un transmisor intencional propio, no modifica la cadena RF del UNO Q y no debe modificar antena, matching, potencia de RF ni firmware regulatorio del host.

La documentación de conformidad/certificación del UNO Q se tratará como **evidencia de proveedor del host** y deberá archivarse en el expediente técnico del producto. Esa evidencia no sustituye la evaluación del shield ni de la configuración final integrada.

### Reglas RF inmutables

1. No incorporar Wi‑Fi, Bluetooth, LoRa, celular u otro transmisor intencional en el shield base.
2. No incorporar red de matching, amplificador RF, conmutador RF ni antena propia en la PCBA base.
3. Preservar los keepouts mecánicos/RF y condiciones de integración del UNO Q.
4. No colocar cobre, componentes, cables permanentes o planos del shield dentro de una zona RF/antena que el fabricante del host defina como keepout.
5. Cualquier cambio que altere esta frontera requiere un PR específico de compliance antes de placement/routing.

## 2. Matriz objetivo europea

La siguiente matriz es un **objetivo de ingeniería y expediente**, no una declaración legal de conformidad. La edición armonizada aplicable de cada norma se confirmará con el laboratorio antes del pre-compliance/fabricación final.

| Marco | Referencia objetivo | Frontera NFB Insight V2 |
|---|---|---|
| EMC | 2014/30/EU; objetivo de ensayo EN 55032 Clase B + EN 61000-4-2/-3/-4/-5/-6 | El shield debe diseñarse para minimizar emisiones y soportar inmunidad; la configuración integrada se valida a nivel sistema. |
| RoHS 3 | 2011/65/EU + (EU) 2015/863 | Aplica directamente a PCB, acabado, soldadura y BOM del shield. SAC305 + ENIG son la línea base, pero se exige evidencia RoHS de todos los materiales/componentes. |
| WEEE | 2012/19/EU | Se gestiona al nivel del equipo colocado en mercado: clasificación, marcado y registro por país según corresponda. |
| RED | 2014/53/EU | La función radio proviene del UNO Q. El shield no modifica RF; se conserva evidencia del host y se evalúa la integración final si la radio queda habilitada. |
| REACH | (EC) 1907/2006 | Declaraciones de proveedor y control SVHC para PCB, componentes, conectores, soldadura y materiales relevantes. |
| Marcado CE | Legislación UE aplicable al producto final | Expediente técnico + evaluación de riesgos + informes aplicables + Declaración UE de Conformidad antes de colocar el producto final en mercado. |

## 3. Reglas EMC obligatorias para los próximos PR

### Referencia y retornos

- Mantener una referencia GND continua bajo señales sensibles y digitales rápidas.
- Si `In1.Cu` se congela como GND en el stackup final, queda prohibido usarla para routing de señales.
- Evitar cortes de plano bajo I²C, UART, HX711, reloj y señales analógicas.
- Mantener rutas de retorno cortas y deliberadas en conectores de campo.

### Zonas funcionales

Mantener el gradiente ya congelado:

`UNO Q → Z1 sensores/analógico → Z2 digital bajo ruido → Z3 potencia → Z4 actuadores`

- Los nodos de alto `dV/dt`/`dI/dt` no se desplazan hacia Z1/Z2.
- Drivers de bomba, solenoides y otros actuadores deben permanecer físicamente separados de adquisición.
- El chiller se mantiene por defecto con potencia externa; el shield entrega señal de control salvo revisión explícita.

### Interfaces externas

- Toda línea cableada externa debe tener estrategia ESD definida antes de fabricación.
- Los TVS deben colocarse cerca del punto de entrada del cable durante placement.
- Los conectores de campo continúan sobre `Y=0`, orientados hacia `-Y`.
- El layout debe permitir incorporar filtrado/ferrita cuando las pruebas de pre-compliance lo justifiquen sin romper el retorno de GND.

### Alimentación

- La Fase 3 debe documentar corriente continua, pico y transitorios.
- El filtro de entrada, protección contra transitorios y distribución de 5 V/3.3 V deben revisarse también desde EMC, no solo desde corriente nominal.
- No se liberará fabricación con F1/D2/buck heredados sin revisión documentada de la arquitectura de potencia V2.

## 4. RoHS 3 y REACH — evidencia del shield

Antes de liberar BOM/CPL para fabricación se requiere:

- declaración RoHS vigente para cada MPN poblado o evidencia equivalente del fabricante;
- control de las diez sustancias restringidas RoHS, no únicamente Pb/Hg/Cd;
- declaración REACH/SVHC vigente de proveedores relevantes;
- declaración del fabricante de PCB para laminado, máscara, serigrafía y acabado ENIG;
- evidencia del proceso de ensamblaje y soldadura SAC305 o alternativa aprobada;
- registro de excepciones, si alguna llegara a ser necesaria.

Un MPN sin evidencia no se convierte automáticamente en no conforme, pero **bloquea la liberación de producción** hasta ser calificado o reemplazado.

## 5. Gates de liberación

### Antes de placement

- keepout del UNO Q/RF confirmado contra documentación mecánica del host;
- conectores de campo y zonas ruidosas asignados;
- lista de componentes externos/cables conocida.

### Antes de routing

- stackup y capa de referencia congelados;
- estrategia de retorno GND revisada;
- netclasses y separaciones de potencia definidas;
- ninguna señal atraviesa el keepout RF del host.

### Antes de fabricación RC

- DRC/ERC = 0;
- BOM con estado RoHS/REACH;
- revisión footprint/datasheet;
- plan de pre-compliance EMC/ESD/inmunidad;
- expediente de evidencia del UNO Q archivado.

### Antes de mercado UE

- ensayos/evaluaciones aplicables de la configuración final;
- expediente técnico;
- gestión WEEE donde corresponda;
- Declaración UE de Conformidad y marcado CE del producto final.

## 6. Regla de cambio

Cualquier PR que añada un transmisor, modifique la integración RF del UNO Q, cambie stackup/GND, elimine protección ESD, cambie el esquema de potencia o introduzca un material/MPN sin trazabilidad RoHS/REACH deberá actualizar `compliance/eu_compliance_contract.json` y pasar el workflow **EU Compliance Gate**.
