#!/usr/bin/env python3
"""PR19A v2: mismo lote, planificación conservadora contra pads/tracks/vías.

No cambia netclasses ni DRC. Aumenta únicamente la geometría de exclusión del
planificador para aproximar el ancho de pista + clearance físico antes de que
KiCad haga la verificación final.
"""
import materialize_pr19a_local as impl
import pr19a_router_core as base

# Grid 0.25 mm. El centro de una pista de 0.20 mm necesita típicamente
# ~0.30-0.40 mm respecto del bbox de un pad ajeno según la clase.
base.PAD_HALO = 0.35
impl.TURN_PENALTY = 2.50
impl.VIA_COST = 14.0


class RouterPR19AConservative(impl.RouterPR19A):
    def _mark_track(self, net, layer, cells, halo=2):
        # 2 celdas = 0.50 mm de exclusión de centro a centro entre rutas.
        return super()._mark_track(net, layer, cells, halo=2)

    def _mark_via(self, net, ix, iy, halo=3):
        # Vía mínima 0.60/0.30 mm; 0.75 mm de exclusión de planificación.
        return super()._mark_via(net, ix, iy, halo=3)


impl.RouterPR19A = RouterPR19AConservative

if __name__ == "__main__":
    raise SystemExit(impl.main())
