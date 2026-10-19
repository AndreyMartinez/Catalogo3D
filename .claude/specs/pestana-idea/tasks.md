# Plan de implementación — Pestaña «Idea»

El orden persigue una cosa: **que la vía sin red funcione de punta a punta en el
paso 5**, antes de escribir una línea de decodificador de PNG o de cliente HTTP.
A partir de ahí, cada bloque agrega una vía nueva sobre algo que ya se puede
probar a mano en el navegador.

El paso 1 va primero porque es la red de seguridad: sin la línea base grabada,
no hay forma de demostrar después que las piezas de siempre salen idénticas.

- [x] 1. Red de seguridad antes de tocar el motor
  - Crear `generadores/pruebas.py` con `unittest` de la librería estándar, que
    corra con `python3 -m unittest generadores.pruebas` sin red y sin API key.
  - Para cada receta de `DISENOS`, construir la malla con `cuerpo.construir()` y
    grabar en el propio archivo de pruebas el número de vértices, el número de
    triángulos y los gramos como valores esperados.
  - Correrlo y dejarlo en verde **antes** de cualquier otro cambio.
  - _Requisitos: 6.3_

- [x] 2. El parámetro `trazo` y la receta libre
  - [x] 2.1 Declarar el tipo de parámetro nuevo en `generadores/disenos.py`
    - Agregar el constructor `trazo(clave, etiqueta, grupo)` junto a `num` y
      `opcion`, con `tipo: "trazo"`, `valor: ""` y `depende: ["trazado"]`.
    - Agregar el parámetro `trazo` a `PARAMETROS`, en el grupo «Forma».
    - Agregar la rama de `tipo == "trazo"` a `normalizar()`: aceptar sólo cadenas
      base64 de hasta 4096 caracteres, validadas con expresión regular; cualquier
      otra cosa se descarta y queda la cadena vacía.
    - _Requisitos: 4.3, 6.5_
  - [x] 2.2 Agregar la receta `libre`
    - Cuarta entrada en `DISENOS`: clave `libre`, nombre «Pieza libre», carpeta
      «Ideas», `valores` vacío.
    - Verificar que la pestaña «Crear» la levanta sola, sin tocar
      `catalogo_generadores()` ni `generar_diseno()`.
    - _Requisitos: 1.1, 5.4_
  - [x] 2.3 Pruebas del parámetro
    - Que `normalizar()` rechace un base64 de 5000 caracteres, un valor que no
      sea cadena, y una cadena con caracteres fuera del alfabeto base64.
    - Volver a correr la prueba de línea base del paso 1: los ocho contornos y
      las tres recetas originales deben dar exactamente lo mismo.
    - _Requisitos: 6.3_

- [x] 3. El contorno trazado, con radios sintéticos
  - [x] 3.1 Codificar y decodificar en `generadores/nucleo/trazo.py`
    - `codificar(radios)` → `base64(zlib(b"T1" + 180 bytes))`, cuantizando cada
      radio a 0–255 como fracción del máximo.
    - `decodificar(cadena)` → lista de 180 flotantes, o `None` si la marca de
      versión no es `T1`, si el base64 no abre, o si `zlib` falla.
    - Nada de imágenes todavía: esta tarea trabaja con arreglos de radios.
    - _Requisitos: 4.3_
  - [x] 3.2 Registrar el contorno en `generadores/nucleo/contornos.py`
    - `trazado(p)`: decodifica `p["trazo"]`, interpola linealmente entre muestras
      y reescala para llenar exactamente `ancho` y `fondo`, igual que las otras
      plantas.
    - Con `trazo` vacío o corrupto, devolver el círculo.
    - Agregar la entrada `"trazado": ("Trazado de imagen", trazado)` a `CONTORNOS`.
    - Cerrar el pendiente de la 2.1: agregarle `depende=["trazado"]` al
      parámetro `trazo`, que hasta aquí no podía apuntar a nada.
    - _Requisitos: 4.3, 6.4_
  - [x] 3.3 Pruebas del contorno
    - Radios constantes → un círculo, comparado contra `circulo(p)` dentro del 1%.
    - Radios de una elipse → la razón de semiejes sale a menos del 3%.
    - `trazo` vacío y `trazo` corrupto → el círculo, sin lanzar.
    - Que la malla completa se construya con `contorno="trazado"` y salga cerrada.
    - _Requisitos: 4.3, 6.4_

- [ ] 4. El intérprete sin red
  - [ ] 4.1 Escribir `generadores/idea/palabras.py`
    - Tabla de reglas construida en tiempo de ejecución desde `CONTORNOS`,
      `ACABADOS` y `PERFILES`, más los sinónimos escritos a mano (piedra →
      guijarro, tela → lino, cañas → junco).
    - Medidas explícitas con `(\d+(?:[.,]\d+)?)\s*(mm|cm)` asociadas al
      sustantivo más cercano de {alto, ancho, fondo, diámetro}.
    - Adjetivos relativos como factor sobre la receta base, aplicados **antes**
      que las medidas explícitas para que éstas ganen.
    - Conteos del uno al ocho, en dígito y en letra; presencias de drenaje,
      bandeja y divisiones.
    - Devolver la lista de ajustes con su `porque`, nunca un diccionario pelado.
    - _Requisitos: 3.1, 3.2, 3.4, 3.5_
  - [ ] 4.2 Escribir el orquestador `generadores/idea/__init__.py`
    - `interpretar(texto, receta, png_bytes=None)` con la forma de retorno del
      diseño: `ok`, `clave`, `valores`, `nombre`, `via`, `explicacion`, `avisos`.
    - Por ahora sólo la vía `palabras`; los ganchos de imagen y modelo quedan
      declarados pero sin implementar.
    - Nunca lanzar: devolver `ok: False` con mensaje en español.
    - Pasar siempre por `disenos.normalizar()` antes de devolver.
    - Traducir «no reconocí nada» al mensaje de R3.3.
    - _Requisitos: 1.5, 3.3, 3.4_
  - [ ] 4.3 Pruebas del intérprete
    - Tabla de frase → clave/valor esperado, cubriendo cada familia de regla.
    - El caso de R3.2: «un vaso alto de 60 mm» da 60, no el factor de «alto».
    - El caso de R3.3: texto sin nada reconocible devuelve la receta intacta.
    - Que ningún camino de `palabras.py` importe `urllib` ni abra un socket.
    - _Requisitos: 3.1, 3.2, 3.3, 3.5_

- [ ] 5. Primera vuelta completa en el navegador
  - [ ] 5.1 Agregar el endpoint en `catalog3d.py`
    - `POST /api/idea` en la lista blanca de `do_POST`, bajo el mismo guardia de
      `HAY_GENERADORES` que usan `/api/vista` y `/api/crear`.
    - Rechazar texto vacío o de sólo espacios antes de hacer nada.
    - _Requisitos: 1.2, 1.4_
  - [ ] 5.2 Agregar la pestaña «Idea» a la interfaz
    - Botón de pestaña, `textarea`, selector de receta base con la opción «que lo
      decida la idea», y botón de interpretar.
    - Pintar la lista de `explicacion` con etiqueta legible y el `porque`, y los
      `avisos` con el mismo estilo de aviso que ya usa «Crear».
    - Botón «Ajustar en Crear» que copia a `crValores`, llama a
      `dibujarControles()` y `pedirVista()`, y cambia de pestaña.
    - Hacer que `dibujarControles()` salte los parámetros de `tipo === 'trazo'`.
    - _Requisitos: 1.1, 1.2, 1.3, 5.1, 5.2_
  - [ ] 5.3 Probar a mano de punta a punta
    - Escribir una descripción, ver la vista previa, ajustar un deslizador,
      guardar, y confirmar que aparecen el `.3mf`, el `.stl` y la miniatura en la
      subcarpeta que toca.
    - Confirmar que el catálogo sigue arrancando y guardando igual sin usar la
      pestaña nueva.
    - _Requisitos: 5.2, 5.4, 6.2_

- [ ] 6. Leer un PNG
  - [ ] 6.1 Escribir `generadores/nucleo/imagen.py`
    - Verificar la firma en los bytes, no la extensión.
    - Soportar profundidad de 8 bits y tipos de color 0, 2, 3, 4 y 6; con 16 bits,
      quedarse con el byte alto.
    - Implementar los cinco filtros por fila: `None`, `Sub`, `Up`, `Average` y
      `Paeth`.
    - Rechazar el entrelazado Adam7 con un mensaje que diga cómo volver a
      guardar la imagen, y lo que no sea PNG nombrando el formato aceptado.
    - Topes: 8 MB de archivo y 4000 px de lado.
    - Devolver luminancia y alfa por píxel, ya escalado a 512 px de lado mayor.
    - _Requisitos: 4.1, 4.5_
  - [ ] 6.2 Pruebas del decodificador
    - Sintetizar las imágenes con `render.escribir_png()`, que ya existe: cero
      binarios en el repositorio.
    - Un caso por tipo de color y uno por filtro de fila. El de `Paeth` importa
      más que los otros: mal implementado da una imagen que se ve casi bien.
    - Casos de rechazo: JPEG, PNG entrelazado, archivo de más de 8 MB.
    - _Requisitos: 4.1, 4.5_

- [ ] 7. De la imagen a la silueta
  - [ ] 7.1 Completar el trazado en `generadores/nucleo/trazo.py`
    - Separar figura de fondo: si hay alfa, manda el alfa; si no, umbral de Otsu
      sobre luminancia con el fondo decidido por mayoría de las cuatro esquinas.
    - Componente conexa mayor por relleno de inundación **iterativo** con
      `deque` — nunca recursivo, que una silueta de 512 px desborda la pila.
    - Centroide, 180 rayos, y por cada ángulo el último píxel de dentro.
    - Suavizado por media móvil **circular** de ventana 5.
    - Comparar el área del borde trazado contra el área de la versión radial y
      emitir el aviso de entrantes si la diferencia pasa del 5%.
    - Avisar y no trazar cuando no hay figura distinguible del fondo.
    - _Requisitos: 4.2, 4.4, 4.6_
  - [ ] 7.2 Pruebas del trazado
    - Círculo negro sobre blanco → los 180 radios dentro del 2% entre sí.
    - Elipse → la razón de semiejes a menos del 3%.
    - Cuadrado → las esquinas dan √2 veces el radio de los lados.
    - Una luna o una C → dispara el aviso de entrantes.
    - Imagen de un solo color → el aviso de R4.6, sin trazo.
    - Dos manchas separadas → se queda con la mayor.
    - _Requisitos: 4.2, 4.4, 4.6_

- [ ] 8. La imagen dentro de la pestaña
  - [ ] 8.1 Conectar la imagen al orquestador
    - `interpretar()` acepta los bytes del PNG, traza, y fija `contorno="trazado"`,
      `trazo`, y `ancho`/`fondo` en la proporción de la silueta.
    - Aplicar la precedencia de R4.8: la imagen manda sobre la planta, el texto
      sobre todo lo demás.
    - Memoizar el trazo por hash SHA-256 de los bytes, con tope de 8 entradas.
    - _Requisitos: 4.7, 4.8_
  - [ ] 8.2 Subir la imagen desde el navegador
    - `input file` que lee el PNG con `FileReader` como data URL y lo manda en el
      JSON de `/api/idea`; rechazar arriba de 8 MB antes de mandarlo.
    - Mostrar la miniatura de la silueta trazada, con un botón para quitarla que
      devuelve el contorno a `circulo`.
    - _Requisitos: 4.1, 4.5, 4.6_
  - [ ] 8.3 Probar a mano que el trazo sobrevive
    - Con una silueta cargada: ver la vista previa, cambiar de pestaña a «Crear»,
      recargar la página, guardar, y abrir el `.3mf` resultante.
    - _Requisitos: 5.3_

- [ ] 9. La vía con modelo
  - [ ] 9.1 Generar el esquema en `generadores/idea/esquema.py`
    - `catalogo()`: el texto del sistema con clave, etiqueta, rango u opciones y
      el texto de `ayuda` de cada entrada de `PARAMETROS`, generado en tiempo de
      ejecución.
    - `json_schema()`: el esquema de salida con `receta`, `nombre` y la lista de
      `ajustes` de `{clave, valor, porque}`, con `valor` siempre cadena.
    - _Requisitos: 2.2, 6.5_
  - [ ] 9.2 Escribir el cliente en `generadores/idea/modelo.py`
    - `POST https://api.anthropic.com/v1/messages` con `urllib.request`, con las
      cabeceras `x-api-key`, `anthropic-version: 2023-06-01` y `content-type`.
    - Cuerpo: modelo `claude-opus-5`, `max_tokens` 2000, `output_config` con
      `effort: "low"` y el `format` de `json_schema`, y `cache_control` efímero
      sobre el catálogo del sistema.
    - Tiempo límite de 20 segundos; un reintento en 429, 5xx, tiempo agotado y
      JSON inválido; nada de reintento en `URLError` ni en 401.
    - Tratar `stop_reason: "refusal"` como respuesta vacía.
    - Leer la clave de `ANTHROPIC_API_KEY` y, si no está, de
      `~/.catalog3d/config.json` con permisos 600.
    - El transporte se **inyecta**, para poder probar sin red.
    - _Requisitos: 2.1, 2.5, 2.6, 2.7_
  - [ ] 9.3 Pruebas del cliente, sin tocar la red
    - Que `json_schema()` salga válido para todo `PARAMETROS`.
    - Con un transporte de mentira: respuesta buena, JSON truncado, clave
      inventada, valor fuera de rango, `refusal`, 401, 429 y tiempo agotado.
    - Que la clave inventada se descarte en silencio y que el valor fuera de
      rango lo recorte `normalizar()`.
    - _Requisitos: 2.3, 2.4, 2.5_

- [ ] 10. Enganchar el modelo y cerrar
  - [ ] 10.1 Encadenar las dos vías en el orquestador
    - Si hay clave, `modelo`; si falla por cualquier motivo, `palabras` con el
      aviso de por qué se cayó. `via` dice cuál ganó.
    - _Requisitos: 2.5, 2.8_
  - [ ] 10.2 Estado y aviso en la interfaz
    - `GET /api/idea/estado` devuelve sólo si hay clave y por qué no, nunca la
      clave.
    - La pestaña muestra qué vía se usó y, sin clave, lo dice sin estorbar.
    - _Requisitos: 2.7, 2.8_
  - [ ] 10.3 Proteger los ajustes manuales
    - Bandera `crTocado`, que se prende con el `input` de cualquier control y se
      apaga al poblar desde una idea; con la bandera prendida, interpretar de
      nuevo pide confirmación.
    - _Requisitos: 5.5_
  - [ ] 10.4 El nombre de la pieza
    - Derivar el nombre propuesto de la descripción, limpiando lo que no sirve
      para un nombre de archivo, con el nombre sugerido de siempre como respaldo.
    - _Requisitos: 5.4_
  - [ ] 10.5 Cerrar con las pruebas completas y el README
    - Correr `python3 -m unittest generadores.pruebas` en frío, sin red y sin API
      key, y dejarlo en verde.
    - Volver a correr la línea base del paso 1: las tres recetas originales dan
      exactamente lo mismo que antes de todo esto.
    - Agregar al `README.md` la sección de la pestaña «Idea» y la línea de dónde
      va la API key, en el tono del resto del documento.
    - _Requisitos: 6.1, 6.2, 6.3, 6.4_
