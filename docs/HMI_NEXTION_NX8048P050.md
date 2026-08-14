# Decisión HMI — Nextion NX8048P050-011C-Y

## Estado

**SELECCIONADO para NFB Insight:** Nextion Intelligent Series 5.0" capacitiva con enclosure, MPN `NX8048P050-011C-Y`, SKU `6920075776553`.

Esta pantalla es un **ensamble externo**, no un footprint poblado sobre la PCBA. La shield mantiene `J_HMI` como interfaz de cable y el repositorio añade una huella mecánica de referencia del enclosure para integración física.

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

La razón de **no mover pads** es deliberada: PR19C ya cerró el routing de `HMI_RX/HMI_TX`. ITEAD publica la interfaz del display como `XH2.54 4P` pero no publica en la ficha consultada un MPN JST exacto. Por tanto:

1. no se inventa una equivalencia 2.50 ↔ 2.54;
2. se conserva la geometría de producción del board-side connector;
3. el arnés final debe pasar **mating test de first article** antes de release;
4. cualquier cambio posterior de `J_HMI` será un ECO de footprint/routing explícito.

Mapping lógico: `HMI_TX` del UNO → TXU0202 → `HMI_FIELD_RX` → RX de Nextion; TX de Nextion → `HMI_FIELD_TX` → TXU0202 → `HMI_RX` del UNO. Campo protegido con `PESD5V0U1UL,315`.

## Accesorios seleccionados

### Nextion Micro SD Card Extender

- modelo `SDExtender`;
- 17.1 × 41.48 × 2.5 mm; 7 g;
- FAT32 microSD; compatible con todas las series Nextion;
- ensamble externo, no poblado en PCBA;
- fuente: https://itead.cc/product/nextion-micro-sd-card-extender/.

### Nextion BOX Speaker

- 31 × 28 × 14.8 mm; 21.2 g;
- 1.5 W, 100 Hz–3 kHz;
- conector hembra 2P pitch 1.25 mm `1.25T-2-2A`; cable 250 mm;
- ITEAD exige **+0.5 A** sobre la recomendación de alimentación del display;
- reserva de diseño para display + speaker: **5 V / 1.5 A**;
- verificar acceso/montaje del audio con la variante `-Y` durante first article;
- fuente: https://itead.cc/product/nextion-box-speaker/.

### Nextion Foca Max

`Foca Max` queda como **herramienta de programación/bring-up, no instalada en el producto**:

- CP2102; TTL 3.3 V; hasta 2 Mbps;
- DC externo 8–26 V; salida 5–5.5 V, 2 A máx.;
- PCB 50 × 50 × 1.6 mm; volumen 50 × 50 × 12 mm;
- incluye USB wire y XH2.54 4P wire;
- para pantallas >4.3" ITEAD recomienda alimentación DC externa 8–26 V;
- fuente: https://itead.cc/product/nextion-foca-max-5v2a-output-usb-to-ttl-serial-converter-board/.

## Gate de potencia — obligatorio antes de PR20A/release

El `5V_RAIL` actual usa `TPSM33625RDNR` (2.5 A nominal), pero el contrato de NFB limita el diseño a **1.5 A continuo** y ese mismo rail alimenta pH, ORP, DO y la entrada del LDO 3.3 V. La HMI + speaker ya reserva **1.5 A** por sí sola.

Por tanto el uso del conjunto está seleccionado, pero **la alimentación desde el 5V_RAIL actual no se declara liberada**. Antes de congelar PR20A se debe cerrar uno de estos ECOs:

- validar térmica/corriente/layout y elevar formalmente el presupuesto continuo con margen para todas las cargas, o
- introducir 5 V dedicado para HMI mediante una revisión eléctrica explícita.

No se reduce margen ni se relaja una regla para hacer caber el HMI.

## Firmware y mantenimiento

- Transporte de producción: UART D0/D1 a través de `TXU0202DCUR`.
- Versionar fuente Nextion `.HMI` y binario liberado `.tft`.
- Actualización de campo/lab: microSD mediante `SDExtender`.
- Programación/diagnóstico de banco: `Foca Max`.

## Archivos fuente de verdad

- `hardware/hmi_system_contract.json`
- `bom/insight_hmi_system_bom.csv`
- `kicad/lib/nfb_footprints.pretty/Nextion_NX8048P050_011C_Y_Enclosure.kicad_mod`
- `hardware/z2_digital_contract.json`
- `hardware/power_architecture_contract.json`
