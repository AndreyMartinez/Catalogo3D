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

## 2026-11-16 (v2) — «Puedes hacer estos más anchos y largos y optimizarlos»

Feedback sobre la tarjeta (placa de 3, 300.2 g). Contexto: MLM3713176381 lleva 1 venta
en W44–W45 (medido, «nueva»), y la queja de la familia son los controles gruesos que no
caben (memoria portacontroles-mas-grande).

Cambios contra v1 (precheck aprobado 11-16):
- Planta 126 × 72.5 → **148 × 90** (con relieve 128.4 × 74.9 → **150.4 × 92.4**); alto
  igual 105 → 60, por la caja 20×16×11 (cabe).
- Huecos 42 / 38.8 / 38.8 × 70 → **46 / 47.7 / 47.8 × 87.5**; hondo 94 / 67 / 40.
- Plato: 3 en fila ya no caben (3 × 92.4 + 14 > 256). Ahora van **dos en fila y la
  tercera girada 90° a un lado** (150.4 + 7 + 92.4 = 249.8). `acomodo()` en el generador
  escoge solo: en fila si cabe, si no en L.
- Perfil: `z_hop` 0.4 → **0**, `retraction_minimum_travel` 1 → **3** (como el florero
  minimalista) y `sparse_infill_pattern` grid → **lightning**: el relleno solo sostiene
  los techos de las losas del piso, que era el 23 % del filamento.

Variantes laminadas por CLI (Bambu Studio, placa de 3; costo = g × 198 $/kg + $13.96,
valores de `.catalogo3d_costos.json` al 11-16):

| Versión | Placa de 3 | Por pieza | Peso/pieza | Costo/pieza |
|---|---|---|---|---|
| v1 128 × 75 | 7 h 59 · 300.2 g | 2 h 40 | 100.1 g | $33.78 (era $33.09 con 167 + 16.38) |
| v2-A: 150 × 92, perfil v1 | 9 h 56 · 391.3 g | 3 h 18 | 130.4 g | $39.78 |
| v2-B: A + sin z_hop + retracción > 3 mm | 9 h 32 · 391.3 g | 3 h 10 | 130.4 g | $39.78 |
| **v2-C: B + relleno rayo (el del catálogo)** | **8 h 55 · 335.3 g** | **2 h 58** | **111.8 g** | **$36.09** |
| v2-E: C + divisores 1.24 | 8 h 58 · 338.2 g | 2 h 59 | 112.7 g | $36.28 ✗ no ahorra |

Desglose de B por gramos: pared exterior 44 %, relleno 23 %, sólido interno 21 % (techos
de losas y divisores). El estimado antes de laminar era 115–125 g; A salió 130 g por las
losas, que crecieron con el área del piso (×1.39).

Respaldos: `Portacontroles_Tejido.{3mf,png,stl}.v1.bak`. El `.3mf` del catálogo es el
laminado C sin el G-code (`slice_info` 335.26 g, 8 h 55): la tarjeta muestra la placa
de 3.

## Pendiente
- v2: imprimir y revisar que los techos de las losas no se hundan sobre el relleno rayo y
  que sin elevación en Z la boquilla no raye la textura. Si raya, regresar `z_hop` a 0.4.
- Fotos y medidas de la publicación MLM3713176381 siguen siendo de la v1.
- Imprimir: revisar que el valle de la textura salga macizo (una vuelta Arachne en 1.24),
  que las cuentas se lean como en la foto y que el celular y los controles entren.
- Pedir medidas reales de controles gruesos y del celular (ver memoria portacontroles-mas-grande).
