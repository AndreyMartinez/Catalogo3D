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

## 2026-11-24 (v3) — «llegó roto a la persona … más robustas las paredes» y «la curva se vea más parecido» a la foto de ML

Feedback: una pieza llegó rota al cliente aunque viajó en bolsa de burbujas. Se rompió
por la pared alta y las esquinas, por el borde de arriba y por los divisores. Además, la
curva no se parecía a las fotos de MLM3713176381 (renders de 128 × 75 × 105).

Medición de la foto de medidas (perspectiva corregida a ojo): la bajada va del ~14 % al
~64 % del largo, con hombro redondo arriba, la parte más empinada a la mitad y panza
cóncava abajo. El lado bajo mide ~0.58 del alto. La v2 bajaba en línea recta del
18 % al 82 %, por eso se veía floja. El usuario: «la curva se ve más pronunciada en las
fotos». Tamaño (decisión del usuario): se queda la planta de la v2 y se sube el alto
a la proporción de la foto.

Cambios contra v2 (precheck aprobado 11-24):
- Borde `curva` = «s»: medio coseno de 0.14 a 0.64 del largo. La «recta» de v1-v2
  sigue disponible como parámetro.
- Alto 105 → 60 → **120 → 70**; planta 148 → **150**, esquinas 8 → **11**. Exterior
  **152.4 × 92.4 × 120**: cabe en la caja 20×16×11 acostada (92.4 en los 110).
- Pared en el valle 1.24 → **2.4** y `wall_loops` 1 → **2** (4 hilos macizos por lado y
  lado, sin relleno dentro de la pared).
- Labio: engorda **1.6 mm hacia adentro** en los 3 mm de arriba y baja a la pared en 4 mm
  (volado menor a 45°).
- Divisores 2 → **3 mm**, a 4 mm del borde (eran 10), con un **chaflán cóncavo de 3 mm**
  contra la pared.
- Huecos 46 / 47.7 / 47.8 × 87.5 → **46 / 46.6 / 46.6 × 85.2**; hondo 110 / 64 / 48.

Laminado por CLI (Bambu Studio, P2S, placa de 3 con dos en fila y una girada; costo =
g × 180 $/kg + $13.96, `.catalogo3d_costos.json` al 11-24):

| Versión | Placa de 3 | Por pieza | Peso/pieza | Costo/pieza |
|---|---|---|---|---|
| v2 150 × 92 × 105, pared 1.24 | 8 h 55 · 335.3 g | 2 h 58 | 111.8 g | $34.08 |
| **v3 152 × 92 × 120, pared 2.4, curva S** | **13 h 06 · 581.2 g** | **4 h 22** | **193.7 g** | **$48.83** |

Filamento de la v3 por función: pared interior 40 %, pared exterior 38 %, sólido interno
12 %, relleno 3.6 %. El 78 % es pared: el refuerzo es lo que pesa. El estimado antes de
laminar era 165–180 g.

Respaldos: `Portacontroles_Tejido.{3mf,png,stl}.v2.bak`. El `.3mf` del catálogo es el
laminado sin el G-code (`slice_info` 581.19 g, 13 h 06).

## 2026-11-24 (v4) — «¿existe forma de que sea más rápido … y un poquito menos de peso sin perder la calidad?»

Diagnóstico del G-code de la v3: a velocidad nominal la placa saldría en 6.8 h, pero el
estimado de Bambu es 13 h 06. El tiempo lo manda acelerar y frenar en los tramitos de la
textura (165 costillas × 6 puntos por vuelta), no la velocidad. Las paredes ya iban al
tope de flujo (21 mm³/s ÷ 0.62 × 0.2 ≈ 169 mm/s). Palancas: menos capas, menos pared y
más aceleración en la pared exterior.

Variantes laminadas por CLI (placa de 3; costo = g × 180 $/kg + $13.96):

| Variante | Placa de 3 | Por pieza | Peso/pieza | Costo/pieza |
|---|---|---|---|---|
| v3 (pared 2.4, capa 0.20) | 13 h 06 · 581.2 g | 4 h 22 | 193.7 g | $48.83 |
| A: pared 2.0 | 12 h 19 · 541.9 g | 4 h 06 | 180.6 g | $46.47 |
| B: capa 0.24 | 12 h 12 · 590.7 g | 4 h 04 | 196.9 g | $49.40 |
| C: `outer_wall_acceleration` 6000 → 10000 | 12 h 28 · 581.2 g | 4 h 09 | 193.7 g | $48.83 |
| **D = v4: A + B + C (el del catálogo)** | **10 h 43 · 552.4 g** | **3 h 34** | **184.1 g** | **$47.10** |

Cambios contra v3: `valle` 2.4 → **2.0** (sigue con 4 hilos y 2 vueltas; 60 % más que la
v2 que se rompió), `layer_height` 0.20 → **0.24** (una cuenta de 2.8 mm = 12 capas) y
`outer_wall_acceleration` 6000 → **10000** (la textura tapa el eco). Labio, divisores y
chaflanes no cambian. Huecos 46 / 47.4 / 47.4 × 86. Se descartaron la capa de 0.28 y la
pared de 1 sola vuelta: cuestan calidad o resistencia.

Respaldos: `Portacontroles_Tejido.{3mf,png,stl}.v3.bak`. El `.3mf` del catálogo es el
laminado D sin el G-code (`slice_info` 552.43 g, 10 h 43).

## Pendiente
- v4: imprimir y mandarla en la caja con burbuja (prueba de caída); revisar el
  escalón de la capa 0.24 en la curva del borde.
- Publicación MLM3713176381: actualizar las medidas a 15.2 × 9.2 × 12 cm. Las fotos ya
  traen la curva de la v3.
- v2: imprimir y revisar que los techos de las losas no se hundan sobre el relleno rayo y
  que sin elevación en Z la boquilla no raye la textura. Si raya, regresar `z_hop` a 0.4.
- Imprimir: revisar que las cuentas se lean como en la foto y que el celular y los
  controles entren.
- Pedir medidas reales de controles gruesos y del celular (ver memoria portacontroles-mas-grande).
