# NFB Insight PCBA v2

Clean-sheet carrier/PCBA for **Nebula Fermentation Insight®** built around the Arduino UNO Q immutable mechanical form factor.

This repository intentionally starts from a clean geometry. The previous `Nhilson73/nebula_qshield_pcb` repository is treated as an **engineering donor** for validated BOM items, symbols, footprints, net naming, test concepts and documentation — not as a placement/routing template.

## Frozen V2 mechanical convention

- Global board origin: `(0,0)` at the lower-left of the rotated UNO Q envelope.
- UNO Q rotated so its USB-C points toward `-Y`.
- UNO Q immutable envelope after rotation: `53.34 mm × 68.58 mm`.
- Board height is frozen at `68.58 mm`.
- PCBA grows only toward `+X`.
- Field wiring/connectors are placed along the lower `Y=0` edge and face `-Y` toward the enclosure cable-exit side.
- Functional zoning grows left-to-right: UNO Q → analog/isolation → digital/low-noise → power → actuators.

## First milestone

Bootstrap the geometry, inherited engineering assets and Insight BOM before placement or routing.
