# Fase 5 — PR19B: routing analógico long-haul

## Objetivo

Cerrar el segundo lote incremental de routing sobre el checkpoint PR19A sin modificar placement, outline, netlist ni reglas físicas.

## Alcance

PR19B materializa exclusivamente cuatro nets `ANALOG_SENSITIVE`:

- `PH_ADC`
- `ORP_ADC`
- `DO_ADC`
- `PUMP_CURRENT_ADC`

Las 27 nets de PR19C/PR20A/PR20B permanecen sin cobre.

## Topología aplicada

`PH_ADC`, `ORP_ADC` y `DO_ADC` resuelven sus conexiones locales en `F.Cu` y usan corredores long-haul anidados en `B.Cu` hacia `J_UNOQ`. `PUMP_CURRENT_ADC` sale de Z4, evita el corredor de switching/entrada de Z3 y cruza el corredor de `DO_ADC` mediante cambio controlado de capa en la banda superior.

No existe signal routing en `In1.Cu`; esa capa continúa reservada para el plano GND de PR20B. No se añadieron copper zones.

## Resultado físico

Sobre PR19A se añadieron:

- 32 segmentos;
- 7 vías;
- ancho de señal: 0.20 mm;
- vía mínima: 0.60/0.30 mm.

Checkpoint acumulado:

- PR19A: 28/28 nets preservadas;
- PR19B: 4/4 nets conectadas;
- 555 segmentos totales;
- 31 vías totales;
- 27 nets futuras sin cobre;
- `In1.Cu`: 0 signal tracks;
- copper zones: 0;
- unconnected: 192.

## DRC

KiCad 10.0.5: **0 errores**.

Se preserva exactamente la deuda conocida de 255 warnings, todos de texto/serigrafía:

- `silk_edge_clearance`: 13;
- `text_height`: 1;
- `silk_overlap`: 173;
- `silk_over_copper`: 68.

No se introdujo ningún nuevo tipo de violación.

## Gobernanza

La política `ALL_OR_NOTHING` se cumplió: el lote solo se acepta con 4/4 nets cerradas, DRC físico sin errores, PR19A intacto y lotes posteriores sin cobre.

El PCB persistido es `kicad/NFB_Insight_PCBA_v2.kicad_pcb`. La evidencia machine-readable vive en `hardware/pr19b_analog_routing_manifest.json` y `hardware/pr19b_analog_probe.json`; el gate final es `tools/validate_pr19b_analog.py`.

Siguiente checkpoint, únicamente después del merge: **PR19C — 16 nets digital/control inter-zona**.
