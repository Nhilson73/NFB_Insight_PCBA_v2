#!/usr/bin/env python3
"""Materializa el PCB de placement PR17 desde el manifest XY y contratos JSON.

Parte siempre del board mergeado por PR16, expande únicamente +X, añade nets y
footprints de producción, y conserva routing=0. Requiere git history disponible.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PCB_REL = Path("kicad/NFB_Insight_PCBA_v2.kicad_pcb")
PCB = ROOT / PCB_REL
MANIFEST = ROOT / "hardware" / "placement_manifest.json"
PIN = ROOT / "hardware" / "insight_pin_contract.json"
ZONE_FILES = [
    ROOT / "hardware" / "z1_production_netlist.json",
    ROOT / "hardware" / "z2_production_netlist.json",
    ROOT / "hardware" / "power_production_netlist.json",
    ROOT / "hardware" / "z4_production_netlist.json",
]
STD = Path("/usr/share/kicad/footprints")
LOCAL = ROOT / "kicad" / "lib" / "nfb_footprints.pretty"
PR16_BASE_SHA = "898c98ac985b2861adfb4cc5cc0f372c5d648b84"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def set_fpid(fp, lib: str, name: str) -> None:
    """Preserva explícitamente nickname:item en el footprint serializado por pcbnew."""
    try:
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
    except TypeError:
        fid = pcbnew.LIB_ID()
        if hasattr(fid, "SetLibNickname") and hasattr(fid, "SetLibItemName"):
            fid.SetLibNickname(lib)
            fid.SetLibItemName(name)
            fp.SetFPID(fid)
        else:
            fail(f"KiCad no permite fijar LIB_ID explícito para {lib}:{name}")


def load_fp(fid: str):
    lib, name = fid.split(":", 1)
    libdir = LOCAL if lib == "NFB" else STD / f"{lib}.pretty"
    fp = pcbnew.FootprintLoad(str(libdir), name)
    if fp is None:
        fail(f"no pudo cargar footprint {fid}")
    set_fpid(fp, lib, name)
    return fp


def replace_one(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"base PR16: marcador {label} aparece {count} veces")
    return text.replace(old, new)


def base_board_text(manifest: dict) -> str:
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{PR16_BASE_SHA}:{PCB_REL.as_posix()}"],
            cwd=ROOT,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        fail(f"no pudo leer board base PR16 {PR16_BASE_SHA}: {exc}")

    width = float(manifest["board"]["width_mm"])
    bounds = manifest["zone_bounds_mm"]
    z1r = float(bounds["Z1"]["x_max"])
    z2r = float(bounds["Z2"]["x_max"])
    z3r = float(bounds["Z3"]["x_max"])
    centers = {
        "Z1": (float(bounds["Z1"]["x_min"]) + z1r) / 2,
        "Z2": (float(bounds["Z2"]["x_min"]) + z2r) / 2,
        "Z3": (float(bounds["Z3"]["x_min"]) + z3r) / 2,
        "Z4": (float(bounds["Z4"]["x_min"]) + float(bounds["Z4"]["x_max"])) / 2,
    }
    mid = width / 2

    raw = replace_one(raw, "(gr_line (start 0 0) (end 220 0)", f"(gr_line (start 0 0) (end {width:g} 0)", "Edge bottom")
    raw = replace_one(raw, "(gr_line (start 220 0) (end 220 68.58)", f"(gr_line (start {width:g} 0) (end {width:g} 68.58)", "Edge right")
    raw = replace_one(raw, "(gr_line (start 220 68.58) (end 0 68.58)", f"(gr_line (start {width:g} 68.58) (end 0 68.58)", "Edge top")

    raw = replace_one(raw, "(gr_line (start 105 0) (end 105 68.58)", f"(gr_line (start {z1r:g} 0) (end {z1r:g} 68.58)", "Z1/Z2")
    raw = replace_one(raw, "(gr_line (start 145 0) (end 145 68.58)", f"(gr_line (start {z2r:g} 0) (end {z2r:g} 68.58)", "Z2/Z3")
    raw = replace_one(raw, "(gr_line (start 180 0) (end 180 68.58)", f"(gr_line (start {z3r:g} 0) (end {z3r:g} 68.58)", "Z3/Z4")

    raw = replace_one(raw, '(gr_text "Z1 ANALÓGICO / AISLAMIENTO" (at 79.17 34.29 90)', f'(gr_text "Z1 ANALÓGICO / AISLAMIENTO" (at {centers["Z1"]:g} 34.29 90)', "label Z1")
    raw = replace_one(raw, '(gr_text "Z2 DIGITAL / BAJO RUIDO" (at 125 34.29 90)', f'(gr_text "Z2 DIGITAL / BAJO RUIDO" (at {centers["Z2"]:g} 34.29 90)', "label Z2")
    raw = replace_one(raw, '(gr_text "Z3 POTENCIA" (at 162.5 34.29 90)', f'(gr_text "Z3 POTENCIA" (at {centers["Z3"]:g} 34.29 90)', "label Z3")
    raw = replace_one(raw, '(gr_text "Z4 ACTUADORES" (at 200 34.29 90)', f'(gr_text "Z4 ACTUADORES" (at {centers["Z4"]:g} 34.29 90)', "label Z4")
    raw = replace_one(raw, '(gr_text "FIELD I/O EDGE — conectores orientados hacia -Y" (at 130 2 0)', f'(gr_text "FIELD I/O EDGE — conectores orientados hacia -Y" (at {mid:g} 2 0)', "field label")
    raw = replace_one(raw, '(gr_text "ANCHO 220 mm PROVISIONAL — congelar después del placement" (at 130 66 0)', f'(gr_text "ANCHO {width:g} mm — PLACEMENT PR17 / ROUTING PENDIENTE" (at {mid:g} 66 0)', "width label")
    return raw


def component_map() -> dict[str, dict]:
    result = {}
    for path in ZONE_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for comp in data["components"]:
            if comp["ref"] in result:
                fail(f"ref duplicada: {comp['ref']}")
            result[comp["ref"]] = comp
    return result


def main() -> int:
    if not MANIFEST.exists():
        fail("falta hardware/placement_manifest.json; ejecutar generador PR17")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "PRODUCTION_PLACEMENT_PR17":
        fail("manifest no es PR17")
    if manifest["policies"].get("routing_allowed") is not False:
        fail("manifest intenta habilitar routing")

    comps = component_map()
    placements = {p["ref"]: p for p in manifest["placements"]}
    if set(comps) != set(placements):
        fail(f"refs manifest/netlists divergen: missing={sorted(set(comps)-set(placements))[:10]} extra={sorted(set(placements)-set(comps))[:10]}")

    tmp = Path("/tmp/nfb_pr17_base.kicad_pcb")
    tmp.write_text(base_board_text(manifest), encoding="utf-8")
    board = pcbnew.LoadBoard(str(tmp))
    fps0 = list(board.GetFootprints())
    if len(fps0) != 1 or fps0[0].GetReference() != "J_UNOQ":
        fail("board base PR16 no contiene exactamente J_UNOQ")

    pin_contract = json.loads(PIN.read_text(encoding="utf-8"))
    netnames = {p["net"] for p in pin_contract["pins"] if p.get("net")}
    for comp in comps.values():
        netnames.update(n for n in comp["pins"].values() if n and n != "NC")
    nets = {}
    for name in sorted(netnames):
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
        nets[name] = item

    host = fps0[0]
    host_map = {str(p["pad"]): p.get("net") for p in pin_contract["pins"]}
    for pad in host.Pads():
        num = str(pad.GetNumber())
        name = host_map.get(num)
        if name:
            pad.SetNet(nets[name])

    for ref in sorted(comps):
        comp = comps[ref]
        p = placements[ref]
        if comp["footprint"] != p["footprint"]:
            fail(f"{ref}: footprint manifest != JSON")
        fp = load_fp(comp["footprint"])
        fp.SetReference(ref)
        fp.SetValue(str(comp.get("value", "")))
        fp.SetPosition(
            pcbnew.VECTOR2I(
                pcbnew.FromMM(float(p["x_mm"])),
                pcbnew.FromMM(float(p["y_mm"])),
            )
        )
        fp.SetOrientationDegrees(float(p.get("rotation_deg", 0.0)))
        pinmap = {str(k): v for k, v in comp["pins"].items()}
        numbered_seen = set()
        for pad in fp.Pads():
            num = str(pad.GetNumber())
            if not num:
                continue
            numbered_seen.add(num)
            if num not in pinmap:
                fail(f"{ref}: pad {num} existe en footprint pero no en JSON pins")
            netname = pinmap[num]
            if netname and netname != "NC":
                pad.SetNet(nets[netname])
        missing_pins = set(pinmap) - numbered_seen
        if missing_pins:
            fail(f"{ref}: pins JSON sin pad físico {sorted(missing_pins)}")
        board.Add(fp)

    if len(list(board.GetTracks())) != 0:
        fail("PR17 no permite tracks/vias")
    try:
        if len(list(board.Zones())) != 0:
            fail("PR17 no permite copper zones")
    except AttributeError:
        pass

    pcbnew.SaveBoard(str(PCB), board)
    print(f"WROTE {PCB_REL} footprints={len(list(board.GetFootprints()))} nets={len(nets)} tracks=0")

    if "--check" in sys.argv:
        generated = PCB.read_bytes()
        existing = subprocess.check_output(["git", "show", f"HEAD:{PCB_REL.as_posix()}"], cwd=ROOT)
        if generated != existing:
            fail("PCB PR17 no reproduce byte-for-byte desde manifest/PR16 base")
        print("OK: PCB PR17 reproducible byte-for-byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
