#!/usr/bin/env python3
"""PR17 probe de la API pcbnew en KiCad 10.0.5.

No modifica archivos. Verifica carga, placement y asignación de nets en memoria
antes de materializar el PCB de producción.
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

    loaded = {}
    for ref, lib, name in CASES:
        libdir = LOCAL if lib == "NFB" else STD / f"{lib}.pretty"
        fp = pcbnew.FootprintLoad(str(libdir), name)
        if fp is None:
            raise SystemExit(f"no pudo cargar {lib}:{name}")
        loaded[ref] = fp
        pads = []
        for pad in fp.Pads():
            p = pad.GetPosition()
            pads.append((str(pad.GetNumber()), mm(p.x), mm(p.y)))
        print("PADS", ref, pads)

    for symbol in ("FootprintLoad", "LoadBoard", "SaveBoard", "NETINFO_ITEM", "VECTOR2I", "FromMM"):
        if not hasattr(pcbnew, symbol):
            raise SystemExit(f"pcbnew sin API requerida: {symbol}")

    # Ensayo in-memory de las operaciones exactas que usará el materializador PR17.
    fp = loaded["J_PWR_IN"]
    fp.SetReference("J_PROBE")
    fp.SetValue("PROBE")
    fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10.0), pcbnew.FromMM(5.0)))
    fp.SetOrientationDegrees(0.0)
    board.Add(fp)
    net = pcbnew.NETINFO_ITEM(board, "__PR17_PROBE_NET__")
    board.Add(net)
    first_pad = next(iter(fp.Pads()))
    first_pad.SetNet(net)
    print(
        "INMEMORY",
        fp.GetReference(),
        mm(fp.GetPosition().x),
        mm(fp.GetPosition().y),
        fp.GetOrientationDegrees(),
        str(first_pad.GetNumber()),
        first_pad.GetNetname(),
    )
    if first_pad.GetNetname() != "__PR17_PROBE_NET__":
        raise SystemExit("SetNet no preservó net de prueba")
    if len(list(board.GetTracks())) != 0:
        raise SystemExit("probe introdujo tracks inesperados")

    print("OK: pcbnew API disponible para placement+nets deterministas PR17")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
