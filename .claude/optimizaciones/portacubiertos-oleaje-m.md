# Portacubiertos Oleaje M

Archivo: `own design 3d/Pruebas de productos/Portacubiertos_Oleaje_M.3mf` (+ `.png`, `.stl`;
antes en `portacubiertos/`, movido a pruebas desde la galería el 10-19)
Origen: **generador propio** (clave `portacubiertos`, perfil `oleaje`), a partir de una
foto de referencia: óvalo con estría fina vertical y dos panzas con cresta en «M».
Desde la v3 tiene 3 compartimentos y la medida del Portacubiertos Torsión.

Los parámetros completos van dentro del .3mf (`Catalogo3D:parametros`). Los que se
salen de la receta `portacubiertos` (v2; la v3 cambia lo que dice su sección):

```json
{"contorno": "superelipse", "ancho": 180, "fondo": 102, "redondeo": 47, "alto": 115,
 "acabado": "ondulado", "onda_amplitud": 0.7, "onda_paso": 3.6,
 "acabado_desvanece": 6, "acabado_cierre": 1.0,
 "perfil": "oleaje", "perfil_intensidad": 0.064, "oleaje_ondas": 2,
 "oleaje_inclinacion": 0.04, "oleaje_giro": 0.5, "oleaje_desfase": 0.8,
 "oleaje_m": 0.23, "oleaje_m_ancho": 0.40,
 "pared": 1.95, "piso": 1.2, "ranuras": 2, "filas": 2,
 "divisor_grosor": 2.0, "divisor_alto": 75, "divisor_forma": "ola", "divisor_ola": 3.0,
 "drenaje_diametro": 0, "base_redondeo": 6, "grano": 0.6, "segmentos": 600}
```

### Parámetro «cresta en M» (`oleaje_m`) — en el motor desde el PR #16 (10-19)

En la foto, la cresta de cada panza sube hacia los extremos y se hunde al centro
del frente y de la espalda, como el borde de arriba de una «M». El perfil
`oleaje` no lo hacía (las panzas dan la vuelta pareja). Se probó con un parche en
una copia temporal de `generadores/nucleo/perfiles.py` (función `oleaje`, dentro de
`angular`, justo después de calcular `fase`):

```python
m_caida = float(p.get("oleaje_m", 0.0))            # antes de def angular
m_ancho = max(0.05, float(p.get("oleaje_m_ancho", 0.35)))
...
        if m_caida > 0.0:
            u = math.cos(theta)
            # Se apaga en la boca y en la base: el labio queda óvalo limpio.
            fase += (m_caida * math.exp(-(u / m_ancho) ** 2)
                     * math.sin(math.pi * min(1.0, max(0.0, z))))
```

más dos `num(...)` en `disenos.py` (`oleaje_m` 0–0.30, `oleaje_m_ancho` 0.10–1.0).
Sin el `sin(πz)` la boca se deformaba vista desde arriba. Pasar de 0.25 dispara el
voladizo (51° con 0.25/0.40): por eso la intensidad del perfil bajó a 0.064.
Integrado al motor con la receta `portacubiertos_oleaje_m` en
[AndreyMartinez/Catalogo3D#16](https://github.com/AndreyMartinez/Catalogo3D/pull/16)
(fusionado a `main`, commit 48067e9). Según esa sesión, la pieza regenerada sale
idéntica al .3mf de la v2.

## Feedback recibido
- 2026-10-18 — «Quiero que creemos este portacubiertos» (foto); antes del 3MF,
  la imagen y la viabilidad.
- 2026-10-18 — «las olas tienen como la parte superior de una M, y es un poquito
  más ovalado» → cresta en M + planta superelipse (exponente ~2.6) en vez de óvalo
  de pista.
- 2026-10-18 — «la pared un tris más gruesa de las divisiones y del borde».
- 2026-10-19 — «con la rápida y optimízala»; «¿se puede reducir los 154 g?».
- 2026-10-19 — «la pared puede ser más alta y dividida en 3, tener este mismo ancho
  y alto» (tarjeta del Portacubiertos_Torsión_3ranuras) → eligió la opción con el
  mismo fondo también.

## Diagnóstico
- **Tiempo con pared 2.2 maciza (perfil normal, 2 vueltas, hilo interior 0.62):**
  21 h 16 m la placa de 2 y 183 mil retracciones. La vuelta interior se parte en
  un triangulito por estría (dibujo de la capa z=60), con relleno de hueco entre
  ellos. Es el mismo fenómeno del portacepillos ([[tiempo-lo-manda-el-numero-de-trazos]]).
  «Sigue el relieve» lo empeoró (32 h) y Arachne con 2 vueltas también (37.7 h y 22 h).
- **Receta rápida:** 1 vuelta + Arachne con los hilos de 0.62 se tocan en el valle
  solo si valle = pared − relieve ≈ 2 × 0.62 → **pared 1.95** con relieve 0.7. Con
  2.2 quedaban dos cáscaras separadas ~0.25 mm en el valle (variante G). Con 1.95 se
  tocan en el valle y quedan huecos dentro de las crestas (patrón aceptado en el
  portacepillos rápido).
- **Drenaje:** quitado por el bug documentado en [portacubiertos-nuevo](portacubiertos-nuevo.md)
  (pared de 0.03 mm donde los agujeros caen en las puntas del óvalo). La foto no
  tiene agujeros.
- **Capa 0.24:** más lenta que 0.20 (24 mil retracciones contra 9 mil). Descartada.
- **Peso:** la palanca real es el piso (2.0 → 1.2 mm ≈ −8 g por pieza). La
  estimación de gramos del motor no sirve para comparar alturas de divisor (salía
  al revés); solo cuenta lo laminado.
- **Costo:** precio_kg 167, paquete «Paquetería» $16.38 (41 % del costo en la v2).
- Voladizo máximo 46.7° (cierra), sin soportes. Plato P2S: 2 piezas en 193 × 240 mm.

## Versiones (CLI Bambu Studio 02.08, P2S, Bambu PLA Basic; por pieza)

| v | pared | piso | divisores | drenaje | perfil | tiempo | peso | costo |
|---|---|---|---|---|---|---|---|---|
| v1 | 2.2 | 2.0 | 2.0 × 88 | 5 mm | 2 vueltas clásico, interior 0.62 | 10 h 38 m | 214.6 g | $52.22 |
| — | 1.95 | 2.0 | 2.0 × 88 | 5 mm | rápida | 3 h 46 m | 152.2 g | $41.79 |
| — | 1.95 | 2.0 | 2.0 × 88 | no | rápida | 3 h 33 m | 154.3 g | $42.14 |
| — | 1.95 | 1.2 | 2.0 × 88 | no | rápida | 3 h 19 m | 145.9 g | $40.75 |
| v2 (2/plato) | 1.95 | 1.2 | 2.0 × 75 | no | rápida | 3 h 19 m | 140.8 g | $39.89 |
| **v3** (3/plato, 195.5×78×102, 3 compartimentos) | 1.95 | 1.2 | 2.0 × 100 | no | rápida | **2 h 34 m** | **105.1 g** | **$33.93** |

Perfil rápido (en `project_settings.config` y en `different_settings_to_system`):
`wall_loops` 1, `wall_generator` arachne, `outer/inner_wall_line_width` 0.62,
`filter_out_gap_fill` 0, `resolution` 0.05, `sparse_infill_density` 0 %,
`top_shell_layers` 3, `infill_combination` 1. Base de ajustes: `portacubiertos nuevo.3mf`
(0.20 mm Standard P2S, Bambu PLA Basic, 21 mm³/s).

## 2026-10-19 (v2) — «con la rápida y puedes optimizar la pieza»
Cambios v1 → v2: pared 2.2 → 1.95, receta rápida, sin drenaje, piso 2.0 → 1.2,
divisores 88 → 75 mm (40 mm bajo la boca, como en la foto).
Placa de 2: 21 h 16 m / 429.2 g → **6 h 39 m / 281.6 g**. Por pieza: −7 h 19 m,
−73.8 g, −$12.33. Respaldos: `Portacubiertos_Oleaje_M.3mf.v1.bak` y `.png.v1.bak`
(`.3mf.bak` = la misma v1, primer archivo).

## 2026-10-19 (v3) — «la pared puede ser más alta y dividida en 3, tener este mismo ancho y alto»
Medida del Portacubiertos_Torsión_3ranuras (196.0 × 78.4 × 102.2 por fuera). Se
mostraron dos opciones: A con el fondo actual (195.5 × 113.5 × 102, ~188 g) y B igual
al Torsión. El usuario eligió la B. Cambios v2 → v3: planta 180×102 → 184×66.5
(redondeo 47 → 30, mismo exponente de superelipse), alto 115 → 102, `ranuras` 2 → 3 y
`filas` 2 → 1, divisores 75 → 100 mm (2 mm bajo la boca). `perfil_intensidad`
0.064 → 0.055 porque las mismas panzas en menos altura subían el voladizo a 51°;
queda en 46.5°. Plato: 3 piezas en 195.5 × 248 mm (separación 7 mm).
Placa: 2 piezas en 6 h 39 m / 281.6 g → **3 piezas en 7 h 42 m / 315.2 g**. Por
pieza: −45 m, −35.7 g, −$5.96. Respaldos: `.3mf.v2.bak` y `.png.v2.bak`.
Parámetros que cambian respecto de la v2:
`{"ancho": 184, "fondo": 66.5, "redondeo": 30, "alto": 102, "perfil_intensidad": 0.055,
"ranuras": 3, "filas": 1, "divisor_alto": 100}`.

## Pendiente / conocido y no resuelto
- Imprimir la v3: confirmar que la pared sale maciza en los valles (no dos
  cáscaras), que el voladizo de 46.5° bajo la panza de arriba no se cae, que la
  estría se ve como en la foto y que los cubiertos caben en los compartimentos
  angostos (~55 mm en la cintura).
- La receta `portacubiertos_oleaje_m` del motor es la v2; si la v3 se queda,
  actualizarla.
- Lo que queda de tiempo es pared exterior (5.9 h de las 7.6 h de la placa), frenada
  por el tope de 21 mm³/s del filamento. No se subió.
- Si hace falta rascar peso: divisores 2.0 → 1.6 mm (~−8 g, va contra lo que pidió
  el usuario).
