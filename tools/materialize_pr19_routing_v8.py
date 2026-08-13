#!/usr/bin/env python3
"""PR19 v8: v7 + diagnóstico local CO2 antes de PUMP_CURRENT_ADC/analógico largo."""
import pcbnew  # type: ignore
import materialize_pr19_routing as base

base.STEP = 0.25
base.PAD_HALO = 0.05
base.MAX_EXPANSIONS = 900_000

CONTROL_ORDER = [
    "5V_VCC", "5V_FB", "UNO_IOREF_3V3", "5V_PGOOD",
    "EFUSE_ILM", "EFUSE_ITIMER", "EFUSE_DVDT", "EFUSE_EN_UVLO", "EFUSE_OVLO",
    "CO2_ILIM", "PUMP_SR_CFG",
]
CONTROL_RANK = {n: i for i, n in enumerate(CONTROL_ORDER)}
EARLY_Z4_DIGITAL = ["CO2_OPENLOAD_N", "CO2_EN_DRV"]
EARLY_RANK = {n: i for i, n in enumerate(EARLY_Z4_DIGITAL)}
DIGITAL_LOCAL_ORDER = [
    "PUMP_DIR_DRV", "PUMP_PWM_DRV",
    "CHILLER_GATE", "CHILLER_LED_A", "CHILLER_LED_K",
    "HMI_FIELD_RX", "HMI_FIELD_TX", "WDT_MR_N",
]
DIGITAL_RANK = {n: i for i, n in enumerate(DIGITAL_LOCAL_ORDER)}


class RouterV8(base.Router):
    def _astar(self, net, cls, start_ep, goal_ep, xmin, xmax):
        original = base.allowed_layers
        if net == "UNO_IOREF_3V3":
            def layers(c):
                if c == "CONTROL_SENSITIVE":
                    return [pcbnew.B_Cu, pcbnew.F_Cu]
                return original(c)
            base.allowed_layers = layers
        try:
            return super()._astar(net, cls, start_ep, goal_ep, xmin, xmax)
        finally:
            base.allowed_layers = original

    def route(self) -> dict:
        routes_by_net = {r["net"]: r for r in self.probe["routes"]}
        to_route, deferred = [], []
        for net, cls in sorted(self.by_net.items()):
            if cls in base.ROUTE_CLASSES:
                to_route.append(net)
            elif cls in base.DEFER_CLASSES:
                deferred.append(net)
            else:
                base.fail(f"clase sin política PR19: {cls}")

        def key(net):
            cls = self.by_net[net]
            local = routes_by_net[net]["mode"].startswith("LOCAL")
            if cls == "FIELD_ANALOG_LOCAL": return (0, 0, net)
            if cls == "CONTROL_SENSITIVE": return (1, CONTROL_RANK.get(net, 1000), net)
            if net in EARLY_RANK: return (2, EARLY_RANK[net], net)
            if cls == "ANALOG_SENSITIVE": return (3, 0 if local else 1, net)
            if cls == "CHILLER_DRY_CONTACT": return (4, 0, net)
            if cls == "DIGITAL_LOW_SPEED" and local:
                return (5, DIGITAL_RANK.get(net, 1000), net)
            return (6, 0, net)
        to_route.sort(key=key)

        net_stats=[]
        for net in to_route:
            cls=self.by_net[net]; clsinfo=self.by_class[cls]; route=routes_by_net[net]
            eps=self.pads_by_net.get(net,[])
            if len(eps)!=int(route["endpoint_count"]):
                base.fail(f"{net}: endpoints board/probe divergen {len(eps)} != {route['endpoint_count']}")
            eps.sort(key=lambda e:(e["ref"],e["pad"],round(e["x_mm"],4),round(e["y_mm"],4)))
            xmin,xmax=base.route_bounds(route,self.placement); edges=base.mst_edges(eps)
            bs,bv=len(self.segments),len(self.vias)
            for i,j in edges:
                path=self._astar(net,cls,eps[i],eps[j],xmin,xmax)
                self._materialize_path(net,cls,clsinfo,path,eps[i],eps[j])
            net_stats.append({"net":net,"class":cls,"mode":route["mode"],"edge_count":len(edges),"segment_count":len(self.segments)-bs,"via_count":len(self.vias)-bv})
            print("ROUTED",net,cls,route["mode"],"edges",len(edges),"segments",len(self.segments)-bs,"vias",len(self.vias)-bv)

        return {"schema_version":1,"status":"SIGNAL_ROUTING_PR19","scope":"SIGNALS_CONTROL_ONLY_POWER_GND_DEFERRED_PR20","grid_mm":base.STEP,"board_mm":[self.width,self.height],"routed_classes":sorted(base.ROUTE_CLASSES),"deferred_classes":sorted(base.DEFER_CLASSES),"routed_nets":to_route,"deferred_nets":deferred,"net_stats":net_stats,"segments":self.segments,"vias":self.vias,"long_haul_exceptions":{"UNO_IOREF_3V3":"B.Cu trunk permitted by PR18 layer policy; local feedback/programming remain F.Cu"}}

base.Router=RouterV8
if __name__=="__main__": raise SystemExit(base.main())
