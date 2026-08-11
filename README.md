# NFB Insight PCBA v2

PCBA/carrier diseñada desde cero para **Nebula Fermentation Insight®**, construida alrededor del factor de forma mecánico inmutable del Arduino UNO Q.

Este repositorio parte intencionalmente de una geometría limpia. El repositorio anterior `Nhilson73/nebula_qshield_pcb` se trata como **donante de ingeniería** para componentes, símbolos, footprints, nomenclatura, conceptos de prueba y trazabilidad; no se usa como plantilla de placement, routing ni como autoridad automática de topología eléctrica.

## Convención mecánica V2 congelada

- Origen global de la board: `(0,0)` en la esquina inferior izquierda de la envolvente rotada del UNO Q.
- UNO Q rotado de modo que su USB-C apunte hacia `-Y`.
- Envolvente inmutable del UNO Q después de la rotación: `53.34 mm × 68.58 mm`.
- Altura de la board congelada en `68.58 mm`.
- La PCBA crece únicamente hacia `+X`.
- Los conectores y cables de campo se ubican a lo largo del borde inferior `Y=0` y orientan su conexión hacia `-Y`, correspondiente al lado de salida de cables del enclosure.
- La zonificación funcional crece de izquierda a derecha: UNO Q → sensores/interfaz → digital/bajo ruido → potencia → actuadores.

## Baseline eléctrico de sensores

Desde PR #5, la fuente de verdad de las interfaces es `hardware/sensor_interface_contract.json`.

- pH A0 y DO A5 reciben señales ya acondicionadas de 0–3 V desde sus módulos DFRobot.
- ORP A1 recibe la salida acondicionada y la escala a un máximo de 3.0 V antes del UNO Q.
- Temperatura usa `KIT0021/DS18B20`: A2/D16 es `TEMP_1WIRE`, no una entrada NTC/ADC.
- Presión CO₂ A4 permanece analógica, pero el `MPX5700AP` legacy debe sustituirse antes de fabricación.
- Los BNC de electrodos permanecen en los acondicionadores OEM; no son conectores de la PCBA base.
- El aislamiento analógico de sondas se evalúa a nivel de sistema mediante módulo inline cuando las pruebas de interferencia lo justifiquen.

`hardware/analog_insight_manifest.json` y `bom/insight_analog_inheritance.csv` se conservan como **trazabilidad del Q-Shield donante**, no como BOM/topología de producción.

## Estado

Geometría, contrato UNO Q e interfaces reales de sensores están congelados. El siguiente hito es materializar el netlist discreto de sensores después de cerrar sensor de presión CO₂, conectores, protección y filtros.
