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
