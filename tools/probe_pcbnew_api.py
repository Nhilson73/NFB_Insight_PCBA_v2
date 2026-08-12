#!/usr/bin/env python3
"""PR17 probe de la API pcbnew en KiCad 10.0.5.

No modifica archivos. Verifica que la misma toolchain CI puede cargar el board y
footprints reales, y reporta orientación/pads de conectores de campo antes de
materializar placement.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
STD = Path("/usr/share/kicad/footprints")
LOCAL = ROOT / "kicad" / "lib" / "nfb_footprints.pretty"

CASES = [
    ("J_PH", "Connector_JST", "JST_XH_S3B-XH-A_1x03_P2.50mm_Horizontal"),
    ("J_GNSS_RTC", "Connector_JST", "JST_XH_S4B-XH-A_1x04_P2.50mm_Horizontal"),
    ("J_LOADCELL", "Connector_Phoenix_MSTB", "PhoenixContact_MSTBA_2,5_4-G-5,08_1x04_P5.08mm_Horizontal"),
    ("J_PWR_IN", "Connector_Phoenix_MSTB", "PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal"),
    ("U_CO2", "NFB", "Honeywell_MPR_LongPort_12Pad"),
]


def mm(v: int) -> float:
    return float(v) / 1_000_000.0


def main() -> int:
    import pcbnew  # type: ignore

    print("KICAD_BUILD", pcbnew.GetBuildVersion())
    board = pcbnew.LoadBoard(str(BOARD))
    print("BOARD_FOOTPRINTS", len(list(board.GetFootprints())))

    for ref, lib, name in CASES:
        libdir = LOCAL if lib == "NFB" else STD / f"{lib}.pretty"
        fp = pcbnew.FootprintLoad(str(libdir), name)
        if fp is None:
            raise SystemExit(f"no pudo cargar {lib}:{name}")
        bb = fp.GetBoundingBox()
        print(
            "CASE",
            ref,
            f"{lib}:{name}",
            "bbox_mm=",
            [mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetWidth()), mm(bb.GetHeight())],
        )
        pads = []
        for pad in fp.Pads():
            p = pad.GetPosition()
            pads.append((str(pad.GetNumber()), mm(p.x), mm(p.y)))
        print("PADS", ref, pads)

    # Confirmar que la API necesaria para PR17 existe sin alterar el board.
    for symbol in ("FootprintLoad", "LoadBoard", "SaveBoard", "NETINFO_ITEM"):
        if not hasattr(pcbnew, symbol):
            raise SystemExit(f"pcbnew sin API requerida: {symbol}")
    print("OK: pcbnew API disponible para materialización determinista PR17")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
