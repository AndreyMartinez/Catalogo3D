# TripleRemoteHolder

Archivo: `own design 3d/TripleRemoteHolder.3mf`
Origen: comprado (Designer: lunatiic, MakerWorld «Remote Control Caddy / Remote
Control Holder», licencia «MakerWorld Exclusive License»)

Portacontroles de 3 compartimentos en fila, exterior con estrías verticales y boca
en **plano inclinado** (87 → 125 mm de alto a lo largo de 144 mm, ~15° sobre la
horizontal). Escala anisotrópica que ya traía el archivo: 1.380 × 1.641 × 1.569 →
**81.2 × 144.1 × 125.5 mm** por pieza.

## Feedback recibido
- 2026-10-12 — `/transform` con la tarjeta («sin laminar», «falta peso y retorno»).

## Diagnóstico (2026-10-12)
- Malla: 9 792 caras, cerrada y con orientación consistente.
- Grosor de pared: mínimo 2.14 mm (p1), mediana 5.7 mm — pared gruesa con relleno
  adentro; sin zonas al límite de 2 perímetros → `detect_thin_wall` 1 es seguro.
- Voladizo sobre 30°: **0 mm²**. El archivo traía `enable_support` = 1 (perfil del
  diseñador) y el CLI marcaba `support_used`, pero el G-code no tenía ni una línea
  de soporte → se apagó (recipiente, cero soportes).
- Volumen sólido-equivalente 290.8 cm³/pieza; shell_vol implícito ≈ 121 cm³ (≈ 42 %);
  el relleno (10 % gyroid) ocupa ≈ 170 cm³.
- Tiempo: 81 % de las extrusiones son paredes (exterior + interior); ~8
  retracciones por pieza por capa (contorno + 3 huecos + islas de relleno).
- Costo con `.catalogo3d_costos.json` al 10-12: 170 $/kg + paquetería **$16.38**.

## (v1) 2026-10-12 — /transform
Respaldo: `TripleRemoteHolder.3mf.bak` (= v0, como estaba en el catálogo; no había `.png` aparte).

Cambios:
- Capa 0.20 → **0.16** en el cuerpo (z < 86 mm) y **0.12 en la boca** (z ≥ 86 mm, rango
  en `Metadata/layer_config_ranges.xml`, los 4 objetos iguales). Shells 5/3 → 7/4.
- Planchado **solo en la boca** (`ironing_type` = `top` dentro del rango; global
  `no ironing`). Con `top` global también planchaba los fondos de los 12
  compartimentos: +2 h 34 min por plato sin verse.
- `infill_combination` 0 → 1 (palanca gratis en pared gruesa con relleno: −12 % de tiempo).
- `detect_thin_wall` 0 → 1. `enable_support` 1 → 0.
- Tamaño sin tocar (sin feedback).
- Plato: 2 → **4 copias en molinete** (90/180/270/0°): convex hull 81.15 × 144.05,
  cuadro de 232.2 mm, 7 mm entre hulls (verificado con shapely), 11.9 mm al borde.
  En fila solo cabían 2 (3 × 81 + huecos > 246). Objetos 4 y 5 nuevos; ids
  sincronizados en `3dmodel.model`, `model_settings.config` (identify_id 301 y 388)
  y `cut_information.xml`.
- `slice_info.config` y `plate_1.json` del laminado CLI, y miniatura `plate_1.png`
  regenerada con `generadores/nucleo/render.py` (el CLI no dibuja).

Variantes laminadas con el CLI de Bambu Studio 02.08 (por pieza; costo = g × 0.170 + 16.38):

| Versión | Plato | Capa / planchado | Tiempo plato | Tiempo pieza | g pieza | Costo pieza |
|---|---|---|---|---|---|---|
| v0 (original) | 2 | 0.20, sin planchar | 10 h 52 | 5 h 26 | 170.8 | $45.42 |
| **v1 (aplicada)** | 4 | 0.16 + boca 0.12 planchada, infill_combination | 25 h 26 | **6 h 21** | 173.7 | $45.90 |
| preset puro | 4 | 0.12 todo + planchado `top` | 32 h 04 | 8 h 01 | 175.3 | $46.18 |
| 0.12 sin planchar | 4 | 0.12 todo | 29 h 30 | 7 h 23 | 175.1 | $46.15 |
| 0.16 sin planchar | 4 | 0.16 todo | 23 h 52 | 5 h 58 | 174.1 | $45.98 |
| rápida | 4 | 0.20 + boca 0.12 planchada | 21 h 55 | 5 h 29 | 167.2 | $44.80 |
| v1 + relleno 5 % (no aplicada) | 4 | como v1 | 24 h 24 | 6 h 06 | 161.1 | $43.77 |

Por qué no el preset puro (0.12 en todo): es portacontroles (48 % de las ventas
de 90 días, *medido*) y 8 h por pieza en un plato de 32 h pesa; en las paredes
verticales estriadas la capa fina luce poco. La capa fina va donde sí se nota, la
boca inclinada (~15°, escalón de 0.45 mm con 0.12 vs 0.75 mm con 0.20). Es el mismo
criterio que se aceptó en pORTAcONTROLES03 (0.16 en pared recta).

## Hallazgo (afecta a otras piezas)
`ironing_type` = `"top surface"` **no es un valor válido**: Bambu lo cambia en
silencio a `no ironing` (comprobado en el G-code). Los válidos son `no ironing`,
`top`, `topmost`, `solid`. Wolken-Stiftehalter, pORTAcONTROLES03 y
Portacontrol_borderedondo01 tienen `"top surface"` → nunca se plancharon.
Corregido en `transform` §2a y `optimizar-pieza` §4c.

## Pendiente
- Rebanar en la app y confirmar tiempo y peso; el CLI se ha quedado corto en
  tiempo antes (01O: 18.7 h CLI vs 26 h real).
- Imprimir y ver la boca: si el escalón aún se nota, bajar el rango a 0.08.
- Relleno 5 % (−12.6 g, −$2.13 por pieza): decisión del usuario.
- Revisar la licencia «MakerWorld Exclusive License» antes de venderlo.
- Competencia directa: el imitador MLM5971780506 (Vimi Shop) vende un
  portacontroles de 3 compartimentos con estrías a $154.23 en Full.
