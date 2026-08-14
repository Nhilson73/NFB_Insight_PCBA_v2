#!/usr/bin/env python3
"""Corrige de forma determinista el lector CSV del materializador PR19D.

Utilidad transitoria: reemplaza dos accesos erróneos a fieldnames sobre el
TextIOWrapper por el atributo del csv.DictReader. Falla si el source esperado
no aparece exactamente dos veces.
"""
from pathlib import Path
p=Path(__file__).with_name('apply_hmi_power_eco.py')
s=p.read_text(encoding='utf-8')
old="with {var}.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f)); fields=f.fieldnames"
repls=0
for var in ('zp','bp'):
    a=old.format(var=var)
    b=f"with {var}.open(newline='',encoding='utf-8') as f:\n    reader=csv.DictReader(f); rows=list(reader); fields=reader.fieldnames"
    if a not in s:
        raise SystemExit(f'patrón no encontrado para {var}')
    s=s.replace(a,b,1); repls+=1
if repls!=2:
    raise SystemExit(f'reemplazos={repls} != 2')
p.write_text(s,encoding='utf-8')
print('OK: materializador ECO corregido (2 lectores CSV)')
