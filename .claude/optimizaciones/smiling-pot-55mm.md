# Smiling_Pot_55mm_SizeAdjustable

Archivo: `own design 3d/Smiling_Pot_55mm_SizeAdjustable.3mf`
Origen: comprado — "BuddyPot Vol. 53" ("The Honest Shelf" collection, MakerWorld),
personalizado a 55mm. Misma familia de diseños que el "Barista Buddy" (maceta de
regalo ya registrada) — mismo tipo de personaje-maceta.
Backup original en `Smiling_Pot_55mm_SizeAdjustable.3mf.bak`.
6 copias originales, todas la misma malla (`object_1.model`), configurado
originalmente para Bambu Lab P2S (placa 256×256).

## Feedback recibido
- 2026-09-22 — Ajustarlo para imprimir en la Bambu Lab A1 mini y ocupar el mayor
  espacio posible de su placa.

## Diagnóstico
- Placa A1 mini: 180×180mm (bastante más chica que la P2S de 256×256 en la que
  estaba configurado el archivo).
- Tamaño por unidad actual: ~64.7×64.7×40.5mm (malla base 100×99.9×62.6mm sin
  escalar × 0.646991055). A ese tamaño, en la A1 mini solo entran 2×2=4 con
  márgenes seguros — MENOS que las 6 originales.
- Para aprovechar bien la placa más chica y no perder cantidad, hacía falta
  achicar un poco: con escala relativa ×0.75 (footprint ~48.5mm por maceta) cabe
  una cuadrícula de **3×3=9** con margen de seguridad de ~12.7mm en cada borde
  (calculado a mano, sin depender del auto-organizar de Bambu).

## Cambios aplicados
- 2026-09-22: `printer_settings_id` → "Bambu Lab A1 mini 0.4 nozzle",
  `print_settings_id` → "0.20mm Standard @BBL A1M" (nombre inferido por el patrón
  de Bambu — si Bambu Studio no lo reconoce exacto, pedirá elegir un perfil de
  proceso compatible al abrir, no rompe nada), `printable_area` → 180×180.
- 2026-09-22: las 6 macetas existentes reescaladas de 0.646991→**0.485243**
  (×0.75) y reposicionadas, más **3 macetas nuevas** agregadas — total **9**, en
  cuadrícula 3×3 (pitch 53mm), verificado sin encimarse. Traslación Z recalculada
  para las 9 (Tropiezo #3), verificado en 0.0000 exacto.

## Resultado real (pendiente de que el usuario abra y Rebane)
- No se estimó peso/costo — el pedido fue solo de espacio/cantidad en la A1 mini,
  no de costo. Si lo pide después, retomar con el modelo de volumen del skill
  (esta familia de diseño ya se caracterizó en el registro de la maceta de
  regalo: ~82% cascarón, poco margen de relleno).

## Ajuste 2 (2026-09-22 — el usuario dijo que quedaron muy pequeñas)
- Pidió subir el gramaje hasta 23g por unidad y que quedaran un poco más altas.
- Medí el volumen real de esta malla (distinto al de la maceta "Barista Buddy" —
  aquí el cascarón es solo ~38.6% del volumen sólido-equivalente, no ~82%; esta
  maceta sí tiene bastante hueco real). Resolví el factor de escala anisotrópico
  (X/Y iguales, Z un 12% más alto en proporción) que da exactamente 23g con 15%
  de relleno: **63.6×63.5×44.6mm** por unidad (el tamaño original era
  64.7×64.7×40.5mm — o sea, queda casi del mismo ancho que el original, pero
  ~10% más alta).
- **Consecuencia de tamaño**: a esa medida ya NO caben 9 en la placa de la A1
  mini — el ancho vuelve a superar el tercio de placa que necesitaba la
  cuadrícula 3×3. Se recortó a una cuadrícula **2×2 = 4 macetas**, con 80mm de
  separación entre centros (mucho margen, footprint ~63.6mm). Se eliminaron los
  5 objetos/posiciones que sobraban del intento anterior (limpieza).
- Traslación Z recalculada para las 4 con la nueva escala Z (Tropiezo #3),
  verificado en 0.0000.

## Bug encontrado y corregido (2026-09-22 — "falló al abrirlos")
El usuario reportó que Bambu Studio fallaba al abrir el archivo tras el ajuste 2.
Causa: nunca actualicé `Metadata/model_settings.config` en ninguno de los dos
cambios de cantidad (6→9→4) — ese archivo seguía listando `<object id>`,
`<model_instance>` y `<assemble_item>` para ids que ya no existían en
`3D/3dmodel.model` (le faltaba el 8/9/10 del primer cambio, y le sobraba el 6/7
tras el segundo). Bambu Studio cruza ambos archivos y falla si no coinciden
exactamente. Corregido recortando esos tres bloques en `model_settings.config`
(y de paso `cut_information.xml`) para que coincidan uno a uno con los objetos
reales (2,3,4,5). Verificado comparando los sets de ids entre archivos.
Quedó como **Tropiezo #5** en el SKILL.md — aplica a cualquier pieza futura donde
se cambie la cantidad de copias en el plato.

## Pendiente / conocido y no resuelto
- Verificar que `print_settings_id="0.20mm Standard @BBL A1M"` sea el nombre
  exacto que Bambu Studio tiene instalado — si no, al abrir pedirá elegir un
  perfil de impresión para la A1 mini, cosa menor de un clic.
- No se confirmó si 9 es realmente el máximo posible — un cálculo más fino (o el
  "Organizar" de Bambu Studio con estas 9 ya puestas) podría ajustar un poco más
  el pitch y ver si cabe alguna extra, pero 9 ya es una mejora clara sobre las 6
  originales pese al cambio de placa más chica.
