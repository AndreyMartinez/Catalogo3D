# CAT_SOAP — jabonera de gato (comprado, descargado 10-23)

Archivo: `~/Desktop/own design 3d/Pruebas de productos/CAT_SOAP.3mf`
(original de Descargas en `CAT_SOAP.3mf.bak`). Gato estirado con el plato de
jabón en la espalda; según el diseñador el agua escurre por la boca y se
imprime **sin soportes**. Una sola malla de 155 002 triángulos, escala uniforme
×3.918 → **159.6 × 94.5 × 67.0 mm**.

## Diagnóstico (10-23, trimesh)

- La malla no es cerrada: además del cuerpo trae 40 pedacitos sueltos de 1 a
  5 mm, todos a menos de 0.55 mm de la superficie (se funden al laminar). Esos
  pedacitos ensucian la medición de grosor (6 % de muestras < 1 mm), así que no
  se activa `detect_thin_wall`.
- Volumen sólido de 370 cm³ y superficie de 413 cm²; el cuerpo es macizo bajo el
  plato (un solo cruce de rayo de arriba abajo).
- Volado con umbral de 30°: 481 mm². Unos 322 mm² quedan tapados por la propia
  malla: unos 185 mm² bajo la cabeza (z≈27, de 3 a 10 mm de hueco), que es el
  **canal de desagüe hacia la boca**, más 26 mm² bajo el arco de la cola.
  **No se activa el soporte**: taparía el desagüe y el diseñador lo da por
  imprimible sin soporte.

## v1 (10-23) — /transform

| | v0 (descarga) | v1 |
|---|---|---|
| Capa | 0.20 | 0.12 |
| Capas sólidas arriba / abajo | 5 / 3 | 9 / 5 |
| Paredes | classic | arachne |
| Planchado | no | top (el plato es inclinado, plancha poco) |
| Soporte | apagado | apagado (desagüe) |
| Copias por plato | 1 | 2 (con 3 no cabe en ningún ángulo) |
| Tamaño | 159.6×94.5×67 | sin cambio |
| Tiempo / peso / costo | — | **sin laminar**; estimado ≈80 g y ≈$30 con paquetería (*suposición*) |

Pendiente: rebanar en la P2S (el archivo trae perfil P1S/X1C; hay que elegir la
P2S al abrirlo) para tiempo, peso y costo reales; imprimir y revisar que el
desagüe quede limpio y el arco de la cola sin colgajos.
