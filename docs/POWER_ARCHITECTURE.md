# NFB Insight PCBA v2 — Arquitectura y Producción de Potencia

**Arquitectura:** PR #9 — Fase 3  
**Baseline discreto:** PR #10  
**Objeto:** shield/carrier del Arduino UNO Q  
**Entrada nominal:** 12 VDC  
**Fuentes de verdad:** `hardware/power_architecture_contract.json` + `hardware/power_production_netlist.json`  
**Fuente primaria UNO Q:** repositorios oficiales `arduino/*`, según `docs/SOURCE_OF_TRUTH.md`

## 1. Frontera eléctrica con UNO Q

La revisión del repositorio oficial `arduino/docs-content` confirma que UNO Q admite USB-C a 5 V, VIN 7–24 V y alimentación regulada de 5 V mediante JANALOG. NFB selecciona **12 V protegidos → VIN** como método base.

El shield genera sus propios `5V_RAIL` y `3V3_RAIL` y no los une a J_UNOQ.5/J_UNOQ.4. `IOREF` se usa solo como salida/referencia de alta impedancia para secuenciar el shield y nunca se retroalimenta.

## 2. Árbol de potencia de producción

```text
J_PWR_IN 12 V
   │
   ├── D_IN_TVS SMBJ15A-TR → GND
   ├── C_IN_HF 100 nF / 50 V
   │
   └── U_EFUSE TPS259470ARPWR
            │
            └── 12V_PROTECTED + C_IN_BULK 100 µF / 25 V
                   ├── NT_HOST  ──> 12V_HOST_VIN ──> J_UNOQ.8 VIN
                   ├── NT_LOGIC ──> 12V_LOGIC ──> TPSM33625 ──> 5V_RAIL
                   └── F_ACT 1.5 A Slo-Blo ──> 12V_ACT

UNO Q IOREF ──> EN TPSM33625
5V_PGOOD   ──> EN TLV75533
TLV75533   ──> 3V3_RAIL

Chiller: alimentación externa; señal de control únicamente.
```

## 3. Entrada y protección — TPS259470ARPWR

### 3.1 Red UVLO/OVLO

Se adopta el ladder de tres resistencias de la aplicación TI:

```text
12V_IN_RAW ─ R1 470k ─ EN/UVLO ─ R2 11k ─ OVLO ─ R3 47k ─ GND
```

Con referencia nominal de 1.2 V:

- `UVLO ≈ 1.2 × (470k + 11k + 47k) / (11k + 47k) = 10.924 V`;
- `OVLO ≈ 1.2 × (470k + 11k + 47k) / 47k = 13.481 V`.

Los valores nominales quedan próximos a la ventana de diseño 10.8–13.2 V; las tolerancias reales del IC y resistores se validarán en bring-up.

### 3.2 Corriente, dV/dt y timer

- `R_EFUSE_ILIM = 750 Ω / 1 %`.
- Relación típica de diseño: `3334 / 750 ≈ 4.445 A`; el contrato conserva `4.452 A typ` de referencia de datasheet.
- `C_EFUSE_DVDT = 3.3 nF`.
- `C_EFUSE_ITIMER = 2.2 nF`.
- `AUXOFF` y `FLT` quedan NC en Insight base.

El valor de 750 Ω conserva además el criterio publicado por TI para reconocimiento UL 2367 del dispositivo. La protección general no convierte por sí sola al producto final en certificado; el conjunto debe mantener su expediente y ensayos aplicables.

### 3.3 TVS y bulk

- `D_IN_TVS = SMBJ15A-TR`, unidireccional, 15 V, 600 W, SMB.
- `C_IN_HF = 100 nF / 50 V X7R` junto a la entrada.
- `C_IN_BULK = EEEFK1E101P`, 100 µF / 25 V, después del eFuse.

No se congela todavía un filtro LC serie adicional. Añadir inductancia sin medir impedancias, cableado y emisiones puede empeorar resonancias. La red adicional se decidirá con pre-scan de emisiones conducidas y surge.

## 4. Split estrella y rama de actuadores

El split de `12V_PROTECTED` se hace explícito mediante:

- `NT_HOST`: `12V_PROTECTED → 12V_HOST_VIN`;
- `NT_LOGIC`: `12V_PROTECTED → 12V_LOGIC`;
- `F_ACT`: `12V_PROTECTED → 12V_ACT`.

`F_ACT = Littelfuse 045401.5MR`, 1.5 A Slo-Blo Nano². El envelope de pico usado para arquitectura es 0.8 A bomba + 0.25 A solenoide = 1.05 A. La curva tiempo-corriente y el inrush real se validarán con cargas finales durante HIL.

Los retornos de `12V_ACT` deben regresar a la región de entrada/estrella sin atravesar Z1/Z2.

## 5. Buck 5 V — TPSM33625RDNR

Baseline discreto:

- `VIN = 12V_LOGIC`;
- `EN = UNO_IOREF_3V3` con `R_5V_EN_PD = 100 kΩ` a GND;
- `VOUT = 5V_RAIL`;
- `RT` unido a `VCC` → **1 MHz**;
- feedback: `R_5V_FBT = 40.2 kΩ`, `R_5V_FBB = 10 kΩ`;
- entrada: `4.7 µF / 50 V X7R + 100 nF / 50 V`;
- `VCC`: 1 µF;
- salida: `2 × 22 µF / 16 V X7R + 100 nF`;
- `PGOOD`: pull-up de 47 kΩ a `5V_RAIL`.

Los dos capacitores de 22 µF suman 44 µF nominales. **Antes de placement/fabricación se debe comprobar su DC-bias a 5 V** para garantizar al menos 25 µF efectivos combinados.

Los pines SW y BOOT del módulo no reciben componentes externos en este baseline; el cobre SW deberá quedar confinado a la isla recomendada por TI.

## 6. LDO 3.3 V — TLV75533PDBVR

Pinout contractual:

- pin 1 `IN = 5V_RAIL`;
- pin 2 `GND`;
- pin 3 `EN = 5V_PGOOD`;
- pin 4 `NC`;
- pin 5 `OUT = 3V3_RAIL`.

Capacitores:

- `C_3V3_IN = 1 µF / 25 V`;
- `C_3V3_OUT = 1 µF / 25 V`;
- `C_3V3_HF = 100 nF`.

## 7. Secuencia

1. 12 V llegan a `J_PWR_IN`.
2. TVS/eFuse generan `12V_PROTECTED`.
3. `12V_HOST_VIN` energiza al UNO Q por VIN.
4. El power tree del UNO Q levanta `IOREF`.
5. `IOREF` habilita el TPSM33625.
6. Al estabilizarse 5 V, `5V_PGOOD` habilita TLV75533.
7. Se habilita `3V3_RAIL` para sensores/lógica.

Bring-up debe probar, además, escenarios USB-C presente/ausente y fuente principal presente/ausente para demostrar ausencia de back-feed.

## 8. Screening térmico a 60 °C

Este análisis es **screening**, no validación final de PCB:

- Corriente equivalente del envelope total: `43.5 W / 12 V = 3.625 A`.
- TPS25947 con `RON typ = 28.3 mΩ`: pérdida estimada ≈ `0.372 W` a 3.625 A y ≈ `0.561 W` a 4.452 A.
- TPSM33625: usando 88 % como referencia conservadora para 7.5 W de salida, pérdida ≈ `1.02 W`; el valor real depende del punto de carga y layout.
- TLV75533 a 250 mA: `(5 - 3.3) × 0.25 = 0.425 W`; usando `RθJA ≈ 60.3 °C/W` de referencia, `Tj ≈ 85.6 °C` con 60 °C ambiente.

La termografía con PCB real, cobre final y enclosure sigue siendo obligatoria antes del RC.

## 9. Netclasses congeladas contractualmente

`hardware/power_netclasses.json` define mínimos iniciales:

| Clase | Nets | Ancho mínimo | Clearance mínimo |
|---|---|---:|---:|
| `PWR_INPUT_5A` | 12V_IN_RAW, 12V_PROTECTED | 2.0 mm | 0.50 mm |
| `PWR_12V_BRANCH` | HOST/LOGIC/ACT | 1.0 mm | 0.40 mm |
| `PWR_5V` | 5V_RAIL | 0.75 mm | 0.30 mm |
| `PWR_3V3` | 3V3_RAIL | 0.40 mm | 0.25 mm |
| `PWR_CONTROL` | FB/PGOOD/UVLO/etc. | 0.25 mm | 0.25 mm |

Son restricciones contractuales previas al routing; deberán aplicarse físicamente en KiCad y revalidarse con el stackup/cobre del fabricante.

## 10. Gates antes de placement

PR #10 **no autoriza placement ni routing**. Permanecen abiertos:

1. crear/auditar footprint `TPS259470A RPW-10` desde package drawing TI;
2. crear/auditar footprint `TPSM33625 RDN-11` desde package drawing TI;
3. validar DC-bias de `C_5V_OUT1/2`;
4. cerrar MPN exacto del capacitor dV/dt de 3.3 nF;
5. comprobar consumo/inrush de bomba, solenoide, HMI y sensores;
6. termografía y pre-compliance EMC del conjunto.

## 11. Fuentes primarias

### UNO Q

Snapshot oficial Arduino `arduino/docs-content` commit `196feda03787005572a059f030677b8a1de9bcd2`:

- `content/hardware/02.uno/boards/uno-q/datasheet/datasheet.md`;
- `content/hardware/02.uno/boards/uno-q/tutorials/03.power-specification/content.md`;
- `content/hardware/02.uno/carriers/uno-breakout-carrier/datasheet/datasheet.md`.

### Shield

- Texas Instruments: `TPS259470ARPWR`, `TPSM33625RDNR`, `TLV75533PDBVR`.
- Phoenix Contact: `1757242`.
- Littelfuse: `045401.5MR`.
- STMicroelectronics: `SMBJ15A-TR`.
- Panasonic: `EEEFK1E101P`.
- TDK/Murata: capacitores cerámicos seleccionados en la BOM.

La BOM final para fabricación deberá acompañarse de evidencia RoHS/REACH conforme al EU Compliance Gate.
