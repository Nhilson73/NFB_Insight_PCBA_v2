# HMI Nextion

HMI de producción seleccionada: **Nextion NX8048P050-011C-Y**.

Los proyectos de interfaz deben conservar dos artefactos trazables por release:

- fuente editable Nextion: `.HMI`;
- binario compilado/liberado: `.tft`.

Convención sugerida: `NFB_Insight_HMI_vMAJOR.MINOR.PATCH.HMI/.tft`.

No colocar archivos generados sin versión o backups del editor en este directorio. La integración eléctrica, accesorios y gates están en `../hardware/hmi_system_contract.json` y `../docs/HMI_NEXTION_NX8048P050.md`.
