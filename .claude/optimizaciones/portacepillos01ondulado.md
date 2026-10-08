# Portacepillos01ONDULADO ("Portacepillos01O" en la tarjeta)

Archivo: `own design 3d/portacepillos/Portacepillos01ONDULADO.3mf`
Origen: comprado — "Verdali" dual cup holder (MakerWorld, "Twisted Design").
Backup original en `Portacepillos01ONDULADO.3mf.bak`.
Estructura: 4 objetos "Cup" (ids 2,3,6,7) + 2 objetos "Tray" (ids 5,8), cada grupo
comparte la misma malla base (`object_21.model` los vasos, `object_18.model` las
bandejas) con distinta escala/posición por instancia.

## Feedback recibido
- 2026-09-19 — Se vende muy bien pero cuesta demasiado producir. Optimizar al máximo
  sin perder la sensación de peso.
- 2026-09-19 (seguimiento) — Mejorar calidad de acabado, y probar angostar los vasos
  (menos ancho) compensando con un poco más de altura, para ahorrar en la bandeja y
  en el ancho de los vasos.

## Diagnóstico
- Costo real: $102.50 = material ($86.40 = 493.7g × $175/kg) + paquetería ($16.10,
  paquete "Paquetería" de `.catalogo3d_costos.json`).
- **Ojo — sin confirmar con el usuario**: el paquete "Paquetería" que se le cobra
  incluye "Maceta regalo" ($4.00) y "Nuevo tarro tierra" ($1.50), que suenan a
  insumos de un producto de plantas, no de un portacepillos. El usuario no confirmó
  si es error o intencional — se dejó sin tocar. Posible ahorro extra de $5.50 sin
  tocar la pieza física, pendiente de confirmar.
- Grosor real medido: vasos mediana ~4.67mm, bandeja mediana ~4.65mm — es una pieza
  CASI MACIZA (no hueca con paredes finas). Por eso bajar el relleno interno tiene
  poco efecto: de 15%→4% solo ahorra ~19g (~$3.30). El shell (paredes+techos+piso)
  es ~73% del volumen sólido-equivalente total en el modelo usado.
- Volumen sólido-equivalente original: 4 vasos × 78.5cm³ + 2 bandejas × 100.5cm³ ≈
  515.3cm³.

## Cambios aplicados
- 2026-09-19: `sparse_infill_density` 15%→6% (con `different_settings_to_system`
  correcto desde el inicio esta vez).
- 2026-09-19: bandeja (objetos 5 y 8) reescalada a 90% en X/Y (footprint) y 85% en Z
  (alto) — de ~160×88×11mm a ~144×79×9mm. **Primer intento falló**: se editó
  `Metadata/model_settings.config` → `<assemble_item transform>` (solo metadata de
  la vista Ensamblar, no afecta el rebanado). Corregido reescalando el transform real
  en `3D/3dmodel.model` → `<build><item objectid="5"/"8" transform=...>`.
- 2026-09-19: calidad — `layer_height` 0.2→0.12, `top_shell_layers` 5→8,
  `bottom_shell_layers` 3→5, `ironing_type`→"top surface".
- 2026-09-19: vasos (objetos 2,3,6,7) reescalados a 90% en diámetro (X/Y) y 108% en
  alto (Z) — de ~68.3×68.4×88.3mm a ~61.5×61.5×95.4mm. Ojo: esto NO preserva la
  capacidad interna (el diámetro pesa cuadrático, la altura solo lineal), se lo
  avisé al usuario como compensación parcial, no exacta.

## Resultado real (confirmado por el usuario tras Rebanar)
- 2026-09-19: tras el primer intento (infill 6% pero bandeja SIN reescalar de
  verdad, por el error del assemble_item) → 473g reales, muy cerca de lo predicho
  solo-por-infill (~478g), confirmando que el resize no había pegado.
- 2026-09-19: tras corregir el resize de bandeja + vasos + calidad, el usuario
  confirmó "qué cambio tan drástico funcionó perfectamente" (no dio el número
  exacto, pero validó el resultado). Estimado en ese momento: ~384g / ~$83.25
  (de 493.7g / $102.50).

## Pendiente / conocido y no resuelto
- Confirmar con el usuario si "Maceta regalo" / "Nuevo tarro tierra" en la
  paquetería son un error (ahorro de $5.50 sin tocar la pieza).
- Confirmar en mano que el vaso más angosto/alto no se siente "flaco" (el usuario no
  ha reportado esto explícitamente, solo que "funcionó perfectamente" en general).

## Bug encontrado y corregido (2026-09-19)
El usuario reportó, tras rebanar, que los vasos se veían "sin base" desde abajo en
Bambu Studio. Verificado: la malla NUNCA estuvo dañada (watertight=True siempre,
confirmado con render propio desde abajo que coincidía con lo que mostraba Bambu).
La causa real: al reescalar los vasos en Z (×1.06, para "un poco más altos") y la
bandeja en Z (×0.85), solo cambié el factor de escala en el transform y dejé la
traslación Z **sin recalcular** — la traslación estaba calibrada para que la base
cayera en mundo Z=0 con la escala VIEJA. Resultado: los vasos quedaron ~3.5mm por
debajo del plato (la impresora corta todo lo que queda bajo Z=0 → "sin base"), y la
bandeja quedó flotando ~0.8mm sobre el plato.
Corregido recalculando `tz = -escala_z_nueva × z_min_local_de_la_malla_sin_escalar`
para los 6 objetos (vasos: z_min=-45, bandeja: z_min=-5). Verificado releyendo el
transform: `escala_z × z_min + tz = 0.0` exacto para los 6.
Esto quedó como "Tropiezo #3" en el SKILL.md — aplica a cualquier pieza futura donde
se reescale en Z.

## 2026-09-27 — Pedido: reducir tiempo (prioridad #1), sin perder el acabado actual;
peso y tamaño solo si se puede sin sacrificar lo anterior.

## Diagnóstico — causa real del tiempo (no es infill ni relleno)
- Rebané el archivo actual (ya con el resize + capa 0.12 de la sesión anterior) por línea de
  comandos: **34.0 horas**, de las cuales **13.6 h (40%) son puro desplazamiento del cabezal**
  (nada de eso imprime). 470,412 movimientos de traslado, 3.38mm en promedio cada uno.
- Probé las palancas típicas y NINGUNA de estas tocó el tiempo real:
  - Patrón de relleno (grid→adaptive cubic): sin cambio (ya casi no hay relleno, 6%).
  - Patrón de relleno sólido interno (concéntrico): sin cambio.
  - Subir a 3-4 perímetros: **empeoró** a 43h (más "gap infill" fragmentado — la onda no
    encaja limpio con más vueltas de pared).
  - `travel_short_distance_acceleration` (sospechaba que sea el freno de los saltos
    cortos): sin cambio, esa configuración no es lo que domina el tiempo aquí.
- **La causa real: `retraction_minimum_travel = 1mm`** (ajuste de la IMPRESORA, no de la
  pieza ni del perfil de impresión). Con eso, CUALQUIER salto mayor a 1mm dispara una
  retracción + levantamiento en espiral (z-hop) + de-retracción completos. Con una pieza
  casi maciza y superficie ondulada, prácticamente todos los ~470 mil saltos superan 1mm,
  así que la impresora hace ~470 mil ciclos completos de retracción en vez de solo saltar.
  Confirmado con el propio rebanador (cambiando este único valor, sin tocar geometría,
  capa, relleno ni perímetros):
  - 1mm (como está): 34.0h, viajes 13.6h
  - 3mm: 26.35h (−22%)
  - **5mm: 20.55h (−40%), viajes bajan a 3.6h**
  - 8mm/10mm: 20.43h — ya no mejora más allá de 5-6mm.
- Por qué es seguro: estos saltos ocurren DENTRO del volumen casi macizo de la pieza (entre
  fragmentos internos), no cruzando huecos al aire libre visibles desde fuera — subir el
  umbral no debería notarse en la pared ondulada exterior, que es la que se ve. No toca
  capa (sigue en 0.12mm), relleno, perímetros ni ninguna geometría — el acabado que "quedó
  perfecto" la vez pasada no se tocó en absoluto.

## Cambios aplicados (2026-09-27)
- Ninguno en el archivo .3mf en sí — **`retraction_minimum_travel` es un ajuste de la
  IMPRESORA (perfil de máquina), no del proyecto**. Lo probé metiéndolo directo en
  `project_settings.config` del .3mf y Bambu Studio lo ignora (no es una llave que el
  perfil de impresión/proyecto pueda sobre-escribir; solo vive en el perfil de la
  impresora). Necesita cambiarse en Bambu Studio mismo (ver instrucciones al usuario en
  el chat) — no lo hice por archivo para no arriesgar tocar el perfil de impresora
  "Bambu Lab P2S 0.4 nozzle" que usan TODOS los demás diseños sin que el usuario lo pida
  explícitamente.
- Sí se quitó el `plate_1.gcode`/`.md5` viejo del archivo (quedaba desde antes del
  resize, ya no corresponde a la geometría actual). Backup: `.3mf.v2.bak`.
- No se tocó tamaño ni layout: el plato ya está lleno de esquina a esquina (x:15.7-241.6,
  y:6.7-246.4 de 256×256) con los 2 juegos actuales — no hay margen para agrandar ni para
  meter un tercero sin rediseñar el acomodo completo.
- Peso: no se tocó (ninguna palanca de relleno dio ahorro real por ser pieza casi maciza,
  ver diagnóstico de la sesión 09-19). Sigue siendo la misma pieza, mismo peso.

## Pendiente / conocido y no resuelto
- **Acción pendiente DEL USUARIO en Bambu Studio**: cambiar `retraction_minimum_travel` de
  1mm a 5mm en el perfil de la impresora P2S (Ajustes de impresora → buscar "retracción"/
  "retraction" → el campo de distancia mínima de viaje antes de retraer). Esto aplica a
  esta impresora en general, no solo a esta pieza — beneficiaría a cualquier otro diseño
  casi macizo con textura (portacontroles, portalápices, etc.) si tienen el mismo patrón
  de fragmentación.
- Pesa/tamaño "imponente": no hay margen físico en el plato actual para agrandar. Si se
  quiere más grande, habría que sacrificar uno de los 2 juegos actuales o rediseñar el
  acomodo desde cero.
- Sigue sin confirmarse con el usuario si "Maceta regalo"/"Nuevo tarro tierra" en la
  paquetería son un error (pendiente desde 09-19).
- Sigue sin resolverse la diferencia entre el peso real guardado a mano (207g) y lo que
  calcula el propio archivo/mi estimador (493g / ~720g) — no se investigó a fondo esta
  sesión, el usuario no respondió qué representa el 207g.

## 2026-09-28 — Seguimiento: sí se pudo automatizar
El usuario preguntó si de verdad no había forma de aplicarlo yo mismo. Sí la había: un
perfil de impresora PERSONALIZADO (no tocar el sistema "Bambu Lab P2S 0.4 nozzle" que
usan todos los demás diseños).

- Encontré ejemplos reales de presets de usuario ya guardados por el propio usuario
  (`~/Library/Application Support/BambuStudio/user/3786897911/filament/*.json` + `.info`,
  creados con "Guardar como" desde la app) — de ahí saqué el esquema mínimo real: solo
  `name`/`inherits`/`from`/`version` + las llaves que cambian, SIN necesidad de duplicar
  todo el perfil. Confirmé el ID de usuario activo (`preset_folder` en
  `BambuStudio.conf` → `3786897911`).
- Creé 3 presets de usuario nuevos (todos con el sufijo "- saltos rapidos", heredando
  100% del original salvo lo indicado):
  - `user/.../machine/Bambu Lab P2S 0.4 nozzle - saltos rapidos.json`:
    `retraction_minimum_travel` 1→5mm (la causa real, ver sesión 09-27).
  - `user/.../process/0.20mm Standard @BBL P2S - saltos rapidos.json`: necesario porque
    el proceso original solo declara `compatible_printers: ["Bambu Lab P2S 0.4
    nozzle"]` — con la impresora nueva, Bambu Studio rechaza el proceso viejo por
    "no compatible". El nuevo apunta `compatible_printers` a la impresora nueva.
  - `user/.../filament/Bambu PLA Matte @BBL P2S - saltos rapidos.json`: mismo problema,
    mismo arreglo (el filamento original también restringe `compatible_printers`).
  - Verifiqué el esquema exacto (sin inventar `setting_id`/`base_id`) probando primero
    con `--load-settings` apuntando directo al archivo — dio 20.54h, igual que el
    perfil de máquina aislado de la sesión anterior. Confirma que el JSON en sí es
    válido para el motor de rebanado.
- Cambié `printer_settings_id`/`print_settings_id`/`filament_settings_id` del proyecto
  a estos 3 nuevos presets (el resto de overrides del proyecto — capa 0.12, relleno 6%,
  etc. — siguen intactos en `different_settings_to_system`, no se tocaron).
- **Limitación real, no pude eliminarla**: el binario de línea de comandos de Bambu
  Studio (el que uso para verificar) NO resuelve presets de usuario por nombre desde
  el .3mf solo — solo los encuentra si se le pasan con `--load-settings` explícito.
  No pude confirmar 100% que la app de escritorio (GUI) sí los recoja solo con
  reiniciarla, aunque es el comportamiento estándar de este tipo de apps
  (Bambu/Prusa/Orca Slicer) al reescanear la carpeta de usuario al abrir. Le pedí al
  usuario reiniciar Bambu Studio (cerrar del todo, no solo la ventana) antes de abrir
  este archivo — si el desplegable de impresora no la reconoce, el respaldo es el
  método manual (cambiar `retraction_minimum_travel` a mano en Ajustes de impresora).
- Backup antes de este cambio: no se hizo uno nuevo (el `.3mf.v2.bak` de la sesión
  09-27 sigue siendo el respaldo válido — solo cambiaron las referencias de
  perfil/impresora, no la geometría ni el resto de ajustes).

## Pendiente / conocido y no resuelto (actualizado)
- Confirmar que Bambu Studio, tras reiniciarse, muestra y usa el perfil
  "Bambu Lab P2S 0.4 nozzle - saltos rapidos" al abrir el archivo, y que al Rebanar da
  ~20.5h (no 34h). Si no aparece en el desplegable, aplicar el cambio a mano como
  respaldo (ver sesión 09-27).
- Si funciona bien, vale la pena aplicar el mismo perfil de impresora "- saltos
  rapidos" a otras piezas casi macizas con textura (revisar portacontroles,
  portalápices) — no se tocó ningún otro archivo esta sesión.

## 2026-09-28 (seguimiento) — Reabrí el archivo para verificar, y encontré un bug real
Cerré Bambu Studio del todo (`osascript ... quit`) y lo reabrí con este archivo para que
detecte los presets de usuario nuevos. Al abrir salió un aviso de la propia app:

> "ironing_type": "top surface" fue reemplazado por "no ironing"

Esto **no tiene que ver con el perfil de impresora nuevo** — es un bug viejo, ahí desde la
sesión 09-19: la clave interna correcta de Bambu Studio para ese valor es **`topmost`**, no
`"top surface"` (confirmado buscando las claves válidas reales en el binario de la app:
`no ironing`, `topmost`, `solid`). Como `"top surface"` no es una clave válida, la app lo
viene sustituyendo en silencio por `no ironing` **cada vez que se abre el archivo desde
hace más de una semana** — el planchado que se activó para mejorar el acabado en 09-19
probablemente nunca se estuvo aplicando de verdad al rebanar. Corregido: `ironing_type` →
`"topmost"`.
- No pude confirmar visualmente en pantalla si el desplegable de impresora ya muestra
  "Bambu Lab P2S 0.4 nozzle - saltos rapidos" (el entorno desde el que trabajo no puede
  interactuar con la ventana de Bambu Studio en este Mac — está en otro Space/escritorio
  y no lo pude traer al frente). Al usuario le pedí que lo revise él mismo.

## 2026-09-28 (seguimiento 2) — El usuario confirmó 26h reales y pidió más velocidad
Con el perfil "- saltos rapidos" ya seleccionado y confirmado por el usuario ("esta
perfecto"), el rebanado real dio **26h** (1d 2h) — más que las 20.5h que predije. Probé
que NO era por el planchado (`ironing_type=topmost` real solo agrega 0.11h, nada). No
identifiqué la causa exacta de esas ~5h de diferencia entre mi predicción y lo real (podría
ser una diferencia de versión/arreglo entre mi Bambu Studio de prueba y el suyo, o algo del
plato/arreglo automático) — no se investigó más porque encontré una palanca mejor.

### Nueva palanca: ancho de línea de la pared INTERNA y el relleno sólido interno
Probé subir `outer_wall_speed`/`inner_wall_speed`/`internal_solid_infill_speed` (doblar la
velocidad nominal): casi sin efecto (20.55h→20.28h) — esos tramos ya estaban limitados por
aceleración en segmentos cortos (misma causa que el problema de traslados), no por el techo
de velocidad. Subir la velocidad no ayuda cuando el tramo es demasiado corto para llegar a
esa velocidad.

Lo que sí funcionó: **ensanchar las líneas de la pared interior y del relleno sólido
interno** (invisibles — la pared EXTERIOR, la que se ve, no se tocó):
- `inner_wall_line_width` 0.45→**0.6mm**, `internal_solid_infill_line_width` 0.42→**0.6mm**.
- Por qué funciona: con la pared interior más ancha (2 vueltas × 0.6mm en vez de 0.45mm),
  llega más lejos hacia el centro de la pieza, y el "núcleo" que le queda al relleno sólido
  para cubrir es mucho más chico — por eso "Internal solid infill" bajó de 4.7h a 0.7h.
  Probé anchos mayores (0.7, 0.8mm): empeoraban de nuevo (más "Gap infill" fragmentado, la
  pared ya no encajaba limpio con la onda) — 0.6mm es el punto dulce encontrado.
  También probé ensanchar SOLO el relleno (dejando la pared en 0.45mm): casi no ayuda
  (4.7h→4.4h) — el ahorro grande depende de ensanchar las DOS cosas juntas.
- Verificado con el propio rebanador sobre el archivo real (capa 0.12, retracción 5mm ya
  aplicada): **18.7h** (vs 26h que reportó el usuario, vs 34h original).
- Riesgo: bajo. Es una línea que nunca se ve (va detrás de la pared exterior de 0.42mm, que
  no cambió) — si algo, la pieza queda con la pared interior más gruesa, no más débil. Solo
  hay que confirmarlo con la impresión real, como todo lo demás.
- Aplicado directo en `project_settings.config` (es un ajuste de perfil de impresión, no de
  impresora — sí es editable por proyecto, a diferencia de la retracción).

## Resultado acumulado esperado (por confirmar al Rebanar)
| Cambio | Tiempo |
|---|---|
| Original | 34.0 h |
| + retracción 5mm (impresora) | ~26h real (20.5h predicho — diferencia sin explicar) |
| + pared/relleno interno 0.6mm | **~18.7h predicho** |
