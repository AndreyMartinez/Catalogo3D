# PortalapicesHuevoOndas

Archivo: `own design 3d/Huevo/PortalapicesHuevoOndas.3mf`
Origen: generador propio (`generadores/huevo_lowpoly.py --superficie ondas`; hoy
vive en el worktree `catalog-egg-shape-design-b7f611`, sin versionar). Los
parámetros van dentro del .3mf (`Catalogo3D:parametros`).

## Feedback recibido
- 2026-10-08 — «poner la pared más gruesa y hacer de tamaño un poco más grande y
  aumentar la pared el grosor para que se sienta un poco pesado».

## Diagnóstico
- La v1 salía del generador sin perfil de laminado (tarjeta «sin laminar»).
  Laminada con P2S 0.20mm Standard (2 perímetros, relleno 15 %): 73.9 g, 2 h 11.
- **Engrosar la malla sola no pesa**: con pared de 3.0 mm y perfil estándar la
  pieza grande da 80 g. El grosor extra se llena con relleno al 15 %. Para que se
  sienta pesada, la pared tiene que imprimirse maciza; eso es perfil, no malla.
- Maciza más rápida: 3 perímetros + relleno 100 % zig-zag (3 h 32) gana a 7
  perímetros (4 h 27) y a perímetros anchos de 0.62 (3 h 43) con el mismo peso.
- Costo = g × 0.175 + 14.04 (paquete «Paquetería», `.catalogo3d_costos.json`).
- Mercado: portalápices = 45 u en 90 días (9 %), 0 en octubre parcial
  (*medido*, estudio-de-mercado). El huevo aún no está publicado.

## 2026-10-08 (v2) — «que se sienta un poco pesado»
Cambios v1 → v2:
- Tamaño ×1.10: ancho 84 → 92.4, alto 94 → 103.4 (exterior 86.6×86.6×94 →
  95.0×95.0×103.4 mm). Boca por dentro 52.9 → 56.5 mm.
- Pared (valle) 2.0 → 3.0 mm; piso 3.0 → 4.5 mm. Ondas, relieve, torsión y pie
  sin tocar (20 / 1.3 / −0.3 / 0.64). Voladizo sigue en 44°.
- Perfil P2S 0.20mm Standard embebido + `wall_loops` 3, `sparse_infill_density`
  100 %, `sparse_infill_pattern` zig-zag, `bottom_shell_layers` 5 (todas en
  `different_settings_to_system`). Archivo entregado = exportación laminada del
  CLI (trae peso y tiempo para la tarjeta) con nuestra miniatura azul.
- Respaldo: `PortalapicesHuevoOndas.3mf.v1.bak` (y `.bak` = original).

Tabla (CLI de Bambu Studio, 1 pieza; tiempos del CLI, no medidos):

| Variante | Tamaño | Pared / piso | Perfil | Tiempo | Peso | Costo |
|---|---|---|---|---|---|---|
| v1 | 87×87×94 | 2.0 / 3.0 | estándar | 2 h 11 | 73.9 g | $26.97 |
| v1 maciza | 87×87×94 | 2.0 / 3.0 | 3 per + 100 % | 3 h 17 | 78.7 g | $27.80 |
| ×1.10 | 95×95×103 | 3.0 / 4.5 | estándar | 2 h 12 | 80.3 g | $28.09 |
| **v2** ×1.10 maciza | 95×95×103 | 3.0 / 4.5 | 3 per + 100 % | **3 h 32** | **133.7 g** | **$37.43** |
| ×1.10 maciza | 95×95×103 | 3.0 / 4.5 | 7 per + piso 23 capas | 4 h 27 | 133.3 g | $37.36 |
| ×1.10 pared 3.5 | 95×95×103 | 3.5 / 5.0 | 3 per + 100 % | 4 h 15 | 152.1 g | $40.65 |
| ×1.15 pared 3.5 | 99×99×108 | 3.5 / 5.0 | 3 per + 100 % | 4 h 36 | 166.5 g | $43.17 |

Regenerar la v2:
```
python3 generadores/huevo_lowpoly.py --nombre PortalapicesHuevoOndas \
  --superficie ondas --ondas 20 --relieve 1.3 --torsion -0.3 --pie 0.64 \
  --ancho 92.4 --alto 103.4 --pared 3.0 --piso 4.5
```
y después inyectar el perfil (el generador no lo hace; sin él sale liviana).

## 2026-10-08 (v3) — «16 cm de alto y proporcional»; «5 horas es bastante… el estándar, pero si se puede optimizar»
Cambios v2 → v3:
- Escala ×1.70 sobre la v1 (×1.55 sobre la v2): ancho 92.4 → 143.0, alto 103.4 →
  160.0 → exterior **147×147×160 mm**, boca por dentro 56.5 → 90.9 mm. Relieve
  1.3 → 2.0 y filete 6 → 9.3 escalados; pared 3.0 y piso 4.5 se quedan.
- **Generador**: los tramos donde la onda se apaga (6 mm boca / 10 mm pie) eran
  fijos en mm; a 160 mm el lomo subía en el mismo tramo corto y el arranque daba
  48° (z 2–8 mm). Ahora escalan con `alto/94` → 43°. A 94 mm la salida es
  idéntica byte a byte a la v1 (comprobado contra `.v1.bak`).
- Perfil: el usuario eligió el **estándar** (no maciza) y pidió bajar tiempo. Se
  quitó la pared maciza de la v2 y se agregó `infill_combination` 1 +
  `resolution` 0.05 (desviación invisible, no toca la pared exterior).
- Respaldo: `PortalapicesHuevoOndas.3mf.v2.bak`.

Por qué tardaba: a velocidad nominal los trazos suman ~2.5 h, el CLI decía 5 h.
El contorno son tramitos de 1.4 mm (malla de 320 segmentos por vuelta) y la
pared exterior nunca llega a sus 200 mm/s. `resolution` 0.05 junta tramitos;
`infill_combination` imprime el relleno cada 2 capas.

Tabla (CLI, 1 pieza por plato — a 147 mm no caben 2):

| Variante 16 cm (pared 3.0 / piso 4.5) | Tiempo | Peso | Costo |
|---|---|---|---|
| v2 (10.3 cm, maciza) | 3 h 32 | 133.7 g | $37.43 |
| estándar tal cual | 5 h 10 | 199.7 g | $48.99 |
| + `sparse_infill_pattern` grid | 5 h 12 | 199.7 g | — |
| + Arachne | 5 h 01 | 199.2 g | — |
| + capa 0.24 / 0.28 | 4 h 42 / 4 h 21 | ~203 g | — (además pierde acabado) |
| + `resolution` 0.05 | 4 h 40 | 199.3 g | $48.92 |
| + `infill_combination` | 4 h 17 | 194.1 g | $48.00 |
| **v3: combinación + resolution 0.05** | **3 h 47** | **193.5 g** | **$47.91** |
| v3 + relleno 10 % | 3 h 33 | 185.1 g | $46.43 |
| intermedio (3 per + 40 %) | 7 h 57 | 294.4 g | $65.56 |
| maciza (como v2) | 9 h 15 | 351.2 g | $75.50 |
| maciza pared 4.0 / piso 6 | 11 h 09 | 442.0 g | $91.39 |

Arc fitting y `resolution` 0.1 no ganaron nada más.

Regenerar la v3:
```
python3 generadores/huevo_lowpoly.py --nombre PortalapicesHuevoOndas \
  --superficie ondas --ondas 20 --torsion -0.3 --pie 0.64 \
  --ancho 143.0 --alto 160.0 --relieve 2.0 --filete 9.3 --pared 3.0 --piso 4.5
```
+ perfil P2S 0.20mm Standard con `infill_combination` 1 y `resolution` 0.05.

## Resultado real
- 2026-10-08: el usuario imprimió la v3: «está perfecto». Pidió después pared más
  lisa (se ven las líneas del filamento) y boca redonda (v4).

## 2026-10-08 (v4) — «que se vea un poco más lisa»; «se ven las líneas del filamento»; «arriba cerrar la boca… redondita para que no se vea plana»
Cambios v3 → v4:
- **Capa 0.20 → 0.12** (shells 5/3 → 9/5, mismo grosor en mm). Es lo que borra
  las líneas de capa; elegido por el usuario entre 0.20 / 0.16 / 0.12.
- **Labio redondo** (`--labio redondo`, opción nueva del generador): medio bordón
  de afuera hacia adentro que sube en la dirección de la pared, tangente por los
  dos lados, todo mirando hacia arriba (sin voladizo). Suma 1.3 mm: alto 161.3.
- **Malla más fina** (`--finura 32`, antes 16 puntos por estría): quiebres del
  contorno por capa p90 8.5° → 4.9°, sin costo de tiempo. Columnas de malla en
  espiral se probaron y no cambiaron nada medible: descartado.
- Respaldo: `PortalapicesHuevoOndas.3mf.v3.bak`.

Tabla (CLI, 1 pieza, labio redondo + finura 32):

| Variante | Tiempo | Peso | Costo |
|---|---|---|---|
| v3 (capa 0.20, labio plano) | 3 h 47 | 193.5 g | $47.91 |
| capa 0.20 | 3 h 43 | 194.7 g | $48.11 |
| capa 0.16 | 4 h 29 | 205.5 g | $49.99 |
| capa 0.16 + pared ext. 150 mm/s | 4 h 50 | 205.5 g | $49.99 |
| **v4: capa 0.12** | **5 h 15** | **205.8 g** | **$50.05** |

Regenerar la v4:
```
python3 generadores/huevo_lowpoly.py --nombre PortalapicesHuevoOndas \
  --superficie ondas --ondas 20 --torsion -0.3 --pie 0.64 \
  --ancho 143.0 --alto 160.0 --relieve 2.0 --filete 9.3 --pared 3.0 --piso 4.5 \
  --finura 32 --labio redondo
```
+ perfil P2S 0.20mm Standard con `layer_height` 0.12, `top_shell_layers` 9,
`bottom_shell_layers` 5, `infill_combination` 1, `resolution` 0.05.

## Pendiente / conocido y no resuelto
- Imprimir y confirmar la sensación en mano y el tiempo real (con el 01O el CLI
  se quedó corto ~40 %).
- `huevo_lowpoly.py` no embebe perfil de laminado: si se regenera, hay que
  volver a poner el de arriba (o agregarle `--ajustes` como `portacepillos_rapido.py`).
- v4: imprimir y confirmar que las líneas ya no se notan y cómo sale el bordón de la boca; tiempo real (5 h 15 según CLI).
