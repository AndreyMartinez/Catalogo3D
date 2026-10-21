# Checklist de optimización por pieza

Se corre con `transform` / `optimizar-pieza`, una pieza a la vez. Cada pase es
una versión (`.vN.bak` + tabla de tiempo, peso y costo contra la anterior).

## Metas (del usuario, 2026-10-21)
- Paredes perfectas y mejor acabado.
- Menos tiempo y menos costo por pieza.
- Aprovechar la caja de envío: **20 × 16 × 11 cm** (puede ir inclinada).
- Menos gramos **sin que se sienta liviana**:
  - **Decoración** (figuras, floreros): que se sienta con cuerpo al levantarla.
  - **Recipientes** (portacontroles, cubiertos, portacepillos, portalápices):
    peso abajo para que no se volteen con los productos puestos.

## Pasos
1. **Línea base medida**: laminar por CLI el `.3mf` actual. Anotar tiempo, gramos
   y costo por pieza, y qué parte del tiempo es pared, relleno y soporte.
2. **Malla**: cerrada y sin caras invertidas; grosor mínimo de rasgos (orejas,
   colas, bordes) contra 2 perímetros.
3. **Paredes**: `wall_generator` Arachne en curvas y rasgos finos. Recipientes:
   grosor parejo (pared que sigue la forma), sin zonas al límite.
4. **Relleno**: lo que menos se nota y más pesa.
   - Decoración: rayo (lightning). Solo sostiene los techos.
   - Recipientes: el relleno ya es poco; lo que importa es el piso.
5. **Peso donde sirve** (rango de capas en `layer_config_ranges.xml`):
   relleno denso solo en los primeros 2–3 cm. Baja el centro de gravedad,
   da estabilidad y se siente sólido al levantarla, sin cargar gramos arriba.
6. **Acabado**: altura de capa según la superficie (curvas suaves 0.16–0.20,
   facetas 0.20); planchado solo donde hay techos planos visibles.
7. **Soporte** (solo figuras): árbol orgánico, apoyado en el modelo donde haga
   falta, interfaz densa bajo panzas y barbillas.
8. **Tamaño contra caja**: escala uniforme máxima que entra en 20 × 16 × 11 con
   ~2 mm por lado (rotación 3D libre). Nunca estirar un solo eje.
9. **Plato lleno**: máximas copias con la huella real silueta + soporte, 9–10 mm
   al borde.
10. **Precheck** (`generadores/precheck.py`) si cambió forma o tamaño. Visto
    bueno antes del `.3mf`.
11. **Cierre**: laminar, tabla contra la versión anterior, registro en
    `<slug>.md` e `INDICE.md`.

## Orden sugerido (por ventas)
1. Gato Japandi · 2. Cubiertos Más Obsequio · 3. Redondo Ondas (Torsión) ·
4. Curvo Ondas · 5. Portacontroles Arco · 6. pORTAcONTROLES03 · 7. Loop ·
8. Portacepillos · 9. Florero Ondas · 10. Figuras (jirafa, elefante, gorilas) ·
11. Portalápices · 12. El resto.
