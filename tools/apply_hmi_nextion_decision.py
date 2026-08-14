#!/usr/bin/env python3
"""Materializa la decisión de sistema HMI Nextion sin alterar cobre/placement.

Este script es intencionalmente idempotente. La HMI es un conjunto externo al
PCBA; J_HMI conserva la geometría ya ruteada y se añade una huella mecánica de
referencia para integración de enclosure.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HMI_URL = "https://itead.cc/product/5-0-nextion-intelligent-series-hmi-touch-display-with-enclosure/"
HMI_DS = "https://nextion.tech/datasheets/NX8048P050-011C-Y/"
DIM_URL = "https://cdn.nextion.tech/wp-content/uploads/2020/12/NX8048P050-011X-Y-Dimension.pdf"
SD_URL = "https://itead.cc/product/nextion-micro-sd-card-extender/"
SPEAKER_URL = "https://itead.cc/product/nextion-box-speaker/"
FOCA_URL = "https://itead.cc/product/nextion-foca-max-5v2a-output-usb-to-ttl-serial-converter-board/"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_between(text: str, start: str, end: str, replacement: str) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[:a] + replacement.rstrip() + "\n\n" + text[b:]


contract = {
    "schema_version": 1,
    "product": "NFB Insight PCBA v2",
    "status": "HMI_SYSTEM_DECISION_NEXTION_NX8048P050_011C_Y",
    "decision_date": "2026-08-14",
    "architecture_role": "EXTERNAL_HMI_ASSEMBLY_CONNECTED_TO_Z2_J_HMI",
    "selected_display": {
        "manufacturer": "Nextion / ITEAD",
        "series": "Intelligent Series",
        "mpn": "NX8048P050-011C-Y",
        "sku": "6920075776553",
        "display_size_in": 5.0,
        "touch": "CAPACITIVE",
        "enclosure": True,
        "resolution_px": [800, 480],
        "mcu_mhz": 200,
        "flash_mb": 128,
        "sram_kb": 512,
        "eeprom_bytes": 1024,
        "rtc": "CR1220",
        "gpio_count": 8,
        "audio_supported": True,
        "video_supported": True,
        "input_power": {"voltage_v": 5.0, "current_a_recommended": 1.0},
        "usart_connector_vendor_description": "XH2.54 4P",
        "working_temperature_c": [-20, 70],
        "storage_temperature_c": [-30, 85],
        "mechanical": {
            "front_envelope_mm": [160.04, 107.07],
            "rear_body_mm": [151.64, 104.78],
            "max_depth_mm": 21.2,
            "source": DIM_URL,
            "footprint": "NFB:Nextion_NX8048P050_011C_Y_Enclosure"
        },
        "sources": {"product": HMI_URL, "datasheet": HMI_DS, "dimension": DIM_URL}
    },
    "pcba_interface": {
        "ref": "J_HMI",
        "role": "BOARD_SIDE_CABLE_INTERFACE",
        "board_connector_mpn": "S4B-XH-A(LF)(SN)",
        "board_connector_footprint": "Connector_JST:JST_XH_S4B-XH-A_1x04_P2.50mm_Horizontal",
        "board_connector_pitch_mm": 2.50,
        "nextion_interface_vendor_description": "XH2.54 4P",
        "routing_frozen": True,
        "footprint_change_on_pcba": False,
        "reason": "PR19C ya cerró HMI_RX/HMI_TX; ITEAD publica XH2.54 4P pero no un MPN JST exacto. Se conserva la geometría de J_HMI y se exige prueba de apareamiento del arnés en first article antes de release.",
        "pinout_board": {"1": "5V_RAIL", "2": "GND", "3": "HMI_FIELD_RX", "4": "HMI_FIELD_TX"},
        "signal_mapping": {
            "NFB_HMI_FIELD_RX": "Nextion TX",
            "NFB_HMI_FIELD_TX": "Nextion RX",
            "power": "5V_RAIL",
            "return": "GND"
        },
        "translator": "TXU0202DCUR",
        "field_esd": "PESD5V0U1UL,315"
    },
    "selected_accessories": [
        {
            "id": "HMI_SD_EXT",
            "manufacturer": "Nextion / ITEAD",
            "product": "Nextion Micro SD Card Extender",
            "model": "SDExtender",
            "qty_per_system": 1,
            "classification": "PRODUCTION_EXTERNAL_ACCESSORY",
            "dimensions_mm": [17.1, 41.48, 2.5],
            "mass_g": 7.0,
            "filesystem": "FAT32 microSD",
            "source": SD_URL,
            "pcba_population": False
        },
        {
            "id": "HMI_SPEAKER",
            "manufacturer": "Nextion / ITEAD",
            "product": "Nextion BOX Speaker",
            "model": "Nextion BOX Speaker",
            "qty_per_system": 1,
            "classification": "PRODUCTION_EXTERNAL_ACCESSORY",
            "dimensions_mm": [31.0, 28.0, 14.8],
            "mass_g": 21.2,
            "input_power_w": 1.5,
            "frequency_hz": [100, 3000],
            "connector": "1.25 mm pitch 2-pin female (1.25T-2-2A)",
            "wire_length_mm": 250,
            "power_increment_a": 0.5,
            "source": SPEAKER_URL,
            "pcba_population": False,
            "first_article_check": "Confirmar acceso/montaje del conector de audio con la variante -Y con enclosure."
        },
        {
            "id": "HMI_FOCA_MAX",
            "manufacturer": "Nextion / ITEAD",
            "product": "Nextion Foca Max 5V2A Output USB To TTL Serial Converter Board",
            "model": "Foca Max",
            "qty_per_lab_kit": 1,
            "classification": "SERVICE_PROGRAMMING_TOOL_NOT_INSTALLED",
            "usb_uart": "CP2102",
            "max_baud_bps": 2000000,
            "ttl_level_v": 3.3,
            "dc_input_v": [8, 26],
            "output_v": [5.0, 5.5],
            "output_current_a_max": 2.0,
            "pcb_dimensions_mm": [50.0, 50.0, 1.6],
            "overall_dimensions_mm": [50.0, 50.0, 12.0],
            "included": ["USB wire x1", "XH2.54 4P wire x1"],
            "source": FOCA_URL,
            "pcba_population": False,
            "usage": "Programación/bring-up. Para displays >4.3 in ITEAD recomienda alimentar Foca Max con DC externo 8-26 V."
        }
    ],
    "power_integration": {
        "display_current_a": 1.0,
        "speaker_increment_a": 0.5,
        "reserved_hmi_current_a_with_audio": 1.5,
        "reserved_hmi_power_w_with_audio": 7.5,
        "current_5v_rail_design_limit_a": 1.5,
        "current_5v_rail_also_feeds": ["pH module", "ORP module", "DO module", "3.3V LDO input", "TXU0202 VCCB/support"],
        "status": "POWER_ECO_REQUIRED_BEFORE_PRODUCT_RELEASE",
        "decision": "No declarar el HMI+speaker liberado sobre 5V_RAIL mientras el presupuesto continuo siga en 1.5 A. PR20A no debe congelar potencia sin cerrar este gate.",
        "acceptable_closure": [
            "revalidar térmica/corriente y elevar formalmente el presupuesto continuo del rail con margen para todas las cargas",
            "o introducir una alimentación 5 V dedicada para HMI mediante un ECO eléctrico explícito"
        ]
    },
    "firmware_and_service": {
        "transport": "UART TTL mediante TXU0202; D0=HMI_RX, D1=HMI_TX",
        "project_source_extension": ".HMI",
        "compiled_distribution_extension": ".tft",
        "deployment_methods": ["microSD mediante SDExtender", "UART/USB mediante Foca Max en banco"],
        "repository_policy": "Versionar fuentes HMI y binario .tft liberado por versión; no depender de archivos locales no trazados."
    },
    "release_gates": [
        "First-article mating test entre J_HMI S4B-XH-A y el arnés XH2.54 4P seleccionado.",
        "Cerrar power ECO para 1.5 A de reserva HMI+speaker más las demás cargas 5 V.",
        "Confirmar acceso del speaker y SDExtender en el enclosure -Y.",
        "Validar UART bidireccional a 5 V field-side mediante TXU0202.",
        "Validar actualización .tft por SDExtender y programación de banco con Foca Max.",
        "Revisar EMC/pre-compliance del cable HMI final en el producto integrado."
    ]
}
write_json(ROOT / "hardware/hmi_system_contract.json", contract)

bom = """categoria,item_id,qty,rol_producto,fabricante,mpn_modelo,sku,footprint_o_mecanica,poblacion_pcba,alimentacion,interfaz,fuente,nota
HMI,HMI_DISPLAY,1,PRODUCTION_EXTERNAL_ASSEMBLY,Nextion / ITEAD,NX8048P050-011C-Y,6920075776553,NFB:Nextion_NX8048P050_011C_Y_Enclosure,NO,5V 1A,XH2.54 4P UART,{hmi},5.0in capacitiva Intelligent Series con enclosure; 800x480.
HMI,HMI_SD_EXT,1,PRODUCTION_EXTERNAL_ACCESSORY,Nextion / ITEAD,SDExtender,,17.1x41.48x2.5 mm,NO,N/A,microSD FAT32,{sd},Extensor de microSD para acceso desde enclosure.
HMI,HMI_SPEAKER,1,PRODUCTION_EXTERNAL_ACCESSORY,Nextion / ITEAD,Nextion BOX Speaker,,31x28x14.8 mm,NO,+0.5A sobre presupuesto HMI,1.25mm 2P female 1.25T-2-2A,{speaker},1.5W; cable 250mm; reservar HMI total 5V/1.5A.
SERVICE,HMI_FOCA_MAX,1,SERVICE_PROGRAMMING_TOOL_NOT_INSTALLED,Nextion / ITEAD,Foca Max,,50x50x12 mm,NO,DC 8-26V -> 5-5.5V max 2A,USB 2.0 / TTL 3.3V CP2102,{foca},Incluye USB wire y XH2.54 4P wire; usar para programación/bring-up.
INTERFACE,J_HMI,1,PCBA_BOARD_SIDE_INTERFACE,JST,S4B-XH-A(LF)(SN),,Connector_JST:JST_XH_S4B-XH-A_1x04_P2.50mm_Horizontal,YES,5V_RAIL,5V/GND/UART,{hmi},Geometría de PCBA congelada post-PR19C; mating con cable Nextion debe verificarse en first article.
""".format(hmi=HMI_URL, sd=SD_URL, speaker=SPEAKER_URL, foca=FOCA_URL)
write_text(ROOT / "bom/insight_hmi_system_bom.csv", bom)

footprint = '''(footprint "Nextion_NX8048P050_011C_Y_Enclosure"
  (version 20240108)
  (generator pcbnew)
  (layer "F.Cu")
  (descr "EXTERNAL MECHANICAL ENVELOPE ONLY - Nextion NX8048P050-011C-Y with enclosure; front 160.04 x 107.07 mm; max depth 21.2 mm. Not to be placed on NFB PCBA.")
  (tags "Nextion HMI NX8048P050-011C-Y enclosure external mechanical")
  (attr exclude_from_pos_files exclude_from_bom)
  (fp_rect
    (start -80.02 -53.535)
    (end 80.02 53.535)
    (stroke (width 0.25) (type default))
    (fill none)
    (layer "F.Fab")
  )
  (fp_rect
    (start -80.02 -53.535)
    (end 80.02 53.535)
    (stroke (width 0.20) (type dash))
    (fill none)
    (layer "Dwgs.User")
  )
  (fp_text reference "HMI_EXT"
    (at 0 -56)
    (layer "F.Fab")
    (effects (font (size 1.5 1.5) (thickness 0.25)))
  )
  (fp_text value "NX8048P050-011C-Y"
    (at 0 56)
    (layer "F.Fab")
    (effects (font (size 1.5 1.5) (thickness 0.25)))
  )
  (fp_text user "EXTERNAL HMI - NOT PCBA"
    (at 0 0)
    (layer "F.Fab")
    (effects (font (size 2 2) (thickness 0.3)))
  )
)'''
write_text(ROOT / "kicad/lib/nfb_footprints.pretty/Nextion_NX8048P050_011C_Y_Enclosure.kicad_mod", footprint)

hmi_doc = f'''# Decisión HMI — Nextion NX8048P050-011C-Y

## Estado

**SELECCIONADO para NFB Insight:** Nextion Intelligent Series 5.0\" capacitiva con enclosure, MPN `NX8048P050-011C-Y`, SKU `6920075776553`.

Esta pantalla es un **ensamble externo**, no un footprint poblado sobre la PCBA. La shield mantiene `J_HMI` como interfaz de cable y el repositorio añade una huella mecánica de referencia del enclosure para integración física.

## Pantalla congelada

- MPN: `NX8048P050-011C-Y`.
- 5.0\", 800×480, capacitiva.
- Intelligent Series, MCU 200 MHz, Flash 128 MB, SRAM 512 KB, EEPROM 1024 B.
- RTC CR1220; 8 GPIO; audio/video soportados.
- alimentación oficial: **5 V / 1 A**.
- USART: **XH2.54 4P**.
- operación: -20…70 °C; almacenamiento: -30…85 °C.
- envelope frontal oficial: **160.04 × 107.07 mm**; profundidad máxima **21.2 mm**.

Fuentes oficiales: {HMI_URL} y {HMI_DS}; plano mecánico: {DIM_URL}.

## Interfaz con NFB PCBA

`J_HMI` permanece `S4B-XH-A(LF)(SN)` con footprint KiCad `Connector_JST:JST_XH_S4B-XH-A_1x04_P2.50mm_Horizontal`, side-entry hacia `-Y`.

La razón de **no mover pads** es deliberada: PR19C ya cerró el routing de `HMI_RX/HMI_TX`. ITEAD publica la interfaz del display como `XH2.54 4P` pero no publica en la ficha consultada un MPN JST exacto. Por tanto:

1. no se inventa una equivalencia 2.50 ↔ 2.54;
2. se conserva la geometría de producción del board-side connector;
3. el arnés final debe pasar **mating test de first article** antes de release;
4. cualquier cambio posterior de `J_HMI` será un ECO de footprint/routing explícito.

Mapping lógico: `HMI_TX` del UNO → TXU0202 → `HMI_FIELD_RX` → RX de Nextion; TX de Nextion → `HMI_FIELD_TX` → TXU0202 → `HMI_RX` del UNO. Campo protegido con `PESD5V0U1UL,315`.

## Accesorios seleccionados

### Nextion Micro SD Card Extender

- modelo `SDExtender`;
- 17.1 × 41.48 × 2.5 mm; 7 g;
- FAT32 microSD; compatible con todas las series Nextion;
- ensamble externo, no poblado en PCBA;
- fuente: {SD_URL}.

### Nextion BOX Speaker

- 31 × 28 × 14.8 mm; 21.2 g;
- 1.5 W, 100 Hz–3 kHz;
- conector hembra 2P pitch 1.25 mm `1.25T-2-2A`; cable 250 mm;
- ITEAD exige **+0.5 A** sobre la recomendación de alimentación del display;
- reserva de diseño para display + speaker: **5 V / 1.5 A**;
- verificar acceso/montaje del audio con la variante `-Y` durante first article;
- fuente: {SPEAKER_URL}.

### Nextion Foca Max

`Foca Max` queda como **herramienta de programación/bring-up, no instalada en el producto**:

- CP2102; TTL 3.3 V; hasta 2 Mbps;
- DC externo 8–26 V; salida 5–5.5 V, 2 A máx.;
- PCB 50 × 50 × 1.6 mm; volumen 50 × 50 × 12 mm;
- incluye USB wire y XH2.54 4P wire;
- para pantallas >4.3\" ITEAD recomienda alimentación DC externa 8–26 V;
- fuente: {FOCA_URL}.

## Gate de potencia — obligatorio antes de PR20A/release

El `5V_RAIL` actual usa `TPSM33625RDNR` (2.5 A nominal), pero el contrato de NFB limita el diseño a **1.5 A continuo** y ese mismo rail alimenta pH, ORP, DO y la entrada del LDO 3.3 V. La HMI + speaker ya reserva **1.5 A** por sí sola.

Por tanto el uso del conjunto está seleccionado, pero **la alimentación desde el 5V_RAIL actual no se declara liberada**. Antes de congelar PR20A se debe cerrar uno de estos ECOs:

- validar térmica/corriente/layout y elevar formalmente el presupuesto continuo con margen para todas las cargas, o
- introducir 5 V dedicado para HMI mediante una revisión eléctrica explícita.

No se reduce margen ni se relaja una regla para hacer caber el HMI.

## Firmware y mantenimiento

- Transporte de producción: UART D0/D1 a través de `TXU0202DCUR`.
- Versionar fuente Nextion `.HMI` y binario liberado `.tft`.
- Actualización de campo/lab: microSD mediante `SDExtender`.
- Programación/diagnóstico de banco: `Foca Max`.

## Archivos fuente de verdad

- `hardware/hmi_system_contract.json`
- `bom/insight_hmi_system_bom.csv`
- `kicad/lib/nfb_footprints.pretty/Nextion_NX8048P050_011C_Y_Enclosure.kicad_mod`
- `hardware/z2_digital_contract.json`
- `hardware/power_architecture_contract.json`
'''
write_text(ROOT / "docs/HMI_NEXTION_NX8048P050.md", hmi_doc)

hmi_readme = '''# HMI Nextion

HMI de producción seleccionada: **Nextion NX8048P050-011C-Y**.

Los proyectos de interfaz deben conservar dos artefactos trazables por release:

- fuente editable Nextion: `.HMI`;
- binario compilado/liberado: `.tft`.

Convención sugerida: `NFB_Insight_HMI_vMAJOR.MINOR.PATCH.HMI/.tft`.

No colocar archivos generados sin versión o backups del editor en este directorio. La integración eléctrica, accesorios y gates están en `../hardware/hmi_system_contract.json` y `../docs/HMI_NEXTION_NX8048P050.md`.
'''
write_text(ROOT / "hmi/README.md", hmi_readme)

# Enlazar contrato Z2 sin cambiar topología, footprint ni nets.
z2p = ROOT / "hardware/z2_digital_contract.json"
z2 = json.loads(z2p.read_text(encoding="utf-8"))
h = z2["hmi_uart"]
h["system_contract"] = "hardware/hmi_system_contract.json"
h["selected_display_mpn"] = "NX8048P050-011C-Y"
h["selected_display_sku"] = "6920075776553"
h["selected_display_role"] = "EXTERNAL_HMI_WITH_ENCLOSURE"
h["selected_accessories"] = ["SDExtender", "Nextion BOX Speaker", "Foca Max (service tool)"]
h["power_requirement"] = {
    "display_v": 5.0,
    "display_a": 1.0,
    "speaker_increment_a": 0.5,
    "reserved_a_with_audio": 1.5,
    "release_status": "POWER_ECO_REQUIRED_BEFORE_PRODUCT_RELEASE"
}
h["phase3_resolution"] = (
    "PR #9 congela 5V_RAIL local con TPSM33625RDNR, 2.5 A nominal y límite de diseño de 1.5 A continuo. "
    "La HMI seleccionada NX8048P050-011C-Y requiere 5 V/1 A y el BOX Speaker obliga a reservar +0.5 A; "
    "HMI+audio consume por diseño 1.5 A, igual al límite continuo actual antes de pH/ORP/DO y 3V3 LDO. "
    "Se exige ECO de potencia antes de PR20A/release; ver hardware/hmi_system_contract.json."
)
write_json(z2p, z2)

# Registrar el gate en la arquitectura de potencia, sin elevar límites sin validación.
pp = ROOT / "hardware/power_architecture_contract.json"
power = json.loads(pp.read_text(encoding="utf-8"))
power["shield_5v"]["hmi_integration"] = {
    "system_contract": "hardware/hmi_system_contract.json",
    "selected_display": "NX8048P050-011C-Y",
    "display_current_a": 1.0,
    "speaker_increment_a": 0.5,
    "reserved_current_a_with_audio": 1.5,
    "current_design_limit_a": power["shield_5v"]["regulator"]["design_continuous_limit_a"],
    "status": "POWER_ECO_REQUIRED_BEFORE_PRODUCT_RELEASE",
    "reason": "HMI+speaker iguala por sí solo el límite continuo actual y 5V_RAIL tiene cargas adicionales."
}
power["power_budget"]["selected_hmi_with_audio_w"] = 7.5
power["power_budget"]["hmi_power_gate"] = "OPEN_POWER_ECO_REQUIRED"
write_json(pp, power)

# Anotar J_HMI en BOM Z2 sin añadir refs externos que romperían BOM==netlist.
bp = ROOT / "bom/insight_z2_production_bom.csv"
with bp.open(newline="", encoding="utf-8") as fh:
    reader = csv.DictReader(fh)
    rows = list(reader)
    fields = reader.fieldnames
assert fields
for row in rows:
    if row["ref"] == "J_HMI":
        row["nota"] = (
            "Board-side para Nextion NX8048P050-011C-Y; 5V/GND/RX/TX; side-entry -Y. "
            "ITEAD denomina el arnés XH2.54 4P; conservar footprint ruteado S4B-XH-A 2.50 mm y validar mating first article. "
            "BOM de sistema: bom/insight_hmi_system_bom.csv."
        )
with bp.open("w", newline="", encoding="utf-8") as fh:
    writer = csv.DictWriter(fh, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)

# Actualizar narrativa histórica Z2: la selección posterior supersede la HMI genérica.
dp = ROOT / "docs/FASE2_PR7_Z2_DIGITAL.md"
doc = dp.read_text(encoding="utf-8")
replacement = '''## 4. HMI UART — selección final Nextion

D0/D1 mantienen el contrato lógico:

- D0 = `HMI_RX`
- D1 = `HMI_TX`

La HMI seleccionada posteriormente para producto es **Nextion Intelligent Series `NX8048P050-011C-Y`**, 5.0\" capacitiva con enclosure, 800×480, alimentación oficial 5 V/1 A y USART `XH2.54 4P`. La interfaz de lógica sigue usando **TI `TXU0202DCUR`**:

- UNO `HMI_TX` 3.3 V → `HMI_FIELD_RX` 5 V → RX de Nextion.
- TX de Nextion → `HMI_FIELD_TX` 5 V → UNO `HMI_RX` 3.3 V.

`J_HMI` conserva `S4B-XH-A(LF)(SN)` y su footprint side-entry ya ruteado. ITEAD no identifica un MPN JST exacto para su denominación `XH2.54 4P`; por eso no se mueve la geometría post-PR19C y se exige prueba de apareamiento del arnés en first article.

Accesorios seleccionados: `SDExtender`, `Nextion BOX Speaker` y `Foca Max` (este último solo como herramienta de servicio/programación). El BOX Speaker añade 0.5 A al requisito del display, por lo que se reserva **5 V/1.5 A** para HMI+audio.

Esto abre un gate de potencia: el límite continuo actual de `5V_RAIL` también es 1.5 A y el rail alimenta cargas adicionales. El conjunto HMI queda seleccionado, pero su alimentación no puede declararse liberada hasta un ECO de potencia previo a PR20A/release.

Fuente de verdad: `hardware/hmi_system_contract.json`, `bom/insight_hmi_system_bom.csv` y `docs/HMI_NEXTION_NX8048P050.md`.
'''
doc = patch_between(doc, "## 4. HMI UART", "## 5. Watchdog / supervisión", replacement)
write_text(dp, doc)

# README: hacer visible la selección exacta y el gate de potencia.
rp = ROOT / "README.md"
readme = rp.read_text(encoding="utf-8")
old = "- HMI D0/D1 mediante `TXU0202DCUR`."
new = (
    "- HMI: **Nextion Intelligent `NX8048P050-011C-Y`**, 5.0 in capacitiva con enclosure, 800×480; D0/D1 mediante `TXU0202DCUR`.\n"
    "- Accesorios HMI seleccionados: `SDExtender` + `Nextion BOX Speaker`; `Foca Max` queda como herramienta de programación/servicio.\n"
    "- HMI+speaker reserva **5 V / 1.5 A**; existe un gate de potencia abierto antes de PR20A/release porque `5V_RAIL` tiene otras cargas. Ver `hardware/hmi_system_contract.json`."
)
if old in readme:
    readme = readme.replace(old, new, 1)
elif "NX8048P050-011C-Y" not in readme:
    raise SystemExit("README: no se encontró ancla HMI esperada")
write_text(rp, readme)

print("OK: decisión HMI Nextion materializada sin modificar PCB/placement/routing")
