#!/usr/bin/env python3
"""Wrapper PR19: reduce solo el halo heurístico del router.

No cambia clearances KiCad ni el contrato eléctrico. El DRC real sigue siendo la
autoridad; este ajuste evita que la rejilla A* trate el espacio legal entre pads
finos como un obstáculo geométrico imposible.
"""
import materialize_pr19_routing as router

router.PAD_HALO = 0.05

if __name__ == "__main__":
    raise SystemExit(router.main())
