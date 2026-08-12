#!/usr/bin/env python3
"""Migra únicamente footprints PR15 verificados contra fuente primaria.

No modifica MPN ni conectividad. Para cada referencia exige el footprint legacy
esperado antes de reemplazarlo; si aparece un valor distinto, falla para evitar
cambios silenciosos.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TXU_OLD = "Package_MSOP:VSSOP-8_2x3.1mm_P0.65mm"
TXU_NEW = "NFB:TI_DCU0008A_TXU0202"
PHX_OLD = "TerminalBlock_Phoenix:PhoenixContact_MSTBA-G_02x5.08mm_Angled"
PHX_NEW = "Connector_Phoenix_MSTB:PhoenixContact_MSTBA_2,5_2-G-5,08_1x02_P5.08mm_Horizontal"

JSON_TARGETS = {
    ROOT / "hardware" / "z2_production_netlist.json": {
        "U_HMI_LVL": (TXU_OLD, TXU_NEW),
    },
    ROOT / "hardware" / "power_production_netlist.json": {
        "J_PWR_IN": (PHX_OLD, PHX_NEW),
    },
    ROOT / "hardware" / "z4_production_netlist.json": {
        "J_PUMP": (PHX_OLD, PHX_NEW),
        "J_CO2_SOL": (PHX_OLD, PHX_NEW),
        "J_CHILLER_CTL": (PHX_OLD, PHX_NEW),
    },
}

CSV_TARGETS = {
    ROOT / "bom" / "insight_z2_production_bom.csv": {
        "U_HMI_LVL": (TXU_OLD, TXU_NEW),
    },
    ROOT / "bom" / "insight_power_production_bom.csv": {
        "J_PWR_IN": (PHX_OLD, PHX_NEW),
    },
    ROOT / "bom" / "insight_z4_production_bom.csv": {
        "J_PUMP": (PHX_OLD, PHX_NEW),
        "J_CO2_SOL": (PHX_OLD, PHX_NEW),
        "J_CHILLER_CTL": (PHX_OLD, PHX_NEW),
    },
}


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def migrate_json(path: Path, mapping: dict[str, tuple[str, str]]) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    by_ref = {c["ref"]: c for c in data.get("components", [])}
    for ref, (old, new) in mapping.items():
        if ref not in by_ref:
            fail(f"{path.name}: falta {ref}")
        current = by_ref[ref].get("footprint")
        if current == new:
            continue
        if current != old:
            fail(f"{path.name}:{ref} footprint inesperado: {current!r}")
        by_ref[ref]["footprint"] = new
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"


def migrate_csv(path: Path, mapping: dict[str, tuple[str, str]]) -> str:
    text = path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or "ref" not in reader.fieldnames or "footprint" not in reader.fieldnames:
        fail(f"{path.name}: columnas BOM inválidas")
    rows = list(reader)
    seen = set()
    for row in rows:
        ref = row["ref"]
        if ref not in mapping:
            continue
        seen.add(ref)
        old, new = mapping[ref]
        current = row["footprint"]
        if current == new:
            continue
        if current != old:
            fail(f"{path.name}:{ref} footprint inesperado: {current!r}")
        row["footprint"] = new
    missing = set(mapping) - seen
    if missing:
        fail(f"{path.name}: faltan refs {sorted(missing)}")
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def expected() -> dict[Path, str]:
    result: dict[Path, str] = {}
    for path, mapping in JSON_TARGETS.items():
        result[path] = migrate_json(path, mapping)
    for path, mapping in CSV_TARGETS.items():
        result[path] = migrate_csv(path, mapping)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stale = []
    for path, content in expected().items():
        current = path.read_text(encoding="utf-8")
        if current != content:
            stale.append(path)
            if not args.check:
                path.write_text(content, encoding="utf-8")
                print(f"updated {path.relative_to(ROOT)}")
    if args.check and stale:
        for path in stale:
            print(f"STALE: {path.relative_to(ROOT)}")
        return 1
    if args.check:
        print("OK: footprints PR15 verificados ya migrados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
