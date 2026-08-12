#!/usr/bin/env python3
"""Valida coherencia cruzada Z1 + Z2 + potencia + contrato UNO Q."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "integration": ROOT / "hardware" / "electrical_integration_contract.json",
    "pins": ROOT / "hardware" / "insight_pin_contract.json",
    "z1": ROOT / "hardware" / "z1_production_netlist.json",
    "z2": ROOT / "hardware" / "z2_production_netlist.json",
    "power": ROOT / "hardware" / "power_production_netlist.json",
    "audit": ROOT / "hardware" / "footprint_audit.json",
    "sch": ROOT / "kicad" / "integration_contract.kicad_sch",
}


def fail(msg: str) -> None:
    raise SystemExit("ERROR: " + msg)


def netmap(netlist: dict) -> dict[str, set[str]]:
    return {n["name"]: set(n["nodes"]) for n in netlist["nets"]}


def compmap(netlist: dict) -> dict[str, dict]:
    return {c["ref"]: c for c in netlist["components"]}


def main() -> int:
    for path in FILES.values():
        if not path.exists():
            fail(f"falta {path.relative_to(ROOT)}")
    ic = json.loads(FILES["integration"].read_text(encoding="utf-8"))
    pins = json.loads(FILES["pins"].read_text(encoding="utf-8"))
    z1 = json.loads(FILES["z1"].read_text(encoding="utf-8"))
    z2 = json.loads(FILES["z2"].read_text(encoding="utf-8"))
    power = json.loads(FILES["power"].read_text(encoding="utf-8"))
    audit = json.loads(FILES["audit"].read_text(encoding="utf-8"))

    if ic.get("status") != "ELECTRICAL_INTEGRATION_BASELINE_PR11":
        fail("contrato de integración no es PR11")
    if ic["scope"].get("placement") or ic["scope"].get("routing") or ic["scope"].get("actuators"):
        fail("PR11 no debe habilitar placement/routing/actuadores")
    if audit.get("status") != "FOOTPRINT_AUDIT_BASELINE_PR11":
        fail("integración no enlaza audit PR11")

    pby = {int(p["pad"]): p for p in pins["pins"]}
    expected_pins = {
        2:"UNO_IOREF_3V3",8:"12V_HOST_VIN",9:"PH_ADC",10:"ORP_ADC",11:"TEMP_1WIRE",14:"DO_ADC",
        15:"HMI_RX",16:"HMI_TX",17:"HX711_DOUT",18:"HX711_SCK",19:"MCU_WDI",28:"LED_STATUS",31:"I2C_SDA",32:"I2C_SCL"
    }
    for pad, net in expected_pins.items():
        if pby[pad].get("net") != net:
            fail(f"J_UNOQ pad {pad} perdió {net}")
    for pad in (4, 5, 12, 13, 24):
        if pby[pad].get("net") is not None:
            fail(f"pad UNO Q {pad} no debe ganar net activa en PR11")

    n1, n2, np = netmap(z1), netmap(z2), netmap(power)
    for net in ("GND", "3V3_RAIL", "5V_RAIL"):
        if net not in n1 or net not in n2 or net not in np:
            fail(f"net compartida {net} no existe en Z1/Z2/power")
    for net in ("I2C_SDA", "I2C_SCL"):
        if net not in n1 or net not in n2:
            fail(f"bus {net} no está compartido Z1/Z2")

    if "J_UNOQ.4" in n1["3V3_RAIL"] | n2["3V3_RAIL"] | np["3V3_RAIL"]:
        fail("back-feed: J_UNOQ.4 apareció en 3V3_RAIL")
    if "J_UNOQ.5" in n1["5V_RAIL"] | n2["5V_RAIL"] | np["5V_RAIL"]:
        fail("back-feed: J_UNOQ.5 apareció en 5V_RAIL")

    cp = compmap(power)
    if cp["U_5V"]["pins"].get("4") != "5V_RAIL" or cp["U_3V3"]["pins"].get("5") != "3V3_RAIL":
        fail("productores locales de 5V/3V3 cambiaron")
    if cp["U_5V"]["pins"].get("2") != "UNO_IOREF_3V3":
        fail("enable U_5V dejó de venir de UNO_IOREF_3V3")
    if cp["U_3V3"]["pins"].get("3") != "5V_PGOOD":
        fail("enable U_3V3 dejó de venir de 5V_PGOOD")
    if "12V_HOST_VIN" not in np:
        fail("power netlist perdió 12V_HOST_VIN")

    # Ownership: solo I2C puede estar declarado simultáneamente en Z1 y Z2 con endpoints del UNO Q.
    z1_uno = set(z1["uno_q_interface"]["sensor_endpoints"].values()) - {None}
    z2_uno = set(z2["uno_q_interface"]["endpoints"].values())
    overlap = z1_uno & z2_uno
    if overlap != {"I2C_SDA", "I2C_SCL"}:
        fail(f"colisión de ownership Z1/Z2 inesperada: {overlap}")

    # I2C final: MPR 0x28 y DFR1103 0x66 solamente como devices activos de baseline.
    addresses = {x["address"].lower(): x["device"] for x in ic["i2c_address_map"]}
    if addresses != {"0x28":"MPRLS0030PA00002A", "0x66":"DFR1103"}:
        fail(f"mapa I2C de integración inesperado: {addresses}")
    if "U_CO2.2" not in n1["I2C_SDA"] or "U_CO2.3" not in n1["I2C_SCL"]:
        fail("MPR no está en el bus I2C Z1")
    if "J_GNSS_RTC.1" not in n2["I2C_SDA"] or "J_GNSS_RTC.2" not in n2["I2C_SCL"]:
        fail("DFR1103 connector no está en el bus I2C Z2")

    prohib = " ".join(ic["hard_prohibitions"])
    for marker in ("J_UNOQ.4", "J_UNOQ.5", "CO2_ADC", "A3", "D9", "placement", "routing"):
        if marker not in prohib:
            fail(f"hard_prohibitions sin {marker}")

    sch = FILES["sch"].read_text(encoding="utf-8")
    for marker in ("PR #11", "J_UNOQ.4 NO conecta", "J_UNOQ.5 NO conecta", "MPRLS0030PA00002A = 0x28", "DFR1103 GNSS+RTC = 0x66", "Routing permanece bloqueado"):
        if marker not in sch:
            fail(f"hoja de integración sin marcador: {marker}")

    print("OK: integración eléctrica PR #11 coherente")
    print("- Z1 + Z2 consumen rails locales de Z3 sin back-feed al UNO Q")
    print("- I2C compartido: 0x28 MPR + 0x66 DFR1103")
    print("- ownership UNO Q sin colisiones salvo SDA/SCL compartidos")
    print("- placement/routing siguen bloqueados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
