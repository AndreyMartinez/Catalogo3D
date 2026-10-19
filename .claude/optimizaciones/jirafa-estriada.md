# JirafaEstriada — figura de bolo estriada (generador propio)

Archivo: `own design 3d/JirafaEstriada.3mf`
Generador: `generadores/jirafa_estriada.py` (solo biblioteca estándar; usa
`nucleo/` del motor). Regenerar: `python3 generadores/jirafa_estriada.py
--salida <carpeta> --3mf [--render]`.

## Origen
2026-10-18 — el usuario mandó la foto de tres renos estriados (verde salvia,
beige, rojo: bolo con estrías verticales y astas) y pidió mezclar ese estilo
con la jirafa (`jirafa-reduced-color.md`): «forma de cuello para arriba».

## Cómo está hecha
Un solo tubo estriado barrido sobre una columna: sube recto y arriba se dobla
hacia el frente para volverse cabeza y trompa, así las estrías corren sin
corte del pie a la nariz. Osiconos (tallo + bola) y orejas (elipsoides
aplanados) son mallas aparte metidas en la cabeza; el laminador las une.

## Iteraciones (todas con render, en el color de la foto)
| v | Cambio | Por qué |
|---|---|---|
| 1 | Bolo de revolución + cabeza ovalada, 32 estrías 1.3 mm | primer intento |
| 1b | 26 estrías de 2.0 mm, orejas y osiconos más grandes | el reno tiene menos estrías y más hondas |
| 2 | Hocico aparte → **rechazado**: se leía como concha. Se cambió a cuello doblado en cabeza (una pieza) | «que se vea más la trompa» |
| 2b | Nariz lisa (estrías se apagan 10 mm antes), curva radio 19 | las estrías juntas en la punta hacían una flor; la curva de 15 se pellizcaba |
| 3 | Cabeza en cuña: el radio se afina y el centro sube (`cuna` 0.85) | foto de jirafa de perfil: frente recta, quijada que sube |
| 4 / 4b | Cuerpo triangular recto / cóncavo | «el cuello es más triangular» |
| 5 | Cuello delgado → curva cóncava → hombros redondos → costados casi rectos | dibujo de jirafa de frente: «no tan triángulo». Con hombro corto parecía botella de vino; se alargó la caída |
| **6** | Sección de cabeza en triángulo invertido (`cara_triangulo` 0.5, `ancho` 1.14) + cabeza baja 135° (antes 112°) | «la trompa es como un triángulo viniendo hacia el frente». De frente la trompa se ve de punta y se lee redonda; bajando la cabeza se ve la frente ancha que se cierra en la trompa. Con 155° parecía bastón |
| **7** | Estría de 4.0 mm (antes 2.0), surco abierto (`estria_forma` 1.0, antes 0.55) y profundidad completa desde radio 9 (antes 13) | «que se vea más hueco el espacio entre cada línea». 3.2 mm casi no se distinguía en el render (no dibuja sombra en el surco) |

| 8 | **Descartada, se volvió a v7**: trompa 9 mm, ojos (media bola a cada lado), cabeza lisa (toda o solo la frente) | de frente la trompa larga y las estrías abiertas desde el cráneo «parecen el revés de un paraguas». La cabeza lisa gustó, pero los ojos «se ven horribles» y el usuario pidió volver todo a v7 y ajustar desde ahí. El código se quitó; la v7 regenera idéntica |
| 9 | Cabeza «recta» (`cabeza_forma`): el cuello sube recto y cierra en media esfera en la nuca; la cabeza es una cuña estriada recta aparte (30° abajo, 46 mm, r 15 → 7.5, 1.25 más alta que ancha, frente recta) con nariz chata (superelipse). Se cruzan y la garganta queda en esquina | foto de jirafa de perfil: «que la curva del hocico no sea una U». La primera cuña (36 mm, 40°) se veía como tubo corto; se alargó, se hizo más alta y se acentuó la cuña |
| **10** | Frente de la cabeza lisa (`frente_lisa`: seno 0.15 → 0.6 del ángulo de la sección), costados y quijada estriados | el usuario marcó en rojo la frente vista de frente: «volvamos lisa esta parte, el resto me encantó» |

| **11** | Forma del florero-jirafa café de la foto: panza de jarrón abajo (r 31 a z 36, pie r 23) que cierra cóncava a un cuello largo r 12; cabeza de huevo **toda lisa** (`cabeza_lisa`), nuca redonda completa (`cabeza_nuca` 1.0), cráneo ancho que cierra a trompa redonda (`cabeza_afina` 1.4, `nariz_exp` 2, nariz r 11), más agachada (52°); osiconos largos y delgados | foto de una jirafa estriada tipo jarrón: «dale más esta forma» |

**Elegida: v11** (10-18, «me gusta, saca el .3mf»). Respaldos: `.v6.bak`, `.v7.bak`, `.v10.bak`.
Los valores de la v10 quedan en comentarios junto a cada parámetro de `JIRAFA`.
El `.v10.bak` (guardado desde Bambu Studio, con gcode adentro) no lo lee el
CLI («can not be parsed»); para la tabla se regeneró la v10 con esos valores.

**Antes: v10** (10-18, «me gustó, sácala»).
`cabeza_forma: "curva"` regenera la v7 idéntica (malla verificada).

**Base de trabajo antes de la v9: v7** (10-18, después de descartar la v8). Antes se había
elegido la **v6** («me quedo con este», render salvia 3/4);
v7 es la misma con la estría más honda. Respaldo: `JirafaEstriada.3mf.v6.bak`.

## Resultado v6 (CLI Bambu Studio, ajustes copiados de `reduced_color.3mf`)
P2S, capa 0.12, 2 perímetros clásicos, relleno 15 %, soporte árbol (auto,
45°, también sobre el modelo), PLA Basic.

| Medida | Valor |
|---|---|
| Tamaño | 64 × 85 × 163 mm (cabe acostada en la caja 20×16×11) |
| Peso | **89.4 g** |
| Tiempo | **5 h 28 min** (soporte ≈ 40 min) |
| Costo (167 $/kg + $16.38) | **$31.31** |

Comparación: la jirafa low-poly v5 sale 68.0 g · 4.37 h · $27.74.

### v7 contra v6 (mismos ajustes de laminado)
| | v6 (estría 2.0) | v7 (estría 4.0) | Δ |
|---|---|---|---|
| Peso | 89.4 g | 106.1 g | +16.7 g |
| Tiempo | 5 h 28 | 6 h 49 | +1 h 21 |
| Soporte | ≈ 40 min | ≈ 55 min | +15 min |
| Costo | $31.31 | $34.10 | +$2.79 |

Sube porque la pared exterior sigue cada surco: más recorrido de perímetro
(92 min) y más recorridos en vacío (67 min). El soporte crece bajo la cabeza,
donde las crestas hondas cuelgan. De frente, las crestas de la frente se abren
como abanico arriba de la cabeza: revisar en el prototipo si gusta.

### v10 contra v7 (mismos ajustes de laminado)
| | v7 | v10 | Δ |
|---|---|---|---|
| Tamaño | 64 × 85 × 163 mm | 65 × 73 × 169 mm | cabeza más corta hacia el frente, más alta |
| Peso | 106.1 g | **119.1 g** | +13.0 g |
| Tiempo | 6 h 49 | **6 h 55** | +6 min |
| Soporte | ≈ 55 min | ≈ 86 min | +31 min |
| Costo | $34.10 | **$36.27** | +$2.17 |

El soporte crece porque la cuña sale recta en el aire hasta la nariz chata
(el arco de la v7 se sostenía más a sí mismo); casi todo el peso extra es
soporte. Cuello y cabeza son dos cuerpos que se cruzan dentro de un mismo
objeto: el laminado salió «Success» sin avisos, pero conviene mirar en Bambu
Studio que no queden paredes internas donde se cruzan.

### v11 contra v10 (mismos ajustes de laminado, CLI 10-18)
| | v10 | v11 | Δ |
|---|---|---|---|
| Tamaño | 65 × 73 × 169 mm | 69 × 64 × 176 mm | más ancha de panza, cabeza más corta al frente |
| Peso | 119.2 g | **106.8 g** | −12.4 g |
| Tiempo (modelo) | 6 h 54 | **5 h 25** | −1 h 29 |
| Soporte | ≈ 85 min | ≈ 39 min | −46 min |
| Costo (167 $/kg + $16.38) | $36.29 | **$34.21** | −$2.08 |

Baja casi todo por el soporte: la cabeza agachada y redonda se sostiene sola
mucho más que la cuña recta de la v10, y sin estrías en la cabeza no hay
crestas colgando. El cuerpo es más grande (201 cm³ contra 167) pero con
relleno 15 % pesa poco. Sigue cabiendo acostada en la caja 20×16×11.

## Pendiente
- Imprimir el prototipo y revisar: soporte bajo la trompa y las orejas, y si
  las estrías de 2 mm en la curva de la cabeza salen limpias con 2 perímetros
  (ver la memoria del tiempo por número de trazos: 1 perímetro + Arachne si
  el tiempo se dispara).
- Sin estudio de mercado todavía: comparar contra lo que se vende antes de
  producir en serie.
