# Portacontrol_borderedondo01 ("Remote control organizer", LGND3RY)

Archivo: `~/Desktop/own design 3d/Porta controles/Portacontrol_borderedondo01.3mf`
Backup de fábrica: `Portacontrol_borderedondo01.3mf.bak` (creado 2026-09-30, antes de cualquier cambio)

Tarjeta de origen: 146.0 g, $39.59 costo, PLA, categoría "Porta controles" (una de
[[dos-piezas-que-se-fabrican]]).

## 2026-09-30 — pase completo con `/transform`

**Diagnóstico (paso 1, con trimesh sobre la malla escalada al transform actual):**
- Malla watertight y winding consistente (8684 caras, sin reparar).
- Grosor de pared por raycasting: mínimo 3.84 mm, mediana 5.57 mm — muy por
  encima del límite de 2 perímetros (~0.8mm con boquilla 0.4mm). No hay zonas
  al límite, así que `detect_thin_wall` se pudo activar sin riesgo de
  toolpaths erráticos.
- Overhang bloqueado por la propia malla: 39.8% del área con overhang
  (5539 de 13924 mm², threshold 30°) no tiene línea recta libre hasta la
  cama. Sin embargo el archivo ya traía `enable_support=0` — política
  correcta para esta pieza según [[soportes-en-figuras]] (es un recipiente,
  no una figura), y ya traía `support_on_build_plate_only=0` y
  `support_type=tree(auto)` desde antes. **No se tocó nada de soporte.**

**2a. Calidad aplicada:**
- `layer_height`: 0.2 → 0.12 mm
- `top_shell_layers`: 6 → 10 (mismo 1.2mm sólido)
- `bottom_shell_layers`: 3 → 5 (mismo 0.6mm sólido)
- `ironing_type`: "no ironing" → "top surface"
- `detect_thin_wall`: 0 → 1 (seguro, ver diagnóstico arriba)
- `wall_loops` (2) y `sparse_infill_density` (20%) sin tocar — eso es peso, no calidad.

**2b. Soporte:** sin cambios (ya estaba correcto, ver diagnóstico).

**2c. Tamaño:** sin cambios — no hubo feedback de tamaño y la escala actual
(1.1196× / 1.0924× / 0.9885×, propia del archivo) ya se ve proporcionada.

**2d. Empaque — 1 → 4 copias en el plato (P2S, 256×256):**
- Convex hull 2D local escalado por (sx,sy) → huella 134.35 × 65.54 mm.
- 3 copias sin rotar en una columna (margen 5mm, separación 7mm) + 1 copia
  rotada 90° aprovechando la franja sobrante a la derecha (mismo patrón que
  [[loop-remote-holder]] / portacontroles4espacios: columna + 1 rotada).
- Verificado con `shapely.distance()` entre cada par de hulls: mínimo 7.00 mm
  (exactamente el margen pedido, sin solapes).
- Sincronizado `model_settings.config`: 3 objetos nuevos (`id=3,4,5`, mismo
  mesh compartido `object_4.model`), 3 `model_instance` e `assemble_item`
  nuevos, `identify_id` 132/133/134 (no colisionan con el 131 existente).

**Paso 3 — peso/costo (reportado, no aplicado):**
- Peso real de la tarjeta a 20% infill: 146.0 g/pieza — el cambio de calidad
  (capa/ironing/detect_thin_wall) no mueve este número de forma apreciable,
  solo el gramaje por copia se mantiene igual.
- Con las 4 copias en el mismo plato: ~584 g de filamento por corrida
  (4× 146g), ~4× el costo de material de una sola pieza en una sola sesión
  de impresión.
- Palanca de peso si se quisiera bajar gramaje: `sparse_infill_density`
  20% → 10% (u otro valor). No se estima aquí un número preciso porque el
  reparto real entre pared sólida y relleno disperso de esta pieza requiere
  rebanar — es la única forma de no inventar el dato. Si se quiere explorar,
  puedo bajar el infill y volver a pedir Rebanar para dar el número real.

**Verificación (paso 4):**
- `zipfile.testzip()` → sin errores.
- Malla re-parseada: watertight=True, winding_consistent=True.
- `project_settings.config`: valores nuevos confirmados y agregados a
  `different_settings_to_system`.
- 4 copias: `instance_id`/`object_id` coinciden entre build items,
  `model_instance` y `assemble_item`; `identify_id` únicos; las 4 bbox
  (incluida la rotada) caen dentro de 0..256 en X e Y con margen ≥5mm y
  separación ≥7mm entre sí.
- Reabierto con Bambu Studio (`open -a "BambuStudio"`).

**Pendiente:** falta pedir **Rebanar** en Bambu Studio para confirmar
peso/tiempo reales de las 4 copias (y, si el usuario quiere, probar el
trade-off de infill con un número real en vez de estimado).

## 2026-09-30 (mismo día) — el usuario reporta devoluciones: "muy pequeño, no caben los controles"

Pidió ensanchar y alargar. Antes de tocar nada le pregunté con
`AskUserQuestion` (por la lección de [[jirafa-reduced-color]]: estirar un solo
eje rompió la proporción) si quería solo XY o escala uniforme en los 3 ejes, y
cuánto. Eligió **escala uniforme +18%** (dentro del rango +15-20% que ofrecí).

**Aplicado:**
- Backup versionado: `Portacontrol_borderedondo01.3mf.v2.bak` = estado justo
  antes de este resize (ya con las 4 copias del pase anterior).
- Escala uniforme ×1.18 sobre los factores que ya traía el archivo:
  `sx` 1.1195683→1.3210906, `sy` 1.0923996→1.2890315, `sz` 0.9884520→1.1663733
  (se preserva la anisotropía original del archivo, solo se escala parejo).
- `tz` recalculado con la fórmula (`tz = -sz · z_min_local`, z_min_local=-42.5
  mm) → 49.5708658, verificado `sz·z_min_local+tz ≈ 0`.
- Tamaño de pieza: de ~134.3×65.5×84.0mm a **~158.5×77.3×99.1mm** por copia.
- **Reempaquetado obligado**: con el tamaño nuevo, la columna de 3 copias sin
  rotar ya no entraba en los 246mm útiles con el margen de 7mm entre piezas
  (246.03mm > 246mm disponibles, por 0.03mm). Bajé la separación a **6.5mm**
  (sigue dentro del rango 6-8mm que marca el skill) y con eso las 4 copias
  vuelven a caber con margen real (separación mínima verificada 6.50mm exacta
  entre pares, sobra 0.97mm de aire en el borde más ajustado). Mismas 4
  posiciones (3 en columna + 1 rotada 90°), mismo esquema de `object
  id=2,3,4,5`, solo cambian los `transform` (scale+traslación) de los 4
  `<item>` y sus `<assemble_item>` correspondientes — no hizo falta tocar
  `model_instance` ni `identify_id`.
- Calidad/soporte (2a/2b) intactos, no se tocaron en este pase.

**Peso proyectado:** al ser una escala uniforme real (misma geometría, mismo
espesor de pared relativo, todo ×1.18), el volumen escala ×1.18³≈1.643 — a
diferencia del ajuste de infill, esta SÍ es una proyección confiable:
146g × 1.643 ≈ **~240 g/pieza** (~960g las 4 copias en el plato). Falta
Rebanar para el número real, pero acá el estimado es mucho más sólido que el
de infill porque es geometría idéntica a mayor escala, no un reparto
pared/relleno distinto.

**Verificación:** `testzip` sin errores, malla watertight/winding consistente
(no cambia, es la misma malla compartida), las 4 bbox dentro de 0..256 con
margen ≥5mm y separación real ≥6.5mm entre cada par (verificado con
`shapely.distance()`), `object_id`/`instance_id` siguen coincidiendo entre
build items, `model_instance` y `assemble_item`. Reabierto en Bambu Studio.

**Pendiente:** Rebanar para confirmar que los controles ahora sí entran (esto
no lo puedo verificar yo — solo agrandé proporcionalmente el modelo completo,
incluida la ranura) y para el peso/tiempo real a este tamaño.
