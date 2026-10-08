# 🌈_Wolken-Stiftehalter (MakerWorld, DElex3D)

Archivo real: `~/Desktop/own design 3d/🌈_Wolken-Stiftehalter.3mf`
Backup de fábrica: `🌈_Wolken-Stiftehalter.3mf.bak` (creado 2026-10-01, antes de tocar nada).

## 2026-10-01: /transform completo

Diagnóstico con trimesh sobre la malla ya escalada por el transform (sx=0.8933,
sy=0.7620, sz=1, sin rotación):

- Malla watertight y winding consistente (116,936 vértices / 233,868 caras).
- **Grosor mínimo de pared**: 1.65 mm en todo el muestreo (4000 rayos normal-a-
  normal) — muy por encima del mínimo de 2 perímetros (~0.84mm a 0.42mm línea),
  sin zonas de riesgo. `detect_thin_wall` se activó sin reparos.
- **Overhang bloqueado por la propia malla**: de 12,463.7 mm² de área con
  overhang por encima de `support_threshold_angle=30°`, solo 0.1 mm² (0.0%)
  queda bloqueado por un raycast recto hacia abajo antes de llegar al plato.
  Esto confirma la afirmación del diseñador en la descripción del modelo
  ("druckoptimiert... keine Stützstrukturen nötig") — es un portalápices
  (recipiente), consistente con [[soportes-en-figuras]] (cero soporte es
  esperado en recipientes, no en figuras). **No se tocó soporte**:
  `enable_support` sigue en `0`, `support_on_build_plate_only` ya estaba en
  `0` y `support_type` ya era `tree(auto)` — nada que corregir aquí.
- Volumen sólido-equivalente: 295.88 cm³ (world). Peso real de referencia (de
  `slice_info.config`, versión previa): **173.57 g** a 10% infill / 2 wall
  loops / capa 0.2mm.

### Aplicado (calidad, 2a)
- `layer_height`: 0.2 → **0.12mm**
- `top_shell_layers`: 5 → **9** (1.0mm → 1.08mm, mismo grosor sólido o más)
- `bottom_shell_layers`: 3 → **5** (0.6mm exacto)
- `ironing_type`: `top` → **`top surface`** (alisa las superficies horizontales
  de arriba; no promete nada en los costados curvos de la nube)
- `detect_thin_wall`: 0 → **1** (seguro, sin zonas al límite)
- `wall_loops` (2) y `sparse_infill_density` (10%) sin tocar — eso es peso, va
  en el reporte.

### Soporte (2b)
Sin cambios — ver diagnóstico arriba, el modelo es genuinamente autoportante.

### Tamaño (2c)
Sin cambios — no hubo feedback específico de tamaño y la proporción actual
(con escala anisotrópica propia del diseñador, 0.893x/0.762y) ya se ve bien.

### Empaque (2d) — máximas copias en el plato
Plato P2S 256×256mm. El convex hull 2D (XY) de la pieza mide **198.65 × 80.72
mm** (la orientación 0° YA es la caja mínima — se probó rotación cada 15° de
0 a 90° y cualquier rotación agranda el bounding box, el perfil es demasiado
alargado para beneficiarse de girarlo). Con eso:
- 1 sola fila en X (198.65mm no deja espacio para una 2ª columna en 246mm
  útiles).
- Apilado en Y: 2 filas caben con margen holgado (84.1mm → 171.9mm de centro,
  margen de 27.5mm en X y 43.8mm en Y a los bordes del plato, separación real
  verificada con `shapely .distance()` = exactamente 7.0mm). **3 filas NO
  caben**: 3×80.72+2×7=256.17mm > 256mm de plato, incluso con margen cero.
- Resultado: **2 copias** (antes 1). `3D/3dmodel.model` con 2 `<item>` del
  mismo `objectid=2`, nuevo `p:UUID` para la copia; `Metadata/model_settings.config`
  sincronizado con `model_instance`/`assemble_item` adicional (`instance_id=1`,
  `identify_id=750`, no colisiona con el 749 existente).

### Reporte de peso/costo (NO aplicado, solo informativo)
Peso por pieza no cambia con lo aplicado arriba (mismo wall_loops, mismo %
infill, shells mantienen el mismo grosor en mm) — sigue ~173.6 g/pieza. El
plato completo con 2 copias ronda **~347 g** totales.

Si se quisiera bajar peso, la única palanca real es `sparse_infill_density`
(compite con robustez): estimación aproximada (erosión de cáscara por área,
calibrar con el peso real al rebanar) 10%→5% ronda **~155-165 g/pieza
(-5 a -10%)**, sin tocar `wall_loops` ni el grosor de pared. No se aplicó —
decisión pendiente del usuario.

### Verificación hecha
- `zipfile.testzip()` → None (zip íntegro).
- Malla re-parseada: watertight + winding consistente.
- `model_instance` / `assemble_item` / items del build: 2 = 2 = 2,
  `identify_id` únicos (749, 750).
- Bbox mundo de ambas copias dentro de 0..256 en X/Y/Z.
- `different_settings_to_system` actualizado para incluir las keys nuevas.

### Pendiente
- Reabrir en Bambu Studio (ya se hizo `open -a`) y pedir **Rebanar** para
  confirmar peso/tiempo reales — el peso de 173.6g/pieza es el de referencia
  anterior (capa 0.2mm, 1 copia), no una medición nueva con capa 0.12mm.
- Decidir si se aplica la baja de `sparse_infill_density` reportada arriba.
