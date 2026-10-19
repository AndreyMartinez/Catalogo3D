# Requisitos — Vocabulario de formas

## Introducción

El motor tiene un solo arquetipo. Contorno + acabado + perfil + divisores +
base da siempre lo mismo: un recipiente de pared constante, fondo plano y boca
horizontal completa. Las ocho plantas por diez acabados por siete perfiles no
son quinientas sesenta piezas, son quinientas sesenta versiones del mismo bote.

Y no es cuestión de afinación. Los siete perfiles están escritos como
`1.0 ± k·(algo)` con `k` topada en 0.35, así que la silueta no puede alejarse
más de un tercio de un cilindro; el relieve se recorta a `pared − 0.4`, que es
milímetro y pico; el pliegue se topa en 0.16. Puestos los siete perfiles a su
máximo, uno junto a otro, salen siete tazas. Por eso mover los controles no
cambia el diseño: lo que se mueve es la decoración sobre una forma fija.

Lo que falta no son más opciones dentro de los ejes que hay. Son ejes que no
existen. Un jarrón no es un vaso con otro acabado: es una pieza que **se cierra
arriba**. Una pieza se ve diseñada y no comprada cuando **se levanta de la
mesa**. Lo bohemio no es una textura, es **el hueco**: la celosía, el arco, lo
que deja pasar la luz. Y lo moderno vive tanto en **el borde** —un corte
diagonal, un labio que no es un aro— como en la silueta.

Este documento agrega esos cuatro ejes y revisa los topes de los que ya están.

Dos cosas mandan sobre todo lo demás, y no son negociables:

- **Se sigue imprimiendo sin soportes.** Es el contrato de la línea. Un eje
  nuevo que obligue a soportes no es un eje nuevo, es otro producto.
- **Las piezas de siempre salen idénticas.** El portacontroles, el portalápices
  y el portacubiertos no se enteran de nada de esto.

Y una regla de criterio, que aparece muchas veces abajo: **el motor avisa, no
prohíbe.** Donde la física impide algo, se impide. Donde sólo el buen gusto
sugiere un límite, el límite se mueve y el motor advierte — el gusto es del
usuario, no del código.

Nota de contexto: la pestaña «Idea» queda pausada en su tarea 4. Su valor
depende del espacio de formas que pueda alcanzar, así que primero se agranda el
espacio.

## Requisitos

### Requisito 1 — El cuello y la boca

**Historia:** Como alguien que quiere un jarrón y no un vaso, quiero que la
pieza se cierre arriba y que la boca sea independiente de la panza, para llegar
a la silueta que ningún perfil actual alcanza.

#### Criterios de aceptación

1. CUANDO el usuario define un cuello ENTONCES el sistema DEBERÁ permitir que la
   boca mida desde una cuarta parte de la panza hasta el ancho completo.
2. CUANDO se define un cuello ENTONCES el sistema DEBERÁ permitir elegir a qué
   altura empieza a cerrarse el hombro, independientemente de dónde esté la
   parte más ancha.
3. CUANDO el hombro se cierra ENTONCES la transición DEBERÁ ser continua en
   tangente con la panza y con el cuello: una esquina viva en el hombro es
   exactamente lo que hace que una pieza se lea barata.
4. SI el hombro se cierra más rápido de 45° respecto a la vertical ENTONCES el
   sistema DEBERÁ avisar que la pieza va a pedir soportes, con el mismo
   mecanismo de aviso que ya usa el perfil.
5. CUANDO hay cuello ENTONCES la pared interior DEBERÁ seguir el cuello
   conservando su espesor, igual que hace hoy con el perfil.
6. CUANDO hay cuello ENTONCES el sistema NO DEBERÁ ofrecer divisores: no caben
   por la boca y no tienen dónde apoyarse.
7. CUANDO el cuello está en su valor neutro ENTONCES la geometría DEBERÁ ser
   idéntica, vértice por vértice, a la de una pieza sin cuello.

### Requisito 2 — El pie

**Historia:** Como alguien que quiere que la pieza se vea como un objeto y no
como un bote, quiero levantarla de la mesa, porque una pieza que se para sobre
su huella completa se lee como envase.

#### Criterios de aceptación

1. CUANDO el usuario elige un pie ENTONCES el sistema DEBERÁ ofrecer al menos
   tres maneras: anillo de apoyo, plinto retranqueado y patas.
2. CUANDO se elige anillo de apoyo ENTONCES el fondo DEBERÁ levantarse de la
   mesa quedando sólo un aro en contacto, con el ancho del aro y el hueco
   ajustables.
3. CUANDO se elige plinto ENTONCES el sistema DEBERÁ permitir ajustar cuánto se
   mete hacia adentro y cuánto mide de alto.
4. CUANDO se eligen patas ENTONCES el sistema DEBERÁ permitir de tres a seis, y
   DEBERÁ repartirlas parejo alrededor del contorno.
5. SI el retranqueo del pie deja un saliente de más de 45° ENTONCES el sistema
   DEBERÁ achaflanarlo automáticamente para que imprima sin soportes, y DEBERÁ
   decir que lo hizo.
6. CUANDO hay pie ENTONCES la superficie de apoyo DEBERÁ ser plana y estar toda
   a la misma altura: una pieza que baila es una pieza mal generada.
7. CUANDO hay pie y bandeja de goteo ENTONCES la bandeja DEBERÁ medirse contra
   lo que de verdad apoya, no contra la huella del cuerpo.
8. CUANDO el pie está en su valor neutro ENTONCES la geometría DEBERÁ ser
   idéntica a la de una pieza sin pie.

### Requisito 3 — El calado

**Historia:** Como alguien que busca lo bohemio, quiero abrir huecos en la
pared, porque el hueco —la celosía, el arco, la luz que pasa— es lo que más
aleja una pieza del bote y ninguna textura lo consigue.

#### Criterios de aceptación

1. CUANDO el usuario activa el calado ENTONCES el sistema DEBERÁ ofrecer al
   menos dos familias: ventanas en rejilla y celosía de diagonales.
2. CUANDO se definen ventanas ENTONCES el sistema DEBERÁ permitir cuántas hay a
   lo largo del contorno y cuántas hileras a lo alto.
3. CUANDO se dibuja el remate superior de una abertura ENTONCES DEBERÁ ser en
   arco o en punta, nunca un dintel plano: un dintel plano es un puente
   horizontal y es justo lo que obliga a poner soportes. Ese límite es físico,
   y por lo tanto no se puede desactivar.
4. CUANDO se calcula el calado ENTONCES el sistema DEBERÁ dejar un marco
   completo arriba y abajo, y el puente entre dos aberturas NUNCA DEBERÁ ser más
   angosto que dos paredes.
5. SI los valores pedidos no dejan material suficiente ENTONCES el sistema
   DEBERÁ reducir la cantidad o el tamaño de las aberturas hasta que quepan, y
   DEBERÁ avisar de lo que recortó, como ya hace con los divisores y el drenaje.
6. CUANDO hay calado ENTONCES el sistema DEBERÁ avisar que la pieza no retiene
   agua, y NO DEBERÁ ofrecer bandeja de goteo ni drenaje.
7. CUANDO hay calado y también acabado con relieve ENTONCES el relieve DEBERÁ
   respetar el marco de las aberturas sin dejar bordes deshilachados.
8. CUANDO el calado está apagado ENTONCES la geometría DEBERÁ ser idéntica a la
   de hoy.

### Requisito 4 — El borde

**Historia:** Como alguien que quiere una pieza que se lea moderna, quiero que
el labio no sea siempre un aro horizontal, porque el borde es lo primero que
mira el ojo y hoy es idéntico en las quinientas sesenta combinaciones.

#### Criterios de aceptación

1. CUANDO el usuario elige un borde ENTONCES el sistema DEBERÁ ofrecer al menos:
   recto, corte diagonal, ondulado y en pétalos.
2. CUANDO se elige corte diagonal ENTONCES el sistema DEBERÁ permitir ajustar la
   inclinación y hacia dónde mira el punto bajo.
3. CUANDO se elige ondulado o pétalos ENTONCES el sistema DEBERÁ permitir
   ajustar cuántas ondas y qué tan hondas.
4. CUANDO el borde baja ENTONCES el casco DEBERÁ cerrarse igual de bien que con
   el escalón que ya existe, reusando el mismo corte por columna.
5. SI el borde baja más de lo que mide un divisor ENTONCES el sistema DEBERÁ
   recortar el divisor para que no asome, y DEBERÁ avisarlo.
6. CUANDO el borde está en recto ENTONCES la geometría DEBERÁ ser idéntica a la
   de hoy.

### Requisito 5 — Rangos que alcancen para algo

**Historia:** Como alguien que mueve un control al máximo, quiero que se note,
porque hoy los siete perfiles a tope siguen siendo siete tazas.

#### Criterios de aceptación

1. CUANDO se revise cada parámetro numérico ENTONCES su tope DEBERÁ justificarse
   por geometría o por imprimibilidad; SI el tope sólo responde al buen gusto
   ENTONCES DEBERÁ ampliarse y el motor DEBERÁ avisar en su lugar.
2. CUANDO se amplíe el rango de un parámetro ENTONCES los valores de las recetas
   existentes NO DEBERÁN moverse.
3. CUANDO un valor entra en la zona donde la pieza pide soportes ENTONCES el
   sistema DEBERÁ avisar, pero NO DEBERÁ impedirlo.
4. CUANDO se amplíen los rangos ENTONCES el sistema DEBERÁ seguir garantizando
   que la malla salga cerrada en todo el rango declarado.

### Requisito 6 — Que siga imprimiendo sin soportes

**Historia:** Como quien va a imprimir esto de verdad, quiero que la promesa de
la línea siga en pie, porque una pieza que pide soportes deja de ser un archivo
que se manda a imprimir y pasa a ser un problema.

#### Criterios de aceptación

1. CUANDO se construye cualquier pieza ENTONCES el sistema DEBERÁ medir el
   voladizo de todas las superficies nuevas —hombro, cuello, pie, remates de las
   aberturas— con el mismo criterio con que ya mide la pared.
2. CUANDO alguna supera los 45° respecto a la vertical ENTONCES el sistema
   DEBERÁ avisar diciendo qué parte y cuánto.
3. CUANDO una restricción es física ENTONCES el sistema DEBERÁ resolverla solo
   —achaflanar el pie, arquear el remate— en vez de dejar al usuario descubrirlo
   en el laminador.
4. CUANDO la pieza queda apoyada en el plato ENTONCES la superficie de contacto
   DEBERÁ ser plana y suficiente para que no se despegue.
5. CUANDO cualquier combinación de los ejes nuevos se construye ENTONCES la
   malla DEBERÁ salir cerrada.

### Requisito 7 — Que no se rompa lo que ya funciona

**Historia:** Como dueño de un catálogo que ya uso, quiero que los ejes nuevos
sean aditivos, para no cambiar unas piezas por otras.

#### Criterios de aceptación

1. CUANDO se construyen las tres recetas existentes ENTONCES DEBERÁN dar
   exactamente los mismos vértices, triángulos y gramos que antes de este
   trabajo.
2. CUANDO se agrega un eje nuevo ENTONCES DEBERÁ declararse en
   `disenos.PARAMETROS` con su etiqueta, rango, grupo y ayuda, de modo que la
   pestaña «Crear» lo levante sola y la pestaña «Idea» lo conozca sin tocar
   ningún prompt.
3. CUANDO dos ejes no pueden convivir ENTONCES el sistema DEBERÁ decirlo en la
   interfaz —escondiendo el control o avisando—, y NUNCA DEBERÁ generar en
   silencio una pieza que ignora lo que el usuario pidió.
4. CUANDO se combinan ejes nuevos con los viejos ENTONCES el orden de aplicación
   DEBERÁ quedar definido y ser el mismo siempre: la planta, luego el perfil,
   luego el cuello, luego el acabado, luego el calado, luego el borde, y el pie
   al final.
5. El sistema NUNCA DEBERÁ requerir una dependencia fuera de la librería
   estándar de Python 3.
6. CUANDO se termine cada eje ENTONCES DEBERÁ haber pruebas que cubran su
   geometría, sus avisos y su valor neutro, en el mismo archivo de pruebas que
   ya existe.

### Requisito 8 — Que se pueda ver lo que se elige

**Historia:** Como quien va a usar todo esto, quiero ver las opciones antes de
elegirlas, porque con cuatro ejes más el catálogo pasa de quinientas
combinaciones a decenas de miles y elegir a ciegas deja de ser viable.

#### Criterios de aceptación

1. CUANDO la interfaz muestre un selector de forma —planta, perfil, cuello, pie,
   calado o borde— ENTONCES DEBERÁ acompañar cada opción de una miniatura
   generada por el propio motor.
2. CUANDO se generen esas miniaturas ENTONCES DEBERÁN calcularse una sola vez y
   guardarse, para no rehacerlas en cada arranque.
3. CUANDO el usuario cambia un eje ENTONCES la vista previa DEBERÁ seguir
   respondiendo con la misma agilidad que hoy.
4. Este requisito DEBERÁ abordarse después de los ejes de forma, no antes:
   ponerle miniaturas bonitas al catálogo de hoy sería decorar el problema.
