# Loop_Remote_Control_Holder_by_Pork_3D(2)

Archivo: `own design 3d/Porta controles/Loop_Remote_Control_Holder_by_Pork_3D(2).3mf`
Origen: comprado — Pork3D (Pork3D.com), "Loop Remote Control Holder". Backup del
original (2 piezas, 116 g c/u): `...(2).3mf.bak`. Diseño en cuña (anillo extruido en Z,
78.8 mm de alto, huella 192.7×81.1 mm), 4 ranuras en la pared inclinada, mismo mesh
(`object_5.model`) para ambas piezas, escala 0.8759, ya con perfil P2S y plato 256.

## Feedback recibido
- 2026-09-24 — Aplicar las mismas optimizaciones de espacio para que quepan 3,
  agujeros (ranuras) un poco más grandes, e imprimir un poco más rápido sin perder
  calidad.

## Diagnóstico
- Las 2 piezas originales ocupaban 163 mm de Y (huella apilada 81.1 c/u, hueco de ~1 mm);
  3 apiladas serían ~245 mm + huecos: no cabía con margen seguro.
- La huella es una **cuña** (45 mm de alto a la izquierda, 81 a la derecha): girando una
  copia 180° su borde inclinado encaja contra el de la otra (pitch ~57 mm en vez de 81).
- 4 ranuras de 22.2×57.4 mm (mundo) en la pared inclinada (12.8°), paso 36.4 mm, costillas
  de 14.2 mm. Las paredes son ~10 mm de espesor (relleno importa mucho); en los extremos
  de cada ranura hay un labio biselado de 10 mm de profundidad.
- Tiempo/peso reales de la cinta original (rebanado CLI con P2S + Generic PLA P2S, coincide
  con la predicción guardada 6.63 h): **6.52 h las 2 piezas** (3.26 h c/u); sparse infill
  (crosshatch 12%) = 2.35 h, paredes 3.0 h, travel 0.63 h.
- El `Metadata/layer_heights_profile.txt` traía un perfil adaptativo viejo (0.08–0.2 mm,
  para z 0–90, sobrante de otra orientación) que no se aplicaba (394 capas a 0.2); se quitó
  para que no pueda activarse por error.

## Cambios aplicados
- 2026-09-24 (geometría, boolean con manifold3d en el marco del mesh): 4 cortadores
  redondeados (r=2) con ranura **+3.0 mm de ancho (25.2 mm) y +3.6 mm de alto (61.0 mm)**
  cada una; costillas 14.2→11.2 mm; profundidad de corte -3…12 mm respecto a la cara
  exterior (a menos de ~10 mm deja un resto del labio y produce rebabas finas). Malla
  resultante watertight/winding OK, volumen −3.5% (380.4→366.9 cm³ mesh).
- 2026-09-24 (layout): 3 `<item objectid="2">` del mismo objeto (se eliminó el objeto 3,
  duplicado; `model_settings.config` con 3 `model_instance` y 3 `assemble_item`, mismos ids
  que `3dmodel.model`). Copia A abajo (rot 0), copia B **girada 180° sobre Z** encajada en
  su borde inclinado (hueco mínimo 7.6 mm), copia A' encima (hueco plano 10 mm), X=128.
  Centros Y 53.3 / 111.8 / 202.8, huella total 230.6 mm de 256 (márgenes ~12.7 mm).
  Verificado con distancia raster (0.25 mm) y con el propio rebanador (CLI, `--arrange 0`):
  las 3 en un plato.
- 2026-09-24 (velocidad, `project_settings.config`): `sparse_infill_pattern`
  crosshatch→**adaptivecubic**, `sparse_infill_density` 12%→**10%** (ya en
  `different_settings_to_system`). Sin cambios a capas (0.2), paredes (2), velocidades ni
  costura → la superficie exterior es idéntica.
  - Comparativa por pieza (CLI): original 3.26 h / 116 g → nuevo **2.67 h / ~100 g**
    (−18% tiempo, −14% peso). Las 3 juntas: **8.0 h**, ~299 g (peso estimado sumando E del
    gcode ×1.108 de calibración contra los 232.89 g reales de la cinta original).
  - Descartados: `lightning` 10% (1.97 h/pieza, ~71 g) por dejar las paredes de 10 mm casi
    huecas; `grid` 10% (2.87 h) y `grid` 8% (2.75 h) ahorran menos que adaptive cubic;
    subir a 4 perímetros (12.4 h) es más lento.
- Se quitaron `Metadata/plate_1.gcode`/`.md5` (rebanado viejo de otra geometría — evita
  mandar a imprimir un gcode desactualizado) y se regeneró `plate_1.png` (la tarjeta del
  catálogo). `slice_info.config` quedó con el peso viejo (232.89 g, 2 piezas) hasta que
  el usuario vuelva a rebanar y guardar.

## Resultado real (pendiente)
- Falta que el usuario abra, rebane y confirme: tiempo (~8.0 h predicho), gramaje (~300 g
  las 3) y que las ranuras nuevas se vean bien.

## Pendiente / conocido y no resuelto
- Al rebanar el 3-piezas el CLI imprime 2 líneas `ZFiller: encounter idx from clip` (aparece
  también con la malla original en este layout, solo con las 3 copias; no afecta el resultado
  "Success"). Probablemente solapamiento de brim (auto_brim 5 mm) — inofensivo.
- El filamento del proyecto es Generic PLA (12 mm³/s máx); con Bambu PLA Basic (21 mm³/s)
  saldría más rápido, pero no se cambió por no saber qué carrete usa el usuario.
- CLI de Bambu Studio: para rebanar un .3mf generado/editado a mano hay que pasar
  `--load-settings "<maquina aplanada>;<proceso>"` con la máquina **resuelta** (con
  `printable_area` heredado del padre) y `--load-filaments`, si no usa un plato de 180-200 mm
  y un filamento de 2 mm³/s (tiempos absurdos de 16-20 h). Ver [portacubiertos-torsion.md].
