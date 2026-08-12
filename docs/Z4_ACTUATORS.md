# NFB Insight PCBA v2 — Z4 Actuadores PR #12

**Estado:** baseline eléctrico de producción; placement/routing fuera de alcance.  
**Fuente de verdad:** `hardware/z4_actuator_contract.json` + `hardware/z4_production_netlist.json`.

## Objetivo

Reemplazar la electrónica discreta/relés heredada del Q-Shield por drivers protegidos y diagnosticables, manteniendo la potencia ruidosa en Z4 y la lógica/telemetría en dominio 3.3 V del UNO Q.

## 1. Bomba — DRV8242H-Q1

Se selecciona `DRV8242HQRHLRQ1` (versión HW) en lugar de `IR2104 + IRLZ44N`.

- VM desde `12V_ACT`.
- D5 = `PUMP_PWM` -> EN/IN1.
- D6 = `PUMP_DIR` -> PH/IN2.
- MODE a GND -> PH/EN.
- SR por 22 kΩ a GND -> nivel de slew moderado para reducir EMI.
- DIAG e ITRIP a GND; se preservan protecciones internas y retry, sin regulación ITRIP externa.
- nFAULT open-drain comparte `ACT_FAULT_N`.
- VM con 100 nF + 22 µF local.

### Telemetría de corriente

El pin `IPROPI` se usa activamente y A4 deja de ser una reserva desperdiciada:

- `R_PUMP_IPROPI = 1.5 kΩ`.
- `C_PUMP_IPROPI = 100 nF`.
- A4/pad13 = `PUMP_CURRENT_ADC`.
- con A_IPROPI típico 1425 A/A, una corriente de bomba de 0.8 A produce ~0.842 V;
- usando el factor mínimo contractual 1354 A/A, 3.05 V corresponden a ~2.75 A, dejando margen para detectar inrush/atasco antes de saturar el ADC.

Esto permite detectar bomba trabada, degradación mecánica, desconexión indirecta y construir un baseline de corriente durante HIL.

## 2. Solenoide CO₂ — TPS1HC120C-Q1

Se selecciona `TPS1HC120CQDYCRQ1`, smart high-side automotive.

- VBB = `12V_ACT`.
- D7 = `CO2_SOL_CTL` -> EN por 100 Ω.
- pull-down 100 kΩ para fail-safe cerrado durante boot.
- `R_CO2_ILIM = 27 kΩ` -> límite objetivo ~0.5 A según relación TI `R_ILIM(kΩ) ≈ 13.5 / I(A)`.
- FLT1 open-drain -> `ACT_FAULT_N`.
- FLT2 -> `CO2_OPENLOAD_N` con pull-up 10 kΩ y test point.
- clamp inductivo integrado: no se puebla flyback discreto en el baseline.

La salida conmutada y GND llegan a un Phoenix 1757242 sobre el FIELD I/O EDGE.

## 3. Chiller — contacto seco PhotoMOS

La PCBA **no alimenta el chiller**. D8 controla únicamente un contacto seco aislado:

- `AQY212EHAX`, Panasonic PhotoMOS GE DIP4 SMD, 1 Form A.
- rating del componente 60 V, pero NFB limita el uso del sistema a **SELV <=48 V**.
- **No se permite conmutación de mains/red eléctrica desde este conector.**
- aislamiento componente 5 kVrms.
- lado de contacto completamente flotante respecto a GND/rails del shield.

El LED del PhotoMOS se conmuta con `2N7002,215` para no cargar directamente el GPIO:

- D8 -> 1 kΩ -> gate;
- 100 kΩ gate-GND;
- 3.3 V -> 360 Ω -> LED PhotoMOS -> NMOS.
- con Vf máximo 1.5 V: corriente LED = 5.0 mA; con Vf típico 1.25 V: ~5.69 mA.

## 4. Diagnóstico común

D10 deja la reserva RS485 que no pertenece al baseline Insight y pasa a:

`ACT_FAULT_N`

Es un wired-OR active-low con pull-up único de 10 kΩ a `3V3_RAIL`, alimentado por:

- nFAULT del DRV8242H-Q1;
- FLT1 del TPS1HC120C-Q1.

FLT2 del solenoide se conserva como test/diagnóstico específico de open-load. El firmware deberá incorporar D10 y A4 en una migración posterior.

## 5. Fail-safe

- PWM bomba: 100 kΩ pull-down.
- dirección bomba: 100 kΩ pull-down.
- EN solenoide: 100 kΩ pull-down.
- gate chiller: 100 kΩ pull-down.
- durante boot/reset, bomba y solenoide quedan off y el contacto chiller abierto.

## 6. EMC / layout

Cuando se habilite placement:

- drivers y conectores quedan en Z4, lejos de Z1/Z2 y RF UNO Q;
- decoupling VM/VBB adyacente al driver;
- loops de OUT1/OUT2 y VOUT/GND mínimos;
- retorno de corriente de bomba/solenoide a la región estrella de potencia;
- `PUMP_CURRENT_ADC` sale de Z4 hacia A4 por una ruta referenciada a GND, lejos de nodos de switching;
- nFAULT/FLT1 son señales lentas, con pull-up en 3.3 V;
- contacto PhotoMOS conserva aislamiento físico y clearance apropiado para SELV 48 V, aunque no se usa para mains.

## 7. Footprint gates

Antes de placement deben cerrarse contra CAD/drawing de fabricante:

- TI RHL-20 del DRV8242;
- TI DYC-8 del TPS1HC120;
- Panasonic GE DIP4 SMD del AQY212EHAX.

El audit machine-readable vive en `hardware/footprint_audit.json` y CI bloquea placement prematuro.

## 8. Fuentes primarias

- Arduino `docs-content`, UNO Q datasheet: dominio MCU/JDIGITAL/JANALOG 3.3 V.
- Texas Instruments DRV8242-Q1 datasheet/product resources.
- Texas Instruments TPS1HC120-Q1 datasheet/product resources.
- Panasonic Industry AQY212EHAX product/CAD resources.
- Nexperia 2N7002 official product documentation.
