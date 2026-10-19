#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render por software de una malla a PNG. Solo Python 3 estándar.

Se usa para dos cosas: la vista previa de la pestaña «Crear» (rápida, sin
suavizado) y la miniatura que se guarda dentro del .3mf (con suavizado).
"""

import math
import struct
import zlib

FONDO = (244, 242, 238)      # el mismo gris cálido de la galería
MATERIAL = (223, 214, 201)   # beige tipo PLA mate

# Las vistas se guardan como (giro, elevación) en grados, no como vector:
# así la interfaz puede moverlas con dos deslizadores.
VISTA_3_4 = (32, 31)       # tres cuartos, luce la forma y el relieve
VISTA_PICADA = (19, 52)    # desde arriba: la silueta se lee en planta


def vector_vista(giro, elevacion):
    """Vector de mirada. Giro 0 mira la pieza de frente (desde -Y) y crece en
    sentido horario; elevación 90 sería justo desde arriba."""
    g, e = math.radians(giro), math.radians(elevacion)
    ce = math.cos(e)
    return (math.sin(g) * ce, math.cos(g) * ce, -math.sin(e))


def camara(p):
    """Vista de arranque. La silueta se lee en planta, así que esas piezas se
    miran más desde arriba; el resto, en tres cuartos."""
    es_silueta = (p.get("contorno") == "silueta"
                  and p.get("silueta", "ninguna") != "ninguna")
    return VISTA_PICADA if es_silueta else VISTA_3_4


def _normalizar(v):
    largo = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / largo, v[1] / largo, v[2] / largo)


def _cruz(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _punto(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def escribir_png(ruta, ancho, alto, pixeles):
    """Devuelve los bytes del PNG (y lo escribe si se le pasa una ruta)."""
    filas = bytearray()
    for y in range(alto):
        filas.append(0)
        filas.extend(pixeles[y * ancho * 3:(y + 1) * ancho * 3])

    def trozo(tipo, datos):
        return (struct.pack(">I", len(datos)) + tipo + datos
                + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
           + trozo(b"IDAT", zlib.compress(bytes(filas), 6))
           + trozo(b"IEND", b""))
    if ruta:
        with open(ruta, "wb") as f:
            f.write(png)
    return png


def render(vertices, triangulos, tam=512, suavizado=2, direccion=None,
           color=MATERIAL, fondo=FONDO, ruta=None):
    """Z-buffer con perspectiva suave y luz de tres puntos.

    `suavizado=1` es el modo borrador (rápido, para la vista previa);
    `suavizado=2` renderiza al doble y baja, para la miniatura definitiva.
    """
    s = max(1, int(suavizado))
    W = H = tam * s
    if direccion is None:
        direccion = vector_vista(*VISTA_3_4)

    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    centro = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
    radio = max(math.dist(v, centro) for v in vertices) or 1.0

    f = _normalizar(direccion)
    ojo = tuple(centro[i] - f[i] * radio * 3.4 for i in range(3))
    derecha = _normalizar(_cruz(f, (0.0, 0.0, 1.0)))
    arriba = _cruz(derecha, f)

    proy = []
    for v in vertices:
        d = (v[0] - ojo[0], v[1] - ojo[1], v[2] - ojo[2])
        proy.append((_punto(d, derecha), _punto(d, arriba), _punto(d, f)))
    escala = (W / 2 * 0.93) / max(max(abs(q[0]), abs(q[1])) / q[2] for q in proy)
    pantalla = [(W / 2 + q[0] / q[2] * escala, H / 2 - q[1] / q[2] * escala, 1.0 / q[2])
                for q in proy]

    # Las luces van amarradas a la cámara, no al mundo: si se quedaran fijas,
    # al girar la vista media vuelta la pieza se vería contra la luz y negra.
    luz_clave = _normalizar(tuple(-0.85 * f[i] + 0.55 * arriba[i] - 0.35 * derecha[i]
                                  for i in range(3)))
    luz_relleno = _normalizar(tuple(-0.25 * f[i] + 0.85 * derecha[i] + 0.05 * arriba[i]
                                    for i in range(3)))

    lienzo = bytearray(bytes(fondo) * (W * H))
    zbuf = [0.0] * (W * H)

    for ia, ib, ic in triangulos:
        va, vb, vc = vertices[ia], vertices[ib], vertices[ic]
        u = (vb[0] - va[0], vb[1] - va[1], vb[2] - va[2])
        w = (vc[0] - va[0], vc[1] - va[1], vc[2] - va[2])
        n = _normalizar(_cruz(u, w))
        cen = ((va[0] + vb[0] + vc[0]) / 3, (va[1] + vb[1] + vc[1]) / 3,
               (va[2] + vb[2] + vc[2]) / 3)
        if _punto(n, (cen[0] - ojo[0], cen[1] - ojo[1], cen[2] - ojo[2])) >= 0:
            continue  # cara que da la espalda

        luz = (0.46 + 0.18 * n[2]
               + 0.62 * max(0.0, _punto(n, luz_clave))
               + 0.26 * max(0.0, _punto(n, luz_relleno)))
        rgb = bytes(min(255, int(c * luz)) for c in color)

        pa, pb, pc = pantalla[ia], pantalla[ib], pantalla[ic]
        area = (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pb[1] - pa[1]) * (pc[0] - pa[0])
        if abs(area) < 1e-9:
            continue
        x0 = max(0, int(min(pa[0], pb[0], pc[0])))
        x1 = min(W - 1, int(max(pa[0], pb[0], pc[0])) + 1)
        y0 = max(0, int(min(pa[1], pb[1], pc[1])))
        y1 = min(H - 1, int(max(pa[1], pb[1], pc[1])) + 1)
        if x1 < x0 or y1 < y0:
            continue

        # Coordenadas baricéntricas por incrementos: son lineales en x e y,
        # así que se avanzan sumando en vez de recalcularlas por píxel.
        d0x = (pb[1] - pc[1]) / area
        d0y = (pc[0] - pb[0]) / area
        d1x = (pc[1] - pa[1]) / area
        d1y = (pa[0] - pc[0]) / area
        px, py = x0 + 0.5, y0 + 0.5
        l0_fila = ((pb[0] - px) * (pc[1] - py) - (pb[1] - py) * (pc[0] - px)) / area
        l1_fila = ((pc[0] - px) * (pa[1] - py) - (pc[1] - py) * (pa[0] - px)) / area
        za, zb, zc = pa[2], pb[2], pc[2]

        for y in range(y0, y1 + 1):
            l0, l1 = l0_fila, l1_fila
            fila = y * W
            for x in range(x0, x1 + 1):
                if l0 >= 0.0 and l1 >= 0.0 and l0 + l1 <= 1.0:
                    i = fila + x
                    invz = zc + l0 * (za - zc) + l1 * (zb - zc)
                    if invz > zbuf[i]:
                        zbuf[i] = invz
                        lienzo[i * 3:i * 3 + 3] = rgb
                l0 += d0x
                l1 += d1x
            l0_fila += d0y
            l1_fila += d1y

    if s == 1:
        return escribir_png(ruta, tam, tam, lienzo)

    salida = bytearray(tam * tam * 3)
    total = s * s
    for y in range(tam):
        for x in range(tam):
            r = g = b = 0
            for dy in range(s):
                base = ((y * s + dy) * W + x * s) * 3
                for dx in range(s):
                    r += lienzo[base + dx * 3]
                    g += lienzo[base + dx * 3 + 1]
                    b += lienzo[base + dx * 3 + 2]
            i = (y * tam + x) * 3
            salida[i] = r // total
            salida[i + 1] = g // total
            salida[i + 2] = b // total
    return escribir_png(ruta, tam, tam, salida)
