#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arma el recipiente juntando contorno + acabado + perfil + divisores + base.

Todos los productos de la línea salen de aquí: lo único que cambia entre
ellos son los valores de los parámetros. Si la receta pide bandeja, la pieza
se le pide a `bandeja.py` y sale como un segundo objeto en el mismo archivo.

El orden importa. Primero se resuelve la base perforada, porque si el
drenaje no sale hay que armar el casco con piso sólido en vez de como tubo.
"""

import math

from . import bandeja as B
from . import borde as BO
from . import malla as M
from .acabados import ACABADOS
from .contornos import CONTORNOS, muestrear
from .cuello import CUELLOS
from .perfiles import PERFILES

DENSIDAD = {"PLA": 1.24, "PETG": 1.27, "ABS": 1.04, "TPU": 1.21}


def _loft(secciones):
    """Sólido cerrado que pasa por una lista de (puntos, z). Todas las
    secciones llevan el mismo número de puntos, en sentido antihorario."""
    m = M.Malla()
    n = len(secciones[0][0])
    anillos = [[m.punto(x, y, z) for x, y in pts] for pts, z in secciones]
    for k in range(len(anillos) - 1):
        for i in range(n):
            j = (i + 1) % n
            m.quad(anillos[k][i], anillos[k][j], anillos[k + 1][j], anillos[k + 1][i])
    for extremo, anillo, signo in ((0, anillos[0], -1), (-1, anillos[-1], 1)):
        pts, z = secciones[extremo]
        c = m.punto(sum(x for x, _ in pts) / n, sum(y for _, y in pts) / n, z)
        for i in range(n):
            j = (i + 1) % n
            if signo < 0:
                m.cara(c, anillo[j], anillo[i])
            else:
                m.cara(c, anillo[i], anillo[j])
    return m


def _cruce(anillo, eje, corte):
    """Dónde corta al anillo la recta perpendicular a `eje` en `corte`.

    Con eje 0 la recta es vertical y devuelve (ymin, ymax); con eje 1 es
    horizontal y devuelve (xmin, xmax). Es la misma cuenta con las
    coordenadas cambiadas de lugar, y tenerla en los dos sentidos es lo que
    permite cruzar divisores en rejilla.

    Devuelve un tramo que está de verdad dentro de la pieza, no el mínimo y el
    máximo de todos los cruces. En una planta convexa da lo mismo —la recta
    entra y sale una sola vez—, pero con una planta cóncava, la recta puede
    entrar, salir por un valle y volver a entrar; ahí, mínimo a máximo
    puentearía el valle y el divisor asomaría por fuera de la pared. Ordenando
    los cruces, los tramos de dentro son los pares (0,1), (2,3)…, y el que le
    toca al divisor es el que pasa por el centro de la pieza.
    """
    otro = 1 - eje
    cruces = []
    n = len(anillo)
    for i in range(n):
        a = anillo[i]
        b = anillo[(i + 1) % n]
        if (a[eje] > corte) != (b[eje] > corte):
            t = (corte - a[eje]) / (b[eje] - a[eje])
            cruces.append(a[otro] + t * (b[otro] - a[otro]))
    if len(cruces) < 2:
        return None
    cruces.sort()
    if len(cruces) == 2:
        return (cruces[0], cruces[1])
    dentro = [(cruces[i], cruces[i + 1]) for i in range(0, len(cruces) - 1, 2)]
    centro = sum(q[otro] for q in anillo) / n
    for a, b in dentro:
        if a <= centro <= b:
            return (a, b)
    return max(dentro, key=lambda t: t[1] - t[0])


def _redondeo_base(radio_nominal, r, grados_perfil=0.0):
    """Filete que suaviza el canto de abajo: la diferencia entre una cubeta y
    una maceta.

    Es un cuarto de círculo cortado, no completo. Uno entero arrancaría
    horizontal desde la cama y sería un voladizo imposible. En este filete el
    ángulo respecto a la vertical coincide con el ángulo del arco, así que
    cortándolo se controla directamente el voladizo.

    El corte se ajusta a lo que el perfil ya esté aportando: si la pieza
    además tiene panza, el filete se acuesta menos para que entre los dos no
    pasen de 45° y la pieza siga imprimiendo sin soportes.

    Devuelve (factor(z), altura del filete). El filete es un factor de escala,
    no un desplazamiento, para que la pared conserve su espesor.
    """
    if r <= 0.05 or radio_nominal <= 0:
        return (lambda z: 1.0), 0.0
    tope = math.radians(max(10.0, 45.0 - max(0.0, grados_perfil)))
    h = r * math.sin(tope)

    def factor(z):
        if z >= h:
            return 1.0
        phi = math.asin(max(-1.0, min(1.0, (h - z) / r)))
        return max(0.12, 1.0 - r * (1.0 - math.cos(phi)) / radio_nominal)
    return factor, h


def _pared_se_cruza(anillo, pared):
    """Milímetros de contorno cuya cara interior se sale de la pieza.

    Es la firma de una punta más angosta que dos paredes: al correr el
    contorno hacia adentro, los dos flancos se cruzan por detrás y la
    superficie interior acaba del otro lado. La malla cierra igual, pero la
    pieza sale mal.

    La prueba es directa —se corre el punto y se pregunta si sigue dentro—,
    así que no depende de cuántos segmentos tenga el contorno. Antes se
    contaban los puntos donde el segmento invertía la marcha, y eso invierte
    en cualquier esquina viva: el mismo hexágono avisaba con 600 segmentos y
    se callaba con 300. Como preguntar «¿está dentro?» cuesta recorrer el
    contorno entero, primero se filtran candidatos —donde el segmento
    invierte la marcha o donde la normal pega un giro— y sólo esos se
    confirman.
    """
    n = len(anillo)
    poligono = [(x, y) for x, y, _, _, _ in anillo]
    sospechosos = []
    for i in range(n):
        ax, ay, anx, any_, _ = anillo[i]
        bx, by, bnx, bny, _ = anillo[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        ix = (bx - bnx * pared) - (ax - anx * pared)
        iy = (by - bny * pared) - (ay - any_ * pared)
        # El giro de la normal entra al filtro porque con pocos segmentos una
        # punta puede no llegar a invertir ningún tramo y aun así estar mal.
        if ex * ix + ey * iy < 0 or anx * bnx + any_ * bny < 0.985:
            sospechosos.append((i, math.hypot(ex, ey)))

    fuera = 0.0
    for i, largo in sospechosos:
        x, y, nx, ny, _ = anillo[i]
        if not M.dentro(poligono, (x - nx * pared, y - ny * pared)):
            fuera += largo
    return fuera


def _decimar(puntos, objetivo):
    paso = max(1, len(puntos) // objetivo)
    return [puntos[i] for i in range(0, len(puntos), paso)]


# Hasta dónde se deja crecer la malla. No es una cuenta de memoria: una pieza
# de más de un millón de triángulos tarda más en laminarse que en imprimirse,
# y arriba de ahí el detalle que se agrega ya no lo resuelve una boquilla de
# 0.4 mm. Cuando el acabado pide más, se engorda el grano y se avisa.
PRESUPUESTO = {"final": 800_000, "borrador": 200_000}

# Hasta dónde se deja engordar el grano cuando la pieza no cabe en el
# presupuesto. Pasado este punto ya no se engorda más y la malla sale como
# salga: un dibujo muestreado cuatro veces por repetición se ve romo, pero se
# ve parejo, y eso es preferible a soltar el múltiplo de estrías y volver al
# acabado desigual que se vino a arreglar.
GRANO_TOPE = 4.0

# La vista previa se mira en 360 px y se redibuja a cada movimiento del
# deslizador, así que va con grano grueso a propósito. Lo que conserva —y es
# lo que importa para juzgar el acabado— es que todas las estrías se
# muestreen igual: se ven romas, pero se ven todas iguales.
GRANO_BORRADOR = 1.6

# Lo que tiene que quedar de pared en el valle de la estría. Son dos
# perímetros de una boquilla de 0.4: con menos, el laminador no mete dos
# hilos y resuelve el valle con uno solo o con relleno de hueco, y ahí es
# donde la pieza sale traslúcida, con costura y floja justo en la línea que
# más se mira. Estaba en 0.4 —un solo hilo— y las recetas caían debajo: el
# portacontroles y el portalápices dejaban 0.60 mm en cada valle.
PARED_MINIMA = 0.8


def _resolver_malla(contorno_fn, p, perfil, cuello, calidad):
    """Cuántos puntos por anillo y cuántos anillos pide esta pieza.

    Es una cuenta circular: el acabado necesita el perímetro para saber
    cuántas estrías caben, y el perímetro sale de muestrear el contorno. Se
    resuelve iterando —el perímetro casi no se mueve entre una resolución y
    otra—, y se para en cuanto el acabado pide lo mismo dos veces seguidas.

    Los valores de «Resolución del contorno» y «Capas verticales» son el
    piso, no la palabra final: el contorno y el perfil piden los suyos y el
    acabado sube desde ahí hasta donde haga falta. Antes eran el techo, y por
    eso un lino de paso corto salía con cuatro puntos por hilo.

    De paso recorta el relieve a lo que la pared aguante. Se hace aquí y no
    antes porque hasta que el acabado no está armado no se sabe cuánto hunde:
    el junco sólo pone lomos y no le quita nada a la pared, y recortarlo como
    si fuera una onda le robaba la mitad del relieve sin motivo.

    Devuelve (anillo, perímetro, acabado, capas, avisos).
    """
    avisos = []
    alto = float(p["alto"])
    base_s = int(p["segmentos"])
    capas_perfil = int(p["capas"]) if (perfil.varia_z or cuello.varia_z) else 1
    presupuesto = PRESUPUESTO["final" if calidad == "final" else "borrador"]
    grano_pedido = float(p.get("grano", 0.6))
    grano = grano_pedido if calidad == "final" else max(grano_pedido, GRANO_BORRADOR)

    segmentos = base_s
    anillo, perimetro = muestrear(contorno_fn, segmentos)
    acabado = ACABADOS[p["acabado"]][1](p, perimetro)

    pared = float(p["pared"])
    if acabado.hunde > 0 and acabado.hundimiento() > pared - PARED_MINIMA:
        p["onda_amplitud"] = max(0.0, (pared - PARED_MINIMA) / acabado.hunde)
        acabado = ACABADOS[p["acabado"]][1](p, perimetro)
        avisos.append("Relieve recortado a %.1f mm: el valle de la estría "
                      "tiene que dejar %.1f mm de pared o el laminador no "
                      "mete dos hilos ahí. Con pared de %.1f mm no da para "
                      "más; súbela si quieres más relieve."
                      % (p["onda_amplitud"], PARED_MINIMA, pared))

    capas, minimo = capas_perfil, 4
    for _ in range(16):
        objetivo_s, capas = acabado.resolucion(perimetro, alto, grano,
                                               base_s, capas_perfil, minimo)
        # No cabe. Primero se engorda el grano y se vuelve a preguntar, y si
        # con el grano al tope sigue sin caber, se le baja el piso de muestras
        # por repetición. Lo que no se toca en ningún caso son los totales:
        # recortarlos a secas rompería el múltiplo exacto de estrías, que es
        # justo lo que se vino a arreglar.
        if 4 * objetivo_s * (capas + 1) > presupuesto:
            if grano < GRANO_TOPE:
                grano = min(GRANO_TOPE, grano * 1.3)
                continue
            if minimo > 2:
                minimo = 2
                continue
        if objetivo_s == segmentos:
            break
        segmentos = objetivo_s
        anillo, perimetro = muestrear(contorno_fn, segmentos)
        acabado = ACABADOS[p["acabado"]][1](p, perimetro)

    if calidad == "final" and (grano > grano_pedido * 1.01 or minimo < 4):
        avisos.append("El acabado pedía más malla de la que conviene mover: "
                      "salió con un grano de %.1f mm en vez de %.1f. Súbele el "
                      "paso de la estría, o bájale las vueltas a la torsión, "
                      "si lo ves escalonado." % (grano, grano_pedido))
    return anillo, perimetro, acabado, capas, avisos


def construir(p, calidad="final"):
    """Devuelve (malla, datos). `p` es el diccionario de parámetros completo
    (ver disenos.PARAMETROS).

    Con `calidad="borrador"` la malla sale con grano grueso: es para la vista
    previa, que se redibuja a cada movimiento del deslizador. El archivo que
    se guarda siempre se construye en `final`.
    """
    avisos = []
    p = dict(p)
    alto = float(p["alto"])
    pared = float(p["pared"])
    piso = float(p["piso"])

    contorno_fn = CONTORNOS[p["contorno"]][1](p)
    perfil = PERFILES[p["perfil"]][1](p)
    cuello = CUELLOS[p.get("cuello", "ninguno")][1](p)
    anillo, perimetro, acabado, capas, avisos_malla = _resolver_malla(
        contorno_fn, p, perfil, cuello, calidad)
    avisos.extend(avisos_malla)
    amp = acabado.amplitud
    n = len(anillo)

    cruce = _pared_se_cruza(anillo, pared / min(1.0, cuello.minimo))
    if cruce > 0.0:
        avisos.append("Hay una punta más angosta que dos paredes de %.1f mm: "
                      "la cara interior se sale de la pieza a lo largo de "
                      "%.0f mm. Baja la pared o suaviza la forma."
                      % (pared, cruce))

    # Qué fracción del relieve se copia por la cara interior: 0 = lisa, 1 = la
    # pared mide lo mismo en todas partes. Entre medias queda una onda más
    # suave por dentro, que deja engrosar la pared sin que se pliegue.
    copia = (min(1.0, max(0.0, float(p.get("pared_copia", 1.0))))
             if p.get("pared_forma") == "sigue" else 0.0)
    dm = -(pared + amp * (1.0 - copia)) / 2.0   # plano medio de la pared: material garantizado

    radio_nominal = max(math.hypot(x, y) for x, y, _, _, _ in anillo)
    r_base = float(p["base_redondeo"])
    tope_r = min(radio_nominal * 1.4, alto * 0.9)
    if r_base > tope_r:
        r_base = tope_r
        avisos.append("El redondeo de la base no cabe; se recortó a %.0f mm."
                      % r_base)
    # Cuánto se abre ya el perfil por sí solo cerca del fondo, en grados
    # respecto a la vertical. El filete se corta con lo que sobre de 45°.
    grados_perfil = 0.0
    for j in range(24):
        z0, z1 = alto * j / 120.0, alto * (j + 1) / 120.0
        dr = (perfil(z1 / alto) - perfil(z0 / alto)) * radio_nominal
        grados_perfil = max(grados_perfil, math.degrees(math.atan2(dr, z1 - z0)))
    filete, alto_filete = _redondeo_base(radio_nominal, r_base, grados_perfil)

    # Alturas donde se cortan las capas, en fracción de la columna. El filete
    # sólo trabaja en unos milímetros, así que ahí se meten capas extra en vez
    # de subdividir la pieza entera.
    #
    # Cuántas, por la misma regla que el relieve: ninguna faceta más larga que
    # el grano. Eran diez fijas, y diez repartidas en un filete de 70 mm dejan
    # facetas de siete milímetros — el canto que se vino a suavizar sale
    # poligonal.
    # Cuánto se alisa el relieve cerca de la boca, sin importar el acabado.
    # Una torsión (o cualquier onda con desplazamiento radial) llega a la
    # boca con su cresta completa, y ahí el labio sale mordido en vez de un
    # aro limpio. El desvanecido no es un borde nuevo —el borde ya decide
    # hasta dónde sube cada columna— es una escala sobre el propio relieve,
    # que lo va llevando a cero en los últimos milímetros.
    desvanece = min(max(0.0, float(p.get("acabado_desvanece", 0.0))), alto * 0.9)

    def desvanecimiento(zn):
        """1.0 en el cuerpo; baja a 0 en la boca con un smoothstep, para que
        el relieve no llegue de golpe: una recta dejaría un quiebre justo
        donde empieza a alisarse."""
        if desvanece <= 0.0:
            return 1.0
        umbral = alto - desvanece
        z = zn * alto
        if z <= umbral:
            return 1.0
        t = min(1.0, (z - umbral) / desvanece)
        return 1.0 - t * t * (3.0 - 2.0 * t)

    # A dónde lleva el desvanecido al relieve: 0 = a la pared nominal (la boca
    # lisa de siempre); 1 = a ras de las crestas, que cierra los surcos contra
    # un aro liso, como remata el Portacepillos01O.
    cierre = min(1.0, max(0.0, float(p.get("acabado_cierre", 0.0))))
    meta_cierre = cierre * acabado.amplitud

    def relieve(s, zn):
        f = desvanecimiento(zn)
        if f >= 1.0:
            return acabado(s, zn)
        return acabado(s, zn) * f + meta_cierre * (1.0 - f)

    fracciones = [k / capas for k in range(capas + 1)]
    if alto_filete > 0:
        pasos = max(10, int(math.ceil(alto_filete / float(p["grano"]))))
        fracciones += [(alto_filete / alto) * j / pasos for j in range(pasos + 1)]
    if desvanece > 0:
        # Mismo truco que el filete: la franja que se alisa es angosta, así
        # que ahí se meten capas extra en vez de subdividir la pieza entera.
        pasos = max(10, int(math.ceil(desvanece / float(p["grano"]))))
        fracciones += [1.0 - (desvanece / alto) * j / pasos for j in range(pasos + 1)]
    fracciones = sorted(f for f in set(fracciones) if 0.0 <= f <= 1.0)

    def escala(z):
        """Perfil vertical y filete de la base, en un solo factor. Va como
        escala y no como desplazamiento para que la pared no cambie de
        espesor al redondear el fondo."""
        zn = min(max(z, 0.0), alto) / alto
        return perfil(zn) * cuello(zn) * filete(z)

    # Un perfil angular (el oleaje) no escala la sección pareja: cada columna
    # lleva su propio factor encima de `escala`. Se le pasa el ángulo de la
    # columna en el contorno, no el de la normal, para que la panza no
    # dependa de por dónde se haya empezado a muestrear.
    #
    # La panza sale en milímetros parejos, no como fracción del radio de cada
    # columna: en un óvalo de 182×76, la fracción daba 5 mm en las puntas y 2
    # en el frente, y la ola se veía de lado justo donde no se mira la pieza.
    # La intensidad se cuenta sobre el radio mayor; en un círculo da lo mismo.
    # El ángulo se toma sobre la planta normalizada (x/xmax, y/ymax): así su
    # coseno es dónde cae la columna a lo largo de la pieza, que es lo que
    # necesitan los pliegues que nacen en los extremos. En un círculo es el
    # ángulo de siempre.
    medio_x = max(abs(q[0]) for q in anillo) or 1.0
    medio_y = max(abs(q[1]) for q in anillo) or 1.0
    angulos = [math.atan2(y / medio_y, x / medio_x) for x, y, _, _, _ in anillo]
    parejo = [radio_nominal / max(1e-6, math.hypot(x, y))
              for x, y, _, _, _ in anillo]
    if perfil.angular is None:
        def columna(zn, i):
            return 1.0
    else:
        def columna(zn, i):
            f = perfil.angular(min(max(zn, 0.0), 1.0), angulos[i])
            return 1.0 + (f - 1.0) * parejo[i]

    def anillo_ext(z):
        e, zn = escala(z), z / alto
        return [(x * e * columna(zn, i) + nx * relieve(s, zn),
                 y * e * columna(zn, i) + ny * relieve(s, zn))
                for i, (x, y, nx, ny, s) in enumerate(anillo)]

    def anillo_int(z):
        e, zn = escala(z), z / alto
        return [(x * e * columna(zn, i) - nx * (pared - copia * relieve(s, zn)),
                 y * e * columna(zn, i) - ny * (pared - copia * relieve(s, zn)))
                for i, (x, y, nx, ny, s) in enumerate(anillo)]

    def anillo_medio(z):
        e, zn = escala(z), z / alto
        return [(x * e * columna(zn, i) + nx * dm, y * e * columna(zn, i) + ny * dm)
                for i, (x, y, nx, ny, _) in enumerate(anillo)]

    # ── Divisores: dónde van ───────────────────────────────────────────────
    ranuras = max(1, int(p["ranuras"]))
    grosor_div = float(p["divisor_grosor"])
    alto_div = min(float(p["divisor_alto"]), alto - 0.6)
    filas = max(1, int(p["filas"]))

    # Un divisor se arma cruzando la sección de pared a pared y se mete por
    # arriba. Con la boca cerrada no hay por dónde meterlo, y arriba del hombro
    # la sección se encoge y el divisor se quedaría colgando del aire.
    if not cuello.neutro and (ranuras > 1 or filas > 1):
        avisos.append("Con cuello no caben divisores: no entran por la boca y "
                      "no tienen dónde apoyarse arriba del hombro.")
        ranuras = filas = 1

    interior = anillo_int(alto / 2.0)

    def _repartir(eje, cuantas, nombre):
        """Dónde van los divisores de un sentido, y cuánto mide cada hueco."""
        c0 = min(q[eje] for q in interior)
        c1 = max(q[eje] for q in interior)
        util = c1 - c0
        hueco = (util - (cuantas - 1) * grosor_div) / cuantas
        if cuantas > 1 and hueco < 4.0:
            avisos.append("No caben %d %s en %.0f mm útiles; se hizo sin esos "
                          "divisores." % (cuantas, nombre, util))
            return 1, util, []
        if cuantas <= 1:
            return 1, util, []
        return cuantas, hueco, [c0 + hueco * (i + 1) + grosor_div * (i + 0.5)
                                for i in range(cuantas - 1)]

    ranuras, ancho_ranura, posiciones = _repartir(0, ranuras, "ranuras")
    filas, fondo_fila, posiciones_filas = _repartir(1, filas, "filas")

    # ── Base perforada: se resuelve antes de armar el casco ────────────────
    plato, n_agujeros = None, 0
    if float(p["drenaje_diametro"]) > 0.05:
        radio = float(p["drenaje_diametro"]) / 2.0
        sep = max(float(p["drenaje_separacion"]), float(p["drenaje_diametro"]) + 1.5)
        # El plato es delgado, así que se toma la sección a media altura del piso.
        contorno_plato = _decimar(anillo_medio(piso / 2.0), 72)
        adentro = _decimar(anillo_int(piso / 2.0), 72)
        xs = [x for x, _ in adentro]
        ys = [y for _, y in adentro]
        cx0, cy0 = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        cols_ag = int((max(xs) - min(xs)) // sep) + 1
        filas_ag = int((max(ys) - min(ys)) // sep) + 1

        huecos = []
        for iy in range(filas_ag):
            cy = cy0 + (iy - (filas_ag - 1) / 2) * sep
            for ix in range(cols_ag):
                cx = cx0 + (ix - (cols_ag - 1) / 2) * sep
                if not M.dentro(adentro, (cx, cy)):
                    continue
                if M.distancia_al_borde(adentro, (cx, cy)) < radio + 1.2:
                    continue
                if any(abs(cx - d) < radio + grosor_div / 2 + 0.8 for d in posiciones):
                    continue
                huecos.append(M.circulo_puntos(cx, cy, radio, 10))

        if not huecos:
            avisos.append("No cupo ningún agujero con esa separación; el piso "
                          "quedó sólido.")
        else:
            plato = M.placa(contorno_plato, huecos, 0.0, piso)
            if plato is None:
                avisos.append("No se pudo perforar la base con esos valores; "
                              "el piso quedó sólido.")
            else:
                n_agujeros = len(huecos)
        if piso < 1.2 and plato is not None:
            avisos.append("Con drenaje conviene un piso de al menos 1.2 mm.")

    drenaje = plato is not None
    z_int0 = 0.0 if drenaje else piso

    # ── Escalón: el frente más bajo que el fondo ───────────────────────────
    # Cada columna del contorno lleva su propia altura de remate. Es lo que
    # convierte una cubeta en un organizador: los cubiertos largos paran
    # atrás, donde la pared sube, y adelante quedan huecos playos donde se ve
    # lo que hay dentro.
    escalon = float(p["escalon"])
    frente = float(p["escalon_frente"])
    y_corte, alto_bajo = None, alto
    if escalon < 0.999 and frente > 0.001:
        ys = [q[1] for q in anillo]
        y_corte = min(ys) + (max(ys) - min(ys)) * frente
        alto_bajo = max(z_int0 + 6.0, alto * escalon)
    tope = [alto if (y_corte is None or y > y_corte) else alto_bajo
            for _, y, _, _, _ in anillo]

    # El borde recortado se compone con el escalón por mínimo: los dos son
    # alturas de remate y el material sobra donde cualquiera de los dos corta.
    # El suelo de 6 mm sobre el interior es el mismo que ya se impone el
    # escalón: por debajo de eso no queda pared, queda un plato.
    if not BO.es_neutro(p):
        labio = BO.remate(p, anillo, alto)
        tope = [max(z_int0 + 6.0, min(t, l)) for t, l in zip(tope, labio)]

    # ── Casco ──────────────────────────────────────────────────────────────
    m = M.Malla()
    ext, inte = [], []
    for fr in fracciones:
        aro_e, aro_i = [], []
        for idx, (x, y, nx, ny, s) in enumerate(anillo):
            z = tope[idx] * fr
            e = escala(z) * columna(z / alto, idx)
            d = relieve(s, z / alto)
            aro_e.append(m.punto(x * e + nx * d, y * e + ny * d, z))
            zi = z_int0 + (tope[idx] - z_int0) * fr
            ei = escala(zi) * columna(zi / alto, idx)
            pi = pared - copia * relieve(s, zi / alto)
            aro_i.append(m.punto(x * ei - nx * pi, y * ei - ny * pi, zi))
        ext.append(aro_e)
        inte.append(aro_i)

    for k in range(len(fracciones) - 1):
        for i in range(n):
            j = (i + 1) % n
            m.quad(ext[k][i], ext[k][j], ext[k + 1][j], ext[k + 1][i])
            m.quad(inte[k][i], inte[k + 1][i], inte[k + 1][j], inte[k][j])
    for i in range(n):
        j = (i + 1) % n
        m.quad(ext[-1][i], ext[-1][j], inte[-1][j], inte[-1][i])    # borde de la boca

    if drenaje:
        for i in range(n):
            j = (i + 1) % n
            m.quad(ext[0][i], inte[0][i], inte[0][j], ext[0][j])    # canto inferior
    else:
        c_abajo = m.punto(0.0, 0.0, 0.0)
        c_piso = m.punto(0.0, 0.0, piso)
        for i in range(n):
            j = (i + 1) % n
            m.cara(c_abajo, ext[0][j], ext[0][i])
            m.cara(c_piso, inte[0][i], inte[0][j])

    # ── Divisores: la malla ────────────────────────────────────────────────
    # Un divisor se corta contra el plano medio de la pared, que no sabe del
    # relieve: lo único que le cambia la sección conforme sube son el perfil,
    # el cuello y el filete del fondo. Seguir las capas del acabado le metía
    # cientos de secciones idénticas a un tabique plano.
    seccion_varia = (perfil.varia_z or cuello.varia_z or alto_filete > 0.0
                     or p.get("divisor_forma", "recto") == "ola")
    capas_div = (int(p["capas"]) if seccion_varia else 1)

    # Divisor en ola: el tabique se corre de lado siguiendo las mismas panzas
    # que la pared, con los extremos quietos (sen πt) para que siga pegado
    # donde la toca. Con perfil oleaje toma sus panzas; con otro, una sola.
    ola_div = (float(p.get("divisor_ola", 0.0))
               if p.get("divisor_forma", "recto") == "ola" else 0.0)
    ondas_div = (float(p.get("oleaje_ondas", 2.0)) if p["perfil"] == "oleaje"
                 else 1.0)
    puntos_div = 33 if ola_div > 0.0 else 2

    def _seccion_tabique(eje, centro, lim, z, medio_grosor):
        """La sección del divisor a la altura `z`, en sentido antihorario.
        Se arma como si el divisor corriera a lo largo de y (eje 0) y, para
        el otro sentido, se intercambian las coordenadas: es lo mismo que
        hacía la caja de cuatro puntos, que era este caso con dos."""
        zn = min(max(z, 0.0), alto) / alto
        vaiven = math.sin(2.0 * math.pi * ondas_div * zn)
        lado_b, lado_a = [], []
        for j in range(puntos_div):
            t = j / (puntos_div - 1)
            u = lim[0] + (lim[1] - lim[0]) * t
            corre = ola_div * math.sin(math.pi * t) * vaiven
            lado_b.append((centro + corre + medio_grosor, u))
            lado_a.append((centro + corre - medio_grosor, u))
        poligono = lado_b + lado_a[::-1]
        poligono = poligono[-1:] + poligono[:-1]   # arranca en (a, lim0)
        if eje == 0:
            return poligono
        return [(u, v) for v, u in poligono]

    def _tabique(eje, centro, alto_tab, limite=None):
        """Un divisor perpendicular a `eje`, de pared a pared. `limite`
        recorta hasta dónde llega a lo largo, que es lo que permite partir un
        divisor en dos alturas cuando la pieza va escalonada. Devuelve la
        malla o None si no alcanza a tocar el contorno."""
        secciones = []
        for k in range(capas_div + 1):
            z = alto_tab * k / capas_div
            medio = anillo_medio(z)
            lim = None
            for cara in (centro - grosor_div / 2, centro + grosor_div / 2):
                c = _cruce(medio, eje, cara)
                if c is None:
                    return None
                lim = c if lim is None else (max(lim[0], c[0]), min(lim[1], c[1]))
            if limite is not None:
                lim = (max(lim[0], limite[0]), min(lim[1], limite[1]))
            if lim[1] - lim[0] < 1.0:
                return None
            secciones.append((_seccion_tabique(eje, centro, lim, z,
                                               grosor_div / 2), z))
        # Canto superior en filo: el chaflán es lo que evita que la boca del
        # divisor quede plana y se vea de molde barato.
        secciones.append((_seccion_tabique(eje, centro, lim, alto_tab, 0.01),
                          alto_tab + float(p["divisor_chaflan"])))
        return _loft(secciones)

    # Un divisor más alto que el punto más bajo del labio asoma por encima y se
    # ve desde fuera. Se recorta contra el remate más bajo de toda la pieza, que
    # es conservador a propósito: con un corte al bies, un divisor del lado alto
    # cabría más, pero saber cuál es «su» lado exige mirar por dónde pasa, y una
    # pieza donde a veces asoma y a veces no es peor que una pareja.
    remate_minimo = min(tope) - 0.6 - float(p["divisor_chaflan"])
    if not BO.es_neutro(p) and alto_div > remate_minimo and (
            posiciones or posiciones_filas):
        avisos.append("Los divisores se recortaron a %.0f mm para que no asomen "
                      "por encima del borde." % max(0.0, remate_minimo))
        alto_div = remate_minimo

    def _alto_util(cima):
        # El chaflán va por encima de `alto_div`, así que hay que descontarlo:
        # sin eso, un divisor pedido tan alto como la pared asoma justo lo que
        # mide el filo.
        return min(alto_div, cima - 0.6 - float(p["divisor_chaflan"]))

    omitidos = 0
    for centro in posiciones:
        # A lo largo cruza el escalón, así que va en dos tramos: alto atrás y
        # bajo adelante. De una pieza, sobresaldría del frente.
        if y_corte is None:
            tramos = [(alto_div, None)]
        else:
            tramos = [(_alto_util(alto), (y_corte, float("inf"))),
                      (_alto_util(alto_bajo), (float("-inf"), y_corte))]
        for alto_tab, limite in tramos:
            tab = _tabique(0, centro, alto_tab, limite)
            if tab is None:
                omitidos += 1
            else:
                m.unir(tab)
    for centro in posiciones_filas:
        # A lo ancho cae entero de un lado del escalón o del otro.
        cima = alto if (y_corte is None or centro > y_corte) else alto_bajo
        tab = _tabique(1, centro, _alto_util(cima))
        if tab is None:
            omitidos += 1
        else:
            m.unir(tab)
    if omitidos:
        avisos.append("%d divisor(es) no alcanzaban la pared y se omitieron."
                      % omitidos)

    if plato is not None:
        m.unir(plato)

    # ¿Se acuesta la pared más de lo que aguanta una impresora sin soportes?
    #
    # Se mide en los dos sentidos. Una pared que se cierra cuelga sobre el hueco
    # exactamente igual que una que se abre cuelga sobre el aire: en los dos
    # casos la capa nueva sale hacia afuera de la que tiene debajo, y lo que
    # decide si se sostiene es el ángulo respecto a la vertical, no hacia dónde
    # va. Medir sólo la que se abre dejaba pasar un cono invertido de 49°.
    #
    # Con un perfil angular cada columna se acuesta distinto, así que se mide
    # en varias alrededor de la pieza, cada una con su propio radio: en un
    # óvalo, la misma panza en la punta sale el doble que en el costado.
    if perfil.angular is None:
        muestras = [(None, radio_nominal)]
    else:
        muestras = [(i, math.hypot(anillo[i][0], anillo[i][1]))
                    for i in range(0, n, max(1, n // 48))]
    voladizo, sentido = 0.0, ""
    for i, radio in muestras:
        for j in range(160):
            z0, z1 = alto * j / 160.0, alto * (j + 1) / 160.0
            r0 = escala(z0) * radio * (1.0 if i is None else columna(z0 / alto, i))
            r1 = escala(z1) * radio * (1.0 if i is None else columna(z1 / alto, i))
            grados = math.degrees(math.atan2(abs(r1 - r0), z1 - z0))
            if grados > voladizo:
                voladizo, sentido = grados, "abre" if r1 > r0 else "cierra"
    if voladizo > 47.0:
        avisos.append("La pared se %s hasta %.0f° respecto a la vertical: va a "
                      "pedir soportes. %s"
                      % (sentido, voladizo,
                         "Baja la intensidad del perfil." if sentido == "abre"
                         else "Cierra la pieza más despacio."))

    # ── Bandeja de goteo ───────────────────────────────────────────────────
    bandeja, datos_bandeja = None, None
    if p.get("bandeja", "ninguna") != "ninguna":
        if not drenaje:
            avisos.append("Una bandeja sin drenaje no recoge nada: súbele el "
                          "diámetro del agujero al piso del vaso.")
        bandeja, datos_bandeja = B.construir(anillo, amp, escala, p)
        if bandeja is None:
            avisos.append(datos_bandeja)
            datos_bandeja = None

    piezas = [("cuerpo", m)]
    montada = m
    if bandeja is not None:
        piezas.append(("bandeja", bandeja))
        # Para la vista previa se enseña armado: el vaso parado en la bandeja,
        # subido lo que miden el piso y las costillas.
        montada = M.Malla()
        montada.unir(bandeja)
        montada.unir(m.trasladada(0.0, 0.0, datos_bandeja["apoyo"]))

    (x0, y0, z0), (x1, y1, z1) = montada.caja()
    volumen = montada.volumen() / 1000.0
    cerrada = montada.aristas_sueltas() == 0
    if not cerrada:
        avisos.append("La malla quedó abierta; revisa los parámetros.")

    return montada, {
        "piezas": piezas,
        "bandeja": datos_bandeja,
        "ancho": round(x1 - x0, 1),
        "fondo": round(y1 - y0, 1),
        "alto": round(z1 - z0, 1),
        "volumen_cm3": round(volumen, 1),
        "gramos": round(volumen * DENSIDAD.get(p.get("material", "PLA"), 1.24)),
        "ranuras": ranuras,
        "ancho_ranura": round(ancho_ranura, 1) if ranuras > 1 else None,
        "filas": filas,
        "fondo_fila": round(fondo_fila, 1) if filas > 1 else None,
        "huecos": ranuras * filas,
        "escalon": round(alto_bajo, 1) if y_corte is not None else None,
        "agujeros": n_agujeros,
        "estrias": (max(1, round(perimetro / max(p["onda_paso"], 0.5)))
                    if p["acabado"] in ("ondulado", "facetado", "torsion")
                    else max(1, round(alto / max(p["onda_paso"], 0.5)))
                    if p["acabado"] == "torsion_lado" else 0),
        "triangulos": len(m.t),
        # La resolución con la que salió, que ya no es la que dice el control:
        # el acabado la sube hasta donde la necesita. Verla es lo que permite
        # saber si una pieza se laminó fina o si el presupuesto la recortó.
        "segmentos": n,
        "capas": capas,
        "calidad": calidad,
        "cerrada": cerrada,
        "avisos": avisos,
    }
