# Base de conocimiento de routing — NFB Insight PCBA v2

## Propósito

Este documento conserva el conocimiento de ingeniería aprendido durante la transición de placement a routing de producción. Su objetivo es evitar que decisiones críticas queden dispersas entre conversaciones, commits experimentales o logs de CI.

La regla de trabajo desde Fase 5 es **divide y vencerás**: cada lote de cobre debe ser pequeño, completo, reproducible, auditable y mergeable de forma independiente.

## Autoridad

La jerarquía de autoridad para routing es:

1. `hardware/routing_contract.json` — reglas eléctricas, netclasses, capas, anchos y clearances congelados en PR18.
2. `hardware/routing_batches_contract.json` — partición vigente de 60 nets; PR19D añadió `5V_HMI` después de PR19C sin reescribir manifests históricos.
3. `hardware/placement_manifest.json` — placement PR17 + cadena ECO vigente.
4. JSON/BOM de Z1/Z2/Z3/Z4 — conectividad y footprints de producción.
5. `kicad/NFB_Insight_PCBA_v2.kicad_dru` — reglas custom efectivas de KiCad.
6. KiCad 10.0.5 + DRC — autoridad física final para cobre.
7. `docs/KICAD_TOOLING_NOTES.md` — reglas técnicas de tooling.
8. Este documento — narrativa, rationale y lecciones aprendidas.

Ningún router, script u optimización puede debilitar los contratos anteriores para obtener un resultado “verde”.

## Geometría congelada

- Board: `242.34 × 68.58 mm`.
- Altura inmutable: `68.58 mm`.
- Crecimiento solo `+X`.
- Z0: `0.00 → 53.34 mm`.
- Z1: `53.34 → 108.84 mm`.
- Z2: `108.84 → 163.34 mm`.
- Z3: `163.34 → 198.34 mm`.
- Z4: `198.34 → 242.34 mm`.
- `Y=0` = FIELD I/O EDGE.
- Cables hacia `-Y`.
- Placement global PR17 permanece congelado; solo se permiten ECOs locales contractuales y mergeados antes de reiniciar routing.

## Política de capas

- `F.Cu`: señales críticas/locales, front-end analógico y loops compactos.
- `In1.Cu`: referencia GND continua; **sin signal routing**.
- `In2.Cu`: distribución de potencia y troncales de baja impedancia; sin analógica sensible.
- `B.Cu`: señales low-speed / control / telemetría long-haul cuando sea necesario.

## Partición vigente de las 60 nets

La partición es exhaustiva y mutuamente excluyente:

### PR19A — 28 nets locales

`FIELD_ANALOG_LOCAL`:
- `PH_FIELD_SIG`
- `ORP_FIELD_SIG`
- `DO_FIELD_SIG`

`CONTROL_SENSITIVE` locales:
- `5V_VCC`
- `5V_FB`
- `5V_PGOOD`
- `EFUSE_ILM`
- `EFUSE_ITIMER`
- `EFUSE_DVDT`
- `EFUSE_EN_UVLO`
- `EFUSE_OVLO`
- `CO2_ILIM`
- `PUMP_SR_CFG`

`ANALOG_SENSITIVE` locales / quiet:
- `HX_VBG`
- `LOAD_A_NEG`
- `LOAD_A_POS`

`CHILLER_DRY_CONTACT`:
- `CHILLER_CONTACT_A`
- `CHILLER_CONTACT_B`

`DIGITAL_LOW_SPEED` locales:
- `CO2_OPENLOAD_N`
- `CO2_EN_DRV`
- `PUMP_DIR_DRV`
- `PUMP_PWM_DRV`
- `CHILLER_GATE`
- `CHILLER_LED_A`
- `CHILLER_LED_K`
- `HMI_FIELD_RX`
- `HMI_FIELD_TX`
- `WDT_MR_N`

**Gate de merge PR19A:** 28/28 conectadas; 0 nets fuera del lote tocadas; 0 shorts; 0 errores nuevos de clearance/courtyard; placement/outline fuera de scope sin cambios; `In1.Cu` sin signal tracks.

### PR19B — 4 nets analógicas inter-zona

- `PH_ADC`
- `ORP_ADC`
- `DO_ADC`
- `PUMP_CURRENT_ADC`

Estas cuatro redes se revisan como dominio sensible. `PUMP_CURRENT_ADC` debe cruzar Z4→Z0 por el corredor más silencioso disponible y evitar los loops de switching/power-entry de Z3. La revisión visual de retorno contra el futuro plano GND es obligatoria antes de merge.

### PR19C — 16 nets digital/control inter-zona

- `ACT_FAULT_N`
- `CHILLER_CTL`
- `CO2_SOL_CTL`
- `HMI_RX`
- `HMI_TX`
- `HX711_DOUT`
- `HX711_SCK`
- `I2C_SCL`
- `I2C_SDA`
- `LED_STATUS`
- `MCU_NRST`
- `MCU_WDI`
- `PUMP_DIR`
- `PUMP_PWM`
- `TEMP_1WIRE`
- `UNO_IOREF_3V3`

B.Cu es el corredor preferente para long-haul low-speed; F.Cu se preserva para escapes locales, analógica y loops compactos.

### PR19D — 1 net ECO de potencia HMI

- `5V_HMI`

PR19D fue insertado después de PR19C para cerrar el ECO abierto por la selección de Nextion + BOX Speaker. `5V_HMI` nace en un subensamble externo 5 V / 2 A y entra a Z2 por `J_HMI.1`; en la PCBA solo alimenta `U_HMI_LVL.7` y `C_HMI_B.1`. No existe net-tie ni puente a `5V_RAIL`.

Routing cerrado: 7 segmentos + 2 vías; acumulado 924/121; DRC=0; `In1.Cu` sin señales; zones=0. El escape de `U_HMI_LVL.7` usa neck-down 0.20 mm por ≤1.20 mm únicamente para liberar el VSSOP, conservando clearance ≥0.20 mm y retornando a 0.40 mm.

**Gate PR19D:** `5V_HMI` 1/1 conectada, UART HMI previa intacta, placement/outline congelados, ninguna net PR20A/PR20B adelantada.

### PR20A — 10 nets de potencia + actuadores

Potencia:
- `12V_IN_RAW`
- `12V_PROTECTED`
- `12V_HOST_VIN`
- `12V_LOGIC`
- `12V_ACT`
- `5V_RAIL`
- `3V3_RAIL`

Salidas de actuadores:
- `PUMP_OUT1`
- `PUMP_OUT2`
- `CO2_SOL_POS`

Este lote usa F.Cu/In2.Cu según `routing_contract.json`; debe preservar la estrella Z3/Z4 y evitar retornos de alta corriente por Z1/Z2.

### PR20B — GND

- `GND`

Aunque es una sola net, el probe experimental identificó **83 endpoints**. Se trata como lote independiente porque define el plano continuo de `In1.Cu`, stitching y la calidad de los retornos analógicos/digitales/potencia.

## Lecciones del PR #19 experimental

PR #19 fue cerrado **sin merge** y su rama se conserva como laboratorio. Su valor es de conocimiento, no de cobre de producción.

Hallazgos principales:

1. Intentar resolver señales locales, long-haul, potencia y GND en un mismo PR genera demasiadas variables simultáneas.
2. El router experimental llegó a cerrar las 28 nets locales antes de entrar en congestión inter-zona; esa frontera es natural y reproducible.
3. El TPSM33625 y TPS259470A requieren prioridad de escape local por pitch fino; no se debe relajar el clearance global para “hacerlos pasar”.
4. El TPS1HC120 DYC0008A mostró garganta geométrica en `CO2_OPENLOAD_N` y `CO2_EN_DRV`; los escapes cortos deben tratarse como geometría local y siempre quedar bajo DRC KiCad.
5. Los primeros long-haul llegaron a producir cientos de segmentos por net. **Conectar no es suficiente**: calidad geométrica, número de giros, número de vías y claridad del corredor son criterios de aceptación.
6. `In1.Cu` no se usa como vía de escape de routing; queda reservado al plano GND.
7. Los rails multipunto (`3V3_RAIL` y `5V_RAIL`) no deben forzarse como pistas improvisadas alrededor de encapsulados finos; pertenecen al lote de potencia.

## Lecciones PR21–PR24: routing como detector de placement

Los PR21 y PR23 fueron cerrados sin merge porque el routing reveló problemas locales de placement que era mejor corregir antes de persistir cobre.

### PR22 — TPSM33625

Trigger: `5V_FB` y `5V_VCC` podían rutearse individualmente pero se bloqueaban mutuamente con el packing geométrico original.

Corrección: ECO mínimo de 5 pasivos alrededor de `U_5V`, manteniendo `U_5V` fijo. Resultado: DRC físico 0.

Regla preventiva: componentes de bypass, feedback y programación deben formar **micro-islas por función eléctrica**, no solo quedar “dentro de Z3”.

### PR23/PR24 — HX711 load-cell

Trigger: `LOAD_A_NEG` llegó a cerrar con ~198 segmentos, ~97.8 mm y 4 vías, mientras `LOAD_A_POS` se bloqueaba; ambos TP estaban en la banda superior lejos de `U_HX`.

Corrección: PR24 movió únicamente `TP_LOAD_A_POS` y `TP_LOAD_A_NEG` junto al HX711. Resultado: 2 refs movidas / 117 intactas, courtyard 0, DRC físico 0 y menor deuda de silk.

Regla preventiva: para entradas diferenciales de muy bajo nivel, el camino principal `J_LOADCELL → U_HX` es la topología prioritaria; los testpoints deben ser ramas secundarias cortas.

## Lecciones de tooling KiCad transferidas y verificadas

Detalle completo: `docs/KICAD_TOOLING_NOTES.md`.

Reglas que afectan directamente PR19A:

1. **Sandbox DRC = triplete de basename.** Una copia temporal del `.kicad_pcb` debe tener `.kicad_pro` y `.kicad_dru` homónimos al lado.
2. **`.kicad_pro` no define por sí solo el mínimo legal.** Las reglas custom de `.kicad_dru` pueden imponer límites/overrides distintos.
3. **Courtyard real por layer.** `footprint.GetBoundingBox()` no sustituye `F.Courtyard/B.Courtyard`.
4. **Pad-shapes duplicados se colapsan por `ref.pin` para conectividad**, pero siguen siendo obstáculos geométricos.
5. **Margen positivo en clearance propio.** Nunca hacer un planner ligeramente permisivo esperando que DRC “perdone”.
6. **PCB regenerado se compara semánticamente**, porque `pcbnew` puede generar UUIDs nuevos.
7. **CI final read-only.** No dejar auto-commits recurrentes sobre un artefacto no byte-estable.
8. **Gates históricos composicionales.** Cada ECO valida su delta y después reproduce la cadena vigente completa.
9. **`unconnected_item` no implica automáticamente una pista.** Con zones futuras, distinguir endpoints reales de islas/artefactos `Zone↔Zone`.

## Topología multipunto y endpoints lógicos

No imponer MST geométrico ciegamente.

- `5V_VCC`: bypass y strap RT→VCC tienen roles distintos; el árbol debe reflejar la función eléctrica.
- eFuse: ITIMER/UVLO/OVLO/ILM/DVDT se priorizan por confinamiento y conectividad del divisor/programación.
- footprints compuestos: varios pad-shapes con mismo número físico son un solo endpoint eléctrico.
- `LOAD_A_POS/NEG`: par principal acoplado; TP como stubs cortos.

## Micro-rutas y neckdown

Si una rejilla no representa un corredor que físicamente sí existe:

1. medir el corredor exacto;
2. usar waypoint/micro-ruta solo para ese caso;
3. mantener reglas globales intactas;
4. limitar cualquier neckdown por net/región;
5. DRC obligatorio.

No bajar resolución o clearance global para resolver una sola garganta.

## Criterio de merge por lote

Un lote solo puede mergearse si cumple simultáneamente:

- 100% de las nets declaradas en ese lote conectadas.
- 0 nets de lotes futuros ruteadas accidentalmente.
- 0 shorts.
- 0 errores nuevos de clearance físico.
- 0 courtyard collisions nuevas.
- placement semánticamente equivalente fuera de ECO aprobado.
- outline y dimensiones congelados.
- `In1.Cu` sin signal tracks hasta PR20B.
- cualquier warning/deuda restante está tipificado, contado y documentado; nunca se usa una exclusión genérica para ocultar violaciones de cobre.
- revisión visual de la topología del lote antes del merge.

No se mergean “17 de 28 porque funcionan”. Se mergea **28/28 o 0/28**.

## Calidad geométrica

Además de DRC, cada lote debe registrar:

- longitud aproximada por net;
- cantidad de segmentos;
- cantidad de vías;
- capa(s) utilizadas;
- número de cambios de dirección;
- desviación respecto al corredor previsto;
- proximidad de nets sensibles vs. dirty nets.

Los umbrales concretos pueden evolucionar, pero la tendencia debe favorecer rutas simples y auditables. Una ruta con cientos de pequeños segmentos no se acepta solo porque sea eléctricamente conectada.

## Regla de aprendizaje

Cada problema físico relevante descubierto durante routing debe incorporarse aquí con:

- síntoma;
- causa raíz;
- corrección aplicada;
- regla preventiva para futuros lotes;
- referencia al PR/commit que la materializó.

De esta forma el repositorio conserva no solo el resultado final, sino también el conocimiento de ingeniería que permitió llegar a él.
