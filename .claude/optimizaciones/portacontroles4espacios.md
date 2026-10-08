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
