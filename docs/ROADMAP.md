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
- [x] Congelar mapeo A0/A1/A2/A4/A5 de sensores.
- [x] Congelar D0/D1 HMI, D2/D3 HX711, D4 watchdog, D5-D8 controles de actuadores y D20/D21 I2C.
- [x] Eliminar canal de humedad A3 de la línea base Insight; A3 queda DNP/Reserva.
- [x] Mantener PWM de válvula proporcional D9 fuera de la línea base; D9 queda DNP/Reserva.
- [x] Reservar D10 para expansión RS485/Signature sin poblar el bridge en la línea base Insight.
- [x] Verificar el contrato contra `Nebula_ArduinoAPPLab_UNOQ` `main` en el commit `cf100b38df890f61aed472e934241e145425569b`.
- [x] Documentar divergencias actuales del firmware: build Signature, A3 humedad y D9 CO2 flow PWM.
- [ ] ERC del root schematic = 0 mediante GitHub Actions.

### Migración posterior por bloques

- [ ] Construir hoja analógica/aislamiento desde los circuitos donantes aceptados, eliminando funciones fuera de Insight.
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
- [ ] Z1 analógico/aislamiento con conectores de campo directamente debajo de sus front-end.
- [ ] Z2 digital/bajo ruido.
- [ ] Z3 potencia con loops de conmutación minimizados.
- [ ] Z4 actuadores/potencia ruidosa en el extremo `+X`.
- [ ] Todos los conectores de campo alineados sobre `Y=0` y orientados hacia `-Y` cuando sea mecánicamente posible.
- [ ] Revisión mecánica 3D antes del routing.
- [ ] Congelar ancho final de la board a partir del placement real.

## Fase 5 — Routing

- [ ] Preservar plano de referencia continuo para señales sensibles.
- [ ] Prioridad de routing manual: pH/ORP/DO → clock/I2C/HX711 → potencia → actuadores.
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
- [ ] Validación de ruido y aislamiento de pH/ORP/DO.
- [ ] Prueba HX711/celda de carga.
- [ ] Verificaciones funcionales HMI/GPS/RTC/I2C.
- [ ] Pruebas de control de bomba/solenoide/chiller con cargas representativas.
- [ ] Prueba de watchdog/failsafe.
- [ ] Fixture HIL y procedimiento repetible de prueba de producción.
