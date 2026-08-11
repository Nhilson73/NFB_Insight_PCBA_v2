# NFB Insight PCBA v2 — Hoja de Ruta de Desarrollo

## Fase 0 — Congelar arquitectura

- [x] Inicializar repositorio limpio.
- [x] Congelar sistema global de coordenadas.
- [x] Congelar orientación del UNO Q: USB-C hacia `-Y`.
- [x] Congelar altura de la board en `68.58 mm`.
- [x] Congelar dirección de crecimiento: únicamente `+X`.
- [x] Designar `Y=0` como FIELD I/O EDGE.
- [x] Definir el orden de zonificación funcional.
- [x] Definir herencia selectiva desde el Q-Shield donante.
- [x] Clasificar BOM donante en ACEPTAR / REVISAR / DESCARTAR / RESERVA.

## Fase 1 — Activos mecánicos donantes

- [x] Crear footprint inmutable del UNO Q rotado en el origen global.
- [x] Verificar los cuatro agujeros de montaje usando las coordenadas transformadas.
- [x] Incorporar referencias mecánicas conservadoras para USB-C/PMIC, JCTL, SPI2/JSPI y Qwiic en `Eco1.User`.
- [x] Crear contorno inicial de la board con `H = 68.58 mm` y ancho provisional de `220 mm`.
- [x] Añadir zonificación visual Z0–Z4 y declarar `Y=0` como FIELD I/O EDGE.
- [x] Añadir validación automática de origen, altura, agujeros y pads extremos del UNO Q.
- [ ] Convertir las exclusiones mecánicas necesarias en keepouts DRC-enforced únicamente después de contrastarlas con CAD/STEP oficial y enclosure.
- [ ] Añadir corredor/courtyards definitivos de conectores del lado de servicio en `Y=0` cuando se seleccione cada familia de conectores.
- [ ] Verificar relación UNO Q + carrier en KiCad 3D Viewer con modelo STEP oficial.

## Fase 2 — Migración limpia del esquemático Insight

### PR #3 — Baseline contractual

- [x] Crear root schematic V2 limpio, sin copiar literalmente la hoja raíz donante.
- [x] Crear contrato de 32 pines legible por máquina en `hardware/insight_pin_contract.json`.
- [x] Congelar mapeo A0/A1/A2/A4/A5 de sensores según la arquitectura conocida en ese hito.
- [x] Congelar D0/D1 HMI, D2/D3 HX711, D4 watchdog, D5-D8 controles de actuadores y D20/D21 I2C.
- [x] Eliminar canal de humedad A3 de la línea base Insight; A3 queda DNP/Reserva.
- [x] Mantener PWM de válvula proporcional D9 fuera de la línea base; D9 queda DNP/Reserva.
- [x] Reservar D10 para expansión RS485/Signature sin poblar el bridge en la línea base Insight.
- [x] Verificar el contrato contra `Nebula_ArduinoAPPLab_UNOQ` `main` en el commit `cf100b38df890f61aed472e934241e145425569b`.
- [x] Documentar divergencias actuales del firmware: build Signature, A3 humedad y D9 CO2 flow PWM.
- [x] ERC del root schematic = 0 mediante GitHub Actions.

### PR #4 — Arquitectura analógica y aislamiento Insight — trazabilidad donante

- [x] Tomar `kicad/analog_acquisition.kicad_sch` del Q-Shield como fuente primaria del circuito donante.
- [x] Crear `hardware/analog_insight_manifest.json` con trazabilidad por canal y precedencia esquemático > BOM histórica.
- [x] Crear `bom/insight_analog_inheritance.csv` separando `INHERIT` y `REVIEW`.
- [x] Congelar como funciones Insight únicamente pH/A0, ORP/A1, TEMP/A2, CO2/A4 y DO/A5.
- [x] Preservar la arquitectura de aislamiento pH/ORP/DO del donante para revisión, sin convertirla todavía en netlist de producción.
- [x] Excluir explícitamente A3/HUM y refs donantes `J7`, `D8`, `R17`, `R18`, `C23`.
- [x] Aplicar a todos los conectores de campo la regla mecánica `Y=0` / salida `-Y`.
- [x] Crear `kicad/analog_insight.kicad_sch` como hoja de trazabilidad Z1 parseable por KiCad.
- [x] Añadir gate automático de manifiesto/BOM/contrato y ERC de la hoja analógica.
- [x] Revisar datasheets, impedancias, rangos y ganancias antes de convertir los bloques heredados en netlist discreto de producción; la revisión se materializa como corrección en PR #5.

### PR #5 — Corrección de interfaces reales de sensores

- [x] Crear `hardware/sensor_interface_contract.json` como fuente de verdad de producción de los cinco sensores.
- [x] Congelar el dominio analógico del UNO Q en 3.3 V y un objetivo de diseño de entrada externa `<= 3.05 V`.
- [x] Corregir pH: recibir salida acondicionada 0–3 V de `SEN0161-V2` / `SEN0169-V2`; BNC fuera de la PCBA.
- [x] Marcar `SEN0169-V2` como opción preferida para monitoreo continuo sin invalidar `SEN0161-V2` para prototipo.
- [x] Corregir ORP: recibir `SEN0464` acondicionado y escalar con divisor 10 kΩ / 20 kΩ; 4.5 V -> 3.0 V.
- [x] Corregir temperatura: `KIT0021` usa DS18B20 digital; A2/D16 cambia de `TEMP_ADC` a `TEMP_1WIRE`.
- [x] Registrar la migración de firmware pendiente para DS18B20/1-Wire.
- [x] Corregir DO: recibir salida acondicionada 0–3 V de `SEN0237-A`; BNC fuera de la PCBA.
- [x] Retirar del baseline de producción las cadenas obligatorias `SN6501 + transformer + AMC1301` de pH/ORP/DO.
- [x] Definir `DFR0504` o equivalente como opción inline de sistema cuando pruebas de interferencia entre sondas lo requieran; no es placement de la PCBA.
- [x] Marcar `MPX5700AP` como `REPLACE_BEFORE_FAB` por lifecycle/rango y mantener 18 kΩ / 30 kΩ únicamente como red de validación legacy.
- [x] Crear `bom/insight_sensor_interface_bom.csv` sin revivir BNC ni aislamiento legacy onboard.
- [x] Añadir gate numérico automático de escalamiento, coherencia de contratos y lifecycle.
- [x] Mantener ERC del root schematic = 0 y las validaciones PR4 como trazabilidad histórica.

### PR #6 — Netlist discreto de producción de sensores

- [ ] Seleccionar sensor de presión CO₂ vigente y apropiado al rango real del biorreactor.
- [ ] Congelar MPN/footprint de conectores 3p considerando enclosure y alivio de tensión.
- [ ] Congelar clamps ESD/protección con corriente de fuga/capacitancia compatibles con cada interfaz.
- [ ] Congelar filtros RC después de pruebas de ruido/ancho de banda.
- [ ] Materializar pH/ORP/TEMP/CO2/DO como netlist discreto KiCad de producción.
- [ ] Conectar la hoja de sensores al root schematic.
- [ ] Mantener ERC = 0 y coherencia automática BOM/contrato/netlist.

### Migración posterior por bloques

- [ ] Construir hoja digital/bajo ruido para HX711, RTC/GPS, I2C, HMI y watchdog.
- [ ] Construir hoja de potencia únicamente después de congelar la arquitectura de potencia de Fase 3.
- [ ] Construir hoja de actuadores con control Insight y sin arrastrar etapas Signature innecesarias.
- [ ] Conectar la jerarquía completa al root schematic y mantener ERC = 0.

## Fase 3 — Congelar arquitectura de potencia

- [ ] Separar potencia de lógica/sensores de la potencia ruidosa de actuadores.
- [ ] Decidir si las cargas de actuadores atraviesan la PCBA o si la PCBA entrega únicamente señales de control.
- [ ] Preferir chiller con alimentación externa; la PCBA suministra solo control.
- [ ] Calcular corrientes continuas y de pico.
- [ ] Reseleccionar F1/D2/conector de entrada cuando corresponda.
- [ ] Revalidar topología buck/LDO.
- [ ] Definir netclasses antes del placement/routing.

## Fase 4 — Placement por zonas

- [ ] Z0 UNO Q bloqueado.
- [ ] Z1 sensores/interfaz con conectores de campo directamente debajo de sus front-end.
- [ ] Z2 digital/bajo ruido.
- [ ] Z3 potencia con loops de conmutación minimizados.
- [ ] Z4 actuadores/potencia ruidosa en el extremo `+X`.
- [ ] Todos los conectores de campo alineados sobre `Y=0` y orientados hacia `-Y` cuando sea mecánicamente posible.
- [ ] Revisión mecánica 3D antes del routing.
- [ ] Congelar ancho final de la board a partir del placement real.

## Fase 5 — Routing

- [ ] Preservar plano de referencia continuo para señales sensibles.
- [ ] Prioridad de routing manual: sensores → clock/I2C/HX711 → potencia → actuadores.
- [ ] No sacrificar integridad de plano ni aislamiento para resolver congestión del autorouter.
- [ ] Rutear alta corriente únicamente después de congelar arquitectura de carga/corriente.
- [ ] Añadir stitching vias y test points de forma deliberada.
- [ ] 0 items desconectados inesperados.
- [ ] DRC = 0.

## Fase 6 — Preparación para fabricación

- [ ] Revisión de lifecycle y disponibilidad de la BOM.
- [ ] Auditoría footprint vs. datasheet.
- [ ] Revisión de conectores de panel y alivio de tensión de cables.
- [ ] Revisión visual de Gerbers y drill.
- [ ] Exportar BOM + CPL.
- [ ] Variante de ensamblaje = Insight.
- [ ] Congelar notas de fabricación y stackup.
- [ ] Crear tag `v2.0-RC1` únicamente después de superar todos los gates de revisión.

## Fase 7 — Bring-up y HIL

- [ ] Bring-up de rails antes de instalar el UNO Q.
- [ ] Encendido con corriente limitada.
- [ ] Pruebas de inyección en canales de sensores.
- [ ] Validación de ruido e interferencia pH/ORP/DO con y sin aislamiento inline.
- [ ] Prueba HX711/celda de carga.
- [ ] Verificaciones funcionales HMI/GPS/RTC/I2C.
- [ ] Pruebas de control de bomba/solenoide/chiller con cargas representativas.
- [ ] Prueba de watchdog/failsafe.
- [ ] Fixture HIL y procedimiento repetible de prueba de producción.
