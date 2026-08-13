# Gates de merge por lote de routing

| Lote | Nets | Gate mínimo |
|---|---:|---|
| PR19A | 28 | 28/28 conectadas, 0 nets futuras tocadas, 0 shorts/clearance/courtyard nuevos |
| PR19B | 4 | 4/4 analógicas inter-zona + revisión visual de corredor/retorno |
| PR19C | 16 | 16/16 digital/control + calidad geométrica long-haul |
| PR20A | 10 | 10/10 potencia/actuadores + revisión de trayectoria de corriente |
| PR20B | 1 | GND plano In1 + stitching + revisión de retornos |

Regla universal: **ALL_OR_NOTHING**. Un lote parcialmente conectado nunca se mergea.
