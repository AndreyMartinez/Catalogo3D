---
name: optimizar-pieza
description: Optimiza una pieza ya en el catálogo (tarjeta de catalog3d.py) a partir de feedback del usuario — calidad de acabado, peso/costo, grosor de pared, defectos de curvas/bordes. Úsalo cuando el usuario pegue una tarjeta del catálogo o mencione el nombre de un diseño y pida "mejorar calidad", "reducir peso/gramaje/costo", "engrosar/adelgazar paredes", "arreglar acabado en bordes/curvas", o pregunte por costos de producción. Mantiene un registro por pieza para no repetir diagnóstico ni perder decisiones entre sesiones.
---

# Optimizar una pieza del catálogo

Flujo para atender feedback tipo "a este diseño hazlo más grueso/liviano/barato/mejor
acabado" sobre una pieza que el usuario ya tiene en su catálogo (`catalog3d.py`), casi
siempre pegando la tarjeta como imagen. Este skill junta lo aprendido optimizando
varias piezas reales (portacontroles, portacepillos) para no repetir los mismos
tropiezos.

## Contexto de mercado

Antes de proponer cambios, revisa en `.claude/mercado/estudio-de-mercado.md` cuánto vende la pieza y su categoría. Una pieza que vende mucho justifica optimizar tiempo de impresión para meterla a Full; una dormida no justifica una sesión larga. Cita el nivel de evidencia (medido / correlación / suposición) que trae el estudio.

## 0. Antes que nada: revisa el registro

Cada pieza tocada tiene (o debe tener) un archivo en
`.claude/optimizaciones/<slug>.md`. Si existe, LÉELO PRIMERO — ahí está qué ya se
intentó, qué funcionó, qué se dejó pendiente a propósito (ej. una esquina con defecto
que no se pudo arreglar sin dañar la malla) y qué le contestó el usuario la última vez
(gramaje real tras rebanar, si le gustó la sensación en mano, etc.). No vuelvas a
medir/diagnosticar algo que el registro ya resolvió; sí actualízalo al final de esta
sesión con lo nuevo.

Si no sabes el slug, revisa `.claude/optimizaciones/INDICE.md` — lista todas las
piezas ya registradas. Si no existe registro para esta pieza, es nueva para el
skill: créalo al terminar (paso 6) y agrégala también al índice.

## 1. Identifica el archivo real

La tarjeta trae nombre truncado, gramaje y costo. El archivo real vive en
`~/Desktop/own design 3d/**/*.3mf` — búscalo por nombre aproximado y confirma
haciendo match del gramaje contra `Metadata/slice_info.config` (`weight="..."`) dentro
del .3mf (es un zip). No asumas: dos diseños pueden llamarse parecido.

Determina el origen abriendo `3D/3dmodel.model` y mirando los `<metadata>`:
- Si dice `Application: BambuStudio-...` y trae `Designer`/`DesignModelId`/licencia:
  es un diseño **comprado/descargado** (MakerWorld u otro). Este skill aplica casi
  todo su peso a este caso — sigue con el resto del documento.
- Si en vez de eso reconoces que viene de `generadores/disenos.py` (una receta
  `DISENOS`): es nuestro generador paramétrico. Usa
  `python3 generadores/crear.py <clave> --param valor ...` para iterar (ver
  `generadores/crear.py --help`), y cuando quede bien, actualiza la receta en
  `disenos.py` y el snapshot `RECETAS` en `generadores/pruebas.py` (correr
  `python3 -m unittest pruebas` para confirmar que no se rompió nada más).

## 2. Entiende el costo real antes de tocar nada

El costo que muestra la tarjeta NO es solo material. Se arma así (ver
`catalog3d.py`, funciones `cuentas`/`costoMaterial`/`totalPaquete`):

```
costo total = peso_g/1000 × precio_kg   +   paquetería
```

`precio_kg` y los paquetes de paquetería viven en
`own design 3d/.catalogo3d_costos.json` (o el `.catalogo3d_costos.json` de la
subcarpeta si la pieza tiene uno propio). Antes de proponer nada, calcula cuánto pesa
cada componente del costo — a veces el ahorro más fácil y de cero riesgo está en la
paquetería (artículos que no aplican a esa pieza), no en el material. Si ves algo raro
ahí (ej. insumos de otro producto), pregúntalo, no lo asumas ni lo borres solo.

## 3. Diagnostica la malla con datos, no a ojo

Instala lo que falte (una vez por sesión basta): `pip3 install trimesh scipy
scikit-image rtree networkx lxml`.

**Grosor real de pared** (para "se ve delgado", "acabado feo en la curva", "que no
pierda lo grueso"): parsea el/los `3D/Objects/object_*.model` referenciados desde
`3D/3dmodel.model` (XML simple: `<vertices>`/`<triangles>`), arma un `trimesh.Trimesh`,
y por cada vértice lanza un rayo a lo largo de `-normal` para medir la distancia a la
pared opuesta. Los puntos con grosor bajo (usa ~1.2mm como umbral de alarma) te dicen
EXACTAMENTE dónde está el problema — no le subas `wall_loops` a ciegas: si el hueco de
malla ya es más angosto que lo que caben los loops configurados, no hay ajuste de
perfil de impresión que lo arregle (el perfil no puede meter más material del que la
geometría permite). Confírmalo así antes de tocar el perfil de slicer.

**Volumen "sólido equivalente"** (para estimar peso/costo antes de rebanar de verdad):
`mesh.volume` de cada pieza única × su escala de instancia × cuántas copias hay en el
plato = volumen si estuviera 100% sólida. Con el peso medido actual y el % de relleno
actual puedes despejar el volumen de "cascarón" (paredes+techos+piso, que NO cambia
con el relleno):

```
shell_vol = (peso_medido_g/densidad - infill% × V_solido) / (1 - infill%)
```//densidad PLA ≈ 1.24 g/cm³. Con eso puedes proyectar el peso a otro % de relleno o
a una geometría reescalada. **Siempre acláralo como estimado** — solo Bambu Studio
rebanando de verdad da el número real.

## 4. Arregla lo que haga falta

### 4a. Engrosar una zona delgada (sin dañar la malla)

**Deja margen de sobra, no el mínimo justo.** Un `target` apenas un poco por encima
de lo que caben 2 perímetros (ej. 1.4mm cuando 2 perímetros ocupan ~0.87mm) se
imprimió real y salió con un acabado "peludo/serrado" en la curva — muy poco margen
para una geometría curva compleja, y con `detect_thin_wall` activado el slicer
trazaba ahí líneas delgadas sueltas en vez de una pared sólida. Usa un `target` con
margen generoso (~2.0mm, el doble del ancho de 2 perímetros) y, si ya no hace falta,
**desactiva `detect_thin_wall`** — es sospechoso de producir toolpaths erráticos
justo en la franja límite que arreglaste. Si el usuario tiene forma de imprimir
físicamente la pieza, un defecto de acabado real solo se confirma con la foto del
resultado, no con la verificación geométrica sola (que solo garantiza que la malla
no está dañada, no que el slicer la trate bien).

Para los vértices bajo el umbral: `need = target - grosor_actual`, empuja cada lado
`need/2` a lo largo de su propia normal (así ambos lados de la pared crecen hacia
afuera simétricamente). Suaviza la transición para no dejar un pliegue visible, pero
**sin aplastar el pico** — usa algo tipo:
```python
smoothed = half.copy()
for _ in range(6):
    nb_avg = promedio_de_vecinos(smoothed)
    smoothed = max(half, 0.5*smoothed + 0.5*nb_avg)   # nunca por debajo de lo necesario
```
Después de aplicar (`vertice_nuevo = vertice + smoothed·normal`), **verifica siempre**:
`is_watertight`, `is_winding_consistent`, y que ninguna cara haya invertido su normal
(`dot(normal_antes, normal_despues) < 0` debe dar 0 caras). Si algo de eso falla —
pasó con una esquina donde un divisor se junta con la pared exterior en un pellizco
casi-cero—, **no lo fuerces**: restringe el arreglo espacialmente (por rango de
coordenadas) a la zona que sí se puede arreglar limpio, deja la otra sin tocar, y
repórtaselo al usuario como pendiente conocido en vez de entregar una malla dañada.

### 4b. Bajar peso sin perder grosor de pared
Si el usuario pide "más liviano pero que no pierda lo grueso": **no toques
`wall_loops`**. La única palanca segura es `sparse_infill_density` (y opcionalmente
`bottom_shell_layers`/`top_shell_layers` si sobran). Antes de prometer un ahorro
grande, revisa con el modelo del paso 3 cuánto volumen es realmente cascarón — en
piezas casi macizas (ej. un portacepillos con paredes de 4-5mm reales) el relleno
apenas pesa y bajar el % ahorra poco (~4-5%); en piezas más huecas sí hay margen real
(~15-20%). Sé honesto con la diferencia, no vendas lo mismo en los dos casos.

Si además se puede achicar/reescalar una pieza secundaria (una bandeja, no la parte
que se agarra en mano) para bajar más costo sin tocar la sensación de peso del objeto
principal, es una palanca legítima — confírmalo con el usuario si toca proporciones,
no solo tamaño absoluto.

### 4c. Mejorar calidad de acabado
Perfil típico que subió calidad sin subir peso (el relleno/paredes no cambian):
`layer_height` 0.2→0.12, `top_shell_layers` y `bottom_shell_layers` súbelos en la
misma proporción en que baja `layer_height` (mismo grosor sólido en mm, más capas),
`ironing_type` → `"top surface"`, `detect_thin_wall` → `"1"`.

## 5. Escribe el archivo — los dos tropiezos que ya no debes repetir

**Backup siempre primero**: si no existe `<archivo>.3mf.bak`, cópialo antes de tocar
nada.

**Tropiezo #1 — el perfil de impresión se revierte solo.** `Metadata/project_settings.config`
es JSON. Cambiar una clave (`wall_loops`, `layer_height`, `sparse_infill_density`,
etc.) NO BASTA: Bambu Studio guarda `different_settings_to_system` (3 strings, la
primera para ajustes de impresión, separados por `;`) y al abrir el proyecto
**resuelve desde el preset del sistema cualquier clave que no esté en esa lista**,
pisando tu cambio sin avisar. Siempre agrega cada clave que toques a esa lista
(primer elemento del array).

**Tropiezo #2 — reescalar el objeto equivocado.** Para achicar/agrandar/estirar una
pieza (cambiar sus proporciones), el transform que de verdad usa Bambu Studio para
rebanar es `<item objectid="X" transform="...">` dentro de **`3D/3dmodel.model`**
(sección `<build>`, spec estándar de 3MF). El `<assemble_item transform="...">` de
`Metadata/model_settings.config` es solo metadata de la vista "Ensamblar" de Bambu —
tocar solo ese no cambia nada al rebanar. El transform son 12 números (matriz 3×3 +
traslación); para escalar en X/Y/Z sin rotar, multiplica las posiciones diagonales
(índices 0, 4, 8) por tu factor y deja la traslación (índices 9,10,11) intacta.

**Tropiezo #3 — reescalar en Z sin recalcular la traslación Z.** Si cambias el factor
de escala Z de un objeto (por ejemplo para hacerlo "un poco más alto/bajo"), la
traslación Z del transform casi siempre estaba calibrada para que la base de la malla
quedara exactamente en el plato (mundo Z=0) CON LA ESCALA VIEJA. Si solo tocas el
factor de escala y dejas la traslación igual, la base ya no cae en Z=0: si subiste el
factor Z, la pieza se hunde bajo el plato y la impresora le corta la base entera (se
ve como "sin fondo" en la vista previa — así se descubrió este bug); si lo bajaste,
queda flotando sobre el plato. **Cada vez que cambies un factor de escala Z, recalcula
la traslación Z** con el mínimo local en Z de la malla sin escalar (`mesh.bounds[0,2]`,
world_z_base debe dar 0):
```python
nueva_tz = -nuevo_factor_z * z_min_local_sin_escalar
```
Verifícalo después releyendo el transform: `factor_z * z_min_local + tz` debe dar
`0.0` para cada objeto que reescalaste en Z.

**Tropiezo #4 — `repr()`/`%r` sobre un escalar de numpy, no un float de Python.**
Al escribir coordenadas de vértices al XML, `"%r" % valor_numpy` (o `repr(valor_numpy)`)
en numpy 2.x produce literalmente el texto `"np.float64(-4.68915...)"`, no el número
— corrompe el XML de la malla en silencio (el zip se escribe bien, `testzip()` no
lo detecta, solo se nota al re-parsear el mesh). Siempre convierte con `float(x)`
antes de formatear cualquier coordenada que venga de un array de numpy.

**Tropiezo #5 — agregar/quitar copias sin sincronizar `Metadata/model_settings.config`.**
Cuando se agregan o quitan objetos del `<build>` en `3D/3dmodel.model` (para cambiar
cuántas copias hay en el plato), Bambu Studio también valida
`Metadata/model_settings.config`: sus bloques `<object id="X">`, la lista
`<plate><model_instance>` y `<assemble><assemble_item>` tienen que listar
EXACTAMENTE los mismos ids que `3dmodel.model` — ni de más ni de menos. Si
`model_settings.config` referencia un id que ya no existe (o le falta uno que sí
existe), Bambu Studio puede fallar directamente al abrir el archivo. Cada vez que
cambies la cantidad de copias, recorta/agrega también esos tres bloques en
`model_settings.config` para que los ids coincidan uno a uno con `3dmodel.model`,
y de paso revisa `Metadata/cut_information.xml` (mismo patrón, menos crítico pero
igual de fácil de sincronizar). Verifícalo comparando los sets de ids extraídos de
ambos archivos antes de dar el cambio por terminado.

**Después de escribir el zip, verifica antes de avisar que quedó listo:**
```python
z = zipfile.ZipFile(ruta)
assert z.testzip() is None                       # zip no corrupto
# re-parsea el/los .model tocados y confirma is_watertight / is_winding_consistent
# re-parsea project_settings.config y confirma que los valores nuevos están Y que
# quedaron en different_settings_to_system
```

Reabre con `open -a "BambuStudio" "<ruta>"` y pide al usuario que le dé **Rebanar** —
el gramaje que trae el archivo es el de la rebanada vieja hasta que él lo vuelva a
rebanar. No inventes un número final; da el estimado del paso 3 como aproximación y
pide el real.

## 6. Antes de cerrar: actualiza el registro

Escribe/actualiza `.claude/optimizaciones/<slug>.md` (usa el nombre de carpeta o
archivo del diseño como slug) con este formato:

```markdown
# <nombre de la pieza>

Archivo: `own design 3d/.../archivo.3mf`
Origen: comprado (Designer: X) | generador propio (clave: Y)

## Feedback recibido
- <fecha> — <qué pidió el usuario, textual o resumido>

## Diagnóstico
- Grosor real medido: <dónde, cuánto>
- Costo real: material $X + paquetería $Y = $Z (precio_kg=..., paquete=...)
- Volumen sólido-equivalente: ...cm³, shell_vol implícito: ...cm³ (...% del total)

## Cambios aplicados
- <fecha>: <qué se cambió, valores antes→después, estimado de resultado>

## Resultado real (cuando el usuario lo confirma tras Rebanar)
- <fecha>: dice <N> g reales (estimado era <M> g)

## Pendiente / conocido y no resuelto
- <ej. esquina superior con pellizco de 0.01mm, riesgoso de arreglar sin dañar malla>
- <ej. paquetería con ítems que parecen de otro producto, sin confirmar con el usuario>
```

Esto es lo que evita perder el hilo: la próxima vez que el usuario mencione esta
pieza (en esta sesión o en una nueva), lee este archivo antes de volver a medir o
preguntar lo mismo.
