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
  `project_settings` del florero (`Florero Minimalista Grande 178mm.3mf`: P2S 0.4,
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

## 2026-11-22 (v11) — «los vasos se están rompiendo muy fácil, hazlos más fuertes»
Impreso: **se truenan costillas y el vaso se parte en anillo** (entre capas). Respaldo:
`Portacubiertos_Trenzado.{3mf,png,stl}.v10.bak`. Aprobado con el precheck («B: sólida»).

Diagnóstico: cada costilla era una lámina suelta de 91 mm (solo pegada al zócalo y al
aro de la boca), de 1.1 mm en la orilla de la rendija, y desde la v9 con relleno ligero
por dentro (dos pieles de 0.45 mm). Poco material de capa a capa y nada que la amarre.

Cambios (forma por fuera igual, juego 195.9 × 100.9 × 103.1, cabe en la caja):
- `canto` 1.0 → **1.8**, `grueso` 2.4 → **3.2**: sección por costilla en la panza
  34 → 45 mm² (+32 %), lo más delgado 1.1 → 1.9 mm. El vaso queda 1.6 mm más angosto
  por dentro.
- **2 aros por dentro** (`aros`, `aro_cara` 4, `aro_entra` 2.0, `aro_fondo` 1.2) a 1/3 y
  2/3 entre zócalo y boca: el tramo suelto baja de 91 a ~30 mm. Cara recta de 4 mm (lo
  que se asoma por la rendija, 0.6 mm por debajo de la orilla) y chaflanes a 45° arriba
  y abajo: sin soporte y sin repisa.
- Se quitó `minimum_sparse_infill_area` 0 de los vasos: costillas sólidas otra vez.
- El donante de perfil (`Florero Minimalista Grande 178mm.3mf`) ya no está en
  `own design 3d/`; se usó el .3mf v10 del catálogo con `--ajustes`. El script ahora
  avisa si falta el donante.

Juego (CLI), costo = g × 180 $/kg + $13.96:

| Versión | Tiempo | Peso | Costo |
|---|---|---|---|
| v10 | 6 h 33 | 211.8 g | $52.08 |
| A: forma v11, costillas con relleno ligero | 7 h 54 | 247.5 g | $58.52 |
| **v11 — B: forma v11, costillas sólidas (elegida)** | **8 h 05** | **261.2 g** | **$60.97** |
| C: B + 3 paredes en vasos | 9 h 16 | 287.5 g | $65.70 |
| D: B + 4 paredes en vasos | 9 h 25 | 291.9 g | $66.49 |

## 2026-11-24 (v12) — «optimizar el peso, que sea más rápido… sin que sea frágil, paredes muy lisas»
También pidió 2 juegos por plato si se podía. Respaldo: `Portacubiertos_Trenzado.{3mf,png,stl}.v11.bak`.
Aprobado con el precheck («Apruebo la A»).

Diagnóstico (CLI de la v11): de las 8 h 05, **3.4 h eran viajes + retracciones**
(Travel 6 074 s + Undefined 6 071 s): cada costilla es una isla por capa, ~68 000
retracciones por vaso (bandeja 6 300). Vaso 82.4 g, bandeja 92.1 g. Esas 16 costuras por
capa en las costillas son también lo que se ve «impreso».

Cambio: `cerrado` = 1, `piel` = 1.8. El vaso es una piel continua que por fuera es igual
(cordón de `panza` 4 sobre la orilla) y cierra cada rendija con un fondo al radio de su
orilla; por dentro es el contorno de afuera erosionado 1.8 mm (`contorno_cerrado`, 0
aristas sueltas). Sin aros por dentro: ya no hay costillas sueltas. La costura «aligned» cae
sola en el fondo de una rendija. Ya no se ve a través de la rendija; el agua sale por los
agujeros del piso.

Resistencia: plástico por capa en un vaso, medido en el G-code arriba de la bandeja
(66–94 mm, mediana): v10 (la que se rompió) **370 mm²**, 16 láminas sueltas · v11 567,
sueltas atadas por 2 aros · **v12 521, un solo anillo corrugado (+41 % sobre la v10)** ·
piel 2.1 604 · piel 2.4 686.

Juego (CLI), costo = g × 180 $/kg + $13.96:

| Versión | Tiempo | Peso | Costo |
|---|---|---|---|
| v10 (se rompía) | 6 h 33 | 211.8 g | $52.09 |
| v11 | 8 h 05 | 261.2 g | $60.97 |
| **v12 — A: piel continua 1.8 (elegida)** | **5 h 55** | **245.0 g** | **$58.07** |
| piel 2.1 | 6 h 46 | 265.5 g | $61.76 |
| piel 2.4 (relleno sólido entre líneas) | 6 h 58 | 282.3 g | $64.77 |

**2 juegos por plato: no caben** sin achicar el producto. Dos bandejas ocupan 196 × 202 mm
del plato de 256 y quedan 54 mm, el vaso mide 92. Lo que sí: 2 juegos en 11 h 50 (antes
16 h 10); si conviene, un plato de 4 vasos y otro de 2 bandejas.

## 2026-11-25 (v13) — «a los dos vasos (más el izquierdo) les quedaron salidas como hilos sueltos por los lados»
Impreso: v12. Lo mismo que el Torsión v3. Respaldo: `Portacubiertos_Trenzado.{3mf,png,stl}.v12.bak`
(la malla no cambió; solo `model_settings.config`).

Diagnóstico (G-code por CLI, midiendo cuánto de cada salto va por fuera del plástico, capas
66–99): con `seam_position` «aligned», la pared que da afuera y la que da adentro alinean su
costura cada una por su lado y quedan en lados opuestos. En **cada capa la boquilla cruzaba
el interior del vaso por el aire (30–64 mm)**, además del paso al otro vaso: 2 saltos largos
por capa y vaso, ~1 000 por vaso. Cada uno arranca de la pared de afuera y deja un pelito en
el costado. En el vaso izquierdo esos arranques caían repartidos por su costado de afuera
(120–240° y 330°), a la vista; en el derecho, casi todos del lado del otro vaso. Por eso el
izquierdo se ve peor. Los dos vasos son la misma malla y el mismo laminado.

Cambio: `seam_position` = **back** por objeto en los vasos (`POR_OBJETO["vaso"]`). Las dos
costuras quedan juntas atrás (+y = espalda alta de la bandeja) y el salto solo atraviesa la
piel de 1.8 mm. Queda un salto por capa, el paso de un vaso al otro, que sale siempre de la
costura de atrás.

| Juego (CLI) | Tiempo | Peso | Saltos por el aire por capa y vaso | Cruce del interior |
|---|---|---|---|---|
| v12 (aligned) | 5 h 54 | 245.0 g | 2 | sí, 30–64 mm |
| **v13 (back en vasos)** | **5 h 51** | **245.0 g** | **1** (paso al otro vaso, desde atrás) | no |
| nearest en vasos | 5 h 49 | 245.0 g | 1 | no (costuras sueltas) |

Costo sin cambio: $58.07 por juego. Probadas y descartadas: `reduce_crossing_wall` por objeto
(Bambu lo ignora; global: +25 min y peor en la bandeja), `wall_sequence` outer/inner (no quita
el cruce). No se bajó la temperatura: la v11 se partía en anillo.

**Impresa (11-25): «funcionó»**, sin los pelitos en los costados.

Torsión v4 revisado con lo mismo: costura atrás + `reduce_crossing_wall` desde el 11-24, solo
el paso de una pieza a otra por capa; sin cruces del interior.

## Pendiente / conocido
- v13 impresa sin pelitos (11-25). Falta apretar / dejar caer un vaso para confirmar resistencia / dejarlo caer antes de producir. Si todavía se parte
  en anillo, lo siguiente es adhesión entre capas (temperatura de boquilla +10 °C o menos
  ventilador en los vasos), no más geometría; la piel de 2.1 cuesta más que la v11.
- La bandeja (92 g, pared 4.5 al 10 %) no se tocó en la v12.
- Sin z-hop se ahorrarían 17 min por vaso, 51 por juego, pero la boquilla podría
  raspar las costillas: no se aplicó.
- Vaso de 80 mm (v9) 49.3 g laminado; la suma de sólidos del script sobreestima.
- Holgura justa en la caja (4 mm): si el burbuja no deja cerrar, `--largo 190`.
- El tiempo lo mandan los vasos, sobre todo los trayectos entre costillas.
- Rendijas de 2.2 mm: la punta de cuchillos o tenedores podría atorarse; el usuario
  eligió dejarlas así.
