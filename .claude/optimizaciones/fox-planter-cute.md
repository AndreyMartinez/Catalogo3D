# fox_planter_cute (Cute Fox Planter, comprado, MakerWorld — Doxico)

Archivo original: `~/Downloads/fox_planter_cute.3mf` (sin tocar). Un objeto,
malla de 478 720 caras, 89.4×100×89.8 mm a escala 1; venía a ×1.2 en perfil
P2S (0.2 mm, 2 paredes, 15 %, sin soporte; el diseñador recomienda soporte).

## Feedback recibido
- 2026-10-15 — Varias copias como maceta de regalo en la A1 mini, ~25 g c/u.

## Cambios (v1, 2026-10-15)
- Perfil de proceso completo del donante `3 MACETAS.3mf` (A1 mini, placa
  180×180, 0.16 mm High Quality, 2 paredes, gyroid 10 %, soporte árbol auto,
  Generic PLA @BBL A1M). Las claves tocadas van a `different_settings_to_system`.
- Escala uniforme en los 3 ejes, rejilla centrada con 5 mm entre piezas;
  `model_settings.config` sincronizado (un `model_instance` y un
  `assemble_item` por copia, `identify_id` 600+).
- Miniatura `plate_1.png` regenerada con `--export-png 1 --camera-view 0`
  (isométrica). Ojo: `--export-3mf` NO regenera `plate_1.png`, solo `top_1.png`.

## Variantes laminadas con el CLI (medido)

| Variante | Copias | Escala | Tamaño c/u | g c/u | Placa | Filamento c/u (167 $/kg) |
|---|---|---|---|---|---|---|
| **6x (elegida)** | 3×2 | 0.615 | 55×61.5×55 mm | **24.5** | 147.2 g · 8 h 41 | $4.09 |
| 9x | 3×3 | 0.55 | 49×55×49 mm | 18.9 | 169.7 g · 10 h 22 | $3.15 |
| 9x relleno 15 % | 3×3 | 0.55 | 49×55×49 mm | 19.7 | 176.9 g · 11 h 03 | $3.29 |
| 4x | 2×2 | 0.70 | 62.6×70×62.9 mm | 32.8 ✗ | 131.4 g · 7 h 32 | $5.48 |

- 0.55 es el tope para 3×3 (3·100·s + 10 ≤ 176) y 0.619 para 3 columnas.
- El peso escala ~s^2.4 (pieza dominada por cascarón), no s³.
- Salidas: `~/Downloads/fox_planter_6x_a1mini.3mf` y `fox_planter_9x_a1mini.3mf`.

## Pendiente
- Imprimir la 6x y confirmar que el soporte árbol bajo cabeza/cola sale limpio.
