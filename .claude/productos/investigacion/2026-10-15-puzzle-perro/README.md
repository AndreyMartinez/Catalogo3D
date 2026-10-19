# Puzzle de comida para perro — Ondas en óvalo

Diseño del 2026-10-15, salido de la investigación
[`2026-10-15-comedero-juego-gato.md`](../2026-10-15-comedero-juego-gato.md).
El usuario pidió un puzzle para perro «liso, elegante, minimalista, que se vea
caro» y que quepa en una caja de 200 × 160 × 110 mm.

Dato de mercado: Amazon México, «Juguetes de rompecabezas para perro», $199,
«200+ comprados el mes pasado» (553 calificaciones); ML, Kong Wobbler +500 a
$549 — *medido* (señal de venta pública, no ventas propias).

## Ronda 1 — tres conceptos (disco Ø230 × 24, una pieza)

| Concepto | Laminado (P2S, 0.2 mm, 12 %) | Render |
|---|---|---|
| Ondas: anillos concéntricos, más altos al centro | 186 g · 3.7 h | `r1-ondas.png` |
| Pétalos: roseta de 11 crestas con foso | 190 g · 4.0 h | `r1-petalos.png` |
| Guijarros: domos en filotaxis | 173 g · 3.6 h | `r1-guijarros.png` |

Elegido: **Ondas** (una sola idea de forma; los guijarros se leían como juguete).

## Ronda 2 — óvalo partido en dos

- Óvalo 246 × 186 × 24 mm (los anillos siguen el contorno), partido por el eje
  corto en dos mitades: 132 × 186 y 123 × 186. Apiladas: 186 × 132 × 48 mm,
  caben en la caja.
- Unión: 3 colas de milano verticales (cuello 10, cabeza 16, hondo 9 mm,
  holgura 0.30 mm total). Se arma bajando una mitad sobre la otra; sin soporte.
- Piso de los valles de 3 → 5 mm para que las lengüetas no queden frágiles.
- Las dos mitades en una placa, armadas, abiertas 12 mm y giradas 45°
  (226.6 × 226.6 mm): **174 g · 3.8 h** por juego.
- Tira de prueba de la unión: 12 g · 22 min. **Pendiente: imprimirla** y
  ajustar la holgura (0.4 si aprieta, 0.2 si baila).

Renders: `r2-ovalo-armado.png`, `r2-ovalo-separado.png`, `r2-prueba-union.png`.

## Cómo se genera

Scripts en `generadores/` (copia de trabajo principal, sin versionar):
`puzzle_perro.py` (conceptos de disco) y `puzzle_ovalo.py` (óvalo en dos
mitades y `--prueba` para la tira). Solo biblioteca estándar.

## Pendiente

1. Resultado de la tira de prueba → holgura definitiva.
2. Rangos de capa de 0.12 mm en el relieve para que lo liso no escalone.
3. Material PETG; leyenda «solo croqueta seca, lavar a mano», sin promesa
   sanitaria (`limites-de-diseno.md`: contacto con comida en rojo).
4. Confirmar tamaño de perro y de croqueta (fija ancho y hondura de los valles).
