#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Las recetas de la línea.

Como todos los productos son el mismo primitivo (contorno + acabado +
perfil + divisores + base), una receta no es código: son los valores con los
que arranca. Para agregar un producto nuevo basta con sumar una entrada a
DISENOS; la pestaña «Crear» lo levanta sola. Dos recetas con la misma forma y
distinto paso de estría son dos productos distintos, y eso es a propósito.

Cada parámetro se declara con etiqueta, rango y grupo, y eso es lo que lee la
interfaz para dibujar los controles.
"""

import re

from nucleo.acabados import ACABADOS
from nucleo.contornos import CONTORNOS
from nucleo.borde import BORDES
from nucleo.cuello import CUELLOS
from nucleo.perfiles import PERFILES


def num(clave, etiqueta, valor, minimo, maximo, paso=1.0, unidad="mm",
        grupo="Medidas", depende=None, ayuda=""):
    return {"clave": clave, "etiqueta": etiqueta, "tipo": "num", "valor": valor,
            "min": minimo, "max": maximo, "paso": paso, "unidad": unidad,
            "grupo": grupo, "depende": depende, "ayuda": ayuda}


def opcion(clave, etiqueta, valor, tabla, grupo="Forma", depende=None, ayuda=""):
    return {"clave": clave, "etiqueta": etiqueta, "tipo": "opcion", "valor": valor,
            "opciones": [{"clave": k, "etiqueta": v[0]} for k, v in tabla.items()],
            "unidad": "", "grupo": grupo, "depende": depende, "ayuda": ayuda}


def trazo(clave, etiqueta, grupo="Forma", depende=None, ayuda=""):
    """Una silueta sacada de una imagen, guardada como texto.

    No es un control que se mueva: la pestaña no le dibuja deslizador, lo
    enseña como miniatura. Viaja dentro de los valores como cualquier otro
    parámetro para no tener que inventarle un registro aparte al servidor.
    """
    return {"clave": clave, "etiqueta": etiqueta, "tipo": "trazo", "valor": "",
            "unidad": "", "grupo": grupo, "depende": depende, "ayuda": ayuda}


# Lo que se acepta como trazo: base64 y nada más. Termina en zlib.decompress,
# así que conviene acotarlo antes y no después.
TRAZO_LARGO_MAX = 4096
_BASE64 = re.compile(r"[A-Za-z0-9+/]*={0,2}")


# Cómo es la cara interior de la pared. «Lisa» es la de siempre: el relieve queda
# sólo por fuera y el espesor oscila. «Sigue el relieve» copia la onda por
# dentro, y el espesor queda parejo — lo que el laminador imprime sin cambiar
# de dos hilos a relleno en cada cresta.
PAREDES = {"lisa": ("Lisa por dentro",), "sigue": ("Sigue el relieve",)}

MATERIALES = {"PLA": ("PLA",), "PETG": ("PETG",), "ABS": ("ABS",), "TPU": ("TPU",)}

# Por ahora sólo la de goteo. Sale como segunda pieza en el mismo archivo.
# Cómo va el tabique de pared a pared: plano, o ondulado con la pieza.
DIVISORES = {"recto": ("Recto",), "ola": ("En ola",)}

BANDEJAS = {"ninguna": ("Sin bandeja",), "goteo": ("De goteo",)}

PARAMETROS = [
    opcion("contorno", "Planta", "rectangulo", CONTORNOS, "Forma",
           ayuda="La silueta vista desde arriba. Es lo que más cambia la pieza: el acabado se nota de cerca, la planta se lee de lejos."),
    trazo("trazo", "Silueta de la imagen", "Forma", depende=["trazado"],
          ayuda="La planta trazada de una imagen, guardada como radio en "
                "función del ángulo. Sin ella, el contorno «trazado» sale "
                "redondo."),
    num("ancho", "Ancho", 132, 30, 260, 1, "mm", "Forma"),
    num("fondo", "Fondo", 66, 30, 260, 1, "mm", "Forma"),
    num("alto", "Alto", 88, 20, 250, 1, "mm", "Forma"),
    num("redondeo", "Redondeo de esquina", 16, 0, 80, 0.5, "mm", "Forma",
        depende=["rectangulo", "chaflan", "trapecio", "superelipse",
                 "poligono", "hoja"],
        ayuda="En el rectángulo, el trapecio y el polígono son milímetros de "
              "radio. En el chaflán es el largo del corte a bisel. En la hoja "
              "no redondea una esquina: afila o desafila la punta."),
    num("trapecio_cierre", "Cierre del frente", 0.30, 0.0, 0.75, 0.05, "",
        "Forma", depende=["trapecio"],
        ayuda="Cuánto se angosta el frente respecto a la espalda. En 0 es un "
              "rectángulo; en 0.5 el frente mide la mitad y los "
              "compartimentos salen claramente en abanico."),
    num("lados", "Lados", 6, 3, 12, 1, "", "Forma", depende=["poligono"],
        ayuda="Seis es el hexágono, que es el que más se lee como pieza "
              "diseñada. Pasando de nueve las aristas se juntan tanto que la "
              "pared vuelve a parecer curva y la faceta se pierde."),
    num("arco_plano", "Aplanado de la espalda", 0.6, 0.0, 0.9, 0.05, "",
        "Forma", depende=["arco"],
        ayuda="Cuánto se aplana la espalda para arrimarse a la pared. Se "
              "topa en 0.9: recta del todo, la espalda llega horizontal al "
              "frente y salen dos escuadras."),
    num("pliegues", "Pliegues", 9, 3, 16, 1, "", "Forma", depende=["plegado"],
        ayuda="Cada pliegue son dos facetas: una cresta y un valle."),
    num("pliegue_profundidad", "Hondura del pliegue", 0.07, 0.02, 0.16, 0.01,
        "", "Forma", depende=["plegado"],
        ayuda="Qué tanto se mete el valle. Hasta 0.08 es una pieza acanalada; "
              "de 0.10 para arriba deja de parecer vidrio labrado y empieza a "
              "parecer estrella."),
    num("lobulos", "Lóbulos", 6, 4, 12, 2, "", "Forma", depende=["lobulos"],
        ayuda="Cuántos pétalos se reparten alrededor. Van de dos en dos: la "
              "pieza tiene dos ejes de simetría y una corona impar deja un "
              "lóbulo en una punta y un valle en la otra, que sale en forma "
              "de pera. Cuatro es un trébol ancho; de ocho para arriba se lee "
              "como pieza torneada."),
    num("lobulo_hondura", "Hondura del lóbulo", 0.22, 0.0, 0.45, 0.01, "",
        "Forma", depende=["lobulos"],
        ayuda="Qué tanto se meten los valles. Abajo de 0.06 no se distingue "
              "de un óvalo; arriba de 0.30 con muchos lóbulos el valle se "
              "cierra tanto que el motor avisa de que la pared se cruza."),
    num("rinon_hendidura", "Hendidura de la espalda", 0.32, 0.0, 0.45, 0.01,
        "", "Forma", depende=["rinon"],
        ayuda="Cuánto se mete la muesca de atrás. 0.20 es la que la mano "
              "agarra sin pensarlo; pasando de 0.30 la pieza empieza a "
              "abrazar una esquina de verdad y el motor puede avisar."),
    num("guijarro_irregular", "Irregularidad", 0.18, 0.0, 0.30, 0.01, "",
        "Forma", depende=["guijarro"],
        ayuda="Cuánto se sale del redondo. Abajo de 0.10 no se distingue de "
              "un óvalo; pasando de 0.25 se vuelve un bollo."),
    opcion("acabado", "Acabado", "ondulado", ACABADOS, "Acabado",
           ayuda="El relieve de la pared exterior. Por dentro siempre queda liso."),
    num("onda_amplitud", "Relieve", 0.5, 0.0, 3.0, 0.1, "mm", "Acabado",
        depende=["ondulado", "canal", "facetado", "torsion", "torsion_lado",
                 "escalonado", "rombo", "junco", "espiga", "lino",
                 "martillado", "meandro"],
        ayuda="Cuánto sobresale la estría. Como el valle se mete lo mismo que "
              "sube la cresta, el motor lo topa en pared − 0.8 mm: por debajo "
              "de eso el laminador no mete dos hilos en el valle y la pieza "
              "sale traslúcida ahí. El junco es la excepción —sólo pone "
              "lomos, no quita nada— y puede ir hondo sobre pared delgada."),
    opcion("pared_forma", "Cara interior", "lisa", PAREDES, "Acabado",
           depende=["ondulado", "canal", "facetado", "torsion", "torsion_lado",
                    "escalonado", "rombo", "espiga", "lino", "martillado"],
           ayuda="«Sigue el relieve» copia la onda por dentro y deja la pared "
                 "del mismo espesor en todas partes: sin cambios de dos hilos "
                 "a relleno en las crestas, que es donde salen los hilos "
                 "sueltos al imprimir. Pide pared de 4 perímetros (1.7 mm)."),
    num("pared_copia", "Relieve por dentro", 1.0, 0.0, 1.0, 0.05, "×", "Acabado",
        depende=["ondulado", "canal", "facetado", "torsion", "torsion_lado",
                 "escalonado", "rombo", "espiga", "lino", "martillado"],
        ayuda="Con «Sigue el relieve», qué fracción de la onda se copia por "
              "dentro. En 1 la pared mide lo mismo en todas partes; más "
              "abajo la cara interior queda más suave, y es lo que deja "
              "una pared gruesa con estría fina sin que se pliegue. Con "
              "«Lisa por dentro» no hace nada."),
    num("onda_paso", "Paso de la estría", 10.0, 3.0, 40.0, 0.5, "mm", "Acabado",
        depende=["ondulado", "canal", "facetado", "torsion", "torsion_lado",
                 "escalonado", "rombo", "junco", "espiga", "lino",
                 "martillado"],
        ayuda="De cuánto en cuánto se repite el dibujo. El lino lo quiere "
              "corto —4 a 6 mm— o los hilos se separan y deja de ser tela."),
    num("torsion_vueltas", "Vueltas de torsión", 0.15, -1.0, 1.0, 0.05, "",
        "Acabado", depende=["torsion", "torsion_lado"]),
    num("meandro_paso", "Paso del lóbulo (lóbulo + surco)", 60.0, 20.0, 120.0,
        1.0, "mm", "Acabado", depende=["meandro"]),
    num("meandro_surco", "Ancho del surco", 0.30, 0.05, 0.80, 0.05, "×",
        "Acabado", depende=["meandro"],
        ayuda="Qué parte del paso es surco. Bajo, los lóbulos casi se tocan."),
    num("meandro_cintura", "Bulbo del lóbulo", 0.35, 0.0, 0.7, 0.05, "",
        "Acabado", depende=["meandro"],
        ayuda="Cuánto engorda el bulbo y se angosta el cuello. Un lóbulo lleva "
              "el bulbo arriba y su vecino abajo; en 0 son franjas rectas."),
    num("meandro_vaiven", "Vaivén de lado", 0.0, 0.0, 0.25, 0.01, "×",
        "Acabado", depende=["meandro"],
        ayuda="Corre los lóbulos de lado al subir, uno hacia cada lado."),
    num("meandro_canto", "Redondez del canto", 4.0, 0.5, 12.0, 0.5, "mm",
        "Acabado", depende=["meandro"]),
    num("meandro_pie", "Pie liso", 6.0, 0.0, 30.0, 1.0, "mm", "Acabado",
        depende=["meandro"],
        ayuda="Milímetros lisos sobre la base, donde el lóbulo se cierra."),
    num("acabado_desvanece", "Alisa hacia la boca", 0.0, 0.0, 40.0, 1.0, "mm",
        "Acabado",
        depende=["ondulado", "canal", "facetado", "torsion", "torsion_lado",
                 "escalonado", "rombo", "junco", "espiga", "lino",
                 "martillado", "meandro"],
        ayuda="Cuántos milímetros, medidos desde la boca hacia abajo, se "
              "alisan sin importar el acabado elegido. En 0 el relieve llega "
              "hasta el labio y puede dejarlo mordido, sobre todo con "
              "torsión; con 10-15 mm la boca sale lisa y el resto de la "
              "pared conserva el relieve entero."),

    num("acabado_cierre", "Cierra hacia las crestas", 0.0, 0.0, 1.0, 0.05, "×",
        "Acabado",
        depende=["ondulado", "canal", "facetado", "torsion", "torsion_lado",
                 "escalonado", "rombo", "junco", "espiga", "lino",
                 "martillado", "meandro"],
        ayuda="Con «Alisa hacia la boca», a dónde se lleva el relieve. En 0 "
              "se alisa a la pared nominal; en 1 sube a ras de las crestas y "
              "los surcos terminan contra un aro liso en la boca."),

    opcion("cuello", "Cuello", "ninguno", CUELLOS, "Cuello",
           ayuda="Cómo se cierra la pieza hacia la boca. Es lo que separa un "
                 "vaso de un jarrón, y es una decisión distinta de la del "
                 "perfil: el perfil pone la panza, el cuello pone la boca."),
    num("boca", "Boca", 1.00, 0.25, 1.00, 0.05, "×", "Cuello",
        depende=["suave", "abrupto", "botella"],
        ayuda="Cuánto mide la boca comparada con la panza. En 1 no hay cuello; "
              "abajo de 0.4 la pieza deja de servir para meter cosas y pasa a "
              "ser un jarrón de tallo."),
    num("cuello_hombro", "Altura del hombro", 0.60, 0.30, 0.95, 0.05, "×",
        "Cuello", depende=["suave", "abrupto", "botella"],
        ayuda="Desde qué fracción de la altura empieza a cerrarse. Cuanto más "
              "arriba, más rápido tiene que cerrar para llegar a la misma "
              "boca, y antes pide soportes."),

    opcion("perfil", "Perfil vertical", "recto", PERFILES, "Perfil"),
    num("perfil_intensidad", "Intensidad del perfil", 0.12, 0.0, 0.35, 0.01, "",
        "Perfil", depende=["conico", "invertido", "barril", "campana", "cintura",
                           "oleaje"],
        ayuda="Arriba de 0.25 empieza a pedir soportes. En el oleaje cuenta "
              "doble, porque cada panza tiene un lado de abajo: de 0.08 para "
              "arriba revisa el aviso de voladizo."),
    num("oleaje_ondas", "Panzas", 2.0, 1.0, 4.0, 0.5, "", "Perfil",
        depende=["oleaje"],
        ayuda="Cuántas panzas caben en la altura. Dos es la maceta de la "
              "foto; con tres o más la pared ya no se lee como tela sino "
              "como acordeón, y cada panza pide su propio voladizo."),
    num("oleaje_inclinacion", "Ladeo de la panza", 0.10, 0.0, 0.25, 0.01, "",
        "Perfil", depende=["oleaje"],
        ayuda="Cuánto se ladea cada panza, en fracción de la altura. En 0 son "
              "anillos parejos —un barril de varios pisos—; hacia 0.12 se ve "
              "torcida; pasando de 0.20 una panza alcanza a la siguiente."),
    num("oleaje_reparto", "Pliegues desde los extremos", 0.0, 0.0, 1.0, 0.05,
        "", "Perfil", depende=["oleaje"],
        ayuda="En 0 cada panza le da la vuelta completa a la pieza. En 1 los "
              "pliegues nacen en los dos extremos, bajan en curva hacia el "
              "centro y se apagan antes de juntarse: el frente queda liso al "
              "medio, como tela que cuelga de las dos puntas. Aquí el ladeo "
              "es cuánto baja el pliegue hasta el centro."),
    num("oleaje_desfase", "Altura de las crestas", 0.0, 0.0, 1.0, 0.05, "",
        "Perfil", depende=["oleaje"],
        ayuda="Corre todas las panzas hacia abajo, en fracción de una panza. "
              "Sirve para que una cresta caiga justo donde se quiere —por "
              "ejemplo, que el último pliegue nazca en la boca."),
    num("oleaje_variacion", "Pliegues distintos", 0.0, 0.0, 1.0, 0.05, "",
        "Perfil", depende=["oleaje"],
        ayuda="Con pliegues desde los extremos: en 0 todos iguales y en "
              "espejo; hacia 1 cada uno arranca a su altura, cae distinto y "
              "se extiende o se corta por su cuenta."),
    num("oleaje_gancho", "Pliegue en gancho", 0.0, 0.0, 1.0, 0.05, "",
        "Perfil", depende=["oleaje"],
        ayuda="Dónde cae el pliegue. En 0 baja fuerte al salir del extremo y "
              "se va tendiendo hacia el centro; en 1 sale casi plano y se "
              "clava hacia abajo al final, apuntando al piso."),
    num("oleaje_semilla", "Sorteo de pliegues", 0, 0, 999, 1, "",
        "Perfil", depende=["oleaje"],
        ayuda="Cambia cuáles pliegues salen largos o cortos sin tocar lo "
              "demás. El mismo número da siempre la misma pieza."),
    num("oleaje_giro", "Giro del ladeo", 0.5, -1.0, 1.0, 0.05, "vueltas",
        "Perfil", depende=["oleaje"],
        ayuda="Hacia dónde se ladea cada panza conforme sube. En 0 todas "
              "miran al mismo lado; en 0.5 la de arriba mira al lado "
              "contrario de la de abajo, que es lo que la hace ver retorcida."),

    num("oleaje_m", "Cresta en M", 0.0, 0.0, 0.30, 0.01, "",
        "Perfil", depende=["oleaje"],
        ayuda="Hunde la cresta de cada panza al centro del frente y de la "
              "espalda, y la deja alta en los extremos, como la parte de "
              "arriba de una M. Se apaga en la boca y en la base. Pasando de "
              "0.25 el voladizo se dispara: baja la intensidad del perfil."),
    num("oleaje_m_ancho", "Ancho del hundido de la M", 0.35, 0.10, 1.0, 0.05,
        "", "Perfil", depende=["oleaje"],
        ayuda="Qué tanto del frente ocupa el hundido de la M. Chico es un "
              "pico angosto al centro; hacia 1 baja casi todo el frente y "
              "solo las puntas quedan altas."),

    num("base_redondeo", "Redondeo del fondo", 0.0, 0.0, 70.0, 1.0, "mm",
        "Perfil",
        ayuda="Suaviza el canto de abajo. Es la diferencia entre una cubeta y "
              "una maceta. Imprime sin soportes: el filete va cortado a 45° y "
              "deja asiento plano."),

    num("pared", "Pared", 1.6, 0.8, 4.0, 0.1, "mm", "Estructura"),
    num("piso", "Piso", 2.4, 0.8, 6.0, 0.1, "mm", "Estructura"),
    num("ranuras", "Ranuras", 4, 1, 8, 1, "", "Estructura",
        ayuda="Divisiones a lo ancho. 1 = sin divisores."),
    num("filas", "Filas", 1, 1, 6, 1, "", "Estructura",
        ayuda="Divisiones a lo largo. Con ranuras y filas a la vez, los "
              "compartimentos salen en rejilla en vez de en tiras."),
    num("divisor_grosor", "Grosor del divisor", 1.6, 0.8, 4.0, 0.1, "mm",
        "Estructura"),
    num("divisor_alto", "Alto del divisor", 60, 5, 250, 1, "mm", "Estructura"),
    opcion("divisor_forma", "Forma del divisor", "recto", DIVISORES, "Estructura",
           ayuda="«En ola» corre el tabique de lado siguiendo las panzas de "
                 "la pared, con los extremos quietos donde la toca. Con el "
                 "perfil oleaje se ve como parte de la misma tela."),
    num("divisor_ola", "Vaivén del divisor", 4.0, 0.0, 12.0, 0.5, "mm",
        "Estructura", depende=["ola"],
        ayuda="Cuánto se sale de la recta a media longitud. Hasta 6 mm no "
              "estorba a los cubiertos; arriba de eso el hueco de un lado se "
              "angosta a la altura de la panza."),
    num("divisor_chaflan", "Filo del divisor", 0.8, 0.0, 4.0, 0.1, "mm",
        "Estructura"),
    num("escalon", "Alto del frente", 1.0, 0.25, 1.0, 0.05, "×", "Estructura",
        ayuda="Qué fracción del alto mide la parte de adelante. En 1 la pieza "
              "es pareja; bajándolo, atrás quedan los huecos altos para lo "
              "largo y adelante los playos."),
    num("escalon_frente", "Parte que baja", 0.5, 0.0, 0.8, 0.05, "", "Estructura",
        ayuda="Qué tanto del fondo se queda bajo. En 0 no hay escalón. "
              "Conviene que caiga donde va un divisor."),

    opcion("borde", "Borde", "recto", BORDES, "Borde",
           ayuda="Hasta dónde sube el labio. Es lo primero que mira el ojo y "
                 "hasta ahora era el mismo aro horizontal en todas las piezas."),
    num("borde_hondura", "Hondura del recorte", 0.18, 0.0, 0.45, 0.01, "×",
        "Borde", depende=["diagonal", "ondulado", "petalos"],
        ayuda="Qué fracción de la altura baja el punto más bajo del labio. "
              "En 0 el borde vuelve a ser recto."),
    num("borde_ondas", "Ondas del borde", 6, 2, 16, 1, "", "Borde",
        depende=["ondulado", "petalos"],
        ayuda="Cuántas se reparten alrededor. Enteras a la fuerza: el contorno "
              "se cierra sobre sí mismo y media onda dejaría un escalón."),
    num("borde_rumbo", "Rumbo del corte", 0, 0, 360, 15, "°", "Borde",
        depende=["diagonal"],
        ayuda="Hacia dónde mira la parte alta del corte."),

    num("drenaje_diametro", "Diámetro del agujero", 0.0, 0.0, 12.0, 0.5, "mm",
        "Drenaje", ayuda="0 = piso sólido, sin drenaje."),
    num("drenaje_separacion", "Separación entre agujeros", 12.0, 4.0, 40.0, 0.5,
        "mm", "Drenaje"),

    opcion("bandeja", "Bandeja", "ninguna", BANDEJAS, "Bandeja",
           ayuda="Un plato con reborde donde se para el vaso. Recoge lo que "
                 "escurre por el drenaje y se levanta para vaciarlo. Sale "
                 "como segunda pieza en el mismo .3mf."),
    num("bandeja_alto", "Alto de la bandeja", 16.0, 8.0, 40.0, 0.5, "mm",
        "Bandeja", depende=["goteo"]),
    num("bandeja_holgura", "Holgura del vaso", 0.6, 0.2, 2.0, 0.1, "mm",
        "Bandeja", depende=["goteo"],
        ayuda="Lo que le sobra al vaso por cada lado. 0.6 entra y sale sin "
              "juego; súbele si tu impresora saca las piezas gordas."),
    num("bandeja_costillas", "Costillas del fondo", 2, 0, 4, 1, "", "Bandeja",
        depende=["goteo"],
        ayuda="Barras de lado a lado que levantan el vaso sobre el charco. "
              "Dos hacen una cruz. En cero, el vaso se queda parado dentro "
              "del agua."),

    opcion("material", "Material", "PLA", MATERIALES, "Cálculo",
           ayuda="Solo cambia el peso estimado."),
    num("grano", "Finura del acabado", 0.6, 0.3, 2.0, 0.05, "mm", "Cálculo",
        ayuda="Lo más largo que se le permite medir a una faceta del relieve. "
              "Es lo que decide la resolución de la pieza: el motor parte el "
              "dibujo hasta que ninguna faceta pase de aquí. Bajarlo afina el "
              "acabado y engorda el archivo; arriba de 1 mm se empieza a "
              "notar facetado en las estrías redondas."),
    num("segmentos", "Resolución mínima del contorno", 480, 120, 900, 20, "",
        "Cálculo",
        ayuda="El piso, no el techo: es lo que pide la planta por sí sola. El "
              "acabado sube desde aquí hasta los puntos que necesite, "
              "siempre en múltiplo entero de estrías para que salgan todas "
              "iguales."),
    num("capas", "Capas verticales mínimas", 64, 8, 220, 4, "", "Cálculo",
        ayuda="Las que pide el perfil vertical para salir liso. Si el acabado "
              "también dibuja con la altura, el motor pone las que le hagan "
              "falta: el lino, la espiga y la torsión cerrada piden muchas "
              "más que éstas."),
]

DEFECTOS = {p["clave"]: p["valor"] for p in PARAMETROS}


# Las tres recetas siguen la regla que el README ya tenía escrita y que ellas
# no habían alcanzado: estrías finas y regulares en vez de pocas y gordas, y
# silueta esbelta antes que textura. El paso bajó de 9-10 mm a 4-4.5 y el
# relieve de 1.0 mm a medio, que es la diferencia entre plástico corrugado y
# cerámica acanalada; el vaso pasó de 78 × 95 a 70 × 110.
#
# El relieve no bajó sólo por cómo se ve. A 1.0 mm sobre pared de 1.6, el
# valle de cada estría dejaba 0.60 mm de material —un solo hilo de boquilla—
# y ahí la pieza sale traslúcida y con costura. A medio milímetro quedan 1.1.
#
# El filete del fondo es la única de estas decisiones que no arregla un
# defecto: es de gusto, y es la que conviene revisar si no convence. Suaviza
# el canto de abajo —lo que el README llama la diferencia entre una cubeta y
# una maceta— y de paso se lleva el borde aserrado que dejan 92 estrías finas
# al morir de golpe contra la base. Imprime sin soportes y pesa un gramo
# menos. Poniéndolo en 0 la pieza vuelve al canto vivo.
DISENOS = [
    {
        "clave": "portacontroles",
        "nombre": "Portacontroles",
        "descripcion": "Cuatro ranuras para los controles de la sala.",
        "carpeta": "Porta controles",
        "valores": {
            "contorno": "rectangulo", "ancho": 145, "fondo": 66, "alto": 88,
            "redondeo": 16, "acabado": "ondulado", "onda_amplitud": 0.5,
            "onda_paso": 4.0, "pared": 2.0, "piso": 2.0, "ranuras": 4,
            "divisor_grosor": 1.3, "divisor_alto": 60, "drenaje_diametro": 0.0,
            "base_redondeo": 10, "grano": 0.4, "segmentos": 600,
        },
    },
    {
        "clave": "portalapices",
        "nombre": "Portalápices",
        "descripcion": "Vaso de escritorio, ligeramente cónico.",
        "carpeta": "PortaLapices",
        "valores": {
            "contorno": "superelipse", "ancho": 70, "fondo": 70, "alto": 110,
            "redondeo": 23, "acabado": "ondulado", "onda_amplitud": 0.5,
            "onda_paso": 4.0, "perfil": "conico", "perfil_intensidad": 0.12,
            "pared": 1.6, "piso": 2.4, "ranuras": 1, "drenaje_diametro": 0.0,
            "base_redondeo": 10,
        },
    },
    {
        "clave": "portacubiertos",
        "nombre": "Portacubiertos",
        "descripcion": "Tres compartimentos y drenaje, para el fregadero.",
        "carpeta": "portacubiertos",
        "valores": {
            "contorno": "ovalo", "ancho": 134, "fondo": 76, "alto": 112,
            "acabado": "ondulado", "onda_amplitud": 0.6, "onda_paso": 4.5,
            "pared": 1.8, "piso": 2.0, "ranuras": 3, "divisor_grosor": 1.6,
            "divisor_alto": 78, "drenaje_diametro": 5.0, "drenaje_separacion": 13.0,
            "base_redondeo": 8,
        },
    },
    {
        # La pieza de la foto del 2026-10-18: óvalo con estría vertical, dos
        # panzas ladeadas con la cresta en «M» y cuatro compartimentos. Es la
        # v2 de la receta rápida: pared 1.95 para que el hilo de 0.62 en una
        # vuelta se toque en el valle de la estría (ver el registro en
        # .claude/optimizaciones/portacubiertos-oleaje-m.md).
        "clave": "portacubiertos_oleaje_m",
        "nombre": "Portacubiertos Oleaje M",
        "descripcion": "Óvalo con estría y dos panzas en «M», cuatro compartimentos.",
        "carpeta": "portacubiertos",
        "valores": {
            "contorno": "superelipse", "ancho": 180, "fondo": 102,
            "redondeo": 47, "alto": 115, "acabado": "ondulado",
            "onda_amplitud": 0.7, "onda_paso": 3.6, "acabado_desvanece": 6,
            "acabado_cierre": 1.0, "perfil": "oleaje",
            "perfil_intensidad": 0.064, "oleaje_ondas": 2,
            "oleaje_inclinacion": 0.04, "oleaje_giro": 0.5,
            "oleaje_desfase": 0.8, "oleaje_m": 0.23, "oleaje_m_ancho": 0.40,
            "pared": 1.95, "piso": 1.2, "ranuras": 2, "filas": 2,
            "divisor_grosor": 2.0, "divisor_alto": 75, "divisor_forma": "ola",
            "divisor_ola": 3.0, "drenaje_diametro": 0.0, "base_redondeo": 6,
            "grano": 0.6, "segmentos": 600,
        },
    },
    {
        # La pieza de la foto del 2026-10-22: óvalo en barrilito con lóbulos
        # abultados que se alternan —bulbo arriba, el vecino bulbo abajo— y
        # tres compartimentos con divisores hasta la boca. v1 aprobada en
        # precheck (ver .claude/optimizaciones/portacubiertos-meandro.md).
        "clave": "portacubiertos_meandro",
        "nombre": "Portacubiertos Meandro",
        "descripcion": "Óvalo en barril con lóbulos alternados, tres compartimentos.",
        "carpeta": "portacubiertos",
        "valores": {
            "contorno": "superelipse", "ancho": 188, "fondo": 88, "alto": 112,
            "redondeo": 34, "perfil": "barril", "perfil_intensidad": 0.07,
            "acabado": "meandro", "onda_amplitud": 4.2, "meandro_paso": 52,
            "meandro_surco": 0.32, "meandro_cintura": 0.45,
            "meandro_canto": 4.5, "meandro_pie": 7, "pared": 1.8, "piso": 1.4,
            "ranuras": 3, "divisor_grosor": 2.4, "divisor_alto": 112,
            "divisor_forma": "ola", "divisor_ola": 3, "drenaje_diametro": 0.0,
            "base_redondeo": 8, "grano": 0.7, "segmentos": 480,
        },
    },
    {
        # Donde aterriza una idea que no es ninguno de los productos de arriba.
        # No trae valores propios a propósito: los pone quien la describa.
        "clave": "libre",
        "nombre": "Pieza libre",
        "descripcion": "Lo que salga de una idea, sin receta de por medio.",
        "carpeta": "Ideas",
        "valores": {},
    },
]

POR_CLAVE = {d["clave"]: d for d in DISENOS}


def parametros_de(clave):
    """Los parámetros con los valores de arranque de ese diseño."""
    valores = dict(DEFECTOS)
    valores.update(POR_CLAVE[clave]["valores"])
    return valores


def normalizar(entrada):
    """Completa lo que falte y recorta los números a su rango."""
    p = dict(DEFECTOS)
    for spec in PARAMETROS:
        c = spec["clave"]
        if c not in entrada:
            continue
        if spec["tipo"] == "num":
            try:
                v = float(entrada[c])
            except (TypeError, ValueError):
                continue
            p[c] = max(spec["min"], min(spec["max"], v))
        elif spec["tipo"] == "trazo":
            v = entrada[c]
            if (isinstance(v, str) and len(v) <= TRAZO_LARGO_MAX
                    and _BASE64.fullmatch(v)):
                p[c] = v
        else:
            claves = [o["clave"] for o in spec["opciones"]]
            if entrada[c] in claves:
                p[c] = entrada[c]
    return p


def nombre_sugerido(clave, p):
    acabado = dict(ACABADOS)[p["acabado"]][0]
    # Cada palabra con mayúscula en vez de pegarlas a secas: con recetas de
    # varias palabras, «Portacepillos en torsión» salía «Portacepillosentorsión».
    nombre = POR_CLAVE[clave]["nombre"] if clave in POR_CLAVE else "Diseño"
    base = "".join(w[:1].upper() + w[1:] for w in nombre.split())
    partes = [base, acabado]
    if p["ranuras"] > 1:
        partes.append("%dranuras" % int(p["ranuras"]))
    return "_".join(partes).replace(" ", "")
