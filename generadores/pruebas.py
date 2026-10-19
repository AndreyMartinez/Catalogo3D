#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Las pruebas del generador. Sólo librería estándar, como todo lo demás.

    python3 -m unittest generadores.pruebas          (desde la raíz)
    python3 generadores/pruebas.py                   (equivalente)

Corren en frío: sin red, sin API key y sin archivos de apoyo en el
repositorio. Lo que haga falta se sintetiza aquí mismo.

La primera clase es la que importa más y por eso va primero. `LineaBase`
guarda lo que el motor produce hoy, antes de que la pestaña «Idea» le agregue
un contorno y un parámetro. Los números de abajo no se calcularon a mano: se
midieron con el motor tal como estaba, y su único trabajo es avisar si un
cambio pensado para las piezas nuevas movió una pieza vieja.

Si una prueba de esta clase falla, la pregunta no es qué número actualizar,
sino qué se rompió.
"""

import base64
import math
import sys
import unittest
import zlib
from pathlib import Path

# Los módulos del generador se importan entre sí en plano («from nucleo…»),
# que es como los arranca crear.py. Sin esto, sólo funcionaría corriendo el
# archivo desde dentro de la carpeta.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import disenos                                  # noqa: E402
from nucleo import cuerpo                       # noqa: E402
from nucleo import trazo as T                   # noqa: E402
from nucleo import borde as BO                   # noqa: E402
from nucleo.contornos import muestrear           # noqa: E402
from nucleo.cuello import CUELLOS                # noqa: E402
from nucleo.contornos import CONTORNOS, circulo  # noqa: E402
from nucleo.acabados import ACABADOS             # noqa: E402
from nucleo.perfiles import PERFILES             # noqa: E402


# Cada receta: (vértices, triángulos, gramos). Se volvieron a medir cuando
# las recetas alcanzaron las reglas que el README ya tenía escritas y ellas
# no cumplían. Queda anotado aquí porque ésta es la clase donde un número que
# se mueve solo es una alarma, y conviene saber cuál fue la última vez que se
# movió por buenas razones:
#
#  - Estrías finas en vez de gordas: el paso bajó de 9-10 mm a 4-4.5.
#  - Relieve de medio milímetro en vez de uno entero. No es sólo estética: a
#    1.0 mm sobre pared de 1.6, el valle de cada estría dejaba 0.60 mm de
#    material, menos de dos perímetros de boquilla.
#  - El vaso pasó de 78 × 95 a 70 × 110, que es la silueta esbelta que el
#    README declara. Baja de 61 a 60 g siendo 15 mm más alto.
#  - Filete en el fondo, que multiplica los anillos cerca de la base: de ahí
#    el salto grande en vértices.
#
# Y aparte, gratis: la resolución dejó de ser un número fijo y pasó a salir
# del acabado, así que el anillo lleva un múltiplo entero de puntos por
# estría en vez de 480 a secas.
#
# De aquí en adelante: si estos números se mueven sin que alguien haya tocado
# DISENOS, se rompió algo.
RECETAS = {
    "portacontroles": (40400, 80784, 123),   # 990 puntos = 99 estrías × 10
    "portalapices":   (14114, 28224,  59),   # 504 puntos = 63 estrías × 8
    "portacubiertos": (16530, 33048, 129),   # 632 puntos = 79 estrías × 8
}

# Los contornos con todo lo demás fijo, para que la única variable sea la
# planta. Sin acabado, sin perfil, sin divisores: si uno de estos números se
# mueve, se movió la geometría del contorno y nada más.
PLANTA_FIJA = {
    "ancho": 100, "fondo": 70, "alto": 80, "acabado": "liso", "perfil": "recto",
    "ranuras": 1, "filas": 1, "drenaje_diametro": 0.0, "bandeja": "ninguna",
    "segmentos": 240,
}

CONTORNOS_BASE = {
    "circulo":     (962, 1920, 57),
    "rectangulo":  (962, 1920, 68),
    "ovalo":       (962, 1920, 60),
    "superelipse": (962, 1920, 68),
    "hoja":        (962, 1920, 54),
    "arco":        (962, 1920, 57),
    "plegado":     (962, 1920, 56),
    "guijarro":    (962, 1920, 56),
    # La segunda tanda, la que salió de mirar el portacontroles y el
    # portacubiertos en vez de mirar el catálogo de siluetas.
    "chaflan":     (962, 1920, 65),
    "trapecio":    (962, 1920, 63),
    "poligono":    (962, 1920, 57),
    "lobulos":     (962, 1920, 56),
    "rinon":       (962, 1920, 59),
}


def medir(p):
    """(vértices, triángulos, gramos, cerrada) de un juego de parámetros."""
    malla, datos = cuerpo.construir(disenos.normalizar(p))
    return len(malla.v), len(malla.t), datos["gramos"], datos["cerrada"]


class LineaBase(unittest.TestCase):
    """Que las piezas de siempre sigan saliendo idénticas."""

    def test_recetas(self):
        for clave, esperado in RECETAS.items():
            with self.subTest(receta=clave):
                v, t, g, _ = medir(disenos.parametros_de(clave))
                self.assertEqual((v, t, g), esperado)

    def test_recetas_cerradas(self):
        # Una malla abierta no se guarda, así que esto vale por sí solo.
        for clave in RECETAS:
            with self.subTest(receta=clave):
                self.assertTrue(medir(disenos.parametros_de(clave))[3])

    def test_contornos(self):
        for clave, esperado in CONTORNOS_BASE.items():
            with self.subTest(contorno=clave):
                p = dict(disenos.DEFECTOS, **PLANTA_FIJA)
                p["contorno"] = clave
                v, t, g, cerrada = medir(p)
                self.assertEqual((v, t, g), esperado)
                self.assertTrue(cerrada)

    def test_las_recetas_declaradas_son_las_medidas(self):
        # Si alguien agrega una receta y no la mide, esta prueba lo dice en vez
        # de dejar el hueco callado. La receta «libre» de la pestaña «Idea» no
        # cuenta: no tiene valores propios que puedan cambiar.
        declaradas = {d["clave"] for d in disenos.DISENOS} - {"libre"}
        self.assertEqual(declaradas, set(RECETAS))

    def test_los_contornos_declarados_son_los_medidos(self):
        # Lo mismo para las plantas. «trazado» se excluye porque su geometría
        # no sale de una fórmula sino de la imagen que le toque.
        self.assertEqual(set(CONTORNOS) - {"trazado"}, set(CONTORNOS_BASE))

    def test_el_guijarro_no_es_sorteado(self):
        # La irregularidad está escrita, no sorteada: la misma piedra siempre.
        # Si esto falla, el catálogo dejó de ser reproducible.
        p = dict(disenos.DEFECTOS, **PLANTA_FIJA)
        p["contorno"] = "guijarro"
        self.assertEqual(medir(p), medir(p))


class Normalizar(unittest.TestCase):
    """El cuello por donde pasa todo lo que entra al motor."""

    def test_recorta_al_rango(self):
        p = disenos.normalizar({"alto": 9000, "pared": -5})
        spec = {s["clave"]: s for s in disenos.PARAMETROS}
        self.assertEqual(p["alto"], spec["alto"]["max"])
        self.assertEqual(p["pared"], spec["pared"]["min"])

    def test_descarta_lo_que_no_conoce(self):
        p = disenos.normalizar({"parametro_inventado": 3, "contorno": "no_existe"})
        self.assertNotIn("parametro_inventado", p)
        self.assertEqual(p["contorno"], disenos.DEFECTOS["contorno"])

    def test_acepta_numeros_como_texto(self):
        # De esto depende que el modelo pueda mandar todo como cadena.
        self.assertEqual(disenos.normalizar({"alto": "120"})["alto"], 120.0)

    def test_completa_lo_que_falta(self):
        p = disenos.normalizar({})
        self.assertEqual(set(p), set(disenos.DEFECTOS))

    def test_no_lanza_con_basura(self):
        # Un valor que no se puede leer deja el de la receta, y nadie se cae.
        for clave, basura in (("alto", "muy alto"), ("alto", None),
                              ("alto", [1, 2]), ("contorno", 7),
                              ("contorno", None)):
            with self.subTest(clave=clave, basura=basura):
                p = disenos.normalizar({clave: basura})
                self.assertEqual(p[clave], disenos.DEFECTOS[clave])


class ParametroTrazo(unittest.TestCase):
    """La silueta viaja como texto dentro de los valores, así que la puerta
    de entrada es lo único que la separa de zlib.decompress."""

    def test_acepta_base64(self):
        for bueno in ("", "eNpjYGBg", "eNpjYGBg=", "eNpjYGBg==", "a+b/c"):
            with self.subTest(trazo=bueno):
                self.assertEqual(disenos.normalizar({"trazo": bueno})["trazo"],
                                 bueno)

    def test_rechaza_lo_muy_largo(self):
        largo = "A" * (disenos.TRAZO_LARGO_MAX + 1)
        self.assertEqual(disenos.normalizar({"trazo": largo})["trazo"], "")

    def test_acepta_justo_el_tope(self):
        tope = "A" * disenos.TRAZO_LARGO_MAX
        self.assertEqual(disenos.normalizar({"trazo": tope})["trazo"], tope)

    def test_rechaza_fuera_del_alfabeto(self):
        # El guion bajo y el guion son base64 «de URL», que zlib no espera; el
        # resto es lo que llegaría de un cliente descompuesto o malicioso.
        for malo in ("a_b-c", "hola mundo", "<script>", "AAAA\nAAAA", "ñ",
                     "=AAAA", "AA=A"):
            with self.subTest(trazo=malo):
                self.assertEqual(disenos.normalizar({"trazo": malo})["trazo"], "")

    def test_rechaza_lo_que_no_es_texto(self):
        for malo in (123, None, ["eNpjYGBg"], {"a": 1}, True):
            with self.subTest(trazo=malo):
                self.assertEqual(disenos.normalizar({"trazo": malo})["trazo"], "")

    def test_el_defecto_es_vacio(self):
        self.assertEqual(disenos.DEFECTOS["trazo"], "")

    def test_no_estorba_al_motor(self):
        # Un trazo cargado con un contorno normal no cambia nada: la silueta
        # sólo la mira el contorno «trazado».
        p = dict(disenos.DEFECTOS, **PLANTA_FIJA)
        p["contorno"] = "circulo"
        sin_trazo = medir(p)
        con_trazo = medir(dict(p, trazo="eNpjYGBg"))
        self.assertEqual(sin_trazo, con_trazo)


class RecetaLibre(unittest.TestCase):
    """Donde aterriza una idea que no es ninguno de los productos."""

    def test_existe_y_tiene_carpeta_propia(self):
        self.assertIn("libre", disenos.POR_CLAVE)
        self.assertEqual(disenos.POR_CLAVE["libre"]["carpeta"], "Ideas")

    def test_arranca_con_los_valores_por_defecto(self):
        self.assertEqual(disenos.parametros_de("libre"), disenos.DEFECTOS)

    def test_construye_una_pieza_cerrada(self):
        v, t, g, cerrada = medir(disenos.parametros_de("libre"))
        self.assertTrue(cerrada)
        self.assertGreater(g, 0)

    def test_no_desplaza_a_la_receta_que_abre_por_defecto(self):
        # La pestaña «Crear» abre con genRecetas[0]: si «libre» se colara al
        # frente, cambiaría lo que ve el usuario al entrar.
        self.assertEqual(disenos.DISENOS[0]["clave"], "portacontroles")

    def test_tiene_nombre_sugerido(self):
        nombre = disenos.nombre_sugerido("libre", disenos.parametros_de("libre"))
        self.assertTrue(nombre)
        self.assertNotIn(" ", nombre)


def curva(fn, n=360):
    """Muestrea un contorno para poder compararlo con otro."""
    return [fn(i / n) for i in range(n)]


def separacion(a, b):
    """La distancia mayor entre dos curvas muestreadas igual."""
    return max(math.dist(p, q) for p, q in zip(a, b))


class Codificacion(unittest.TestCase):
    """La silueta guardada como texto: ida y vuelta."""

    def test_ida_y_vuelta(self):
        radios = T.de_funcion(lambda a: 1.0 + 0.3 * math.cos(2 * a))
        vueltos = T.decodificar(T.codificar(radios))
        mayor = max(radios)
        # Un byte por radio: el error no puede pasar de medio paso de 1/255.
        peor = max(abs(r / mayor - v) for r, v in zip(radios, vueltos))
        self.assertLess(peor, 0.5 / 255 + 1e-9)

    def test_cabe_donde_tiene_que_caber(self):
        # De esto depende que el trazo viaje dentro de los valores en vez de
        # necesitar un registro en el servidor.
        cadena = T.codificar(T.de_funcion(
            lambda a: 1.0 + 0.2 * math.cos(3 * a) + 0.1 * math.sin(7 * a)))
        self.assertLessEqual(len(cadena), 512)
        self.assertEqual(disenos.normalizar({"trazo": cadena})["trazo"], cadena)

    def test_siempre_da_las_mismas_muestras(self):
        for n in (12, 90, 180, 720):
            with self.subTest(muestras=n):
                radios = [1.0] * n
                self.assertEqual(len(T.decodificar(T.codificar(radios))),
                                 T.MUESTRAS)

    def test_la_escala_no_importa(self):
        # Se guarda como fracción del mayor, así que una silueta y la misma al
        # doble de tamaño son el mismo trazo. La escala la pone la ficha.
        chico = T.de_funcion(lambda a: 1.0 + 0.3 * math.cos(2 * a))
        grande = [r * 37.0 for r in chico]
        self.assertEqual(T.codificar(chico), T.codificar(grande))

    def test_devuelve_none_y_no_lanza(self):
        for malo in ("", None, 123, "no es base64!", "AAAA", "a_b-c",
                     base64.b64encode(b"otra cosa").decode(),
                     base64.b64encode(zlib.compress(b"T9" + bytes(180))).decode(),
                     base64.b64encode(zlib.compress(b"T1" + bytes(12))).decode()):
            with self.subTest(entrada=repr(malo)[:40]):
                self.assertIsNone(T.decodificar(malo))

    def test_no_se_deja_inflar(self):
        # Tres kilobytes comprimidos pueden ser muchísimos descomprimidos, y
        # esto lo manda quien tenga el navegador abierto.
        bomba = base64.b64encode(zlib.compress(b"T1" + b"\0" * 2_000_000)).decode()
        self.assertLess(len(bomba), disenos.TRAZO_LARGO_MAX)   # pasa el filtro
        self.assertIsNone(T.decodificar(bomba))                 # y aun así, no

    def test_sin_radios_no_hay_trazo(self):
        self.assertEqual(T.codificar([]), "")
        self.assertEqual(T.codificar([0.0] * 180), "")


class ContornoTrazado(unittest.TestCase):
    """La silueta trazada como una planta más del motor."""

    def marco(self, ancho=100, fondo=70, **extra):
        return dict(disenos.DEFECTOS, **dict(PLANTA_FIJA, ancho=ancho,
                                             fondo=fondo, contorno="trazado",
                                             **extra))

    def test_radios_constantes_dan_la_elipse(self):
        # Un radio constante encajado en 100×70 es exactamente lo que hace el
        # contorno «círculo», que en este motor ya es la elipse.
        p = self.marco(trazo=T.codificar([1.0] * T.MUESTRAS))
        trazada = curva(CONTORNOS["trazado"][1](p))
        redonda = curva(circulo(p))
        self.assertLess(separacion(trazada, redonda), 0.01 * p["ancho"])

    def test_conserva_la_forma(self):
        # Una silueta cualquiera, comparada contra su versión analítica pasada
        # por el mismo encaje. Lo que las separe es la cuantización.
        def r(a):
            return 1.0 + 0.22 * math.cos(2 * a + 0.9) + 0.11 * math.cos(5 * a)
        p = self.marco(ancho=100, fondo=100, trazo=T.codificar(T.de_funcion(r)))
        trazada = curva(CONTORNOS["trazado"][1](p))
        exacta = curva(circulo(dict(p, ancho=100, fondo=100)))
        # No se compara contra el círculo: se compara que no sea el círculo.
        self.assertGreater(separacion(trazada, exacta), 5.0)
        # Y que el dibujo esté donde debe: los máximos de r(a) mandan.
        radios = [math.hypot(x, y) for x, y in trazada]
        pico = radios.index(max(radios)) / len(radios)
        esperado = max(range(360), key=lambda i: r(i * math.tau / 360)) / 360
        self.assertLess(abs(pico - esperado) % 1.0, 0.02)

    def test_las_esquinas_de_un_cuadrado(self):
        # Un cuadrado: el radio en la esquina es √2 veces el del lado. Con 180
        # muestras la esquina cae entre dos —45° no es múltiplo de 2°—, así que
        # se queda 1.7% corta. Es el límite conocido de la resolución, y por
        # eso la tolerancia es del 3% y no del 1%.
        cuadrado = T.de_funcion(
            lambda a: 1.0 / max(abs(math.cos(a)), abs(math.sin(a))))
        p = self.marco(ancho=100, fondo=100, trazo=T.codificar(cuadrado))
        radios = [math.hypot(x, y) for x, y in curva(CONTORNOS["trazado"][1](p))]
        self.assertAlmostEqual(max(radios) / min(radios), math.sqrt(2),
                               delta=0.03 * math.sqrt(2))

    def test_llena_el_cuadro_pedido(self):
        # R4.3: dos plantas distintas con los mismos milímetros ocupan lo mismo.
        p = self.marco(ancho=132, fondo=66,
                       trazo=T.codificar(T.de_funcion(
                           lambda a: 1.0 + 0.3 * math.cos(3 * a))))
        pts = curva(CONTORNOS["trazado"][1](p), 720)
        xs = [x for x, _ in pts]
        ys = [y for _, y in pts]
        self.assertAlmostEqual(max(xs) - min(xs), 132, delta=0.5)
        self.assertAlmostEqual(max(ys) - min(ys), 66, delta=0.5)

    def test_sin_trazo_sale_redondo(self):
        for trazo in ("", "AAAA", "no es base64!"):
            with self.subTest(trazo=trazo):
                p = self.marco(trazo=trazo)
                self.assertLess(
                    separacion(curva(CONTORNOS["trazado"][1](p)),
                               curva(circulo(p))), 1e-9)

    def test_la_pieza_completa_sale_cerrada(self):
        p = self.marco(trazo=T.codificar(T.de_funcion(
            lambda a: 1.0 + 0.25 * math.cos(2 * a + 0.5))))
        v, t, g, cerrada = medir(p)
        self.assertTrue(cerrada)
        self.assertGreater(g, 0)

    def test_la_pieza_completa_mide_lo_que_dice(self):
        p = self.marco(ancho=110, fondo=80, trazo=T.codificar(
            T.de_funcion(lambda a: 1.0 + 0.2 * math.cos(4 * a))))
        _, datos = cuerpo.construir(disenos.normalizar(p))
        self.assertAlmostEqual(datos["ancho"], 110, delta=1.0)
        self.assertAlmostEqual(datos["fondo"], 80, delta=1.0)

    def test_una_silueta_rara_no_tumba_el_motor(self):
        # Radios casi nulos en un tramo: una silueta con una hendidura brutal.
        # Puede salir fea y puede avisar, pero no puede lanzar.
        radios = [1.0 if i % 60 else 0.02 for i in range(T.MUESTRAS)]
        p = self.marco(trazo=T.codificar(radios))
        _, datos = cuerpo.construir(disenos.normalizar(p))
        self.assertIsInstance(datos["avisos"], list)


class Voladizo(unittest.TestCase):
    """El vigilante: que avise cuando la pieza va a pedir soportes.

    Se mide en los dos sentidos porque las dos cosas cuelgan. Una pared que se
    abre cuelga sobre el aire; una que se cierra cuelga sobre el hueco. En los
    dos casos la capa nueva sale hacia afuera de la que tiene debajo, y lo que
    decide si se sostiene es el ángulo respecto a la vertical.

    Los ángulos de abajo están calculados a mano: con un perfil lineal, la
    pared avanza `k · radio` en horizontal a lo largo de `alto` en vertical, así
    que el ángulo es atan(k · radio / alto). Si el motor y esta cuenta no
    coinciden, uno de los dos está mal.
    """

    def pieza(self, **extra):
        p = dict(disenos.DEFECTOS, contorno="circulo", acabado="liso",
                 ranuras=1, filas=1, drenaje_diametro=0.0, bandeja="ninguna",
                 segmentos=240, base_redondeo=0.0)
        p.update(extra)
        return cuerpo.construir(disenos.normalizar(p))[1]

    def aviso_de_voladizo(self, datos):
        for a in datos["avisos"]:
            if "respecto a la vertical" in a:
                return a
        return None

    def test_calcula_el_angulo_que_toca(self):
        # atan(0.35 · 100 / 30) = 49.4°, y el aviso lo redondea a 49.
        for perfil in ("conico", "invertido"):
            with self.subTest(perfil=perfil):
                d = self.pieza(ancho=200, fondo=200, alto=30, perfil=perfil,
                               perfil_intensidad=0.35)
                self.assertIn("49°", self.aviso_de_voladizo(d) or "")

    def test_avisa_cuando_se_abre(self):
        d = self.pieza(ancho=200, fondo=200, alto=30, perfil="conico",
                       perfil_intensidad=0.35)
        self.assertIn("se abre", self.aviso_de_voladizo(d) or "")

    def test_avisa_cuando_se_cierra(self):
        # El caso que el motor dejaba pasar callado: sólo miraba r1 > r0.
        d = self.pieza(ancho=200, fondo=200, alto=30, perfil="invertido",
                       perfil_intensidad=0.35)
        self.assertIn("se cierra", self.aviso_de_voladizo(d) or "")

    def test_el_consejo_va_con_el_sentido(self):
        abre = self.pieza(ancho=200, fondo=200, alto=30, perfil="conico",
                          perfil_intensidad=0.35)
        cierra = self.pieza(ancho=200, fondo=200, alto=30, perfil="invertido",
                            perfil_intensidad=0.35)
        self.assertIn("intensidad", self.aviso_de_voladizo(abre))
        self.assertIn("despacio", self.aviso_de_voladizo(cierra))

    def test_calla_cuando_la_pieza_es_sana(self):
        # atan(0.35 · 38 / 120) = 6.3°: ni de lejos.
        for perfil in ("recto", "conico", "invertido", "barril", "campana",
                       "cintura", "organico"):
            with self.subTest(perfil=perfil):
                d = self.pieza(ancho=76, fondo=76, alto=120, perfil=perfil,
                               perfil_intensidad=0.35)
                self.assertIsNone(self.aviso_de_voladizo(d))

    def test_las_recetas_siguen_sin_avisos(self):
        # El cambio no puede estrenar avisos en las piezas de siempre.
        for clave in RECETAS:
            with self.subTest(receta=clave):
                _, datos = cuerpo.construir(disenos.parametros_de(clave))
                self.assertIsNone(self.aviso_de_voladizo(datos))

    def test_el_umbral_esta_donde_dice(self):
        # Justo por debajo de 47° calla; justo por encima, avisa. Quien cruza
        # el umbral es la proporción de la pieza, no la intensidad: con el
        # radio en 100 y k topada en 0.35, el ángulo es atan(35 / alto), y hace
        # falta bajar de 33 mm de alto para pasar de 47°. Con la pieza esbelta
        # de las recetas —radio 38, alto 120— el máximo alcanzable son 16°.
        callado = self.pieza(ancho=200, fondo=200, alto=35, perfil="invertido",
                             perfil_intensidad=0.35)      # 45.0°
        self.assertIsNone(self.aviso_de_voladizo(callado))
        ruidoso = self.pieza(ancho=200, fondo=200, alto=31, perfil="invertido",
                             perfil_intensidad=0.35)      # 48.5°
        self.assertIsNotNone(self.aviso_de_voladizo(ruidoso))

    def test_el_cuello_del_prototipo_avisaria(self):
        # Del prototipo que se hizo antes de escribir el diseño: una boca de
        # 0.30 con el hombro en 0.80 cierra a 57.7°. Todavía no hay cuello en
        # el motor, así que aquí se comprueba la cuenta que el motor usará.
        def escala(zn, boca=0.30, hombro=0.80):
            if zn <= hombro:
                return 1.0
            t = (zn - hombro) / (1.0 - hombro)
            return 1.0 - (1.0 - boca) * t * t * (3.0 - 2.0 * t)
        alto, radio = 150.0, 45.0
        peor = 0.0
        for j in range(400):
            z0, z1 = alto * j / 400, alto * (j + 1) / 400
            dr = (escala(z1 / alto) - escala(z0 / alto)) * radio
            peor = max(peor, math.degrees(math.atan2(abs(dr), z1 - z0)))
        self.assertGreater(peor, 47.0)
        self.assertAlmostEqual(peor, 57.7, delta=0.5)


class Cuello(unittest.TestCase):
    """El eje que separa un vaso de un jarrón."""

    def pieza(self, **extra):
        p = dict(disenos.DEFECTOS, contorno="circulo", ancho=90, fondo=90,
                 alto=150, acabado="liso", perfil="recto", ranuras=1, filas=1,
                 drenaje_diametro=0.0, bandeja="ninguna", segmentos=240,
                 capas=120, base_redondeo=0.0)
        p.update(extra)
        return cuerpo.construir(disenos.normalizar(p))

    def radio_de_la_boca(self, malla):
        """El radio mayor del aro de arriba, medido sobre la malla."""
        cima = max(z for _, _, z in malla.v)
        return max(math.hypot(x, y) for x, y, z in malla.v if z > cima - 0.01)

    def test_la_boca_mide_lo_que_se_pidio(self):
        # R1.1: de una cuarta parte de la panza al ancho entero.
        for boca in (0.25, 0.40, 0.60, 0.85, 1.00):
            with self.subTest(boca=boca):
                m, _ = self.pieza(cuello="suave", boca=boca, cuello_hombro=0.50)
                esperado = 45.0 * boca
                self.assertAlmostEqual(self.radio_de_la_boca(m) / esperado, 1.0,
                                       delta=0.02)

    def test_el_hombro_manda_donde_se_pidio(self):
        # R1.2: por debajo del hombro no se ha cerrado nada todavía.
        for hombro in (0.30, 0.60, 0.95):
            with self.subTest(hombro=hombro):
                c = CUELLOS["suave"][1]({"boca": 0.4, "cuello_hombro": hombro})
                self.assertEqual(c(hombro - 1e-9), 1.0)
                self.assertLess(c(hombro + (1.0 - hombro) * 0.5), 1.0)

    @staticmethod
    def salto(f, punto, h):
        """Cuánto cambia la pendiente al cruzar `punto`, con paso `h`."""
        izq = (f(punto) - f(punto - h)) / h
        der = (f(punto + h) - f(punto)) / h
        return abs(der - izq)

    def sin_esquina(self, f, punto, quien):
        """Una esquina se reconoce porque el salto de pendiente NO se
        desvanece al achicar el paso: se queda clavado en el valor del
        quiebre. Donde la curva empalma bien, el salto que se mide es curvatura
        y se va a cero con el paso.

        Comparar el salto con cero y una tolerancia fija no serviría: el valor
        depende de lo corto que sea el tramo de cierre, no de si hay esquina.
        """
        grueso = self.salto(f, punto, 1e-3)
        fino = self.salto(f, punto, 1e-4)
        self.assertLess(fino, max(grueso / 5.0, 1e-9),
                        "%s: el salto de pendiente no se desvanece" % quien)

    def test_no_hay_esquina_en_el_hombro(self):
        # R1.3: es lo que se gana con el smoothstep. Una recta saltaría de
        # pendiente 0 a −(1−boca)/tramo de golpe, y ahí sí habría esquina.
        for familia in ("suave", "abrupto", "botella"):
            for hombro in (0.40, 0.60, 0.80):
                with self.subTest(familia=familia, hombro=hombro):
                    c = CUELLOS[familia][1]({"boca": 0.35,
                                             "cuello_hombro": hombro})
                    self.sin_esquina(c, hombro, "hombro")

    def test_tampoco_al_terminar_de_cerrar(self):
        # El otro empalme: donde el hombro termina y el cuello sigue recto.
        for familia, tramo in (("abrupto", 0.45), ("botella", 0.25)):
            with self.subTest(familia=familia):
                hombro = 0.5
                c = CUELLOS[familia][1]({"boca": 0.35, "cuello_hombro": hombro})
                self.sin_esquina(c, hombro + (1.0 - hombro) * tramo, "fin del cierre")

    def test_la_prueba_de_la_esquina_tiene_dientes(self):
        """Que la comprobación de arriba sepa reprobar.

        Un cierre lineal —lo que se descartó al diseñar— es exactamente lo que
        no debe pasar. Si esta prueba dejara de fallar con la recta, las dos de
        arriba no estarían comprobando nada.
        """
        hombro, boca = 0.6, 0.35
        def recta(zn):
            if zn <= hombro:
                return 1.0
            return 1.0 - (1.0 - boca) * (zn - hombro) / (1.0 - hombro)
        with self.assertRaises(AssertionError):
            self.sin_esquina(recta, hombro, "recta")

    def test_cierra_mas_rapido_cuanto_mas_corto_el_tramo(self):
        # Lo que distingue a las tres familias, dicho como aserción.
        p = {"boca": 0.35, "cuello_hombro": 0.60}
        medio = 0.60 + 0.40 * 0.5
        self.assertGreater(CUELLOS["suave"][1](p)(medio),
                           CUELLOS["abrupto"][1](p)(medio))
        self.assertGreater(CUELLOS["abrupto"][1](p)(medio),
                           CUELLOS["botella"][1](p)(medio) - 1e-9)

    def test_la_malla_cierra_en_todo_el_rango(self):
        spec = {s["clave"]: s for s in disenos.PARAMETROS}
        for familia in ("suave", "abrupto", "botella"):
            for boca in (spec["boca"]["min"], 0.5, spec["boca"]["max"]):
                for hombro in (spec["cuello_hombro"]["min"],
                               spec["cuello_hombro"]["max"]):
                    with self.subTest(familia=familia, boca=boca, hombro=hombro):
                        _, d = self.pieza(cuello=familia, boca=boca,
                                          cuello_hombro=hombro)
                        self.assertTrue(d["cerrada"])
                        self.assertGreater(d["gramos"], 0)

    def test_cerrar_la_boca_quita_material(self):
        pesos = [self.pieza(cuello="suave", boca=b, cuello_hombro=0.5)[1]["gramos"]
                 for b in (1.00, 0.70, 0.45, 0.25)]
        self.assertEqual(pesos, sorted(pesos, reverse=True))

    def test_el_valor_neutro_no_toca_nada(self):
        # R1.7: sin cuello, la geometría es la de antes de que el eje existiera.
        sin = self.pieza()
        for neutro in ({"cuello": "ninguno"},
                       {"cuello": "suave", "boca": 1.00}):
            with self.subTest(**neutro):
                m, d = self.pieza(**neutro)
                self.assertEqual((len(m.v), len(m.t), d["gramos"]),
                                 (len(sin[0].v), len(sin[0].t), sin[1]["gramos"]))

    def test_una_boca_entera_no_es_un_cuello(self):
        # Elegir «suave» con la boca en 1 no debe encender las capas extra ni
        # apagar los divisores: no se pidió cerrar nada.
        c = CUELLOS["suave"][1]({"boca": 1.0, "cuello_hombro": 0.6})
        self.assertTrue(c.neutro)
        self.assertFalse(c.varia_z)

    def test_con_cuello_no_quedan_divisores(self):
        # R1.6, y que el aviso llegue: quitar cosas en silencio es peor que no
        # quitarlas.
        _, d = self.pieza(cuello="suave", boca=0.45, cuello_hombro=0.55,
                          ranuras=4, filas=2)
        self.assertEqual(d["ranuras"], 1)
        self.assertEqual(d["filas"], 1)
        self.assertTrue(any("divisores" in a for a in d["avisos"]))

    def test_sin_cuello_los_divisores_siguen(self):
        _, d = self.pieza(ranuras=4, filas=1)
        self.assertEqual(d["ranuras"], 4)
        self.assertFalse(any("divisores" in a for a in d["avisos"]))

    def test_un_cuello_imposible_avisa(self):
        # R1.4. El caso del prototipo: boca 0.30 con el hombro en 0.80 cierra a
        # 58°, y ahora lo mide el motor y no una cuenta aparte.
        _, d = self.pieza(cuello="suave", boca=0.30, cuello_hombro=0.80)
        aviso = [a for a in d["avisos"] if "vertical" in a]
        self.assertTrue(aviso)
        self.assertIn("se cierra", aviso[0])

    def test_un_cuello_razonable_no_avisa(self):
        _, d = self.pieza(cuello="suave", boca=0.30, cuello_hombro=0.50)
        self.assertFalse([a for a in d["avisos"] if "vertical" in a])


class Borde(unittest.TestCase):
    """El labio: hasta dónde sube cada columna de la pared."""

    def pieza(self, **extra):
        p = dict(disenos.DEFECTOS, contorno="circulo", ancho=100, fondo=100,
                 alto=120, acabado="liso", perfil="recto", ranuras=1, filas=1,
                 drenaje_diametro=0.0, bandeja="ninguna", segmentos=300,
                 capas=100, base_redondeo=0.0)
        p.update(extra)
        return cuerpo.construir(disenos.normalizar(p))

    def labio(self, **extra):
        """El arreglo de alturas que produce el borde, sin construir malla."""
        p = disenos.normalizar(dict(disenos.DEFECTOS, contorno="circulo",
                                    ancho=100, fondo=100, **extra))
        anillo, _ = muestrear(CONTORNOS["circulo"][1](p), 300)
        return BO.remate(p, anillo, 120.0)

    def test_baja_hasta_donde_se_pidio(self):
        # R4.1 y R4.3: la hondura es la fracción de altura que baja el punto
        # más bajo, y la parte alta se queda donde estaba.
        for familia in ("diagonal", "ondulado", "petalos"):
            for hondura in (0.10, 0.25, 0.45):
                with self.subTest(familia=familia, hondura=hondura):
                    t = self.labio(borde=familia, borde_hondura=hondura,
                                   borde_ondas=6, borde_rumbo=0)
                    self.assertAlmostEqual(max(t), 120.0, delta=0.2)
                    self.assertAlmostEqual(min(t), 120.0 * (1 - hondura),
                                           delta=0.6)

    def test_el_labio_se_cierra_sobre_si_mismo(self):
        """Las ondas son enteras a la fuerza: si no cierran, queda un escalón.

        No sirve comparar la primera muestra con la última y pedir que se
        parezcan: en un pétalo el valle es una punta viva, y dos muestras
        vecinas ahí se llevan mucho **por diseño**. Lo que delata una costura
        es que el salto en el cierre sea mayor que los saltos normales del
        resto de la vuelta.
        """
        for familia in ("ondulado", "petalos"):
            for ondas in (2, 5, 6, 11, 16):
                with self.subTest(familia=familia, ondas=ondas):
                    t = self.labio(borde=familia, borde_hondura=0.3,
                                   borde_ondas=ondas)
                    saltos = [abs(t[i] - t[i - 1]) for i in range(len(t))]
                    self.assertLessEqual(saltos[0], max(saltos[1:]) + 1e-9)

    def test_hay_tantos_lobulos_como_se_pidieron(self):
        for ondas in (3, 6, 12):
            with self.subTest(ondas=ondas):
                t = self.labio(borde="ondulado", borde_hondura=0.3,
                               borde_ondas=ondas)
                # Contar máximos locales cerrando el arreglo sobre sí mismo.
                picos = sum(1 for i in range(len(t))
                            if t[i] > t[i - 1] and t[i] >= t[(i + 1) % len(t)])
                self.assertEqual(picos, ondas)

    def test_el_diagonal_es_un_plano(self):
        # Un plano inclinado, no una onda de media vuelta: la altura tiene que
        # ser lineal en la proyección sobre el rumbo.
        p = disenos.normalizar(dict(disenos.DEFECTOS, contorno="circulo",
                                    ancho=100, fondo=100, borde="diagonal",
                                    borde_hondura=0.30, borde_rumbo=0))
        anillo, _ = muestrear(CONTORNOS["circulo"][1](p), 300)
        t = BO.remate(p, anillo, 120.0)
        for (x, _, _, _, _), altura in zip(anillo, t):
            esperado = 120.0 - 36.0 * (1.0 - (x + 50.0) / 100.0)
            self.assertAlmostEqual(altura, esperado, delta=0.5)

    def test_el_rumbo_gira_el_corte(self):
        bajo_en = {}
        for rumbo in (0, 90, 180, 270):
            p = disenos.normalizar(dict(disenos.DEFECTOS, contorno="circulo",
                                        ancho=100, fondo=100, borde="diagonal",
                                        borde_hondura=0.30, borde_rumbo=rumbo))
            anillo, _ = muestrear(CONTORNOS["circulo"][1](p), 300)
            t = BO.remate(p, anillo, 120.0)
            i = t.index(min(t))
            bajo_en[rumbo] = (round(anillo[i][0]), round(anillo[i][1]))
        # Con rumbo 0 lo alto mira a +x, así que lo bajo cae en −x.
        self.assertLess(bajo_en[0][0], -40)
        self.assertGreater(bajo_en[180][0], 40)
        self.assertLess(bajo_en[90][1], -40)
        self.assertGreater(bajo_en[270][1], 40)

    def test_los_petalos_tienen_punta_y_las_ondas_no(self):
        # Lo que separa un pétalo de un festón: el valle. El arco llega con
        # tangente vertical y deja punta; la onda llega con tangente nula.
        hondo = dict(borde_hondura=0.30, borde_ondas=6)
        onda = self.labio(borde="ondulado", **hondo)
        petalo = self.labio(borde="petalos", **hondo)
        def pendiente_en_el_valle(t):
            i = t.index(min(t))
            return abs(t[(i + 3) % len(t)] - t[i])
        self.assertGreater(pendiente_en_el_valle(petalo),
                           pendiente_en_el_valle(onda) * 3)

    def test_la_malla_cierra_con_cualquier_borde(self):
        spec = {s["clave"]: s for s in disenos.PARAMETROS}
        for familia in ("recto", "diagonal", "ondulado", "petalos"):
            for hondura in (0.0, 0.20, spec["borde_hondura"]["max"]):
                with self.subTest(familia=familia, hondura=hondura):
                    _, d = self.pieza(borde=familia, borde_hondura=hondura,
                                      borde_ondas=6)
                    self.assertTrue(d["cerrada"])
                    self.assertGreater(d["gramos"], 0)

    def test_recortar_el_labio_quita_material(self):
        pesos = [self.pieza(borde="ondulado", borde_hondura=h,
                            borde_ondas=6)[1]["gramos"]
                 for h in (0.0, 0.15, 0.30, 0.45)]
        self.assertEqual(pesos, sorted(pesos, reverse=True))

    def test_el_valor_neutro_no_toca_nada(self):
        # R4.6, por los dos caminos que llevan a «no recortar nada».
        sin = self.pieza()
        for neutro in ({"borde": "recto"},
                       {"borde": "ondulado", "borde_hondura": 0.0}):
            with self.subTest(**neutro):
                m, d = self.pieza(**neutro)
                self.assertEqual((len(m.v), len(m.t), d["gramos"]),
                                 (len(sin[0].v), len(sin[0].t), sin[1]["gramos"]))

    def test_convive_con_el_escalon(self):
        # Los dos son alturas de remate y se componen por mínimo: con los dos
        # puestos, la pieza no puede quedar más alta que con cualquiera solo.
        solo_escalon = self.pieza(escalon=0.6, escalon_frente=0.5)[1]["gramos"]
        solo_borde = self.pieza(borde="diagonal", borde_hondura=0.3)[1]["gramos"]
        ambos = self.pieza(escalon=0.6, escalon_frente=0.5, borde="diagonal",
                           borde_hondura=0.3)[1]["gramos"]
        self.assertLessEqual(ambos, min(solo_escalon, solo_borde))

    def test_ningun_divisor_asoma_por_el_borde(self):
        # R4.5, comprobado sobre la malla y no sobre la intención.
        m, d = self.pieza(contorno="rectangulo", ancho=132, fondo=66, alto=88,
                          redondeo=16, ranuras=4, divisor_alto=80,
                          borde="ondulado", borde_hondura=0.40, borde_ondas=6)
        self.assertTrue(any("recortaron" in a for a in d["avisos"]))
        # Ningún vértice de la pieza puede subir más que el labio más bajo…
        # salvo la propia pared, así que se mira sólo el centro, donde no hay
        # pared pero sí divisores.
        centrales = [z for x, y, z in m.v if abs(x) < 30 and abs(y) < 12]
        p = disenos.normalizar(dict(disenos.DEFECTOS, contorno="rectangulo",
                                    ancho=132, fondo=66, borde="ondulado",
                                    borde_hondura=0.40, borde_ondas=6))
        anillo, _ = muestrear(CONTORNOS["rectangulo"][1](p), 300)
        labio_bajo = min(BO.remate(p, anillo, 88.0))
        self.assertLessEqual(max(centrales), labio_bajo + 0.01)


class Acabados(unittest.TestCase):
    """Que el relieve salga igual de bien en toda la vuelta.

    El defecto que estas pruebas cuidan no es que una estría esté mal
    dibujada: es que estén mal muestreadas. Con una cantidad de puntos que no
    sea múltiplo entero de las estrías, cada una cae con una fase distinta
    —unas justo en la cresta, otras a medio flanco— y la pieza sale con el
    relieve desparejo aunque la fórmula sea impecable. Con 480 puntos y 31
    estrías, el facetado perdía hasta el 12 % de la punta en unas sí y en
    otras no.
    """

    # Todos menos el liso, que no tiene relieve que medirle.
    CON_RELIEVE = [a for a in ACABADOS if a != "liso"]

    # Base propia, no una receta del catálogo. Las recetas son del usuario y
    # se mueven: cuando el portacontroles pasó a pedir 600 puntos de piso y
    # grano 0.4, tres de estas pruebas empezaron a fallar sin que el motor
    # hubiera cambiado — el piso tapaba justo lo que se estaba midiendo. Una
    # prueba del motor no puede depender de una decisión de producto.
    BASE = {
        "contorno": "rectangulo", "ancho": 132, "fondo": 66, "alto": 88,
        "redondeo": 16, "perfil": "recto", "cuello": "ninguno",
        "borde": "recto", "bandeja": "ninguna", "ranuras": 1, "filas": 1,
        "drenaje_diametro": 0.0, "base_redondeo": 0.0,
        "pared": 1.6, "piso": 2.4, "onda_amplitud": 0.5, "onda_paso": 10.0,
        "torsion_vueltas": 0.15, "segmentos": 480, "capas": 64, "grano": 0.6,
    }

    def resolver(self, calidad="final", **extra):
        """(parámetros, anillo, perímetro, acabado, capas) de una pieza."""
        v = dict(disenos.DEFECTOS, **self.BASE)
        v.update(extra)
        if v.get("acabado") == "lino":
            v["onda_paso"] = extra.get("onda_paso", 5.0)   # el lino quiere paso corto
        p = disenos.normalizar(v)
        fn = CONTORNOS[p["contorno"]][1](p)
        anillo, per, acabado, capas, _ = cuerpo._resolver_malla(
            fn, p, PERFILES[p["perfil"]][1](p),
            CUELLOS[p.get("cuello", "ninguno")][1](p), calidad)
        return p, anillo, per, acabado, capas

    def test_cada_estria_cae_en_la_misma_fase(self):
        # El corazón del asunto: puntos por vuelta múltiplo entero —y par— de
        # las estrías. Par para que la cresta y el valle caigan los dos sobre
        # un punto; entero para que le pase lo mismo a todas.
        for calidad in ("final", "borrador"):
            for acab in self.CON_RELIEVE:
                with self.subTest(acabado=acab, calidad=calidad):
                    _, anillo, _, ac, capas = self.resolver(
                        acabado=acab, calidad=calidad)
                    if ac.periodos_s:
                        self.assertEqual(len(anillo) % ac.periodos_s, 0)
                        self.assertEqual((len(anillo) // ac.periodos_s) % 2, 0)
                    if ac.periodos_z:
                        self.assertEqual(capas % ac.periodos_z, 0)

    def test_todas_las_estrias_salen_iguales(self):
        # La consecuencia visible de lo anterior, medida donde se ve: la
        # cresta que alcanza cada estría. El martillado queda fuera porque su
        # dibujo no se repite estría por estría —son tres tramas que no
        # encajan— y ahí la diferencia entre una y otra es el acabado, no un
        # defecto.
        for acab in [a for a in self.CON_RELIEVE if a != "martillado"]:
            with self.subTest(acabado=acab):
                _, anillo, _, ac, _ = self.resolver(acabado=acab)
                if not ac.periodos_s:
                    continue
                seg, n = len(anillo), ac.periodos_s
                por_estria = seg // n
                picos = [max(ac(i / seg, 0.5)
                             for i in range(k * por_estria, (k + 1) * por_estria))
                         for k in range(n)]
                self.assertAlmostEqual(min(picos), max(picos), places=9,
                                       msg="unas estrías salen más altas que otras")

    def test_ninguna_faceta_se_aparta_del_dibujo(self):
        # Que además haya puntos suficientes, no sólo bien repartidos: entre
        # dos puntos la malla va recta, y esto mide cuánto se aparta esa recta
        # del relieve verdadero. Cinco centésimas de milímetro es la mitad de
        # una capa impresa; la boquilla no resuelve nada de eso.
        for acab in self.CON_RELIEVE:
            with self.subTest(acabado=acab):
                _, anillo, _, ac, capas = self.resolver(acabado=acab)
                seg = len(anillo)
                peor = 0.0
                for k in range(0, capas, max(1, capas // 8)):
                    z0, z1 = k / capas, (k + 1) / capas
                    for i in range(0, seg, max(1, seg // 120)):
                        s0, s1 = i / seg, (i + 1) / seg
                        peor = max(peor, abs(ac((s0 + s1) / 2, z0)
                                             - (ac(s0, z0) + ac(s1, z0)) / 2))
                        if capas > 1:
                            peor = max(peor, abs(ac(s0, (z0 + z1) / 2)
                                                 - (ac(s0, z0) + ac(s0, z1)) / 2))
                self.assertLess(peor, 0.15, "el relieve sale facetado")

    def test_el_valle_deja_pared_para_dos_hilos(self):
        # El defecto físico, no el visual: donde el valle de la estría se mete
        # en la pared, tiene que quedar material para dos perímetros. Con
        # menos, el laminador resuelve el valle con un hilo solo o con relleno
        # de hueco, y la pieza sale traslúcida y con costura justo en la línea
        # que más se mira. Las recetas dejaban 0.60 mm.
        for acab in self.CON_RELIEVE:
            for pared in (0.9, 1.2, 1.6, 2.4):
                with self.subTest(acabado=acab, pared=pared):
                    _, _, _, ac, _ = self.resolver(
                        acabado=acab, pared=pared, onda_amplitud=3.0)
                    self.assertLessEqual(ac.hundimiento(),
                                         pared - cuerpo.PARED_MINIMA + 1e-9)

    def test_el_junco_no_paga_por_un_valle_que_no_tiene(self):
        # El junco sólo pone lomos: nace de la pared y sube, nunca se mete.
        # Recortarlo como si fuera una onda le robaba relieve sin motivo.
        _, _, _, junco, _ = self.resolver(acabado="junco", pared=1.6,
                                          onda_amplitud=1.4)
        _, _, _, onda, _ = self.resolver(acabado="ondulado", pared=1.6,
                                         onda_amplitud=1.4)
        self.assertEqual(junco.amplitud, 1.4)
        self.assertEqual(junco.hundimiento(), 0.0)
        self.assertLess(onda.amplitud, 1.4)

    def test_las_recetas_no_salen_con_avisos(self):
        # Una receta de arranque que ya nace advertida es una receta mal
        # puesta: el usuario no tocó nada todavía.
        for clave in ("portacontroles", "portalapices", "portacubiertos"):
            with self.subTest(receta=clave):
                _, datos = cuerpo.construir(
                    disenos.normalizar(disenos.parametros_de(clave)))
                self.assertEqual(datos["avisos"], [])

    def test_el_grano_manda(self):
        # El parámetro tiene que hacer algo y tiene que hacerlo en el sentido
        # que dice: más fino, más malla.
        for acab in ("ondulado", "lino", "espiga"):
            with self.subTest(acabado=acab):
                _, fino, _, _, capas_fino = self.resolver(acabado=acab, grano=0.4)
                _, grueso, _, _, capas_grueso = self.resolver(acabado=acab, grano=1.2)
                self.assertGreater(len(fino), len(grueso))
                self.assertGreaterEqual(capas_fino, capas_grueso)

    def test_el_liso_no_pide_nada(self):
        # Sin relieve no hay nada que muestrear: la pieza se queda con lo que
        # piden el contorno y el perfil, ni un punto más.
        p, anillo, _, ac, capas = self.resolver(acabado="liso")
        self.assertEqual(len(anillo), int(p["segmentos"]))
        self.assertEqual(capas, 1)

    def test_una_torsion_sin_vueltas_no_gasta_capas(self):
        # Con cero vueltas la estría es vertical y la pieza sale de una capa.
        # Antes se partía en 64 para dibujar una hélice que no gira.
        _, _, _, ac, capas = self.resolver(acabado="torsion", torsion_vueltas=0.0)
        self.assertFalse(ac.varia_z)
        self.assertEqual(capas, 1)

    def test_la_torsion_cerrada_pide_mas_que_la_abierta(self):
        # La hélice es una diagonal y la malla sólo tiene anillos
        # horizontales: cuanto más corre de lado, más anillos hacen falta.
        #
        # Con grano grueso a propósito: a 0.6 mm sobre las estrías finas de la
        # receta, la torsión de 0.9 vueltas se sale del presupuesto y lo que
        # se acabaría midiendo es el tope, no lo que el acabado pide.
        _, _, _, _, poca = self.resolver(acabado="torsion", torsion_vueltas=0.15,
                                         grano=1.2)
        _, _, _, _, mucha = self.resolver(acabado="torsion", torsion_vueltas=0.9,
                                          grano=1.2)
        self.assertGreater(mucha, poca * 2)

    def test_el_borrador_pesa_lo_mismo_que_el_final(self):
        # La vista previa se construye con grano grueso, pero el peso y el
        # costo que enseña son los que va a tener el archivo. Si esto falla,
        # la pestaña «Crear» está cotizando una pieza y guardando otra.
        for acab in self.CON_RELIEVE:
            with self.subTest(acabado=acab):
                v = dict(disenos.DEFECTOS, **self.BASE)
                v["acabado"] = acab
                if acab == "lino":
                    v["onda_paso"] = 5.0
                p = disenos.normalizar(v)
                _, fino = cuerpo.construir(p)
                _, borrador = cuerpo.construir(p, calidad="borrador")
                self.assertAlmostEqual(fino["gramos"], borrador["gramos"], delta=1)

    def test_el_presupuesto_topa_la_malla_y_lo_avisa(self):
        # Una pieza grande, alta, de paso corto y con la torsión cerrada pide
        # más malla de la que tiene sentido mover. Que salga igual, que salga
        # acotada y que lo diga: callarse y tardar cinco minutos es peor.
        p = disenos.normalizar(dict(
            disenos.DEFECTOS, **dict(self.BASE, acabado="torsion",
                                     torsion_vueltas=1.0, onda_paso=3.0,
                                     alto=250, ancho=260, fondo=260)))
        _, datos = cuerpo.construir(p)
        self.assertTrue(datos["cerrada"])
        self.assertLess(datos["triangulos"], 2_000_000)
        self.assertTrue(any("grano" in a for a in datos["avisos"]))


class Declaracion(unittest.TestCase):
    """Que PARAMETROS siga siendo legible por quien lo consume.

    La pestaña «Crear» dibuja sus controles leyendo esta declaración, y la
    pestaña «Idea» va a generar el catálogo del modelo desde aquí. Las dos
    dependen de que cada entrada esté completa.
    """

    def test_cada_parametro_esta_completo(self):
        for s in disenos.PARAMETROS:
            with self.subTest(parametro=s["clave"]):
                for campo in ("clave", "etiqueta", "tipo", "grupo"):
                    self.assertTrue(s.get(campo), "falta %s" % campo)
                if s["tipo"] == "num":
                    self.assertLess(s["min"], s["max"])
                    self.assertGreaterEqual(s["valor"], s["min"])
                    self.assertLessEqual(s["valor"], s["max"])
                elif s["tipo"] == "opcion":
                    claves = [o["clave"] for o in s["opciones"]]
                    self.assertIn(s["valor"], claves)

    def test_no_hay_claves_repetidas(self):
        claves = [s["clave"] for s in disenos.PARAMETROS]
        self.assertEqual(len(claves), len(set(claves)))

    def test_las_recetas_solo_usan_claves_declaradas(self):
        claves = {s["clave"] for s in disenos.PARAMETROS}
        for d in disenos.DISENOS:
            with self.subTest(receta=d["clave"]):
                self.assertLessEqual(set(d["valores"]), claves)

    def test_las_dependencias_apuntan_a_algo(self):
        # `depende` nombra claves de contorno, acabado, perfil o bandeja. Una
        # que no exista deja un control invisible para siempre.
        universo = set()
        for s in disenos.PARAMETROS:
            if s["tipo"] == "opcion":
                universo |= {o["clave"] for o in s["opciones"]}
        for s in disenos.PARAMETROS:
            if s.get("depende"):
                with self.subTest(parametro=s["clave"]):
                    self.assertLessEqual(set(s["depende"]), universo)


class Geometria(unittest.TestCase):
    """Las propiedades que el motor promete y de las que dependen otras cosas."""

    def test_los_contornos_son_estrellados(self):
        # El piso se cierra en abanico desde el centro, y eso sólo vale si el
        # radio es función del ángulo. La pestaña «Idea» va a apoyarse en esta
        # propiedad para guardar una silueta como r(θ); conviene tenerla
        # afirmada aquí y no de palabra.
        p = dict(disenos.DEFECTOS, **PLANTA_FIJA)
        for clave, (_, fn) in CONTORNOS.items():
            if clave == "trazado":
                continue
            with self.subTest(contorno=clave):
                f = fn(dict(p, contorno=clave))
                angulos = []
                for i in range(360):
                    x, y = f(i / 360.0)
                    angulos.append(math.atan2(y, x))
                # Recorrido antihorario y sin retrocesos: el ángulo avanza
                # siempre en el mismo sentido, que es justo lo que significa
                # «hay un solo radio por cada ángulo».
                saltos = [(b - a) % (2 * math.pi) for a, b in
                          zip(angulos, angulos[1:] + angulos[:1])]
                self.assertLess(max(saltos), math.pi,
                                "el contorno se devuelve sobre sí mismo")

    def test_el_relieve_no_se_come_la_pared(self):
        # El motor recorta el relieve a lo que la pared aguante y lo avisa.
        # Cuánto es eso lo cuida Acabados.test_el_valle_deja_pared_para_dos_hilos;
        # aquí lo único que se pide es que el aviso llegue, porque recortar en
        # silencio le cambia la pieza al usuario sin decírselo.
        p = dict(disenos.DEFECTOS, acabado="ondulado", pared=1.0,
                 onda_amplitud=3.0)
        _, datos = cuerpo.construir(disenos.normalizar(p))
        self.assertTrue(any("Relieve recortado" in a for a in datos["avisos"]))



class PlantasNuevas(unittest.TestCase):
    """Las cinco plantas de la segunda tanda.

    Lo que se comprueba de una planta es siempre lo mismo y en este orden:
    que mida lo que su ficha dice, que su valor neutro devuelva la planta de
    la que salió, que la malla cierre en todo el rango declarado, y que lo
    que la forma promete en su nombre esté de verdad en la geometría — un
    chaflán tiene que tener ocho lados y un lobulado tiene que tener valles.
    """

    NUEVAS = ("chaflan", "trapecio", "poligono", "lobulos", "rinon")

    def _planta(self, clave, **extra):
        p = dict(disenos.DEFECTOS, contorno=clave, ancho=134, fondo=76, **extra)
        p = disenos.normalizar(p)
        return CONTORNOS[clave][1](p), p

    def _puntos(self, fn, n=1440):
        return [fn(i / n) for i in range(n)]

    def test_miden_lo_que_dice_la_ficha(self):
        # Sin esto, dos plantas con los mismos milímetros no coinciden sobre
        # la mesa y el catálogo deja de poder compararse consigo mismo.
        for clave in self.NUEVAS:
            with self.subTest(contorno=clave):
                fn, _ = self._planta(clave)
                pts = self._puntos(fn)
                xs = [x for x, _ in pts]
                ys = [y for _, y in pts]
                self.assertAlmostEqual(max(xs) - min(xs), 134, delta=0.15)
                self.assertAlmostEqual(max(ys) - min(ys), 76, delta=0.15)

    def test_la_malla_cierra_en_todo_el_rango(self):
        # Los extremos de cada eje propio, que es donde una forma se rompe.
        casos = [("chaflan", {"redondeo": 0.0}), ("chaflan", {"redondeo": 80.0}),
                 ("trapecio", {"trapecio_cierre": 0.0}),
                 ("trapecio", {"trapecio_cierre": 0.75}),
                 ("poligono", {"lados": 3}), ("poligono", {"lados": 12}),
                 ("poligono", {"lados": 5, "redondeo": 0.0}),
                 ("lobulos", {"lobulos": 4, "lobulo_hondura": 0.0}),
                 ("lobulos", {"lobulos": 12, "lobulo_hondura": 0.45}),
                 ("lobulos", {"lobulos": 4, "lobulo_hondura": 0.45}),
                 ("rinon", {"rinon_hendidura": 0.0}),
                 ("rinon", {"rinon_hendidura": 0.45})]
        for clave, extra in casos:
            with self.subTest(contorno=clave, **extra):
                p = dict(disenos.DEFECTOS, contorno=clave, ancho=134, fondo=76,
                         alto=90, ranuras=3, **extra)
                _, _, _, cerrada = medir(p)
                self.assertTrue(cerrada)

    def test_el_valor_neutro_devuelve_la_planta_de_origen(self):
        # Cada una de estas tres nace de una planta que ya existía. Apagada,
        # tiene que volver exactamente a ella: es lo que permite moverse por
        # el selector sin que la pieza dé un brinco.
        parejas = [("trapecio", {"trapecio_cierre": 0.0}, "rectangulo", {}),
                   ("lobulos", {"lobulo_hondura": 0.0}, "circulo", {}),
                   ("rinon", {"rinon_hendidura": 0.0}, "circulo", {})]
        for nueva, apagada, vieja, extra in parejas:
            with self.subTest(contorno=nueva):
                a, _ = self._planta(nueva, **apagada)
                b, _ = self._planta(vieja, **extra)
                for i in range(240):
                    pa, pb = a(i / 240), b(i / 240)
                    self.assertAlmostEqual(pa[0], pb[0], delta=0.05)
                    self.assertAlmostEqual(pa[1], pb[1], delta=0.05)

    def _esquinas(self, pts):
        """Cuántas veces el contorno quiebra el rumbo.

        Se cuentan racimos y no muestras: una esquina que cae entre dos
        puntos reparte el giro entre los dos, y contándolos sueltos la misma
        esquina valdría por dos.
        """
        n = len(pts)
        rumbos = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            rumbos.append(math.atan2(by - ay, bx - ax))
        quiebra = []
        for i in range(n):
            d = (rumbos[(i + 1) % n] - rumbos[i] + math.pi) % (2 * math.pi) - math.pi
            quiebra.append(abs(d) > math.radians(6))
        return sum(1 for i in range(n) if quiebra[i] and not quiebra[i - 1])

    def test_el_chaflan_tiene_ocho_esquinas(self):
        # Un chaflán que no deja faceta es un rectángulo con otro nombre.
        fn, _ = self._planta("chaflan", redondeo=18)
        self.assertEqual(self._esquinas(self._puntos(fn, 1440)), 8)

    def test_el_chaflan_sin_corte_vuelve_a_ser_rectangulo(self):
        fn, _ = self._planta("chaflan", redondeo=0.0)
        self.assertEqual(self._esquinas(self._puntos(fn, 1440)), 4)

    def test_el_trapecio_angosta_el_frente_y_no_la_espalda(self):
        # El frente es −y. Si esto se invierte, la cuña apunta al revés y los
        # compartimentos salen anchos adelante, que es lo contrario del fin.
        fn, _ = self._planta("trapecio", trapecio_cierre=0.5)
        pts = self._puntos(fn)
        frente = max(abs(x) for x, y in pts if y < -30)
        espalda = max(abs(x) for x, y in pts if y > 30)
        self.assertLess(frente, espalda * 0.75)

    def test_el_poligono_tiene_los_lados_que_pide(self):
        for n in (3, 5, 6, 8, 12):
            with self.subTest(lados=n):
                fn, _ = self._planta("poligono", lados=n, redondeo=0.0)
                self.assertEqual(self._esquinas(self._puntos(fn, 1440)), n)

    def test_el_poligono_deja_una_faceta_plana_al_frente(self):
        # Es lo que permite arrimar la pieza a la pared sin hueco en cuña.
        for n in (3, 4, 6, 7, 8):
            with self.subTest(lados=n):
                fn, _ = self._planta("poligono", lados=n, redondeo=0.0)
                pts = self._puntos(fn, 720)
                bajo = min(y for _, y in pts)
                llanos = [x for x, y in pts if y < bajo + 0.3]
                self.assertGreater(max(llanos) - min(llanos), 134 * 0.15)

    def test_los_lobulos_son_pares_y_simetricos(self):
        # Con número impar la planta sale en forma de pera. El motor sube al
        # par de arriba, y el resultado tiene que quedar simétrico a izquierda
        # y derecha: es lo que separa un lobulado de un accidente.
        for pedidos in (4, 5, 6, 7, 9, 12):
            with self.subTest(lobulos=pedidos):
                fn, _ = self._planta("lobulos", lobulos=pedidos,
                                     lobulo_hondura=0.25)
                pts = self._puntos(fn, 720)
                for x, y in pts[:120]:
                    espejo = min(math.dist((x, y), (-bx, by)) for bx, by in pts)
                    self.assertLess(espejo, 1.0)

    def test_los_lobulos_hacen_valles_de_verdad(self):
        # Cuantos más lóbulos, más veces entra y sale el contorno. Si el radio
        # deja de oscilar, se perdió el lóbulo y quedó un óvalo.
        for n in (4, 6, 8):
            with self.subTest(lobulos=n):
                fn, _ = self._planta("lobulos", lobulos=n, lobulo_hondura=0.25)
                radios = [math.hypot(x, y) for x, y in self._puntos(fn, 720)]
                vueltas = sum(1 for i in range(720)
                              if radios[i - 1] < radios[i] > radios[(i + 1) % 720])
                self.assertEqual(vueltas, n)

    def test_la_hendidura_del_rinon_esta_en_la_espalda(self):
        # Atrás y en el centro: es lo que abraza la orilla del fregadero y lo
        # que recibe el pulgar. Adelante sería una mordida sin función.
        hondo, _ = self._planta("rinon", rinon_hendidura=0.40)
        liso, _ = self._planta("rinon", rinon_hendidura=0.0)
        # El punto más alto de la espalda deja de estar en el centro.
        pts = self._puntos(hondo)
        centro = max(y for x, y in pts if abs(x) < 4)
        borde = max(y for x, y in pts)
        self.assertLess(centro, borde - 3.0)
        # Y el frente no se toca.
        for i in range(240):
            a, b = hondo((i / 240) * 0.5 + 0.5), liso((i / 240) * 0.5 + 0.5)
            if a[1] < -20:
                self.assertAlmostEqual(math.hypot(*a), math.hypot(*b), delta=3.0)


class DivisoresEnPlantaConcava(unittest.TestCase):
    """Que un divisor no puentee un valle.

    `_cruce` devolvía el mínimo y el máximo de todos los cruces. En una planta
    convexa eso es correcto —la recta entra y sale una sola vez—, pero el
    lobulado y el riñón pueden hacerla entrar, salir y volver a entrar, y ahí
    el mínimo a máximo cruza por fuera de la pieza: el divisor asomaría por la
    pared. Esta clase es la que sostiene esa corrección.
    """

    def test_en_planta_convexa_da_lo_de_siempre(self):
        caja = [(-10, -5, 0, 0, 0), (10, -5, 0, 0, 0),
                (10, 5, 0, 0, 0), (-10, 5, 0, 0, 0)]
        self.assertEqual(cuerpo._cruce(caja, 0, 0.0), (-5.0, 5.0))
        self.assertEqual(cuerpo._cruce(caja, 1, 0.0), (-10.0, 10.0))

    def test_no_puentea_la_muesca(self):
        # Una U: la recta vertical en x = 0 cruza cuatro veces y el tramo de
        # material es el de abajo, no el que va de un brazo al otro.
        u = [(-10, -5, 0, 0, 0), (10, -5, 0, 0, 0), (10, 5, 0, 0, 0),
             (2, 5, 0, 0, 0), (2, -1, 0, 0, 0), (-2, -1, 0, 0, 0),
             (-2, 5, 0, 0, 0), (-10, 5, 0, 0, 0)]
        self.assertEqual(cuerpo._cruce(u, 0, 0.0), (-5.0, -1.0))

    def test_los_divisores_caben_en_las_plantas_nuevas(self):
        # La prueba de arriba mira la función; ésta mira la pieza entera, con
        # los divisores que de verdad llevan el portacontroles y el
        # portacubiertos.
        for clave, ranuras in (("lobulos", 3), ("rinon", 3),
                               ("trapecio", 4), ("chaflan", 4), ("poligono", 4)):
            with self.subTest(contorno=clave):
                p = dict(disenos.DEFECTOS, contorno=clave, ancho=140, fondo=76,
                         alto=95, ranuras=ranuras, divisor_alto=70,
                         lobulo_hondura=0.30, rinon_hendidura=0.35)
                malla, datos = cuerpo.construir(disenos.normalizar(p))
                self.assertTrue(datos["cerrada"])
                self.assertEqual(datos["ranuras"], ranuras)


if __name__ == "__main__":
    unittest.main(verbosity=2)
