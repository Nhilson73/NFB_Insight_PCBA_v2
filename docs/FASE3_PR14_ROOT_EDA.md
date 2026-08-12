# PR #14 — Integración EDA raíz Z0–Z4

**Estado:** jerarquía eléctrica inter-zona previa a materialización completa de símbolos internos.  
**Fuente machine-readable:** `hardware/root_eda_contract.json`.  
**Root KiCad:** `kicad/NFB_Insight_PCBA_v2.kicad_sch`.

## Objetivo

Sustituir el antiguo root textual/Z1 por una jerarquía KiCad real que conecte las fronteras eléctricas entre:

- Z0 — Arduino UNO Q host;
- Z1 — sensores;
- Z2 — digital / bajo ruido;
- Z3 — potencia;
- Z4 — actuadores.

PR #14 **no pretende todavía dibujar de nuevo cada componente interno** de las cuatro zonas. La conectividad interna continúa gobernada por los netlists JSON/BOM de producción ya validados. Esto evita duplicar manualmente más de cien referencias y crear una segunda fuente de verdad antes de construir un generador reproducible.

## Jerarquía

El root instancia cinco hojas:

- `uno_q_interface.kicad_sch`
- `z1_interface.kicad_sch`
- `z2_interface.kicad_sch`
- `z3_interface.kicad_sch`
- `z4_interface.kicad_sch`

Cada hoja expone `hierarchical_label` y el root contiene el `sheet pin` correspondiente conectado mediante la net local del mismo nombre.

## Frontera UNO Q

Z0 expone únicamente endpoints activos del contrato `hardware/insight_pin_contract.json`.

Puntos críticos:

- `GND` sí pertenece a Z0 y es referencia común Z0–Z4.
- `3V3_RAIL` y `5V_RAIL` **no pertenecen a Z0**; siguen siendo rails locales del shield.
- `J_UNOQ.4` no alimenta `3V3_RAIL`.
- `J_UNOQ.5` no alimenta `5V_RAIL`.
- `UNO_IOREF_3V3` es host→shield.
- `12V_HOST_VIN` es shield→VIN del host.
- A4=`PUMP_CURRENT_ADC`; D10=`ACT_FAULT_N`.
- `CO2_ADC`, `TEMP_ADC`, `HUM_ADC`, `CO2_PWM/CO2_FLOW_PWM` y RS485 Insight permanecen prohibidos.

## Nets inter-zona

`hardware/root_eda_contract.json` congela la pertenencia de cada net. Ejemplos:

- `GND`: Z0/Z1/Z2/Z3/Z4.
- `5V_RAIL`: Z1/Z2/Z3.
- `3V3_RAIL`: Z1/Z2/Z3/Z4.
- I²C SDA/SCL: Z0/Z1/Z2.
- sensores analógicos/digitales: Z0↔Z1.
- HMI/HX711/watchdog/status: Z0↔Z2.
- host VIN/IOREF: Z0↔Z3.
- `12V_ACT`: Z3↔Z4.
- controles/diagnóstico de actuadores: Z0↔Z4.

## Contrato Z1 separado

El archivo raíz antiguo contenía en realidad el contrato textual Z1. PR #14 lo separa como `kicad/z1_sensor_contract.kicad_sch` para que los gates Z1 sigan validando el baseline PR #6/#12 sin confundirlo con la nueva jerarquía raíz.

## Gate automático

`tools/validate_root_eda.py` comprueba:

- exactamente cinco hojas Z0–Z4;
- endpoint set Z0 = endpoints activos del pin contract;
- GND incluye Z0 y rails locales excluyen Z0;
- labels de cada child sheet = contrato inter-zona;
- cantidad de sheet pins/labels del root = ownership contractual;
- I²C y rails compartidos correctos;
- ausencia de nets legacy/prohibidas;
- footprints PR #13 siguen cerrados;
- `.kicad_pcb` continúa sin placement de componentes de producción.

El workflow `Validación root EDA inter-zona Insight` ejecuta además ERC del root con KiCad 10.0.5.

## Alcance explícitamente pendiente

`zone_internal_component_symbols=false` en PR #14.

Por tanto, antes de placement se requiere un siguiente gate que materialice símbolos/conectividad interna de Z1/Z2/Z3/Z4 a partir de JSON/BOM de forma reproducible, evitando transcripción manual. Ese será el siguiente PR.

## Fuera de alcance

- placement XY;
- routing;
- cambio de ancho del PCB;
- thermal-via layout;
- revisión 3D;
- HIL / termografía / pre-scan EMC.
