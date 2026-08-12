# PR #11 — Notas técnicas de cierre

Este PR no habilita placement ni routing. Su objetivo es elevar la calidad de la evidencia física y cerrar la integración eléctrica contractual entre Z1, Z2 y Z3.

## Decisiones

- El footprint Honeywell MPR se considera cerrado únicamente porque existe geometría explícita de PCB en una fuente primaria del fabricante.
- El TPS259470A permanece bloqueado para placement hasta reproducir y comparar exactamente el land pattern RPW0010A/HotRod QFN del drawing TI.
- El TPSM33625 permanece bloqueado para placement hasta importar o verificar CAD autorizado por TI para RDN-11.
- Body size y pitch nunca se consideran suficientes para inventar un land pattern de producción.
- Z1, Z2 y Z3 comparten únicamente las nets definidas en `hardware/electrical_integration_contract.json`.
- La frontera de potencia del UNO Q definida en PR #9 se conserva: rails locales del shield separados y `IOREF` solo host→shield.

## Resultado esperado

Un merge de PR #11 significa que la arquitectura eléctrica puede avanzar hacia Z4 sin riesgo de confundir una integración lógica cerrada con un placement físicamente autorizado. Los dos footprints TI críticos permanecen como gates explícitos para Fase 4.
