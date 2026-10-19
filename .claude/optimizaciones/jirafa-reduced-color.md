# reduced_color — jirafa low-poly

Archivo: `own design 3d/reduced_color.3mf`
Origen: comprado/generado vía MakerWorld "Image to 3D v2" (reconstrucción 3D desde
una foto, no un diseño hecho a mano — explica la malla de 1M de triángulos con
detalle innecesario y triángulos degenerados).
Backup original en `reduced_color.3mf.bak`.
Un solo objeto, escala anisotrópica (sin rotación).

## Feedback recibido
- 2026-09-21 — Que quepa en una caja de 20×15×11cm, que se vea "gruesa" (más
  robusta), mejorar el acabado en las patas (dice que no se ve bien por el soporte
  que usa), y reducir el tamaño en general.
- 2026-09-28 — El ancho quedó demasiado pequeño tras el achicado del 09-21; las
  patas se dañan por el volado (overhang) al imprimir. Sugerencia: usar el mismo
  tamaño que el elefante (`origami-elefante.md`) o al menos un cuello un poco más
  alto.

## Diagnóstico
- Tamaño original: 87.8 × 210.2 × 252.3mm — NO cabía en la caja de ninguna forma
  (252mm de alto ni siquiera cabe de pie en la impresora cómodamente).
- Malla original: 1,000,000 triángulos / 500,001 vértices para un modelo que
  visualmente es low-poly/faceteado — sobra casi todo ese detalle (típico de
  reconstrucción foto→3D). Decimé a 60,000 triángulos y el resultado es
  visualmente IDÉNTICO (mismo volumen casi exacto: 19.23→19.23cm³ sin escalar).
- Grosor de patas (sin escalar): mediana 4.6mm, pero con un mínimo de 0.015mm en
  algún punto — un pellizco degenerado típico de la malla generada por IA, no un
  problema de diseño real.
- Soporte: `enable_support=0` en el config guardado, pero `support_used=true` en
  el último laminado real (inconsistencia — probablemente se desactivó sin volver
  a rebanar). Medí volados reales en la zona de patas (z<-15 sin escalar): 20.1%
  del área de las patas tiene volado >30°, la mayoría probablemente falsos
  positivos del facetado low-poly sobre una columna básicamente vertical, no
  voladizos genuinos.

## Cambios aplicados
- 2026-09-21: **Reconstruí la malla completa** — decimada a 60k caras (limpia el
  detalle inútil y los triángulos degenerados) y luego **engordada**: empuje hacia
  afuera a lo largo de la normal (suavizada entre vecinos, no la normal cruda —
  con normal cruda el empuje generaba cientos de caras invertidas por lo ruidosa
  que es la malla; con normal suavizada bajó a un puñado, y esos pocos vértices
  problemáticos se les redujo el empuje iterativamente hasta 0 caras invertidas),
  0.3mm en las patas (z<-15, con transición suave hasta z=-10) — de paso resolvió
  el pellizco de 0.015mm (confirmado tras engordar: grosor mínimo en patas
  0.015mm→0.466mm sin escalar, mediana 4.6mm→5.29mm). Verificado: watertight, sin
  caras invertidas, volumen sin escalar 19.23→20.08cm³ (+4.4%).
- 2026-09-21: reescalada con la MISMA proporción anisotrópica original × 0.65
  adicional (factor elegido para caber en la caja con margen, no ajustado al
  límite) — de 87.8×210.2×252.3mm a **57.1×137.2×164.5mm**. Traslación Z
  recalculada con el nuevo mínimo local de la malla engordada (Tropiezo #3),
  verificado en 0.0000.
- 2026-09-21: soporte — `enable_support=1` (explícito, ya no ambiguo),
  `support_threshold_angle` 30°→50° (menos falsos positivos del facetado en las
  patas), `support_on_build_plate_only=1` (evita que el soporte se apoye en las
  patas/cuerpo, solo sube desde el plato — debería ayudar directo al acabado que
  se quejaba).
- 2026-09-21: calidad — `layer_height` 0.2→0.12mm, techo/piso 5→8 / 3→5.

## Resultado real (pendiente de que el usuario Rebane y confirme)
- No se estimó peso/costo con precisión (no fue el foco de este pedido — tamaño y
  acabado de patas). Si lo pide, retomar con el modelo de volumen del skill.
- El `slice_info.config` embebido en el archivo trae un peso viejo (195.24g) de
  una rebanada anterior a todos estos cambios — no es el peso real actual, solo se
  actualiza cuando el usuario vuelve a Rebanar.

## Cambios aplicados (continuación)
- 2026-09-28: **confirmado el diagnóstico del "volado daña la estructura" con
  datos** (no solo a ojo): a la escala del 09-21, medí qué % del área con overhang
  >50° (el `support_threshold_angle` configurado) queda bloqueada — es decir, un
  rayo recto hacia abajo desde esa cara choca con la propia malla antes de llegar
  al plato, así que con `support_on_build_plate_only=1` Bambu Studio directamente
  NO genera soporte ahí (no es que lo genere mal, es que lo omite). Resultado:
  9.0% del área con overhang (232.9 mm² de 2577 mm²) queda sin soporte por esta
  causa, distribuido en casi todo el rango de Z del modelo (no solo patas — también
  cuernos/orejas/mentón/panza). **Cambié `support_on_build_plate_only` 1→0** (ya
  estaba en `different_settings_to_system`, no hace falta agregarlo) para que el
  soporte tipo árbol pueda apoyarse en el modelo donde de verdad lo necesita.
  Contrapartida: puede dejar marcas de contacto en esas zonas al retirar el
  soporte (ya mitigado en parte por `support_interface_top_layers=2` y
  `support_top_z_distance=0.2` que ya traía el perfil) — más aceptable que perder
  la estructura.
- 2026-09-28: **ensanchado + un poco más alto** (pedido: mismo tamaño que el
  elefante, o al menos el cuello más alto). Escalar TODO al tamaño del elefante
  (~144mm) no aplica bien aquí — el elefante es compacto/cúbico (144×133×141mm) y
  esta pieza es naturalmente alta y angosta (una reconstrucción foto→3D de un
  animal de pie); escalar parejo para igualar el elefante habría exigido subir Z a
  ~400mm (no cabe en la P2S) o si se iguala por Z, X habría quedado aún MÁS
  angosto (lo contrario de lo pedido). En vez de eso escalé de forma no uniforme
  en el transform del `<item>` de `3D/3dmodel.model` (Tropiezo #2): **X ×1.50**
  (ancho/grosor del cuerpo — la dimensión que se veía "flaca" y la que más engorda
  las patas, ya que su sección transversal crece con este eje) y **Z ×1.10**
  (cuello/alto, la sugerencia alternativa del usuario). Y (largo hocico-cola) sin
  cambios. Traslación Z recalculada (Tropiezo #3): `tz = -1.8037595219 ×
  (-50.30320404) = 90.7348833`, verificado `factor_z·z_min_local+tz ≈ 0`
  (3.1e-9, redondeo de float). Traslación X/Y ajustada para mantener el mismo
  centro en el plato (el centro local de la malla no es exactamente 0,0, así que
  al cambiar sx hay que recorregir tx o el objeto se corre unos mm).
  - Tamaño: **57.1×137.2×164.5mm → 85.6×137.2×180.9mm**. Cabe con margen en el
    plato P2S (256×256×256mm): bbox mundo X 85.7–171.3, Y 49.9–187.1, Z 0–180.9.
  - Verificado tras escribir el zip: `testzip()` sin errores, malla re-parseada
    watertight y winding-consistente, `support_on_build_plate_only=0` confirmado
    en el config guardado.
  - Backup de este estado (antes de este cambio, ya con el ensanchado/soporte del
    09-21 previo): `reduced_color.3mf.v2.bak`.
  - **⚠️ Revertido el mismo día** — ver abajo, el usuario mandó foto de frente y
    se veía desproporcionado (patas muy separadas/pecho muy ancho vs. cabeza
    angosta). Causa: este modelo YA traía escala anisotrópica propia desde el
    archivo original (no 1:1:1 — ver nota al inicio del documento), estirar solo
    X rompió esa relación entre ejes en vez de mantenerla.

- 2026-09-28 (corrección, mismo día): **revertido el X×1.50/Z×1.10 al transform
  original** (`2.0849245885 / 1.9851328510 / 1.6397813835`, translate
  `128.494472 / 118.214118 / 82.486257515194` — de vuelta a 57.1×137.2×164.5mm),
  `support_on_build_plate_only` se dejó en `0` (esa parte no causaba el problema
  de proporción, no hacía falta tocarla). Le pregunté al usuario cómo prefería
  agrandar sin distorsionar; eligió **escala uniforme pareja** (no engordar solo
  patas, no combinar). Apliqué **factor uniforme ×1.20 en X, Y y Z** (mantiene
  exactamente la proporción anisotrópica original del archivo, solo más grande):
  scale final `2.5019095062 / 2.3821594212 / 1.9677376602`, translate
  `128.49544278050197 / 118.1571339972359 / 98.98350901823278` (tz recalculada,
  Tropiezo #3, verificado `factor_z·z_min_local+tz = 0`).
  - Tamaño: **57.1×137.2×164.5mm → 68.5×164.6×197.4mm**. Cabe en la P2S con
    margen (bbox mundo X 94.2–162.7, Y 36.2–200.8, Z 0–197.4).
  - Verificado: `testzip()` sin errores, malla watertight/winding-consistente,
    `support_on_build_plate_only=0` sigue confirmado.

## 2026-09-28 (parte 3) — Calidad + máximas copias en el plato
- Pedido: "dale calidad y agrega las que más quepan en el mismo espacio".
- **Calidad**: `layer_height`/`top_shell_layers`/`bottom_shell_layers` ya estaban
  en el perfil bueno desde el 09-21 (0.12/8/5). Faltaba del perfil recomendado por
  el skill: `ironing_type` "no ironing"→**"top surface"**, `detect_thin_wall`
  0→**1** (seguro activarlo ahora — las patas ya están bien engordadas desde el
  09-21, lejos del límite de 2 perímetros que hacía riesgoso activarlo antes).
  Ambos agregados a `different_settings_to_system`.
- **Empaque (cuántas caben)**: calculé el *convex hull* 2D (proyección XY) de la
  malla local, lo escalé por los factores de escala actuales por eje (`hull` es
  invariante a escalado afín, así que escalar el hull = hull de la malla
  escalada), y busqué la rotación que más copias da en una grilla simple con
  margen a bordes 5mm y separación 6mm entre piezas (cota conservadora — el hull
  es más grande que la silueta real cóncava de un animal parado, así que el
  espacio real entre piezas termina siendo mayor a 6mm, nunca se solapan).
  Resultado: **3 copias sin rotar en fila** (68.5×164.6mm cada una) + **1 copia
  rotada 90°** aprovechando la franja sobrante arriba (75.4mm de alto libre,
  la copia rotada necesita 68.5mm) = **4 copias totales** en el plato P2S
  (256×256mm). Verificado con `shapely`: las 4 caen dentro del plato y la
  distancia mínima entre hulls es de 6mm (sin overlap).
  - No probé nesting más agresivo (offsets diagonales tipo el elefante) — con
    la franja sobrante que quedó (~28mm de ancho a la derecha, ~7mm de alto
    arriba) no alcanza para una 5ª copia de ningún tamaño/rotación simple.
  - Sincronicé `Metadata/model_settings.config` (Tropiezo #5): 4
    `<model_instance>` (instance_id 0-3, identify_id 76/90/91/92, todos únicos)
    y 4 `<assemble_item>` — verificado que los instance_ids de ambos bloques
    coinciden 1:1 con los 4 `<item>` de `3D/3dmodel.model`.
  - Verificado tras escribir: `testzip()` sin errores, malla watertight, las 4
    bbox mundo dentro de 0-256 en X/Y.

## Versiones

| Versión | Fecha | Qué es | Respaldo |
|---|---|---|---|
| v1 | 09-19 | Original de MakerLab, 87.8×210.2×252.3 mm | `reduced_color.3mf.bak` |
| v2 | 09-21 | Malla decimada 60k + patas +0.3 mm, ×0.65 → 57×137×165 mm | `reduced_color.3mf.v2.bak` |
| v3 | 09-28 | Uniforme ×1.20 → 68.5×164.6×197.4 mm, 4 por plato | `reduced_color.3mf.v3.bak` |
| v4 | 10-17 | Cuello/cara/patas engrosados, 61×125×150 mm, 4 por plato | `reduced_color.3mf.v4.bak` |
| v5 | 10-17 | v4 + soporte que se desprende limpio y bloqueadores pintados | `reduced_color.3mf.v5.bak` |
| v6 | 10-18 | Patas ×1.75, pezuña plana (corte 1 mm) y brim de 6 mm | `reduced_color.3mf.v6.bak` |
| v7 | 10-18 | v6 + soporte `tree_hybrid` (bloque sólido bajo la panza) | `reduced_color.3mf.v7.bak` |
| v8 | 10-18 | Trompa original, patas ×1.45, cola inflada, cuello +15, `tree_strong` suelto | (actual) |

## 2026-10-17 (v4) — "cuando lo imprimí se ve aún muy delgado, el cuello y la cara"

- Feedback: impresa se ve delgada, sobre todo cuello y cara; que el tamaño se vea
  atractivo en la caja de 20×16×11 cm (la misma de los gorilas). La tarjeta trae
  77 g capturados a mano (`.catalogo3d_mercadolibre.json`), no se sabe a qué alto
  la imprimió.
- Mercado: figuras = 44 u / 90 d, 9 % (*medido*, estudio al 10-07).
- Diagnóstico (v3, 197 mm): cuello 26×30 mm a media altura, patas ~11 mm, cara
  ~16 mm de ancho en el hocico. A 197 mm **no cabía en la caja** (164.6 mm de
  largo contra 160). CLI v3: 487.2 g / 28.8 h el plato de 4 (~122 g y 7.2 h c/u).
- Cambio de malla (deformación por regiones, no geometría nueva, ver
  [[estilo-origami-facetado]]): escalas afines por altura para que las facetas
  sigan planas, con transiciones smoothstep.
  - Cuello (z 0→60 del marco centrado a 197 mm): ×1.40 en X y ×1.35 en Y
    alrededor de un eje recto ajustado al cuello diagonal; solo vértices a <16–24 mm
    del eje (si no, el hocico se estiraba).
  - Cara/cabeza (z>52–64): ×1.35 en X dentro de |x|<17 mm; orejas y cuernos
    fuera de eso solo se recorren hacia afuera, conservan su tamaño.
  - Patas (z<−48→−36): ×1.30 en X/Y alrededor del centro de cada pata por altura
    (centros tomados de secciones por debajo de z=−50), solo a <11–17 mm del
    centro; peso cero en la cola y en las costuras x≈0 / y≈0. Las versiones
    sin esas máscaras dieron 210 → 74 → 40 → 8 caras invertidas; la final, 0.
  - Resultado a 197 mm: cuello 26×30 → 36×40, sección baja 35×48 → 49×50,
    patas 11 → 14–15 mm; vol. sólido 235.5 → 287.4 cm³; watertight y winding OK.
- Tamaño para la caja (decidido con el usuario entre 3, laminados con el CLI,
  1 pieza cada uno):

  | Opción | Medidas | Peso | Tiempo | Costo (167 $/kg + $16.38) | En caja |
  |---|---|---|---|---|---|
  | A | 100 mm de alto | 28.2 g | 2.3 h | $21.09 | de pie, se ve chica; 12/plato |
  | **B (elegida)** | 61×125×150 mm | 76.9 g | 5.1 h | $29.22 | acostada, ~2.5 cm de holgura; 4/plato |
  | C | 73×150×180 mm | 122.0 g | 7.3 h | $36.75 | acostada, ~1 cm de holgura; 4/plato |

- La malla quedó horneada a medida final (transform de escala 1, base en z=0,
  sin la escala anisotrópica de antes). Plato P2S: 3 en fila + 1 girada 90°
  (convex hull, 6 mm entre huellas, 5 mm a bordes; `model_settings.config`
  sincronizado, 4 items / 4 instancias / 4 assemble).
- Perfil: `ironing_type` "top surface" → **"top"** (Bambu no reconocía el valor
  viejo y no planchaba); lo demás igual (0.12 mm, 2 paredes, grid 15 %, árbol
  auto a 50°, `support_on_build_plate_only`=0).

| | v3 (197 mm, delgada) | v4 (150 mm, engrosada) |
|---|---|---|
| Plato de 4 (CLI) | 487.2 g · 28.8 h | **307.2 g · 20.3 h** |
| Por pieza | ~121.8 g · 7.2 h · $36.72 | **76.8 g · 5.1 h · $29.21** |
| ¿Cabe en 20×16×11? | no | sí, acostada |

- Pendiente: la miniatura `plate_1.png` sigue siendo la vieja (se regenera al
  rebanar y guardar en Bambu Studio); imprimir una y confirmar que el cuello y
  la cara ya se ven robustos.

## 2026-10-17 (v5) — "que cuando desprenda los apoyos no quede algo sobrante feo"

- Volados medidos en la v4 (150 mm, caras a <45° de la horizontal): 2596 mm²
  — cabeza 799, cuello 63, cuerpo 1343 (casi todo panza), patas 284, cola 108.
- **Bloqueadores pintados** (`paint_supports="8"` por triángulo en
  `3D/Objects/object_1.model`; 8 = bloqueador, 4 = forzar): 1830 caras /
  407 mm² en cabeza (240), cuello (50) y patas (117). Criterio: volado de 30–45°
  de la horizontal (con capa 0.12 se imprime solo), sin tocar caras a <30°
  (quijada, bajo las orejas, panza) ni las que están a 3 anillos de un mínimo
  local (puntas que arrancan en el aire: 11 vértices).
- Ajustes de soporte (agregados a `different_settings_to_system`):

  | Clave | v4 | v5 |
  |---|---|---|
  | `support_interface_top_layers` | 2 | 3 |
  | `support_interface_spacing` | 0.5 | 0.2 |
  | `support_interface_pattern` | auto | rectilinear_interlaced |
  | `support_object_xy_distance` | 0.35 | 0.5 |
  | `support_top_z_distance` | 0.2 | 0.24 |
  | `support_threshold_angle` | 50 | 45 |

- CLI, plato de 4:

  | | v4 | v5 |
  |---|---|---|
  | Plato | 307.2 g · 20.28 h (soporte 6.43 h) | **272.0 g · 17.48 h (soporte 4.29 h)** |
  | Por pieza | 76.8 g · 5.07 h · $29.21 | **68.0 g · 4.37 h · $27.74** |

- No separé cuánto del ahorro es del ángulo y cuánto de los bloqueadores.
- Pendiente: imprimir y revisar con foto si las facetas bloqueadas de la cara o
  los hombros se caen; si alguna sale colgada, quitarle el bloqueador a esa zona
  (o regresar el ángulo a 50°) en vez de volver a la v4.

## 2026-10-18 (v6) — "se dañaron feo en la generación de base, las patas son muy delgadas"

- Impresa la v5: las jirafas se dañaron en la base (no hubo foto; se interpretó
  como falla de adherencia y estabilidad en las patas).
- Causa medida en la v5 (150 mm): la pezuña termina redondeada y **toca la
  placa con solo 31–40 mm² cada una (~6 mm de ancho)**; 1 mm más arriba ya mide
  ~12 mm. La pata medía ~10 mm de grosor a media altura. Son 4 puntos chicos
  sosteniendo 150 mm de figura más el soporte de árbol, y el brim era `auto_brim`
  (30 s en todo el plato, casi nada).
- Cambios:
  - **Patas ×1.30 → ×1.75**, con la transición radial ampliada de 11–17 a
    14–22 mm (en el marco de 197 mm). Probé ×1.6 y ×1.9; ×1.9 dejaba 29 caras
    invertidas y bultos en los muslos, ×1.75 da 0. Los bultos de las rodillas son
    del modelo original.
  - **Corte plano de 1 mm en la base** (`slice_plane` con tapa): el redondeo
    de la pezuña se va y queda una suela plana. Alto 150 → 149 mm.
  - **Brim** `auto_brim` → `outer_only`, 6 mm (queda bajo la pezuña, no se ve).
  - Soporte igual que la v5; bloqueadores recalculados con las mismas reglas
    sobre la malla nueva: 2070 caras / 671 mm² (los muslos más gruesos agregan
    facetas de 30–45° en las rodillas).
- Medidas (150 mm):

  | | v5 | v6 |
  |---|---|---|
  | Contacto de cada pezuña con la placa | 31–40 mm² | **183–209 mm²** |
  | Grosor de pata a 12 mm de alto | ~10 mm | **13.1–13.8 mm** |
  | Plato de 4 (CLI) | 272.0 g · 17.48 h | **297.2 g · 18.33 h** (brim 4.8 min) |
  | Por pieza | 68.0 g · 4.37 h · $27.74 | **74.3 g · 4.58 h · $28.79** |

- Pendiente: imprimir y confirmar con foto que la base ya aguanta. Si todavía
  se mueve, siguen bajar la velocidad y la aceleración de la pared exterior
  (hoy 200 mm/s y 6000 mm/s²) o agregar `slow_down_layer_time` en las capas
  delgadas de las patas.

## 2026-10-18 (v7) — "se dañó el centro de nuevo, la panza no funcionó"

- La v6 falló otra vez a media impresión: la cámara de la P2S mostraba
  filamento enredado sobre la placa y la tarea cancelada.
- Diagnóstico con el gcode de la v6 (dibujé los trazos de soporte por capa):
  la panza es una superficie casi plana de ~1300 mm² a **48 mm de altura**,
  entre las patas. Arriba sí quedaba cubierta (95 % en la capa de 47.8 mm), pero
  la sostenían **unos pocos troncos de árbol de ~5 mm** que suben desde la placa
  (ramas de 2 mm, a 150 mm/s, ×4 jirafas). Esa estructura es la que cede.
- Cambios:
  - `support_style` default → **`tree_hybrid`**: árbol en puntas y orejas, y
    soporte normal (bloque en rejilla) bajo superficies grandes y planas. Es el
    estilo que usan los perfiles de Bambu.
  - `tree_support_branch_diameter` 2 → **4**; `support_speed` 150 → **100**;
    `support_top_z_distance` 0.24 → **0.2** (la panza grande cuelga menos;
    la interfaz densa de 3 capas sigue facilitando el desprendimiento).
  - Pintura: se quitan los bloqueadores en la franja de 28–56 mm (muslos y
    panza; quedan 1889 caras / 479 mm² en cara, cuello y patas) y se **fuerza
    soporte** (`paint_supports="4"`) en las caras de abajo de la panza
    (3582 caras / 1791 mm², z 43–53, |x|<26, normal hacia abajo).
- Verificación en gcode: bajo la panza hay un bloque sólido de rejilla desde la
  placa (~780 mm² a 10 mm de altura, ~640 mm² a 40 mm, contra 145–475 mm² en
  troncos sueltos en la v6) y la cobertura arriba sube a 99.5 %. Bajo la cabeza
  sale un tronco de ~15 mm.

  | Por pieza (CLI, plato de 4) | v6 | v7 |
  |---|---|---|
  | Peso | 74.3 g | **93.0 g** (+18.7 g, casi todo soporte) |
  | Tiempo | 4.58 h | **4.96 h** |
  | Costo | $28.79 | **$31.91** |

- Si funciona y se quiere recortar soporte: subir `support_base_pattern_spacing`
  de 2.5 a 3.5 (no probado).

## 2026-10-18 (v8) — "el árbol fue demasiado difícil de quitar, la trompa y las patas demasiado anchas, la cola se cayó"

- Resultado de imprimir la v7: el soporte híbrido costó mucho quitarlo; la
  trompa y las patas quedaron demasiado anchas; la cola se rompió. El usuario
  pidió resolverlo primero en un boceto a lápiz y después pasarlo a 3D, y además
  alargar el cuello.
- Boceto (líneas de facetas proyectadas, estilo lápiz) con medidas a 149 mm,
  aprobado con las opciones elegidas:
  - **Trompa a su ancho original**: el ×1.35 de la cara ahora se desvanece
    hacia el hocico (`ss(y,-68,-58)`): 21.7 → **16.3 mm**.
  - **Patas ×1.75 → ×1.45**: 13.6 → **11.5 mm** a 12 mm de alto; pezuña plana
    137 mm² (contra 31–40 en la v5).
  - **Cola inflada** 1.5 mm por lado (marco de 197 mm) por normal suavizada, con
    reducción iterativa donde se invertía una cara (escalarla alrededor de su eje
    invertía caras en la curva): sección de 46 → **120 mm²**, 4.9 → **8.3 mm**.
  - **Cuello +15 mm** a lo largo de su eje (dirección (0, −0.42, 0.91)), solo
    en la franja z 28–55 (marco de 197 mm): lineal ahí, la cabeza se traslada
    sin deformarse. A z0 = 30 quedaban 2 caras invertidas, a 28 ninguna. Se
    probaron +15 (159 mm de alto) y +25 (166 mm); se eligió +15.
  - La escala del cuerpo es la misma de la v4–v7 (×150/197.4), así que la
    figura queda en **61×131×159 mm**; acostada en la caja deja 20 mm de holgura
    a lo largo y 15 a lo ancho.
- Soporte "árbol suelto" (elegido): `support_style` **`tree_strong`**,
  ramas de 4 mm, interfaz 2 capas a 0.5 (suelta), z 0.24, xy 0.5, 100 mm/s; se
  mantienen el soporte forzado en la panza y los bloqueadores fuera de la franja
  28–56 (1619 caras / 338 mm²).
- Verificación en el gcode: bajo la panza sale **un tronco grueso continuo**
  a lo largo de cada panza (314–370 mm² a 10–30 mm de alto), contra troncos
  sueltos en la v6 (145–242 mm²) y el bloque de la v7 (~750 mm²); 98 % de la
  panza apoyada arriba.

  | Por pieza (CLI, plato de 4) | v7 | v8 |
  |---|---|---|
  | Alto | 149 mm | **159 mm** |
  | Peso | 93.0 g | **83.5 g** |
  | Tiempo | 4.96 h | **4.38 h** |
  | Costo | $31.91 | **$30.32** |

- Pendiente: imprimir. Si la panza vuelve a ceder, regresar a `tree_hybrid`
  solo bajo la panza (v7) y aflojar su interfaz (0.5, z 0.24) para que se quite
  más fácil.

## Pendiente / conocido y no resuelto
- **Bug propio detectado y corregido en el momento (09-21)**: al escribir las
  coordenadas de la malla nueva usé `%r` directo sobre valores numpy sin convertir
  a `float()` primero — en numpy 2.x eso escribe literalmente "np.float64(...)" en
  el XML, corrompiendo la malla. Se detectó al re-verificar (el parseo falló) y se
  corrigió antes de entregar nada al usuario. **Lección para cualquier escritura
  futura de XML de malla: siempre `float(x)` antes de formatear, nunca pasar un
  escalar de numpy directo a `%r` o `repr()`.**
- Falta que el usuario Rebane en Bambu Studio y confirme: 1) que el tamaño nuevo
  (85.6×137.2×180.9mm) se ve bien proporcionado y no "gordo" en X, 2) que
  desactivar `support_on_build_plate_only` de verdad arregló las patas/volados
  dañados y no dejó marcas de soporte inaceptables en zonas visibles (cuernos,
  cara), 3) el peso/costo real a este tamaño nuevo (no se recalculó, no fue el
  foco de este pedido).
- Si tras Rebanar el 9% de área bloqueada sigue viéndose mal incluso con soporte
  en el modelo permitido, el siguiente paso sería revisar visualmente en Bambu
  Studio dónde caen esas zonas exactas (no se aisló cuáles caras son cuernos vs.
  panza vs. patas, solo el rango Z/X/Y agregado) y considerar engrosar
  puntualmente esa zona (método 4a del skill) en vez de/además de tocar soporte.
