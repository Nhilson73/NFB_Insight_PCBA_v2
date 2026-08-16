#!/usr/bin/env python3
"""Probe read-only de endpoints y cobre para PR20A."""
from __future__ import annotations
import json
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
TARGET = [
    "12V_IN_RAW", "12V_PROTECTED", "12V_HOST_VIN", "12V_LOGIC", "12V_ACT",
    "5V_RAIL", "3V3_RAIL", "PUMP_OUT1", "PUMP_OUT2", "CO2_SOL_POS",
]
ZONES = {
    "Z0": (0.0, 53.34), "Z1": (53.34, 108.84), "Z2": (108.84, 163.34),
    "Z3": (163.34, 198.34), "Z4": (198.34, 242.34),
}

def mm(v: int) -> float:
    return round(pcbnew.ToMM(v), 3)

def zone_for_x(x: float) -> str:
    for name, (a, b) in ZONES.items():
        if a - 1e-6 <= x <= b + 1e-6:
            return name
    return "OUT"

def pad_layers(pad) -> list[str]:
    out=[]
    for lid, name in [(pcbnew.F_Cu,"F.Cu"),(pcbnew.In1_Cu,"In1.Cu"),(pcbnew.In2_Cu,"In2.Cu"),(pcbnew.B_Cu,"B.Cu")]:
        try:
            if pad.IsOnLayer(lid): out.append(name)
        except Exception:
            pass
    return out

def via_diameter_mm(via) -> float:
    try:
        return mm(via.GetWidth(pcbnew.F_Cu))
    except TypeError:
        return mm(via.GetWidth())

def main() -> int:
    b=pcbnew.LoadBoard(str(PCB))
    by={n:[] for n in TARGET}
    for fp in b.GetFootprints():
        ref=fp.GetReference()
        for p in fp.Pads():
            n=p.GetNetname()
            if n not in by: continue
            pos=p.GetPosition(); sz=p.GetSize()
            x,y=mm(pos.x),mm(pos.y)
            by[n].append({
                "ref":ref,"pad":p.GetNumber(),"x_mm":x,"y_mm":y,"zone":zone_for_x(x),
                "size_mm":[mm(sz.x),mm(sz.y)],"layers":pad_layers(p),"through_hole":bool(p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH),
            })
    for n in TARGET:
        by[n].sort(key=lambda d:(d["x_mm"],d["y_mm"],d["ref"],str(d["pad"])))

    copper={n:{"segments":0,"vias":0,"items":[]} for n in TARGET}
    layer_names={pcbnew.F_Cu:"F.Cu",pcbnew.In1_Cu:"In1.Cu",pcbnew.In2_Cu:"In2.Cu",pcbnew.B_Cu:"B.Cu"}
    for t in b.GetTracks():
        n=t.GetNetname()
        if n not in copper: continue
        pos=t.GetPosition()
        if isinstance(t, pcbnew.PCB_VIA):
            copper[n]["vias"]+=1
            copper[n]["items"].append({"kind":"via","x_mm":mm(pos.x),"y_mm":mm(pos.y),"diameter_mm":via_diameter_mm(t),"drill_mm":mm(t.GetDrillValue())})
        else:
            copper[n]["segments"]+=1
            s,e=t.GetStart(),t.GetEnd()
            copper[n]["items"].append({"kind":"segment","layer":layer_names.get(t.GetLayer(),str(t.GetLayer())),"start_mm":[mm(s.x),mm(s.y)],"end_mm":[mm(e.x),mm(e.y)],"width_mm":mm(t.GetWidth())})

    fps=[]
    for fp in b.GetFootprints():
        pos=fp.GetPosition(); x,y=mm(pos.x),mm(pos.y); z=zone_for_x(x)
        if z not in {"Z3","Z4"}: continue
        bb=fp.GetBoundingBox()
        fps.append({"ref":fp.GetReference(),"x_mm":x,"y_mm":y,"zone":z,"bbox_mm":[mm(bb.GetX()),mm(bb.GetY()),mm(bb.GetRight()),mm(bb.GetBottom())]})
    fps.sort(key=lambda d:(d["zone"],d["x_mm"],d["y_mm"],d["ref"]))

    vias=[]
    for t in b.GetTracks():
        if not isinstance(t,pcbnew.PCB_VIA): continue
        p=t.GetPosition(); x,y=mm(p.x),mm(p.y)
        if zone_for_x(x) in {"Z3","Z4"}:
            vias.append({"net":t.GetNetname(),"x_mm":x,"y_mm":y,"diameter_mm":via_diameter_mm(t),"drill_mm":mm(t.GetDrillValue())})
    vias.sort(key=lambda d:(d["x_mm"],d["y_mm"],d["net"]))

    out={"targets":by,"existing_target_copper":copper,"z3_z4_footprints":fps,"z3_z4_existing_vias":vias,
         "totals":{"tracks":sum(1 for t in b.GetTracks() if not isinstance(t,pcbnew.PCB_VIA)),"vias":sum(1 for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA)),"zones":len(b.Zones())}}
    print("PR20A_PROBE_BEGIN")
    print(json.dumps(out,sort_keys=True,separators=(",",":")))
    print("PR20A_PROBE_END")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
