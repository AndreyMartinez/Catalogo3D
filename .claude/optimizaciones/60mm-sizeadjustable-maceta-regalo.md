# 60mm_SizeAdjustable — maceta de regalo ("Barista Buddy")

Archivo: `own design 3d/60mm_SizeAdjustable.3mf`
Origen: comprado/MakerWorld — "Barista Buddy" Vol. 63 ("The Honest Shelf"),
personalizado a 60mm vía la herramienta "Parametric Model Maker" de MakerWorld.
Backup original en `60mm_SizeAdjustable.3mf.bak`.
No se vende sola — es la maceta/regalo que se incluye como obsequio en otros
productos (ver también el pendiente de paquetería en portacepillos y en el
dispensador de huevos, que referencian "Maceta regalo"/"Nuevo tarro tierra").
9 copias originales en el plato, todas la misma malla (`object_1.model`, un
personaje-maceta detallado, 441k caras) a escala uniforme 0.701688175.

## Feedback recibido
- 2026-09-19/20 — Optimizarla lo más posible para que el costo por unidad sea $3
  (filamento a $175/kg), y que salgan la mayor cantidad posible en una sola
  impresión. Primero pidió no achicarla (mejor un poco más grande) y compensar con
  mini respiraderas/agujeros de drenaje en la base; al ver que el margen real de
  ahorro sin achicar tiene un piso de ~$3.34 (con 0% relleno), aceptó achicarla un
  poco.

## Diagnóstico
- Nunca se había rebanado ("sin laminar"), así que no hay peso real de referencia —
  todo lo de acá es estimado con el modelo de volumen, sin calibrar contra una
  rebanada real (más flojo que en las otras piezas).
- Volumen sólido-equivalente a escala actual: 18.79cm³. Grosor real medido por
  ray-casting: mediana ~3.4mm (a escala del mesh sin imprimir) ≈ 2.4mm a escala de
  impresión — pero esto está sesgado por partes pequeñas muy detalladas (la tacita
  de café, el asa); el estimado de volumen por erosión (empujar la malla hacia
  adentro por el grosor de 2 perímetros) da un cálculo más confiable:
  shell_vol ≈ 15.41cm³ = **~82% del volumen es cascarón**, no un cascarón delgado
  con mucho hueco. Con eso, incluso a 0% de relleno el costo no baja de ~$3.34 al
  tamaño actual — el relleno solo mueve el número entre $3.34 y $3.45.
- Los "mini respiraderas" de drenaje (3-5mm de diámetro) quitan un volumen
  insignificante (~0.19cm³ ≈ $0.03) — buena idea funcional para una maceta real,
  pero no ayuda al costo.
- Para llegar a $3.00 exacto sin tocar el cascarón, hace falta achicar ~5.6% lineal
  (factor relativo 0.9443): de ~58×68×41mm a ~54.7×63.8×38.7mm.

## Cambios aplicados
- 2026-09-20: escala uniforme de las 9 copias existentes de 0.701688175 →
  0.6626173910961044 (factor relativo 0.9443, resuelto para llegar exacto a
  17.14g/$3.00 con 4% de relleno). **Traslación Z recalculada** para las 12 copias
  (lección del Tropiezo #3) para que la base quede exacto en mundo Z=0.
- 2026-09-20: agregadas 3 copias más (objetos nuevos 11,12,13) para un total de
  **12 copias** en el plato — cuadrícula 4×3 verificada a mano (pitch 58.05×67.02mm,
  sin encimarse, dentro de la placa 256×256mm de la P2S). El usuario prefirió esta
  opción seg ura sobre agregar más y usar "Organizar" de Bambu Studio.
- 2026-09-20: `sparse_infill_density` 15%→4%, registrado en
  `different_settings_to_system`.

## Resultado real (pendiente de que el usuario Rebane y confirme)
- Estimado: 493.7g→17.14g×12? NO — es por unidad: ~17.1g por maceta ≈ $3.00 c/u.
  (Nunca se había rebanado antes, así que este estimado es el menos confiable de
  todos los registrados hasta ahora — pendiente de calibrar con un Rebanar real.)

## Pendiente / conocido y no resuelto
- **Los agujeros de drenaje (mini respiraderas) nunca se llegaron a cortar en la
  malla** — se instaló `manifold3d` para hacerlo (boolean de cilindros pequeños en
  el piso de la taza) pero la conversación se desvió a otras piezas antes de
  ejecutarlo. Si el usuario lo vuelve a pedir, retomar desde ahí (manifold3d ya
  instalado, mesh de 441k caras — decimar para pruebas rápidas, cortar sobre la
  malla completa para el resultado final).
- Sin peso real de referencia todavía — el estimado de $3.00 exacto puede no
  cumplirse al rebanar de verdad; avisar al usuario que ajuste fino puede hacer
  falta.
