# Decisión HMI — Nextion NX8048P050-011C-Y

## Estado

**SELECCIONADO para NFB Insight:** Nextion Intelligent Series 5.0" capacitiva con enclosure, MPN `NX8048P050-011C-Y`, SKU `6920075776553`.

Esta pantalla es un **ensamble externo**, no un footprint poblado sobre la PCBA. La shield mantiene `J_HMI` como interfaz de cable y el repositorio incorpora huellas mecánicas externas para la HMI y sus accesorios, utilizables en integración de enclosure/servicio sin contaminar BOM o pick-and-place de la PCBA.

**Actualización PR19D:** el ECO de potencia queda cerrado en diseño mediante una rama externa dedicada `5V_HMI`. La pantalla y el BOX Speaker ya no consumen desde `5V_RAIL` de la PCBA principal.

## Pantalla congelada

- MPN: `NX8048P050-011C-Y`.
- 5.0", 800×480, capacitiva.
- Intelligent Series, MCU 200 MHz, Flash 128 MB, SRAM 512 KB, EEPROM 1024 B.
- RTC CR1220; 8 GPIO; audio/video soportados.
- alimentación oficial: **5 V / 1 A**.
- USART: **XH2.54 4P**.
- operación: -20…70 °C; almacenamiento: -30…85 °C.
- envelope frontal oficial: **160.04 × 107.07 mm**; profundidad máxima **21.2 mm**.

Fuentes oficiales: https://itead.cc/product/5-0-nextion-intelligent-series-hmi-touch-display-with-enclosure/ y https://nextion.tech/datasheets/NX8048P050-011C-Y/; plano mecánico: https://cdn.nextion.tech/wp-content/uploads/2020/12/NX8048P050-011X-Y-Dimension.pdf.

## Interfaz con NFB PCBA

`J_HMI` permanece `S4B-XH-A(LF)(SN)` con footprint KiCad `Connector_JST:JST_XH_S4B-XH-A_1x04_P2.50mm_Horizontal`, side-entry hacia `-Y`.

La razón de **no mover pads** es deliberada: PR19C cerró el routing UART y PR19D solo reasigna eléctricamente el pin de potencia. ITEAD publica la interfaz del display como `XH2.54 4P` pero no publica en la ficha consultada un MPN JST exacto. Por tanto:

1. no se inventa una equivalencia 2.50 ↔ 2.54;
2. se conserva la geometría de producción del board-side connector;
3. el arnés final debe pasar **mating test de first article** antes de release;
4. cualquier cambio posterior de `J_HMI` será un ECO de footprint/routing explícito.

Mapping lógico: `HMI_TX` del UNO → TXU0202 → `HMI_FIELD_RX` → RX de Nextion; TX de Nextion → `HMI_FIELD_TX` → TXU0202 → `HMI_RX` del UNO. Campo protegido con `PESD5V0U1UL,315`.

Desde PR19D, `J_HMI.1 = 5V_HMI`; `5V_HMI` también alimenta `U_HMI_LVL.7` (VCCB) y `C_HMI_B.1`. No existe puente permitido entre `5V_HMI` y `5V_RAIL`.

## Accesorios seleccionados

### Nextion Micro SD Card Extender

- modelo `SDExtender`;
- 17.1 × 41.48 × 2.5 mm; 7 g;
- FAT32 microSD; compatible con todas las series Nextion;
- ensamble externo, no poblado en PCBA;
- footprint mecánico: `NFB:Nextion_SDExtender_External`;
- fuente: https://itead.cc/product/nextion-micro-sd-card-extender/.

### Nextion BOX Speaker

- 31 × 28 × 14.8 mm; 21.2 g;
- 1.5 W, 100 Hz–3 kHz;
- conector hembra 2P pitch 1.25 mm `1.25T-2-2A`; cable 250 mm;
- ITEAD exige **+0.5 A** sobre la recomendación de alimentación del display;
- reserva de diseño para display + speaker: **5 V / 1.5 A**;
- footprint mecánico: `NFB:Nextion_BOX_Speaker_External`;
- verificar acceso/montaje del audio con la variante `-Y` durante first article;
- fuente: https://itead.cc/product/nextion-box-speaker/.

### Nextion Foca Max

`Foca Max` queda como **herramienta de programación/bring-up, no instalada en el producto**:

- CP2102; TTL 3.3 V; hasta 2 Mbps;
- DC externo 8–26 V; salida 5–5.5 V, 2 A máx.;
- PCB 50 × 50 × 1.6 mm; volumen 50 × 50 × 12 mm;
- incluye USB wire y XH2.54 4P wire;
- footprint de referencia de servicio: `NFB:Nextion_Foca_Max_Service`;
- para pantallas >4.3" ITEAD recomienda alimentación DC externa 8–26 V;
- fuente: https://itead.cc/product/nextion-foca-max-5v2a-output-usb-to-ttl-serial-converter-board/.

## Footprints mecánicos congelados

Las huellas siguientes son **referencias mecánicas externas, sin pads**, y están marcadas para quedar excluidas de BOM/position files de la PCBA:

- `NFB:Nextion_NX8048P050_011C_Y_Enclosure` — 160.04 × 107.07 mm, profundidad máxima documentada 21.2 mm.
- `NFB:Nextion_SDExtender_External` — 17.1 × 41.48 mm, espesor 2.5 mm.
- `NFB:Nextion_BOX_Speaker_External` — 31 × 28 mm, altura 14.8 mm.
- `NFB:Nextion_Foca_Max_Service` — 50 × 50 mm, altura total 12 mm; servicio solamente.
- `NFB:RECOM_R78K5_0_2_0L_External` — referencia mecánica del convertidor dedicado HMI.

No se insertan estas huellas externas dentro de `NFB_Insight_PCBA_v2.kicad_pcb`.

## ECO de potencia PR19D — cerrado en diseño

El problema detectado en PR #32 era que `5V_RAIL` tenía un límite continuo de diseño de 1.5 A y HMI + speaker ya reservaban esos mismos 1.5 A, sin dejar margen a sensores ni al LDO de 3.3 V.

PR19D resuelve el conflicto sin mover placement de Z3 y sin usar capacidad ficticia del rail principal:

```text
12V sistema (split externo, upstream del eFuse de la PCBA)
   → Littelfuse 0FHM0001ZXJ
   → Littelfuse 0997002.WXN / 2 A
   → RECOM R-78K5.0-2.0L / 5 V, 2 A
   → 5V_HMI
      ├─ Nextion NX8048P050-011C-Y
      ├─ Nextion BOX Speaker
      └─ J_HMI.1 → TXU0202 VCCB + C_HMI_B
```

Consecuencias:

- display/audio no atraviesan la NFB PCBA v2;
- `5V_RAIL` queda para pH, ORP, DO y la cadena 3V3;
- `5V_HMI` es una net distinta y no puede unirse a `5V_RAIL`;
- el convertidor dedicado tiene 2.0 A nominales frente a 1.5 A reservados, es decir, **0.5 A de headroom nominal**;
- se recomienda fuente de sistema 12 V / 6 A para recuperar margen global.

PR19D introdujo `5V_HMI` como la net #60 y la ruteó como lote ALL_OR_NOTHING 1/1: **7 segmentos + 2 vías**, acumulado **924 segmentos / 121 vías**, `In1.Cu` sin señales, zones=0, DRC=0. El escape inmediato de `U_HMI_LVL.7` usa 0.20 mm por ≤1.20 mm debido al pitch VSSOP; el clearance permanece ≥0.20 mm y la distribución retorna a 0.40 mm.

El cierre de diseño no sustituye el first article: deben medirse arranque/corriente, temperatura del RECOM dentro del enclosure, comportamiento del fusible de 2 A, mating del arnés y EMC del cable final.

## Firmware y mantenimiento

- Transporte de producción: UART D0/D1 a través de `TXU0202DCUR`.
- Versionar fuente Nextion `.HMI` y binario liberado `.tft`.
- Actualización de campo/lab: microSD mediante `SDExtender`.
- Programación/diagnóstico de banco: `Foca Max`.

## Archivos fuente de verdad

- `hardware/hmi_system_contract.json`
- `hardware/hmi_power_eco.json`
- `hardware/pr19d_hmi_power_routing_manifest.json`
- `bom/insight_hmi_system_bom.csv`
- `docs/HMI_POWER_ECO_PR19D.md`
- `hardware/z2_digital_contract.json`
- `hardware/z2_production_netlist.json`
- `hardware/power_architecture_contract.json`
- `hardware/routing_contract.json`
- `hardware/routing_batches_contract.json`
- `kicad/lib/nfb_footprints.pretty/Nextion_NX8048P050_011C_Y_Enclosure.kicad_mod`
- `kicad/lib/nfb_footprints.pretty/RECOM_R78K5_0_2_0L_External.kicad_mod`
