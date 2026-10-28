# Portacubiertos Ondas

Archivo: `own design 3d/Pruebas de productos/Portacubiertos_Ondas.3mf` (laminado, + `.png`, `.stl`)
Origen: **generador propio**, `generadores/portacubiertos_ondas.py`, a partir de una foto
de referencia (10-22): pieza negra de tres cilindros fundidos, perfil en ondas (panzas
apiladas) y estría vertical fina en toda la cara, boca a una sola altura.

    python3 generadores/portacubiertos_ondas.py            # 3MF de 2 por plato en Pruebas
    python3 generadores/portacubiertos_ondas.py --solo-stl --salida <carpeta>   # para precheck

Los parámetros completos van dentro del .3mf (`Catalogo3D:parametros`).

## Forma aprobada (v3, 10-23: «así me gusta»)
- Planta: contorno de tres lóbulos del trenzado (`tres_lobulos`), cintura cóncava r 6.
- **200 × 88 × 102 mm**. Radio del lóbulo (al valle) 43.3 en las panzas, 38.8 en los
  cuellos; 3 panzas, base y boca en cuello (coseno). Voladizo máx. ~22°, sin soportes.
- Estría «canal» (cresta plana) paso 3 mm, relieve 0.7, 162 estrías; cada arco del
  contorno se remuestrea por separado para que la estría suba recta (con remuestreo
  por perímetro total se torcía: v1 interna).
- Pared 1.24 en el valle (2 hilos de 0.62) + relieve = 1.94: regla de
  [[tiempo-lo-manda-el-numero-de-trazos]]. Piso 1.2. Divisores 2 mm en las cinturas,
  3 mm bajo la boca. 3 compartimentos.

## Versiones (precheck; solo la v3 se laminó)
| v | medida | qué cambió | resultado |
|---|---|---|---|
| v1 | 195.5 × 78 × 102 | medida del Torsión | «me encantó», pidió más ancho |
| v2 | 210 × 78 × 102 | largo +14.5 | pidió menos largo y más ancho |
| **v3** | **200 × 88 × 102** | largo −10, fondo +10 | aprobada |

## Laminado v3 (CLI Bambu Studio 02.08, P2S, Bambu PLA Basic, ajustes copiados de Oleaje M)
Receta rápida: 1 vuelta Arachne, hilos 0.62, relleno 0 %, resolución 0.05.
Plato de **2**: 6 h 09 m · 235.0 g. **Por pieza: 3 h 05 m · 117.5 g · $36.00**
(167 $/kg + Paquetería $16.38). 3 por plato no caben (3 × 88 + huecos > 256).

## Pendiente
- Imprimir: confirmar que el valle sale macizo (hilos que se tocan) y que los cuellos
  de la base no se despegan.
