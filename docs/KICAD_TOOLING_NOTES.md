# NFB Insight PCBA v2 — notas técnicas de tooling KiCad

Referencia técnica para scripts `pcbnew`, validadores y CI de NFB Insight PCBA v2. Estas notas destilan hallazgos propios PR17–PR24 y conocimiento reusable verificado en el repo donor `nebula_qshield_pcb`. **No se hereda geometría ni layout del donor.**

## 1. El triplete de KiCad es inseparable en pruebas

Para este proyecto existen:

- `kicad/NFB_Insight_PCBA_v2.kicad_pcb`
- `kicad/NFB_Insight_PCBA_v2.kicad_pro`
- `kicad/NFB_Insight_PCBA_v2.kicad_dru`

Si un test copia el PCB a otro basename, debe copiar también `.kicad_pro` y `.kicad_dru` con ese mismo basename. De lo contrario `kicad-cli` puede evaluar el board con reglas genéricas diferentes a las reglas efectivas del proyecto y producir falsos resultados.

**Regla CI:** preferir validar el board canónico. Si se necesita sandbox, clonar el triplete completo.

## 2. `.kicad_pro` y `.kicad_dru` cumplen papeles distintos

`*.kicad_pro` contiene valores de proyecto/netclass, incluidos anchos preferidos. `*.kicad_dru` contiene reglas custom que pueden imponer mínimos o excepciones locales diferentes.

El router no debe asumir que `track_width` de `.kicad_pro` es automáticamente el mínimo legal. Antes de implementar neckdown o rutas críticas, calcular la regla efectiva aplicable a la net y dejar que `kicad-cli pcb drc` sea la autoridad final.

En NFB existe ya una excepción localizada del TPSM33625: clearance interno de `0.125 mm` exclusivamente para geometría asociada a `U_5V`; no debe convertirse en una relajación global.

## 3. `PCB_VIA.GetWidth()` necesita capa

Evitar:

```python
via.GetWidth()
```

Usar:

```python
via.GetWidth(pcbnew.F_Cu)
```

La llamada sin capa puede disparar un assert nativo y bloquear el proceso en lugar de producir una excepción Python manejable.

## 4. Courtyard real ≠ `footprint.GetBoundingBox()`

Para placement, ECO y keepouts, no usar el bounding box global del footprint como sustituto de courtyard. Puede incluir Fab, texto u otros gráficos.

Calcular el courtyard desde `fp.GraphicalItems()` filtrando ítems por `F.Courtyard` / `B.Courtyard` y construir el bounding box a partir de esa geometría.

Esto es crítico para los gates que exigen `courtyard overlaps = 0`.

## 5. Clearance propio con margen positivo

Los scripts geométricos usan coordenadas discretizadas y pueden acumular errores submicrónicos. Un chequeo propio nunca debe ser permisivo respecto al límite DRC.

Ejemplo recomendado: exigir margen positivo adicional (orden `0.01 mm` cuando sea apropiado) antes de considerar un corredor disponible. El valor exacto no sustituye la regla de KiCad: solo evita falsos positivos del planner.

**Autoridad final:** DRC KiCad 10.0.5.

## 6. Pad-shape no equivale a endpoint eléctrico

Algunos footprints usan varios shapes con el mismo número de pad. Para routing/connectivity:

- todos los shapes siguen participando como cobre/obstáculos;
- pero un mismo `ref.pin` representa **un endpoint eléctrico lógico**.

Este hallazgo fue crítico en PR23 para el TPS259470A: contar cada shape como endpoint separado generaba árboles de routing artificiales y cobre innecesario.

## 7. Nets multipunto: no imponer MST geométrico ciegamente

La topología eléctrica debe preceder al árbol geométrico.

Ejemplos ya demostrados:

- `5V_VCC`: el capacitor VCC es centro físico/funcional y el strap RT→VCC tiene propósito de configuración; un MST genérico generaba una unión innecesariamente difícil pin8→pin11.
- divisores/programación eFuse: ITIMER/UVLO/OVLO/ILM/DVDT requieren priorización por confinamiento físico y función, no solo por distancia.
- `LOAD_A_POS/NEG`: deben tratarse como par quieto principal `J_LOADCELL → U_HX`; los testpoints son ramas secundarias cortas.

## 8. Micro-ruta determinista cuando la grilla no representa un corredor legal

Una grilla A*/Dijkstra puede no muestrear una garganta física real aun cuando DRC permita un camino. En ese caso:

1. medir geometría exacta;
2. demostrar que el corredor existe;
3. usar waypoints continuos/locales solo para esa micro-ruta;
4. mantener netclass/clearance;
5. validar con DRC.

No reducir globalmente la rejilla o el clearance para resolver un solo pin.

## 9. Neckdown: siempre local, documentado y DRC-gated

Si una salida de pitch fino requiere ancho/clearance especial:

- limitarla a una net concreta;
- limitarla a una región/courtyard concreta;
- no debilitar reglas fuera de esa microzona;
- documentar el motivo eléctrico/físico;
- exigir DRC completo.

Un neckdown que “hace que el router encuentre camino” pero produce un nuevo error DRC se rechaza.

## 10. `unconnected_items` no significa automáticamente “dibujar una pista”

Antes de rutear un ítem reportado como desconectado:

- identificar net y endpoints reales;
- reconstruir conectividad de board;
- diferenciar pads/tracks/vías de islas de plano;
- cuando existan zones, detectar posibles pares `Zone ↔ Zone` espurios del refill/island detector.

En PR19A todavía no se materializan planos de GND/potencia; esta regla cobrará más importancia en PR20A/PR20B.

## 11. Refill de zones y conectividad

Cuando un cambio futuro afecte zones:

```python
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
```

No asumir continuidad de un plano por inspección visual. Confirmar cobre relleno/conectividad real mediante APIs de zone/connectivity y después DRC.

## 12. PCB regenerado: equivalencia semántica, no byte-a-byte

`pcbnew` puede regenerar UUIDs al reconstruir footprints/board. Por eso PR17 abandonó la expectativa de `git diff` cero para el `.kicad_pcb` regenerado.

Validar semánticamente:

- refs;
- XY/rotación;
- `LIB_ID`/footprints;
- pads/nets;
- board outline;
- layer/routing policy;
- DRC;
- métricas del lote.

Los JSON deterministas sí pueden exigir reproducción byte/text exacta cuando corresponda.

## 13. CI de validación debe ser read-only

No persistir automáticamente un `.kicad_pcb` reconstruido en cada corrida: los UUIDs no byte-estables pueden crear bucles de commits del bot.

Patrón vigente:

- persistencia explícita y excepcional cuando un artefacto ya pasó DRC;
- después, workflow final con `permissions: contents: read`;
- HEAD normal de usuario/agente revalida antes del merge.

## 14. Gates históricos deben ser composicionales

Un gate antiguo no debe asumir que su revisión sigue siendo la última.

Ejemplo ya aplicado:

- PR22 valida su ECO Z3 contra PR17;
- después aplica PR24 Z2;
- finalmente compara/reconstruye el estado vigente completo.

Cada ECO futuro debe preservar esta cadena: **validar el delta local contra su baseline y luego reproducir todos los ECO posteriores vigentes**.

## 15. Placement global congelado, ECO local permitido con evidencia

Routing puede revelar un problema real de placement. No se debe forzar cobre alrededor de una mala microtopología.

Un ECO post-PR17 requiere:

- trigger reproducible desde routing;
- evidencia primaria o inferencia de ingeniería declarada;
- mínimo número de refs movidas;
- resto de refs idénticas;
- courtyard overlaps = 0;
- DRC físico = 0;
- contrato JSON + script reproducible;
- merge del ECO antes de reiniciar el lote de routing.

Aplicado ya en:

- PR22: 5 pasivos de la isla TPSM33625;
- PR24: 2 testpoints de load-cell junto a HX711.

## 16. Calidad geométrica además de conectividad

Una ruta conectada puede seguir siendo inaceptable.

Métricas mínimas por net/lote:

- longitud total;
- número de segmentos;
- número de vías;
- giros/cambios de dirección;
- capa(s);
- corredor/zona;
- relación con nets sensitive/dirty.

Ejemplo de anti-patrón detectado en PR23: una net local podía cerrar con ~200 segmentos y múltiples vías. Esa ruta no debe mergearse solo por estar eléctricamente conectada.

## 17. Política de routing incremental NFB

Contrato vigente:

`28 locales → 4 analógicas inter-zona → 16 digital/control → 10 potencia/actuadores → 1 GND`

Cada lote es **ALL_OR_NOTHING**:

- 100% de sus nets conectadas;
- 0 nets de lotes futuros con cobre;
- 0 shorts/clearance/courtyard nuevos;
- placement/outline fuera de scope congelados;
- métricas razonables;
- DRC acorde a la fase.

## 18. Fuente donor: qué se hereda y qué no

Del repo `Nhilson73/nebula_qshield_pcb` se heredan únicamente aprendizajes/tooling generalizable: gotchas `pcbnew`, DRC, courtyards, triplete de basename, tratamiento de zones y estrategias de routing.

**No heredar:** dimensiones, coordenadas, J21, layout 170×120, netclasses concretas, copper, placement, keepouts ni topology específica del Q-Shield.

NFB Insight conserva su propia geometría contractual **242.34 × 68.58 mm** y sus contratos PR17–PR24 como autoridad.
