# Portacubiertos Trenzado

Archivo: `own design 3d/Pruebas de productos/Portacubiertos_Trenzado.3mf` (+ `.png`, `.stl`)
Origen: **generador propio**, `generadores/portacubiertos_trenzado.py`, a partir de una
foto de referencia (10-22): tres vasos color nogal de costillas en espiral, caladas,
dentro de una bandeja beige. Cuatro piezas: 3 vasos + bandeja (dos colores posibles).

    python3 generadores/portacubiertos_trenzado.py --salida "<carpeta>"

Los parámetros completos van dentro del .3mf (`Catalogo3D:parametros`).

## Forma aprobada (v7, 10-22)
- **Vaso de huevo** 80 × 100 mm: radio 31 en el piso, 40 en la panza (46 % del alto),
  29 en la boca. 14 costillas de cordón a 35° (suben a la izquierda vistas de frente),
  sobresalen 5 mm, cáscara de 2.4 mm que sigue la panza; rendijas caladas de 2.2 mm
  (perpendiculares). Zócalo macizo de 6 mm, aro de 3 mm en la boca, piso de 1.6 con
  4 agujeros de drenaje de 4 mm.
- **Bandeja** 252 × 89 × 65 mm: frente y espalda **rectos** por fuera (sin cinturas),
  borde recto que baja en S de 65 mm atrás a 32 mm al frente, pared de 4.5 con labio
  de medio círculo y orilla de abajo suavizada. Por dentro abraza cada vaso a 0.8 mm
  hasta la panza (huevera) y de ahí sube derecha para que el vaso entre. Costillitas de
  1.5 mm en el piso para que el vaso no se quede en el agua.
- Vasos a 0.6 mm entre sí en la panza. Sin soportes (curva más inclinada ~20°).
- Juego: 252 × 89 × 103 mm. Cabe justo en el plato del P2S (256).

## Feedback recibido
- 10-22 — «Puedes generar este diseño de portacubiertos» (foto).
- 10-22 — «la base es de un lado más grande y del otro más chico; los vasos más ovales,
  gorditos y pegados casi rozando» → barril, separación 0.6, bandeja alta atrás.
- 10-22 — pared funcional: dejar las rendijas como están; drenaje sí (sin preferencia
  explícita, se aplicó lo recomendado).
- 10-22 — «el plato atrás más alto, al frente más bajo… armonía; las paredes del vaso
  más anchas y en forma de huevo» → costillas de cordón, labio redondo.
- 10-22 — «más huevo, más anchos que altos, pegado a su vaso, pared más alta» → 80 mm
  (tope del plato P2S), bandeja huevera.
- 10-22 — «no me gustan las curvas en cada cintura del frente» → borde y frente rectos;
  «atrás de la misma forma y más alta» → espalda recta a 65 mm. Aprobada («de maravilla»).

## Pendiente / conocido
- **Peso de la bandeja:** la estimación maciza da ~326 g (las cinturas rellenas de frente
  y espalda son un bloque). Propuesto y no hecho: cinturas huecas por dentro. Laminar
  antes con relleno para ver el peso real.
- **Vaso** ~61 g estimado (suma de sólidos encimados, sobreestima).
- No se ha laminado: falta tiempo/gramos/costo reales con el CLI de Bambu y embebir
  perfil (el script no copia ajustes de laminado todavía).
- Cada costilla es una isla por capa (42 por capa en 3 vasos): vigilar retracciones.
- Rendijas de 2.2 mm: la punta de cuchillos o tenedores podría atorarse; el usuario
  eligió dejarlas así.
