# Maceta de gajos trenzada (generador propio)

`generadores/maceta_gajos.py` → `own design 3d/Pruebas de productos/Maceta_Gajos_Trenzada.3mf`

Sale de una foto (11-19): cuenco crema de lóbulos fundidos con pliegues hondos y
estría vertical fina. El usuario la quiso **vertical**, para venta en ML (P2S),
sin hoyo (cubremaceta / florero).

## Cómo se construye

Corona de `lobulos` círculos unidos por redondeos cóncavos (como los tres
lóbulos del portacubiertos ondas, pero en anillo). A cada altura la planta se
escala con el perfil (`base` → 1 en `panza` → `boca`, con `cierre` como
exponente de la curva) y se gira `giro`·t grados; la estría va por fracción del
perímetro y gira con la planta, así sigue al gajo. Pared lisa por dentro a 1.24
(dos hilos de 0.62), piso 1.6, boca recta (`ola` 0) u ondulada.

## Iteraciones (11-19 / 11-20)

| v | Cambio pedido | Clave |
|---|---|---|
| 1 | 6 gajos, panza al 38 %, boca ondulada | «no me gustó tanto»: se leía tulipán |
| 2 | ancho abajo, cierre arriba | panza 0.24, boca 0.72 |
| 3 | 4 hojas, una por lado | `lobulos 4`, base 0.95 |
| 4 | hojas más anchas, boca «lineal» (recta) | pliegue 9, redondeo 2, `ola 0` |
| 5 | más separación y más ancho abajo | pliegue 13, redondeo 1.5, boca 0.62 |
| 6 | más ancho abajo | `cierre` < 1 (bulbo); el 1.er intento dejó escalón tipo candelabro → curva `sin²(π/2·s^cierre)` |
| 7 | medio más ancho | cierre 1.0 (medio 73 → 84 %) |
| 8 | panza y base con más volumen | base 0.98, panza 0.22, cierre 1.25 (medio 92 %) |
| 9 | lo ancho de la panza más abajo | panza 0.10, base 0.96 |
| 10 | gajos trenzados | `giro 90` («me encantó») |
| **11** | tamaño del Florero Minimalista grande (Ø90 × 190) | diámetro 90, alto 190, pliegue 11 |

Rechazado: 6 gajos con panza a media altura (tulipán); diámetro 130 (no cabe en la caja).

## v11 laminada (11-20)

Ajustes copiados del Portacubiertos_Oleaje_M (1 vuelta Arachne, hilos 0.62,
PLA Basic, P2S, capa 0.20, sin soporte). CLI de Bambu Studio, plato de 4 (2×2):

| | Plato de 4 | Por pieza |
|---|---|---|
| Tiempo | 11 h 22 | **2 h 51** |
| Peso | 353.1 g | **88.3 g** |
| Costo (180 $/kg + paquetería $13.96, `.catalogo3d_costos.json` al 11-20) | — | **$29.85** |

Sin «Overhang wall» en el laminado. 89.5 × 89.5 × 190 mm: cabe acostada en la
caja 20×16×11 (5 mm por punta a lo largo, ~10 mm por lado de alto), igual que el
florero minimalista grande. Boca libre ≈ 36 mm: florero más que maceta de tierra.

El 3MF del catálogo no lleva G-code; `slice_info.config` se escribió a mano con
los gramos y el tiempo del CLI (el `--export-3mf` falló por la ruta absoluta:
pasarle solo el nombre del archivo).

    python3 maceta_gajos.py --nombre Maceta_Gajos_Trenzada --copias 4 --diametro 90 \
      --alto 190 --lobulos 4 --pliegue 11 --redondeo 1.5 --ola 0 --base 0.96 \
      --panza 0.10 --boca 0.58 --cierre 1.25 --giro 90

## Pendiente
- Imprimir y revisar la estría en diagonal y la cara colgada del giro (~30°).
- Probar en la caja real con burbuja.
- Sin estudio de mercado propio: comparar con los pares de floreros (+100 en Full, $256–283).
