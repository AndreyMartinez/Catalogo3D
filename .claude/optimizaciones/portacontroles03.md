# pORTAcONTROLES03 ("pORTAcONTROL" en la tarjeta)

Archivo: `own design 3d/pORTAcONTROLES03.3mf`
Origen: comprado/generado vía "Parametric Model Maker" de MakerWorld (no es nuestro
generador propio — sin Designer declarado, MakerLab: "Parametric Model Maker").
Backup original en `pORTAcONTROLES03.3mf.bak`.
Estructura: 2 copias idénticas del mismo objeto (`object_1.model`, 3 ranuras), una al
lado de la otra en el plato. El peso de slice_info es de las 2 juntas.

## Feedback recibido
- 2026-09-19 — Mejorar calidad, reducir peso pero sin perder lo grueso de las
  paredes (que se sienta imponente), y corregir un acabado feo en las curvas de los
  bordes de la parte inferior.

## Diagnóstico
- Grosor real medido (ray-cast por vértice, mesh compartida por las 2 copias):
  - Zona inferior/curva de borde (la que reportó el usuario, z≈-44, cerca del piso):
    mínimo 0.715mm, 168 vértices por debajo de 1.2mm.
  - **Encontrado sin que lo pidiera, más grave**: esquina superior donde un divisor
    se junta con la pared exterior (z≈45-47, las 4 esquinas): grosor de hasta
    **0.013-0.16mm**, prácticamente sin material. Intentar el mismo arreglo de
    empuje-por-normal ahí generó caras con normal invertida (mesh dañada) — es un
    pellizco geométrico distinto a un simple "pared delgada", no un simple
    engrosado. Se dejó SIN TOCAR a propósito para no entregar un archivo roto.
- Volumen sólido-equivalente (mesh única × 2 copias): 615.6cm³. Con 310.66g medidos
  y 15% de relleno, shell_vol implícito ≈186cm³ (~30% del total) — bastante más
  hueco real que el portacepillos, así que bajar relleno sí tiene buen margen aquí.

## Cambios aplicados
- 2026-09-19: engrosamiento de malla SOLO en la zona inferior/curva reportada
  (restringido a z<-20 a propósito, para no acercarse al pellizco superior sin
  resolver) — grosor mínimo en esa zona 0.715mm → 1.160mm. Verificado: watertight,
  sin caras invertidas, volumen +1.1cm³ (insignificante).
- 2026-09-19: NO se tocó `wall_loops` (se dejó en 2) a propósito, para cumplir "que
  no pierda lo grueso de las paredes".
- 2026-09-19: `sparse_infill_density` 15%→6% (única palanca de peso usada, ya que
  hay margen real de hueco interior aquí, a diferencia del portacepillos).
- 2026-09-19: calidad — `layer_height` 0.2→0.12, `top_shell_layers` 5→8,
  `bottom_shell_layers` 3→5, `ironing_type`→"top surface", `detect_thin_wall`→1.
  Todo registrado correctamente en `different_settings_to_system` desde el
  principio (ya no se repitió el error de las piezas anteriores).

## Resultado real
- Estimado inicial: 310.7g → ~265g (−15%), sin tocar tamaño exterior ni `wall_loops`.
- El usuario SÍ imprimió con el primer arreglo (margen a 1.4mm + `detect_thin_wall=1`)
  y reportó, con foto real de la impresión, que el borde inferior de la curva salía
  "peludo/serrado" — un acabado feo a lo largo de todo el borde donde toca la placa,
  justo en la zona que se había arreglado.

## Corrección 2 (2026-09-19, tras ver la foto)
Diagnóstico: 1.4mm de margen deja apenas ~0.5mm de holgura sobre el ancho de 2
perímetros (~0.87mm) — muy justo para una curva compleja. Sospecha: con
`detect_thin_wall=1` activado, el slicer trataba esa franja límite de forma
inconsistente (líneas delgadas sueltas en vez de pared sólida de 2 perímetros),
produciendo exactamente ese aspecto peludo/con hilos.
Arreglo: rehecho el engrosado de la curva inferior desde la malla ORIGINAL (no sobre
la ya parchada, para no acumular dos suavizados) con margen más generoso — **2.0mm**
en vez de 1.4mm. Verificado: watertight, sin caras invertidas, grosor mínimo en la
zona 0.715mm → **1.731mm** (antes solo llegaba a 1.16mm). Además se **desactivó
`detect_thin_wall`** (vuelto a 0): con ~0.86mm de holgura sobre 2 perímetros ya no
debería hacer falta, y es sospechoso de causar el toolpath errático.

## Pendiente / conocido y no resuelto
- **La esquina superior con el pellizco de 0.01-0.16mm sigue sin arreglar.** Es más
  grave que lo que el usuario reportó originalmente, pero arreglarla necesita una
  técnica más cuidadosa que el empuje-por-normal simple (esa geometría genera
  auto-intersecciones). Ofrecido al usuario, no confirmado si quiere que se intente.
- Falta que el usuario reimprima con este segundo arreglo y confirme si el borde ya
  sale limpio, y el gramaje real.

## 2026-10-02 — /transform, foco en la curva inferior ("no se ve pulida")
Estado de partida: el archivo ya traía 3 copias (3 filas de 160×80 mm, 1 mm de hueco) y
Bambu Studio le había quitado `ironing_type` (estaba en "no ironing"). Backup previo a este
pase: `pORTAcONTROLES03.3mf.v2.bak`.

**Causa real del borde "peludo/serrado" (no era el grosor):** el borde inferior es un filete
de ~14.5 mm que arranca TANGENTE a la placa (δ=14.5 mm a z=0 → 5 mm a z=3.7). Con capas de
0.12 mm la pared de una capa sobresale hasta ~1 mm sobre la anterior en los primeros 2 mm
(pendiente run/rise de 16 → 1.3): son voladizos de aire, no un acabado ajustable por
velocidad/ironing. Por eso ni el engrosado (06-19) ni `detect_thin_wall` lo resolvían.
**Arreglo:** en la malla, solo los vértices del anillo exterior con z<3.7 mm se desplazan
hacia afuera (normal horizontal del rectángulo redondeado 160×80, R=15) para que por debajo
de z=3.7 la pared sea una recta de pendiente 1.27 (~38° sobre la horizontal) en vez del arco
casi plano. Continuo en tangente con el filete (sin arista), base 131×51 → 140.6×60.6 mm,
radio de esquina en la base 0.5 → ~5.3 mm. Cada capa sobresale ahora ~0.15 mm (<0.42 de
ancho de línea). Verificado: watertight, winding consistente, 0 normales volteadas, grosor
mínimo en z<14 igual que antes (1.74 mm), volumen +1.26 cm³, 0 overhang bloqueado por la
propia malla (sin cambio en soporte).

Otros cambios del pase: `ironing_type`→"top surface" (registrado en
different_settings_to_system). `detect_thin_wall` se deja en 0 (sigue el pellizco de
0.02–0.16 mm en las esquinas superiores, 88 vértices <0.8 mm — pendiente sin resolver).
Empaque: 3→**4 copias**: 3 filas en Y (x=85, y=45/128/211, 3 mm de separación) + 1 copia
rotada 90° en la franja derecha (x=211, y=128). Distancia mínima 3.01 mm, todas dentro
(margen ≥5 mm). `model_settings.config` sincronizado (objeto 5, identify_id 211).
Peso/costo: sin cambio (relleno 6%, 2 loops); falta rebanar para gramaje/tiempo reales
(4 piezas a 0.12 mm será una impresión larga, ~20+ h — si es demasiado, quitar la 4ª copia).

## 2026-10-07 — "ya no se ve liso" + borde feo otra vez al imprimir
- El usuario vio en la tarjeta del catálogo la curva inferior sin arreglar. **Causa de eso:** la
  miniatura que muestra el catálogo es `Metadata/plate_1.png` DENTRO del .3mf, y el pase del
  10-02 editó la malla pero no la regeneró (seguía la del 09-19: 3 piezas, base vieja). La malla
  SÍ estaba arreglada (base 140.6×60.6 mm a z=0). Se regeneró `plate_1.png`/`plate_1_small.png`
  con `generadores/nucleo/render.py` (4 copias, geometría actual). Respaldo: `.3mf.v3.bak`.
  **Regla:** al editar la malla de un .3mf, regenerar siempre la miniatura.
- Después el usuario reportó que, al MANDAR A IMPRIMIR, el borde feo volvió. Rebané por CLI el
  archivo tal cual (4 copias, 0.12 mm): pared exterior crece 0.15→0.10 mm/capa desde z=0.2 hasta
  z=5.5, 0 puntos de "Overhang wall", sin soporte, sin brim visible en esa zona → **el G-code de
  este archivo NO explica el defecto**. Pendiente: foto de la pieza impresa y confirmar desde qué
  archivo/proyecto se rebanó (¿proyecto viejo abierto en Bambu Studio con la malla anterior?).
  Candidatos aún sin descartar: elephant_foot_compensation 0.15 mm en capas bajas, aceleración/
  velocidad de pared exterior en la curva, `Floating vertical shell` en capas 50-62 (interior).

## 2026-10-07 (2) — foto del borde: causa y arreglo real
Foto del usuario (IMG_5627): pelusa/hilos SOLO en el tramo bajo de la curva (primeros ~2-3 mm
sobre la placa), liso más arriba. Es el patrón de voladizo demasiado inclinado, no de velocidad
(el G-code imprime la pared exterior a 46-50 mm/s en esas capas) ni de soporte.
Medido cortando la malla cada 0.05-0.25 mm (perfil d(z) = inset del contorno exterior respecto
al rectángulo 160×80): la pendiente run/rise era **1.27 (52° de la vertical) hasta z=3.1**,
~1.07 (47°) hasta 4.5, 0.94 hasta 5.3 y ≤0.83 desde ahí. El arreglo del 10-02 solo había
reemplazado el arco tangente por una recta de 1.27 — mejor que antes (1 mm/capa) pero aún >45°.
**Arreglo:** pendiente tope **0.80 (38.7° de la vertical)** desde z=0 hasta z=5.8 mm (donde el
arco original ya baja de 0.8; empalme casi tangente, sin arista). Se desplazan 1,352 vértices
del anillo exterior a lo largo de la normal del rectángulo redondeado. Base a z=0: 140.6×60.6 →
**144.5×64.5 mm** (inset 9.70→7.79). Cada capa de 0.12 sobresale ahora 0.10 mm (antes 0.15).
Verificado: watertight, winding consistente, 0 caras volteadas (min dot 0.81), +1.7 cm³, 0 puntos
"Overhang wall"; rebanado: 18 h 28 m, 568.9 g las 4 copias. Respaldos: `.v4.bak` (antes de
este arreglo, con miniatura nueva). Miniatura regenerada otra vez con la geometría nueva.
Pendiente: que el usuario imprima y confirme. Si aún hay pelusa, siguiente paso = bajar tope a
0.6 (31°) o chaflán de 45° recto, o subir el abanico de pieza en capas 2-50.
Lección (para otras piezas con base redondeada): el límite práctico es ~40° de la vertical con
capa de 0.12 mm; medir SIEMPRE el perfil con cortes, no con la tabla de vértices (mezcla
superficies interiores).

## 2026-10-07 (3) — malla rehecha exacta + velocidad (sesión con Opus 5.5)
Pedido: «toda la pulidez de detalle a las paredes», borde inferior que no se ve parejo, y más
velocidad sin bajar calidad (se vende en Mercado Libre).
**Hallazgos:** (1) la malla comprada tiene 9.7 k triángulos: los filetes R15 van en bandas de
~1.4 mm que el laminado reproduce como facetas (en el G-code se ve el contorno crecer a saltos
cada 3 capas); (2) el borde «disparejo» era real: en el archivo del 10-07 las esquinas de la base
crecían **0.23 mm/capa** entre z=3.9 y 5.6 mientras los lados crecían 0.096 (el parche movía
vértices de triángulos largos y en las esquinas la interpolación se salía 0.5 mm del perfil);
(3) la costura «aligned» caía en la esquina redondeada **delantera derecha**, a la vista.
**Arreglo — geometría:** medida por rayos, la pieza es exactamente un núcleo |x|≤65, |y|≤25,
z ≤ 20+0.6·y engordado 15 mm (Minkowski), menos 3 bolsillos 45.33×68 de esquina R4 con piso a
6 mm. Se rehízo con función de distancia + marching cubes (paso 0.25, proyección de vértices a
la superficie exacta, simplificada a 300 k triángulos; error medio 0.0002 mm, estanca):
`generadores/portacontroles03_pulido.py`. Mismas medidas (160×80×100) y la misma base aprobada
(chaflán 0.80 = 38.7° que entra tangente al arco R15, 7.79 mm de entrada), pero ahora exacta y
pareja en lados y esquinas (G-code: 0.096 mm/capa en lados, 0.13-0.14 en la diagonal, sin saltos).
Además: canto superior redondeado r=1.2 (antes filo de cuchillo donde la pared se junta con el
bolsillo) y filete cóncavo r=1.5 en el piso de los bolsillos. Las 4 esquinas de arriba siguen
bajando un poco (el bolsillo R4 no es concéntrico con la esquina R15 — propiedad del diseño
original; arreglarlo pide bolsillo R9 en esas esquinas, no se hizo para no quitar espacio a los
controles).
**Arreglo — costura:** franja pintada (paint_seam) al centro de la espalda y, en cada bolsillo,
al centro de la cara interior del labio delantero; costura biselada (scarf) en paredes externas.
**Velocidad (rebanado CLI, 4 piezas):** antes 18 h 28 m / 568.8 g →
**15 h 19 m / 549.2 g** (−3 h 10 m, −17 %). Lo que pesó: `infill_combination`=1 (relleno cada
2 capas, invisible: −2.4 h) y altura de capa 0.16 en la franja de pared recta z=17-53 con
rampas de 0.14 (rangos editables en Bambu bajo cada objeto: −50 min); scarf cuesta +13 min.
Probado y descartado: `retraction_minimum_travel` 1→3 (0 efecto), zig-zag y gyroid (peor que
grid+combinación), wall_loops 3 (+2 h, +80 g).
**Opción no aplicada:** relleno lightning → ~13 h 15 m y 462 g (−22 g/pieza ≈ −$4 MXN), pero
las dos caras de la pared de 6 mm quedan sin amarre entre sí (se pueden sentir flexionar al
apretar). Banda a 0.20 en vez de 0.16: −26 min más.
Respaldo previo: `.v5.bak` (el del 10-07 con la base 0.80 parchada). Falta imprimir y confirmar.
