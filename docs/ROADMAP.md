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

- [ ] Importar/crear footprint inmutable del UNO Q rotado en el origen global.
- [ ] Verificar los cuatro agujeros de montaje usando las coordenadas transformadas.
- [ ] Añadir keepouts de USB-C, botón de power, JCTL, SPI/Qwiic y conectores.
- [ ] Crear contorno inicial de la board con `H = 68.58 mm`; ancho provisional.
- [ ] Añadir corredor de courtyards para conectores del lado de servicio/enclosure en `Y=0`.
- [ ] Verificar relación UNO Q + carrier en KiCad 3D Viewer.

## Fase 2 — Migración limpia del esquemático Insight

- [ ] Reconstruir la jerarquía del esquemático V2 en lugar de copiar literalmente la hoja raíz donante.
- [ ] Congelar mapeo A0/A1/A2/A4/A5 de sensores.
- [ ] Congelar D0/D1 HMI, D2/D3 HX711, D4 watchdog, D5-D8 controles de actuadores y D20/D21 I2C.
- [ ] Eliminar canal de humedad de la línea base Insight.
- [ ] Mantener PWM de válvula proporcional de gas fuera de la línea base.
- [ ] Definir mecanismo de expansión RS485/Signature sin congestionar la board Insight.
- [ ] Verificar directamente el contrato de pines contra `Nebula_ArduinoAPPLab_UNOQ`, fuente de verdad del firmware.
- [ ] ERC = 0.

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
