# PR27 / PR19A — notas de routing local

## Alcance

PR27 materializa únicamente las **28 nets locales** definidas en `hardware/routing_batches_contract.json`. La política es `ALL_OR_NOTHING`: 28/28 o no merge.

El baseline autoritativo es el merge virtual `main` post-PR24/post-PR25/PR26 + rama PR27. Los runs `push` de la rama histórica no son evidencia de aceptación porque no incorporan los ECO de `main`; para aceptación se usan runs `pull_request` y, al final, el PCB persistido sobre el `main` vigente.

## Hallazgo: `5V_VCC` no debe tratarse como MST geométrico genérico

`5V_VCC` tiene tres endpoints con funciones físicas distintas:

- `U_5V.8` = `VCC`, salida del LDO interno del TPSM33625;
- `C_5V_VCC.1` = bypass local de VCC;
- `U_5V.11` = `RT` en la variante TPSM33625RDNR.

La configuración congelada del proyecto es `PIN11_RT_TO_PIN8_VCC`. La documentación primaria de TI para TPSM33625 establece que, en la variante con pin RT, **RT conectado a VCC selecciona 1 MHz**. La topología intencional queda `C_VCC→VCC` + `C_VCC→RT`, no un MST genérico.

## Clearances locales y KiCad

La excepción `0.125 mm` del TPSM33625 permanece estrictamente local a la garganta demostrada del encapsulado. No se permite reducir clearance global. KiCad 10.0.5 DRC continúa como autoridad física final.

## Pad-shape no equivale a endpoint eléctrico

El footprint `TI_RPW0010A_TPS259470A` usa pads compuestos. Todos los shapes siguen participando como geometría/obstáculos, pero el árbol de conectividad usa un solo endpoint lógico por `(ref,pin)`.

## Resultado autoritativo PR27 — primera materialización 28/28

Run `pull_request` #57 sobre el merge virtual vigente:

- **28/28 nets materializadas**;
- `1229` segmentos;
- `15` vías;
- `204` unconnected restantes, correspondientes al resto del board/lotes futuros;
- DRC ejecutado completamente;
- **60 errores físicos** y 257 warnings.

Los errores no están distribuidos aleatoriamente. Se concentran en pocas sub-islas:

| Dominio | Errores DRC | Causa dominante |
|---|---:|---|
| eFuse `OVLO/ILM/DVDT` | 29 | micro-rutas deterministas anteriores cruzan el corredor A* de OVLO |
| `LOAD_A_POS/NEG` | 11 | vías/rutas del árbol independiente invaden el pin del par opuesto |
| bomba `DIR/PWM/SR_CFG` | 8 | corredores F.Cu competidores junto a pines 1/3/4 del DRV8242 |
| CO₂ `ILIM/EN/OPENLOAD` | 6 | vías/escapes digitales interfieren con ILIM |
| `5V_FB` | 2 | aproximación a FBB demasiado cercana al pad GND |
| HMI field | 2 | vía TX demasiado próxima al pad RX de TXU0202 |
| chiller LED | 2 | vía LED_A demasiado próxima al pad 3V3 de R_CH_LED |

Tipos totales de error:

- `shorting_items`: 19;
- `tracks_crossing`: 18;
- `clearance`: 15;
- `hole_clearance`: 4;
- `solder_mask_bridge`: 4.

**Decisión:** no se corrigen 60 errores uno por uno. Se sustituyen las topologías de esas sub-islas por rutas deterministas simples y separadas.

## Plan correctivo por sub-isla

### eFuse

- `EFUSE_OVLO`: corredor izquierdo dedicado entre `U_EFUSE.2` y divisor R2/R3.
- `EFUSE_DVDT`: corredor exterior derecho en banda inferior-superior propia.
- `EFUSE_ILM`: corredor exterior aún más a la derecha y banda superior independiente.
- ITIMER/EN-UVLO se conservan si DRC sigue limpio.

### Load-cell / HX711

`LOAD_A_POS/NEG` dejan de ser dos árboles A* independientes. Se tratan como **par quieto**:

- troncales largas preferentemente B.Cu;
- escapes cortos F.Cu hacia `U_HX.8/7`;
- testpoints como ramas secundarias cortas;
- evitar vías junto a pads NC/HX y evitar cruce entre el par;
- objetivo ≤2 vías por net y topología paralela/auditable.

### Bomba

- `PUMP_SR_CFG` recibe corredor F.Cu inferior independiente.
- `PUMP_DIR_DRV`: breakout corto F.Cu, tramo B.Cu y retorno F.Cu; 2 vías.
- `PUMP_PWM_DRV`: corredor F.Cu separado.

### CO₂

- `CO2_ILIM` se lleva por corredor superior dedicado.
- `CO2_EN_DRV` queda en corredor inferior/local F.Cu.
- `CO2_OPENLOAD_N` usa una rama local F.Cu y el trayecto largo al TP por B.Cu con solo dos vías.

### HMI / chiller / 5V_FB

- `HMI_FIELD_TX`: tramo largo por B.Cu con vía alejada del TXU0202; rama local F.Cu.
- `CHILLER_LED_A`: F.Cu determinista, sin vía.
- `5V_FB`: unión corta `U_5V.9 → R_FBB.1 → R_FBT.2`, evitando el pad GND de FBB.

## Calidad geométrica pendiente aun después de DRC

Aunque no generaron los 60 errores, estas rutas son demasiado fragmentadas para aceptar como producción:

- `5V_PGOOD`: 143 segmentos / 69.623 mm;
- `CO2_OPENLOAD_N`: 106 segmentos / 52.025 mm (se corrige con la topología anterior);
- `WDT_MR_N`: 100 segmentos / 47.733 mm;
- `LOAD_A_NEG`: 98 segmentos / 4 vías / 47.985 mm;
- `LOAD_A_POS`: 91 segmentos / 44.655 mm.

Una vez eliminado DRC físico, `5V_PGOOD` y `WDT_MR_N` deben simplificarse antes de merge aunque el gate formal antiguo de 220 segmentos los tolerase.

## Gate de aceptación

PR27 no se mergea hasta cumplir simultáneamente:

- 28/28 conectadas;
- 0 nets de los otros 31 nets con cobre;
- **DRC errors = 0**;
- 0 shorts/clearance/courtyard/hole-clearance/solder-mask-bridge nuevos;
- In1.Cu sin signal tracks;
- sin copper zones;
- placement/outline/footprints/netlist congelados;
- rutas excesivamente fragmentadas simplificadas;
- `.kicad_pcb` final persistido en la rama sobre el `main` vigente;
- CI final read-only;
- `README.md` actualizado al estado real antes del merge.

Además, el validador debe comparar orientaciones módulo 360 (`270° ≡ -90°`) para no generar falsos negativos de placement.
