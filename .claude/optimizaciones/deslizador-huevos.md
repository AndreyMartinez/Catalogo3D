# DeslizadorHuevos (generador propio)

- **Archivo:** `~/Desktop/own design 3d/DeslizadorHuevos.3mf` (+ `_con_huevos.png`)
- **Generador:** `generadores/deslizador_huevos.py` (parámetros dentro del .3mf)
- **Origen:** pedido del usuario el 2026-10-15 con una foto del «Kiki Egg Slide»
  (Chris the Buzz, MakerWorld): algo así que quepa en la **caja de 20 × 16 × 11 cm**
  (20 largo, 16 ancho, 11 alto), que quepan varios huevos y que ruede muy bien.
  Huevo de diseño: hasta extra grande (62 × 47 mm).

## Decisiones de forma

- Con 11 cm de alto no caben dos niveles techados (~125 mm con huevo XL) →
  **nivel de arriba abierto** (repisa de carga) y **dos carriles** usando los 16 cm.
- El huevo rueda de lado: carril 66 mm de ancho, 51 mm de claro abajo.
- Pendiente 4° en los dos niveles (5° no cabía en 11 cm). Caída de 54 mm al
  final de la repisa, igual que el Kiki.
- Boca al frente con tope de 12 mm: el huevo se saca rodándolo hacia uno.
- Se imprime parado sin soportes: techo de abajo = puente entre chaflanes 45°.

## Versiones (CLI Bambu Studio, P2S, 0.20 mm, relleno 10 % grid, 2 perímetros)

Costo = g × 167 $/kg + $16.38 (paquete activo al 10-15).

| v | Qué cambió | Medidas (mm) | Huevos | Tiempo | Peso | Costo |
|---|---|---|---|---|---|---|
| v1 | Primera: paredes 1.8, repisa en cuña, ventanas en forma de huevo | 195 × 137 × 101 | 12 | 5 h 39 | 256 g | $59.1 |
| v2 | Repisa de grosor parejo, fondo 2.4 | 195 × 137 × 101 | 12 | 5 h 38 | 251 g | $58.3 |
| v3 | Pared 1.5, fondo 1.8, piso 1.6, 3 capas de techo | 195 × 137 × 100 | 12 | 5 h 20 | 230 g | $54.8 |
| v4 | **Minimalista**: una sola cinta con esquinas redondas en planta (R12), borde que baja en una curva a la boca, sin ventanas, divisor como riel bajo | 195 × 137 × 100 | 12 | 5 h 10 | 229 g | $54.6 |
| v5 ondas | Pared ondulada entera, ondas a 45°, paso 34, 2 mm, pared 2.2 (descartada) | 196 × 143 × 100 | 12 | 6 h 13 | 251 g | $58.3 |
| **v5 japandi** | **Elegida por el usuario («piel 1»)**: estría de media caña cada ~9 mm, 1.5 mm, pared 1.8, franja lisa de 6 mm arriba; base 192 para que con relieve mida 195; repisa desde x=42 para no perder el 2.º huevo de arriba; esquinas macizas solo hasta la vuelta (sin postes en el carril) | 195 × 140 × 100 | 12 | 6 h 55 | 246 g | $57.5 |
| **v6** | Prueba del usuario: los huevos se atoraban al pasar del 2.º al 1.er nivel y rodaban poco. Causa: los rellenos macizos de las esquinas redondas subían hasta lo alto de la vuelta (~5 cm) y se metían 10 mm en el hueco de la caída junto a cada pared, donde pasan las puntas del huevo (hueco efectivo ~42 mm para un huevo de 47). Arreglo: rellenos solo hasta el piso, hueco 52 → 60, pendiente 4° → 6° (máximo en 11 cm), pared lisa por dentro (estría solo afuera, pared 1.2 + 1.5 de relieve), huevo de diseño 64 × 48, carril 68, claro 54, chaflán 8, borde arriba 22, repisa de largo fijo por `huevos_arriba` | 195 × 143 × 104 | 12 | 7 h 55 | 274 g | $62.2 |

Respaldos: `DeslizadorHuevos.3mf.v3.bak`, `.v4.bak`, `.v5.bak` (y sus `.png`) en la carpeta de
diseños; v1/v2 solo quedaron en el scratchpad de la sesión.

## Aprendizajes

- El usuario rechazó v3 y v4 por «no me gusta / más minimalista premium»; lo que
  lo convenció fue **jugar con la pared** (piel japandi). La forma general de v4
  (cinta + curva a la boca) sí le pareció buen camino.
- La pared ondulada de grosor parejo solo hacia afuera no angosta el carril y casi
  no sube el peso; lo que sube es el tiempo (+1.7 h vs liso) por la pared exterior
  curva.
- El relieve suma ~3 mm al largo: compensar `largo` para la caja.
- Las esquinas redondas en planta piden relleno por dentro (lo de adentro es
  rectangular); ese relleno nunca debe subir más que el piso que tapa, o se
  come espacio del huevo en las esquinas (v5).
- 6° es la pendiente máxima con huevo 64 × 48 en la caja de 11 cm (7° da 108.6).

## Pendiente

- Reimprimir v6 y probar con huevos reales: (1) que pasen la caída de 56 mm sin
  atorarse ni cuartearse; (2) que a 6° rueden solos con la fila llena.
- Si v6 funciona, ver de bajar peso/tiempo (274 g / 7 h 55): la estría maciza
  por fuera suma; probar relieve 1.0 o pared 1.0.
- Validar precio en ML (dispensador / organizador de huevos) antes de producir:
  ~$62 de costo (v6).
