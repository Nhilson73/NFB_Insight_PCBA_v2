# NFB Insight PCBA v2

PCBA/carrier diseñada desde cero para **Nebula Fermentation Insight®**, construida alrededor del factor de forma mecánico inmutable del Arduino UNO Q.

Este repositorio parte intencionalmente de una geometría limpia. El repositorio anterior `Nhilson73/nebula_qshield_pcb` se trata como **donante de ingeniería** para componentes validados de la BOM, símbolos, footprints, nomenclatura de nets, conceptos de prueba y documentación; no se usa como plantilla de placement ni routing.

## Convención mecánica V2 congelada

- Origen global de la board: `(0,0)` en la esquina inferior izquierda de la envolvente rotada del UNO Q.
- UNO Q rotado de modo que su USB-C apunte hacia `-Y`.
- Envolvente inmutable del UNO Q después de la rotación: `53.34 mm × 68.58 mm`.
- Altura de la board congelada en `68.58 mm`.
- La PCBA crece únicamente hacia `+X`.
- Los conectores y cables de campo se ubican a lo largo del borde inferior `Y=0` y orientan su conexión hacia `-Y`, correspondiente al lado de salida de cables del enclosure.
- La zonificación funcional crece de izquierda a derecha: UNO Q → analógico/aislamiento → digital/bajo ruido → potencia → actuadores.

## Primer hito

Congelar la geometría, los activos de ingeniería heredables y la BOM de Insight antes de iniciar placement o routing.
