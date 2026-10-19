# Requisitos — Pestaña «Idea»

## Introducción

La pestaña «Crear» ya materializa piezas: el motor de `generadores/nucleo/`
construye contorno + acabado + perfil + divisores + base a partir de un
diccionario de ~30 parámetros, y de ahí salen el `.3mf`, el `.stl` y la
miniatura. Lo que falta no es geometría, es **la entrada**: hoy hay que saber
qué deslizador mover.

La pestaña «Idea» agrega el traductor que falta. El usuario describe la pieza
en español —o suelta una imagen con la silueta que quiere— y el sistema
devuelve un juego de valores para el motor de siempre. **En ningún caso se
genera una malla suelta.** Lo que se produce son valores que entran por
`disenos.normalizar()`, con lo cual la pieza hereda todas las garantías que ya
tiene la línea: pared de espesor controlado, relieve recortado a lo que la
pared aguanta, filete de fondo cortado a 45°, aviso de voladizos. Una idea mal
interpretada produce una pieza fea, nunca una pieza no imprimible.

El resultado nunca se guarda solo: abre la pestaña «Crear» con los
deslizadores ya puestos, la vista previa en vivo, el peso y el costo. La idea
propone el punto de arranque; el usuario conserva el ajuste fino y la decisión
de guardar.

Son tres vías de entrada hacia el mismo destino:

1. **Texto con modelo** — descripción libre → JSON de parámetros, vía la API
   de Claude llamada con `urllib` (sin instalar nada; sólo hace falta que el
   usuario tenga una API key).
2. **Texto sin red** — intérprete de palabras clave en español, escrito a
   mano contra `disenos.PARAMETROS`. Es el respaldo cuando no hay API key o
   la red falla, y también la opción para quien no quiera usar red nunca.
3. **Imagen** — un PNG del que se extrae la silueta y se registra como
   contorno «trazado» del motor, una función `t → (x, y)` más en la tabla de
   `nucleo/contornos.py`.

Restricción que manda sobre todo lo demás: **sólo librería estándar de
Python 3**. Sin dependencias nuevas, ni para el HTTP ni para la imagen.

## Requisitos

### Requisito 1 — Describir la pieza con palabras

**Historia:** Como alguien que quiere una pieza pero no conoce los parámetros
del motor, quiero escribir lo que necesito en español, para llegar a una vista
previa concreta sin tener que aprenderme treinta deslizadores.

#### Criterios de aceptación

1. CUANDO el usuario abre la pestaña «Idea» ENTONCES el sistema DEBERÁ mostrar
   un campo de texto libre, la elección de qué producto de `DISENOS` usar como
   base (o «que lo decida la idea»), y un botón para interpretar.
2. CUANDO el usuario envía una descripción no vacía ENTONCES el sistema DEBERÁ
   devolver un juego completo de parámetros del motor y mostrar la vista previa
   renderizada junto al peso en gramos y el costo estimado.
3. CUANDO el sistema devuelve los parámetros interpretados ENTONCES DEBERÁ
   mostrar, en lenguaje llano, qué entendió de la descripción y qué valores
   asignó por eso, de modo que el usuario pueda ver dónde se equivocó la
   interpretación y no sólo el resultado.
4. CUANDO el usuario envía un texto vacío o sólo con espacios ENTONCES el
   sistema DEBERÁ pedir una descripción sin llamar a la red.
5. SI la descripción no menciona un parámetro ENTONCES el sistema DEBERÁ dejar
   el valor de la receta base elegida, y NO DEBERÁ inventar un valor extremo.

### Requisito 2 — Interpretación con el modelo

**Historia:** Como usuario que sí tiene API key, quiero que un modelo lea mi
descripción, para que entienda frases que ningún diccionario de palabras clave
va a cubrir.

#### Criterios de aceptación

1. CUANDO hay una API key disponible ENTONCES el sistema DEBERÁ llamar a la
   API de Claude usando únicamente `urllib.request`, sin dependencias externas.
2. CUANDO el sistema arma la petición ENTONCES DEBERÁ incluir la declaración
   viva de `disenos.PARAMETROS` —claves, rangos, opciones válidas y textos de
   ayuda— generada desde el código y no copiada a mano, de modo que un
   parámetro nuevo quede disponible sin tocar el prompt.
3. CUANDO el modelo responde ENTONCES el sistema DEBERÁ aceptar únicamente
   claves declaradas en `PARAMETROS`, descartar en silencio las que no existan,
   y pasar el resto por `disenos.normalizar()` antes de construir nada.
4. SI el modelo devuelve un valor fuera de rango ENTONCES `normalizar()` DEBERÁ
   recortarlo a su rango y el sistema DEBERÁ seguir adelante, no fallar.
5. SI la respuesta no es JSON válido ENTONCES el sistema DEBERÁ reintentar una
   vez y, si vuelve a fallar, caer al intérprete sin red avisando al usuario.
6. CUANDO la llamada tarda más de un tiempo límite razonable ENTONCES el
   sistema DEBERÁ abandonarla y caer al intérprete sin red en vez de dejar la
   interfaz colgada.
7. La API key NUNCA DEBERÁ quedar escrita en el repositorio ni en los archivos
   generados; el sistema DEBERÁ leerla del entorno (`ANTHROPIC_API_KEY`) o de
   un archivo de configuración local ya ignorado por git.
8. CUANDO no hay API key ENTONCES el sistema DEBERÁ decirlo con claridad, usar
   el intérprete sin red, y seguir siendo plenamente utilizable.

### Requisito 3 — Interpretación sin red

**Historia:** Como usuario sin API key —o sin ganas de mandar nada a internet—
quiero que el campo de texto siga sirviendo, para no depender de un servicio
externo para usar mi propio catálogo.

#### Criterios de aceptación

1. CUANDO se usa el intérprete sin red ENTONCES el sistema DEBERÁ reconocer,
   como mínimo: el producto base por su nombre, los ocho contornos y los diez
   acabados por su etiqueta en español, tamaños relativos («alto», «bajo»,
   «ancho», «chico», «grande»), medidas explícitas en milímetros o
   centímetros, cantidad de divisiones («tres ranuras», «dos filas»), la
   presencia de drenaje y la presencia de bandeja.
2. CUANDO el texto trae una medida explícita ENTONCES esa medida DEBERÁ ganarle
   al adjetivo relativo que aparezca en la misma frase.
3. CUANDO el intérprete no reconoce ninguna palabra ENTONCES el sistema DEBERÁ
   devolver la receta base sin cambios y decir que no entendió nada, en vez de
   devolver algo aleatorio.
4. CUANDO el intérprete termina ENTONCES DEBERÁ reportar qué palabras usó, en
   el mismo formato de explicación que el requisito 1.3.
5. El intérprete NUNCA DEBERÁ abrir una conexión de red.

### Requisito 4 — La silueta desde una imagen

**Historia:** Como usuario con un logo, una hoja escaneada o un boceto,
quiero que esa silueta sea la planta de la pieza, para obtener una forma que
no está en los ocho contornos del motor.

#### Criterios de aceptación

1. CUANDO el usuario sube un PNG ENTONCES el sistema DEBERÁ decodificarlo con
   `zlib` y la librería estándar, sin dependencias externas.
2. CUANDO se extrae la silueta ENTONCES el sistema DEBERÁ separar figura de
   fondo, quedarse con la región conexa más grande, trazar su borde exterior,
   suavizarlo y remuestrearlo a una cantidad fija de puntos.
3. CUANDO la silueta queda trazada ENTONCES el sistema DEBERÁ registrarla como
   contorno «trazado», con la misma firma `t → (x, y)` que los demás, y DEBERÁ
   recentrarla y estirarla para llenar exactamente el ancho y el fondo pedidos,
   igual que hacen los ocho contornos existentes.
4. SI la silueta resultante no es estrellada respecto de su centro ENTONCES el
   sistema DEBERÁ avisar que el fondo puede salir mal, porque el cierre en
   abanico del piso depende de esa propiedad.
5. SI la imagen no es PNG ENTONCES el sistema DEBERÁ decirlo explícitamente y
   nombrar el formato aceptado, en vez de fallar con un error técnico.
6. SI la imagen no tiene una figura distinguible del fondo —toda de un color,
   o demasiado ruidosa— ENTONCES el sistema DEBERÁ decirlo y dejar la planta
   como estaba.
7. CUANDO el usuario sube una imagen ENTONCES ésta NUNCA DEBERÁ salir de la
   máquina: el trazado DEBERÁ ocurrir localmente aunque haya API key.
8. CUANDO hay a la vez texto e imagen ENTONCES la imagen DEBERÁ mandar sobre la
   planta y el texto sobre todo lo demás.

### Requisito 5 — De la idea al ajuste fino

**Historia:** Como usuario que ya vio la propuesta, quiero corregirla con los
mismos deslizadores de siempre, para que una interpretación imperfecta sea el
principio del trabajo y no un callejón sin salida.

#### Criterios de aceptación

1. CUANDO el sistema devuelve una interpretación ENTONCES DEBERÁ poder pasarse
   a la pestaña «Crear» con todos los deslizadores ya en los valores
   propuestos.
2. CUANDO los valores llegan a «Crear» ENTONCES la vista previa, el giro, la
   elevación, el peso, el costo y el guardado DEBERÁN funcionar exactamente
   igual que para una receta de `DISENOS`, sin ninguna ruta especial.
3. CUANDO la planta viene de una imagen ENTONCES el contorno «trazado» DEBERÁ
   sobrevivir el paso a «Crear» y el guardado del `.3mf`.
4. CUANDO el usuario guarda una pieza nacida de una idea ENTONCES el sistema
   DEBERÁ proponer un nombre derivado de su descripción, y DEBERÁ dejar el
   `.3mf`, el `.stl` y la miniatura como lo hace hoy `crear.py`.
5. CUANDO el usuario vuelve a interpretar una idea nueva ENTONCES los cambios
   manuales que hizo antes DEBERÁN quedar reemplazados, y el sistema DEBERÁ
   advertirlo antes de descartarlos.

### Requisito 6 — Que no se rompa lo que ya funciona

**Historia:** Como dueño de un catálogo que ya uso todos los días, quiero que
la pestaña nueva no toque lo existente, para no cambiar una función por otra.

#### Criterios de aceptación

1. El sistema NUNCA DEBERÁ requerir una dependencia fuera de la librería
   estándar de Python 3, ni siquiera para la vía con modelo.
2. CUANDO el usuario no usa la pestaña «Idea» ENTONCES el catálogo DEBERÁ
   arrancar, funcionar y guardar exactamente como hoy, sin API key ni red.
3. CUANDO se agrega el contorno «trazado» ENTONCES los ocho contornos
   existentes DEBERÁN seguir dando la misma geometría que antes.
4. CUANDO el intérprete propone valores ENTONCES DEBERÁ respetar los avisos que
   ya emite el motor —voladizos, capas verticales insuficientes— y mostrarlos
   al usuario en vez de ocultarlos.
5. CUANDO se agregue un parámetro nuevo a `PARAMETROS` ENTONCES las tres vías
   DEBERÁN reconocerlo sin editar el prompt ni el intérprete, salvo por las
   palabras clave en español que quieran asociársele.
