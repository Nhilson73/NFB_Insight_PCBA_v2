# Migration from `nebula_qshield_pcb`

The previous Q-Shield repository is an **engineering donor**, not a PCB-layout template.

## Inherit

- Validated component selections and manufacturer part numbers.
- KiCad symbols and footprints that have already been checked against the physical part.
- UNO Q shield/header pattern and official mechanical reference.
- Net naming that already matches the Insight firmware contract.
- ESD/protection concepts for sensor interfaces.
- Analog front-end circuit intent for pH, ORP, temperature, CO2 pressure and DO.
- HX711/load-cell interface.
- RTC, GPS, HMI UART and I2C architecture.
- Watchdog architecture.
- BOM/DNP metadata where it remains relevant to Insight.
- Existing validation scripts such as schematic-to-PCB parity checks.
- Useful 3D models and enclosure/cable documentation after review.

## Review before inheritance

These items must not be copied without re-approval:

- 12 V input protection chain and current ratings.
- F1 PTC sizing.
- D2 reverse-polarity diode sizing/topology.
- buck regulator thermal/current margin.
- actuator power distribution.
- chiller power architecture.
- relay contact use and clearance classification.
- connector families and panel-vs-PCBA termination strategy.
- galvanic isolation implementation and isolated power islands.
- any item whose tier/DNP assignment is inconsistent across donor documentation.

## Do not inherit

- PCB component coordinates.
- tracks, vias or autorouter output.
- copper pours/zones.
- donor board Edge.Cuts.
- donor board dimensions.
- routing compromises involving `In1.Cu`.
- reduced clearances introduced only to make routing pass.
- unconnected-net state.

## Frozen Insight signal contract for bootstrap

The V2 bootstrap adopts the following mapping as its source of truth pending a direct firmware cross-check:

| UNO Q pin | V2 function | Tier |
|---|---|---|
| A0 | PH_ADC | Insight |
| A1 | ORP_ADC | Insight |
| A2 | TEMP_ADC | Insight |
| A3 | RESERVED / humidity removed | DNP |
| A4 | CO2_ADC | Insight |
| A5 | DO_ADC | Insight |
| D0 | HMI_RX | Insight |
| D1 | HMI_TX | Insight |
| D2 | HX711_DOUT | Insight |
| D3 | HX711_SCK | Insight |
| D4 | MCU_WDI | Insight |
| D5 | PUMP_PWM | Insight |
| D6 | PUMP_DIR | Insight |
| D7 | CO2_SOL_CTL | Insight |
| D8 | CHILLER_CTL | Insight control only |
| D9 | RESERVED / proportional gas valve removed | DNP |
| D10 | RS485_IRQ | reserve for future Signature path |
| D13 | LED_STATUS | Insight |
| D20 | I2C_SDA | Insight |
| D21 | I2C_SCL | Insight |

## V2 product principle

V2 is designed first as **NFB Insight**, not as a physically congested universal board for every future tier.

Future Signature capability should be enabled by deliberate expansion hooks, reserved interfaces or an optional daughterboard when that is electrically/mechanically cleaner than populating unused circuitry on every Insight PCBA.
