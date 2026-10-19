#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Malla triangular y utilidades de geometría. Solo Python 3 estándar."""

import math


class Malla:
    """Malla de triángulos. Las caras se guardan con el giro hacia afuera."""

    def __init__(self):
        self.v = []
        self.t = []

    def punto(self, x, y, z):
        self.v.append((x, y, z))
        return len(self.v) - 1

    def cara(self, i, j, k):
        if i != j and j != k and k != i:
            self.t.append((i, j, k))

    def quad(self, i, j, k, m):
        self.cara(i, j, k)
        self.cara(i, k, m)

    def volumen(self):
        """Volumen con signo (mm3). Negativo = malla del revés."""
        total = 0.0
        for i, j, k in self.t:
            ax, ay, az = self.v[i]
            bx, by, bz = self.v[j]
            cx, cy, cz = self.v[k]
            total += (ax * (by * cz - bz * cy)
                      - ay * (bx * cz - bz * cx)
                      + az * (bx * cy - by * cx))
        return total / 6.0

    def normalizar(self):
        if self.volumen() < 0:
            self.t = [(i, k, j) for i, j, k in self.t]
        return self

    def unir(self, otra):
        base = len(self.v)
        self.v.extend(otra.v)
        self.t.extend((i + base, j + base, k + base) for i, j, k in otra.t)
        return self

    def trasladada(self, dx=0.0, dy=0.0, dz=0.0):
        otra = Malla()
        otra.v = [(x + dx, y + dy, z + dz) for x, y, z in self.v]
        otra.t = list(self.t)
        return otra

    def caja(self):
        xs = [v[0] for v in self.v]
        ys = [v[1] for v in self.v]
        zs = [v[2] for v in self.v]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def aristas_sueltas(self):
        """0 = malla cerrada. Sirve de prueba: cada arista debe aparecer una
        sola vez en cada sentido."""
        vistas = {}
        for i, j, k in self.t:
            for a, b in ((i, j), (j, k), (k, i)):
                vistas[(a, b)] = vistas.get((a, b), 0) + 1
        return (sum(1 for c in vistas.values() if c != 1)
                + sum(1 for e in vistas if (e[1], e[0]) not in vistas))


# ─── Polígonos ─────────────────────────────────────────────────────────────

def area_con_signo(poligono):
    total = 0.0
    n = len(poligono)
    for i in range(n):
        x0, y0 = poligono[i]
        x1, y1 = poligono[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return total / 2.0


def orientar(poligono, antihorario=True):
    return (list(poligono) if (area_con_signo(poligono) > 0) == antihorario
            else list(reversed(poligono)))


def dentro(poligono, punto):
    """Prueba de punto en polígono por lanzamiento de rayo."""
    x, y = punto
    adentro = False
    n = len(poligono)
    for i in range(n):
        x0, y0 = poligono[i]
        x1, y1 = poligono[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            corte = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if x < corte:
                adentro = not adentro
    return adentro


def distancia_al_borde(poligono, punto):
    """Distancia mínima del punto a cualquier lado del polígono."""
    x, y = punto
    mejor = float("inf")
    n = len(poligono)
    for i in range(n):
        x0, y0 = poligono[i]
        x1, y1 = poligono[(i + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        largo2 = dx * dx + dy * dy
        u = 0.0 if largo2 == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / largo2))
        mejor = min(mejor, math.hypot(x - (x0 + u * dx), y - (y0 + u * dy)))
    return mejor


def _puentear(exterior, huecos):
    """Une cada hueco al contorno exterior con un puente, dejando un solo
    polígono simple que ya se puede recortar por orejas.

    Método clásico: desde el punto más a la derecha del hueco se lanza un rayo
    hacia +X, se toma el lado que corta primero y se puentea a su extremo, o
    al vértice cóncavo que estorbe dentro de ese triángulo. Es O(n) por hueco,
    contra O(n²) de probar visibilidad vértice por vértice.
    """
    poly = list(exterior)
    for hueco in sorted(huecos, key=lambda h: -max(p[0] for p in h)):
        im = max(range(len(hueco)), key=lambda i: hueco[i][0])
        m = hueco[im]
        n = len(poly)

        # Lado que corta el rayo hacia la derecha, lo más cerca posible
        mejor_x, mejor_i = float("inf"), None
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            if (y0 > m[1]) == (y1 > m[1]):
                continue
            xc = x0 + (m[1] - y0) * (x1 - x0) / (y1 - y0)
            if m[0] - 1e-9 <= xc < mejor_x:
                mejor_x, mejor_i = xc, i
        if mejor_i is None:
            continue  # el hueco no ve el contorno: se descarta

        a, b = poly[mejor_i], poly[(mejor_i + 1) % n]
        ip = mejor_i if a[0] > b[0] else (mejor_i + 1) % n
        punto_i = (mejor_x, m[1])

        # ¿Algún vértice cóncavo se mete en el triángulo M-I-P? Si sí, hay que
        # puentear a ese, no al extremo del lado.
        def dentro_tri(p, t0, t1, t2):
            d1 = (t1[0] - t0[0]) * (p[1] - t0[1]) - (t1[1] - t0[1]) * (p[0] - t0[0])
            d2 = (t2[0] - t1[0]) * (p[1] - t1[1]) - (t2[1] - t1[1]) * (p[0] - t1[0])
            d3 = (t0[0] - t2[0]) * (p[1] - t2[1]) - (t0[1] - t2[1]) * (p[0] - t2[0])
            return (d1 >= -1e-9 and d2 >= -1e-9 and d3 >= -1e-9) or \
                   (d1 <= 1e-9 and d2 <= 1e-9 and d3 <= 1e-9)

        mejor_ang, elegido = None, ip
        for i in range(n):
            if i == ip:
                continue
            v = poly[i]
            ant, sig = poly[i - 1], poly[(i + 1) % n]
            convexo = ((v[0] - ant[0]) * (sig[1] - ant[1])
                       - (v[1] - ant[1]) * (sig[0] - ant[0])) > 0
            if convexo or v[0] < m[0]:
                continue
            if not dentro_tri(v, m, punto_i, poly[ip]):
                continue
            ang = abs(math.atan2(v[1] - m[1], v[0] - m[0]))
            clave = (ang, math.dist(m, v))
            if mejor_ang is None or clave < mejor_ang:
                mejor_ang, elegido = clave, i

        anillo = hueco[im:] + hueco[:im]
        poly = (poly[:elegido + 1] + anillo + [anillo[0]] + poly[elegido:])
    return poly


def _es_oreja(poly, reflejos, ia, ib, ic):
    a, b, c = poly[ia], poly[ib], poly[ic]
    cruz = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    if cruz <= 1e-12:
        return False  # cóncavo o degenerado
    for ip in reflejos:
        if ip in (ia, ib, ic):
            continue
        p = poly[ip]
        d1 = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        d2 = (c[0] - b[0]) * (p[1] - b[1]) - (c[1] - b[1]) * (p[0] - b[0])
        d3 = (a[0] - c[0]) * (p[1] - c[1]) - (a[1] - c[1]) * (p[0] - c[0])
        if d1 > 1e-9 and d2 > 1e-9 and d3 > 1e-9:
            return False
    return True


def triangular(exterior, huecos=()):
    """Triangula un polígono con huecos por recorte de orejas.

    Devuelve (puntos, triangulos, completo). `completo` en falso significa que
    el recorte se atoró y la triangulación no sirve: quien llama debe tener un
    plan B en vez de quedarse con una malla abierta.
    """
    ext = orientar(exterior, True)
    hs = [orientar(h, False) for h in huecos]
    poly = _puentear(ext, hs) if hs else ext
    n = len(poly)
    if n < 3:
        return poly, [], False

    # Lista doblemente ligada: recortar una oreja es reconectar dos punteros,
    # y sólo hay que revisar de nuevo la convexidad de los dos vecinos.
    ant = [(i - 1) % n for i in range(n)]
    sig = [(i + 1) % n for i in range(n)]

    def convexo(i):
        a, b, c = poly[ant[i]], poly[i], poly[sig[i]]
        return ((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) > 1e-12

    reflejos = set(i for i in range(n) if not convexo(i))
    triangulos = []
    restantes = n
    i = 0
    fallos = 0

    while restantes > 3 and fallos <= restantes:
        if i not in reflejos and _es_oreja(poly, reflejos, ant[i], i, sig[i]):
            triangulos.append((ant[i], i, sig[i]))
            p, s = ant[i], sig[i]
            sig[p], ant[s] = s, p
            reflejos.discard(i)
            for v in (p, s):
                reflejos.discard(v) if convexo(v) else reflejos.add(v)
            restantes -= 1
            fallos = 0
            i = p
        else:
            i = sig[i]
            fallos += 1

    if restantes == 3:
        triangulos.append((ant[i], i, sig[i]))
        return poly, triangulos, True
    return poly, triangulos, False


# ─── Sólidos ───────────────────────────────────────────────────────────────

def placa(exterior, huecos, z0, z1):
    """Placa plana con huecos pasantes, entre z0 y z1.

    Devuelve una malla cerrada, o None si la triangulación no salió (mejor
    avisar que entregar una malla rota)."""
    puntos, tris, ok = triangular(exterior, huecos)
    if not ok:
        return None
    m = Malla()
    abajo = [m.punto(x, y, z0) for x, y in puntos]
    arriba = [m.punto(x, y, z1) for x, y in puntos]

    for i, j, k in tris:
        m.cara(abajo[i], abajo[k], abajo[j])   # cara inferior, mira a -Z
        m.cara(arriba[i], arriba[j], arriba[k])  # cara superior, mira a +Z

    # Los cantos son las aristas que sólo aparecen en un triángulo.
    conteo = {}
    for i, j, k in tris:
        for a, b in ((i, j), (j, k), (k, i)):
            conteo[(a, b)] = conteo.get((a, b), 0) + 1
    for (a, b), n in conteo.items():
        if n == 1 and conteo.get((b, a), 0) == 0:
            m.quad(abajo[a], abajo[b], arriba[b], arriba[a])
    return m


def circulo_puntos(cx, cy, radio, lados=16):
    return [(cx + radio * math.cos(2 * math.pi * i / lados),
             cy + radio * math.sin(2 * math.pi * i / lados)) for i in range(lados)]
