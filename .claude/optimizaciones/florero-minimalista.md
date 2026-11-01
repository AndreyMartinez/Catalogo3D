# Set Florero Minimalista (grande + chico)

Archivo: `own design 3d/Florero Minimalista Set.3mf` (v2, plato de 2 sets).
v1 sigue aparte y sin tocar: `Florero Minimalista Grande 178mm.3mf` (también es la
plantilla de ajustes P2S de 6 generadores, no moverlo ni cambiarle el perfil) y
`Florero Minimalista Pequeño 123mm.3mf`.
Origen: comprado (Designer: SQ4BRT, colección Nordé, MakerWorld; Standard Digital File
License). Una sola malla, `object_1.model` (84.3 × 84.1 × 178 mm, centrada, z −89…89).

## Feedback recibido
- 2026-10-31 — «uno grande que ocupe la caja al máximo que se pueda y uno más pequeño
  de decoración… optimizado y de alta calidad a bajo costo». Caja 20 × 16 × 11 cm.

## Diagnóstico
- Perfil del vaso: base Ø84 que se angosta hasta la boca Ø51 (≈5°). Unas 50 estrías
  redondas de ~1 mm de relieve. En el valle la pared mide ~1.8 mm: los 4 hilos del
  perfil (`wall_loops` 2, Arachne, 0 % relleno) la llenan justo.
- Caja: lo que manda es el largo. Acostado a lo largo, el grande llega a ×1.085
  (193 mm). En diagonal sobre el piso cabe menos (es muy ancho). Se usó ×1.067
  (190 × Ø90) para dejar ~5 mm de burbuja en cada punta. Se supuso que 20 × 16 × 11
  es la medida interior.
- Como se angosta, el chico va acostado al revés junto a la boca del grande. La
  silueta 2D permite hasta ×0.85 (151 mm), pero se dejó en ×0.69 (123 × Ø58, el
  mismo de antes) por costo. Quedan 17 mm entre las dos piezas.
- Costo: 159 $/kg + paquetería $13.96 (una por set).

## 2026-10-31 (v2) — «uno grande que ocupe la caja al máximo… y uno más pequeño de decoración»

Cambios contra v1 (dos archivos sueltos):
- Grande 176 mm (escala rara 0.965/1/0.989) → **190 × Ø90 mm, ×1.067 parejo**.
- Chico ×0.69 sin cambio (123 × Ø58).
- Los dos en un solo archivo, con 2 sets por plato.
- Perfil: `z_hop` 0.4 → **0**, `retraction_minimum_travel` 1 → **3**. Arachne parte la
  pared interior en ~54 pedazos por capa y cada salto hacía retracción, limpieza y
  elevación. Se va de 73 a 31 min de traslados. La pared queda igual (mismo peso y
  mismos hilos).

Variantes laminadas por CLI (1 set salvo donde se indica):

| Versión | Tiempo | Peso | Costo/set | Nota |
|---|---|---|---|---|
| v1 (176 + 123, por separado) | 4 h 04 + 3 h 39 = 7 h 43 | 87.5 + 36.5 = 124 g | $33.68 | `slice_info` de fábrica |
| v2 perfil original | 8 h 04 | 143.2 g | $36.73 | |
| A: `resolution` 0.05 | 6 h 59 | 143.0 g | — | ✗ convierte las estrías redondas en picos |
| B: A + 1 perímetro + `filter_out_gap_fill` 2 | 3 h 37 | 82.3 g | — | ✗ quedan dos cáscaras separadas (pared de 1.8 mm) |
| E: pared clásica | 8 h 21 | 143.3 g | — | ✗ más relleno de huecos y más traslados |
| **C: sin elevación en Z + retracción solo > 3 mm** | **6 h 55** | **143.2 g** | **$36.73** | ✓ |
| C, plato de 2 sets (el del catálogo) | 13 h 43 | 286.4 g | $36.73 | 6 h 51 por set |
| C, plato de 4 sets | 27 h 09 | 572.8 g | $36.73 | 6 h 47 por set: casi no rinde y un fallo tira 27 h |

Cómo se laminó: el CLI lamina el 3MF con el perfil que trae dentro
(`BambuStudio --slice 0 --arrange 0 --export-3mf x.3mf --outputdir <abs>`). Al archivo
del catálogo se le quitó el G-code (215 MB) y se dejó `slice_info.config` y la
miniatura. En la galería lleva peso manual de 143.2 g, por set.

## Pendiente / conocido
- Imprimir y revisar que sin elevación en Z la boquilla no raye la pared y que no haya
  hilos. Si raya, regresar `z_hop` a 0.4 y dejar solo `retraction_minimum_travel` 3.
- Comprobar en la caja real, con burbuja, que el grande de 190 mm entra a lo largo.
- La publicación MLM5431278076 sigue con las medidas y fotos de v1.
