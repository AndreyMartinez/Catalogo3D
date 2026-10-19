# Catálogo 3D

Galería local para tus diseños `.3mf` (Bambu Studio). Corre un servidor
en tu máquina y se abre en el navegador — sin dependencias, solo Python 3
estándar.

## Qué hace

- Muestra la miniatura de cada `.3mf` (la que ya trae el propio archivo).
- **Abre el diseño en Bambu Studio** con un clic en la miniatura (o con el
  botón «▶ Abrir en Bambu Studio»). Funciona igual en la pestaña Descargas.
  Si no encuentra Bambu Studio instalado, abre el archivo con la app por
  defecto del sistema.
- Lee el peso en gramos si el archivo ya fue laminado en Bambu Studio, y
  te deja corregirlo a mano por unidad en la propia tarjeta (lo que
  escribas manda sobre lo que trae el `.3mf`).
- **Cuenta cuánto te cuesta cada producto y cuánto ganas**: material
  (peso × precio por kg) + paquetería, frente al retorno de inversión (lo
  que te deposita MercadoLibre por la venta). Lo tienes explicado más
  abajo, en «Costos y precio».
- Pestañas **⏳ Por cargar** y **✓ Con información**: los diseños a los que
  todavía les falta un dato para cerrar la cuenta y los que ya la tienen,
  cada pestaña con su contador.
- Pestaña **📊 Mi negocio**: el cierre de cada mes. Anotas las ventas y los
  gastos que no van dentro de la pieza (publicidad, luz, renta) y te dice
  margen, utilidad, punto de equilibrio y qué diseño te deja más.
- Renombra el archivo real en disco desde la galería.
- Elimina el archivo real en disco desde la galería.
- Recorre subcarpetas: muestra también los `.3mf` que tengas organizados
  en carpetas dentro de tu carpeta de diseños.
- **Selección múltiple**: marca la casilla de cada tarjeta (o «Seleccionar
  todo») y aparece una barra flotante para eliminar en lote, o para mover
  en lote a tu carpeta cuando estás en la pestaña Descargas. Si algún
  archivo falla, los demás sí se procesan y la galería te dice cuántos.
- Pestaña **Descargas**: lista los `.3mf` que tengas en `~/Downloads`,
  te deja moverlos con un botón a tu carpeta de diseños (evita
  sobrescribir si ya existe un archivo con el mismo nombre) y también
  borrarlos directamente de `~/Downloads`.
- **Vínculo con MercadoLibre**: en cada diseño puedes pegar el link de su
  publicación («🔗 Vincular ML») y el precio de venta. La tarjeta muestra
  un botón «🛒 Ver en MercadoLibre» y lo que te queda neto (precio de venta
  menos la comisión de MercadoLibre —ajustable arriba— menos el costo
  total). Se guarda en `.catalogo3d_mercadolibre.json`, dentro de tu
  carpeta de diseños.

- Pestaña **Crear**: genera piezas nuevas de la línea (portacontroles,
  portalápices, portacubiertos) moviendo
  controles, con vista previa en vivo, peso y costo antes de guardar. La
  vista se puede girar y subir con los dos deslizadores de abajo, y la
  miniatura se guarda desde el ángulo que dejaste. Al guardar deja el
  `.3mf`, el `.stl` y la miniatura en la subcarpeta que le toca.

## Costos y precio

Arriba, en la cabecera, se ponen los dos números que valen para todo el
catálogo: **costo del filamento por kg** y **paquetería** (cuál de los
paquetes se usa por defecto). Se guardan en `.catalogo3d_costos.json`,
dentro de tu carpeta de diseños.

Cada tarjeta trae un desplegable **💰 Costos y precio** con lo suyo:

| Campo | Para qué sirve |
|---|---|
| Peso por unidad (g) | corrige el peso del `.3mf`, o lo pone si nunca se laminó |
| Costo de la pieza | escribe el costo a mano y se ignora el cálculo por peso |
| Paquetería | ese diseño puede usar otro paquete, o ninguno |
| Retorno de inversión | los pesos que te deposita MercadoLibre por una venta |
| Precio de la competencia | opcional; sirve para saber si vas caro o barato |

El **retorno de inversión** es dinero, no un porcentaje: los pesos que
MercadoLibre te deposita cuando alguien compra. Es el número que ves en tu
cuenta, así que se escribe tal cual.

Los campos vacíos vuelven a lo automático: el peso al del archivo, el costo
al de peso × filamento y la paquetería a la del catálogo. Se guardan solos,
medio segundo después de la última tecla.

Debajo sale la cuenta completa:

```
Pieza · filamento            $7.55
Paquetería · Envío completo $18.10
Me cuesta el producto       $25.65
Precio publicado           $300.00
Me retorna la venta        $261.00
Ganancia por venta         $235.35
```

### Por cargar / Con información

Las dos pestañas son la misma carpeta con un filtro. Un diseño está
**por cargar** mientras le falte algo para cerrar la cuenta: el peso (ni
laminado ni escrito) o el retorno (ni a mano ni desde MercadoLibre). En
cuanto lo tiene, pasa a **con información**. La tarjeta te dice qué le falta
con una etiqueta «⏳ falta retorno», y las pestañas llevan el contador. La
tarjeta que estás editando no se te mueve de sitio: cambia de pestaña la
próxima vez que entres.

### La paquetería se calcula desde tus compras

El botón ⚙ de la cabecera abre el editor. Hay tres paquetes (por ejemplo
«Envío completo», «Envío simple» y «Entrega en mano»), y cada uno lleva los
elementos que quieras. De cada elemento se apunta **lo que costó la última
compra** y **cuántas unidades traía**; el costo por unidad sale de dividir
una cosa entre la otra:

| Elemento | Última compra | Unidades | Por unidad |
|---|---|---|---|
| Bolsa semillas | $30.00 | 100 | $0.30 |
| Bolsa envío | $12.00 | 1 | $12.00 |
| Etiquetas | $30.00 | 100 | $0.30 |
| Maceta regalo | $4.00 | 1 | $4.00 |
| Nuevo tarro tierra | $1.50 | 1 | $1.50 |
| **Total costos generales** | | | **$18.10** |

Así, cuando vuelvas a comprar bolsas, con cambiar esos dos números se
recalculan todos los precios del catálogo.

## Mi negocio: el cierre del mes

La pestaña **📊 Mi negocio** es el resumen de rentabilidad, un mes a la vez
(las flechas ‹ › cambian de mes). Se guarda en `.catalogo3d_negocio.json`.

**Ventas del mes**: eliges el diseño y se llenan solos lo que te retorna y
lo que te cuesta, con lo que tenga cargado ese día. A partir de ahí son
números del mes: si mañana sube el filamento, el mes cerrado no se mueve.

**Gastos del mes**: lo que no va dentro de la pieza —publicidad, recibo de
luz, renta, la compra de un rollo—. El campo sugiere los conceptos que ya
sueles usar.

Con eso sale la cuenta:

| | |
|---|---|
| Piezas vendidas | y el ticket promedio |
| Me retornaron | lo que te depositaron en total |
| Costo de lo vendido | material y paquetería de esas piezas |
| **Margen bruto** | lo que dejan las piezas, y qué % es del retorno |
| Gastos del mes | publicidad, luz, renta… |
| **Utilidad del mes** | el margen ya con los gastos encima, comparada con el mes pasado |
| Punto de equilibrio | cuántas piezas hay que vender para cubrir los gastos, y cuántas te faltan |

Debajo, **qué te deja más este mes**: cada diseño con su margen del mes en
una barra, ordenados de mejor a peor. Los que salen en rojo te están
costando dinero.

### Precios y publicidad

Al final de la pestaña está el análisis, un renglón por diseño.

**¿Está caro o barato?** Si le cargaste el precio de la competencia, es una
medición: te dice cuánto por encima o por debajo estás (±15% se considera
precio de mercado). Si no, es una inferencia a partir de tu propio catálogo,
cruzando margen con rotación, y la tarjeta lo dice con esas palabras:

- *quizá caro*: deja más que la mediana de tu catálogo pero no rotó este mes.
- *quizá barato*: rota más que los demás y deja menos.
- *tu producto estrella*: rota por encima de la mediana y además deja bien.
- *pierdes dinero en cada venta*: el retorno no cubre el costo.

**¿Qué ROAS necesito?** El ROAS se calcula sobre el precio que paga el
comprador, que es como lo reporta MercadoLibre, para que los números sean
comparables con los de su panel:

```
Pago máximo por venta = margen − gastos generales por pieza − utilidad que pediste
ROAS de equilibrio    = precio publicado ÷ margen
ROAS objetivo         = precio publicado ÷ pago máximo por venta
```

El de equilibrio solo paga la pieza: por encima de ahí el anuncio no te
cuesta dinero. El objetivo es el que de verdad te deja utilidad, porque
además reparte los gastos generales del mes entre las piezas que vendiste y
te descuenta lo que pusiste en «quiero ganar por pieza».

Arriba salen los tres números del mes: lo que gastaste en publicidad (los
gastos marcados como tal), tu **ROAS real** y el **ROAS mínimo** con el tope
en pesos que puedes gastar sin comerte la utilidad. Si el real va por encima
del mínimo, el número sale en verde.

## Crear diseños

Todos los productos son el mismo primitivo: **contorno + acabado + perfil
vertical + divisores + base**. Por eso una receta no es código, son los
valores con los que arranca, y las combinaciones que nadie ha hecho salen
gratis (un portalápices en torsión, un portacubiertos moleteado).

```
generadores/
  nucleo/      contornos, acabados, perfiles, divisores, base perforada,
               bandeja de goteo, malla, render y exportación a 3mf/stl
  disenos.py   las recetas y la declaración de parámetros
  crear.py     lo mismo que la pestaña Crear, pero por terminal
  rescatar.py  vuelve a generar un .3mf viejo midiendo su propia malla
```

### El .3mf se acuerda de cómo se hizo

Cada archivo que guarda el motor lleva sus parámetros adentro, como metadato
del 3MF —Bambu Studio los ignora sin quejarse—. Así, cuando el motor mejora,
volver a sacar una pieza es exacto y no hay nada que adivinar.

No siempre fue así, y de ahí sale `rescatar.py`: para los archivos de antes,
que son una malla y nada más. Mide la geometría y deduce con qué se hizo.

```bash
python3 generadores/rescatar.py "ruta/al/archivo.3mf"            # sólo informa
python3 generadores/rescatar.py "ruta/al/archivo.3mf" --escribir  # lo regenera
```

Sale exacto —comprobado contra piezas de parámetros conocidos— la planta, el
alto, la pared, el piso, el relieve, cuántas estrías hay, cuántos divisores y
de qué grosor, los agujeros del drenaje, y cuántas vueltas da la torsión. El
perfil vertical se ajusta contra la curva de radio por altura y **viene con
su error en milímetros**: por debajo de medio milímetro la silueta está
reconocida, y por encima el programa se niega a regenerar en vez de
inventarle una forma y devolver otra pieza con el mismo nombre.

Por defecto conserva el dibujo: ajusta el paso para que salgan las mismas
estrías que tenía. El original se respalda en una subcarpeta `_originales`,
que la galería no mira.

Tres cosas que costaron y que valen para cualquiera que mida una malla:

- **El nombre del archivo miente.** Uno llamado «ondas» resultó ser una
  torsión. El acabado se deduce proyectando cada anillo sobre la frecuencia
  de sus estrías y viendo si la fase se corre al subir; si se corre, es una
  hélice. Reconstruirlo por el nombre le habría enderezado el dibujo.
- **Las dos caras de la pared hay que emparejarlas bien.** Separarlas por
  radio no sirve: en un rectángulo, la esquina de adentro queda más lejos del
  centro que el lado de afuera. El emparejamiento bueno tampoco es el de
  espesor más parejo —el correcto varía a propósito lo que mide el relieve—
  sino el único donde la cara de adentro queda de verdad por dentro en todo
  el contorno.
- **Dónde termina el casco.** Después de los anillos vienen los divisores y
  la placa del piso, que no son anillos. Se distinguen porque un anillo es
  plano. Sin ese corte, la geometría de los divisores entraba en la curva de
  radio por altura, el ajuste del perfil fallaba por cuatro milímetros y una
  pieza perfectamente reconstruible parecía no serlo.

| Eje | Opciones |
|---|---|
| Contorno | círculo/elipse, rectángulo redondeado, óvalo, superelipse, hoja, arco de espalda plana, plegado, guijarro |
| Acabado | liso, ondulado, canal (cresta plana), facetado, torsión, escalonado, romboidal, junco, espiga, lino, martillado |
| Perfil | recto, orgánico, cónico, invertido, barril, campana, cintura |
| Fondo | canto vivo o redondeado, con el radio como parámetro |
| Divisores | de 1 a 8 ranuras por 1 a 6 filas, en rejilla, con canto en filo |
| Escalón | el frente más bajo que el fondo, con el corte donde tú lo pongas |
| Base | sólida o perforada (diámetro y separación de los agujeros) |
| Bandeja | sin bandeja o de goteo (sale como segunda pieza) |

### El reparto: la planta pone la arquitectura, el acabado pone la piel

Son dos decisiones distintas y conviene no mezclarlas. La planta se lee desde
el otro lado del cuarto y es lo que decide si la pieza parece cara: ahí no
entra el estilo, entra la contención. Curvatura continua, nada que el ojo
pueda contar, nada que se reconozca como figura. El estilo va en el acabado,
que es lo que se ve de cerca y lo que se toca.

Por eso las plantas empezaron siendo ocho y no quince. Salieron entonces el
polígono regular —el hexágono es la forma por defecto de todo lo impreso en
3D— y los pétalos, que leen a manualidad. Salió también el riñón: era la
misma familia que el guijarro (un redondo deformado por armónicos bajos), y
dos versiones de lo mismo en un catálogo es justo lo que lo abarata.

Ese razonamiento se escribió mirando el catálogo entero, preguntándose qué
siluetas hay. Las cinco de la segunda tanda salieron de otra pregunta —qué le
falta al portacontroles y al portacubiertos, que son las dos piezas que de
verdad se están fabricando— y tres de ellas son exactamente las que habían
salido. Vale la pena dejar dicho qué cambió y qué no:

- **El chaflán y el trapecio no discuten con nada.** No existían bajo ninguna
  forma y los dos sirven a una pieza dividida que se apoya en algo.
- **El polígono sigue teniendo el defecto que se le anotó** —el hexágono es
  lo que sale por defecto de una impresora— pero estirado a 145 × 66 con una
  faceta plana al frente ya no es el hexágono de un florero: es una caja con
  las puntas cortadas, y la faceta al frente es la que deja arrimarlo.
- **Los lóbulos leen a manualidad, y eso dejó de ser una objeción** cuando la
  pieza a la que se le ponen es un portacubiertos de cocina. En un florero
  sobraba; sobre la tarja, la cerámica prensada es justo el registro.
- **El riñón sigue siendo de la familia del guijarro, y eso es verdad.** Lo
  que lo separa es que su hendidura tiene función y posición: va centrada
  atrás, recibe la orilla de la tarja y el pulgar. La del guijarro es
  decorativa y va donde cae. Si al verlos juntos en el muestrario parecen lo
  mismo, el que sobra es el riñón y quitarlo es una línea.

Las plantas que no son la elipse ni el rectángulo:

- **Hoja** — la elipse llevada al otro lado de la superelipse. En vez de
  engordar hacia el rectángulo, adelgaza hacia la punta. El redondeo dice
  cuánto: en 0 las puntas quedan vivas, subiéndolo vuelve a ser elipse.
- **Arco de espalda plana** — el frente lleno y la espalda aplanada, para
  arrimar a la pared sin dejar el hueco en cuña que deja un redondo. La mitad
  de atrás es la misma curva, nada más que aplastada, así que llega al borde
  igual de vertical y la unión no tiene esquina. Se topa en 0.9 y no en 1:
  aplastada del todo, la espalda es una recta y llega horizontal al frente,
  y ahí sí aparecen dos escuadras.
- **Plegado** — pliegues rectos que alternan cresta y valle. Es el único
  relieve que puede ir hondo: un acabado está topado por el espesor de la
  pared, porque los divisores y el piso perforado tienen que quedar embebidos
  en el material, y un pliegue de planta se lleva la pared entera con él. La
  hondura es lo que separa el vidrio labrado de la estrella de navidad —hasta
  0.08 es una pieza acanalada, de 0.10 para arriba es otra cosa—, así que el
  parámetro se topa en 0.16.
- **Guijarro** — un redondo al que dos ondas largas le quitan la simetría. No
  hay eje ni repetición que el ojo pueda contar, y por eso se lee como piedra
  y no como pieza torneada. La irregularidad está escrita, no sorteada: el
  mismo diseño da siempre la misma piedra.

Y las cinco de la segunda tanda:

- **Rectángulo achaflanado** — las esquinas cortadas a bisel en vez de
  redondeadas. Donde el redondeo suaviza y desaparece, el corte recto deja
  una faceta que toma la luz distinto de las cuatro caras. El redondeo se lee
  aquí como el largo del corte, en milímetros, así que en 0 vuelve a ser un
  rectángulo de esquina viva.
- **Trapecio / cuña** — la espalda ancha y el frente angosto. Es la planta del
  portacontroles que no es una caja: con ranuras, los compartimentos salen en
  abanico y los controles se escalonan en vez de esconderse unos detrás de
  otros. Arrimada a la pared, deja el frente despejado.
- **Polígono facetado** — aristas verticales de verdad. La superelipse curva
  la pared y la luz resbala; el polígono la quiebra y cada faceta toma un
  tono. Los lados se acomodan con una faceta centrada al frente y otra atrás,
  que es lo que permite apoyarlo contra algo sin hueco en cuña.
- **Lobulado** — pétalos alrededor, arcos llenos y valles llenos, sin una
  sola arista. Los valles se reparten **por el perímetro** y se meten por la
  normal, no por el ángulo desde el centro: repartidos por ángulo, un óvalo
  de 134 × 76 se come la onda en los costados y la concentra en las puntas, y
  en vez de un trébol sale una pera. Van de dos en dos, porque la pieza tiene
  dos ejes de simetría y una corona impar deja un lóbulo en una punta y un
  valle en la otra — que es la misma pera por otro camino.
- **Riñón** — un óvalo con una hendidura suave en la espalda. Abraza una
  esquina, y en el fregadero recibe la orilla de la tarja; en la mesa deja
  meter el pulgar para levantarla con una mano. La muesca se apaga antes de
  llegar a los costados, para que no aparezca esquina viva en ningún punto.

Todas se ajustan al cuadro que pidas: la curva se recentra y se estira para
llenar justo el ancho y el fondo declarados, así que dos plantas distintas con
los mismos milímetros ocupan la misma huella en la mesa.

Ninguna pide soportes. Una planta es una extrusión vertical, así que lo que
hay que vigilar aquí no es el voladizo sino que la cara interior no se cruce
en un valle angosto, y de eso ya se encargaba el motor.

Un detalle que sólo aparece con las plantas cóncavas: un divisor se traza
cruzando la sección de pared a pared, y antes eso era «del mínimo al máximo».
En una planta convexa da lo mismo —la recta entra y sale una sola vez—, pero
en un lobulado la recta puede entrar, salir por un valle y volver a entrar, y
ahí el mínimo a máximo puentea el valle y el divisor asomaría por fuera de la
pared. Ahora se toma el tramo que de verdad tiene material.

### El muestrario: verlas antes de elegirlas

Con catorce plantas, elegir en una lista desplegable es elegir a ciegas. Leer
«Riñón» no contesta la única pregunta que importa, que es cómo se ve *tu*
portacubiertos en riñón.

El botón **▦ Verlas todas**, pegado al selector de planta, abre la misma pieza
repetida en todas las plantas: mismas medidas, mismo acabado, mismas ranuras,
mismo todo, y lo único que cambia es la silueta. Debajo de cada una va su peso,
que es lo que decide el costo — entre la planta más pesada y la más ligera hay
veinte gramos largos, y eso son pesos por pieza. Tocar una se la pone a la
pieza y cierra el muestrario.

Dos decisiones de cómo está hecho, por si hay que tocarlo:

- **Las miniaturas se calculan en grueso.** Lo que se juzga ahí es la silueta,
  no el acabado; de cerca ya está la vista previa grande. Eso baja cada una de
  tres cuartos de segundo a un cuarto. El peso de ese cálculo grueso se midió
  contra la malla final en las catorce plantas de las dos recetas y no se
  separa más de un gramo, así que se enseña con «≈» y no como número firme.
- **Se piden de una en una y la rejilla se va llenando**, en vez de esperar a
  las catorce. La primera aparece enseguida y para cuando el ojo llegó abajo
  ya están todas. Se guardan mientras no cambie nada más que la planta, así
  que volver a abrirlo es instantáneo.

### Los acabados

- **Junco** — cañas redondas separadas por pared lisa. No es la onda: la onda
  sube y baja sin descanso y de lejos se lee como textura pareja. Aquí la
  caña ocupa poco más de medio paso y entre caña y caña queda plano, así que
  la luz cae en una franja angosta y brillante por caña y el resto queda
  mate. De ahí saca el brillo el vidrio labrado. Es el único acabado que
  agrega peso en serio: no quita nada, sólo pone lomos.
- **Espiga** — el facetado quebrado en zigzag, en hileras de galones. El
  quiebre va en vertical, que es lo que ninguna máquina de revolución puede
  hacer, y por eso se lee como papel doblado y no como pieza torneada.
- **Lino** — dos ondas cruzadas sumadas, no multiplicadas: multiplicadas dan
  rombos y eso ya es el moleteado; sumadas dan hilo y pasada. Quiere paso
  corto, de 4 a 6 mm, y relieve bajo: en 0.7 mm se lee como tela, en 1.4 se
  vuelve una reja.
- **Martillado** — tres tramas que no encajan entre sí, sumadas. El dibujo
  tarda muchísimo en repetirse y el ojo no le encuentra la cuenta: cobre
  batido, barro apretado con el pulgar. Irregular a propósito y siempre el
  mismo, porque está escrito y no sorteado.

Las frecuencias que van a lo largo del contorno son enteras a la fuerza. El
contorno se cierra sobre sí mismo, y una onda que no dé un número entero de
vueltas deja un escalón en la costura.

### La resolución la pide el acabado, no un número fijo

Un acabado puede estar impecable como fórmula y salir mal en la pieza, y eso
pasaba: la resolución era un número fijo —480 puntos alrededor— que no tenía
nada que ver con el dibujo que se le estaba poniendo encima. El muestreador
reparte los puntos parejo a lo largo del contorno, así que 480 puntos con 31
estrías dan 15.48 puntos por estría. Como no es entero, cada estría cae con
una fase distinta: unas quedan muestreadas justo en la cresta y salen
completas, otras a medio flanco y salen mochas. **Nadie ve el número; todos
ven que unas estrías se ven distintas de otras.** Medido: el facetado perdía
hasta el 15 % de la punta en unas sí y en otras no, y el martillado hasta el
79 % de la hondura del hoyuelo.

Ahora cada acabado declara su propia geometría —cada cuánto se repite el
dibujo alrededor y a lo alto, y cuánto corre de lado mientras sube— y de ahí
sale la resolución de la pieza. Dos reglas:

- **Múltiplo entero y par de repeticiones.** Entero para que todas las
  estrías se muestreen igual; par para que la cresta y el valle caigan los
  dos sobre un punto. Es lo que hace que salgan idénticas entre sí.
- **Ninguna faceta más larga que el grano.** El grano es un parámetro nuevo,
  en milímetros, y es lo que decide cuánta malla se gasta. En 0.6 mm el
  relieve no se aparta del dibujo más de cinco centésimas de milímetro, que
  es la mitad de una capa impresa.

Los controles «Resolución del contorno» y «Capas verticales» pasaron a ser el
piso y no el techo: son lo que piden la planta y el perfil por su cuenta, y
el acabado sube desde ahí. El del contorno se sube al múltiplo aunque ya
alcance, porque tener puntos de sobra no sirve de nada si caen mal.

Lo que esto cuesta: un acabado sin relieve vertical sale igual de rápido que
antes, y uno que dibuja con la altura —lino, espiga, torsión, romboidal—
tarda entre cinco y diez segundos en guardarse en vez de dos. La vista previa
se sigue construyendo con grano grueso para que el deslizador siga siendo un
deslizador, pero con el mismo múltiplo: se ve roma, no se ve despareja, y el
peso que enseña es el que va a tener el archivo.

Los acabados que dibujan con la altura necesitan capas verticales de sobra o
el dibujo se corta en escalones, y la espiga y la torsión cerrada son las más
exigentes de todas: un galón y una hélice son diagonales, y la malla sólo
tiene anillos horizontales. Lo que manda ahí no es el alto de la capa sino
cuánto corre el dibujo de lado entre una capa y la siguiente. Una torsión de
vuelta entera sobre un contorno de 280 mm pide más de cuatrocientas capas, y
cuando lo que pide una pieza no cabe en un archivo razonable el motor engorda
el grano y lo dice, en vez de soltar el múltiplo y volver al acabado
desigual.

### El escalón y la rejilla

Los divisores eran ranuras paralelas en un solo sentido. Cruzándolos —ranuras
a lo ancho por filas a lo largo— salen compartimentos en rejilla, y con el
frente más bajo que el fondo la cubeta se vuelve un organizador: atrás paran
los cubiertos largos y adelante quedan huecos playos donde se ve lo que hay.

El escalón es altura por columna del contorno: cada columna remata donde le
toca y el casco se cierra igual. Los divisores lo respetan, y los que van a
lo largo cruzan el escalón, así que salen en dos tramos —alto atrás y bajo
adelante—; de una pieza sobresaldrían del frente.

### Lo que se ve caro

Las recetas de arranque tenían el relieve a 9-10 mm de paso: ocho o nueve
lóbulos gordos alrededor de un vaso de 76, y eso es exactamente lo que se lee
como plástico corrugado. Bajando el paso a 4 mm y la amplitud a medio
milímetro, la misma pieza —el mismo código, los mismos deslizadores— se lee
como cerámica acanalada. La regla, hasta donde he podido ver: **muchas
estrías finas y regulares se ven caras; pocas y gordas, baratas.** Y una
silueta esbelta ayuda más que cualquier textura: los vasos van a 70 de
diámetro por 110 de alto, no a 76 por 105.

Las tres recetas ya están así. Tardaron en estarlo: la regla llevaba tiempo
escrita aquí arriba y `DISENOS` seguía con el paso a 9-10 y el relieve a
1.0 mm, que es la versión que esta misma sección llama plástico corrugado.

| | Antes | Ahora |
|---|---|---|
| Portacontroles | 37 estrías de 10 mm, relieve 1.0 | 92 de 4 mm, relieve 0.5 |
| Portalápices | 78 × 78 × 95, 31 de 9 mm | 70 × 70 × 110, 63 de 4 mm |
| Portacubiertos | 35 estrías de 10 mm, relieve 1.0 | 79 de 4.5 mm, relieve 0.6 |

El portalápices baja de 61 a 60 g siendo 15 mm más alto, porque es más
esbelto. Los otros dos pesan igual que antes: una estría simétrica pone
arriba lo mismo que quita abajo, así que afinarla no cambia el material.

### La pared que queda en el valle

Hay un segundo motivo para no pasarse de relieve, y no es de gusto. La
estría va y viene alrededor de la pared nominal: sube la cresta hacia afuera
y **hunde el valle hacia adentro la misma cantidad**. Con pared de 1.6 mm y
relieve de 1.0, en cada valle quedaban 0.60 mm de material.

Eso está por debajo de dos perímetros de una boquilla de 0.4. El laminador no
puede meter dos hilos ahí, así que resuelve la línea con uno solo o con
relleno de hueco — y el resultado es una franja traslúcida, con costura y
floja, recorriendo la pieza justo por la línea que más se mira. Se veía como
un problema de acabado y era un problema de espesor.

El motor ahora topa el relieve en **pared − 0.8 mm** y lo avisa cuando
recorta. Antes topaba en pared − 0.4, que es exactamente un hilo: permitía el
defecto en vez de atajarlo.

El junco es la excepción y por eso cada acabado declara cuánto hunde: la caña
nace de la pared lisa y sube, nunca se mete. No tiene valle, así que puede ir
hondo sobre pared delgada sin que el motor lo recorte.

El acabado romboidal es la torsión multiplicada por sí misma al revés, que es
como se hace un moleteado. Como todo relieve que dibuja con la altura, las
capas que necesita se las pone el motor solo.

### La bandeja de goteo

Un vaso con drenaje pero sin bandeja no resuelve nada — nada más manda el
agua a la repisa. La bandeja es la misma silueta del vaso corrida
hacia afuera lo que miden la pared y la holgura, y sale como segunda pieza en
el mismo .3mf: se lamina de una y se puede imprimir de otro color.

Dos cosas que no son obvias:

- **Las costillas del fondo.** Sin ellas el vaso se queda parado dentro de su
  propia agua y no sirvió de nada haber drenado. Van de lado a lado pasando
  por el centro —dos hacen una cruz— para que el agua corra por debajo en vez
  de quedarse encharcada dentro de un anillo.
- **La bandeja se mide por lo más ancho del vaso, no por su base.** Con un
  perfil cónico o de barril la base es lo más angosto, y una bandeja hecha a
  esa medida le pega al vaso unos milímetros más arriba.

El fondo se cierra en abanico desde el centro y no con el triangulador
general. No es capricho: un rectángulo muestreado tiene tramos rectos llenos
de puntos casi colineales, y ahí el recorte de orejas se queda sin orejas que
cortar. Como todos los contornos del motor están escritos como radio en
función del ángulo, son estrellados respecto al centro y el abanico siempre
vale.

### El fondo redondeado

Es lo que separa una cubeta de una maceta: sin él, la pared se encuentra con
la base a 90° y la pieza se ve como un bote. El filete es un cuarto de
círculo **cortado**, no completo — uno entero arrancaría horizontal desde la
cama y sería imposible de imprimir.

En este filete el ángulo respecto a la vertical coincide con el ángulo del
arco, así que cortarlo controla directamente el voladizo. Y el corte se
ajusta solo: si el perfil ya aporta panza, el filete se acuesta menos para
que entre los dos no pasen de 45°.

Va aplicado como factor de escala, no como desplazamiento, para que la pared
conserve su espesor al curvarse.

El motor mide el voladizo de la pared y **avisa si la pieza va a pedir
soportes**. Con el perfil orgánico a intensidad máxima, avisa.

Desde la terminal:

```bash
python3 generadores/crear.py --listar
python3 generadores/crear.py portalapices --contorno origami --pliegues 10
```

`crear.py --help` lista todos los parámetros con su rango. Para agregar un
producto nuevo basta con sumar una entrada a `DISENOS` en `disenos.py`: la
pestaña Crear lo levanta sola.

El interior siempre queda liso aunque el exterior lleve relieve, y el
relieve se recorta solo si la pared no lo aguanta, para que los divisores y
el piso perforado siempre queden bien pegados a la pared.

## Uso

```bash
python3 catalog3d.py
```

Por defecto busca en `~/Desktop/own design 3d`. Para usar otra carpeta:

```bash
python3 catalog3d.py "/ruta/a/tu/carpeta"
```

Se abre solo en `http://127.0.0.1:8770/`. Para cerrar: `Ctrl+C` en la terminal.

## Requisitos

Solo Python 3 (librería estándar). No hay que instalar nada más.

Para el botón «Abrir en Bambu Studio» hace falta tener Bambu Studio
instalado en la misma máquina (macOS, Windows o Linux). Las rutas donde
lo busca están en `APPS_BAMBU`, arriba en `catalog3d.py`.
