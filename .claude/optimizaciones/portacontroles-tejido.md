# Portacontroles_Tejido (**generador propio**, `generadores/portacontroles_tejido.py`, de foto)

Archivo: `own design 3d/Pruebas de productos/Portacontroles_Tejido.3mf` (laminado, 3 por plato),
más `.png` y `.stl`.

Sale de una foto de referencia (10-23): caja terracota de esquinas redondas, alta a la
izquierda y baja a la derecha, con textura de costillas verticales y cuentas que se abultan
en bandas onduladas, como tejido.

## Geometría (v1 aprobada para laminar, 10-23)
- Planta: rectángulo de 126 × 72.5 (128.4 × 74.9 con relieve), esquinas de 8 mm. Con 22 la
  esquina se comía el fondo del hueco del celular.
- Borde en diagonal recta de 105 → 60 mm (del 18 % al 82 % del largo), con un redondeo
  parabólico de ±14 mm en cada quiebre. La curva en S de la foto se cambió a diagonal a
  pedido del usuario.
- Textura: 137 costillas (paso ~2.8), cuentas cada 2.8 mm, bandas de 30 mm que giran 4
  veces al dar la vuelta. Relieve de 0–1.2 mm, solo por fuera; el valle mide 1.24 (dos
  hilos de 0.62, la regla de la estría). Labio de 2.5 mm y zoclo de 3 mm cerrados a ras.
- 3 compartimentos en fila, de izquierda a derecha: celular 42 × 70, control 38.8 × 70 y
  control 38.8 × 70. Divisores de 2 mm con la cima redonda, 10 mm bajo el borde.
- El piso de cada compartimento sube 8 / 14 / 20 mm (losas que se meten media pared). Hondo
  al centro: 94 / 66 / 40 mm.
- Medidas de lo que va adentro (suposición, modelos comunes, no medidas del usuario):
  celular gordo con funda de ~82 de ancho, recargado en diagonal (42 × 70 dan 81.6); control
  de panza de ~54 × 38; dos controles normales de ladito, de ~26 c/u.

## Iteraciones con el usuario (10-23, todas solo en precheck)
192×97 con fila de enfrente y de atrás → 3 compartimentos, diagonal, 160 → 137 → fondo 90
→ 117 (huecos justos, el del Play de mango) → orden celular/control/control → 109 → 89 →
(el usuario aclaró con dibujo: «largo» = el frente, «ancho» = el fondo) 205×59 («se ve
horrible») → 147×72 → 132×72 → **128×75**. El control de Play (DualSense) quedó fuera:
pide un hueco de ~70 × 110.

## Laminado (CLI Bambu Studio 02.08, P2S, Bambu PLA Basic)
Perfil rápido del Oleaje M embebido: `wall_loops` 1, Arachne, hilos 0.62,
`filter_out_gap_fill` 0, `resolution` 0.05, `infill_combination` 1. Cambios respecto de él:
relleno 0 → **10 %** y techo 3 → **4 capas**, por las losas del piso.

| v | Medidas | Placa de 3 | Por pieza | Peso/pieza | Costo/pieza |
|---|---|---|---|---|---|
| v1 | 128.4 × 74.9 × 105 | 7 h 59 m · 300.2 g | 2 h 40 m | 100.1 g | $33.09 |

Costo = g × 167 $/kg + $16.38 de paquetería. Tiempo de la placa: pared exterior 3.8 h,
sólido interno 1.4 h (divisores y techos de las losas), viajes 1.2 h, relleno 0.7 h.
Como referencia, el portacontroles4espacios v5 da 143.5 g · $40.34.

## Pendiente
- Imprimir: revisar que el valle de la textura salga macizo (una vuelta Arachne en 1.24),
  que las cuentas se lean como en la foto y que el celular y los controles entren.
- Pedir medidas reales de controles gruesos y del celular (ver memoria portacontroles-mas-grande).
