# PR30 — PR19B: 4 nets analógicas long-haul

## Objetivo
Cerrar el segundo lote físico de routing después de PR28/PR19A:

- `PH_ADC`
- `ORP_ADC`
- `DO_ADC`
- `PUMP_CURRENT_ADC`

Política: **ALL_OR_NOTHING**. Las cuatro nets o ninguna.

## Baseline

- `main` post-PR28/PR29.
- PR19A persistido: 28/28 nets, 523 segmentos, 24 vías, DRC físico 0 errores.
- 31 nets futuras intactas al inicio de este lote.
- placement/outline/footprints/netlist congelados.

## Reglas

- Clase: `ANALOG_SENSITIVE`.
- In1.Cu: GND only; signal routing prohibido.
- In2.Cu: no analógica sensible.
- Preferir F.Cu; B.Cu solo cuando reduzca cruces o preserve retorno.
- Separación contractual sensitive↔dirty paralela >= 1.00 mm.
- pH/ORP/DO: priorizar corredor quieto desde Z1 hacia J_UNOQ.
- `PUMP_CURRENT_ADC`: mantenerlo separado de `PUMP_OUT1/2`, `12V_ACT` y futuros recorridos dirty de Z4.
- No crear copper zones.
- No tocar las 28 nets PR19A ni las 27 nets posteriores restantes.

## Método

1. Probe físico de endpoints/pads y cobre existente sobre el PCB persistido.
2. Diseñar las cuatro rutas conjuntamente para evitar que una bloquee a otra.
3. Materializar temporalmente y ejecutar KiCad 10.0.5 DRC.
4. Revisar longitud, segmentos, vías, cambios de dirección y retorno futuro sobre In1.GND.
5. Persistir solo cuando 4/4 estén conectadas y DRC errors=0.
6. Actualizar `README.md` antes del merge.

## Gate de aceptación

- 4/4 nets PR19B conectadas.
- 28/28 PR19A preservadas.
- 27 nets futuras restantes con 0 cobre.
- DRC errors=0.
- sin shorts/clearance/courtyard/hole-clearance nuevos.
- In1.Cu signal tracks=0.
- copper zones=0.
- placement/outline/footprints/netlist sin cambios.
- `README.md` actualizado con el estado PR19B y siguiente checkpoint PR19C.
