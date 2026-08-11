#!/usr/bin/env python3
"""Valida las invariantes mecánicas congeladas de NFB Insight PCBA v2."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"
FP = ROOT / "kicad" / "lib" / "nfb_footprints.pretty" / "Arduino_UNO_Q_Carrier_Rotated.kicad_mod"

EXPECTED_HOLES = {
    (50.80, 13.97),
    (45.72, 66.04),
    (17.78, 66.04),
    (2.54, 15.24),
}

EXPECTED_PADS = {
    "1": (50.80, 27.94),
    "14": (50.80, 63.50),
    "32": (2.54, 18.80),
    "15": (2.54, 63.50),
}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def near(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) <= tol


def main() -> int:
    if not PCB.exists() or not FP.exists():
        fail("faltan archivos mecánicos KiCad")

    pcb = PCB.read_text(encoding="utf-8")
    fp = FP.read_text(encoding="utf-8")

    # Altura fija y ancho provisional del Edge.Cuts.
    required_edges = [
        r"\(gr_line \(start 0 0\) \(end 220 0\).*\(layer \"Edge.Cuts\"\)",
        r"\(gr_line \(start 220 0\) \(end 220 68\.58\).*\(layer \"Edge.Cuts\"\)",
        r"\(gr_line \(start 220 68\.58\) \(end 0 68\.58\).*\(layer \"Edge.Cuts\"\)",
        r"\(gr_line \(start 0 68\.58\) \(end 0 0\).*\(layer \"Edge.Cuts\"\)",
    ]
    for pattern in required_edges:
        if not re.search(pattern, pcb):
            fail(f"Edge.Cuts esperado no encontrado: {pattern}")

    if "FIELD I/O EDGE" not in pcb:
        fail("falta la identificación FIELD I/O EDGE")
    if "USB-C -> -Y" not in fp and "USB-C → -Y" not in pcb:
        fail("falta la orientación USB-C hacia -Y")

    # Patrón de agujeros inmutable.
    holes = {
        (float(x), float(y))
        for x, y in re.findall(
            r'\(pad \"\" np_thru_hole circle \(at ([0-9.]+) ([0-9.]+)\)', fp
        )
    }
    for expected in EXPECTED_HOLES:
        if not any(near(expected[0], x) and near(expected[1], y) for x, y in holes):
            fail(f"agujero UNO Q ausente o movido: {expected}")

    # Puntos extremos del patrón de headers.
    found_pads = {
        n: (float(x), float(y))
        for n, x, y in re.findall(
            r'\(pad \"([0-9]+)\" thru_hole \w+ \(at ([0-9.]+) ([0-9.]+)\)', fp
        )
    }
    for number, expected in EXPECTED_PADS.items():
        actual = found_pads.get(number)
        if actual is None or not (near(actual[0], expected[0]) and near(actual[1], expected[1])):
            fail(f"pad {number} fuera de posición: esperado {expected}, actual {actual}")

    # Las zonas son guías, no dimensiones congeladas salvo Z0.
    for label in [
        "Z0 UNO Q INMUTABLE",
        "Z1 ANALÓGICO / AISLAMIENTO",
        "Z2 DIGITAL / BAJO RUIDO",
        "Z3 POTENCIA",
        "Z4 ACTUADORES",
    ]:
        if label not in pcb:
            fail(f"falta guía funcional: {label}")

    # Referencias mecánicas conservadoras heredadas y rotadas.
    for label in [
        "EXCLUSIÓN USB-C / PMIC",
        "EXCLUSIÓN JCTL",
        "EXCLUSIÓN SPI2 / JSPI",
        "EXCLUSIÓN QWIIC",
    ]:
        if label not in pcb:
            fail(f"falta referencia mecánica: {label}")

    print("OK: invariantes mecánicas V2 verificadas")
    print("- origen global UNO Q: (0,0)")
    print("- envolvente UNO Q rotada: 53.34 x 68.58 mm")
    print("- altura board congelada: 68.58 mm")
    print("- ancho actual: 220 mm (PROVISIONAL)")
    print("- USB-C orientado hacia -Y")
    print("- 4 agujeros y extremos de headers verificados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
