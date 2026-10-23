#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acabados: el relieve de la pared exterior.

Un acabado es una función (s, z) -> desplazamiento en mm hacia afuera, con s
y z normalizados de 0 a 1. El interior siempre queda liso, así que la pieza
entra y sale sin trabarse y la pared no se adelgaza de más.

Pero el relieve no es lo único que declara un acabado. Declara también lo que
ese relieve le pide a la malla: cada cuánto se repite el dibujo a lo ancho y
a lo alto, y cuánto corre de lado mientras sube. De ahí sale la resolución de
la pieza —no de un número fijo—, y es lo que separa un acabado con todas las
estrías iguales de uno donde unas salen afiladas y otras mochas.

Por qué las repeticiones y no nada más la cantidad de puntos: el muestreador
reparte los puntos parejo a lo largo del contorno, así que si la vuelta
entera no lleva un número entero de puntos por estría, cada estría cae con
una fase distinta. Unas quedan muestreadas justo en la cresta y otras a medio
flanco, y el ojo lee eso como un acabado mal hecho aunque ninguna estría esté
mal dibujada. Con 480 puntos y 31 estrías —el portalápices de siempre— el
facetado perdía hasta un 12 % de la punta en unas estrías y nada en otras.
"""

import math

TAU = 2 * math.pi


def _par(m, piso=4):
    """Redondea hacia arriba a par, con un piso.

    Par a propósito: con un número par de muestras por repetición, la cresta
    y el valle caen los dos sobre un punto de la malla. Impar deja uno de los
    dos siempre a medio camino, y ahí es donde el facetado pierde el canto.

    El piso normal es cuatro, que es lo menos con lo que un dibujo todavía se
    parece a sí mismo. Baja a dos sólo cuando la pieza pide tanto relieve que
    no cabe de ninguna manera: con dos, una onda sale hecha un zigzag —roma,
    pero con su altura y todas sus estrías iguales— y eso es preferible a
    soltar el múltiplo.
    """
    m = max(piso, int(math.ceil(m - 1e-9)))
    return m + (m % 2)


class Acabado:
    """El relieve, y lo que el relieve le pide a la malla.

    `periodos_s` y `periodos_z` son cuántas veces se repite el dibujo dando
    la vuelta al contorno y subiendo la pieza. `deriva_s` es cuánto corre de
    lado el dibujo mientras sube, medido en vueltas al contorno: un dibujo
    que corre es una diagonal, y la malla sólo tiene anillos horizontales.

    `hunde` es qué parte de la amplitud se mete hacia adentro de la pared, de
    0 a 1. Casi todos los relieves van y vienen alrededor de la pared nominal
    —suben la cresta y hunden el valle la misma cantidad—, así que valen 1;
    el junco es el único que sólo pone material y no quita nada, y por eso
    vale 0. La diferencia no es cosmética: lo que decide si la pieza sale
    traslúcida en el valle es cuánta pared queda ahí.

    `deriva_z` es el espejo de `deriva_s`: cuánto corre de alto el dibujo
    mientras rodea el contorno, para el acabado que tuerce al revés —bandas
    horizontales que se corren de lado en vez de estrías verticales que
    suben en espiral. Uno bombea capas, el otro bombea segmentos; un acabado
    normal no usa ninguno de los dos.
    """

    def __init__(self, fn, amplitud, periodos_s=0, periodos_z=0, deriva_s=0.0,
                 deriva_z=0.0, hunde=1.0):
        self.fn = fn
        self.amplitud = amplitud          # desplazamiento máximo, en mm
        self.periodos_s = int(periodos_s)
        self.periodos_z = int(periodos_z)
        self.deriva_s = abs(float(deriva_s))
        self.deriva_z = abs(float(deriva_z))
        self.hunde = float(hunde)
        self.varia_z = self.periodos_z > 0 or self.deriva_s > 0.0

    def hundimiento(self):
        """Cuánto le quita este relieve a la pared, en mm."""
        return self.amplitud * self.hunde

    def __call__(self, s, z):
        return self.fn(s, z)

    def resolucion(self, perimetro, alto, grano, piso_s=0, piso_z=0, minimo=4):
        """(segmentos, capas) con los que este relieve sale entero.

        `grano` es lo más largo que se le permite medir a una faceta del
        relieve, en milímetros: el dibujo se parte hasta que ninguna faceta
        pase de ahí. `piso_s` y `piso_z` son lo que ya piden por su cuenta el
        contorno y el perfil vertical.

        Los pisos entran aquí adentro y no afuera con un `max`, y ésa es la
        parte que importa: subirlos después rompería el múltiplo. Un contorno
        que pide 480 puntos con 37 estrías da 12.97 puntos por estría, y ahí
        vuelve el acabado desigual aunque haya puntos de sobra. Lo que sale de
        aquí es siempre un múltiplo entero y par de las repeticiones, por
        encima de los dos pisos.
        """
        segmentos = piso_s
        if self.periodos_s:
            alcance = max(perimetro / grano, piso_s)
            if self.deriva_z:
                # El espejo del caso de abajo: el brinco entre un segmento y
                # el siguiente se mide en alto, no en contorno.
                alcance = max(alcance, self.deriva_z * alto / grano)
            segmentos = self.periodos_s * _par(alcance / self.periodos_s, minimo)
        elif self.deriva_z:
            segmentos = max(piso_s, int(math.ceil(self.deriva_z * alto / grano)))
        capas = piso_z
        if self.periodos_z:
            alcance = max(alto / grano, piso_z)
            if self.deriva_s:
                # Lo que se ve escalonado en una diagonal no es el alto de la
                # capa sino el brinco de lado, y ese se mide sobre el contorno.
                alcance = max(alcance, self.deriva_s * perimetro / grano)
            capas = self.periodos_z * _par(alcance / self.periodos_z, minimo)
        elif self.deriva_s:
            capas = max(piso_z, int(math.ceil(self.deriva_s * perimetro / grano)))
        return segmentos, capas


def _repeticiones(perimetro, paso):
    return max(1, round(perimetro / max(paso, 0.5)))


def liso(p, perimetro):
    return Acabado(lambda s, z: 0.0, 0.0, hunde=0.0)


def ondulado(p, perimetro):
    n = _repeticiones(perimetro, p["onda_paso"])
    a = p["onda_amplitud"]
    return Acabado(lambda s, z: a * math.cos(TAU * n * s), a, periodos_s=n)


def canal(p, perimetro):
    """Estría de cresta plana y surco angosto, como en el Portacepillos01O.

    Medida sobre ese vaso: por cada paso, la cresta plana ocupa 36 %, el surco
    plano 28 %, y los dos flancos 18 % cada uno, en curva de S. No es la onda
    (que sube y baja sin descanso) ni el facetado (de canto vivo): la luz cae
    en una franja ancha y firme por estría, con una sombra fina entre una y
    otra. Con el mismo paso se lee más marcada que la onda a igual relieve."""
    n = _repeticiones(perimetro, p["onda_paso"])
    a = p["onda_amplitud"]

    def fn(s, z):
        d = abs((n * s) % 1.0 - 0.5)          # 0 en el centro de la cresta
        if d <= 0.18:
            return a
        if d >= 0.36:
            return -a
        t = (d - 0.18) / 0.18
        return a * (1.0 - 2.0 * t * t * (3.0 - 2.0 * t))
    return Acabado(fn, a, periodos_s=n)


def facetado(p, perimetro):
    """Estrías de canto vivo en vez de redondas."""
    n = _repeticiones(perimetro, p["onda_paso"])
    a = p["onda_amplitud"]

    def fn(s, z):
        u = (n * s) % 1.0
        return a * (4.0 * abs(u - 0.5) - 1.0)
    return Acabado(fn, a, periodos_s=n)


def torsion(p, perimetro):
    """Las mismas estrías, pero girando conforme sube la pieza.

    La estría deja de ser vertical y se vuelve una hélice, así que la pieza
    necesita capas: no por el alto, sino por lo que la hélice corre de lado
    entre una capa y la siguiente. Con una vuelta entera, ese corrimiento es
    el contorno completo, y por eso una torsión cerrada pide muchísima más
    malla que una abierta.
    """
    n = _repeticiones(perimetro, p["onda_paso"])
    a = p["onda_amplitud"]
    vueltas = p["torsion_vueltas"]
    return Acabado(lambda s, z: a * math.cos(TAU * n * (s - vueltas * z)), a,
                   periodos_s=n, periodos_z=round(n * abs(vueltas)),
                   deriva_s=vueltas)


def torsion_lado(p, perimetro):
    """La torsión, girada 90°: bandas horizontales que se corren de lado en
    vez de estrías verticales que suben en espiral.

    Es la misma hélice —mismo coseno, mismas vueltas—, pero con los papeles
    de `s` y `z` cambiados: aquí lo que se repite es la altura (bandas
    apiladas, como el escalonado) y lo que tuerce es el contorno. El dibujo
    de base ya no lee como estría que sube, lee como cinta que envuelve la
    pieza en espiral, que es lo que pide una silueta más ancha que alta como
    el portacontroles: la torsión normal se nota subiendo una pared de 88 mm,
    ésta se nota recorriendo los 145 mm de frente.
    """
    nz = max(1, round(p["alto"] / max(p["onda_paso"], 0.5)))
    a = p["onda_amplitud"]
    vueltas = p["torsion_vueltas"]
    return Acabado(lambda s, z: a * math.cos(TAU * nz * (z - vueltas * s)), a,
                   periodos_z=nz, periodos_s=round(nz * abs(vueltas)),
                   deriva_z=vueltas)


def escalonado(p, perimetro):
    """Anillos horizontales en vez de estrías verticales."""
    a = p["onda_amplitud"]
    n = max(1, round(p["alto"] / max(p["onda_paso"], 0.5)))
    return Acabado(lambda s, z: a * math.cos(TAU * n * z), a, periodos_z=n)


def rombo(p, perimetro):
    """Moleteado: dos hélices cruzadas, una a cada lado.

    Sale de multiplicar la estría vertical por una horizontal, que es lo
    mismo que sumar dos torsiones opuestas. Los rombos van más altos que
    anchos a propósito: cuadrados se leen como tela de mosquitero."""
    n = _repeticiones(perimetro, p["onda_paso"])
    nz = max(1, round(p["alto"] / max(p["onda_paso"] * 1.6, 0.5)))
    a = p["onda_amplitud"]
    return Acabado(lambda s, z: a * math.cos(TAU * n * s) * math.cos(TAU * nz * z),
                   a, periodos_s=n, periodos_z=nz)


def junco(p, perimetro):
    """Cañas redondas separadas por pared lisa.

    No es la onda. La onda sube y baja sin descanso y de lejos se lee como
    textura pareja; aquí cada caña es un lomo redondo y entre caña y caña
    queda pared plana. Eso hace que la luz caiga en una franja angosta y
    brillante por caña y el resto quede mate, que es de dónde saca el brillo
    el vidrio labrado. La caña ocupa poco más de la mitad del paso: llenándolo
    entero vuelve a ser una onda.
    """
    n = _repeticiones(perimetro, p["onda_paso"])
    a = p["onda_amplitud"]
    ancho = 0.55                     # fracción del paso que ocupa la caña

    def fn(s, z):
        u = (n * s) % 1.0 - 0.5
        if abs(u) > ancho / 2.0:
            return 0.0
        # cos² se apoya en cero con pendiente cero: la caña nace de la pared
        # lisa sin dejar canto, y no hay una línea donde agarrarse con la uña.
        return a * math.cos(math.pi * u / ancho) ** 2
    # hunde=0: la caña nace de la pared y sube, nunca se mete. Es el único
    # acabado que puede llevar relieve hondo sobre pared delgada sin dejar el
    # valle en un solo hilo, porque no tiene valle.
    return Acabado(fn, a, periodos_s=n, hunde=0.0)


def espiga(p, perimetro):
    """El facetado quebrado en zigzag: hileras de galones.

    La estría de canto vivo sigue siendo la misma, pero cada tanto de altura
    se dobla y vuelve, y las puntas de una hilera caen entre las de la de
    abajo. Es el único acabado que se lee como papel doblado en vez de como
    pieza torneada, porque el quiebre va en vertical y ninguna máquina de
    revolución puede hacerlo.

    El galón es una diagonal y la malla sólo tiene anillos horizontales, así
    que es el acabado que más capas pide: lo que manda no es el alto de la
    hilera sino cuánto corre el quiebre de lado dentro de ella.
    """
    n = _repeticiones(perimetro, p["onda_paso"])
    a = p["onda_amplitud"]
    hileras = max(1, round(p["alto"] / max(p["onda_paso"] * 3.2, 0.5)))
    vaiven = 0.42

    def fn(s, z):
        v = (hileras * z) % 1.0
        zig = 4.0 * abs(v - 0.5) - 1.0            # vaivén triangular de -1 a 1
        u = (n * s + vaiven * zig) % 1.0
        return a * (4.0 * abs(u - 0.5) - 1.0)
    # De ida y de vuelta por hilera, y cada viaje corre 2·vaivén pasos de
    # estría: eso es lo que la malla tiene que seguir sin escalonarse.
    return Acabado(fn, a, periodos_s=n, periodos_z=hileras,
                   deriva_s=hileras * 4.0 * vaiven / n)


def lino(p, perimetro):
    """Trama fina, como tela tensada sobre la pieza.

    Dos ondas cruzadas sumadas, no multiplicadas: multiplicadas dan rombos
    —eso ya es el moleteado—, sumadas dan hilo y pasada. De cerca se ve el
    tejido; de lejos sólo se ve una pared que no está pulida, y ese es el
    punto. Pide paso corto: arriba de 6 mm los hilos se separan tanto que
    deja de haber tela y quedan surcos.
    """
    n = _repeticiones(perimetro, p["onda_paso"] * 0.55)
    nz = max(1, round(p["alto"] / max(p["onda_paso"] * 0.9, 0.5)))
    a = p["onda_amplitud"]
    return Acabado(lambda s, z: a * 0.5 * (math.cos(TAU * n * s)
                                           + math.cos(TAU * nz * z)),
                   a, periodos_s=n, periodos_z=nz)


def martillado(p, perimetro):
    """Hoyuelos poco profundos, repartidos sin orden aparente.

    Salen de sumar tres tramas que no encajan entre sí: el dibujo tarda
    muchísimo en repetirse y el ojo no le encuentra la cuenta. Es el golpeteo
    del cobre batido o del barro apretado con el pulgar —irregular a
    propósito, pero siempre el mismo, porque está escrito y no sorteado.

    Las tres frecuencias del contorno son enteras a la fuerza. Tienen que
    serlo: el contorno se cierra sobre sí mismo, y una onda que no dé un
    número entero de vueltas deja un escalón en la costura.

    La resolución la manda la trama más apretada de las tres, no la primera.
    Medirla por la primera era lo que le daba al martillado un hoyuelo hondo
    y el de al lado plano: no era el dibujo, era el muestreo.
    """
    n = _repeticiones(perimetro, p["onda_paso"])
    nz = max(1, round(p["alto"] / max(p["onda_paso"], 0.5)))
    a = p["onda_amplitud"]
    n2, n3 = max(1, round(n * 1.7)), max(1, round(n * 0.6))

    def fn(s, z):
        v = (math.cos(TAU * n * s) * math.cos(TAU * nz * z)
             + 0.70 * math.cos(TAU * n2 * s + 1.1) * math.cos(TAU * nz * 0.62 * z + 2.3)
             + 0.45 * math.cos(TAU * n3 * s + 3.7) * math.cos(TAU * nz * 1.41 * z + 0.4))
        return a * v / 2.15
    return Acabado(fn, a, periodos_s=max(n, n2, n3),
                   periodos_z=max(nz, int(math.ceil(nz * 1.41))))


def meandro(p, perimetro):
    """Lóbulos abultados que se alternan: uno gordo arriba, el vecino gordo
    abajo, encajados como piezas de rompecabezas.

    Es el portacubiertos de piedra de la foto del 2026-10-22. La primera
    versión eran bandas paralelas con el borde en «S» y se leía como espiral
    —una tela torcida—; en la foto cada lóbulo es una gota o un bolo con su
    propio bulbo, y el bulbo de uno cae frente al cuello del de al lado. El
    surco que queda entre los dos es el que dibuja la «S».

    Cada lóbulo es una almohada: cara un poco abombada y canto redondo de
    `meandro_canto` mm, sin arista donde se agarre la uña. Sólo pone material
    (hunde=0), como el junco: el surco es la pared nominal. Abajo el lóbulo
    se cierra redondo antes de la base; arriba llega hasta la boca.

    El número de lóbulos es par a la fuerza, o el último choca con el
    primero en la costura con el mismo bulbo. El primero se centra en el
    frente del rectángulo para que el frente salga simétrico.
    """
    paso = max(10.0, float(p.get("meandro_paso", 60.0)))
    n = max(2, int(round(perimetro / paso / 2.0)) * 2)
    pr = perimetro / n                                  # lóbulo + surco, en mm
    a = p["onda_amplitud"]
    alto = float(p["alto"])
    surco = min(0.8, max(0.05, float(p.get("meandro_surco", 0.30))))
    gordura = float(p.get("meandro_cintura", 0.35))     # cuánto cambia de ancho
    vaiven = float(p.get("meandro_vaiven", 0.0))        # corre de lado, en pasos
    canto = max(0.5, float(p.get("meandro_canto", 4.0)))
    pie = float(p.get("meandro_pie", 6.0))              # mm sin lóbulo sobre la base
    h0 = pr * (1.0 - surco) / 2.0                       # medio ancho de lóbulo
    centro = 0.0
    if p.get("contorno") == "rectangulo":
        r = min(p["redondeo"], p["ancho"] / 2.0, p["fondo"] / 2.0)
        centro = (p["ancho"] / 2.0 - r) / perimetro
    elif p.get("contorno") == "superelipse":
        # Arranca en el extremo derecho y gira antihorario: el centro del
        # frente queda a tres cuartos de vuelta.
        centro = 0.75

    def ancho(k, z):
        # Bulbo arriba (z≈0.78) y cuello abajo, o al revés en el vecino.
        pico = 0.78 if k % 2 == 0 else 0.22
        return h0 * (1.0 + gordura * math.cos(TAU * (z - pico)))

    def fn(s, z):
        x = ((s - centro) % 1.0) * perimetro
        k0 = int(math.floor(x / pr + 0.5))
        zmm = z * alto
        ez = zmm - pie
        mejor = 0.0
        for k in (k0 - 1, k0, k0 + 1):
            signo = 1.0 if k % 2 == 0 else -1.0
            xc = k * pr + signo * vaiven * pr * math.sin(TAU * z)
            h = ancho(k % n, z)
            dist = abs(x - xc)
            e = h - dist
            # Mínimo suave con el pie: el lóbulo se cierra redondo abajo.
            e = -canto * math.log(math.exp(-e / canto) + math.exp(-ez / canto))
            borde = 0.5 * (1.0 + math.tanh(1.6 * e / canto))
            almohada = 1.0 - 0.25 * min(1.0, dist / max(h, 1e-6)) ** 2
            mejor = max(mejor, borde * almohada)
        return a * mejor
    deriva = 2.0 * (gordura * h0 + vaiven * pr) / perimetro
    return Acabado(fn, a, periodos_s=n, periodos_z=2, deriva_s=deriva, hunde=0.0)

ACABADOS = {
    "liso": ("Liso", liso),
    "ondulado": ("Ondulado", ondulado),
    "facetado": ("Facetado", facetado),
    "canal": ("Canal (cresta plana)", canal),
    "torsion": ("Torsión", torsion),
    "torsion_lado": ("Torsión de lado", torsion_lado),
    "escalonado": ("Escalonado", escalonado),
    "rombo": ("Romboidal", rombo),
    "junco": ("Junco", junco),
    "espiga": ("Espiga", espiga),
    "lino": ("Lino", lino),
    "martillado": ("Martillado", martillado),
    "meandro": ("Meandro (lóbulos alternados)", meandro),
}
