# Portacontroles4espacios ("portacontroles4e" en la tarjeta)

Archivo: `own design 3d/portacontroles4espacios.3mf`
Origen: comprado — "Desk Organizer Remote Control Holder" (MakerWorld, diseñador "RJ").
Backup original en `portacontroles4espacios.3mf.bak`.
Backup intermedio (tras el fix de wall_loops, antes del repack de 4 copias) en
`portacontroles4espacios.3mf.v2.bak`.
Perfil: **4 copias** idénticas en el mismo plato desde 2026-09-29 (antes 3; el peso
de slice_info sigue siendo de todas las copias juntas).

## Feedback recibido
- 2026-09-19 — Paredes más gruesas, un poco más largo, mejor calidad de acabado,
  reducir gramaje al máximo.
- 2026-09-19 (seguimiento) — En los bordes/esquinas curvas se ve muy delgado.
- 2026-09-19 (seguimiento) — Sigue igual y subió a 159g, ¿se puede reducir gramaje?

## Diagnóstico
- Grosor real medido (ray-cast por vértice): la mayoría de la pieza bien, pero en las
  puntas redondeadas de los extremos bajaba hasta **0.131mm** (144 de 7647 vértices
  por debajo de 1.2mm, concentrados en las puntas curvas).
- Subir `wall_loops` (2→3→4) NO arregló lo delgado ahí: el hueco de malla real era
  más angosto que lo que caben los loops configurados — es límite de geometría, no de
  perfil de impresión. Confirmado con el usuario notando "sigue igual" y el peso
  subiendo sin mejora visible.

## Cambios aplicados
- 2026-09-19: `wall_loops` 2→4, `layer_height` 0.2→0.12, `top_shell_layers` 5→8,
  `bottom_shell_layers` 3→5, `ironing_type`→"top surface", `sparse_infill_density`
  5%→4%, `detect_thin_wall`→1. (Primer intento sin registrar en
  `different_settings_to_system` → Bambu lo revertía solo; corregido después.)
- 2026-09-19: engrosamiento real de malla en las puntas curvas (empuje a lo largo de
  la normal, suavizado, solo en la zona deficiente) — grosor mínimo real
  0.131mm → 0.887mm, volumen 132.8→139.6cm³, sigue watertight/sin caras invertidas.
  Render antes/después confirmó que por fuera no se nota ningún bulto.
- 2026-09-29: re-medido el grosor tras el fix (sigue ~0.897mm mínimo, 5% de los
  vértices por encima de 2.0mm). Con eso encontrado, `wall_loops=4` ya no tenía
  sentido: en el punto más delgado solo caben ~2 perímetros físicamente (0.84mm),
  y forzar 4 con `detect_thin_wall=1` es la misma combinación que en
  [portacontroles03](portacontroles03.md) produjo el defecto "peludo/serrado" en la
  curva. Bajado `wall_loops` 4→3 (cubre el 99.6% de la superficie con 3 loops
  completos, solo 30/7647 vértices se quedan cortos y ahí el slicer ajusta solo) y
  `detect_thin_wall`→0. La malla (grosor real de pared) no se tocó — sigue
  cumpliendo el pedido original de "paredes más gruesas", el cambio es solo cuántas
  pasadas de perímetro usa el slicer, no cuánto material tiene la pared.

## Resultado real (confirmado por el usuario tras Rebanar)
- 2026-09-19: con solo el ajuste de perfil (antes de arreglar la malla) dio 159g
  (subió de la base, esperado: más wall_loops = más material, pero sin arreglar lo
  delgado).
- 2026-09-29: usuario confirmó **166.0g** (tarjeta del catálogo) con el arreglo de
  malla + perfil de 4 loops — este es el número que llevó a bajar `wall_loops` a 3
  para intentar recortarlo sin perder grosor real de pared.

## Pase /transform (2026-09-29)

Preset completo aplicado sobre lo ya diagnosticado, en el orden fijo del skill:

- **Calidad (2a)**: ya estaba todo aplicado de la sesión anterior (`layer_height`
  0.12, `top_shell_layers` 8, `bottom_shell_layers` 5, `ironing_type`="top surface").
  `detect_thin_wall` se dejó en 0 (ver arriba) porque el diagnóstico de grosor sí
  muestra zonas al límite — no se reactivó.
- **Soporte/volado (2b)**: medí overhang bloqueado por la propia malla (raycast
  hacia abajo desde cada cara con ángulo de overhang candidato, umbral 30° del
  perfil): **93% de las caras con overhang (3511/3776) chocan con la propia pieza
  antes de llegar al plato** — son techos internos de los 4 compartimentos, no
  overhang hacia el aire libre. `support_on_build_plate_only` ya estaba en `0`
  (correcto si hiciera falta soporte apoyado en el modelo), pero `enable_support`
  está en `0` (soporte completamente apagado). Los compartimentos en la foto tienen
  forma de arco/bóveda (curva), que suele ser autoportante — **no activé soporte a
  ciegas**: es una pieza ya vendida/impresa con este perfil, cambiar esto altera
  tiempo/material y el "look" interno. Queda como pendiente a decisión del usuario,
  no como cambio aplicado.
- **Tamaño (2c)**: sin feedback específico de tamaño en este pase y sin indicio de
  que el tamaño actual esté mal — no se tocó.
- **Empaque (2d)**: calculé el convex hull 2D de la malla (161.2×69.7mm, casi un
  rectángulo — 99.4% de su propio bounding box, así que ninguna rotación creativa
  gana espacio por sí sola) y probé si entraba una 4ª copia en el plato de 256×256.
  Sí entra: recorrí la columna de 3 copias 42.5mm hacia el borde izquierdo (mismo
  espaciado interno de 70mm entre ellas, sin tocarlo) y agregué una 4ª copia rotada
  90° en la franja libre de la derecha, con ≥6mm de holgura real (`shapely
  .distance()`) contra las 3 originales y dentro del plato. Sincronizado
  `3D/3dmodel.model` (nuevo `<object id="5">` + `<item>`), `model_settings.config`
  (`<object id="5">`, `model_instance`, `assemble_item`, `identify_id=139` único) y
  `cut_information.xml`. Verificado: zip íntegro, malla watertight/winding
  consistente, los 4 sets de ids coinciden entre archivos.
  - **Ojo con este tropiezo**: en el primer intento confundí los *bounds* del
    polígono ya trasladado con el propio *offset* de traslación al escribir el
    transform de la 4ª copia — la pieza quedó fuera de placa y solapada con las
    otras dos. Se detectó en la verificación (no se avisó al usuario como listo) y
    se corrigió recalculando `place_x/place_y` como el offset real, no el bounds
    resultante.
- **Peso/costo (§3, reportado, no aplicado)**: con el mismo perfil, 4 copias en vez
  de 3 se estima en **~221g total (~55.3g/pieza)**, escalando proporcional al peso
  medido de 166g/3 copias — es una proyección lineal, no un rebanado real.

## Velocidad de impresión (2026-09-29, seguimiento)
Usuario reportó que ahora tarda demasiado (esperado: `layer_height` 0.12mm desde la
sesión anterior es lo que más pesa en tiempo). Se ofrecieron 3 opciones
(capa 0.16mm intermedia, volver a 0.2mm, o solo cambiar patrón de relleno) — el
usuario eligió **solo cambiar el patrón de relleno**, dejando `layer_height` en
0.12mm (no quiere perder la calidad de acabado ya conseguida). Cambiado
`sparse_infill_pattern` `gyroid`→`adaptivecubic` (valor exacto confirmado contra
otras piezas del catálogo que ya lo usan: gato_japandi, portalapices10-2,
origami-elefante). Con solo 4% de relleno el ahorro de tiempo de este cambio es
menor que el que daría subir layer_height — avisado al usuario al ofrecer las
opciones, decisión informada.

## Pendiente / conocido y no resuelto
- Falta que el usuario abra el archivo en Bambu Studio, dé **Rebanar** y confirme:
  (a) el gramaje real con 4 copias + `wall_loops=3`, (b) que la curva ya no salga
  peluda/serrada, y (c) que las 4 copias se vean bien ubicadas en el plato (sin
  overlap visual, holguras suficientes para retirar piezas).
- Decisión pendiente del usuario sobre soporte: dejar `enable_support=0` como está
  (asumiendo que los techos curvos de los compartimentos son autoportantes, como
  parece ser por diseño) o activarlo — no se tocó por ser cambio de mayor impacto
  en una pieza ya vendida con este perfil.

## 2026-10-16 (v4) — "¿puedes ayudarme a mejorar el tiempo de este producto?"

Base medida por CLI (Bambu Studio 02.07, `--slice 1`) de la v3 tal como estaba:
**28 h 50 m y 663.1 g la placa de 4** (7.2 h y 166 g por pieza, igual que la
tarjeta). La `slice_info` guardada era vieja (3 copias, 13.8 h, 465 g).

Diagnóstico (`feature_type_times`):
- Paredes 17.9 h: cada pieza tiene ~1.29 m de pared por capa (divisores + ambas
  caras) × 980 capas de 0.12. La pared mide ~2.2 mm (área/medio perímetro de la
  sección): 3 vueltas de 0.45 no caben y 2 sobran → **relleno de hueco 3 h** y
  ~110 retracciones con salto en Z por capa (**viajes 5.6 h**).
- El filamento del proyecto es «Generic PLA @BBL P2S» con tope de **12 mm³/s**:
  a 0.12 casi no frena, pero a capa 0.2 sí (por eso capa 0.2 sola daba solo −25 %).
- Geometría: paredes rectas verticales de 0 a ~38 mm; de 38 a 118 mm los extremos
  se curvan (arcos).

Probado (placa de 4, CLI):

| Variante | Tiempo | Peso |
|---|---|---|
| v3 actual | 28 h 50 | 663.1 g |
| Arachne (3 vueltas) | 35 h 04 | 671 g — peor |
| `infill_combination`=1 / `filter_out_gap_fill`=2 | 28 h 50 / 28 h 55 | sin efecto |
| `retraction_minimum_travel` 1→3 | −30 a −35 min | — (no aplicado) |
| flujo 21 solo | 28 h 06 | — |
| capa 0.2 toda | 21 h 30 | 647 g |
| capa 0.2 + flujo 21 | 18 h 36 | 647 g |
| **2 vueltas, hilo interior 0.62 / exterior 0.45**, capa 0.12, flujo 21 | 20 h 04 | 661 g |
| ídem, rectas 0.2 / arcos 0.12 | 18 h 06 | 662 g |
| **ídem, rectas 0.2 / arcos 0.16 (elegida)** | **16 h 13** | **658.5 g** |
| ídem, todo 0.2 | 14 h 32 | 645 g |
| ídem todo 0.2, Arachne 2 vueltas | 13 h 27 | 535 g — la pared queda hueca con relleno 4 %, descartada |
| sin flujo 21 (12): todo 0.2 / arcos 0.16 / arcos 0.12 | 17 h 51 / 18 h 52 / 20 h 23 | — |

Cambios aplicados (usuario eligió «arcos 0.16» y dijo que imprime con Bambu PLA
Basic/Matte):
- `wall_loops` 3→2, `inner_wall_line_width` 0.45→0.62, `outer_wall_line_width`
  0.42→0.45 (misma pared maciza en mm, menos trazos; peso igual lo confirma).
- `Metadata/layer_config_ranges.xml` en los 4 objetos: 3–38 mm a 0.20, 38–118 mm
  a 0.16 (0–3 mm queda a 0.12 del perfil, el fondo).
- `filament_max_volumetric_speed` 12→21 (en la lista de filamento de
  `different_settings_to_system`).
- `slice_info.config` + `plate_1.gcode` regenerados con el CLI para que el archivo
  traiga el tiempo/peso nuevos. Malla y `3dmodel.model` sin tocar.

| | v3 | v4 | cambio |
|---|---|---|---|
| Placa de 4 | 28 h 50 m | 16 h 13 m | −44 % |
| Por pieza | 7 h 13 m | 4 h 03 m | −3 h 10 m |
| Peso por pieza | 165.8 g | 164.6 g | −1.2 g |
| Costo por pieza | $44.06 | $43.87 | −$0.19 |

Costo = g × 167 $/kg + $16.38 paquetería. Respaldo de la v3:
`portacontroles4espacios.3mf.v3.bak`.

Pendiente: imprimir la primera placa y revisar (a) la transición 0.2→0.16 a 38 mm
(no debe verse escalón), (b) que las paredes no subextruyan a 21 mm³/s, (c) que la
curva no salga peluda. `ironing_type` sigue en "top surface" (= sin planchado, así
se ha impreso siempre); no se tocó para no sumar tiempo.

## 2026-10-18 (v5) — "el borde de la parte inferior se ve cortado… ¿se puede bajar un poquito el precio?"

Feedback tras imprimir la v4: se perdió un poco de calidad, sobre todo el canto
inferior se ve cortado. Pidió además bajar costo, «pared 2.2→2.05» y que fuera
«un tris menos larga».

Diagnóstico:
- La base trae un **redondeo de ~5.5 mm tangente a la placa**: el contorno pasa de
  151 mm de ancho en z=0 a 161 mm en z=6. Abajo de ~1.3 mm el voladizo es casi
  horizontal (hasta 5 mm hacia adentro en z=0.02) → se imprime caído/cortado. Es la
  misma causa que en [portacontroles03](portacontroles03.md).
- La v4 cambiaba de capa 0.12 a 0.2 en z=3, a la mitad de ese redondeo: la curva
  cambiaba de textura a media altura.
- Costo: la pieza es ~95 % maciza (139.6 cm³ sólidos vs 164.6 g). Bajar techos y
  pisos (8/5 → 5/4) solo quitó 1.3 g por pieza (manda `top_shell_thickness` 1 mm);
  adelgazar el hilo interior sin cambiar la malla no ahorra nada (el gap fill
  rellena el hueco: 660 g y más lento). La única palanca real es la geometría.

Cambios (malla `object_2.model`, la usan las 4 copias):
- Debajo de z=1.33 el redondeo se cambia por un **chaflán de pendiente 0.8**
  (39° de la vertical, el tope que funcionó en portacontroles03): corte con
  manifold3d + contornos desplazados cada 0.03 mm. En z=0 el hueco pasa de 5.1 a
  2.8 mm. Arriba de 1.33 no se toca (empalma tangente).
- Pared adelgazada 0.3 mm por cara empujando vértices por su normal, solo donde la
  pared queda ≥1.75 mm (las puntas de 0.9 mm no se tocan); a z=20 mide 2.05 mm.
  Ojo: con caras planas grandes el empuje por normal de vértice no da el grosor
  exacto, hay que medir la sección después.
- Largo ×0.96 (161 → 154.5 mm; ancho 69.7 y alto 117.4 iguales). Hueco de cada
  compartimento a z=20: 37.8/36.8 → **36.3/35.3 mm** × 63.9 mm.
- Rangos de capa: 0.12 hasta **6.5 mm** (antes 3), 0.2 de 6.5 a 38, 0.16 arriba.
- `inner_wall_line_width` 0.62→0.42 y `outer_wall_line_width` 0.45→0.42
  (2 vueltas para la pared de 2.05).
- Malla verificada: watertight, winding consistente, base en z=0, ids de las 4
  copias iguales. `slice_info` y gcode regenerados con el CLI.

Probado (placa de 4, CLI):

| Variante | Tiempo | Peso |
|---|---|---|
| v4 | 16 h 13 | 658.5 g |
| A: chaflán + capa fina hasta 6.5 | 16 h 17 | 659.7 g |
| A + pared exterior a 150 mm/s | 17 h 06 | 659.7 g (no aplicado) |
| A + techos/pisos 5/4 | 16 h 59 | 654.4 g (no vale) |
| A + hilo interior 0.5 / 0.45 sin cambiar malla | 18 h 26 / 18 h 01 | 660 g (no ahorra) |
| pared −0.2/cara (2.11 mm), hilos 0.45 | 17 h 08 | 615.3 g |
| pared −0.3/cara (2.05 mm), hilos 0.42 | 17 h 07 | 589.7 g |
| **ídem + largo ×0.96 (elegida)** | **16 h 34** | **573.8 g** |

| | v4 | v5 | cambio |
|---|---|---|---|
| Placa de 4 | 16 h 13 | 16 h 34 | +21 min |
| Por pieza | 4 h 03 | 4 h 09 | +6 min |
| Peso por pieza | 164.6 g | 143.5 g | −21.1 g |
| Costo por pieza | $43.87 | $40.34 | −$3.53 |
| Ganancia (retorno $73) | $29.13 | $32.66 | +$3.53 |

Costo = g × 167 $/kg + $16.38 paquetería. Respaldo de la v4:
`portacontroles4espacios.3mf.v4.bak`.

Pendiente: imprimir y revisar (a) el canto inferior con el chaflán, (b) que los
controles del usuario entren en huecos de 35.3–36.3 mm, (c) la pared de 2.05 en
mano. Si vuelve a verse «peor calidad» en las rectas, la palanca es pared exterior
a 150 mm/s (+50 min la placa). La paquetería incluye maceta regalo + semillas +
tierra ($5.15); no se tocó.
