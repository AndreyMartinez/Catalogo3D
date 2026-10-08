# Dispensador_de_huevos_para_10_huevos ("Dispensador_de_" en la tarjeta)

Archivo: `own design 3d/Dispensador_de_huevos_para_10_huevos(2).3mf`
Origen: comprado — "Egg Dispenser for 10 Eggs" (printables.com, @I.Ulianych, CC 4.0).
Backup original en `Dispensador_de_huevos_para_10_huevos(2).3mf.bak`.
Es UN SOLO riel/guía en forma de U (tubo doblado, 274mm de largo) — una de las
piezas del mecanismo espiral del dispensador, no la pieza completa. Impreso acostado
con una rotación 3D (no un simple escalado), con soporte automático activado.

## Feedback recibido
- 2026-09-20 — El acabado en la curva donde toca la base sale con las líneas de
  impresión muy marcadas / calidad baja, igual que le pasó antes al pORTAcONTROLES03.
  Reducir costo y mejorar detalles en general, especialmente en la base.

## Diagnóstico
- **No es un problema de pared delgada** (a diferencia de portacontroles03/4espacios):
  grosor medido cerca de la curva de contacto: mínimo 5.6mm, mediana 15.1mm — es un
  tubo bastante macizo.
- El punto de contacto con la placa es exactamente la curva redonda de arriba del
  gancho (confirmado matemáticamente con el transform: el vértice local
  [-33.5, 19.95, 131.3] cae en mundo Z≈0). Un tubo redondo apoyado en una superficie
  plana solo hace contacto en una línea angosta, no una cara — eso típicamente
  produce una primera capa débil/marcada ahí. Se ve en el render que las puntas de
  las dos patas tienen una patita/talón plano (para atornillar al marco) que sería
  un punto de apoyo mucho más limpio, pero cambiar la orientación no se intentó (alto
  riesgo de que no quepa en altura o genere soporte nuevo en otro lado sin poder
  verificarlo aquí).
- Costo real: $47.37 = material ($31.68 = 181.1g × $175/kg) + paquetería ($15.69,
  paquete "Paquetería" — nota: usa un `.catalogo3d_costos.json` con precios por lote,
  distinto al de portacepillos, pero con los mismos ítems sospechosos "Maceta regalo"
  y "Nuevo tarro tierra" mezclados ahí también).
- Volumen sólido-equivalente: 384.28cm³. Con 181.05g y 10% relleno, shell_vol
  implícito ≈119.5cm³ (~31% del total) — bastante hueco real, el relleno sí importa
  aquí (a diferencia del portacepillos).

## Cambios aplicados
- 2026-09-20: `elephant_foot_compensation` sin definir→0.15mm (para la costura de
  contacto), `sparse_infill_density` 10%→6%, `layer_height` 0.24→0.14mm con
  `top_shell_layers` 4→7 y `bottom_shell_layers` 3→5, `support_threshold_angle`
  20°→35° (menos soporte innecesario). Todo registrado en
  `different_settings_to_system`. No se tocó la malla ni la orientación/transform
  (es una matriz de rotación 3D, no un escalado simple — más riesgoso de tocar a
  ciegas sin Bambu Studio para verificar).

## Resultado real (pendiente de que el usuario Rebane y confirme)
- Estimado: 181.1g → ~168g, $47.37 → ~$45.07 (modesto, ~5%: en esta pieza el
  relleno no es la palanca principal de costo).

## Pendiente / conocido y no resuelto
- La causa raíz del acabado feo (contacto curva-contra-plato) sigue sin resolverse
  de fondo — `elephant_foot_compensation` es un parche de perfil, no cambia que el
  contacto siga siendo una línea. La solución real sería reorientar la pieza para
  apoyarla en las patitas planas de las puntas; se le sugirió al usuario probarlo
  él mismo en Bambu Studio (rotar + vista previa) en vez de intentarlo a ciegas acá.
- Confirmar si "Maceta regalo" / "Nuevo tarro tierra" en la paquetería (mismos ítems
  sospechosos que en portacepillos) aplican a este producto — mismo pendiente sin
  resolver, ahora visto en un segundo archivo.
- Falta que el usuario confirme el gramaje real tras Rebanar y si el acabado mejoró.
