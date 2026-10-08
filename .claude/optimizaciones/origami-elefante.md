# Origami_Elefant_70mm_SizeAdjustable

Archivo: `own design 3d/Origami_Elefant_70mm_SizeAdjustable..3mf`
Origen: comprado — "The Minimalist Fold - Origami Collection Vol. 02" (elefante
faceteado low-poly, MakerWorld), personalizado a 70mm vía "Parametric Model Maker".
Backup original en `Origami_Elefant_70mm_SizeAdjustable..3mf.bak`.
Un solo objeto, escala uniforme (sin rotación), 463k caras.

## Feedback recibido
- 2026-09-21 — Mejorarlo en general, hacerlo un poquito más grande, y mejorar los
  volados (overhangs) para que queden limpios y sea eficiente (poco soporte
  desperdiciado).
- 2026-09-23 — Escalarlo para que pese 180g al rebanar en la Bambu P1S/P2S.
- 2026-09-23 — Agregar la mayor cantidad de copias que quepan en el plato para
  mandar a imprimir, y abrir el archivo en Bambu Studio.

## Diagnóstico
- La descripción del diseñador dice que está pensado para pararse solo, sin soporte
  ("no clunky bases or stands required") — pero el perfil traía
  `support_threshold_angle=24°` (agresivo) y `support_used=true` en el último
  laminado real, contradiciendo esa promesa.
- Medí el área de la malla por ángulo de voladizo real:
  - >24° (umbral viejo): 21.1% del área — genera soporte en mucho más de lo
    necesario.
  - >45°: 12.73%
  - >55°: 10.69%
  - >65°: 9.88% (probablemente la panza/trompa, un voladizo genuino que sí necesita
    algo de soporte)
  - Peor punto: 90° (una cara mirando derecho hacia abajo en algún punto).
- Volumen sólido-equivalente (a escala original 70mm): 54.8cm³. Peso real anterior:
  33.01g.
- Tamaño: la malla base mide 60mm en su eje mayor sin escalar; la escala 1.16667
  la lleva a 70mm ("70mm_SizeAdjustable"). z_min local de la malla sin escalar:
  -29.4446983mm.

## Cambios aplicados
- 2026-09-21: escala 1.16667→1.28333 (+10%, "un poco más grande": 70mm→77mm),
  traslación Z recalculada (Tropiezo #3) para que la base siga exacta en mundo Z=0
  (verificado: 0.0000).
- 2026-09-21: `support_threshold_angle` 24°→50° — deja que los facetados hasta 50°
  impriman sin soporte (PLA aguanta bien esos ángulos con buena refrigeración en
  una pieza chica), solo genera soporte para el ~10-11% de área que de verdad lo
  necesita (la panza/trompa). No se tocó `support_on_build_plate_only` (se dejó en
  0, permitiendo soporte apoyado en el modelo) porque no pude verificar visualmente
  si algún voladizo (oreja/trompa) solo es alcanzable así — más seguro que
  desactivarlo a ciegas y arriesgar un voladizo real sin soporte.
- 2026-09-21: calidad — `layer_height` 0.2→0.12mm, `top_shell_layers` 5→8,
  `bottom_shell_layers` 3→5 (mismo grosor sólido, más resolución — ayuda
  especialmente a que las facetas del origami se vean limpias).
- 2026-09-23: escala 1.28333→2.205117 (77mm→~132mm en el eje mayor) para apuntar a
  180g. Traslación Z recalculada de nuevo (Tropiezo #3): `tz = -2.205116682 ×
  (-29.4446983) = 64.928995417`, verificado `factor_z·z_min_local+tz = 0` (dio
  ~-7.9e-10, redondeo de float). No se tocó `wall_loops` (2), `sparse_infill_density`
  (15%) ni las capas de techo/piso — a este tamaño y con el perfil de calidad ya
  puesto en la sesión anterior, el modelo de volumen (abajo) ya daba 180g solo
  reescalando, sin necesidad de subir relleno.
  - Modelo usado: volumen sólido sin escalar de la malla = 54.7977cm³ (raw,
    triangulación de `object_1.model`, watertight y winding consistente
    confirmados con trimesh). Con el último peso REAL registrado (33.01g @ escala
    1.16667, perfil viejo: layer_height 0.2, top/bottom 5/3 capas) despejé
    `shell_vol` (cascarón: paredes+techos+piso, no cambia con relleno):
    `V_solid(1.16667) = 87.02cm³`, `shell_vol ≈ 15.96cm³` (con
    `infill=15%`, `densidad PLA=1.24g/cm³`). El perfil de calidad de la sesión
    anterior (0.12mm/8/5 capas) da un grosor de techo/piso en mm casi idéntico al
    viejo (0.96mm vs 1.0mm top, 0.6mm vs 0.6mm bottom), así que reutilicé ese
    `shell_vol` escalándolo por `(s/s0)²` (área de cascarón ~ escala² a grosor de
    pared constante) y el volumen sólido por `s³`. Resolviendo
    `peso(s) = densidad·[15%·54.7977·s³ + shell_vol·(s/1.16667)²] = 180g` da
    `s ≈ 2.205117`.
  - Tamaño resultante estimado: ~132.3 × 122.7 × 129.9mm (eje mayor × otros dos),
    cabe sin problema en el plato de una Bambu P1S/P2S (256×256×256mm).

- 2026-09-23: el perfil de impresora del proyecto estaba en "Bambu Lab A1 mini
  0.4 nozzle" (plato 180×180×180mm) aunque el pedido era para la P2S — lo cambié
  a `printer_settings_id`/`printer_model` = "Bambu Lab P2S 0.4 nozzle"/"Bambu Lab
  P2S" (confirmé que existe como perfil real instalado en Bambu Studio, plato
  256×256×256mm con una pequeña zona excluida en la esquina/franja izquierda —
  `~/Library/Application Support/BambuStudio/system/BBL/machine/`). No había
  overrides de impresora en `different_settings_to_system` (los 3 últimos
  elementos vacíos), así que el cambio de perfil no pisa ningún ajuste tocado.
- 2026-09-23: agregué una segunda copia del elefante (mismo `objectid="2"`,
  nuevo `<item>` en `3D/3dmodel.model` con su propio `p:UUID`) — a este tamaño
  (~132.3×122.7mm de huella) **solo caben 2 copias** en el plato de 256×256mm,
  no más: una sola columna sin rotar ya ocupa 132.3mm de los 256mm de ancho, y
  la franja restante (~123.7mm) es apenas más angosta que la huella rotada 90°
  (122.7mm) — casi sin margen para un gap real, así que un tercer elefante no es
  viable con separación segura. Reposicioné ambas copias centradas en X (128mm)
  y apiladas en Y: centros en (128, 64.35) y (128, 191.65) — separación entre
  ellas 4.64mm, margen a los bordes superior/inferior ~3mm cada uno. Traslación Z
  igual para ambas (`tz=64.928995417`, verificado `world_z_base=0` en las dos).
  Sincronicé `Metadata/model_settings.config` (Tropiezo #5): agregué el segundo
  `<model_instance>` (`instance_id="1"`, `identify_id="88"` nuevo) y el segundo
  `<assemble_item instance_id="1">` (reutilizó el transform ya obsoleto del
  primero — solo es metadata de la vista Ensamblar, no afecta el rebanado).

## Resultado real (pendiente de que el usuario Rebane y confirme)
- Estimado para el reescalado a 180g: ver modelo arriba. Es una proyección a
  partir del último peso real medido a otra escala/perfil — el número real solo lo
  da Bambu Studio al Rebanar. Si al rebanar el peso real se aleja mucho de 180g,
  el resto del error probablemente esté en que el modelo de cascarón (`s²`) es una
  aproximación — con el peso real nuevo puedo recalibrar `shell_vol` y ajustar la
  escala de nuevo sin volver a medir la malla.
- Peso proyectado anterior (escala 1.28333, antes de este cambio, con el perfil de
  calidad nuevo pero sin rebanar aún): ~45.5g.

## Pendiente / conocido y no resuelto
- No se verificó visualmente (sin Bambu Studio abierto en pantalla en el momento)
  si el ángulo de 50° deja algún voladizo real sin soporte suficiente — pedirle al
  usuario que revise la vista previa de soportes tras Rebanar antes de imprimir.
  A este tamaño más grande, vale la pena revisarlo de nuevo (más área absoluta de
  voladizo).
- El `assemble_item transform` en `Metadata/model_settings.config` quedó
  desactualizado (sigue en la escala vieja 1.16667) — es solo metadata de la vista
  "Ensamblar" de Bambu Studio y no afecta el rebanado real, así que no se tocó.
- No se recalculó costo/paquetería a este nuevo peso — si el usuario lo pide,
  retomar con `cuentas`/`costoMaterial` de `catalog3d.py` una vez tenga el peso
  real tras Rebanar.
- La separación entre las 2 copias (4.64mm) y el margen a los bordes (~3mm) son
  cálculos geométricos (bounding box), no cuentan el "extruder clearance" real
  de la P2S ni cuánto se puede expandir el soporte generado en el ~10% de área
  con voladizo — pedirle al usuario que en Bambu Studio revise si aparece alguna
  advertencia de colisión/objeto fuera de área, y si quiere más aire entre
  copias use "Organizar automáticamente" (puede que reduzca a menos si no
  encuentra espacio con el gap por defecto del software).
- El archivo ya estaba abierto en una instancia de Bambu Studio antes de este
  cambio (proceso lanzado con este .3mf como argumento) — como la edición fue
  por fuera de la app, puede que esa ventana no se haya refrescado sola; se
  volvió a lanzar `open -a "BambuStudio" <archivo>` después de guardar para que
  cargue la versión nueva (2 copias + perfil P2S).
- 2026-09-24 — **Corregido un error mío de 09-23:** al "cambiar a P2S" solo toqué
  `printer_settings_id`/`printer_model`; el `project_settings.config` seguía con
  `printable_area` 180×180 y `printable_height` 180 de la A1 mini (y los presets de
  impresión/filamento "@BBL A1M"), así que Bambu habría marcado la 2ª copia fuera del
  plato. Ahora se volcaron todas las llaves de impresora y proceso desde los presets
  del sistema ("Bambu Lab P2S 0.4 nozzle" + "0.20mm Standard @BBL P2S": plato 256×256×256)
  y se reaplicaron mis overrides (capa 0.12, techo 8 / piso 5, soporte 50°). Respaldo
  previo: `.3mf.v2.bak`. No se re-rebanó el elefante por CLI (solo se validó el layout
  del portacubiertos).

## 2026-09-25 — Más grandes, más rápido, 3 en el plato (pedido: "lo mismo que el portalápices/loop, pero un poco más grandes")
- Escala 2.2051→**2.40** (+8.8%: ~144×133×141 mm). Zeta recalculada `tz = 2.4×29.4446983 = 70.667`.
- **3 elefantes** en el plato (antes 2): la huella es un blob diagonal; con rotaciones libres
  (búsqueda raster con rotación cada 10°, gap 8 mm, margen 3 mm) caben 3 hasta escala ~2.45
  (2.5 ya solo 2). Rotaciones/traslaciones de los 3 `<item>`: θ = -350°, -60°, -100° (CCW),
  centros por T=(87.2,63.9), (193.8,122.3), (82.5,188.2) (T de la esquina de bbox rotado, no del
  centro; el mesh está centrado en 0). Verificado: bbox de vértices 5–249.5 × 5–247.8 mm, gap
  mínimo entre siluetas 8.35 mm, y el gcode del rebanador CLI extruye entre X 5.0–249.2 / Y 3.8–247.7
  (el `bbox` que reporta el CLI en este caso NO es fiable — sale 283×285; ignorarlo).
  `model_settings.config`: 3er `model_instance` (`instance_id=2`, `identify_id=89`) y 3er `assemble_item`.
- Perfil (agregado a `different_settings_to_system`): `sparse_infill_pattern` grid→**adaptivecubic**,
  `sparse_infill_density` 15%→**8%**, `layer_height` 0.12→**0.16**, `top_shell_layers` 8→6,
  `bottom_shell_layers` 5→4 (mismo grosor sólido en mm); se mantuvo ironing top, soporte
  tree(auto) 50°.
- Comparativa CLI (2 elefantes a escala 2.205): perfil viejo 13.18 h / ~317 g → adaptive cubic 8% @0.12
  10.35 h / ~194 g → **@0.16 7.88 h / ~173 g** (−40% tiempo, −45% peso). Con 0.12 el acabado de las
  facetas sería algo más fino pero +30% tiempo.
- **Nuevo archivo (3 elefantes @2.4): 14.15 h en total (~4.7 h c/u vs ~6.6 h antes), ~320-330 g
  (~107 g c/u vs ~160 g antes).** Ojo: el objetivo original de 180 g/pieza (2026-09-23) ya no se
  cumple — el relleno más ligero baja el peso (y el costo) aunque la pieza sea más grande. Si se
  quiere volver a ~180 g, subir relleno/escala.
- Backup del estado anterior: `.3mf.v3.bak`. El .gcode ya se había quitado antes.
- Pendiente: rebanar/imprimir; revisar que el soporte (2.7 h) no dañe la trompa; Travel 2.9 h (20%).
