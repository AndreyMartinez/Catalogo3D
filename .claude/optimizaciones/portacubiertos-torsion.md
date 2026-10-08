# Portacubiertos_Torsión_3ranuras

Archivo: `own design 3d/portacubiertos/Portacubiertos_Torsión_3ranuras.3mf`
Origen: **generador propio** (`generadores/`), diseño "libre" (no una receta fija de
`DISENOS` — se armó a mano desde la pestaña Crear/Idea con parámetros custom:
contorno óvalo, acabado torsión, perfil barril, 3 ranuras, drenaje).
Backup del original en `Portacubiertos_Torsión_3ranuras.3mf.bak`.
A diferencia de las demás piezas del registro, esta NO se edita hackeando el .3mf
— se regenera con `python3 generadores/crear.py libre --param valor ...` (ver
skill, sección 1: "si viene de `generadores/`, usar `crear.py`").

## Feedback recibido
- 2026-09-21 — Entre las curvas del acabado queda como "hilos" que no dan un
  toque liso. Reducir un poco el tamaño para bajar el gramaje, y aplicarle todos
  los ajustes de calidad.

- 2026-09-24 — (con foto de la impresión real, negro) Siguen saliendo hilos/rebabas
  sueltos a lo largo de las crestas de la torsión, se ve sucio de los lados. Además:
  optimizar tiempo de impresión sin perder calidad, y que quepan 3 en la bandeja
  sin perder mucho tamaño.

## Diagnóstico
- Parámetros originales (extraídos de la metadata `Catalogo3D:parametros`
  embebida en el propio .3mf — el generador la guarda siempre):
  ancho 177, fondo 76, alto 112, `onda_amplitud=1.2`, `pared=2.0`.
- **La causa de los "hilos" está documentada en el propio código** (`cuerpo.py`
  línea ~200): el motor limita `onda_amplitud` a `(pared - 0.8) / hunde` porque
  por debajo de 0.8mm de pared en el valle de la estría "el laminador no mete dos
  hilos ahí" — literalmente el mismo término que usó el usuario. Con pared=2.0 y
  onda_amplitud=1.2, el valle quedaba EXACTO en el mínimo de 0.8mm — al filo del
  límite, no técnicamente "recortado" (no disparó el aviso automático) pero sin
  ningún margen, lo que explica el acabado marginal reportado.
- Reproducido con `crear.py libre` y los parámetros originales: 218.1×95.1×112.2mm,
  206g, sin avisos (porque no está literalmente clippeado, solo al límite).

- 2026-09-24 — **Causa real de los hilos (la de 09-21 era solo parte):** la cara
  interior de la pared era lisa y la exterior ondulada, así que el espesor oscilaba
  entre ~1.25 y ~2.75 mm a lo largo de cada estría. Con 2 perímetros (0.84 mm) el
  laminador pasa de "2 hilos" a "2 hilos + relleno/gap fill" en cada cresta: por eso
  las rebabas siguen la diagonal de las crestas de la torsión. Sobrevoladizo NO es
  la causa (máx. 33° respecto a la vertical en las caras laterales).
- 2026-09-24 — Tiempo (rebanado real por CLI de Bambu Studio con perfil P2S + PLA
  Basic P2S): la pieza vieja (169 g, 0.20 mm, 2 perímetros, 15%) = **5.27 h**, con
  Gap infill 0.78 h, Travel 1.6 h. Los 632k triángulos con facetas de 0.5 mm no
  frenan tanto como parecía una vez cargado el filamento correcto (sin filamento
  el CLI asume 2 mm³/s y da 16-20 h: NO usar esos números).

## Cambios aplicados
- 2026-09-21: `onda_amplitud` 1.2→**0.75mm** — deja el valle en ~1.25mm de pared en
  vez de exactamente 0.8mm (el mínimo absoluto), con margen real. Verificado con
  `crear.py`: ya no aparece ningún aviso de relieve recortado.
- 2026-09-21: tamaño reducido ~10% en las 3 dimensiones (ancho 177→160,
  fondo 76→69, alto 112→102) — de 218.1×95.1×112.2mm a **195.4×85.7×102.2mm**.
- 2026-09-21: calidad — `grano` 0.6→0.4 pedido (el motor lo relajó solo a 0.5mm
  por presupuesto de malla, avisó y sugirió subir `onda_paso` o bajar
  `torsion_vueltas` si se ve escalonado — a 0.5mm no se ve escalonado en el
  render, se dejó así), `segmentos` 480→600, `capas` 64→80.
- Archivo regenerado completo (.3mf + .stl + .png) en el mismo lugar con
  `crear.py`, reemplazando el original (con backup).

- 2026-09-24 (generador): parámetro nuevo `pared_forma` ("lisa" | "sigue", por
  defecto "lisa", no cambia ninguna receta existente) en `disenos.py` +
  `nucleo/cuerpo.py`: con "sigue" la cara interior copia el relieve
  (`anillo_int`/`aro_i` restan `acabado(s,z)` al desplazamiento) y el plano medio
  para divisores pasa a `-pared/2`. Pruebas del generador: 89/89 OK.
- 2026-09-24 (pieza): `pared_forma=sigue`, `pared` 2.0→**1.7** (= 4 perímetros de
  0.42, sin relleno dentro de la pared), `fondo` 69→**63** (eje Y 85.7→78.4 mm; ancho
  y alto intactos: 196.0×78.4×102.2 mm) para que quepan 3 en Y. Peso del generador
  169→**147 g** por pieza.
- 2026-09-24 (3 copias): un solo objeto, 3 `<item>` con transform, apilados en Y con 7 mm
  entre sí (centros Y 42.6/128/213.4, márgenes ~3.4 mm), X centrado en 128. Malla
  recentrada en el origen (estilo Bambu) + `Metadata/model_settings.config` con 3
  `model_instance`. Verificado con el propio rebanador (CLI, `--arrange 0`): las 3
  caen en un solo plato P2S (256×256), 11.1 h en total. El arrange automático de
  Bambu las acomoda con 1 mm de hueco, así que sobra aire.
- 2026-09-24 (perfil P2S embebido, `Metadata/project_settings.config`, base "0.16mm
  Standard @BBL P2S"): `layer_height` 0.16, `wall_loops` 4, `sparse_infill_density`
  5%, `bottom_shell_layers` 8, `top_shell_layers` 5, `enable_support` 0 (voladizo máx
  33°), `ironing_type` no, `seam_position` back, `resolution` 0.02, `enable_prime_tower`
  0 (una sola tinta; con la torre activada el arrange de Bambu reservaba espacio).
  Todas en `different_settings_to_system` (Tropiezo #1). Ojo: copiar SOLO los ids de
  preset no basta — hay que volcar también las llaves de impresora/proceso
  (`printable_area`, etc.) o Bambu se queda con el plato de 180 mm de la A1 mini.
- Respaldos: `.3mf.bak` (206 g original), `.3mf.v2.bak` (169 g de la sesión 09-21).

## Resultado real
- 2026-09-24 (rebanado por CLI, 1 pieza): 0.16 mm → **3.69 h** (vs 5.27 h la vieja,
  −30 %); 0.20 mm → 2.99 h; 0.24 mm → 2.71 h. Se dejó 0.16 por calidad de la
  torsión. Las 3 en un plato: ~11.1 h.
- Del propio generador (esto SÍ es el número real, no un estimado — el motor de
  `cuerpo.py` calcula el volumen exacto de la malla, a diferencia de las piezas
  compradas donde solo Bambu Studio rebanando da el número real):
  206g → **169g** (−18%), 605,444 → 621,200 triángulos (más resolución pese a
  pesar menos).
- (09-21) Falta que el usuario abra el nuevo archivo en Bambu Studio, rebane, e imprima
  para confirmar que el acabado ya no muestra "hilos" en la práctica — el ajuste
  resuelve la causa documentada en el código, pero no hay una impresión física
  todavía que lo confirme.

## Pendiente / conocido y no resuelto
- Ninguno de los "3 tropiezos" de piezas compradas aplica aquí (no hay
  `project_settings.config` ni transforms que tocar — el generador propio no
  tiene esos problemas). Si en el futuro se quiere ajustar el perfil de
  impresión de Bambu Studio para esta pieza (paredes, relleno, etc.), eso sí
  sigue las reglas normales del skill una vez que el usuario la abra y guarde en
  Bambu Studio por primera vez.
- 2026-09-24: falta imprimir y ver la foto del resultado — que el espesor parejo
  elimine las rebabas es el diagnóstico más sólido, pero no está confirmado
  físicamente. Si persisten, probar `wall_generator` classic y/o bajar `outer_wall_speed`.
- Si el gramaje real de Bambu (tras Rebanar) se aleja de 147 g por pieza, es por el
  gap infill; el CLI no reporta peso (sale 0.00).
- El catálogo ahora verá 3 piezas por archivo: el gramaje por pieza = total / 3.
