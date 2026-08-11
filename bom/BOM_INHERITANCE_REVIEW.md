# NFB Insight PCBA v2 — BOM Inheritance Review

This file records which donor components are accepted for V2 bootstrap and which require electrical/mechanical re-selection before schematic freeze.

## Status legend

- `ACCEPT` — may be inherited into the V2 schematic/footprint set.
- `REVIEW` — useful donor candidate, but selection/rating/footprint must be re-approved.
- `DROP` — not part of the Insight V2 baseline.
- `RESERVE` — future capability only; do not let it drive V2 placement congestion.

## Power and protection

| Donor Ref | Part | Donor value | V2 status | Reason |
|---|---|---|---|---|
| D1 | SMAJ15A | 15 V TVS | REVIEW | Protection concept is useful; clamp/energy rating must match final 12 V architecture. |
| F1 | MF-MSMF110/24X-2 | 1.1 A hold / 2.2 A trip | REVIEW | Donor rating is incompatible with some documented Insight current scenarios. Re-size after current-domain split is frozen. |
| D2 | SS34 | 3 A Schottky | REVIEW | 3 A path may be insufficient if it carries actuator current. Consider architecture change instead of simply increasing diode size. |
| U1 | TPS54302DDCR | 12→5 V / 3 A buck | REVIEW | Function fits; thermal/load margin and actual UNO Q/HMI demand must be recalculated. |
| L1 | 744043004700 | 4.7 µH / 4 A | REVIEW | Must be revalidated with selected buck operating point and ripple target. |
| U2 | AMS1117-3.3 | 3.3 V / 800 mA | REVIEW | Electrically usable but efficiency/thermal and modern alternatives should be considered. |
| FB1 | BLM31PG601SN1L | 600 Ω @ 100 MHz / 2 A | REVIEW | Keep only if rail segmentation/filter requirement remains. |

## Analog / sensor front-end

| Donor item | V2 status | Notes |
|---|---|---|
| MCP6002-I/SN op-amps | ACCEPT | Keep for low-voltage buffering where the final sensor interface still requires analog conditioning. |
| PESD5V0 / PESD3V3 sensor ESD parts | ACCEPT | Keep concept and footprints; verify exact working voltage per interface. |
| RC antialias networks | ACCEPT | Values remain starting point; tune per actual sensor bandwidth/noise tests. |
| pH front-end | ACCEPT | Place directly above PH field connector; minimize high-impedance trace length. |
| ORP front-end | ACCEPT | Same placement rule as pH. |
| TEMP front-end | ACCEPT | A2 source-of-truth mapping. |
| CO2 pressure front-end | ACCEPT | A4 source-of-truth mapping. |
| DO front-end | ACCEPT | A5 source-of-truth mapping; isolation strategy to be revalidated. |
| Humidity analog channel | DROP | A3 reserved/DNP in Insight V2. |

## Digital / interfaces

| Donor item | V2 status | Notes |
|---|---|---|
| I2C pull-ups 4.7 kΩ | ACCEPT | D20/D21 bus; final equivalent pull-up must account for attached modules. |
| HX711 | ACCEPT | Keep as Insight load-cell interface. |
| RTC DS3231 | ACCEPT | Retain if RTC remains required after firmware/system architecture review. |
| GPS SAM-M8Q path | ACCEPT | Placement must account for antenna/copper/enclosure constraints. |
| HMI UART connector/interface | ACCEPT | Field connector goes on Y=0 edge facing -Y. |
| TPS3823 external watchdog concept | ACCEPT | D4 MCU_WDI contract retained. |
| SC16IS740 + SN74LVC1G04 RS485 bridge | RESERVE | Do not let Signature/future RS485 path congest Insight placement unless explicitly needed in V2. |

## Actuators

| Donor item | V2 status | Notes |
|---|---|---|
| Pump PWM/DIR control | ACCEPT | Keep control function; power stage to be reviewed in dirty-power zone. |
| CO2 solenoid control | ACCEPT | Keep control function; field output at Y=0. |
| Chiller control | ACCEPT | Control signal only in baseline; high-power chiller energy path should preferably remain external to PCBA. |
| IR2104 + IRLZ44N power stage | REVIEW | Re-evaluate topology, package and actual pump load before copy. |
| HF46F relays | REVIEW | Clarify whether contacts switch 12 V SELV or mains/external loads; clearance rules depend on this. |
| PC817 optocouplers | REVIEW | Keep isolation intent, but review CTR/ageing/speed and whether isolation is actually required per output. |
| Proportional CO2 valve PWM path | DROP | D9 reserved/DNP in Insight V2 baseline. |

## Connectors

The donor BOM's connector part numbers are **not automatically frozen** for V2. Connector selection must follow the new enclosure/cable architecture.

Preferred V2 principle:

- all field-wired board connectors at `Y=0` facing `-Y`;
- heavy/coaxial cable strain terminated at enclosure panel where practical;
- sensor connector families selected for serviceability, polarization/keying and environmental requirements;
- maintain short internal connections from panel-mounted pH/ORP/DO interfaces to their analog front ends.

## Before schematic freeze

1. Freeze 12 V domains and determine which loads are powered through the board.
2. Recalculate maximum continuous and peak current for each domain.
3. Select input connector, protection, copper width and fuse/PTC around those currents.
4. Freeze panel-vs-PCBA connector strategy.
5. Cross-check all accepted parts against current availability and lifecycle status.
6. Generate a machine-readable BOM only after those reviews are complete.
