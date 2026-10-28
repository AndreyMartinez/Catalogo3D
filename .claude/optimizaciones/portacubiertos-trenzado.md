# Portacubiertos Trenzado

Archivo: `own design 3d/Pruebas de productos/Portacubiertos_Trenzado.3mf` (+ `.png`, `.stl`)
Origen: **generador propio**, `generadores/portacubiertos_trenzado.py`, a partir de una
foto de referencia (10-22): tres vasos color nogal de costillas en espiral, caladas,
dentro de una bandeja beige. Desde la v10: 2 vasos + bandeja (`--vasos 3` rehace el de la foto).

    python3 generadores/portacubiertos_trenzado.py --salida "<carpeta>"

Los parámetros completos van dentro del .3mf (`Catalogo3D:parametros`).

## Forma aprobada (v7, 10-22; v8 igual)
- **Vaso de huevo** 80 × 100 mm: radio 31 en el piso, 40 en la panza (46 % del alto),
  29 en la boca. 14 costillas de cordón a 35° (suben a la izquierda vistas de frente),
  sobresalen 5 mm, cáscara de 2.4 mm que sigue la panza; rendijas caladas de 2.2 mm
  (perpendiculares). Zócalo macizo de 6 mm, aro de 3 mm en la boca, piso de 1.6 con
  4 agujeros de drenaje de 4 mm.
- **Bandeja** 252 × 89 × 65 mm: frente y espalda **rectos** por fuera (sin cinturas),
  borde recto que baja en S de 65 mm atrás a 32 mm al frente, pared de 4.5 con labio
  de medio círculo y orilla de abajo suavizada. Por dentro abraza cada vaso a 0.8 mm
  hasta la panza (huevera) y de ahí sube derecha para que el vaso entre. Costillitas de
  1.5 mm en el piso para que el vaso no se quede en el agua.
- Vasos a 0.6 mm entre sí en la panza. Sin soportes (curva más inclinada ~20°).
- Juego: 252 × 89 × 103 mm. Cabe justo en el plato del P2S (256).

## Feedback recibido
- 10-22 — «Puedes generar este diseño de portacubiertos» (foto).
- 10-22 — «la base es de un lado más grande y del otro más chico; los vasos más ovales,
  gorditos y pegados casi rozando» → barril, separación 0.6, bandeja alta atrás.
- 10-22 — pared funcional: dejar las rendijas como están; drenaje sí (sin preferencia
  explícita, se aplicó lo recomendado).
- 10-22 — «el plato atrás más alto, al frente más bajo… armonía; las paredes del vaso
  más anchas y en forma de huevo» → costillas de cordón, labio redondo.
- 10-22 — «más huevo, más anchos que altos, pegado a su vaso, pared más alta» → 80 mm
  (tope del plato P2S), bandeja huevera.
- 10-22 — «no me gustan las curvas en cada cintura del frente» → borde y frente rectos;
  «atrás de la misma forma y más alta» → espalda recta a 65 mm. Aprobada («de maravilla»).

## v8 (10-23) — laminado real, bandeja al 10 % y retracciones de los vasos
Forma **sin cambios** (la v7 aprobada). Respaldo: `Portacubiertos_Trenzado.{3mf,png,stl}.v7.bak`.

- El script ahora **embebe los ajustes de laminado** (`embeber_ajustes`): copia el
  `project_settings` del florero (`General_Vases_print_profile(5).3mf`: P2S 0.4,
  0.20 Standard, Bambu PLA Basic), regresa relleno 15 % y 5 capas de techo a los de
  fábrica, deja Arachne, `resolution` 0.05 e `infill_combination` 1, y declara el .3mf
  de Bambu Studio (metadato Application). Por objeto (`POR_OBJETO`): bandeja al 10 %.
- **El peso de la v7 estaba mal estimado.** Los 326 g eran la malla maciza; laminada al
  15 % la bandeja pesa **124.9 g**. Casi todo ese relleno está en las paredes de 4.5 mm,
  no en las cinturas.
- **Cinturas huecas: probado y descartado.** Se hizo la cavidad cerrada (pared 1.8 mm,
  techo de tienda ≤45°, 0 aristas sueltas): **132.8 g, 2 h 32** — más pesada y lenta,
  porque el relleno al 15 % ya dejaba las cinturas huecas y la cavidad agrega 2+2
  perímetros alrededor. Con pared de 1.0: 118.2 g pero 2 h 20. Se quitó el código.
  El usuario eligió «sin hueco, relleno 10 %».
- **Retracciones de los vasos**: 14 islas por vaso por capa, ~3.5 retracciones por
  costilla (pared interior → exterior → relleno sólido). `retraction_minimum_travel`
  1 → 5 mm: ya no retrae dentro de la costilla. 24 317 → 15 606 retracciones por vaso,
  2 h 45 → 2 h 29. El plato completo: 75 966 → 48 919.

Bandeja sola (CLI):

| Variante | Tiempo | Peso |
|---|---|---|
| v7 maciza, relleno 15 % grid | 2 h 10 | 124.9 g |
| Cinturas huecas, pared 1.8 | 2 h 32 | 132.8 g |
| Cinturas huecas, pared 1.0 | 2 h 20 | 118.2 g |
| Cinturas huecas 1.0 + relleno 10 % | 2 h 14 | 114.3 g |
| **Maciza, relleno 10 % (elegida)** | **1 h 58** | **115.1 g** |
| Maciza, relleno 8 % | 1 h 55 | 109.7 g |
| Maciza, gyroid 10 % | 1 h 58 | 114.5 g |
| Maciza, lightning 15 % | 1 h 35 | 88.4 g (paredes de 4.5 quedan como dos pieles sueltas) |
| Lightning + 3 perímetros | 1 h 53 | 116.0 g |

Vaso solo (CLI), 54.5 g en todas salvo las de 3 perímetros (55.3 g):

| Variante | Tiempo | Retracciones |
|---|---|---|
| v7 (retracción mín. 1 mm, z-hop 0.4) | 2 h 45 | 24 317 |
| 3 perímetros | 3 h 07 | 31 149 |
| aceleración de trayecto corto 2000 | 2 h 45 | 24 317 |
| retracción mín. 3 mm | 2 h 36 | 18 534 |
| **retracción mín. 5 mm (elegida)** | **2 h 29** | **15 606** |
| retracción mín. 5 + z-hop 0.2 | 2 h 24 | 15 606 |
| retracción mín. 5 + sin z-hop | 2 h 12 | 15 606 |
| z-hop en espiral | 3 h 01 | 24 317 |

Juego completo (3 vasos + bandeja, un plato P2S), costo = g × 167 $/kg + paquetería $16.38:

| Versión | Tiempo | Peso | Costo |
|---|---|---|---|
| v7 (perfil embebido, sin cambios) | 10 h 33 | 288.4 g | $64.53 |
| **v8** | **9 h 31** | **278.5 g** | **$62.89** |

## v9 (10-23) — costillas con relleno ligero
Pedido: «Puedes bajar el costo esta un poco alto». Forma sin cambios. Respaldo: `.v8.bak`.

Cada costilla (cáscara de 2.4 mm) tiene por dentro menos de 15 mm² y el laminador la
llenaba de relleno **sólido** (morado en la capa). Con `minimum_sparse_infill_area` = 0
por objeto en los vasos lleva relleno ligero entre sus dos paredes.

Vaso solo (CLI): v8 54.5 g · 2 h 29 → **49.3 g · 2 h 03**. Probadas también: 1 pared
42.9 g · 1 h 54; 1 pared + área 0: 37.4 g · 1 h 50 (piel de 0.45 mm, frágil); área 0 +
relleno 10 %: 47.5 g · 2 h 00.

Juego completo (CLI), costo = g × 167 $/kg + $16.38:

| Opción | Tiempo | Peso | Costo |
|---|---|---|---|
| v8 | 9 h 31 | 278.5 g | $62.89 |
| **v9 — A: costillas con relleno (elegida)** | **8 h 14** | **263.0 g** | **$60.30** |
| B: costillas de 1 pared | 7 h 36 | 227.2 g | $54.32 |
| C: B + bandeja lightning | 7 h 11 | 200.2 g | $49.82 |

La paquetería ($16.38, con maceta de regalo y tierra) es el 27 % del costo; no se tocó.
Si al imprimir la v9 aguanta bien, B queda como siguiente paso (probar uno antes de vender).

## v10 (10-23) — 2 vasos para la caja de 20 × 16 × 11
Pedido: «¿cabe en la caja?» → no: la bandeja de 3 vasos mide 25.2 cm y ni inclinada entra
(le faltan ~16 mm por lado en su mejor giro). «Déjalo de solo 2 espacios… que ocupe los
20 de largo sin problema». Aprobado con el precheck («sí»). Respaldo: `.v9.bak`.

- Bandeja de n lóbulos (`lobulos`, `BANDEJA["vasos"]` = 2) y `largo` = 196 mm: los vasos
  se ensanchan parejo hasta llenarlo (`ajustar_al_largo`): radios 35.8 / 46.2 / 33.5
  (piso / panza / boca), **92 × 100 mm**, mismo alto; costillas 14 → **16** para que cada
  una siga del mismo ancho. Separación, holgura, pared, labio y alturas sin cambio.
- Juego armado **195.9 × 100.9 × 103.1 mm**: entra derecho en la caja de 20 × 16 × 11
  (4 mm de sobra a lo largo, 7 arriba). Un juego por plato P2S.
- Con `--vasos 3 --largo 0` sale idéntico a la v9.

| Juego (CLI) | Tiempo | Peso | Costo |
|---|---|---|---|
| v9 (3 vasos, no cabe en la caja) | 8 h 14 | 263.0 g | $60.30 |
| **v10 (2 vasos 92 × 100)** | **6 h 33** | **211.8 g** | **$51.75** |

## Pendiente / conocido
- **Imprimir** el juego y revisar las costillas (sin z-hop se ahorrarían 17 min por vaso,
  51 por juego, pero la boquilla podría raspar las costillas: no se aplicó).
- Vaso de 80 mm (v9) 49.3 g laminado; la suma de sólidos del script sobreestima.
- Holgura justa en la caja (4 mm): si el burbuja no deja cerrar, `--largo 190`.
- El tiempo lo mandan los vasos, sobre todo los trayectos entre costillas.
- Rendijas de 2.2 mm: la punta de cuchillos o tenedores podría atorarse; el usuario
  eligió dejarlas así.
