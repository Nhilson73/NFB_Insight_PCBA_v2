# Checkpoint de gobernanza de routing

Este checkpoint existe para asegurar que la metodología incremental esté mergeada en `main` antes de volver a materializar cobre.

Condiciones:

- PR #19 experimental cerrado sin merge.
- Partición congelada: `28 + 4 + 16 + 10 + 1 = 59`.
- Política de merge: `ALL_OR_NOTHING` por lote.
- Base de conocimiento: `docs/ROUTING_KNOWLEDGE_BASE.md`.
- Contrato: `hardware/routing_batches_contract.json`.
- Gate CI: `tools/validate_routing_batches.py`.

El siguiente branch de routing debe nacer del `main` que contenga este checkpoint.
