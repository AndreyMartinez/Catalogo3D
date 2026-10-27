# Plan de implementación — Publicador MercadoLibre → Amazon México

El orden persigue una cosa: **llegar pronto a una vista previa real del Olas
sin poder publicar nada por accidente**. Primero va el cliente de SP-API con
sus candados (credenciales, secretos tapados), probado sin red y luego con
una sola lectura. Después, `borrador.py` como funciones puras con su prueba.
Al final, los comandos, en el orden en que se usan, y `publicar` al último,
cuando ya existen `validar` y `comparar` y se puede probar que sin
`--confirmo` no sale nada.

Todo vive en `.claude/skills/publicar-amazon/`. Las pruebas sin red van en
`scripts/prueba_publicar.py` (`unittest`, como
`colecta-full/scripts/prueba_traer_datos.py`) y crecen con cada tarea.

- [x] 1. Esqueleto del skill y cliente de SP-API
  - [x] 1.1 `sp_api.py`: credenciales y candados
    - `cargar_credenciales()` con los mensajes del Req. 1.3, el rechazo de
      permisos ≠ 600 (Req. 1.4) y `_tapar()` para quitar secretos de
      cualquier texto (Req. 1.5).
    - Prueba: un archivo con 644 en una carpeta temporal se rechaza; un
      archivo que falta da el mensaje con los cuatro campos; `_tapar()`
      borra un secreto metido en un mensaje de error.
    - _Requisitos: 1.1, 1.3, 1.4, 1.5_
  - [x] 1.2 `sp_api.py`: token y peticiones
    - `_access_token()` solo en memoria con renovación; `pedir()` con
      `x-amz-access-token`, reintentos 429/5xx (1-2-4-8-16 s), una
      renovación con 401/403 y 0.25 s entre llamadas. `ErrorSP` siempre
      pasa por `_tapar()`.
    - Prueba sin red: con `urlopen` sustituido, un 429 seguido de 200
      reintenta y devuelve; seis 429 seguidos (cinco reintentos) dan `ErrorSP`; el mensaje no trae
      ningún valor de las credenciales.
    - Prueba en vivo, de solo lectura: `pedir("GET",
      "/listings/2021-08-01/items/{seller}", …)` lista el Olas
      (`5Z-W3LH-N087`).
    - _Requisitos: 1.1, 1.2, 1.6, 8.5_

- [x] 2. Esquema de Amazon (`esquema.py`)
  - [x] 2.1 Buscar tipo y cachear esquema
    - `buscar_tipos()`, `esquema(tipo)` con caché por
      `productTypeVersion` en `~/.catalogo3d/amazon/esquemas/` (carpeta
      700, archivos 600).
    - Prueba en vivo: `esquema("CADDY")` baja una vez y la segunda corrida
      usa la caché; los obligatorios coinciden con los leídos
      (`brand`, `bullet_point`, `country_of_origin`, `item_name`,
      `product_description`, `supplier_declared_dg_hz_regulation`).
    - _Requisitos: 5.1, 5.3, 5.5_
  - [x] 2.2 `revisar()`, `valor_mas_cercano()` y `atributo_exencion()`
    - Puras, sobre el esquema.
    - Prueba con un esquema mínimo escrito en la prueba: obligatorio
      faltante, `item_name` de 201 caracteres, valor fuera de enum; «PLA»
      resuelve contra una lista con «PLA» y «Plástico», y un caso ambiguo
      da `None`.
    - _Requisitos: 4.2, 5.3, 5.4_

- [x] 3. Del ítem de ML al borrador (`borrador.py`)
  - [x] 3.1 Reglas de texto
    - Limpieza de título, secciones de la descripción, viñetas,
      descripción y palabras clave; avisos de lo que se quitó y del kit.
    - Prueba con la ficha pública del Olas (título, descripción y
      atributos copiados a la prueba): sale «Organizador De Cubiertos Olas
      Negro» sin «Más Obsequios»; la sección de siembra, «¿Tienes dudas?» y
      «¿Necesitas factura?» no aparecen; los títulos reales de las
      variaciones («Más Regalos Sorpresa», «Mas Obsequio De Cultivo»)
      quedan limpios; una maceta no dispara el aviso de kit.
    - _Requisitos: 3.4, 4.1, 4.3_
  - [x] 3.2 Fotos, medidas, precio, SKU y atributos
    - `-O.jpg → https…-F.jpg`; medidas de artículo y paquete; peso y costo
      de los archivos del catálogo; `original_price` antes que `price`;
      SKU `SR-<clave>-<NOMBRE>-<COL>` sin choques, o el de
      `publicadas.json` si ya existe; marca `Generic` desde
      `categorias.json`; variaciones con su color y sus fotos; lista inicial
      de `por_revisar`.
    - Crear `categorias.json` con las 9 categorías, sus claves,
      `"marca": "Generic"` y MLM190943 → `CADDY` confirmado.
    - Prueba: el Olas da 5 fotos `-F` en orden y paquete 20×16×11 / 198 g;
      una variación hereda solo sus fotos; dos borradores con el mismo
      nombre reciben `-2`.
    - _Requisitos: 2.3, 3.1, 3.3, 3.5, 3.6, 6.1, 6.2, 7.3_
  - [x] 3.3 `payload()`, `huella()` y `cambios_en_ml()`
    - Expansión de valores simples con `language_tag` y `marketplace_id`
      según el esquema; oferta, `fulfillment_availability` (FBA y propio),
      imágenes, exención de GTIN, `supplier_declared_dg_hz_regulation`.
    - Prueba: la huella cambia al editar el título y no al reordenar
      claves; envío propio sin cantidad da error; FBA no lleva cantidad; el
      payload del Olas trae los seis obligatorios de `CADDY`.
    - _Requisitos: 3.2, 4.8, 7.1, 7.2, 8.3, 8.4_
  - [x] 3.4 `fotos_ok()`
    - `GET` con `Range`, tipo de contenido y medidas de JPEG o WebP.
    - Prueba sin red con los primeros bytes de un JPEG chico armado en la
      prueba; en vivo, la foto principal del Olas mide 1200 px.
    - _Requisitos: 4.5_

- [x] 4. Comandos de lectura y borrador (`publicar.py`)
  - [x] 4.1 `lista` y `armar`
    - Leer las activas con `ml_api` y `traer_datos` de `colecta-full`;
      guardar borradores sin pisar los editados y reportar cambios en ML;
      detenerse sin escribir nada si ML falla.
    - Prueba en vivo: `lista` muestra las activas (37 el 2026-10-27, 6 con variaciones);
      `armar MLM3674350731` crea el borrador con SKU `5Z-W3LH-N087`; editar
      el título y volver a correr `armar` no lo pisa.
    - _Requisitos: 2.1, 2.2, 2.4, 3.1, 3.2, 6.1_
  - [x] 4.2 `ver` y `aprobar`
    - Vista legible con las medidas juntas, `por_revisar`, avisos y
      hallazgos de `revisar()`; `aprobar` quita campos de `por_revisar`.
      JSON roto: archivo y línea, sin sobrescribir.
    - Prueba: `aprobar` de un campo que no existe avisa y no cambia nada.
    - _Requisitos: 3.6, 4.4_

- [ ] 5. Validar y comparar con el Olas
  - [ ] 5.1 `validar`
    - Revisión local; si pasa, PUT con `mode=VALIDATION_PREVIEW`,
      `includedData=issues,identifiers`, `issueLocale=es_MX`; guardar
      resultado y huella; reconocer el issue de exención de GTIN.
    - Prueba en vivo: `validar MLM3674350731` responde `VALID` o una lista
      de issues en español, y el Olas en Amazon no cambia (GET antes y
      después, mismo `lastUpdatedDate`).
    - _Requisitos: 4.8, 8.1, 8.2, 8.3, 8.4, 8.5, 10.1_
  - [ ] 5.2 `comparar` y `estado`
    - GET de solo lectura del SKU; tabla lado a lado contra el borrador;
      `estado` con ASIN, estado e issues, y el aviso de foto principal.
    - Prueba en vivo: `comparar MLM3674350731` muestra las diferencias
      conocidas (color Plateado/Negro, peso 450/105 g, paquete 500/198 g,
      6/3 compartimentos, «Obsequios» en el título).
    - _Requisitos: 4.6, 9.5, 10.2_

- [ ] 6. Publicar con `--confirmo`
  - `publicar`: candados del Req. 9.1; resumen y alto sin `--confirmo`;
    PUT si el SKU no existe; si existe, diferencia y PATCH solo de
    `--campos`, primero en `VALIDATION_PREVIEW`; registro en
    `publicadas.json`; pregunta en terminal interactiva.
  - Prueba sin red, con `sp_api.pedir` sustituido por una función que
    falla si se llama: sin `--confirmo`, con un SKU distinto, con
    `por_revisar` no vacío o con la huella vieja, no llama a la red.
  - Sin prueba en vivo de escritura: la primera publicación real la decide
    el usuario fuera de este plan.
  - _Requisitos: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 7. `SKILL.md` y `CLAUDE.md`
  - `SKILL.md` con el flujo `armar → redactar → ver → aprobar → validar →
    publicar`, la regla de no poner `--confirmo` sin el «sí» del usuario
    para esa publicación, y cómo crear `amazon_credenciales.json`.
  - Agregar `publicar-amazon` a la tabla de skills de `CLAUDE.md`.
  - Verificación de punta a punta: `python3 -m py_compile` de todos los
    scripts, `prueba_publicar.py` en verde y el recorrido del Olas
    (`armar` → `ver` → `validar` → `comparar`).
  - _Requisitos: todos_
