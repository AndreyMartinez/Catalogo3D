# FloreroTorsion (**generador propio**, diseño libre)

Archivo: `own design 3d/floreros/FloreroTorsion.3mf` (+ `.stl`, `.png`).
Origen: `python3 generadores/crear.py libre` — los parámetros completos van
embebidos en el .3mf (`Catalogo3D:parametros`). Se regenera, no se edita el .3mf.

## Pedido
- 2026-10-13 — Florero nuevo con la pared del Portacubiertos_T
  ([portacubiertos-torsion.md](portacubiertos-torsion.md)). Base de producto:
  floreros en par para Full ($256–283, nivel: correlación por pantallazo del 10-08).

## v1 (2026-10-13)

Pared copiada tal cual del portacubiertos: `acabado=torsion`,
`onda_amplitud=0.75`, `onda_paso=16.92`, `pared=1.7`, `pared_forma=sigue`.

Lo que cambia es la silueta y las vueltas:

| Parámetro | Valor | Por qué |
|---|---|---|
| contorno | circulo, 100×100 | florero redondo; panza real 116 mm con el barril |
| alto | 240 mm | el mercado anda en ~25–30 cm (estimado); la P2S da 256 de alto |
| torsion_vueltas | 0.26 | `vueltas` es fracción del contorno por alto total. El portacubiertos corre 0.1 × 367 mm = 37 mm en 102 mm (hélice de ~20°); para el mismo ángulo en 240 mm y contorno de ~330 mm hacen falta 0.26 |
| perfil | barril 0.15 | panza suave, menos que el 0.22 del portacubiertos |
| cuello | suave, boca 0.55, hombro 0.70 | boca ~64 mm; cierra a ~20° de la vertical, sin soporte |
| acabado_desvanece | 12 mm | la torsión llega sin amortiguar a la boca y la muerde |
| base_redondeo | 10 mm | el canto de abajo |
| piso / ranuras / drenaje | 2.0 / 1 / 0 | florero de flor seca, sin agujero |

Motor: 116.3×116.4×240 mm, 19 estrías, 177 g, 790k triángulos, malla cerrada.
Aviso: el grano pedido (0.4) se relajó a **0.9 mm** por presupuesto de malla;
en el render no se ve escalonado. Si se ve en la impresión: subir `onda_paso`
o bajar las vueltas (cambia el ángulo de la hélice).

### Laminado (CLI Bambu Studio, P2S 0.4 + Bambu PLA Basic, 1 pieza)

| Perfil | Tiempo | Peso | Costo* |
|---|---|---|---|
| 0.16 mm, 4 perímetros, 5 % (el del Portacubiertos_T) | **3 h 57** | 171.5 g | $45.54 |
| 0.20 mm Standard (2 perímetros) | 2 h 57 | 168.9 g | $45.09 |

\* `.catalogo3d_costos.json` al 10-13: 170 $/kg + paquetería $16.38.
El par con una sola paquetería saldría en ~$74.7 (suposición: una caja por par).

Caben 4 en el plato (Ø116: 2×2 con 7 mm entre piezas = 239 mm). No se armó el plato.

Cómo se laminó: los perfiles del sistema heredan (`inherits`) y el CLI no los
resuelve solo, así que se aplanó la cadena de herencia de
`system/BBL/{machine,process,filament}` a JSON sueltos y se pasaron con
`--load-settings "maquina.json;proceso.json" --load-filaments pla.json
--slice 0 --arrange 0 --outputdir <abs>`.

## Cinco propuestas de silueta (2026-10-13)

Pedidas por el usuario tras ver la v1. Misma pared; `torsion_vueltas` ajustado
en cada una a hélice de ~20° (`vueltas ≈ alto·tan20° / contorno`). Archivos en
`own design 3d/floreros/propuestas-torsion/` (+ `_comparativa.png`).
CLI con el perfil 0.16 / 4 perímetros, 1 pieza:

| # | Silueta | Claves | Medidas (mm) | Tiempo | Peso | Costo |
|---|---|---|---|---|---|---|
| 1 | Botella | recto, cuello suave boca 0.38 hombro 0.45, v 0.25 | 111.5×111.5×240 | 4 h 23 | 158.2 g | $43.28 |
| 2 | Tubo esbelto | Ø80, recto, sin cuello, v 0.35 | 81.5×81.5×245 | 2 h 55 | 133.4 g | $39.06 |
| 3 | Panzón bajo | Ø132, barril 0.22, cuello suave 0.6, v 0.15 | 162.3×162.3×165 | 4 h 20 | 175.6 g | $46.23 |
| 4 | Cintura | Ø110, cintura 0.2, sin cuello, v 0.24 | 110×110×230 | 3 h 36 | 159.6 g | $43.51 |
| 5 | Almohada | óvalo 140×70, barril 0.15, cuello suave 0.7, v 0.24 | 162.3×82×220 | 4 h 14 | 185.7 g | $47.96 |

Descartado en el camino: botella con `cuello=botella` (hombro 0.72 → 73°;
hombro 0.45 → 56°): ambas piden soporte. Con `cuello=suave` y hombro 0.45 no.
Panzón a Ø150/barril 0.25 salía 189 mm de ancho y 220 g: se bajó a Ø132.

### Pendiente
- Que el usuario elija silueta(s) / el par.
- Variante para el par (¿dos alturas o dos iguales?).
- Plato de 2 o 4, perfil embebido, e imprimir.
