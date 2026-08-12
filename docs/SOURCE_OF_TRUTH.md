# NFB Insight PCBA v2 — Jerarquía de Fuentes de Verdad

## Regla obligatoria para Arduino UNO Q

Para cualquier decisión que dependa del **Arduino UNO Q**, la fuente primaria de verdad se consulta en los repositorios oficiales de Arduino en GitHub antes de congelar arquitectura, esquemático, PCB, firmware o documentación.

### Prioridad 1 — GitHub oficial Arduino

- Organización: `https://github.com/Arduino`
- Repositorios: `https://github.com/orgs/arduino/repositories`
- En particular, cuando aplique:
  - `arduino/docs-content`
  - `arduino/linux-qcom`
  - repositorios oficiales de App Lab, Bridge, cores, ejemplos o hardware publicados por Arduino.

Para UNO Q, `arduino/docs-content` contiene actualmente la documentación fuente de:

- datasheet `ABX00162-ABX00173`;
- especificación detallada de potencia;
- especificaciones técnicas;
- documentación de carriers oficiales como UNO Breakout Carrier.

### Prioridad 2 — Documentación oficial Arduino

- `https://docs.arduino.cc/hardware/uno-q/`
- `https://docs.arduino.cc/certifications/`
- PDFs oficiales de schematic, datasheet, STEP y pinout publicados por Arduino.

La documentación web/PDF se usa como confirmación y como artefacto de expediente, pero si existe una versión fuente más reciente en repos oficiales, el repositorio oficial se revisa primero.

### Prioridad 3 — Fabricante del componente

Para componentes que **no son Arduino UNO Q**, la fuente primaria es el fabricante original: TI, Honeywell, Nexperia, DFRobot, Phoenix Contact, Littelfuse y el fabricante del MPN correspondiente. Se priorizan datasheets, product pages, PCN/EOL, modelos CAD y documentación de calidad/RoHS/REACH.

### Prioridad 4 — Fuentes secundarias

Distribuidores, foros, blogs, repositorios de terceros y documentos históricos pueden orientar una investigación, pero **no congelan una decisión de producción** cuando existe una fuente primaria disponible.

## Regla de conflicto

Si dos fuentes oficiales parecen contradecirse:

1. revisar fecha/commit/revisión;
2. preferir la fuente oficial más reciente y específica;
3. inspeccionar schematic/CAD oficial cuando la documentación textual no resuelva el punto;
4. registrar la divergencia en el PR;
5. no congelar fabricación hasta resolverla.

## Aplicación a PR #9

La revisión de `arduino/docs-content` corrigió una interpretación previa del pin de 5 V del UNO Q: Arduino documenta oficialmente que el pin de 5 V de JANALOG puede recibir **5 V regulados** para alimentar el host, además de USB-C 5 V y VIN 7–24 V.

NFB Insight V2 mantiene, sin embargo, **12 V protegido → VIN** como método preferido y conserva `5V_RAIL` / `3V3_RAIL` del shield separados. Esa separación es una **decisión de arquitectura NFB**, no una limitación atribuida al UNO Q.

## Snapshot oficial aplicado a PR #16 — pre-placement

Antes de autorizar coordenadas XY de producción se revalidó `arduino/docs-content` en el commit:

`24445a32e249d410c1e4359bdc99d8c0dcb17bd2`

Archivos primarios revisados:

- `content/hardware/02.uno/boards/uno-q/product.md`
- `content/hardware/02.uno/boards/uno-q/datasheet/datasheet.md`
- `content/hardware/02.uno/boards/uno-q/tech-specs.yml`

La revisión confirma para los SKU ABX00162/ABX00173:

- módulo wireless `WCBN3536A`, basado en Qualcomm `WCN3980`;
- Wi‑Fi/Bluetooth con **shared PCB antenna** en el UNO Q;
- soporte oficial para expansión mediante shields/carriers;
- evidencia de certificaciones del host que incluye CE/RED, RoHS, REACH y WEEE.

### Regla RF derivada para NFB

En los archivos fuente de Arduino revisados **no se encontró una dimensión textual oficial para un antenna keepout numérico**. Por tanto:

- NFB **no inventa** una distancia/rectángulo RF atribuido a Arduino;
- ningún footprint de producción NFB se coloca dentro del envelope físico Z0 del UNO Q;
- la extensión del shield comienza en `X=53.34 mm`;
- Z1, inmediatamente adyacente, permanece como zona de sensores/quiet;
- Z3 y Z4, donde viven switching/high-current, continúan desplazadas hacia +X;
- cualquier metal, shield, bracket, PCB apilada o elemento de enclosure sobre la región RF del host queda sujeto a revisión 3D/RF posterior.

Las separaciones resultantes entre el borde +X del host y los guides Z3/Z4 son **consecuencia de la arquitectura NFB**, no especificaciones de antenna clearance de Arduino.

## Gate de ingeniería

Los PR que modifiquen interfaces del UNO Q deben:

- citar o registrar la fuente oficial Arduino revisada;
- actualizar contratos machine-readable si cambia una interpretación;
- actualizar `README.md` cuando cambie arquitectura/estado;
- mantener CI consistente con la fuente de verdad vigente.
