# Fase 1 — Bootstrap mecánico de NFB Insight PCBA v2

## Objetivo

Crear una base mecánica limpia y verificable antes de migrar el esquemático o realizar placement de componentes.

## Convenciones congeladas

- Origen global `(0,0)` en la esquina inferior izquierda de la envolvente rotada del UNO Q.
- USB-C del UNO Q orientado hacia `-Y`.
- Envolvente inmutable del UNO Q: `53.34 mm × 68.58 mm`.
- Altura total de la PCBA: **68.58 mm fija**.
- Crecimiento permitido únicamente hacia `+X`.
- Ancho inicial de trabajo: **220 mm provisional**; no es dimensión de fabricación.
- Borde `Y=0` reservado como **FIELD I/O EDGE** para conectores y salida de cables del enclosure.

## Patrón mecánico UNO Q rotado

Agujeros de montaje:

| Agujero | X (mm) | Y (mm) |
|---|---:|---:|
| H1 | 50.80 | 13.97 |
| H2 | 45.72 | 66.04 |
| H3 | 17.78 | 66.04 |
| H4 | 2.54 | 15.24 |

Se preservan también las posiciones transformadas del patrón de headers. Los extremos se verifican automáticamente:

- pad 1: `(50.80, 27.94)`
- pad 14: `(50.80, 63.50)`
- pad 32: `(2.54, 18.80)`
- pad 15: `(2.54, 63.50)`

## Zonificación provisional

Las siguientes fronteras son únicamente guías de trabajo y se podrán ajustar después del placement real, excepto Z0:

- Z0 `0–53.34 mm`: UNO Q inmutable.
- Z1 `53.34–105 mm`: analógico y aislamiento.
- Z2 `105–145 mm`: digital y bajo ruido.
- Z3 `145–180 mm`: potencia.
- Z4 `180–220 mm`: actuadores y potencia ruidosa.

## Exclusiones mecánicas

Se incorporan en `Eco1.User` referencias conservadoras heredadas del análisis del Q-Shield para:

- USB-C / PMIC
- JCTL
- SPI2 / JSPI
- Qwiic

Estas referencias **no son todavía keepouts DRC-enforced**. Antes de convertirlas en restricciones definitivas se deben contrastar con el STEP/CAD oficial del UNO Q y con el diseño del enclosure.

## Archivos creados

- `kicad/NFB_Insight_PCBA_v2.kicad_pcb`
- `kicad/NFB_Insight_PCBA_v2.kicad_pro`
- `kicad/fp-lib-table`
- `kicad/lib/nfb_footprints.pretty/Arduino_UNO_Q_Carrier_Rotated.kicad_mod`
- `tools/validate_mechanical.py`
- `.github/workflows/mechanical-kicad.yml`

## Gate de validación

El workflow de GitHub Actions debe:

1. verificar las invariantes mecánicas mediante Python;
2. abrir el board con KiCad 10.0.5;
3. ejecutar DRC a nivel de errores;
4. publicar el reporte DRC como artifact.

No se debe iniciar la Fase 2 hasta revisar visualmente esta base mecánica.
