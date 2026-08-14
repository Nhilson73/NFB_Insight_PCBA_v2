# HMI Nextion

HMI de producción seleccionada: **Nextion NX8048P050-011C-Y**.

Los proyectos de interfaz deben conservar dos artefactos trazables por release:

- fuente editable Nextion: `.HMI`;
- binario compilado/liberado: `.tft`.

Convención sugerida: `NFB_Insight_HMI_vMAJOR.MINOR.PATCH.HMI/.tft`.

Materializador canónico de la decisión de hardware/accesorios: `../tools/apply_hmi_nextion_decision_v2.py`.

El conjunto congelado incluye:

- HMI `NX8048P050-011C-Y`;
- `SDExtender`;
- `Nextion BOX Speaker`;
- `Foca Max` únicamente como herramienta de servicio/programación.

Las huellas mecánicas externas viven en `../kicad/lib/nfb_footprints.pretty/` y no se insertan en el PCB de producción. La integración eléctrica, BOM, fuentes oficiales y gates están en `../hardware/hmi_system_contract.json` y `../docs/HMI_NEXTION_NX8048P050.md`.

No colocar archivos generados sin versión ni backups del editor en este directorio.
