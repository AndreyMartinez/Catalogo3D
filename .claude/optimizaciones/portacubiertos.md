# portacubiertos (3 compartimentos con estría vertical)

Archivo: `own design 3d/Porta controles/portacubiertos.3mf`
Origen: comprado/generado — MakerLab «Parametric Model Maker» v1.0
(DesignModelId FMI_178465675817580860). Malla de fábrica 190 × 100 × 122 mm.

## Feedback recibido
- 2026-11-16 — «Puedes hacer este más grande y optimizarlo porque tarda demasiado tiempo»
  (tarjeta: 147.0 g ✎, $37.33, +$37.67).

## Diagnóstico
- Malla (escala 1): rectángulo redondeado 190×100 con estría de media caña r 2 mm
  cada ~6.57 mm solo por fuera; 3 huecos 58×92 r 20 lisos por dentro; pared 4 mm
  en lo plano y 2 mm en el fondo del surco; divisores 4 mm; piso 4 mm con 6
  agujeros Ø6; labio liso de z 51 a 61 con canto redondo de 2 mm.
- v0 en el catálogo: 3 por plato a ×0.744 (141 × 74 × 91), perfil 0.20 Standard
  P2S, Bambu PLA Basic, `resolution` 0.012, 2 paredes clásicas, grid 15 %.
- CLI v0: plato de 3 **17 h 58 m / 443.3 g** → 6 h 00 y 147.8 g por pieza (cuadra
  con los 147 g de la tarjeta).
- Por qué tarda: la suma nominal del recorrido da 6.4 h por plato, el CLI 18 h. La
  pared exterior va en tramos de 0.9 mm y la impresora nunca llega a velocidad; la
  pared de 1.5–3 mm entre surco y hueco liso se rellenaba con ~190 mil trazos de
  gap infill y relleno sólido y ~5 100 retracciones por pieza.
- Costo: material + paquetería «Paquetería» $13.96 (precio_kg 159, del
  `.catalogo3d_costos.json` del catálogo).

## 2026-11-16 (v1) — «hazlo más grande y optimízalo porque tarda demasiado»

Cambios v0 → v1:
- Escala ×0.744 parejo → **×0.93 en X/Y y ×0.85 en Z: 176.7 × 93.0 × 103.7 mm**
  (cabe en la caja 20×16×11; compartimentos ~54 × 86 mm). Traslación Z recalculada
  (base en 0).
- Huecos abiertos hacia afuera en la malla para que el fondo del surco mida dos
  hilos (1.24 mm reales) y los divisores 1.24 mm. La estría, el labio y el piso con
  agujeros no cambian. La tapa de arriba (z 61) se volvió a triangular con
  earcut: sus abanicos largos se volteaban al mover los huecos (8 caras).
- Receta rápida del Oleaje M en `project_settings.config` y en
  `different_settings_to_system`: `wall_loops` 1, `wall_generator` arachne,
  `outer/inner_wall_line_width` 0.62, `filter_out_gap_fill` 0, `resolution` 0.05,
  `sparse_infill_density` 0 %, `top_shell_layers` 3, `infill_combination` 1,
  `retraction_minimum_travel` 3, `z_hop` 0.
- Plato de 3 → **2** (a 93 mm de fondo no caben 3).
- Capa del G-code revisada a z 50: el hilo de afuera sigue la estría y se pega al
  liso de adentro en el fondo de cada surco; entre surcos queda un hueco cerrado.

Variantes laminadas por CLI:

| Variante | Medidas | Plato | Tiempo/pieza | g/pieza | $/pieza |
|---|---|---|---|---|---|
| v0 (fábrica del catálogo) | 141 × 74 × 91 | 3 · 17 h 58 | 6 h 00 | 147.8 | $37.33 |
| solo receta rápida, mismo tamaño | 141 × 74 × 91 | 1 | 2 h 16 | 94.5 | — (surco sin pegar: dos cáscaras) |
| receta + huecos abiertos, mismo tamaño | 141 × 74 × 91 | 1 | 2 h 03 | 93.2 | $28.78 |
| A: ×0.81 | 154 × 81 × 99 | 3 · 6 h 53 | 2 h 18 | 110.6 | $31.55 |
| B con divisores 1.86 | 177 × 93 × 104 | 2 · 5 h 36 | 2 h 48 | 135.5 | $35.50 |
| **v1 = B** | **177 × 93 × 104** | **2 · 5 h 31** | **2 h 46** | **136.5** | **$35.66** |

Por pieza contra v0: −3 h 14 m, −11.3 g, −$1.67, y 25 % más grande por lado.
Peso manual de la galería 147.0 → 136.5 g (por pieza). Miniatura regenerada con
`--export-png 1 --camera-view 0`; `slice_info.config` del laminado CLI, sin G-code.
Respaldos: `portacubiertos.3mf.v0.bak` (= `.bak`, el de fábrica).

## 2026-11-17 (v2) — «¿puedes generar 3?»

A 93 mm de fondo no caben 3 en el plato de 256 (3 × 93 = 279). Se dejó el largo
y el alto de la v1 y se bajó solo el fondo, como el Oleaje M (179 × 81, 3 por
plato).

Cambios v1 → v2:
- Escala ×0.93 / ×0.93 / ×0.85 → **×0.93 / ×0.80 / ×0.85: 176.7 × 80.0 × 103.7 mm**.
  Huecos recalculados por eje para que el fondo del surco siga en 1.24 mm
  (compartimentos ~54 × 73 mm; las esquinas r 20 quedan apenas ovaladas).
- Plato de 2 → **3**, 4 mm entre piezas; la extrusión va de Y 4.3 a 251.7.
- Mismo perfil que la v1.

| Versión | Medidas | Plato | Tiempo/pieza | g/pieza | $/pieza |
|---|---|---|---|---|---|
| v1 | 177 × 93 × 104 | 2 · 5 h 31 | 2 h 46 | 136.5 | $35.66 |
| **v2** | **177 × 80 × 104** | **3 · 7 h 43** | **2 h 34** | **124.0** | **$33.68** |

Contra v1: −12 min, −12.5 g y −$1.98 por pieza; contra v0: −3 h 26 m y −$3.65.
Peso manual de la galería 136.5 → 124.0 g. Miniatura regenerada por CLI.
Respaldo: `portacubiertos.3mf.v1.bak`.

Ojo al repetir: el script de variantes leía `portacubiertos.3mf`; desde la v1 hay
que partir de `portacubiertos.3mf.bak` (el de fábrica), si no los huecos no se
mueven («vertices movidos 0»).

## Pendiente / conocido
- Imprimir: revisar que sin elevación en Z la boquilla no raye la pared (si raya,
  `z_hop` 0.4 y dejar `retraction_minimum_travel` 3) y que los divisores de 1.24 mm
  se sientan firmes; si no, 1.86 mm cuesta casi lo mismo (tabla).
- Rebanar en la app de Bambu para confirmar los 2 h 46 / 136.5 g.
- Si tiene publicación en ML, las medidas y fotos siguen siendo las de v0.
