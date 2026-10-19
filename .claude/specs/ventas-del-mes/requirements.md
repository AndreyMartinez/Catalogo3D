# Requisitos — Ventas del mes

## Introducción

Hoy el taller mira las ventas por **semana cerrada**: `estudio-mercado` baja
los datos con `colecta-full/scripts/traer_datos.py`, `semana.py` calcula las
cifras de lunes a domingo y el domingo sale el reporte. Lo que no existe es la
pregunta de a media semana o a media quincena: **¿cómo viene el mes?** —
cuánto llevamos, si vamos arriba o abajo del mes pasado al mismo día, a dónde
vamos a cerrar si seguimos a este ritmo, y qué publicaciones lo están jalando
o frenando.

Esta función agrega ese corte mensual, calculado de los mismos datos reales de
MercadoLibre que ya se bajan, y lo deja como un reporte que el usuario puede
pedir cualquier día del mes.

Principios que mandan:

- **Mismo origen de datos.** Nada de una segunda descarga ni de cifras
  tecleadas a mano: se lee lo que deja `traer_datos.py`.
- **Comparar lo comparable.** Un mes a medias se compara contra el mismo
  número de días del mes anterior, no contra el mes anterior completo.
- **Decir cuánto pesa cada cifra.** Con pocas unidades, una proyección es una
  suposición; el reporte lo dice con el mismo vocabulario del estudio de
  mercado (medido / correlación / suposición).
- **Los datos no se versionan.** El repo es público: el reporte vive en
  `.claude/mercado/`, que ya está ignorado por git.

Fuera de alcance: la revisión de competencia en el navegador (sigue siendo
del reporte semanal), metas de venta automáticas, cambiar precios o
publicaciones, y una vista dentro de la galería (puede ser una función
aparte una vez que el cálculo exista).

## Requisitos

### Requisito 1 — El corte del mes en curso

**Historia:** Como dueño de Savia Raíz, quiero ver en un solo lugar cuánto
llevo vendido este mes, para saber cómo voy sin esperar al domingo ni al
cierre de mes.

#### Criterios de aceptación

1. CUANDO el usuario pide el análisis sin indicar mes ENTONCES el sistema
   DEBERÁ usar el mes calendario en curso, del día 1 hasta el último día con
   datos, en hora de la Ciudad de México.
2. CUANDO el sistema calcula el corte ENTONCES DEBERÁ reportar, como mínimo:
   unidades vendidas, número de órdenes, ingreso bruto, ticket promedio y
   días transcurridos contra días totales del mes.
3. CUANDO una orden está cancelada ENTONCES el sistema NO DEBERÁ contarla
   como venta, y DEBERÁ reportar aparte cuántas hubo.
4. CUANDO el usuario indica un mes ya cerrado (`AAAA-MM`) ENTONCES el sistema
   DEBERÁ hacer el mismo análisis sobre ese mes completo, sin proyección.
5. SI los datos disponibles no cubren el mes pedido completo ENTONCES el
   sistema DEBERÁ decir desde y hasta qué fecha hay datos, y no rellenar los
   días faltantes con ceros.

### Requisito 2 — Contra el mes anterior, al mismo día

**Historia:** Como dueño, quiero saber si voy mejor o peor que el mes pasado,
para no confundir «llevo poco» con «es día 15».

#### Criterios de aceptación

1. CUANDO el sistema compara contra el mes anterior ENTONCES DEBERÁ usar los
   mismos días transcurridos (del 1 al día N de cada mes), y además mostrar
   el total del mes anterior completo como referencia.
2. CUANDO el mes anterior es más corto que el día N actual ENTONCES el
   sistema DEBERÁ comparar contra el mes anterior completo y decirlo.
3. CUANDO hay datos de al menos tres meses previos ENTONCES el sistema DEBERÁ
   mostrar también el promedio de esos tres meses al mismo día N.
4. CUANDO el sistema muestra una diferencia ENTONCES DEBERÁ darla en unidades
   y en porcentaje, y SI la base es menor a 10 unidades ENTONCES DEBERÁ
   omitir el porcentaje y decir que la base es demasiado chica.

### Requisito 3 — Hacia dónde va a cerrar

**Historia:** Como dueño, quiero una estimación del cierre del mes, para
decidir con tiempo si empujo algo (publicidad, una colecta a Full, un
producto) o si voy bien.

#### Criterios de aceptación

1. CUANDO el mes está en curso ENTONCES el sistema DEBERÁ proyectar las
   unidades e ingreso al cierre con el ritmo diario de lo que va del mes, y
   mostrar también la proyección con el ritmo de los últimos 7 días.
2. CUANDO las dos proyecciones difieren en más de un 20 % ENTONCES el sistema
   DEBERÁ señalarlo como cambio de ritmo dentro del mes.
3. SI van menos de 7 días del mes ENTONCES el sistema DEBERÁ marcar la
   proyección como «suposición» y decir que todavía no es confiable.
4. CUANDO se muestra la proyección ENTONCES el sistema DEBERÁ etiquetarla
   siempre con su nivel de evidencia y NUNCA DEBERÁ presentarla como cifra
   medida.
5. SI el usuario indica una meta del mes (unidades o pesos) ENTONCES el
   sistema DEBERÁ decir cuánto falta y qué ritmo diario hace falta en los días
   que quedan, comparado con el ritmo actual.

### Requisito 4 — Qué lo está jalando y qué lo frena

**Historia:** Como dueño, quiero ver el mes desglosado por publicación y por
categoría, para saber dónde poner atención y no solo cuánto llevo.

#### Criterios de aceptación

1. CUANDO el sistema desglosa ENTONCES DEBERÁ mostrar unidades e ingreso por
   publicación y por categoría (portacontroles, portacubiertos, portacepillos,
   etc.), con su participación en el total del mes.
2. CUANDO el sistema desglosa ENTONCES DEBERÁ separar las ventas de Full de
   las que no son de Full.
3. CUANDO una publicación cambia frente al mes anterior al mismo día
   ENTONCES el sistema DEBERÁ marcarla con la misma familia de alertas que
   usa el reporte semanal (`sube`, `baja`, `dormida`, `nueva`), con un umbral
   que no dispare por una o dos unidades sueltas.
4. CUANDO una publicación tuvo ventas el mes anterior y ninguna en lo que va
   de este ENTONCES el sistema DEBERÁ listarla como «dormida» aunque haya
   pocas unidades en juego.
5. CUANDO el sistema muestra el desglose ENTONCES DEBERÁ ordenarlo de mayor a
   menor por unidades del mes en curso.

### Requisito 5 — Cuánto deja, no solo cuánto entra

**Historia:** Como dueño, quiero ver el retorno estimado del mes, para no
confundir ingreso bruto con lo que de verdad le queda al negocio.

#### Criterios de aceptación

1. CUANDO el sistema reporta dinero ENTONCES DEBERÁ distinguir ingreso bruto
   (lo que pagó el comprador) del retorno estimado por venta.
2. CUANDO el sistema estima el retorno ENTONCES DEBERÁ partir del retorno por
   venta que registra el estudio de mercado y del costo por pieza de
   `.catalogo3d_costos.json`, citando la fuente y su nivel de evidencia.
3. El sistema NUNCA DEBERÁ usar el neto que devuelve `/orders` como
   ganancia, porque no descuenta todos los cargos de ML.
4. SI no hay un retorno por venta registrado ENTONCES el sistema DEBERÁ
   mostrar solo el ingreso bruto y decir que falta el dato.

### Requisito 6 — Datos frescos y honestos

**Historia:** Como dueño, quiero saber si las cifras están al día, para no
tomar decisiones con datos de hace una semana sin darme cuenta.

#### Criterios de aceptación

1. CUANDO el sistema corre ENTONCES DEBERÁ mostrar arriba del reporte la
   fecha y hora de la última descarga de datos.
2. SI la última descarga tiene más de 24 horas ENTONCES el sistema DEBERÁ
   marcarlo con ⚠️ y sugerir correr `traer_datos.py` antes de leer el
   reporte.
3. SI `traer_datos.py` falla por sesión vencida ENTONCES el sistema DEBERÁ
   seguir con los últimos datos guardados, marcarlos como viejos y decir que
   el usuario tiene que correr `login.py`; NUNCA DEBERÁ iniciar sesión ni
   autorizar la app por su cuenta.
4. SI no hay ningún archivo de datos ENTONCES el sistema DEBERÁ decir qué
   comando correr, en vez de fallar con un error técnico.
5. CUANDO el mes en curso tiene cero ventas registradas ENTONCES el sistema
   DEBERÁ producir el reporte igual, diciendo que no hay ventas, en vez de
   dividir entre cero o abortar.

### Requisito 7 — Dónde queda y cómo se pide

**Historia:** Como dueño, quiero pedir «¿cómo vienen las ventas del mes?» y
recibir el análisis, para no tener que acordarme de comandos.

#### Criterios de aceptación

1. CUANDO el análisis termina ENTONCES el sistema DEBERÁ guardar las cifras en
   `.claude/mercado/meses/AAAA-MM.json` y una versión legible en
   `.claude/mercado/meses/AAAA-MM.md`, sobrescribiendo el corte anterior del
   mismo mes.
2. CUANDO se guarda el corte ENTONCES NINGÚN archivo con ventas DEBERÁ quedar
   fuera de las rutas ya ignoradas por git.
3. CUANDO el usuario pregunta cómo van las ventas del mes ENTONCES
   `estudio-mercado` DEBERÁ saber que existe este corte y usarlo, en vez de
   responder con la última semana cerrada.
4. CUANDO el reporte legible se arma ENTONCES DEBERÁ abrir con un resumen de
   no más de 5 líneas: llevamos X, contra Y al mismo día del mes pasado, vamos
   a cerrar cerca de Z, lo que más se movió, y una sola cosa que haría el
   usuario.
5. El cálculo DEBERÁ usar solo la biblioteca estándar de Python 3.
