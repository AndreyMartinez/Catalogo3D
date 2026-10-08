# portalapices10 2 (Parametric Model Maker, 4 piezas)

Archivo: `own design 3d/portalapices10 2.3mf` (backup del original: `.3mf.bak`)
Origen: comprado/paramétrico — "Parametric_Model_Maker" (MakerWorld). Hexágono facetado
(432 caras, un solo mesh compartido), escala no uniforme del usuario 1.0468 × 1.1609 × 1.0631
→ huella 90.65 × 116.09 mm (hexágono con puntas en ±Y), 106.3 mm de alto, cavidad circular
de ~56 × 63 mm. Ya con perfil P2S / plato 256 / Bambu PLA Basic.

## Feedback recibido
- 2026-09-25 — Como en el Loop Remote (que le quedó "1000/10", con textura suave): más rápido,
  mejorar, mismo proceso, y poner las que se puedan en la bandeja.

## Diagnóstico
- Real (cinta original, CLI = 10.06 h ≈ 10.17 h guardado): 4 piezas, 548 g (137 g c/u).
  Sparse infill grid 15% = **4.91 h de 10.06 h (49%)**, porque las paredes son gruesas:
  17 mm en las caras planas y hasta ~30 mm en las esquinas (cavidad Ø56 dentro de un hexágono
  de 90 mm) → casi todo el volumen es relleno.
- Máximo por plato: el hexágono mide 90.65 mm entre caras (mínimo en cualquier orientación),
  así que caben 2 por fila; con 256 mm son 2 filas (3 filas = 290 mm) → **4 es el máximo con
  este tamaño** (búsqueda greedy con rotaciones 0-165°, gap 5-6 mm, no encontró 5). Las 4
  originales estaban en cuadrícula 2×2 con 1 mm de hueco.

## Cambios aplicados (2026-09-25)
- Layout: retícula hexagonal (2 + 2 desplazadas media pieza), hueco 10 mm entre caras:
  centros (52.51, 80.0), (153.16, 80.0), (102.84, 176.0), (203.49, 176.0); solo se
  cambió la traslación X/Y de los 4 `<item>` (misma escala, mismos objetos, sin tocar
  `model_settings.config`). Huella total 241.6 × 212.1 mm (margen ~7 / ~22 mm). Verificado con el
  rebanador (CLI, `--arrange 0`): 4 objetos en un plato.
- Perfil (`different_settings_to_system` con las 5 claves): `sparse_infill_pattern`
  grid→**adaptivecubic**, `sparse_infill_density` 15%→**8%**, `layer_height` 0.20→**0.16**
  (mejor acabado en las facetas inclinadas), `top_shell_layers` 5→7 y `bottom_shell_layers`
  3→5 (mismo grosor sólido en mm con capas más finas).
- Quitados `plate_1.gcode`/`.md5` (rebanado viejo).

## Resultado (rebanado CLI, 4 piezas)
| Perfil | Tiempo | Peso est.* |
|---|---|---|
| Original (0.20, grid 15%) | 10.06 h | ~548 g |
| adaptive cubic 8%, 0.20 | 6.94 h | ~376 g |
| **adaptive cubic 8%, 0.16 (aplicado)** | **8.59 h (−15%)** | **~387 g (−29%)** |
| lightning 10%, 0.16 (descartado) | 6.06 h | ~257 g |
*suma de E del gcode calibrada ×0.97 contra los 548 g reales.
- `adaptive_layer_height` no lo aplica el CLI (mismo resultado que 0.20); si se quiere, activarlo
  en Bambu Studio.

## Pendiente / conocido y no resuelto
- Falta que el usuario rebane e imprima: confirmar tiempo (~8.6 h), gramaje (~390 g las 4) y
  acabado.
- Opción no aplicada: **6 piezas** en el plato reduciendo el largo (Y) ~20% (escala Y
  1.16→~0.93; 3 filas × 2). No se hizo porque cambia las proporciones que el usuario escogió.
- `lightning` bajaría a ~65 g/pieza y 1.5 h/pieza pero deja las paredes de 17-30 mm casi
  huecas.
