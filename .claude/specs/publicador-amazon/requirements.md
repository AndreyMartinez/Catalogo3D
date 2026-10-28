# Requisitos — Publicador MercadoLibre → Amazon México

## Introducción

Savia Raíz tiene 40 publicaciones activas en MercadoLibre México y acaba de
abrir Amazon México. La primera, el Portacubiertos Olas (MLM3674350731), se
capturó a mano en Seller Central a partir de una ficha armada en el chat
(`~/Downloads/Amazon - Portacubiertos Olas/FICHA_AMAZON.txt`). Hacer eso 39
veces más no escala, y lo que se ajustó a mano en esa ficha es justo lo que
falta automatizar: título sin «obsequio», viñetas que ML no tiene, foto
principal elegida aparte, medidas que en ML estaban mal, kit de siembra
fuera, precio pensado para Amazon. (Amazon aceptó la foto principal del Olas
aunque no tenía fondo blanco puro: la regla existe, pero no bloqueó la
publicación.)

Esta función es un script de línea de comandos que lee las publicaciones
activas de ML, arma para cada una un **borrador** de publicación de Amazon,
lo valida contra Amazon con la Selling Partner API (SP-API) en modo vista
previa, y solo publica de verdad lo que el usuario apruebe, una por una.

Principios que mandan:

- **Vista previa primero, siempre.** Nada llega a Amazon sin pasar antes por
  `VALIDATION_PREVIEW` y sin un «sí» del usuario para esa publicación.
- **El borrador es del usuario.** El script propone; el usuario corrige el
  borrador (título, viñetas, precio, foto principal, envío) y el script
  respeta lo corregido en las siguientes corridas.
- **Lo que pide Amazon sale de Amazon.** Los atributos obligatorios y sus
  límites se leen del Product Type Definitions API, no se escriben a mano.
- **Nada sensible en el repo.** El repo es público: credenciales, borradores
  (llevan precios) y el registro de lo publicado viven en `~/.catalogo3d/`.
- **Solo biblioteca estándar de Python 3** (`urllib`, `json`…), como
  `catalog3d.py` y `generadores/`.

Fuera de alcance: tramitar la exención de GTIN o comprar códigos GS1 (se
hace en Seller Central), editar o retocar fotos (fondo blanco, recortes),
sincronizar precio o stock de forma continua entre ML y Amazon, crear
envíos a FBA (el plan de envío a la bodega), publicidad en Amazon, y
variaciones padre-hijo de Amazon (ver Requisito 6).

## Requisitos

### Requisito 1 — Credenciales fuera del repo

**Historia:** Como dueño de Savia Raíz, quiero que el script use mis
credenciales de Amazon y de ML sin que aparezcan nunca en el repo ni en la
pantalla, para no exponer mi cuenta de vendedor en un repo público.

#### Criterios de aceptación

1. CUANDO el script necesita acceso a Amazon ENTONCES DEBERÁ leer el LWA
   client id, el client secret y el refresh token de
   `~/.catalogo3d/amazon_credenciales.json`, y obtener con ellos un access
   token de LWA.
2. CUANDO el script necesita acceso a ML ENTONCES DEBERÁ usar el token de
   `~/.catalogo3d/ml_token.json` del mismo modo que ya lo usan los scripts
   existentes del repo (incluida su renovación).
3. SI el archivo de credenciales de Amazon no existe ENTONCES el script
   DEBERÁ explicar qué campos lleva y cómo se obtienen (Seller Central →
   Apps y servicios → Desarrollar aplicaciones, roles «Product Listing» y
   «Amazon Fulfillment», autorización de la app por el propio vendedor), sin
   pedir que se peguen en el chat.
4. SI el archivo de credenciales tiene permisos más abiertos que 600
   ENTONCES el script DEBERÁ negarse a usarlo y decir cómo corregirlo.
5. El script NO DEBERÁ imprimir, registrar en archivos ni incluir en
   mensajes de error ningún secreto, refresh token o access token, ni
   siquiera parcialmente.
6. CUANDO un access token vence durante una corrida ENTONCES el script
   DEBERÁ renovarlo y seguir, sin pedir nada al usuario.

### Requisito 2 — Leer lo publicado en ML

**Historia:** Como dueño, quiero que el script tome la información de mis
publicaciones de ML tal como está, para no volver a capturar nada.

#### Criterios de aceptación

1. CUANDO el usuario corre el script sin indicar publicación ENTONCES DEBERÁ
   listar las publicaciones activas de ML con su id MLM, título, precio y su
   estado en Amazon (sin borrador / borrador / validado / publicado).
2. CUANDO el script lee una publicación ENTONCES DEBERÁ traer de la API de
   ML: título, descripción, precio, categoría, atributos (marca, color,
   material, medidas y peso del artículo y del paquete) y fotos.
3. CUANDO el script toma las fotos ENTONCES DEBERÁ usar las URL públicas de
   mlstatic en su variante de tamaño completo (`-F`) y conservar el orden de
   ML.
4. SI la API de ML no responde o el token no sirve ENTONCES el script DEBERÁ
   decirlo y detenerse, sin escribir borradores a medias.

### Requisito 3 — Borrador por publicación, editable

**Historia:** Como dueño, quiero ver y corregir lo que se va a mandar a
Amazon antes de mandarlo, para que cada publicación salga como la del Olas
y no como una copia literal de ML.

#### Criterios de aceptación

1. CUANDO el script arma una publicación por primera vez ENTONCES DEBERÁ
   guardar un borrador legible y editable a mano en `~/.catalogo3d/` (fuera
   del repo) con todo lo que se mandará: SKU, tipo de producto, título,
   viñetas, descripción, palabras clave, atributos, medidas, fotos (la
   principal señalada aparte), precio y modo de envío.
2. CUANDO ya existe un borrador para esa publicación ENTONCES el script NO
   DEBERÁ sobrescribir lo que el usuario cambió; SI cambió algo en ML desde
   el borrador (título, precio, fotos) ENTONCES DEBERÁ avisarlo y dejar que
   el usuario decida.
3. CUANDO el script propone el SKU ENTONCES DEBERÁ seguir el patrón del
   patrón `SR-<TIPO>-<NOMBRE>-<COLOR>` y guardarlo en el borrador; SI la
   publicación ya existe en Amazon ENTONCES DEBERÁ usar su SKU (el Olas
   quedó con `5Z-W3LH-N087`, generado por Amazon). Una vez publicado, el SKU
   no cambia.
4. CUANDO el script propone viñetas y palabras clave (ML no las tiene)
   ENTONCES DEBERÁ sacarlas de la descripción y los atributos de ML, y
   marcarlas como «por revisar» hasta que el usuario las apruebe.
5. CUANDO el script propone el precio ENTONCES DEBERÁ partir del precio de
   ML y mostrar al lado el costo de la pieza si se conoce; el precio queda
   como «por revisar» y nunca se publica sin confirmarlo.
6. CUANDO el script muestra un borrador ENTONCES DEBERÁ mostrar las medidas
   y el peso del artículo y del paquete juntos, para que el usuario detecte
   datos mal capturados en ML (en el Olas, ML decía 8 cm de ancho y el largo
   real era 19.6 cm).

### Requisito 4 — Reglas de Amazon que ML no tiene

**Historia:** Como dueño, quiero que el script detecte lo que Amazon rechaza
o castiga, para no perder una publicación por un detalle que ML sí acepta.

#### Criterios de aceptación

1. CUANDO el título contiene palabras promocionales («obsequio», «regalo»,
   «gratis», «envío gratis», «oferta», «promoción», «más vendido» y
   similares) o caracteres que Amazon prohíbe en títulos ENTONCES el script
   DEBERÁ quitarlas en la propuesta y decir qué quitó.
2. CUANDO el título o cualquier campo excede el largo máximo que da el
   esquema del tipo de producto ENTONCES el script DEBERÁ marcarlo como error
   antes de llamar a Amazon.
3. CUANDO la publicación de ML menciona un kit de siembra, semillas, tierra,
   humus u obsequios incluidos ENTONCES el script DEBERÁ sacarlos de título,
   viñetas y descripción del borrador, avisar que el kit es posiblemente
   producto restringido en Amazon, y dejar al usuario la decisión de
   incluirlo.
4. CUANDO el script arma el borrador ENTONCES DEBERÁ proponer como foto
   principal la primera foto de ML y marcarla «por revisar», con un
   recordatorio de que Amazon pide fondo blanco puro, sin texto ni
   accesorios. Es advertencia, no bloqueo: Amazon aceptó la del Olas sin
   fondo blanco, y el usuario decide si la cambia.
5. CUANDO el usuario elige otra foto de ML como principal, o una URL pública
   propia (no de mlstatic) ENTONCES el script DEBERÁ usarla y verificar que
   responde como imagen antes de mandarla.
6. SI Amazon, al validar o después de publicar, reporta un problema con la
   foto principal (p. ej. publicación suprimida por la imagen) ENTONCES el
   script DEBERÁ mostrarlo como tal, para que el usuario sepa que esa sí
   hay que cambiarla.
7. CUANDO una foto de ML tiene texto promocional («¡Llévatelo hoy!»,
   «regalo sorpresa»…) y el usuario la marca así en el borrador ENTONCES el
   script NO DEBERÁ mandarla.
8. CUANDO la publicación no tiene GTIN ENTONCES el script DEBERÁ pedirla a
   Amazon como producto exento de identificador con la marca configurada
   (`Generic`, como el Olas; decidido el 2026-10-26), y
   SI Amazon responde que la marca no tiene exención ENTONCES DEBERÁ decir
   que se tramita en Seller Central y no reintentar.

### Requisito 5 — Tipo de producto y atributos según Amazon

**Historia:** Como dueño, quiero que el script sepa qué pide Amazon para cada
tipo de producto, para no adivinar campos obligatorios.

#### Criterios de aceptación

1. CUANDO el script arma un borrador ENTONCES DEBERÁ proponer el tipo de
   producto de Amazon buscándolo en el Product Type Definitions API con
   palabras del título y la categoría de ML, y el usuario lo confirma en el
   borrador.
2. CUANDO una categoría de ML ya se mapeó a un tipo de producto confirmado
   ENTONCES el script DEBERÁ reusar ese mapeo para las demás publicaciones de
   esa categoría.
3. CUANDO el script tiene el tipo de producto ENTONCES DEBERÁ leer su esquema
   para el marketplace de México (A1AM78C64UM0Y8) y en español, y reportar
   qué atributos obligatorios quedaron sin valor en el borrador.
4. CUANDO un atributo obligatorio tiene una lista cerrada de valores
   ENTONCES el script DEBERÁ proponer el valor de la lista más cercano al dato
   de ML y, si no hay uno claro, dejarlo marcado para el usuario.
5. El script DEBERÁ guardar el esquema descargado en caché local con su
   versión, y volverlo a bajar cuando Amazon publique una versión nueva.

### Requisito 6 — Variaciones de ML

**Historia:** Como dueño, quiero saber qué pasa con las publicaciones de ML
que tienen varios colores, para no publicar una a medias.

#### Criterios de aceptación

1. CUANDO una publicación de ML tiene variaciones ENTONCES el script DEBERÁ
   decirlo en la lista y armar un borrador por variación, cada una con su
   SKU, color y fotos, como publicaciones independientes de Amazon.
2. El script NO DEBERÁ crear familias padre-hijo de Amazon en esta versión.

### Requisito 7 — Envío: FBA o propio

**Historia:** Como dueño, quiero elegir por publicación si la manda Amazon
desde su bodega o si la mando yo, para empezar con lo que me convenga en cada
producto.

#### Criterios de aceptación

1. CUANDO el borrador dice envío FBA ENTONCES el script DEBERÁ mandar la
   disponibilidad con el canal de Amazon (`AMAZON_NA`), sin cantidad.
2. CUANDO el borrador dice envío propio ENTONCES el script DEBERÁ mandar la
   cantidad disponible que indique el borrador, y SI no hay cantidad ENTONCES
   NO DEBERÁ publicar.
3. CUANDO se crea un borrador nuevo ENTONCES el modo de envío DEBERÁ quedar
   como «por revisar»; el stock que la pieza tenga en ML Full no cuenta como
   stock disponible para envío propio.

### Requisito 8 — Validar antes de publicar

**Historia:** Como dueño, quiero ver qué diría Amazon de una publicación
antes de que exista, para corregir sin dejar basura en mi catálogo.

#### Criterios de aceptación

1. CUANDO el usuario pide validar una publicación ENTONCES el script DEBERÁ
   mandarla a Listings Items API con `mode=VALIDATION_PREVIEW` en
   `sellingpartnerapi-na.amazon.com` y no crear nada en Amazon.
2. CUANDO Amazon responde ENTONCES el script DEBERÁ mostrar, en español
   cuando se pueda, cada error y advertencia con el campo al que se refiere,
   y guardar el resultado en el borrador con su fecha.
3. CUANDO la validación no tiene errores ENTONCES el borrador DEBERÁ quedar
   como «validado» con el contenido exacto que se validó.
4. SI el usuario cambia el borrador después de validarlo ENTONCES el estado
   DEBERÁ volver a «borrador» y pedir validar otra vez.
5. CUANDO Amazon responde con límite de peticiones (429) o un error
   temporal ENTONCES el script DEBERÁ esperar y reintentar con espera
   creciente, sin perder el avance.

### Requisito 9 — Publicar con aprobación una por una

**Historia:** Como dueño, quiero aprobar cada publicación antes de que salga,
para no llenar mi cuenta nueva de Amazon de errores que afecten su salud.

#### Criterios de aceptación

1. El script DEBERÁ publicar de verdad solo con una orden explícita por
   publicación, y solo si el borrador está «validado» y sin campos «por
   revisar» (la foto principal incluida: el usuario la revisa, aunque no
   tenga fondo blanco).
2. CUANDO el usuario ordena publicar ENTONCES el script DEBERÁ mostrar un
   resumen (SKU, título, precio, envío, foto principal) y pedir confirmación
   escrita antes de llamar a Amazon.
3. CUANDO el usuario pide varias publicaciones de una vez ENTONCES el script
   DEBERÁ pedir confirmación de cada una por separado.
4. SI el SKU ya existe en la cuenta de Amazon ENTONCES el script DEBERÁ
   mostrar las diferencias entre lo publicado y el borrador y solo actualizar
   los campos que el usuario confirme, en lugar de reemplazar la publicación.
5. CUANDO Amazon acepta la publicación ENTONCES el script DEBERÁ registrar en
   `~/.catalogo3d/` la relación MLM ↔ SKU ↔ ASIN (cuando Amazon lo asigne),
   la fecha y el precio, y mostrar el estado que reporta Amazon.

### Requisito 10 — Prueba contra el Portacubiertos Olas

**Historia:** Como dueño, quiero ver que el script reproduce lo que hice a
mano con el Olas, para confiar en él con las otras 39.

#### Criterios de aceptación

1. CUANDO el usuario corre la vista previa sobre MLM3674350731 ENTONCES el
   script DEBERÁ armar el borrador, validarlo con `VALIDATION_PREVIEW` y
   mostrar el resultado de Amazon.
2. CUANDO el SKU del Olas (`5Z-W3LH-N087`) ya está publicado ENTONCES el
   script DEBERÁ leerlo de Amazon y mostrar lado a lado lo publicado a mano y
   lo que propone el borrador (título, viñetas, atributos, medidas, fotos,
   precio), sin modificar la publicación existente.
