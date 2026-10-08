# gato_japandi (Katze Japandi)

Archivo: `own design 3d/gato_japandi.3mf` (backup: `.3mf.bak`)
Origen: comprado — "Katze Japandi" (Designer: ChrisB), mesh orgánico escaneado/esculpido
("Meshy_AI_cats..."), 749k caras, muy alto (Z es el eje vertical). Escala del usuario NO
uniforme: (2.05495, 1.66228, 2.02931) en (X,Y,Z). Ya con perfil P2S / plato 256.

## Feedback recibido
- 2026-09-27 — "Lo mismo" que Loop Remote / portalápices / elefante: más grande, más rápido
  sin perder calidad, y las que quepan en el plato.

## Diagnóstico — restricción dura de ALTURA
- Tamaño real actual: 114.9 × 179.1 × **242.6 mm de alto**. El plato de la P2S imprime hasta
  **256 mm de alto** (`printable_height` del perfil de máquina) — esta pieza YA usa el 95% de
  esa altura. Agrandarla "como el elefante" (+9% uniforme) la llevaría a ~265 mm: **no cabría
  en la impresora**. Por eso el crecimiento aplicado es mucho más chico que en piezas anteriores,
  y no uniforme: horizontal (X,Y) +5%, vertical (Z) solo +2% (deja 8.6 mm de margen a los 256 mm).
- Overhangs (ángulo desde horizontal, mismo método que el elefante): >20°=14.0% del área,
  >30°=9.6%, >50°=6.6%, >70°=6.1%. Ya es poco soporte (0.32 h de 7.1 h). **Probé subir
  `support_threshold_angle` 30→55° (la palanca que funcionó en el elefante) y en ESTA pieza
  empeoró: el soporte subió de 0.32 h a 1.49 h** — el sentido de la palanca no es universal,
  depende de la geometría; se descartó y se dejó el soporte en 30° tal cual estaba.
- Huella: 2 copias entran fácil lado a lado (rotadas 180° una de otra) con margen de sobra.
  Intenté una 3ª copia rotando en ángulos libres (igual que el elefante) y encontré varias
  disposiciones "válidas" en la búsqueda gruesa, pero al verificarlas con precisión (rasterizado
  fino + relajación física) ninguna daba una separación real fiable entre las 3 — el contorno
  del gato es cóncavo/irregular (no un blob convexo como el elefante) y el margen de holgura no
  alcanzaba. Se descartó la 3ª copia por seguridad en vez de forzar un archivo con piezas
  demasiado juntas.

## Cambios aplicados (2026-09-27)
- Escala: X 2.05495→**2.15770** (+5%), Y 1.66228→**1.74539** (+5%), Z 2.02931→**2.06990**
  (+2%). Tamaño nuevo: ~120.6 × 187.9 × 247.4 mm. Traslación Z recalculada (Tropiezo #3):
  `tz = 2.06990 × 59.7504501 = 123.678` (verificado con el rebanador: bbox height 247.4mm,
  z=0.0 en la base).
- 2 copias: mismo objeto, 2do `<item>` rotado 180° en Z (escala con signo negativo en X,Y,
  Bambu lo interpreta como la rotación), centros en X=64.96/191.04, Y=148.57/107.43 (uno
  "mirando" al otro, aprovechando que la silueta no es simétrica). Verificado con el propio
  rebanador (extrusión real del gcode): X 4.9–251.1mm, Y 4.2–247.7mm — dentro del plato con
  ~4.9mm de margen. `Metadata/model_settings.config` sincronizado (Tropiezo #5): 2do
  `model_instance` (`instance_id=1`, `identify_id=77`) y 2do `assemble_item`.
- Perfil (agregado a `different_settings_to_system`): `sparse_infill_pattern` grid→
  **adaptivecubic** (la densidad ya estaba en 8%, no se tocó). `layer_height` se **dejó en
  0.20mm** — es un escaneo orgánico de superficies curvas (no facetado como el elefante); subir
  a 0.24mm ahorraba poco más (7.1h→5.78h con capa gruesa vs 7.1h→6.52h solo con el relleno) y
  sí se nota en curvas suaves, así que prioricé calidad como pediste ("me encantó" la textura
  suave del anterior).
- Se quitó `plate_1.gcode`/`.md5` (rebanado viejo, 1 sola pieza).

## Resultado (CLI, comparativas por pieza SIN escalar, para aislar el efecto del relleno)
| Perfil | Tiempo/pieza | Peso/pieza (estimado, ver calibración) |
|---|---|---|
| Original (grid 8%, 0.20mm) | 7.10 h | 256g (REAL, de la tarjeta) |
| adaptive cubic 8%, 0.20mm | 6.52 h (−8%) | ~204g (−20%, calibrado) |

**Con el tamaño nuevo (+5%/+2%) las 2 copias juntas: 14.15 h totales (~7.08 h/pieza),
~459 g totales (~229 g/pieza, calibrado)**. Importante ser honesto: el ahorro de tiempo del
relleno (−8%) queda casi anulado por el aumento de tamaño (+5/+2%, ≈+12% de volumen) — el
tiempo por pieza casi no cambió (7.10h→7.08h). Lo que sí se gana es que **antes había que
imprimir 2 gatos en 2 corridas separadas (≈14.2h con recarga en medio); ahora salen los 2 en
UNA sola corrida de 14.15h**, sin intervención a mitad de camino. Si se prefiere velocidad real
por pieza en vez de tamaño, la alternativa es no agrandar (dejar 2.055/1.662/2.029) y quedarse
con los 6.52h/pieza.
- Calibración del peso: mi estimador (suma de E del gcode × área × densidad) da 178.1g para la
  config original sin escalar, pero el peso REAL de la tarjeta es 256.46g (factor ×1.44 —
  bastante más alto que en otras piezas, probablemente por cómo esta gcode reporta extrusión;
  no lo investigué a fondo). Usé la PROPORCIÓN entre configuraciones (no el valor absoluto) para
  proyectar el peso real de la versión nueva.

## Pendiente / conocido y no resuelto
- Falta que el usuario rebane e imprima: confirmar tiempo, peso real y que la altura (247.4mm)
  no tenga problema en la práctica (colisión de la torre Z, mirillas, etc. — dejé 8.6mm de
  margen a los 256mm nominales).
- 3ª copia descartada por seguridad (ver diagnóstico) — si el usuario quiere insistir, se puede
  intentar con una malla mano a mano en Bambu Studio (arrastrando y usando "Organizar
  automáticamente" con más paciencia que la búsqueda automática que hice).
- No se tocó soporte (ya era bajo, y la única palanca probada lo empeoró).

## Sesión 2026-10-02 — máximas copias tras ajustes del usuario
El usuario reajustó el archivo en Bambu Studio (1 sola copia, escala X 1.74644 / Y 1.41272 /
Z 1.67538 → 97.6 × 152.2 × 200.2 mm, `enable_support` activo, tree(auto), 30°,
`support_on_build_plate_only=0`, 2 paredes, adaptive cubic 8%, capa 0.20). **No se tocó ninguno
de esos ajustes** — solo el empaque. Respaldo del estado del usuario: `gato_japandi.3mf.v1.bak`.
- Método nuevo (mejor que el hull convexo de la sesión 09-27): silueta REAL cóncava de la
  proyección XY (rasterizada a 0.25 mm; 8,642 mm² vs 10,354 del hull) y colocación por
  correlación FFT sobre el plato con rotaciones cada 5-10°, miles de arranques aleatorios.
  Así los gatos se encajan unos en otros (la silueta es muy cóncava).
- **Corrección (mismo día):** Bambu avisó "ruta de G-code fuera del plato". Rebané por CLI
  (`BambuStudio --slice 1`) y medí el recorrido por `; FEATURE:`: lo único que se salía era el
  **soporte de árbol** (Y hasta 257.9, plato 256); paredes/relleno estaban dentro. El soporte
  sobresale hasta ~16 mm de la silueta (rellena concavidades y trepa en los extremos), así que
  5 mm de margen no alcanzaban. Se midió la huella real del soporte por gato en su marco local,
  se infló la silueta con ella (9,127 mm² vs 8,635) y se re-empacó ESA forma (margen 3 mm,
  4.3 mm entre huellas). Con 10 mm de margen uniforme solo entraban 3; usar la huella real
  conserva las 4.
- Resultado: **4 copias** (primera versión rot. 310/140/320/320; la corregida usa otras
  posiciones). Con silueta real ~900 corridas nunca dieron 5.
- Rebanado verificado de la versión corregida: **cero movimientos fuera del plato**
  (soporte X 7.9–242.5, Y 95.8–246.0; paredes Y ≤251.1), **18 h 21 m, 561.9 g las 4 juntas**
  (~140 g/pieza, ~4.6 h/pieza).
- `model_settings.config` sincronizado: 4 `model_instance` (identify 77-80) y 4 `assemble_item`.
- Pendiente: que el usuario imprima y confirme que los soportes entre gatos encajados se retiran bien.
- Lección: al empacar piezas con soporte de árbol (`support_on_build_plate_only=0`), empacar la
  huella silueta+soporte medida del rebanado, no la silueta sola.
