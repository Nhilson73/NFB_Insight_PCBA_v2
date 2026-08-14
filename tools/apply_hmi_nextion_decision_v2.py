#!/usr/bin/env python3
"""Materializador canónico HMI v2.

Ejecuta la decisión base y después materializa las huellas mecánicas externas de
SDExtender, BOX Speaker y Foca Max, además de enlazarlas en el BOM de sistema.
No modifica el PCB, placement ni routing de producción.
"""
from __future__ import annotations

import csv
import runpy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT/'tools'/'apply_hmi_nextion_decision.py'), run_name='__main__')

FOOTPRINTS={
'Nextion_SDExtender_External.kicad_mod': '''(footprint "Nextion_SDExtender_External"
  (version 20240108) (generator pcbnew) (layer "F.Cu")
  (descr "EXTERNAL MECHANICAL ENVELOPE ONLY - Nextion SDExtender; 17.1 x 41.48 x 2.5 mm. Not PCBA.")
  (attr exclude_from_pos_files exclude_from_bom)
  (fp_rect (start -8.55 -20.74) (end 8.55 20.74) (stroke (width 0.25) (type default)) (fill none) (layer "F.Fab"))
  (fp_rect (start -8.55 -20.74) (end 8.55 20.74) (stroke (width 0.20) (type dash)) (fill none) (layer "Dwgs.User"))
  (fp_text reference "HMI_SD_EXT" (at 0 -23) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
  (fp_text value "SDExtender" (at 0 23) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
  (fp_text user "EXTERNAL - NOT PCBA" (at 0 0 90) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
)''',
'Nextion_BOX_Speaker_External.kicad_mod': '''(footprint "Nextion_BOX_Speaker_External"
  (version 20240108) (generator pcbnew) (layer "F.Cu")
  (descr "EXTERNAL MECHANICAL ENVELOPE ONLY - Nextion BOX Speaker; 31 x 28 x 14.8 mm. Not PCBA.")
  (attr exclude_from_pos_files exclude_from_bom)
  (fp_rect (start -15.5 -14) (end 15.5 14) (stroke (width 0.25) (type default)) (fill none) (layer "F.Fab"))
  (fp_rect (start -15.5 -14) (end 15.5 14) (stroke (width 0.20) (type dash)) (fill none) (layer "Dwgs.User"))
  (fp_text reference "HMI_SPEAKER" (at 0 -16.5) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
  (fp_text value "Nextion BOX Speaker" (at 0 16.5) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
  (fp_text user "EXTERNAL - NOT PCBA" (at 0 0) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
)''',
'Nextion_Foca_Max_Service.kicad_mod': '''(footprint "Nextion_Foca_Max_Service"
  (version 20240108) (generator pcbnew) (layer "F.Cu")
  (descr "SERVICE MECHANICAL ENVELOPE ONLY - Nextion Foca Max; 50 x 50 x 12 mm. Not installed in product.")
  (attr exclude_from_pos_files exclude_from_bom)
  (fp_rect (start -25 -25) (end 25 25) (stroke (width 0.25) (type default)) (fill none) (layer "F.Fab"))
  (fp_rect (start -25 -25) (end 25 25) (stroke (width 0.20) (type dash)) (fill none) (layer "Dwgs.User"))
  (fp_text reference "HMI_FOCA_MAX" (at 0 -27.5) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
  (fp_text value "Foca Max" (at 0 27.5) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
  (fp_text user "SERVICE TOOL - NOT PRODUCT" (at 0 0) (layer "F.Fab") (effects (font (size 1.2 1.2) (thickness 0.2))))
)'''
}
lib=ROOT/'kicad'/'lib'/'nfb_footprints.pretty'; lib.mkdir(parents=True,exist_ok=True)
for name,text in FOOTPRINTS.items():
    (lib/name).write_text(text.rstrip()+'\n',encoding='utf-8')

bom=ROOT/'bom'/'insight_hmi_system_bom.csv'
with bom.open(newline='',encoding='utf-8') as fh:
    reader=csv.DictReader(fh); rows=list(reader); fields=reader.fieldnames
mapping={
    'HMI_SD_EXT':'NFB:Nextion_SDExtender_External',
    'HMI_SPEAKER':'NFB:Nextion_BOX_Speaker_External',
    'HMI_FOCA_MAX':'NFB:Nextion_Foca_Max_Service'
}
for row in rows:
    if row['item_id'] in mapping: row['footprint_o_mecanica']=mapping[row['item_id']]
with bom.open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); w.writerows(rows)

print('OK: materializador HMI v2 completo; PCB/placement/routing no modificados')
