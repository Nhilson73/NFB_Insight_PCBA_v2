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

Para componentes que **no son Arduino UNO Q**, la fuente primaria es el fabricante original:

- Texas Instruments;
- Honeywell;
- Nexperia;
- DFRobot para sus módulos propios;
- fabricante del conector, sensor, regulador u otro MPN correspondiente.

Se priorizan datasheets, product pages, PCN/EOL, modelos CAD y documentación de calidad/RoHS/REACH del fabricante.

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

## Gate de ingeniería

Los PR que modifiquen interfaces del UNO Q deben:

- citar o registrar la fuente oficial Arduino revisada;
- actualizar contratos machine-readable si cambia una interpretación;
- actualizar `README.md` cuando cambie arquitectura/estado;
- mantener CI consistente con la fuente de verdad vigente.
