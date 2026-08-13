# Base de conocimiento de routing — NFB Insight PCBA v2

## Propósito

Este documento conserva el conocimiento de ingeniería aprendido durante la transición de placement a routing de producción. Su objetivo es evitar que decisiones críticas queden dispersas entre conversaciones, commits experimentales o logs de CI.

La regla de trabajo desde Fase 5 es **divide y vencerás**: cada lote de cobre debe ser pequeño, completo, reproducible, auditable y mergeable de forma independiente.

## Autoridad

La jerarquía de autoridad para routing es:

1. `hardware/routing_contract.json` — reglas eléctricas, netclasses, capas, anchos y clearances congelados en PR18.
2. `hardware/routing_batches_contract.json` — partición de las 59 nets en lotes de cierre incremental.
3. `hardware/placement_manifest.json` — placement PR17 congelado.
4. JSON/BOM de Z1/Z2/Z3/Z4 — conectividad y footprints de producción.
5. KiCad 10.0.5 + DRC — autoridad física final para cobre.
6. Este documento — narrativa, rationale y lecciones aprendidas.

Ningún router, script o optimización puede debilitar los contratos anteriores para obtener un resultado “verde”.

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
- Placement PR17: congelado; routing no puede mover footprints ni alterar outline.

## Política de capas

- `F.Cu`: señales críticas/locales, front-end analógico y loops compactos.
- `In1.Cu`: referencia GND continua; **sin signal routing**.
- `In2.Cu`: distribución de potencia y troncales de baja impedancia; sin analógica sensible.
- `B.Cu`: señales low-speed / control / telemetría long-haul cuando sea necesario.

## Partición de las 59 nets

La partición es exhaustiva y mutuamente excluyente:

### PR19A — 28 nets locales

Objetivo: cerrar primero las redes que no necesitan corredor inter-zona significativo.

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

**Gate de merge PR19A:** 28/28 conectadas; 0 nets fuera del lote tocadas; 0 shorts; 0 errores nuevos de clearance/courtyard; placement/outline sin cambios; `In1.Cu` sin signal tracks.

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

Aunque es una sola net, el probe de routing identificó **83 endpoints**. Se trata como lote independiente porque define el plano continuo de `In1.Cu`, stitching y la calidad de los retornos analógicos/digitales/potencia.

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

## Criterio de merge por lote

Un lote solo puede mergearse si cumple simultáneamente:

- 100% de las nets declaradas en ese lote conectadas.
- 0 nets de lotes futuros ruteadas accidentalmente.
- 0 shorts.
- 0 errores nuevos de clearance físico.
- 0 courtyard collisions nuevas.
- placement PR17 byte/semánticamente equivalente en XY/rotación/footprint.
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
- proximity de nets sensibles vs. dirty nets.

Los umbrales concretos pueden evolucionar, pero la tendencia debe favorecer rutas simples y auditables. Una ruta con cientos de pequeños segmentos no se acepta solo porque sea eléctricamente conectada.

## Regla de aprendizaje

Cada problema físico relevante descubierto durante routing debe incorporarse aquí con:

- síntoma;
- causa raíz;
- corrección aplicada;
- regla preventiva para futuros lotes;
- referencia al PR/commit que la materializó.

De esta forma el repositorio conserva no solo el resultado final, sino también el conocimiento de ingeniería que permitió llegar a él.
