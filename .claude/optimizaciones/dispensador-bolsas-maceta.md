# Dispensador de bolsas con maceta

Archivo: `own design 3d/Pruebas de productos/Dispensador_Bolsas_Maceta.3mf` (+ `.png`)
Origen: **generador propio**, `generadores/dispensador_bolsas.py`, a partir de una foto
(10-23) de un portacontroles con pared de «tejido» y del mecanismo del
«Dog poop bags roll dispenser planter» (Prints Charming, en `~/Downloads`), del que se
midieron el tubo (64 × 35 por dentro, rollos de ~33 × 60) y la salida.

    python3 generadores/dispensador_bolsas.py --salida "<carpeta>" --3mf

Cuatro piezas, ninguna con soporte: cuerpo, tapa, maceta (charola colgada) y repisa.

## Forma aprobada (v8, 10-23)
- Cuerpo 86 × 85 × 104 (125 de fondo con la charola de salida; 106 con tapa): cabe en
  la caja 20 × 16 × 11. Esquinas de r10 para que la ventana (66 × 44, a ras del piso)
  caiga en el tramo recto del frente.
- Textura: estría vertical cada ~3 mm (0.8) y tres bandas onduladas donde la estría se
  vuelve cuadrícula de bolitas; lisa (solo estría) abajo 7 mm y arriba 9 mm.
- Por dentro, **zigzag de dispensador de latas**: se carga por arriba adelante (tapa
  de tapón), el rollo cae a una **repisa** que baja 8° hacia atrás, cae al fondo y el
  **piso** baja 8° hacia la ventana; charola con labio cóncavo de 18 mm al frente.
  Pasillo libre de 38 mm bajo la repisa; 2.2 mm de holgura con la maceta al bajar.
- Maceta: charola aparte de 20 mm de tierra, colgada de una ceja en la orilla
  (costados y atrás; vuela 2 mm), su frente es la pared del tubo; sin drenaje para que
  el agua no caiga a las bolsas. Se levanta para meter la repisa.
- Repisa: pieza plana de 2 mm (impresa en el cuerpo volaría), sobre dos rieles a 45°
  de 4 mm en los costados (solo en el tramo recto). PLA sobre PLA a 8° no debe resbalar.
- Capacidad (rollos 33 × 60): ~5 (charola 1, piso 2, repisa 1, uno sobre el de atrás).

## Feedback recibido (10-23)
- v1: dos compartimentos lado a lado, ranura vertical → «¿pero dónde se dispensa?»
  + ejemplo comprado → v2 tubo al centro con ventana y charola.
- v3 tubo a un lado y maceta a la derecha → v4 «solo deja hasta aquí para que quepa en
  la caja» (100 × 137).
- v5 «mitad dispensador mitad maceta, tapa y una bajada» → v6 «pared abajo en la maceta
  para que no quede tan llena de tierra» (falso piso de dos aguas a 45°).
- v7 maceta solo arriba atrás, espacio de abajo para rollos (charola colgada) → v8
  «que haga ese recorrido para que rueden de forma automática» (zigzag). Aprobada.

## Laminado (CLI Bambu Studio 02.07, P2S, Bambu PLA Basic, plato con las 4 piezas)

| Perfil | Pared | Tiempo | Peso | Costo* |
|---|---|---|---|---|
| florero + 15 % relleno, 2 vueltas Arachne (4 hilos 0.42) | 1.6 | 12 h 20 m | 134.2 g | $38.79 |
| **1 vuelta Arachne, hilos 0.65, filtro de huecos 2, retracción mín. 5** | **1.3** | **3 h 18 m** | **113.7 g** | **$35.36** |

\* `.catalogo3d_costos.json` al 10-23: 167 $/kg + Paquetería $16.38.
Con 2 vueltas la textura partía la pared en trazos sueltos: 4.6 h de recorridos y
4.7 h de pared interior. Misma lección que el portacepillos rápido.

## Pendiente
- Imprimir y probar con rollos reales: que ruede en las dos bajadas (si se atora,
  subir `--caida`), que la repisa no resbale, el puente de 66 mm de la ventana y la
  ceja de la maceta.
- Medir un rollo real; el tubo está hecho para ~33 × 60.
