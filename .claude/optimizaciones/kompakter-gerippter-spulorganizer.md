# kompakter_gerippter_Spülorganizer (organizador de fregadero estriado)

Archivo: `own design 3d/kompakter_gerippter_Spülorganizer.3mf`
Origen: comprado (Designer: MOLKAMP, MakerWorld «Compact Ribbed Sink Organizer
with Drain Tray», perfil «Small», Standard Digital File License).
Dos objetos: cuerpo (vaso redondo Ø65 interior + compartimento trasero en
estadio + charola de esponja al frente) y rejilla 134×59×2.8 que va en la charola.
Publicación: MLM3652662461 a $209 (ficha en `.claude/productos/fregadero-esponja.md`).

## Feedback recibido
- 2026-10-25 — «optimizar este producto y que quepa en la caja» (20×16×11).
- 2026-10-25 — «que se vean más líneas japandi».

## Diagnóstico
- Original 152×151.3×**140** mm: la base cabe en el piso de la caja, sobra la
  altura. Escala uniforme cabría a ×0.786 plano o ×0.814 inclinado (casco
  convexo + rotación 3D): encoge charola y vaso, descartado.
- La malla no tiene **ningún vértice entre z 10.2–70 ni 80–130** y todas las
  caras que cruzan esas franjas son verticales (|nz| < 4e-5): son prismas
  rectos (estrías verticales). Se comprimen en Z sin deformar bordes, piso,
  charola ni el redondeo de los labios.
- Estrías originales: canal plano 1 mm de hondo × ~3 mm, cada ~10 mm (47 en el
  contorno, 28 en el vaso, más unas por dentro del compartimento sobre la cara
  del vaso). Pared 6 mm (r 32.5 → 38.5 en el vaso). Empiezan en z 10.0/10.2 y
  terminan 10 mm bajo cada labio (compartimento z 70, vaso z 130).
- Costo: 167 $/kg + paquetería $16.38.

## Cambios aplicados

### 2026-10-25 (v2) — «que quepa en la caja» + «más líneas japandi»
- Altura 140 → **105**, compresión proporcional de las dos franjas prisma
  (59.8 → 40.74 y 50 → 34.06): vaso 105, compartimento trasero 80 → 61. Se
  ofreció también «solo bajar el vaso» (trasero a 80); se eligió la proporcional.
- Estrías rehechas: relleno de las viejas con una banda 0.02 mm por dentro de la
  superficie (sin caras coincidentes) y 109 cortes cilíndricos r 1.5 centrados
  en el contorno, **cada 4.65 mm, 1.5 mm de hondo** (52 alrededor del vaso,
  57 en rectas + arco derecho del estadio); mismas bandas lisas de 10 mm.
- Perfil sin cambios (0.20 Standard P2S, 2 paredes, gyroid 5 %, PLA Matte).
- Malla: cerrada, orientada, género 0, 7 triángulos degenerados del booleano
  (Bambu los repara). Transform z 70 → 52.5 (base en el plato).
- Respaldo: `.3mf.v1.bak` (= `.3mf.bak`, de fábrica).

| | v1 (original) | v2 |
|---|---|---|
| Medidas | 152×151×140 | 152×151×105 |
| Tiempo (CLI) | 5 h 08 | **4 h 13** |
| Peso (CLI, juego con rejilla) | 213.3 g | **178.0 g** |
| Costo | $52.00 | **$46.11** |

Método (scripts en el scratchpad de la sesión, no versionados por usar
manifold3d/shapely): comprimir primero y cortar después — si se corta antes, el
booleano mete vértices a media pared (cruce con diagonales de los quads largos)
y la compresión ya no es exacta.

## Resultado real
- (pendiente: rebanar en la app e imprimir)

## Pendiente / conocido y no resuelto
- Confirmar las medidas 20×16×11: si son exteriores, bajar a 100 mm.
- La miniatura del .3mf sigue siendo la del original hasta que se guarde en Bambu.
- Pared exterior 91 → 70 min pese a las estrías densas (manda la altura).
