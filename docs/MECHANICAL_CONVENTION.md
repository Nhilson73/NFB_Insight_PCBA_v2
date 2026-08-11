# NFB Insight PCBA v2 — Mechanical Convention

**Status:** FROZEN for V2 bootstrap  
**Source donor:** `Nhilson73/nebula_qshield_pcb/docs/UNO_Q_FORM_FACTOR.md`

## 1. Global coordinate system

The new PCBA uses a clean, explicit Cartesian convention:

- Global origin `(0,0)` = lower-left corner of the **rotated UNO Q board envelope**.
- `+X` = PCBA expansion direction.
- `+Y` = upward inside the enclosure.
- `-Y` = cable-exit / service direction.
- Arduino UNO Q USB-C faces `-Y`.

The board shall never expand toward negative X or negative Y.

## 2. Immutable UNO Q envelope

Official UNO Q envelope before rotation:

- Width: 68.58 mm
- Height: 53.34 mm

After rotating the UNO Q so USB-C faces `-Y`, the immutable envelope becomes:

- `X = 0.00 ... 53.34 mm`
- `Y = 0.00 ... 68.58 mm`

Therefore:

- **NFB Insight PCBA v2 board height is frozen at 68.58 mm.**
- Overall board width is variable and shall grow only toward `+X` as required by real placement.

## 3. Coordinate transform from donor UNO Q reference

The donor repository expresses UNO Q mechanical coordinates in its previous orientation.
For the V2 orientation use:

```text
X_v2 = 53.34 - Y_donor
Y_v2 = X_donor
```

### Rotated mounting-hole centers

| Hole | X_v2 (mm) | Y_v2 (mm) |
|---|---:|---:|
| H1 | 50.80 | 13.97 |
| H2 | 45.72 | 66.04 |
| H3 | 17.78 | 66.04 |
| H4 | 2.54 | 15.24 |

These four locations are immutable unless the official Arduino UNO Q mechanical specification changes.

## 4. UNO Q keepouts

The V2 design must preserve physical access/clearance for all UNO Q features, including at minimum:

- USB-C
- power button
- JCTL
- SPI2 / JSPI
- QWIIC
- JMEDIA / JMISC where applicable
- shield/header mating volume
- mounting hardware and standoffs

Keepouts are mechanical constraints, not placement suggestions.

## 5. Field I/O edge

The complete lower board edge at `Y = 0` is designated:

> **FIELD I/O EDGE**

Rules:

1. All wired field connectors should be positioned on or immediately adjacent to the `Y=0` edge.
2. Cable mating direction should face `-Y` whenever connector geometry permits.
3. Sensor connectors shall be located directly below or as close as practical to their corresponding front-end circuitry.
4. Do not route high-impedance sensor inputs long distances across the PCBA before conditioning.
5. Mechanical cable loads from heavy/coaxial cables should preferably terminate at the enclosure panel, not directly on the PCBA.

## 6. Functional zoning along +X

The intended left-to-right ordering is:

```text
X = 0
│
├── Z0  UNO Q IMMUTABLE
├── Z1  ANALOG / SENSOR FRONT-END / GALVANIC ISOLATION
├── Z2  DIGITAL / LOW-NOISE / HX711 / I2C / HMI / RTC / GPS
├── Z3  POWER MANAGEMENT
└── Z4  ACTUATORS / DIRTY POWER / FIELD OUTPUTS
                                      → +X
```

Zone widths are **not frozen** during bootstrap. They must be derived from actual component placement and manufacturability.

## 7. Placement principles

- Sensitive analog circuitry stays closest to its field connector.
- Buck switching loops and actuator switching nodes stay away from pH/ORP/DO front ends.
- Prefer a continuous reference plane under low-level signals.
- Do not use autorouting pressure as justification to violate the zoning architecture.
- GPS antenna/receiver placement must be reviewed for copper and enclosure interference.
- Test points must remain service-accessible after enclosure assembly.

## 8. Release gate

No routing shall be considered production-intent until:

- UNO Q transformed coordinates are checked against the official mechanical reference.
- All keepouts are represented in KiCad.
- `Y=0` field-I/O connector orientation is reviewed in 3D.
- enclosure cable egress is confirmed.
- zone boundaries have been reviewed from actual placement, not estimated drawings.
