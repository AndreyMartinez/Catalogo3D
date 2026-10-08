# happy_pot_teacher

Archivo: `own design 3d/happy_pot_teacher.3mf`
Origen: comprado — "Happy Pot teacher" (MakerWorld, diseñador "Layer And Leaf",
vía "Image to 3D v2"). Misma familia de macetas-personaje que "Barista Buddy" y
"Smiling Pot", ya registradas.
Backup original en `happy_pot_teacher.3mf.bak`.
Traía 8 copias originales (ids 2,4,6,8,10,12,14,16 — numeración par, no
consecutiva), configurado para Bambu Lab P2S (placa 256×256).

## Feedback recibido
- 2026-09-23 — Ajustar para imprimir rápido en la Bambu Lab A1 mini, que cada
  una pese máximo 25g, agregar la mayor cantidad posible en el plato, y que las
  proporciones queden bien (alto y de lado, sin distorsión).

## Diagnóstico
- Volumen sólido-equivalente (malla sin escalar): 361.64cm³, shell_vol
  implícito ≈102.85cm³ (~28.5% del total) — bastante hueco real, el relleno sí
  importa aquí.
- Al tamaño ORIGINAL (escala 0.409413755, footprint ~69×61mm), con 15% de
  relleno ya pesa solo ~22g — **el techo de 25g no aprieta nada**, no hacía
  falta achicar por peso.
- El límite real para "agregar la mayor cantidad posible" es el espacio de la
  placa 180×180 de la A1 mini, no el peso. Calculé 3 escenarios (mismo tamaño=4
  piezas/22g c/u, -35%=9 piezas/9g c/u, -50%=16 piezas/5g c/u) y se los presenté
  al usuario — **eligió mantener el tamaño original**, prefiriendo que la
  carita/detalles no pierdan nitidez sobre maximizar cantidad.

## Cambios aplicados
- 2026-09-23: `printer_settings_id` → A1 mini, `printable_area` → 180×180,
  `print_settings_id` → "0.20mm Standard @BBL A1M" (inferido, puede pedir elegir
  perfil al abrir).
- 2026-09-23: **sin reescalar** (tamaño original, decisión del usuario) — solo
  se recortó de 8 a **4 copias** (las que cabían con margen seguro en la placa
  más chica: cuadrícula 2×2, pitch 82mm, footprint 69×61mm). Se sincronizó
  `Metadata/model_settings.config` con los 4 ids que quedaron (Tropiezo #5 — ya
  no se repitió el error de la maceta "Smiling Pot").
- 2026-09-23: ajustes de impresión rápida — `layer_height` 0.2→0.28mm (y capa
  inicial igual), `top_shell_layers` 5→4 (menos capas necesarias con capa más
  gruesa), `sparse_infill_density` 15%→8%, `sparse_infill_pattern` gyroid→
  lightning (relleno más rápido de imprimir).

## Resultado real (pendiente de que el usuario abra y Rebane)
- Estimado: ~22g por unidad al tamaño actual (ya estaba ahí antes de tocar nada,
  el relleno más bajo lo baja un poco más, no calculado con precisión porque no
  era el foco — el usuario ya sabía que estaba bien de peso).

## Pendiente / conocido y no resuelto
- No se confirmó el nombre exacto de "0.20mm Standard @BBL A1M" contra los
  perfiles instalados — mismo pendiente que con la maceta Smiling Pot.
- El usuario declinó maximizar cantidad (9 o 16 piezas) a cambio de mantener
  nitidez de detalle — si en el futuro pide "más cantidad" de nuevo, ya está el
  cálculo hecho arriba (35% y 50% de reducción) para no repetirlo.
