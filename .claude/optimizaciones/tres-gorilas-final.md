# Final — Three Wise Monkeys Gorilla Figurines (3 gorilas)

Archivo: `~/Downloads/Final.3mf` (original intacto, sin laminar en la galería).
Origen: comprado — "Three Wise Monkeys Gorilla Figurines Sets", UKJ Studio,
MakerWorld (Standard Digital File License). Tres objetos: `mouth.stl` (no hablar),
`eyes.stl` (no ver), `ear.stl` (no oír), ~930k caras cada uno.
Perfil del archivo: A1 mini, capa 0.2, 2 paredes, relleno grid 10 %, soporte árbol.

## Feedback recibido
- 2026-10-15 — Dejar las 3 figuras en un tamaño de ~200 g (los 3 juntos) que
  quepan sin problema en una caja de 20×16×11 cm.

## Diagnóstico
- A 60 mm de alto: huella mínima (rectángulo girado) hablar 46.7×45.9, ver
  42.5×49.2, oír 40.9×52.9 mm; volumen sólido ~54 cm³ c/u. 56.1 g los 3.
- En la caja manda la **altura** (110 mm), no la planta: ver + oír lado a lado en
  el lado de 16 cm y hablar junto a ellos en el de 20 cm deja holgura hasta ~100 mm.
- Peso contra alto no es k³ (las paredes escalan k²): exponente medido ~2.4.

## Cambios aplicados
- 2026-10-15: escala uniforme ×1.6667 → **100 mm de alto**, base a z=0, posiciones
  en la placa A1 mini recalculadas, `assemble_item` de `model_settings.config`
  escalados igual. Guardado como `~/Downloads/Final_100mm.3mf`.
- 2026-10-15: alternativa ×1.5833 → 95 mm + `sparse_infill_density` 10→15 %, para
  dejar 15 mm de holgura vertical. `~/Downloads/Final_95mm_relleno15.3mf`.
- La miniatura del plato no se regeneró (sigue la de 60 mm).

## Resultados (CLI Bambu Studio, los 3 en una placa A1 mini)

| Alto | Relleno | Peso | Tiempo | Costo (167 $/kg + $16.38) |
|---|---|---|---|---|
| 60 mm (original) | 10 % | 56.1 g | 2.0 h | — |
| 85 mm | 10 % | 130.8 g | 3.9 h | — |
| 90 mm | 10 % | 150.3 g | 4.3 h | — |
| 95 mm | 10 % | 172.0 g | 4.8 h | — |
| **100 mm** | 10 % | **195.6 g** | 4.9 h | $49.05 |
| 95 mm | 15 % | 207.6 g | 5.4 h | $51.05 |
| 95 mm | 20 % | 243.0 g | 6.1 h | — |

A 100 mm en la caja: 139 mm de 160 (ver + oír), 166 mm de 200 (+ hablar), 100 de
110 de alto. Si 20×16×11 es medida exterior, usar la de 95 mm.

## Estado
- 2026-10-15: el usuario abrió la de 100 mm en Bambu Studio y la aprobó. Falta
  imprimir y probar en la caja.
