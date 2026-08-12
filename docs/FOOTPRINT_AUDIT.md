# NFB Insight PCBA v2 — Auditoría de Footprints PR #11

**Estado:** baseline de auditoría previo a placement  
**Fuente machine-readable:** `hardware/footprint_audit.json`  
**Regla:** ningún componente con auditoría abierta puede colocarse en el PCB.

## 1. Principio

La ausencia de un footprint no se resolverá aproximando geometría a partir del tamaño exterior del encapsulado. Para componentes críticos se exige una fuente primaria reproducible: drawing del fabricante, CAD enlazado/publicado por el fabricante o geometría explícita del datasheet.

El precio del componente no es criterio de cierre. La prioridad es confiabilidad, manufacturabilidad, EMC, térmica y trazabilidad.

## 2. Honeywell MPR — cerrado

Componente: `MPRLS0030PA00002A`  
Footprint: `NFB:Honeywell_MPR_LongPort_12Pad`  
Estado: **CLOSED_PRIMARY_DATASHEET**.

Fuente primaria: Honeywell `32332628`, **Issue L**, Figure 10 — *Long Port and Recommended PCB Pad Layout Dimensions*.

Verificado:

- cuerpo: 5.00 × 5.00 mm;
- 12 pads;
- pitch: 1.27 mm;
- span metálico exterior recomendado: 4.20 mm;
- pads superior/inferior: 0.70 × 0.65 mm;
- pads laterales: 0.65 × 0.70 mm;
- puerto largo: Ø2.50 mm;
- el modelo seleccionado es **absolute**, por lo que el orificio de referencia de gage no se perfora en la PCB.

PR #11 corrige los centros exteriores del footprint de ±1.750 mm a **±1.775 mm**, manteniendo el pitch 1.27 mm, de forma que el patrón metálico alcance 4.20 mm de extremo a extremo.

## 3. TPS259470A — RPW0010A

Componente: `TPS259470ARPWR`  
Estado: **PRIMARY_DRAWING_REVIEWED_CAD_IMPORT_PENDING**.  
Placement: **bloqueado**.

Fuente primaria revisada:

- TI `MPQF568`;
- package `RPW0010A`;
- drawing `4225183/A`.

Verificado en fuente primaria:

- VQFN-HR;
- 10 pines;
- cuerpo nominal 2 × 2 mm;
- altura máxima 1 mm;
- pitch 0.45 mm;
- TI publica *LAND PATTERN EXAMPLE* y prefiere NSMD.

El drawing incluye pads no triviales del HotRod QFN. No se autoriza un footprint simplificado rectangular. El cierre requiere importar o recrear exactamente el land pattern y comparar cobre, máscara y paste con `MPQF568` antes del placement.

## 4. TPSM33625 — RDN-11

Componente: `TPSM33625RDNR`  
Estado: **BLOCKED_VENDOR_CAD_VERIFICATION**.  
Placement: **bloqueado**.

Fuentes primarias revisadas:

- TI TPSM336x5 datasheet Rev. D;
- página oficial `TPSM33625RDNR`;
- package RDN / QFN-FCMOD.

Verificado:

- 11 pines;
- cuerpo 4.5 × 3.5 mm;
- pitch 0.5 mm;
- altura nominal 2 mm;
- TI enlaza CAD/footprint mediante Ultra Librarian.

El body y el pitch **no son suficientes para reconstruir de forma segura el land pattern** del módulo. Se mantiene el token `PENDING_DATASHEET_AUDIT_BEFORE_PLACEMENT` en el netlist de producción hasta disponer de CAD autorizado/verificable y compararlo contra la documentación TI.

## 5. Consecuencia para el proyecto

PR #11 puede cerrar la **integración eléctrica** Z1 + Z2 + potencia porque las nets y contratos no dependen de coordenadas físicas. Sin embargo:

- `U_EFUSE` no puede colocarse;
- `U_5V` no puede colocarse;
- el placement de potencia no puede declararse cerrado;
- el routing continúa bloqueado.

El workflow `Validación footprints e integración PR11` convierte estas condiciones en gates automáticos.

## 6. Próximos cierres

1. Cerrar RPW0010A con land pattern exacto TI.
2. Importar/verificar RDN-11 desde CAD autorizado por TI.
3. Revisar footprints restantes de alto riesgo: conectores de potencia, fusible, MPR, componentes térmicos y interfaces de campo antes de congelar CPL.
4. Solo entonces autorizar placement de Z3 y congelar ancho final del PCB.
