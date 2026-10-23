# GatoEstriado (generador propio + cabeza del Gato Japandi)

Archivo: `own design 3d/Pruebas de productos/GatoEstriado.3mf` (v11 en `.v11.bak` al lado)
Generador: `generadores/gato_estriado.py` (cuerpo de `jirafa_estriada.py`; la
cabeza se recorta en cada corrida de `own design 3d/gato_japandi.3mf`, modelo
comprado «Katze Japandi» de ChrisB — la malla no entra al repo). Revisar que
la licencia del Japandi permita vender derivados.

## Historia (2026-10-22)
| v | Qué | Resultado |
|---|---|---|
| v1 | Cabeza de gato hecha a mano (bolitas de cachete, nariz, conos de oreja) sobre el cuerpo de la jirafa | **Rechazada**: «se ve terrible». Cara con primitivas = juguete barato |
| v2 | Cabeza del Japandi recortada por la cintura del cuello (z 17 crudo), tapada con abanico, sobre el cuello de jirafa | Coherente (la cabeza del Japandi no tiene cara: bola estriada + orejas) pero cabeza chica, se lee botella |
| v3 | Cuello corto (perfil hasta 104), cabeza ×1.08 | Elegida: gato sentado |
| v4–v5 | Bola de la cabeza inflada de 41×42×34 a casi esfera (orejas solo se mueven con su base); cabeza 6 mm más abajo | «Más redonda» pedido por el usuario |
| v6 | Pecho liso (estrías se apagan al frente) + cara lisa (surcos rellenos hasta la envolvente de crestas, en esféricas) | «Me encantaaa» |
| v7 | Todo ×1.33 a 195 mm | Para la caja 20×16×11 acostado |
| v8 | 200 mm; foto del gato negro: cuerpo todo estriado, cabeza lisa salvo nuca | 224.1 g · 10 h 58 · soporte 2 h 14 · $53.80 — caro |
| v9 | 18 estrías anchas (forma 0.6), cuello en copa hasta la barbilla, relleno lightning 10 %, soporte 30° | 60.9 g · 5 h 16 · sin soporte · $26.54 |
| v10 | Relieve de cara (nariz, cuencas de ojos, hocico) y estrías que se cierran en punta en la panza | 67.4 g · 5 h 07 · $27.64 — **rechazada**: «la forma del rostro queda horrible» |
| v11 | Vuelta a la forma v7 (26 estrías, pecho y cara lisos, cuello sin copa) a 200 mm, con lightning 10 % | 70.0 g · 5 h 31 · $28.06 (en `.v11.bak`) |
| **v12** | **Babero liso al frente** de la mitad de la panza (z crudo 43→57 los surcos del frente se cierran en punta) hasta abajo del cuello (88→97 se reabren); por surco entero (±52° del frente); costados, espalda y cuello bajo la cabeza estriados | **72.5 g · 5 h 25 · soporte 18 min · $28.49** (30°) |

## v11 — laminado (CLI Bambu Studio, ajustes de reduced_color + LAMINADO)
85 × 85 × 200 mm, capa 0.12, PLA Basic, lightning 10 %, soporte árbol.
| Ángulo de soporte | Peso | Tiempo | Soporte | Costo (167 $/kg + $16.38) |
|---|---|---|---|---|
| **30° (en el .3mf)** | **70.0 g** | **5 h 31** | 18 min | **$28.06** |
| 40° | 82.2 g | 6 h 04 | 51 min | $30.10 |
| 50° (el de la jirafa) | 114.1 g | 7 h 43 | 2 h 16 | $35.44 |

Lo que más abarató: relleno lightning (grid 15 % → lightning 10 %: 224 → 110 g
en v9) y el ángulo de soporte (el soporte de árbol subía del plato hasta orejas
y barbilla: ~50 g).

## Aprendido
- Una cara de animal con primitivas o relieve escrito a mano no gusta (v1, v10).
  Lo que funcionó fue reusar la cabeza de un modelo comprado y solo
  redondearla/alisarla.
- Alisar estrías de una malla escaneada: empujar cada vértice a la envolvente de
  crestas en coordenadas esféricas desde el centro de la bola. En cilíndricas
  quedan escalones o una tapa en la coronilla.
- Surco que se cierra en punta: angostar el surco (min(c, k)/k), no solo bajarle
  hondura; pide ~40 columnas por estría o salen dientes.

## Publicación
- 2026-10-23: **MLM3699686229** «Gato Estriado Decorativo Minimalista Más Regalos Sorpresa Negro», $219, 6 u, despacho propio (xd_drop_off), paquete 20×16×11 / 198 g, 5 fotos. El mismo día: Flex activado, y premium + envío gratis junto con las demás publicaciones nuevas; anuncio en la campaña de lanzamiento (ROAS 5, $50/día).

## Pendiente
- **Licencia del Katze Japandi (ChrisB)**: confirmar que permite vender derivados; la publicación ya está activa.
- Imprimir el prototipo a 30°: revisar la barbilla (sin copa cuelga) y las
  orejas. Si la barbilla sale fea, 40° (+$2).
- Medir la caja por dentro: 200 mm es justo.
- Sin estudio de mercado todavía.
