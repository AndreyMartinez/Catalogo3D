# Portacubiertos Meandro

Archivo: `own design 3d/Pruebas de productos/Portacubiertos_Meandro.3mf` (+ `.png`), placa de 2.
Origen: **generador propio**, receta `portacubiertos_meandro` (acabado nuevo `meandro`), a
partir de una foto de referencia (2026-10-22): portacubiertos de piedra, tres
compartimentos, cara con lóbulos abultados en forma de bolo.

## Acabado `meandro` (nuevo en `generadores/nucleo/acabados.py`)

Lóbulos tipo almohada que se alternan: uno lleva el bulbo arriba (z≈0.78) y el vecino
abajo (z≈0.22); el surco entre los dos dibuja la «S». Sólo pone material (`hunde`=0).
Parámetros: `meandro_paso` (lóbulo + surco), `meandro_surco`, `meandro_cintura` (bulbo),
`meandro_vaiven`, `meandro_canto` (mm), `meandro_pie` (mm lisos sobre la base). Número de
lóbulos par a la fuerza; el primero se centra en el frente (rectángulo y superelipse).

Camino de diseño (precheck en cada paso):
1. Bandas paralelas con borde en «V» → se leía chevrón.
2. Bandas paralelas con borde en «S» → el usuario: «parecen espirales», no como la foto.
3. Lóbulos alternados (bulbo arriba / bulbo abajo) → «me gusta».
4. + barrilito (perfil `barril` 0.07) y divisores hasta la boca.
5. + planta ovalada (superelipse, redondeo 34) y relieve 3 → 4.2 mm → aprobada.

## Versiones (CLI Bambu Studio 02.08, P2S, Bambu PLA Basic; por pieza)

| v | medida | relieve | laminado | tiempo | peso | costo |
|---|---|---|---|---|---|---|
| **v1** (2/plato) | 205.8 × 100.2 × 112.2 | 4.2 mm macizo, interior liso | 2 vueltas clásico, relleno 12 % | **3 h 53 m** | **212.5 g** | **$51.87** |

Placa: 7 h 46 m / 425.0 g. Costo = 212.5/1000 × 167 + 16.38 (Paquetería).
Ajustes copiados de `Portacubiertos_Oleaje_M.3mf` con `wall_loops` 2, `classic`, hilos
0.42/0.45, `sparse_infill_density` 12 %, `infill_combination` 1. La receta rápida del Oleaje
(1 vuelta Arachne) no sirve aquí: la pared mide de 1.8 a 6 mm entre surco y lóbulo.

## Pendiente
- Imprimir la v1: canto de los lóbulos, panza sin soporte (~11°), cubiertos en los 3 huecos.
- Peso: 2× el Oleaje M. Palancas: `pared_forma` «sigue» (la pared copia el lóbulo, el motor
  estimó −35 %, pero el labio sale ondulado) o relieve 4.2 → 3 mm.
