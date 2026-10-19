#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contornos: la planta del recipiente vista desde arriba.

Cada contorno es una función t -> (x, y) con t entre 0 y 1, recorrida en
sentido antihorario. El muestreador se encarga de repartir los puntos parejo
y de sacar las normales, así que agregar una forma nueva es escribir una
función corta y registrarla en CONTORNOS.
"""

import math

from . import trazo as T

TAU = 2 * math.pi


def _escalar(fn, ancho, fondo):
    """Lleva una curva unitaria (dentro de [-1,1]) a milímetros."""
    def f(t):
        x, y = fn(t)
        return (x * ancho / 2.0, y * fondo / 2.0)
    return f


def _frac_redondeo(p):
    """El redondeo leído como fracción del semieje corto, de 0 a 1.

    Es la misma lectura que ya hacen la superelipse y la hoja: el control
    viaja en milímetros porque en el rectángulo son milímetros de verdad, y
    las formas que no tienen esquina que redondear lo reinterpretan.
    """
    corto = min(p["ancho"], p["fondo"]) / 2.0
    if corto <= 0:
        return 1.0
    return min(1.0, max(0.0, float(p["redondeo"]) / corto))


def _ruta(vertices, radio=0.0):
    """Camino cerrado que pasa por `vertices` —antihorario— con las esquinas
    suavizadas por un arco de radio `radio`.

    Es la misma máquina que arma el rectángulo redondeado: tramos rectos y
    arcos recorridos por longitud, para que el muestreador reparta los puntos
    parejo. La diferencia es que aquí sirve para cualquier polígono convexo,
    y con radio 0 deja las esquinas vivas — que es justo lo que quiere un
    chaflán, donde el corte recto *es* el dibujo.

    Cada filete se recorta a la mitad del lado más corto que toca: dos
    esquinas seguidas no pueden comerse el mismo tramo o el camino se
    devolvería sobre sí mismo.
    """
    n = len(vertices)
    r = max(0.0, float(radio))
    esquinas = []
    for i in range(n):
        vx, vy = vertices[i]
        px, py = vertices[i - 1]
        sx, sy = vertices[(i + 1) % n]
        ux, uy = vx - px, vy - py
        wx, wy = sx - vx, sy - vy
        lu = math.hypot(ux, uy) or 1.0
        lw = math.hypot(wx, wy) or 1.0
        ux, uy = ux / lu, uy / lu
        wx, wy = wx / lw, wy / lw
        giro = math.atan2(ux * wy - uy * wx, ux * wx + uy * wy)
        media = abs(giro) / 2.0
        if r <= 1e-9 or media <= 1e-9:
            esquinas.append(((vx, vy), (vx, vy), (vx, vy), 0.0, giro))
            continue
        d = min(r * math.tan(media), lu / 2.0, lw / 2.0)
        rr = d / math.tan(media)
        p1 = (vx - ux * d, vy - uy * d)
        p2 = (vx + wx * d, vy + wy * d)
        lado = 1.0 if giro > 0 else -1.0
        centro = (p1[0] - uy * rr * lado, p1[1] + ux * rr * lado)
        esquinas.append((p1, p2, centro, rr, giro))

    tramos = []
    for i in range(n):
        a, b = esquinas[i - 1][1], esquinas[i][0]
        largo = math.dist(a, b)
        if largo > 1e-12:
            tramos.append(("r", a, b, largo))
        p1, _, centro, rr, giro = esquinas[i]
        if rr > 1e-12:
            ang0 = math.atan2(p1[1] - centro[1], p1[0] - centro[0])
            tramos.append(("a", centro, rr, ang0, giro, abs(rr * giro)))
    total = sum(tr[-1] for tr in tramos) or 1.0

    def f(t):
        s = (t % 1.0) * total
        for tr in tramos:
            if s > tr[-1]:
                s -= tr[-1]
                continue
            u = s / tr[-1]
            if tr[0] == "r":
                _, a, b, _ = tr
                return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            _, centro, rr, ang0, giro, _ = tr
            ang = ang0 + giro * u
            return (centro[0] + rr * math.cos(ang), centro[1] + rr * math.sin(ang))
        return vertices[0]
    return f


def circulo(p):
    return _escalar(lambda t: (math.cos(TAU * t), math.sin(TAU * t)),
                    p["ancho"], p["fondo"])


def superelipse(p):
    # El redondeo se reinterpreta como exponente: mucho redondeo tira a
    # elipse, poco redondeo tira a rectángulo de esquinas suaves.
    corto = min(p["ancho"], p["fondo"]) / 2.0
    frac = min(1.0, max(0.0, p["redondeo"] / corto)) if corto else 1.0
    k = 2.0 + 8.0 * (1.0 - frac)

    def f(t):
        a = TAU * t
        c, s = math.cos(a), math.sin(a)
        return (math.copysign(abs(c) ** (2.0 / k), c),
                math.copysign(abs(s) ** (2.0 / k), s))
    return _escalar(f, p["ancho"], p["fondo"])


def rectangulo(p):
    """Rectángulo de esquinas redondeadas, con el radio en milímetros."""
    a, b = p["ancho"] / 2.0, p["fondo"] / 2.0
    r = max(0.01, min(p["redondeo"], a - 0.01, b - 0.01))
    sx, sy = a - r, b - r
    arco = r * math.pi / 2.0
    tramos = [
        ("r", (-sx, -b), (sx, -b), 2 * sx),
        ("a", (sx, -sy), -math.pi / 2, arco),
        ("r", (a, -sy), (a, sy), 2 * sy),
        ("a", (sx, sy), 0.0, arco),
        ("r", (sx, b), (-sx, b), 2 * sx),
        ("a", (-sx, sy), math.pi / 2, arco),
        ("r", (-a, sy), (-a, -sy), 2 * sy),
        ("a", (-sx, -sy), math.pi, arco),
    ]
    total = sum(t[-1] for t in tramos)

    def f(t):
        s = (t % 1.0) * total
        for tramo in tramos:
            largo = tramo[-1]
            if s > largo:
                s -= largo
                continue
            u = s / largo
            if tramo[0] == "r":
                _, p0, p1, _ = tramo
                return (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
            _, centro, ang0, _ = tramo
            ang = ang0 + u * math.pi / 2
            return (centro[0] + r * math.cos(ang), centro[1] + r * math.sin(ang))
        return (a, -sy)
    return f


def ovalo(p):
    """Pista de atletismo: los lados cortos son semicírculos completos."""
    q = dict(p)
    q["redondeo"] = min(p["ancho"], p["fondo"]) / 2.0
    return rectangulo(q)


def _encajar(f, muestras=720):
    """Recentra y estira la curva para que llene justo el cuadrado [-1,1].

    Es un ajuste afín —correr y escalar, nada más—, así que no deforma el
    dibujo: sólo garantiza que «ancho» y «fondo» sean de verdad las medidas
    exteriores. Sin esto, una forma que se muerde a sí misma (la hendidura
    del riñón, el valle del pliegue) saldría más chica que lo que pide la
    ficha, y dos plantas distintas con los mismos milímetros no coincidirían.
    """
    puntos = [f(i / muestras) for i in range(muestras)]
    xs = [x for x, _ in puntos]
    ys = [y for _, y in puntos]
    cx, ex = (min(xs) + max(xs)) / 2.0, (max(xs) - min(xs)) / 2.0 or 1.0
    cy, ey = (min(ys) + max(ys)) / 2.0, (max(ys) - min(ys)) / 2.0 or 1.0

    def g(t):
        x, y = f(t)
        return ((x - cx) / ex, (y - cy) / ey)
    return g


def hoja(p):
    """Hoja: dos arcos que se juntan en punta, uno frente al otro.

    Es la elipse llevada al otro lado de la superelipse: en vez de engordar
    hacia el rectángulo, adelgaza hacia la punta. El redondeo dice cuánto —en
    0 las puntas quedan vivas y subiéndolo la hoja vuelve a ser elipse.
    """
    corto = min(p["ancho"], p["fondo"]) / 2.0
    frac = min(1.0, max(0.0, p["redondeo"] / corto)) if corto else 1.0
    e = 2.0 - frac       # 1 = elipse; 2 = punta de ángulo vivo pero finito

    def f(t):
        a = TAU * t
        s = math.sin(a)
        return (math.cos(a), math.copysign(abs(s) ** e, s))
    return _escalar(f, p["ancho"], p["fondo"])


def arco(p):
    """Medio punto: el frente es una curva llena y la espalda se aplana.

    Es la planta que se arrima a la pared sin dejar el hueco en cuña que deja
    un redondo. Aplanado en 1 la espalda queda recta del todo; en 0 vuelve a
    ser elipse. La unión no tiene esquina: la mitad de abajo es la misma curva,
    nada más que aplastada, así que llega al borde igual de vertical. Por eso
    el aplanado se topa en 0.9 y no en 1: aplastada del todo la espalda es una
    recta, y una recta llega horizontal. Ahí aparecen dos escuadras.
    """
    plano = max(0.0, min(0.9, float(p["arco_plano"])))

    def f(t):
        a = TAU * t
        s = math.sin(a)
        return (math.cos(a), s if s >= 0.0 else s * (1.0 - plano))
    return _escalar(_encajar(f), p["ancho"], p["fondo"])


def plegado(p):
    """Acanalado: pliegues rectos que alternan cresta y valle, como una tira
    de papel doblada en acordeón y cerrada en un aro.

    Los tramos van rectos a propósito —el papel no se curva, se quiebra—, así
    que la pared sale en facetas planas y la luz se corta de una a la otra.

    Es el único relieve que puede ser hondo. Un acabado está topado por el
    espesor de la pared —un milímetro y pico— porque los divisores y el piso
    tienen que quedar embebidos en el material; un pliegue de planta se lleva
    la pared entera con él y puede ir a ocho milímetros. Por eso la caña vive
    aquí y no allá. Pero hondura es lo que separa el vidrio labrado de la
    estrella de navidad: de 0.10 para arriba deja de leerse como pieza.
    """
    n = max(3, int(p["pliegues"]))
    prof = max(0.0, min(0.16, float(p["pliegue_profundidad"])))
    total = 2 * n
    vertices = [((1.0 if j % 2 == 0 else 1.0 - prof) * math.cos(TAU * j / total),
                 (1.0 if j % 2 == 0 else 1.0 - prof) * math.sin(TAU * j / total))
                for j in range(total)]

    def f(t):
        u = (t % 1.0) * total
        j = int(u)
        u -= j
        ax, ay = vertices[j % total]
        bx, by = vertices[(j + 1) % total]
        return (ax + (bx - ax) * u, ay + (by - ay) * u)
    return _escalar(_encajar(f), p["ancho"], p["fondo"])


def guijarro(p):
    """Canto rodado: un redondo al que dos ondas largas le quitan la simetría.

    No hay eje ni repetición que el ojo pueda contar, y por eso se lee como
    piedra y no como pieza torneada. La irregularidad está escrita, no
    sorteada: el mismo diseño da siempre la misma piedra.
    """
    k = max(0.0, min(0.3, float(p["guijarro_irregular"])))

    def f(t):
        a = TAU * t
        r = 1.0 + k * (0.62 * math.cos(2 * a + 0.9)
                       + 0.38 * math.cos(3 * a + 2.4))
        return (r * math.cos(a), r * math.sin(a))
    return _escalar(_encajar(f), p["ancho"], p["fondo"])


def trazado(p):
    """La silueta que salió de una imagen.

    No hay fórmula: los radios vienen guardados en el parámetro «trazo», y
    aquí sólo se interpolan y se encajan en el cuadro pedido. Ese encaje es el
    mismo que usan la hoja, el arco, el pliegue y el guijarro, así que una
    silueta trazada ocupa en la mesa exactamente los milímetros que dice su
    ficha, igual que cualquier otra planta.

    Sin trazo —o con uno que no se pudo leer— sale un círculo. Degradar es lo
    correcto aquí: el contorno se elige en un selector y el archivo se carga
    en otro lado, así que el estado «trazado pero todavía sin imagen» es un
    paso normal del camino, no un error del usuario.
    """
    radios = T.decodificar(p.get("trazo", ""))
    if not radios:
        return circulo(p)

    def f(t):
        r = T.radio_en(radios, t)
        a = TAU * t
        return (r * math.cos(a), r * math.sin(a))
    return _escalar(_encajar(f), p["ancho"], p["fondo"])


# ── Las plantas de la segunda tanda ───────────────────────────────────────
#
# Las nueve primeras salieron de la pregunta «qué siluetas hay». Estas cinco
# salieron de otra: qué le falta a un portacontroles y a un portacubiertos,
# que son las dos piezas que de verdad se están fabricando. Las dos son
# recipientes divididos que se apoyan en algo —el brazo del sillón, la orilla
# del fregadero— y las dos se leen de lejos por su planta.
#
# Ninguna necesita soportes: una planta es una extrusión vertical, y lo que
# el motor tiene que vigilar aquí no es el voladizo sino que la cara interior
# no se cruce en un valle angosto. De eso ya se encarga `_pared_se_cruza`.


def chaflan(p):
    """Rectángulo con las esquinas cortadas a bisel, no redondeadas.

    El corte recto es el dibujo: donde el rectángulo redondeado suaviza y
    desaparece, el chaflán deja una faceta que atrapa la luz de otro modo que
    las cuatro caras, y es lo que separa una caja de una pieza. El redondeo se
    lee aquí como el largo del corte —en milímetros, igual que en el
    rectángulo—, así que en 0 vuelve a ser un rectángulo de esquina viva.

    Se construye en milímetros y sin encajar: los ocho vértices ya caen justo
    sobre el rectángulo pedido, así que el ancho y el fondo son exactos.
    """
    a, b = p["ancho"] / 2.0, p["fondo"] / 2.0
    c = max(0.0, min(float(p["redondeo"]), a * 0.9, b * 0.9))
    if c <= 0.01:
        return _ruta([(-a, -b), (a, -b), (a, b), (-a, b)])
    return _ruta([(-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c),
                  (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c)])


def trapecio(p):
    """Cuña: la espalda ancha y el frente angosto.

    Es la planta del portacontroles que no es una caja. Con ranuras, los
    compartimentos salen en abanico —anchos atrás, estrechos adelante—, así
    que los controles se escalonan y se ven todos en vez de esconderse unos
    detrás de otros. Y arrimada a la pared, la cuña deja el frente despejado.

    El dibujo es el rectángulo redondeado con el ancho estrechándose hacia el
    frente. El encaje devuelve la parte más ancha a la medida pedida, así que
    «ancho» sigue siendo el ancho de la espalda.
    """
    base = rectangulo(p)
    cierre = max(0.0, min(0.75, float(p["trapecio_cierre"])))
    b = p["fondo"] / 2.0 or 1.0

    def f(t):
        x, y = base(t)
        v = max(-1.0, min(1.0, y / b))          # −1 el frente, +1 la espalda
        return (x * (1.0 - cierre * (1.0 - v) / 2.0), y)
    return _escalar(_encajar(f), p["ancho"], p["fondo"])


def poligono(p):
    """Polígono facetado de esquinas redondeadas, estirado al cuadro pedido.

    Lo que aporta que no aporten la superelipse ni el rectángulo son las
    aristas verticales: la superelipse curva la pared y la luz resbala, el
    polígono la quiebra y cada faceta toma un tono distinto. Un hexágono de
    134 × 76 no es un óvalo con esquinas, es otra pieza.

    Los lados se acomodan con una faceta centrada al frente y otra atrás, que
    es lo que deja la pieza apoyarse contra algo sin dejar hueco en cuña. Con
    número impar de lados sólo la del frente queda plana, y la punta va atrás.
    """
    n = max(3, min(12, int(p["lados"])))
    vertices = [(math.cos(-math.pi / 2 + math.pi / n + TAU * k / n),
                 math.sin(-math.pi / 2 + math.pi / n + TAU * k / n))
                for k in range(n)]
    # El radio del filete viaja en unidades de la curva unitaria, no en
    # milímetros: el estirado posterior lo deforma igual que deforma el resto
    # del dibujo, que es lo que hace que un hexágono estirado siga leyéndose
    # como hexágono.
    r = 0.5 * _frac_redondeo(p)
    return _escalar(_encajar(_ruta(vertices, r)), p["ancho"], p["fondo"])


def rinon(p):
    """Riñón: un óvalo con una hendidura en la espalda.

    Es la planta que se abraza a una esquina y la que la mano agarra sin
    pensarlo. En el fregadero, la hendidura recibe la orilla de la tarja; en
    la mesa, deja meter el pulgar para levantarla con una mano.

    La hendidura es una muesca suave —no un corte—, centrada en la espalda y
    apagándose antes de llegar a los costados, para que no aparezca esquina
    viva en ningún punto. Pasando de 0.30 el valle se cierra bastante para que
    el motor avise de que la cara interior se cruza: es el aviso correcto, y
    se arregla bajando la pared o la hendidura.
    """
    k = max(0.0, min(0.45, float(p["rinon_hendidura"])))

    def f(t):
        a = TAU * t
        d = abs(((a - math.pi / 2) + math.pi) % TAU - math.pi)
        muesca = k * math.cos(min(d, math.pi / 2)) ** 4
        r = 1.0 - muesca
        return (r * math.cos(a), r * math.sin(a))
    return _escalar(_encajar(f), p["ancho"], p["fondo"])


def lobulos(p):
    """Lobulado: el contorno sale y entra en pétalos alrededor.

    Donde el plegado quiebra en facetas rectas, éste ondula: los lóbulos son
    arcos llenos y los valles también, sin una sola arista. De lejos se lee
    como pieza torneada o de cerámica prensada, y de cerca los valles hacen
    columnas de sombra que suben con la pieza.

    Los valles se reparten por el **perímetro** y se meten por la normal, no
    por el ángulo desde el centro. La diferencia manda: repartidos por ángulo,
    un óvalo de 134 × 76 —que es el portacubiertos— se come la onda en los
    costados y la concentra en las puntas, y en vez de un trébol sale una
    pera. Medido sobre el perímetro, cada lóbulo mide lo mismo que los demás
    sea cual sea la proporción de la pieza, y la hondura son milímetros de
    valle y no una fracción de un radio que aquí no existe.

    Los lóbulos van de dos en dos, y no es un capricho. La pieza tiene dos
    ejes de simetría; una corona de lóbulos sólo los respeta si son pares.
    Con número impar, un lóbulo cae en una punta y un valle en la otra, y la
    planta sale en forma de pera — se probó y es lo que pasa. Un valor impar
    se sube al par de arriba en vez de dejar salir la pera.
    """
    n = max(4, min(12, int(math.ceil(float(p["lobulos"]) / 2.0)) * 2))
    h = max(0.0, min(0.45, float(p["lobulo_hondura"])))
    base = _escalar(lambda t: (math.cos(TAU * t), math.sin(TAU * t)),
                    p["ancho"], p["fondo"])
    if h <= 1e-6:
        return base

    hondo = h * min(p["ancho"], p["fondo"]) / 2.0
    m = 1440
    puntos = [base(i / m) for i in range(m)]
    acum = [0.0]
    for i in range(m):
        acum.append(acum[-1] + math.dist(puntos[i], puntos[(i + 1) % m]))
    total = acum[-1] or 1.0

    ondulado = []
    for i in range(m):
        ax, ay = puntos[i - 1]
        bx, by = puntos[(i + 1) % m]
        tx, ty = bx - ax, by - ay
        largo = math.hypot(tx, ty) or 1.0
        nx, ny = ty / largo, -tx / largo         # normal hacia afuera
        # n vueltas enteras sobre el perímetro: la onda cierra sin escalón.
        valle = hondo * (1.0 - math.cos(TAU * n * acum[i] / total)) / 2.0
        ondulado.append((puntos[i][0] - nx * valle, puntos[i][1] - ny * valle))

    def f(t):
        u = (t % 1.0) * m
        j = int(u)
        w = u - j
        ax, ay = ondulado[j % m]
        bx, by = ondulado[(j + 1) % m]
        return (ax + (bx - ax) * w, ay + (by - ay) * w)
    return _escalar(_encajar(f), p["ancho"], p["fondo"])


# El orden es el de la lista que ve el usuario, y va de lo recto a lo suelto:
# primero las cajas, luego las facetadas, luego las curvas, y al final las que
# ya no tienen eje de simetría.
CONTORNOS = {
    "rectangulo": ("Rectángulo redondeado", rectangulo),
    "chaflan": ("Rectángulo achaflanado", chaflan),
    "trapecio": ("Trapecio / cuña", trapecio),
    "superelipse": ("Superelipse", superelipse),
    "poligono": ("Polígono facetado", poligono),
    "plegado": ("Plegado", plegado),
    "ovalo": ("Óvalo", ovalo),
    "circulo": ("Círculo / elipse", circulo),
    "hoja": ("Hoja", hoja),
    "arco": ("Arco de espalda plana", arco),
    "lobulos": ("Lobulado", lobulos),
    "rinon": ("Riñón", rinon),
    "guijarro": ("Guijarro", guijarro),
    "trazado": ("Trazado de imagen", trazado),
}


def muestrear(fn, n, sobremuestreo=8):
    """Reparte n puntos parejo a lo largo de la curva.

    Devuelve (lista de (x, y, nx, ny, s), perímetro), donde (nx, ny) es la
    normal hacia afuera y s es el avance normalizado de 0 a 1.
    """
    total = n * sobremuestreo
    bruto = [fn(i / total) for i in range(total)]

    acum = [0.0]
    for i in range(total):
        acum.append(acum[-1] + math.dist(bruto[i], bruto[(i + 1) % total]))
    perimetro = acum[-1]

    puntos, j = [], 0
    for i in range(n):
        s = perimetro * i / n
        while j < total - 1 and acum[j + 1] < s:
            j += 1
        tramo = acum[j + 1] - acum[j]
        u = 0.0 if tramo <= 0 else (s - acum[j]) / tramo
        ax, ay = bruto[j]
        bx, by = bruto[(j + 1) % total]
        puntos.append((ax + (bx - ax) * u, ay + (by - ay) * u))

    salida = []
    for i in range(n):
        ax, ay = puntos[i - 1]
        bx, by = puntos[(i + 1) % n]
        tx, ty = bx - ax, by - ay
        largo = math.hypot(tx, ty) or 1.0
        salida.append((puntos[i][0], puntos[i][1], ty / largo, -tx / largo, i / n))
    return salida, perimetro
