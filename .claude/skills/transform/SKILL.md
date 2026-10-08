---
name: transform
description: Aplica de una sola pasada el paquete completo de mejoras a una pieza del catálogo (tarjeta de catalog3d.py pegada como imagen) — calidad de acabado tipo "lijado", diagnóstico y arreglo de soporte/volado, tamaño proporcional, y máximas copias en el plato — en vez de esperar un pedido puntual. Repesa/costo se reporta, no se cambia solo. Úsalo cuando el usuario pida "transforma esta pieza", "mejórala toda", "aplícale todo lo que sepas", o invoque /transform con la imagen de una tarjeta.
---

# /transform — paquete completo de mejora sobre una pieza del catálogo

Este skill es un **preset** sobre `optimizar-pieza`: en vez de reaccionar a un
pedido puntual ("hazlo más grueso", "que pese menos"), aplica en un solo pase la
receta completa que hemos ido validando pieza por pieza — calidad, soporte,
tamaño y empaque — y deja el peso/costo como número reportado, no como cambio
silencioso (eso sigue siendo decisión del usuario).

El input es la imagen de la tarjeta del catálogo (como la pega el usuario para
`optimizar-pieza`) o el nombre del diseño.

## Contexto de mercado

Antes de transformar, revisa en `.claude/mercado/estudio-de-mercado.md` cuánto vende la pieza y su categoría, para decir si el esfuerzo se paga. No cambies las decisiones del usuario por eso; solo menciónalo.

## 0. Identificación y registro (igual que optimizar-pieza)

1. Revisa `.claude/optimizaciones/INDICE.md` y, si existe, el archivo
   `.claude/optimizaciones/<slug>.md` de esta pieza — no repitas diagnóstico ya
   hecho, y respeta pendientes que quedaron marcados a propósito.
2. Encuentra el `.3mf` real en `~/Desktop/own design 3d/**/*.3mf` haciendo match
   por nombre y gramaje contra `Metadata/slice_info.config` (ver optimizar-pieza
   paso 1). Ojo con archivos duplicados/viejos en la misma carpeta (sufijos como
   `(2)`, `(4)`) — confirma cuál es el que usa `catalog3d.py` por fecha de
   modificación y contenido, no asumas por nombre.
3. **Backup versionado antes de tocar nada**: si `<archivo>.3mf.bak` no existe,
   créalo. Si ya existe (de una sesión anterior) y vas a modificar un archivo que
   ya fue editado antes, crea además `<archivo>.3mf.vN.bak` (N = siguiente
   número libre) para poder volver al estado justo anterior a este pase, no solo
   al original de fábrica.

## 1. Diagnóstico (una sola vez, con datos — no a ojo)

Con `trimesh` (instala si falta: `pip3 install trimesh scipy scikit-image rtree
networkx lxml shapely`), sobre la malla y el transform actuales:

- **Grosor de pared** por raycasting normal-a-normal (optimizar-pieza §3) —
  decide si hace falta engordar algo antes de tocar `detect_thin_wall`.
- **Volumen sólido-equivalente y shell_vol** (optimizar-pieza §3) — para poder
  reportar una proyección de peso/costo al final, aunque no se cambie el
  relleno.
- **Overhang bloqueado por la propia malla**: para cada cara con overhang por
  encima del `support_threshold_angle` configurado, lanza un rayo recto hacia
  abajo (en espacio MUNDO, con la malla ya escalada por el transform actual —
  la escala puede ser anisotrópica, no uses la malla local sin escalar) y
  comprueba si choca con la propia pieza antes de llegar al plato. Si un
  porcentaje no trivial del área con overhang queda bloqueado, eso es exactamente
  lo que `support_on_build_plate_only=1` deja sin soportar — la causa típica de
  "el volado daña la estructura" al imprimir.

## 2. Aplica en este orden fijo

### 2a. Calidad ("textura tipo lijada")
- `layer_height` → 0.12mm (si está en algo más grueso como 0.2).
- `top_shell_layers` / `bottom_shell_layers`: súbelos en la misma proporción en
  que baja `layer_height` (mismo grosor sólido en mm, más resolución).
- `ironing_type` → `"top surface"`. **Ojo**: esto alisa solo las superficies
  HORIZONTALES de arriba, no los costados curvos — no prometas "lijado" en toda
  la pieza, el resto del acabado depende del layer height y de la malla.
- `detect_thin_wall` → `"1"` **solo si** el diagnóstico de grosor de pared del
  paso 1 no muestra zonas al límite de 2 perímetros (si las hay, arréglalas
  primero con el método 4a de optimizar-pieza, o deja `detect_thin_wall` en 0 y
  anótalo como pendiente — activarlo sobre pared casi-mínima genera toolpaths
  erráticos, ver optimizar-pieza §4a).
- No toques `wall_loops` ni `sparse_infill_density` en este paso — eso es peso,
  va en el reporte del paso 3, no en calidad.

### 2b. Soporte / volado
Si el paso 1 encontró overhang bloqueado por la propia malla:
`support_on_build_plate_only` → `"0"` (deja que el soporte de árbol se apoye en
el modelo donde de verdad hace falta). Si el archivo no trae `support_type` en
`tree(auto)`, considera cambiarlo — los soportes de árbol necesitan menos
contacto y son más fáciles de retirar que los normales, lo cual ayuda
directamente a que el volado no dañe la pieza al despegar soporte.

### 2c. Tamaño
**Lección aprendida (no la repitas)**: estirar UN SOLO eje (ej. solo ancho) para
"hacerlo más grande" en una pieza que ya trae escala anisotrópica propia (común
en reconstrucciones foto→3D tipo "Image to 3D") rompe visualmente la proporción
— pecho ancho con cabeza angosta, patas separadas de forma antinatural. Pasó en
`reduced_color` el 2026-09-28 y hubo que revertirlo.

Por default, si el tamaño actual ya se ve bien proporcionado (o no hay feedback
específico sobre tamaño), **no lo toques**. Si el usuario sí pidió "más grande"
o "más robusto" sin especificar un eje: aplica una **escala UNIFORME** (mismo
factor en X, Y, Z — preserva exactamente la proporción que ya tiene el archivo,
sea o no anisotrópica) de ~+15-20%, recalculando SIEMPRE la traslación Z
(Tropiezo #3 de optimizar-pieza: `tz = -nuevo_factor_z · z_min_local_sin_escalar`,
verifica `factor_z·z_min_local+tz ≈ 0`) y, si el centro local de la malla no es
exactamente (0,0), recorrige tx/ty para mantener el mismo centro en el plato.
Si el usuario pide específicamente ensanchar/adelgazar UN eje puntual, usa
`AskUserQuestion` antes de aplicarlo — muéstrale la opción de escala pareja como
alternativa recomendada, no lo hagas a ciegas una segunda vez.

### 2d. Empaque — máximas copias en el mismo plato
1. Calcula el *convex hull* 2D (proyección XY) de la malla **local** (antes de
   escalar — el hull es invariante a escalado afín, así que `hull(malla) ×
   escala = hull(malla × escala)`), luego escálalo por los factores de escala
   actuales del transform (por eje, no asumas uniforme).
2. Busca con `shapely` la rotación (barrido cada 5-10°) que más copias permite:
   arma primero una fila/grilla simple con margen a bordes (~5mm) y separación
   entre piezas (~6-8mm, es cota conservadora porque el hull es más grande que
   la silueta cóncava real), y si sobra una franja utilizable, prueba una
   rotación distinta (90° típicamente) para una copia extra ahí.
3. Verifica con `polygon.distance()` entre cada par de hulls colocados que
   ninguna distancia caiga por debajo del margen — cero solapes, sin asumir.
4. Escribe los `<item>` nuevos en `3D/3dmodel.model` (mismo `objectid`, nuevo
   `p:UUID` por copia, transform = rotación·escala + traslación — ver fórmula
   de matriz fila abajo) y **sincroniza `Metadata/model_settings.config`**
   (Tropiezo #5): un `<model_instance>` y un `<assemble_item>` por copia nueva,
   con `identify_id` únicos (no reutilices los que ya existen en el archivo).

Fórmula de transform con rotación Z (convención fila-vector de 3MF,
`world = local · M + T`): con escala `(sx,sy,sz)` y ángulo `θ`,
```
M00,M01,M02 =  cosθ·sx,  sinθ·sx, 0
M10,M11,M12 = -sinθ·sy,  cosθ·sy, 0
M20,M21,M22 =  0,        0,       sz
```

## 3. Reporte de peso/costo (no lo cambies sin que lo pidan)

Con el volumen sólido-equivalente y el `shell_vol` implícito del paso 1,
proyecta el peso al tamaño/relleno actuales (optimizar-pieza §3). Repórtalo
junto con el trade-off si el usuario quisiera bajarlo: "con
`sparse_infill_density` X%→Y% se estima Zg (-N%), sin tocar `wall_loops` ni el
grosor de pared". No lo apliques a menos que el usuario confirme — es la única
palanca real de peso y compite con robustez, además de que "tiempo" (capa más
gruesa + `adaptive cubic`) compite con la calidad ya aplicada en 2a. Preséntalo
como una elección, no la tomes por él.

## 4. Verificación y cierre (siempre)

Antes de avisar que quedó listo:
```python
z = zipfile.ZipFile(ruta)
assert z.testzip() is None
# re-parsea el/los .model tocados: is_watertight, is_winding_consistent
# re-parsea project_settings.config: valores nuevos Y en different_settings_to_system
# si agregaste copias: instance_ids de model_instance == assemble_item == items del build,
#   identify_ids todos únicos, todas las bbox mundo dentro del plato (0..printable_area)
```
Reabre con `open -a "BambuStudio" "<ruta>"` y pide **Rebanar** para el peso/tiempo
reales — no inventes el número final. Actualiza
`.claude/optimizaciones/<slug>.md` (crea el archivo si es la primera vez que se
toca esta pieza, y agrégalo a `INDICE.md`) con qué se aplicó de este preset y
qué quedó pendiente de confirmar tras Rebanar.
