# FloreroOndulado (MakerWorld, generador "Make My Vase")

Archivo real: `~/Desktop/own design 3d/floreros/FloreroOndulado.3mf`
Backup de fábrica: `FloreroOndulado.3mf.bak` (creado 2026-10-01, antes de tocar nada).

## 2026-10-01: /transform completo

Diagnóstico con trimesh sobre la malla (transform identidad, escala 1 en los
tres ejes — no hay escala propia que considerar):

- Malla watertight y winding consistente (14,316 vértices / 28,628 caras).
- **Grosor de pared**: mediana **~2.0mm** en todo el muestreo (3000 rayos
  normal-a-normal), p5=1.72mm, solo 0.03% de muestras <0.8mm (ruido de borde,
  no zona real) — muy por encima del mínimo de 2 perímetros. `detect_thin_wall`
  se activó sin reparos.
- **Overhang bloqueado por la propia malla**: de 9,605.2 mm² de área con
  overhang por encima de `support_threshold_angle=30°` (9.26% del área total,
  en realidad la base/aro inferior, no volado real), **0.0%** queda bloqueado
  por un raycast recto hacia abajo antes de llegar al plato. Es un florero
  (recipiente), consistente con [[soportes-en-figuras]] (cero soporte es
  esperado en recipientes, no en figuras) — **no se tocó soporte**:
  `enable_support` sigue en `0`, `support_on_build_plate_only` ya estaba en
  `0`, `support_type` ya era `tree(auto)`.
- Volumen sólido-equivalente: **99.28 cm³**. Peso real de referencia (de
  `slice_info.config`): **115.30 g** (coincide exacto con la tarjeta del
  catálogo) a 15% infill / 2 wall loops / capa 0.2mm.
- `shell_vol` implícito ≈ **91.88 cm³** (92.5% del volumen sólido-equivalente)
  — la pared es naturalmente gruesa (~2mm), casi no queda cavidad para relleno;
  el diseño del generador "Make My Vase" ya resuelve la mayoría del volumen
  como pared sólida, no como infill.

### Aplicado (calidad, 2a)
- `layer_height`: 0.2 → **0.12mm**
- `top_shell_layers`: 5 → **8** (1.0mm, mismo grosor sólido)
- `bottom_shell_layers`: 3 → **5** (0.6mm exacto)
- `ironing_type`: `no ironing` → **`top surface`** (alisa boca/aro superior
  horizontal; no promete nada en los costados ondulados — eso depende del
  layer height, ya bajado)
- `detect_thin_wall`: 0 → **1** (seguro, sin zonas al límite)
- `wall_loops` (2) y `sparse_infill_density` (15%) sin tocar — eso es peso, va
  en el reporte.

### Soporte (2b)
Sin cambios — ver diagnóstico arriba, 0% de overhang bloqueado por la propia
malla, y es un recipiente (zero soporte es la convención esperada, no un
descuido).

### Tamaño (2c)
Sin cambios — no hubo feedback específico de tamaño.

### Empaque (2d) — máximas copias en el plato
Plato P2S 256×256mm. Convex hull 2D (XY) de la pieza mide **113.17 × 113.17mm**
(prácticamente circular — área del hull 9,620.9mm² vs 12,806mm² del bbox,
96% del área de un círculo circunscrito; rotar no gana nada por ser redondo).
Con margen 5mm a los bordes y separación 7mm entre piezas:
- **2×2 = 4 copias** en grilla (antes 1). Separación real verificada con
  `shapely .distance()` = exactamente 7.0mm en los 4 pares vecinos, diagonales
  a 60.5mm. Las 4 bbox caen dentro de `[11.33, 244.67]` en X/Y, dentro del
  plato con margen.
- `3D/3dmodel.model`: 4 `<item>` del mismo `objectid=2`, `p:UUID` únicos.
  `Metadata/model_settings.config` sincronizado: 4 `model_instance` +
  4 `assemble_item`, `identify_id` 203 (original) + 204/205/206 (nuevos, no
  colisionan).

### Reporte de peso/costo (NO aplicado, solo informativo)
Peso por pieza no cambia con lo aplicado arriba (mismo wall_loops, mismo %
infill, shells mantienen el mismo grosor en mm) — sigue ~115.3 g/pieza, $34.21
c/u (peso/1000 × $175/kg + $14.04 paquetería). El plato completo con 4 copias
ronda **~461 g** totales.

Si se quisiera bajar peso, la palanca real (`sparse_infill_density`) rinde
muy poco en esta pieza: con `shell_vol`≈91.88cm³ siendo 92.5% del volumen
total, bajar 15%→5% proyecta apenas **~114.4 g/pieza (-0.8%)** — no vale la
pena tocarlo, la pared ya es casi maciza por diseño del generador. No se
aplicó.

### Verificación hecha
- `zipfile.testzip()` → None (zip íntegro).
- Malla re-parseada: watertight + winding consistente.
- `model_instance` / `assemble_item` / items del build: 4 = 4 = 4,
  `identify_id` únicos (203, 204, 205, 206).
- Bbox mundo de las 4 copias dentro de 0..256 en X/Y, z_min=0 en todas.
- `different_settings_to_system` actualizado para incluir las keys nuevas.

### Pendiente
- Reabrir en Bambu Studio (ya se hizo `open -a`) y pedir **Rebanar** para
  confirmar peso/tiempo reales — el peso de 115.3g/pieza es el de referencia
  anterior (capa 0.2mm, 1 copia), no una medición nueva con capa 0.12mm.

## 2026-10-28 (v2) — "hacer una grande y una pequeña para mejorar el paquete y que quepan en la caja, y bajar de 122 g sin perder la calidad"

Feedback: tarjeta a 122.0 g / $36.75. Pidió un set grande + chica que quepa en la
caja 20×16×11 y bajar de 122 g sin perder calidad.

### Diagnóstico
- Línea base laminada por CLI (v1, una pieza, capa 0.12): **122.05 g, 2 h 59**.
  31 min de «Internal solid infill»: la pared de la malla mide 2.0 mm y los 4
  hilos (2 vueltas por cada cara, 0.42+0.45) solo ocupan 1.74 mm; el hueco
  intermedio se rellena sólido.
- El v1 no cabe en la caja ni solo: 113 mm de diámetro contra 110 de alto.
- `ironing_type` = «top surface» (inválido) → Bambu lo trataba como sin alisado.
  Corregirlo a «top» alisaba cada escalón de la curva: **+33 min** sin beneficio
  visible. Se dejó explícito «no ironing».

### Cambios
- Cara interior desplazada a lo largo de su normal hasta **pared 1.7 mm**
  (vértices interiores: normal hacia el eje, |nz|<0.9, fuera de base y boca;
  4 pasadas de suavizado). Cara exterior, base y boca intactas. Verificado:
  watertight, winding consistente, 0 caras invertidas, pared p1–p95 1.69–1.71.
- Set: **grande ×0.90 (102×102×159 mm)** + **chica ×0.60 (68×68×106 mm)**, ambas
  con la pared re-afinada a 1.7 mm en absoluto (la chica escalada sola daría 1.2).
- Caja 20×16×11: acostados uno con la boca hacia cada lado (perfil de revolución,
  3 mm de holgura); sobran ~12 mm de separación entre ejes para burbuja.
- Plato P2S: **3 sets** (3 grandes + 3 chicas), separación ≥7 mm, margen 5 mm.
- `.3mf` con dos objetos (id 2 grande → object_1.model, id 4 chica →
  object_2.model); model_settings/assemble/cut_information sincronizados.
  Miniatura `plate_1.png` = vista frontal del precheck.
- `.catalogo3d_mercadolibre.json`: `peso_g` 122.0 → 119.3 (por set).

### Tabla (CLI Bambu, capa 0.12)
| Versión | Medidas | Peso | Tiempo | Costo |
|---|---|---|---|---|
| v1 una pieza | 113×113×176 | 122.05 g | 2 h 59 | $36.75 |
| v2 mismo tamaño afinado (no se usó) | 113×113×176 | 108.1 g | 2 h 41 | $34.43 |
| v2 grande ×0.90 | 102×102×159 | 84.7 g | 2 h 13 | — |
| v2 chica ×0.60 | 68×68×106 | 34.6 g | 1 h 16 | — |
| **v2 plato 3 sets** | | **357.9 g** | **9 h 31** | — |
| **v2 por set** | | **119.3 g** | **3 h 10** | **$36.31** |

Costo = g × 167/1000 + $16.38 (una caja por set). Probado y descartado: chica
×0.65 con 1.7 mm (41.4 g, set 126 g), grande ×0.92 (89.8 g).

Respaldo: `FloreroOndulado.3mf.v1.bak` (v1 del 10-01, 4 copias).

### Pendiente
- Imprimir el set y confirmar acabado de la pared de 1.7 mm y que entra en la caja
  con burbuja.
- Publicación «florero Ondas»: pasarla a set (mismo trámite que el minimalista,
  ojo con family_name y título) y subir precio hacia $256–283.
