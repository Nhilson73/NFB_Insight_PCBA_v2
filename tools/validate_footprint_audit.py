#!/usr/bin/env python3
"""Valida el gate de footprints antes de autorizar placement."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "hardware" / "footprint_audit.json"
MPR = ROOT / "kicad" / "lib" / "nfb_footprints.pretty" / "Honeywell_MPR_LongPort_12Pad.kicad_mod"
POWER = ROOT / "hardware" / "power_production_netlist.json"
Z1 = ROOT / "hardware" / "z1_production_netlist.json"
PCB = ROOT / "kicad" / "NFB_Insight_PCBA_v2.kicad_pcb"


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tol


def main() -> int:
    for path in (AUDIT, MPR, POWER, Z1, PCB):
        if not path.exists():
            fail(f"falta {path.relative_to(ROOT)}")

    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    if audit.get("status") != "FOOTPRINT_AUDIT_BASELINE_PR11":
        fail("audit baseline no es PR11")
    if audit.get("policy", {}).get("do_not_invent_land_patterns") is not True:
        fail("debe permanecer activa la política de no inventar land patterns")

    by_id = {x["id"]: x for x in audit["audits"]}
    required = {"UNO_Q_CARRIER_ROTATED", "MPR_LONG_PORT_12PAD", "TPS25947_RPW0010A", "TPSM33625_RDN11"}
    if set(by_id) != required:
        fail(f"conjunto de auditorías inesperado: {set(by_id)}")

    mpr_a = by_id["MPR_LONG_PORT_12PAD"]
    if mpr_a["status"] != "CLOSED_PRIMARY_DATASHEET" or not mpr_a["placement_allowed"]:
        fail("MPR debe quedar cerrado contra datasheet Honeywell")
    if "32332628" not in mpr_a["source"] or "Issue L" not in mpr_a["source"]:
        fail("fuente Honeywell MPR no está trazada a 32332628 Issue L")
    g = mpr_a["verified_geometry"]
    if g["pad_count"] != 12 or not close(g["pitch_mm"], 1.27) or not close(g["recommended_layout_outer_span_mm"], 4.20):
        fail("geometría contractual MPR incorrecta")

    text = MPR.read_text(encoding="utf-8")
    pads = re.findall(r'\(pad\s+"(\d+)"\s+smd\s+rect\s+\(at\s+([-0-9.]+)\s+([-0-9.]+)\)\s+\(size\s+([-0-9.]+)\s+([-0-9.]+)\)', text)
    if len(pads) != 12 or {int(p[0]) for p in pads} != set(range(1, 13)):
        fail("footprint MPR no contiene pads 1..12 exactamente una vez")
    data = {int(n): tuple(map(float, (x, y, sx, sy))) for n, x, y, sx, sy in pads}
    expected = {
        1:(1.27,1.775,0.70,0.65),2:(0,1.775,0.70,0.65),3:(-1.27,1.775,0.70,0.65),
        4:(1.775,1.27,0.65,0.70),5:(1.775,0,0.65,0.70),6:(1.775,-1.27,0.65,0.70),
        7:(-1.27,-1.775,0.70,0.65),8:(0,-1.775,0.70,0.65),9:(1.27,-1.775,0.70,0.65),
        10:(-1.775,-1.27,0.65,0.70),11:(-1.775,0,0.65,0.70),12:(-1.775,1.27,0.65,0.70),
    }
    for n, exp in expected.items():
        if any(not close(a, b) for a, b in zip(data[n], exp)):
            fail(f"pad MPR {n} difiere de baseline Honeywell PR11: {data[n]} != {exp}")
    if "ISSUE L FIG.10" not in text:
        fail("footprint MPR no conserva trazabilidad gráfica Issue L Fig.10")

    z1 = json.loads(Z1.read_text(encoding="utf-8"))
    uco2 = next(x for x in z1["components"] if x["ref"] == "U_CO2")
    if uco2["footprint"] != "NFB:Honeywell_MPR_LongPort_12Pad":
        fail("Z1 no usa footprint MPR auditado")

    power = json.loads(POWER.read_text(encoding="utf-8"))
    comps = {x["ref"]: x for x in power["components"]}
    for ref, audit_id in (("U_EFUSE", "TPS25947_RPW0010A"), ("U_5V", "TPSM33625_RDN11")):
        a = by_id[audit_id]
        if a["placement_allowed"] is not False:
            fail(f"{ref} no debe estar autorizado todavía")
        if comps[ref]["footprint"] != "PENDING_DATASHEET_AUDIT_BEFORE_PLACEMENT":
            fail(f"{ref} obtuvo footprint sin cerrar auditoría")

    pcb = PCB.read_text(encoding="utf-8")
    forbidden_placed = [ref for ref in ("U_EFUSE", "U_5V") if f'"{ref}"' in pcb]
    if forbidden_placed:
        fail(f"placement prematuro con footprint abierto: {forbidden_placed}")

    rpw = by_id["TPS25947_RPW0010A"]
    if rpw["status"] != "PRIMARY_DRAWING_REVIEWED_CAD_IMPORT_PENDING" or rpw["placement_allowed"]:
        fail("RPW0010A debe seguir bloqueado hasta cierre de CAD/land pattern")
    if rpw["verified_geometry"]["pin_count"] != 10 or rpw["verified_geometry"]["pitch_mm"] != 0.45:
        fail("metadata RPW0010A incorrecta")

    rdn = by_id["TPSM33625_RDN11"]
    if rdn["status"] != "BLOCKED_VENDOR_CAD_VERIFICATION" or rdn["placement_allowed"]:
        fail("RDN-11 debe seguir bloqueado")
    if rdn["verified_geometry"]["pin_count"] != 11 or rdn["verified_geometry"]["body_mm"] != [4.5, 3.5]:
        fail("metadata RDN-11 incorrecta")

    print("OK: auditoría de footprints PR #11")
    print("- MPR Honeywell Issue L: CLOSED y footprint verificado")
    print("- TPS25947 RPW0010A: drawing primario revisado, placement bloqueado")
    print("- TPSM33625 RDN-11: CAD vendor pendiente, placement bloqueado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
