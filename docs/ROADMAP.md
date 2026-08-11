# NFB Insight PCBA v2 — Development Roadmap

## Phase 0 — Architecture freeze

- [x] Initialize clean repository.
- [x] Freeze global coordinate system.
- [x] Freeze UNO Q orientation: USB-C toward `-Y`.
- [x] Freeze board height at `68.58 mm`.
- [x] Freeze growth direction: `+X` only.
- [x] Designate `Y=0` as FIELD I/O EDGE.
- [x] Define functional zoning order.
- [x] Define selective inheritance from donor Q-Shield.
- [x] Classify donor BOM into ACCEPT / REVIEW / DROP / RESERVE.

## Phase 1 — Mechanical donor assets

- [ ] Import/create immutable rotated UNO Q footprint at global origin.
- [ ] Verify all four mounting holes from transformed coordinates.
- [ ] Add USB-C, power-button, JCTL, SPI/Qwiic and connector keepouts.
- [ ] Add initial board outline with `H = 68.58 mm`; width intentionally provisional.
- [ ] Add enclosure/service-side connector courtyard corridor along `Y=0`.
- [ ] Check UNO Q + carrier relationship in KiCad 3D Viewer.

## Phase 2 — Insight schematic clean-room migration

- [ ] Rebuild schematic hierarchy for V2 rather than copying the donor root sheet verbatim.
- [ ] Freeze A0/A1/A2/A4/A5 sensor mapping.
- [ ] Freeze D0/D1 HMI, D2/D3 HX711, D4 watchdog, D5-D8 actuator controls, D20/D21 I2C.
- [ ] Remove humidity channel from the Insight baseline.
- [ ] Keep proportional-gas PWM out of baseline.
- [ ] Decide RS485/Signature expansion mechanism without congesting the Insight board.
- [ ] Cross-check pin contract directly against `Nebula_ArduinoAPPLab_UNOQ` firmware source of truth.
- [ ] ERC = 0.

## Phase 3 — Power architecture freeze

- [ ] Partition logic/sensor power from dirty actuator power.
- [ ] Decide whether actuator loads traverse the PCBA or only control interfaces do.
- [ ] Prefer externally powered chiller; PCBA supplies control only.
- [ ] Calculate continuous/peak currents.
- [ ] Re-select F1/D2/input connector as needed.
- [ ] Revalidate buck/LDO topology.
- [ ] Define netclasses before placement/routing.

## Phase 4 — Placement by zones

- [ ] Z0 UNO Q locked.
- [ ] Z1 analog/isolation placement with field connectors directly below front ends.
- [ ] Z2 digital/low-noise placement.
- [ ] Z3 power placement with minimized switching loops.
- [ ] Z4 actuators/dirty power at far +X.
- [ ] All field connectors aligned along `Y=0` facing `-Y` where mechanically possible.
- [ ] 3D mechanical review before routing.
- [ ] Freeze final board width from actual placement.

## Phase 5 — Routing

- [ ] Preserve continuous reference plane for sensitive signals.
- [ ] Manual priority routing: pH/ORP/DO → clock/I2C/HX711 → power → actuators.
- [ ] Do not sacrifice plane integrity or isolation merely to satisfy autorouter congestion.
- [ ] Route high-current paths only after load/current architecture is frozen.
- [ ] Add stitching vias/test points deliberately.
- [ ] 0 unexpected unconnected items.
- [ ] DRC = 0.

## Phase 6 — Manufacturing readiness

- [ ] BOM lifecycle/availability review.
- [ ] Footprint-to-datasheet audit.
- [ ] Panel connector and cable-strain review.
- [ ] Gerber/drill visual review.
- [ ] BOM + CPL export.
- [ ] Assembly variant = Insight.
- [ ] Fabrication notes and stackup freeze.
- [ ] Tag `v2.0-RC1` only after review gates pass.

## Phase 7 — Bring-up and HIL

- [ ] Rail bring-up before UNO Q installation.
- [ ] Current-limited power-on sequence.
- [ ] Sensor-channel injection tests.
- [ ] pH/ORP/DO noise and isolation validation.
- [ ] HX711/load-cell test.
- [ ] HMI/GPS/RTC/I2C functional checks.
- [ ] Pump/solenoid/chiller control tests with representative loads.
- [ ] Watchdog/failsafe test.
- [ ] HIL fixture and repeatable production test procedure.
