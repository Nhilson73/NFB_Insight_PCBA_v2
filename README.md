# NFB Insight PCBA v2

PCBA **shield/carrier** para **Nebula Fermentation Insight®**, diseñada alrededor del factor de forma inmutable del **Arduino UNO Q**. El repositorio `Nhilson73/nebula_qshield_pcb` es únicamente donante de ingeniería/trazabilidad; no gobierna placement, routing ni topología de producción V2.

## Fuente primaria UNO Q

Toda decisión dependiente del Arduino UNO Q se contrasta primero contra repositorios oficiales Arduino en GitHub (`github.com/Arduino`, especialmente `arduino/docs-content`), luego `docs.arduino.cc` y finalmente datasheets oficiales. La jerarquía y snapshots revisados viven en `docs/SOURCE_OF_TRUTH.md`.

## Frontera del producto / compliance

NFB Insight PCBA v2 es un **shield/carrier del UNO Q**, no un rediseño de su radio. No añade transmisores, antena, matching ni amplificación RF. El **EU Compliance Design Gate** vive en `docs/EU_COMPLIANCE_GATE.md` / `compliance/eu_compliance_contract.json` y cubre EMC, RoHS 3, REACH, WEEE, RED/CE del producto integrado.

## Mecánica

- UNO Q rotado; origen global `(0,0)`; USB-C hacia `-Y`.
- Envolvente UNO Q `53.34 × 68.58 mm`.
- Altura total PCB fija `68.58 mm`; crecimiento solo `+X`.
- `Y=0` = FIELD I/O EDGE.
- Gradiente: Z0 UNO Q → Z1 sensores → Z2 digital → Z3 potencia → Z4 actuadores.
- Ancho actual `220 mm` **provisional** hasta placement.

## Z1 sensores

- pH/A0 y DO/A5: 0–3 V acondicionados, ESD + `1 kΩ / 100 nF`.
- ORP/A1: divisor `10 kΩ / 20 kΩ`, máximo 3.0 V.
- TEMP/A2-D16: DS18B20 `TEMP_1WIRE`.
- CO₂: Honeywell `MPRLS0030PA00002A`, I²C `0x28`; `CO2_ADC` retirado.
- A4/pad13 = `PUMP_CURRENT_ADC`.

## Z2 digital / bajo ruido

- I²C: MPR `0x28` + DFR1103 `0x66`.
- HX711 3.3 V / 10 SPS en D2/D3.
- HMI D0/D1 mediante `TXU0202DCUR`.
- Watchdog `TPS3823-30DBVR`, WDI=D4.
- PR #16 cierra `J_LOADCELL` con Phoenix Contact **1757268 / MSTBA 2,5/4-G-5,08**.

## Z3 potencia — PR #9 / #10 / #13 / #15

- 12 V protegido → VIN del UNO Q.
- `5V_RAIL` y `3V3_RAIL` son locales del shield; no se unen a J_UNOQ.5/J_UNOQ.4.
- Protección `SMBJ15A-TR + TPS259470ARPWR`.
- Split `12V_HOST_VIN / 12V_LOGIC / 12V_ACT`.
- `F_ACT=045401.5MR`.
- 5 V `TPSM33625RDNR`; 3.3 V `TLV75533PDBVR`.
- Potencia del chiller externa.

## Z4 actuadores

- Bomba `DRV8242HQRHLRQ1`, D5/D6, IPROPI → A4.
- Solenoide `TPS1HC120CQDYCRQ1`, D7, ILIM ~0.5 A.
- Chiller `AQY212EHAX` + `2N7002`, **dry contact SELV ≤48 V / NO MAINS**.
- D10=`ACT_FAULT_N`; D9 DNP/Reserva.

## Hierarchy EDA — PR #14 / #15

`kicad/NFB_Insight_PCBA_v2.kicad_sch` es el root Z0–Z4. PR #15 materializó las hojas desde JSON/BOM de forma determinista y eliminó completamente la deuda ERC del PR #14.

KiCad **10.0.5** sobre el hierarchy completo:

- **0 Errors**
- **0 Warnings**
- **0 violations**

Los JSON/BOM siguen siendo autoridad; las hojas generadas no deben editarse manualmente para alterar conectividad.

## Pre-placement readiness — PR #16

Fuente: `hardware/placement_readiness_contract.json`; detalle: `docs/FASE4_PR16_PREPLACEMENT_READINESS.md`.

Se revalidó UNO Q contra `arduino/docs-content` commit `24445a32e249d410c1e4359bdc99d8c0dcb17bd2`. Arduino identifica `WCBN3536A / Qualcomm WCN3980` y una **shared PCB antenna**.

La documentación fuente revisada no publica un antenna keepout numérico textual. NFB por tanto **no inventa una distancia RF**. En su lugar:

- Z0 completo queda prohibido para footprints de producción NFB;
- el shield empieza en `X=53.34 mm`;
- Z1 quiet/sensors queda adyacente al host;
- Z3/Z4 ruidosos permanecen desplazados hacia `+X`;
- cualquier metal/PCB apilada/enclosure sobre la región RF del host requiere validación 3D/RF posterior.

PR #16 también congela:

- `In1.Cu` = **plano GND continuo; no signal routing**;
- orden FIELD I/O izquierda→derecha: pH, ORP, TEMP, MPR CO₂, DO, load cell, GNSS/RTC, HMI, power, pump, CO₂ solenoid, chiller;
- todos los conectores side-entry hacia `-Y`, salvo el puerto vertical MPR;
- retornos high-current fuera de Z1/Z2;
- switching de buck confinado a Z3;
- drivers/bulk de actuadores confinados a Z4.

## Estado actual

Arquitectura Z0–Z4, compliance, footprints críticos y hierarchy EDA están cerrados. PR #16 prepara el PCB para iniciar **placement XY** sin autorizar todavía routing. El ancho de 220 mm continúa provisional y podrá crecer únicamente hacia `+X` si los courtyards reales lo requieren.

**Siguiente frente después del gate PR #16: PR #17 — placement físico de producción, sin routing.**
