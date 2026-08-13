# Decisión de ingeniería — routing incremental

## Decisión

La Fase 5 se ejecutará bajo estrategia **divide y vencerás**: el routing de las 59 nets se divide en lotes cerrados `28 + 4 + 16 + 10 + 1`.

No se acepta merge parcial dentro de un lote. Cada lote es un checkpoint físico reversible y debe cumplir 100% de conectividad de sus nets declaradas, 0 nets futuras tocadas y 0 regresiones físicas de cobre.

## Motivo

El PR #19 experimental demostró que un routing monolítico mezcla demasiadas variables simultáneamente y dificulta distinguir entre congestión local, corredores long-haul, calidad analógica, potencia y retorno GND.

La partición incremental reduce el espacio de búsqueda, facilita DRC y revisión visual, y deja checkpoints verdes en `main` antes de aumentar la complejidad.

## Autoridad

- Narrativa y lecciones: `docs/ROUTING_KNOWLEDGE_BASE.md`.
- Partición machine-readable: `hardware/routing_batches_contract.json`.
- Reglas eléctricas/cobre: `hardware/routing_contract.json`.
- Gate de consistencia: `tools/validate_routing_batches.py` + workflow `Routing incremental por lotes`.

## Estado del PR #19 experimental

Cerrado sin merge. Su rama se conserva como laboratorio/evidencia y no aporta cobre a `main`.
