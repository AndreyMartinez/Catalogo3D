# Portacepillos02RAPIDO (**generador propio**, hermano rápido del 01O)

Archivo: `own design 3d/portacepillos/Portacepillos02RAPIDO.3mf` (+ `.png`)
Se regenera con `python3 generadores/portacepillos_rapido.py --salida <carpeta>`.
Origen: pedido del usuario (2026-10-07) — el 01O tarda ~1 día y es de lo que más
sale; el florero `General_Vases` (líneas parecidas) imprime en ~4 h. Pidió
construir sobre el florero para que sea "demasiado rápido".

## Diagnóstico (por qué el 01O tarda un día y el florero no)
- El vaso del 01O es hueco pero con **pared de 4.7 mm** y la bandeja es una losa de
  7 mm: ~98 g por vaso y ~125 g por bandeja si fueran macizos. Con tanta pared el
  laminador llena el centro con sólido interno y fragmenta todo en trazos cortos.
- El florero tiene pared fina (~1.6 mm), relleno 0%, capa 0.2, `wall_generator`
  arachne: casi todo es pared exterior larga.
- En ambos casos el tiempo lo manda el **número de trazos**, no los gramos: cada
  trazo suelto cuesta una retracción y un salto.

## Qué se construyó
- Vaso del motor (`cuerpo.construir`): planta `circulo` 61.5 mm, alto 95, cónico
  suave, acabado ondulado paso 4.5 / relieve 0.4 (el florero tiene 50 estrías de
  ~4-5 mm de paso), `acabado_desvanece` 6 mm para que la boca no salga mordida.
- **Pared 1.0 mm con `pared_forma=sigue`** (cara interior copia el relieve) y piso
  1.2 mm (= las 6 capas sólidas: 3 piso + 3 techo; con 2.0 el laminador dejaba un
  hueco en medio y lo puenteaba).
- Bandeja doble nueva: plato 144×79×7 con borde de 1.6 mm, piso 1.2 mm y dos aros
  de asiento de 3 mm. ~21 g contra ~125 g de la losa.
- Ajustes de laminado copiados del florero + `resolution` 0.012→0.05.

## Medidas (laminador de Bambu Studio por línea de comandos, plato con 2 juegos)
| Variante | Tiempo | Peso |
|---|---|---|
| 01O actual (lo que reportó el usuario) | ~26 h | ~380 g |
| pared 1.2 lisa por dentro | 9.2 h | 169 g |
| pared 1.0 sigue + pisos 1.2 | 3.8 h | 136 g |
| + resolution 0.05 (**lo que entrega**) | **3.1 h** | **136 g** (68 g por juego) |
Capa 0.28 en vez de 0.2 daría ~2.5 h; no se aplicó (calidad).

## Cosas que costaron
- La clave de planta es `circulo`, no `elipse`: con una clave inválida el motor cae
  en silencio al rectángulo redondeado (salió un vaso cuadrado y redondeado).
- Un .3mf del motor **no declara `Application: BambuStudio`**, y sin eso Bambu
  Studio ignora `Metadata/project_settings.config` y lamina con ajustes genéricos
  (60 mm/s, aceleración 500): salían 22 h para lo mismo. Dos líneas de metadato lo
  arreglan (están en `guardar`).
- `--outputdir` del CLI necesita ruta absoluta y carpeta existente.
- Pared 1.2 con relieve 0.4 y cara lisa: 40 mil trazos sueltos por plato (178 por
  capa) → 9 h. Pared 1.0 + `sigue`: ~3 mil → 3.8 h. Es la palanca grande.
- `z_hop` 0 ahorra otra ~0.7 h pero es ajuste de impresora: no se embebió.

## Pendiente
- Imprimir y ver: que el vaso no se sienta flaco (pierde "peso en mano": ~25 g/vaso
  contra ~100 g) y que el aro de asiento sujete bien.
- Rebanar en la app y confirmar gramaje/tiempo reales (esto es predicción del CLI;
  con el 01O el CLI dijo 18.7 h y el real fue 26 h → esperar quizá ~4 h).
- Cargar el peso real en la tarjeta (el 207 g del 01O está escrito a mano).
- Acomodo: 2 juegos por plato (tres no caben con bandejas de 144×79).

## 2026-10-07 (segunda versión) — el usuario vio el archivo en Bambu y lo cambió
Feedback: pared demasiado delgada, la boca tenía "volado" (la abertura cónica),
quiere todo más recto y pared más gruesa; le encantaron los aros de asiento; vasos
"un tris" más anchos y ondas más marcadas hacia afuera.
- Cambios: perfil `recto` (antes cónico), ancho 61.5→66 (67.5 con relieve), pared
  1.0→**1.7 mm** con `wall_loops`=4 embebido, relieve 0.4→**1.0 mm**, paso 4.5→**9 mm**,
  `acabado_desvanece` 0 (la boca sigue la onda), bandeja 150×79 (aros iguales).
- **Pared gruesa + onda marcada chocan**: la cara interior copia el relieve y, si el
  radio de curvatura de la cresta (paso/2π)²/amplitud es menor que la pared, se
  pliega y el laminador la parte en 300 mil trazos (23-26 h). Por eso se alargó el
  paso: con paso 9 y amplitud 1.0 el radio es 2.05 mm > 1.7. Además la pared debe ser
  múltiplo de los hilos (1.7 = 4 perímetros); 1.6 con 4 perímetros dio 15.8 h.
- Medidas (plato 2 juegos): 1.7 mm/paso 9/amp 1.0 → **5.8 h, 220 g** (≈110 g por
  juego). Alternativa más delgada probada: 1.3 mm, 3 perímetros, amp 0.8, paso 7 →
  5.0 h, 180 g. Capa 0.28 bajaría ~1 h más (no probado en esta versión).

## 2026-10-07 (tercera versión) — "perdió todo, las ondas del original son perfectas"
Feedback: la v2 (23 ondas gruesas, paso 9) perdió el detalle. Pidió ondas muy juntas,
más hondas, vasos más anchos, y que la boca rematara como el original.
- Medido el original (`object_21.model`): 50 estrías, paso 4.15 mm, 0.68 mm pico a
  pico, **cresta plana** (36 % del paso), surco plano 28 %, flancos en S 18 % c/u; en
  los últimos ~3.4 mm los surcos se llenan hasta el nivel de las crestas (aro liso)
  y el labio se redondea.
- Motor: acabado nuevo **`canal`** (ese perfil), parámetro **`acabado_cierre`** (el
  desvanecido lleva el relieve a ras de las crestas en vez de a la pared nominal) y
  **`pared_copia`** (fracción del relieve copiada por dentro con `sigue`). Defaults
  no cambian nada existente; 103 pruebas OK.
- Entregado: Ø70 (71.2 con relieve), recto, `canal` paso 3.0 / amp 0.6 (surco 1.2 mm),
  desvanece 3 + cierre 1, pared 1.45 **lisa** por dentro.
- **Laminado: 1 perímetro (`wall_loops`=1) + Arachne + `filter_out_gap_fill`=2.** Un
  perímetro = 2 hilos (afuera sigue la estría, adentro liso); se pisan en el fondo de
  cada surco y cada cresta queda como cajoncito hueco (corrugado). Verificado
  dibujando la capa 250 del G-code.
- Lo que NO funcionó (plato de 2 juegos): cresta plana con 4 perímetros 22-27 h
  (una isla de perímetro por estría: "wall_loops" son pares de hilos, 4 = 8 hilos =
  3.4 mm en un surco de 1.1); generador clásico 19-23 h, y con 1 perímetro deja los
  dos hilos separados 0.3 mm (dos cáscaras sueltas) — tiene que ser Arachne; filtro de
  huecos solo 14-15 h; 2 perímetros 17.8 h.
- Resultado: **6.0 h, 158 g** por plato (~79 g por juego, CLI). Costo ≈ $26.8/juego.

## 2026-10-07 (cuarta versión) — "es el modelo perfecto", ajustes finos
El usuario aprobó la v3 ("ese es el modelo perfecto", "bajó a 6 h"). Pidió: base que
casi no se vea, vasos un poco menos anchos y más altos, pared un poco más gruesa.
- Base: ya no es plato con borde; placa con silueta de los dos vasos, ceja 0.6 mm
  más allá del aro de asiento, sin borde. 157×80×7 → **144×72×4.2**, 23 → 16 g.
- Vaso: Ø70×95 → **Ø66×105** (67.2 con estría). Misma estría `canal` paso 3 / amp 0.6.
- Pared: 1.45 → **1.6** con `outer_wall_line_width` 0.5 (con 1 perímetro, los dos
  hilos son "Outer wall"; `inner_wall_line_width` no aplica). Valle = 1.0 = 2 × 0.5.
  Probado: 1.45/0.42 → 6.0 h 149 g; 1.6/0.5 → 5.9 h 170 g; 1.75/0.58 → 6.0 h 190 g.
  Engrosar así no cuesta tiempo, solo gramos. Capa 280 dibujada: hilos soldados.
- Resultado: **5.9 h, 170 g** por plato de 2 juegos (~85 g/juego, ≈ $27.9 de costo).
