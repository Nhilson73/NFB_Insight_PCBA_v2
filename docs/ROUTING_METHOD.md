# Método de routing por lotes

El routing se ejecuta de menor a mayor acoplamiento físico:

1. 28 nets locales.
2. 4 nets analógicas inter-zona.
3. 16 nets digital/control inter-zona.
4. 10 nets de potencia + actuadores.
5. GND como plano continuo In1 + stitching.

Cada lote parte del `main` verde del lote anterior y solo se mergea completo. Los intentos exploratorios viven fuera de `main`.
