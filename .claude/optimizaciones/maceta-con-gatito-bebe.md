# maceta_con_gatito_bebe ("Kitty Love", comprado, MakerWorld — Jhocar13)

Archivo: `own design 3d/maceta_con_gatito_bebe.3mf`
Estaba en Descargas (nunca laminada, "sin laminar"); se movió a la carpeta del
catálogo con el mismo efecto que el botón "Mover a mi carpeta". Backup original
en `maceta_con_gatito_bebe.3mf.bak`.
Un solo objeto, malla de 1.3M caras (watertight, winding consistente),
configurado originalmente para una Bambu Lab A1 normal (plato 256×256).

## Feedback recibido
- 2026-09-30 — Hacer `/transform` para que quede lista para imprimir en una
  Bambu Lab A1 mini, aprovechando al máximo su plato.

## Diagnóstico
- Tamaño original: 172.99×187.55×135.92mm — el eje Y (187.55mm) **ya no cabe**
  en el plato de 180×180 de la A1 mini con el archivo tal cual venía.
- Se probó rotar la huella (convex hull 2D, barrido 0-180°) buscando una
  orientación que redujera la huella máxima: no hay ninguna mejor que la
  orientación original (mínimo global ~187.5mm en cualquier ángulo) — la pieza
  ya viene orientada de la forma más eficiente posible.
- Grosor de pared por raycasting (malla decimada a 60k caras para que fuera
  viable en tiempo/memoria — la malla completa de 1.3M caras agotó la memoria
  en el primer intento): mediana ~13mm, prácticamente sin zonas por debajo de
  0.8-1.2mm. Esto es normal en mallas de macetas descargadas: son una
  superficie sólida única (no traen pared modelada), el grosor real de
  impresión lo define el slicer vía `wall_loops`, no la geometría — por eso es
  seguro activar `detect_thin_wall` sin riesgo de toolpaths erráticos.
- Soporte: `support_type=tree(auto)` y `support_on_build_plate_only=0` **ya
  estaban correctos** de fábrica — no hizo falta tocarlos (el diseño tiene
  brazos/orejas con volado que necesitan soporte apoyado en la propia pieza,
  no solo en el plato).

## Cambios aplicados
- **Tamaño**: escala UNIFORME (misma proporción en los 3 ejes, sin estirar un
  solo eje) a factor **0.906422** — la pieza *se achica* respecto al original
  porque venía pensada para un plato más grande. Resultado:
  **156.8×170.0×123.2mm** (antes 172.99×187.55×135.92mm), con 5mm de margen a
  los bordes en Y (el eje que manda) — el ancho X y el alto Z quedan con
  bastante margen de sobra, la pieza es más ancha que alta. Traslación
  recalculada: X,Y al centro del plato de 180×180 (90,90), Z recalculada con
  la fórmula del Tropiezo #3 (`tz = -factor·z_min_local`), verificado
  `factor·z_min_local + tz = 0.0` exacto — la base queda perfecto en el plato.
- **Perfil de impresora**: `printer_model`→"Bambu Lab A1 mini",
  `printer_settings_id`→"Bambu Lab A1 mini 0.4 nozzle", `printable_area`→180×180,
  `printable_height`→180 (antes: A1 normal, 256×256×256).
  `print_settings_id`→"0.12mm Fine @BBL A1M" (nombre inferido por el patrón de
  Bambu; si Bambu Studio no lo reconoce exacto al abrir, pedirá elegir un
  perfil de proceso compatible — cosa de un clic, no rompe nada).
- **Calidad**: `layer_height` 0.2→0.12mm, `top_shell_layers` 4→7 y
  `bottom_shell_layers` 3→5 (mismo grosor sólido en mm, más resolución),
  `ironing_type`→"top surface", `detect_thin_wall`→1.
- Todas las claves tocadas agregadas a `different_settings_to_system` (Tropiezo
  #1) para que Bambu Studio no las revierta al abrir el proyecto.
- No se tocó `wall_loops` (sigue en 2) ni `sparse_infill_density` (sigue en
  8%) — eso es peso, va en el reporte, no en este paso.

## Peso/costo proyectado (estimado por geometría — falta confirmar con Rebanar)
Con el volumen sólido-equivalente y el área de superficie de la malla
(escalados al tamaño nuevo) y los ajustes actuales de pared/relleno:
- Volumen sólido-equivalente: ~779.7 cm³ · Superficie: ~1449.8 cm²
- Cascarón (2 perímetros × 0.4mm) + relleno 8% del volumen restante:
  **~210g estimados** por pieza (~$51 MXN de filamento con la fórmula
  gramos×0.1837+12.30 de la tarjeta del elefante)
- Si al Rebanar sale más pesado/caro de lo que gusta, la palanca real es
  `sparse_infill_density` (8%→menos) — no toques `wall_loops` ni el tamaño para
  bajarlo, eso ya está al máximo seguro para la A1 mini.

## Verificación y cierre
- Zip válido (`testzip()` sin errores), malla re-parseada watertight y con
  winding consistente tras el cambio de transform.
- Bounds mundiales tras el escalado: X [11.60, 168.40], Y [5.00, 175.00], Z
  [0.0000000006, 123.197] — dentro del plato 0..180 en los tres ejes, base
  exactamente en Z=0.
- Reabierto en Bambu Studio (`open -a "BambuStudio"`).

## Ajuste 2 (2026-09-30 — pidió varias copias de ~25g cada una en el mismo plato)
- Pidió "que quepan varias en el mismo lugar que pesen un aprox de 25kg" —
  confirmado por el usuario que era **25 gramos** por pieza (typo), no 25kg.
- Con el modelo de peso del paso anterior (cascarón 2 perímetros + relleno 8%
  sobre el volumen restante, densidad PLA 1.24g/cm³) resolví el factor de
  escala que da exactamente 25g: **0.355377** (mucho más chica que el ajuste 1,
  que era para una sola pieza grande) → **61.5×66.7×48.3mm** por unidad.
- Footprint (convex hull 2D) a ese tamaño: barrido de huella + grilla con
  `shapely` — el plato de 180×180 con 6mm de separación entre piezas solo
  permite una grilla **2×2 = 4 copias** (una fila o columna de 3 no cabe: 3×61.5
  o 3×66.7mm ya superan los 180mm del plato sin margen ni separación). Verificado
  con `polygon.distance()` entre las 4 huellas: mínimo 6.00mm, ninguna se toca,
  y las 4 caen dentro de 0..180 en X e Y.
- Reescala uniforme aplicada a las 4 copias (mismo factor, sin estirar ejes) +
  traslación Z recalculada (Tropiezo #3, verificado en 0.0000).
- **Sincronización de `model_settings.config` (Tropiezo #5)**: al pasar de 1 a
  4 copias del mismo `objectid=2`, actualicé también `<plate><model_instance>`
  (4 bloques, `instance_id` 0-3, `identify_id` únicos 337-340 — no reutilicé el
  336 original) y `<assemble><assemble_item>` (4 bloques por `instance_id`,
  conservando intacto el único `assemble_item` por `volume_id` que no depende
  de la cantidad de instancias). Verificado con `xml.etree` que las 4
  instancias, los 4 `model_instance` y los 4 `assemble_item` por instancia
  coinciden uno a uno.
- Peso total del plato con las 4 copias: ~**100g** (4×25g), muy por debajo de
  cualquier límite físico razonable.

## Pendiente
- Falta que el usuario dé **Rebanar** en Bambu Studio para confirmar peso y
  tiempo reales de las 4 copias (el archivo nunca se había laminado, no había
  ningún número de referencia previo).
- Verificar que `print_settings_id="0.12mm Fine @BBL A1M"` sea un perfil que
  Bambu Studio realmente tenga instalado; si no, elegir el equivalente al abrir.
- El peso de 25g por pieza es una proyección por geometría (cascarón + 8% de
  relleno) — al ser una pieza tan chica, el peso real podría diferir más en
  términos relativos que en la pieza grande del ajuste 1; confirmar con
  Rebanar antes de dar el número por bueno para cotizar.
