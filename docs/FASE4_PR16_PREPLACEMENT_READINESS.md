# PR #16 — Pre-placement Readiness

**Objetivo:** autorizar la siguiente fase de placement XY sin introducir todavía ningún footprint de producción en `kicad/NFB_Insight_PCBA_v2.kicad_pcb`.

**Contrato machine-readable:** `hardware/placement_readiness_contract.json`  
**Gate:** `tools/validate_placement_readiness.py`

## 1. Revalidación UNO Q antes del placement

PR #16 vuelve a consultar primero `arduino/docs-content`, siguiendo `docs/SOURCE_OF_TRUTH.md`.

Snapshot revisado:

`24445a32e249d410c1e4359bdc99d8c0dcb17bd2`

Archivos:

- `content/hardware/02.uno/boards/uno-q/product.md`
- `content/hardware/02.uno/boards/uno-q/datasheet/datasheet.md`
- `content/hardware/02.uno/boards/uno-q/tech-specs.yml`

La fuente oficial identifica `WCBN3536A / Qualcomm WCN3980` y una **shared PCB antenna**. También mantiene el concepto de shields/carriers como expansión oficial del UNO Q y publica evidencia de certificación del host.

## 2. Política RF: no inventar un keepout

La documentación fuente revisada no publica una distancia textual de antenna keepout que podamos convertir honestamente a milímetros.

Por tanto PR #16 **no crea una cifra RF ficticia**. En su lugar congela una frontera física verificable:

- Z0 UNO Q = `X 0…53.34 mm`, `Y 0…68.58 mm`;
- ningún footprint de producción NFB puede ocupar Z0;
- el shield crece únicamente desde `X=53.34 mm` hacia `+X`;
- la primera zona adyacente es Z1 sensores/quiet;
- switching/potencia se mantiene en Z3 y actuadores/high-current en Z4;
- no se permite que enclosure metálico, brackets, cable shields o PCBs apiladas invadan la región RF del host sin validación 3D/RF.

Los guides actuales colocan Z3 a `X≥145 mm` y Z4 a `X≥180 mm`. Esto deja 91.66 mm y 126.66 mm respectivamente desde el borde +X de Z0. **Son separaciones derivadas del zoning NFB, no especificaciones RF de Arduino.**

## 3. Stackup intent antes de placement

El PCB sigue siendo de cuatro capas. PR #16 congela el propósito de capas para evitar repetir el problema del donor Q-Shield:

- `F.Cu`: componentes + señales locales/críticas;
- `In1.Cu`: **plano GND continuo de referencia, sin signal routing**;
- `In2.Cu`: distribución de potencia manteniendo geometría de retornos quiet/dirty;
- `B.Cu`: señales secundarias/low-speed.

Un autorouter no podrá reutilizar `In1.Cu` como capa de señal.

## 4. FIELD I/O EDGE

Todos los conectores/cables de proceso se organizan sobre `Y=0` con salida `-Y`, excepto el MPR cuyo puerto de presión es vertical y debe quedar accesible cerca del borde.

Secuencia izquierda→derecha congelada para PR #17:

1. `J_PH`
2. `J_ORP`
3. `J_TEMP`
4. `U_CO2` — puerto vertical
5. `J_DO`
6. `J_LOADCELL`
7. `J_GNSS_RTC`
8. `J_HMI`
9. `J_PWR_IN`
10. `J_PUMP`
11. `J_CO2_SOL`
12. `J_CHILLER_CTL`

La secuencia conserva el gradiente **sensible → digital → potencia → actuadores**.

## 5. Cierre adicional de J_LOADCELL

El único conector de campo que todavía estaba descrito con una familia no inequívoca era `J_LOADCELL`.

PR #16 lo migra a:

- fabricante: Phoenix Contact;
- MPN: **1757268**;
- modelo: `MSTBA 2,5/4-G-5,08`;
- 4 posiciones;
- pitch 5.08 mm;
- footprint: `Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_4-G-5,08_1x04_P5.08mm_Horizontal`.

Así todas las interfaces FIELD I/O poseen un footprint/MPN suficientemente definido para iniciar placement.

## 6. Reglas de proximidad

PR #17 deberá colocar:

- protección ESD inmediatamente detrás de conectores de campo;
- pH/ORP/TEMP/DO y sus redes únicamente en Z1;
- HX711/load-cell del lado Z1 de Z2;
- HMI del lado Z3 de Z2;
- conector de 12 V + TVS + eFuse como cluster Z3;
- TPSM33625 con su switching loop confinado a Z3;
- drivers de bomba/solenoide y bulk local en Z4, próximos a sus salidas;
- `PUMP_CURRENT_ADC` alejado de nodos switching;
- retornos high-current sin atravesar Z1/Z2;
- PhotoMOS/chiller como contacto seco **SELV ≤48 V / NO MAINS**.

## 7. Qué permanece deliberadamente abierto

No son blockers de placement inicial:

- ancho final del PCB: 220 mm sigue provisional hasta medir courtyards reales;
- exact antenna-local clearance: no publicado en el texto oficial revisado y no se inventará;
- enclosure/3D RF validation;
- termografía/HIL;
- pre-scan EMC;
- routing.

Si el placement real exige más ancho, PR #17 podrá crecer exclusivamente hacia `+X`, manteniendo Z0 inmutable y el orden Z0→Z1→Z2→Z3→Z4.

## 8. Criterio de salida

PR #16 puede considerarse cerrado cuando:

- snapshot oficial Arduino está registrado;
- J_LOADCELL está migrado a Phoenix 1757268 en JSON+BOM+KiCad;
- hierarchy completo continúa `ERC=0/0`;
- auditoría crítica PR #13 permanece cerrada;
- los 12 FIELD I/O coinciden con sus footprints contractuales;
- `.kicad_pcb` sigue con **0 production placements**;
- routing continúa en cero;
- readiness CI queda verde.

Después de ese gate, **PR #17 puede iniciar placement XY real, pero no routing**.
