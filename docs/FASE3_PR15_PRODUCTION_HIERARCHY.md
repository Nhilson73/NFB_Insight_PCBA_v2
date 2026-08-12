# Fase 3 — PR #15: materialización EDA de producción Z0–Z4

**Estado:** baseline propuesto para merge  
**Fecha:** 2026-08-12  
**Objetivo:** convertir la jerarquía inter-zona de PR #14 en una representación KiCad completa y reproducible de las referencias, pines, nets y footprints de producción, sin habilitar todavía placement ni routing.

## 1. Resultado

PR #15 elimina la deuda ERC deliberada de PR #14. Las cinco hojas del root contienen ahora representación interna de producción:

- Z0 → Arduino UNO Q host desde `hardware/insight_pin_contract.json`;
- Z1 → sensores desde `hardware/z1_production_netlist.json` + BOM Z1;
- Z2 → digital/bajo ruido desde `hardware/z2_production_netlist.json` + BOM Z2;
- Z3 → potencia desde `hardware/power_production_netlist.json` + BOM de potencia;
- Z4 → actuadores desde `hardware/z4_production_netlist.json` + BOM Z4.

El root continúa siendo `kicad/NFB_Insight_PCBA_v2.kicad_sch` y conserva las fronteras inter-zona congeladas en PR #14.

## 2. Fuente de verdad y generación

No se transcriben manualmente más de cien referencias a KiCad.

Flujo reproducible:

```text
JSON de producción + BOM
        ↓
tools/generate_production_schematics.py
        ↓
representación raw de refs / pins / nets / footprints
        ↓
tools/normalize_pr15_schematics.py
        ↓
child sheets Z0–Z4 + librería NFB_GEN
        ↓
KiCad 10.0.5 root ERC
```

`generate_production_schematics.py` exige antes de generar:

- igualdad exacta de referencias BOM ↔ JSON;
- igualdad de footprints BOM ↔ JSON;
- coherencia pin ↔ net dentro de cada contrato;
- endpoints externos/inter-zona válidos;
- 32 pads del UNO Q derivados del pin contract.

`normalize_pr15_schematics.py --check` exige que los archivos versionados puedan reproducirse byte-for-byte desde esas fuentes.

**Regla:** los child sheets generados no se editan manualmente para cambiar conectividad. El cambio se hace primero en el contrato JSON/BOM y luego se regenera.

## 3. Símbolos NFB_GEN

Los símbolos `NFB_GEN` son carriers EDA neutrales generados. Conservan:

- referencia;
- value;
- MPN;
- footprint;
- número de pin;
- nombre de net;
- estado DNP cuando aplica.

Los pines generados se modelan como `passive` o `no_connect`. Esto es deliberado: los JSON congelados describen topología, pero no contienen una taxonomía completa de tipos eléctricos de pin equivalente a una librería KiCad nativa. PR #15 no inventa esa semántica para fabricar un ERC artificialmente sofisticado.

Por tanto, el **ERC=0 de PR #15 certifica la integridad de la jerarquía materializada, ausencia de dangling nets y resolución de footprints**, mientras la intención eléctrica de cada bloque continúa protegida por los contratos/netlists y sus validadores especializados de Z1, Z2, potencia y Z4.

## 4. Alcance de labels

PR #14 utilizaba hojas de interfaz sin componentes internos y tenía 125 `label_dangling` controlados.

PR #15:

- mantiene `hierarchical_label` exclusivamente en las fronteras de cada child sheet;
- usa labels locales para unir componentes dentro de una misma hoja;
- elimina contaminación de alcance por `global_label` internos;
- registra la librería de proyecto `NFB_GEN` en `kicad/sym-lib-table`.

## 5. Correcciones de footprints detectadas durante la materialización

La ejecución real de KiCad 10.0.5 permitió detectar asignaciones antiguas o inexistentes antes de placement.

### 5.1 TXU0202DCUR

`U_HMI_LVL` cambia a:

```text
NFB:TI_DCU0008A_TXU0202
```

La huella local reproduce el land pattern del package TI `DCU0008A` usado por `TXU0202DCUR`: 8 pads, pad nominal 0.85 × 0.30 mm, pitch 0.50 mm y separación de centros entre columnas de pads de 3.10 mm.

Fuente primaria: Texas Instruments, package drawing `DCU0008A / 4225266` del encapsulado DCU de TXU0202.

### 5.2 Phoenix Contact 1757242

`J_PWR_IN`, `J_PUMP`, `J_CO2_SOL` y `J_CHILLER_CTL` quedan asignados a:

```text
Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal
```

El MPN `1757242` corresponde oficialmente a `MSTBA 2,5/ 2-G-5,08`, 2 posiciones, una fila y pitch 5.08 mm.

Fuente primaria: Phoenix Contact, producto `1757242`.

### 5.3 Littelfuse 045401.5MR

`F_ACT` queda asignado a:

```text
NFB:Littelfuse_0454_NANO2
```

Littelfuse identifica `045401.5MR` como fusible NANO² Slo-Blo, serie 454, 1.5 A, y publica para esta familia el recurso oficial **Fuse 452 and 454 Datasheet**.

La huella NFB congela el land pattern 452/454 utilizado para este MPN: cuerpo nominal 6.10 × 2.69 mm; span exterior recomendado 6.86 mm; gap interior 2.95 mm; ancho de land 3.15 mm; longitud de copper land derivada `(6.86 - 2.95)/2 = 1.955 mm`.

Fuente primaria: Littelfuse, serie 454 / `045401.5MR`, datasheet conjunto 452/454.

## 6. ERC PR #15

Evidencia en GitHub Actions con `kicad/kicad:10.0.5`:

```text
Found 0 violations
ERC messages: 0
Errors: 0
Warnings: 0
```

El contrato `hardware/root_eda_contract.json` pasa a schema 3 y establece:

```text
ZERO_VIOLATIONS_REQUIRED_PR15
```

El workflow root ejecuta KiCad con `--severity-all --exit-code-violations`; cualquier nuevo error o warning vuelve a bloquear el merge.

## 7. Fronteras preservadas

PR #15 no cambia:

- GND común Z0–Z4;
- rails `3V3_RAIL` / `5V_RAIL` locales del shield, excluyendo Z0;
- I²C compartido Z0/Z1/Z2;
- `12V_ACT` Z3/Z4;
- A4 = `PUMP_CURRENT_ADC`;
- D10 = `ACT_FAULT_N`;
- prohibición de `CO2_ADC`, `TEMP_ADC`, `HUM_ADC`, `CO2_PWM`, `CO2_FLOW_PWM` y RS485 Insight activo.

## 8. Lo que PR #15 NO autoriza

- no placement XY de componentes de producción;
- no routing;
- no cambio de `Edge.Cuts` ni del ancho provisional de 220 mm;
- no relajación de ERC;
- no sustitución silenciosa de MPN o footprint;
- no cambio de pinout del UNO Q.

El `.kicad_pcb` debe continuar con el UNO Q mecánico y **cero referencias de producción Z1–Z4 colocadas**.

## 9. Gate siguiente

Antes de iniciar placement físico deben cerrarse dos tareas de pre-placement:

1. keepouts mecánicos/RF definitivos del UNO Q y enclosure;
2. auditoría de cualquier footprint restante cuyo riesgo físico justifique revisión antes de asignar coordenadas XY.

Solo después se habilita Fase 4: placement Z0→Z4, conectores de campo hacia `Y=0/-Y`, separación limpio/sucio, revisión 3D y congelación del ancho real de la PCBA.
