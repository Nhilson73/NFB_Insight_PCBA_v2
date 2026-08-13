#!/usr/bin/env python3
"""Retira cobre de una copia de trabajo del PCB para gates históricos PR13-PR17.

Uso exclusivo en CI. Modifica el archivo de trabajo local, nunca hace commit.
El PCB persistido de producción se valida por separado mediante PR19A.
"""
from __future__ import annotations

from pathlib import Path
import pcbnew  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"


def main() -> int:
    board = pcbnew.LoadBoard(str(PCB))
    tracks = list(board.GetTracks())
    zones = list(board.Zones())
    for item in tracks:
        board.Remove(item)
    for zone in zones:
        board.Remove(zone)
    pcbnew.SaveBoard(str(PCB), board)
    check = pcbnew.LoadBoard(str(PCB))
    if len(list(check.GetTracks())) != 0 or len(list(check.Zones())) != 0:
        raise SystemExit("ERROR: vista placement-only conserva cobre")
    print(f"OK: vista efímera placement-only; removidos items={len(tracks)} zones={len(zones)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
