# PR #4 — Arquitectura analógica y aislamiento Insight

## Objetivo

Heredar del Q-Shield únicamente la ingeniería útil del bloque analógico para **NFB Insight PCBA v2**, sin copiar placement, routing ni el canal de humedad eliminado.

Este PR congela la **arquitectura por canal, la trazabilidad de BOM y los gates de revisión**. No declara todavía como validada la implementación eléctrica completa de los front-end sensibles.

## Fuente de verdad donante

La fuente primaria es `Nhilson73/nebula_qshield_pcb/kicad/analog_acquisition.kicad_sch` en el commit `2aa42a08d675ad01d18e79157f46008357dbcb0c`.

`docs/04_BOM_PRODUCTION.md` se conserva como fuente secundaria porque se detectaron referencias/valores históricos que no coinciden completamente con el esquemático real. Cuando exista conflicto, prevalece el circuito KiCad donante y el componente queda marcado para revisión.

## Canales Insight congelados

| Canal | UNO Q | Net V2 | Dominio | Conector donante | Decisión |
|---|---|---|---|---|---|
| pH | A0 | `PH_ADC` | Aislado | BNC J2 | Heredar con revisión eléctrica |
| ORP | A1 | `ORP_ADC` | Aislado | BNC J3 | Heredar con revisión eléctrica |
| Temperatura | A2 | `TEMP_ADC` | GND compartido | JST-XH J6 | Heredar con revisión de topología NTC |
| CO₂ | A4 | `CO2_ADC` | GND compartido | JST-XH J4 | Heredar con revisión de rango/transductor |
| DO | A5 | `DO_ADC` | Aislado | BNC J5 | Heredar con revisión del tipo exacto de sonda |
| Humedad | A3 | — | — | J7 | **No migrar** |

## Aislamiento heredado

Los canales húmedos pH, ORP y DO conservan como arquitectura donante:

`front-end → MCP6002 → SN6501 + transformador 750315371 → AMC1301 → ADC`

con dominios aislados independientes para pH, ORP y DO. Esta topología queda como **baseline sujeto a revisión de datasheet**; especialmente deben verificarse impedancia de entrada, rangos, ganancia, bias y compatibilidad con la sonda definitiva antes de congelar el netlist de producción.

## Componentes descartados expresamente

No se migran `J7`, `D8`, `R17`, `R18` ni `C23`, correspondientes al antiguo canal A3/HUM.

## Mecánica de conectores

Todos los conectores de campo pertenecen funcionalmente a Z1 y deberán ubicarse sobre el borde de servicio `Y=0`, orientados hacia `-Y`.

Para pH/ORP/DO se mantiene como preferencia mecánica que el BNC sea panel-mount en el enclosure y que la conexión hacia la PCBA sea corta, evitando transferir esfuerzos del cable directamente a la board.

## Entregables del PR

- `hardware/analog_insight_manifest.json`: contrato de herencia por canal.
- `bom/insight_analog_inheritance.csv`: BOM analógica trazable al donante.
- `kicad/analog_insight.kicad_sch`: hoja KiCad de arquitectura Z1.
- `tools/validate_analog_manifest.py`: gate automático contra el contrato del PR #3.
- `.github/workflows/analog-insight.yml`: validación con KiCad 10.0.5.

## Lo que deliberadamente queda pendiente

1. Revisión de datasheets y rangos eléctricos de cada front-end.
2. Materialización del netlist discreto de producción en la hoja analógica.
3. Selección definitiva de conectores de panel/board.
4. Footprints y placement dentro de Z1.
5. Routing y definición física de islas de aislamiento.

Esto evita repetir el error de heredar un circuito completo solo porque ERC/DRC sea cero: primero se congela qué queremos conservar; después se valida eléctricamente y se materializa.
