#!/usr/bin/env python3
"""Normaliza la salida JSON/BOM→KiCad de PR15 sin alterar conectividad.

La fase raw (`generate_production_schematics.py`) ya valida JSON↔BOM y genera
símbolos/pines/nets de forma determinista. Esta capa realiza únicamente dos
normalizaciones EDA necesarias para KiCad:

1. Las etiquetas usadas dentro de cada child sheet son *local labels*, no
   global labels. La frontera entre hojas continúa siendo exclusivamente los
   hierarchical labels definidos por `root_eda_contract.json`.
2. Materializa una librería de proyecto `NFB_GEN` a partir de las mismas
   definiciones embebidas en los child sheets, evitando referencias a una
   librería inexistente sin inventar símbolos funcionales nuevos.

No cambia refs, valores, MPN, footprints, números de pin ni nombres de net.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KICAD = ROOT / "kicad"
GEN_LIB = KICAD / "lib" / "nfb_generated.kicad_sym"
RAW_GENERATOR = ROOT / "tools" / "generate_production_schematics.py"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def load_raw_generator():
    spec = importlib.util.spec_from_file_location("nfb_pr15_raw_generator", RAW_GENERATOR)
    if spec is None or spec.loader is None:
        fail("no se puede cargar generate_production_schematics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def balanced_block(text: str, start: int) -> tuple[str, int]:
    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:idx + 1], idx + 1
    fail("bloque S-expression sin cierre")


def top_generated_symbols(text: str) -> list[str]:
    marker = '(symbol "NFB_GEN:'
    symbols: list[str] = []
    cursor = 0
    while True:
        pos = text.find(marker, cursor)
        if pos < 0:
            break
        block, end = balanced_block(text, pos)
        # Los sub-symbols internos no llevan prefijo NFB_GEN, por lo que cada
        # match corresponde a una definición superior completa.
        symbols.append(block)
        cursor = end
    return symbols


def normalize_labels(text: str) -> str:
    # El generador raw usa global_label como mecanismo de unión dentro de una
    # hoja. En el hierarchy final esto es innecesario y genera contaminación de
    # alcance/same_local_global_label. Convertimos solo esos bloques.
    text = re.sub(
        r'(\(global_label\s+"[^"]+")\s+\(shape\s+input\)',
        r'\1',
        text,
    )
    text = text.replace('(global_label "', '(label "')
    return text


def normalize_child(text: str) -> str:
    normalized = normalize_labels(text)
    if '(global_label "' in normalized:
        fail("quedó global_label en child normalizado")
    return normalized


def build_generated_library(raw_outputs: dict[Path, str]) -> str:
    by_name: dict[str, str] = {}
    for text in raw_outputs.values():
        for block in top_generated_symbols(text):
            m = re.match(r'\(symbol\s+"NFB_GEN:([^"]+)"', block)
            if not m:
                fail("símbolo NFB_GEN sin nombre parseable")
            name = m.group(1)
            ext = block.replace(f'(symbol "NFB_GEN:{name}"', f'(symbol "{name}"', 1)
            previous = by_name.get(name)
            if previous is not None and previous != ext:
                fail(f"definición divergente para NFB_GEN:{name}")
            by_name[name] = ext
    if not by_name:
        fail("no se extrajeron símbolos generados")
    lines = [
        '(kicad_symbol_lib',
        '  (version 20231120)',
        '  (generator "nfb_pr15_normalizer")',
        '  (generator_version "1.0")',
    ]
    for name in sorted(by_name):
        block = by_name[name]
        lines.extend("  " + line if line else line for line in block.splitlines())
    lines.extend([')', ''])
    return "\n".join(lines)


def expected_outputs() -> dict[Path, str]:
    raw = load_raw_generator().rendered_outputs()
    expected = {path: normalize_child(text) for path, text in raw.items()}
    expected[GEN_LIB] = build_generated_library(raw)
    return expected


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    expected = expected_outputs()
    stale: list[Path] = []
    for path, content in expected.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            stale.append(path)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                print(f"wrote {path.relative_to(ROOT)}")

    if args.check and stale:
        for path in stale:
            print(f"STALE: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if args.check:
        print("OK: PR15 normalizado reproduce byte-for-byte desde JSON/BOM")
    elif not stale:
        print("OK: outputs PR15 ya normalizados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
