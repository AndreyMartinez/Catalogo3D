#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Puzzle Ondas en óvalo, partido en dos mitades con cola de milano vertical.

Cabe en la caja de 200 × 160 × 110: cada mitad mide ~186 × 123 × 24 y las dos
apiladas suben 48 mm. Armado mide 246 × 186.

La cara de arriba es un campo de alturas sobre el dominio de cada mitad. El
dominio se describe con una distancia con signo (óvalo ∩ lado del corte) y se
malla con cuadrados marchantes: cada celda de la rejilla aporta su trozo de
cara superior, el mismo trozo abajo en z = 0 y, donde la celda toca el borde,
la pared vertical. Así el corte con sus lengüetas sale cerrado y sin soporte.

    python3 puzzle_ovalo.py --salida /ruta            # mitades + render
    python3 puzzle_ovalo.py --salida /ruta --prueba   # tira de prueba de la unión
    python3 puzzle_ovalo.py --salida /ruta --completo # todo en una placa
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import puzzle_perro as PP                          # noqa: E402
from puzzle_perro import M, render                 # noqa: E402

P = dict(PP.CONCEPTOS["ondas"], piso=5.0, relieve=17.0, labio_alto=24.0,
         semi_x=123.0, semi_y=93.0,          # óvalo 246 × 186
         lengueta_y=(-48.0, 0.0, 48.0),      # centros de las colas de milano
         cuello=10.0, cabeza=16.0, hondo=9.0,  # mm
         holgura=0.30,                       # total entre caras; 0.15 por lado
         paso=0.5)                           # rejilla (mm)


def altura(x, y, p=P):
    """Ondas de puzzle_perro llevadas al óvalo: el radio equivalente escala
    cada eje para que los anillos sigan el contorno."""
    q = math.hypot(x / p["semi_x"], y / p["semi_y"])
    r = min(q, 1.0) * p["radio"]
    th = math.atan2(y, x)
    return PP.altura("ondas", r, th, p)


def sdf_ovalo(x, y, p=P):
    q = math.hypot(x / p["semi_x"], y / p["semi_y"])
    return (q - 1.0) * min(p["semi_x"], p["semi_y"])


def poligono_corte(p=P):
    """Territorio de la mitad izquierda: todo x < 0 más las lengüetas que
    entran en la derecha. Antihorario."""
    pts = [(-400.0, -400.0), (0.0, -400.0)]
    for yc in p["lengueta_y"]:
        c, h, d = p["cuello"] / 2, p["cabeza"] / 2, p["hondo"]
        pts += [(0.0, yc - c), (d, yc - h), (d, yc + h), (0.0, yc + c)]
    pts += [(0.0, 400.0), (-400.0, 400.0)]
    return pts


def sdf_poligono(poly, x, y):
    d = M.distancia_al_borde(poly, (x, y))
    return -d if M.dentro(poly, (x, y)) else d


def malla_campo(sdf, alto, caja, paso):
    """Sólido = {sdf < 0} extruido de z = 0 hasta alto(x, y)."""
    (x0, y0), (x1, y1) = caja
    ni, nj = int((x1 - x0) / paso) + 2, int((y1 - y0) / paso) + 2
    X = [x0 + i * paso for i in range(ni)]
    Y = [y0 + j * paso for j in range(nj)]
    S = [[sdf(X[i], Y[j]) for j in range(nj)] for i in range(ni)]
    m = M.Malla()
    arriba, abajo = {}, {}

    def vert(clave, x, y):
        if clave not in arriba:
            arriba[clave] = m.punto(x, y, alto(x, y))
            abajo[clave] = m.punto(x, y, 0.0)
        return clave

    def nodo(i, j):
        return vert(("n", i, j), X[i], Y[j])

    def cruce(a, b):
        (i, j), (k, l) = a, b
        sa, sb = S[i][j], S[k][l]
        t = sa / (sa - sb)
        clave = ("e",) + tuple(sorted((a, b)))
        return vert(clave, X[i] + t * (X[k] - X[i]), Y[j] + t * (Y[l] - Y[j]))

    for i in range(ni - 1):
        for j in range(nj - 1):
            esq = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            dentro = [S[a][b] < 0 for a, b in esq]
            if not any(dentro):
                continue
            poly, borde = [], []
            for n in range(4):
                a, b = esq[n], esq[(n + 1) % 4]
                da, db = dentro[n], dentro[(n + 1) % 4]
                if da:
                    poly.append((nodo(*a), False))
                if da != db:
                    poly.append((cruce(a, b), True))
            claves = [c for c, _ in poly]
            for n in range(1, len(claves) - 1):
                m.cara(arriba[claves[0]], arriba[claves[n]], arriba[claves[n + 1]])
                m.cara(abajo[claves[0]], abajo[claves[n + 1]], abajo[claves[n]])
            # pared: dos cruces seguidos en el recorrido antihorario = borde
            for n in range(len(poly)):
                (ca, ea), (cb, eb) = poly[n], poly[(n + 1) % len(poly)]
                if ea and eb:
                    m.quad(arriba[cb], arriba[ca], abajo[ca], abajo[cb])
    m.normalizar()
    return m


def mitades(p=P, alto=None, caja=None):
    poly = poligono_corte(p)
    g = p["holgura"] / 2
    alto = alto or (lambda x, y: altura(x, y, p))
    sx, sy = p["semi_x"] + 1, p["semi_y"] + 1
    izq = malla_campo(lambda x, y: max(sdf_ovalo(x, y, p), sdf_poligono(poly, x, y) + g),
                      alto, caja or ((-sx, -sy), (p["hondo"] + 1, sy)), p["paso"])
    der = malla_campo(lambda x, y: max(sdf_ovalo(x, y, p), -sdf_poligono(poly, x, y) + g),
                      alto, caja or ((-1, -sy), (sx, sy)), p["paso"])
    return izq, der


def girada(m, grados):
    c, s = math.cos(math.radians(grados)), math.sin(math.radians(grados))
    g = M.Malla()
    g.v = [(x * c - y * s, x * s + y * c, z) for x, y, z in m.v]
    g.t = list(m.t)
    return g


def en_placa(piezas, separacion=6.0, grados=45.0):
    """Las dos mitades como van armadas, abiertas 2 × `separacion` sobre el
    eje largo y giradas en la diagonal: así el óvalo (246 mm) entra en la
    placa de 256, que en fila no alcanza (132 + 123 + hueco)."""
    sal = []
    for (n, m), dx in zip(piezas, (-separacion, separacion)):
        sal.append((n, girada(m.trasladada(dx, 0, 0), grados),
                    PP.CENTRO_PLATO, PP.CENTRO_PLATO))
    todos = [v for _, m, _, _ in sal for v in m.v]
    xs = [v[0] for v in todos]; ys = [v[1] for v in todos]
    print("en placa: %.1f × %.1f mm" % (max(xs) - min(xs), max(ys) - min(ys)))
    return sal


def datos(m):
    (a, b, c), (d, e, f) = m.caja()
    return {"x": round(d - a, 1), "y": round(e - b, 1), "z": round(f - c, 1),
            "cm3": round(m.volumen() / 1000, 1), "sueltas": m.aristas_sueltas()}


def tira(p=P):
    """Tira de 60 × 50 × 8 con una sola cola de milano: prueba la holgura en
    22 minutos antes de gastar las mitades."""
    p = dict(p, lengueta_y=(0.0,))
    corte = poligono_corte(p)
    g = p["holgura"] / 2
    a = malla_campo(lambda x, y: max(abs(y) - 25, -x - 30, sdf_poligono(corte, x, y) + g),
                    lambda x, y: 8.0, ((-31, -26), (p["hondo"] + 1, 26)), p["paso"])
    b = malla_campo(lambda x, y: max(abs(y) - 25, x - 30, -sdf_poligono(corte, x, y) + g),
                    lambda x, y: 8.0, ((-1, -26), (31, 26)), p["paso"])
    return [("prueba A", a), ("prueba B", b)]


def en_esquinas(tiras, ocupado, margen=4.0, holgura_min=3.0):
    """Mete cada tira en una esquina libre de la placa (las que deja el óvalo
    en diagonal: arriba-izquierda y abajo-derecha). `ocupado` son los puntos
    (x, y) en coordenadas de placa de lo que ya está puesto."""
    sal = []
    esquinas = [("izq", "arriba"), ("der", "abajo")]
    for (n, m), (lx, ly) in zip(tiras, esquinas):
        (x0, y0, _), (x1, y1, _) = m.caja()
        w, h = x1 - x0, y1 - y0
        px = margen if lx == "izq" else PP.CENTRO_PLATO * 2 - margen - w
        py = PP.CENTRO_PLATO * 2 - margen - h if ly == "arriba" else margen
        dx, dy = px - x0, py - y0
        cerca = min(max(px - x, x - (px + w), 0) ** 2 + max(py - y, y - (py + h), 0) ** 2
                    for x, y in ocupado) ** 0.5
        if cerca < holgura_min:
            raise SystemExit("la tira %s no cabe en su esquina (%.1f mm del óvalo)" % (n, cerca))
        print("%s en esquina %s-%s, a %.1f mm del óvalo" % (n, lx, ly, cerca))
        sal.append((n, m, dx, dy))
    return sal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=".")
    ap.add_argument("--prueba", action="store_true",
                    help="solo la tira de 60 × 50 × 8 con una lengüeta, para la holgura")
    ap.add_argument("--completo", action="store_true",
                    help="una sola placa: las dos mitades y la tira de prueba en las esquinas")
    ap.add_argument("--color", default="92,94,96")
    a = ap.parse_args()
    out = Path(a.salida)
    out.mkdir(parents=True, exist_ok=True)
    color = tuple(int(c) for c in a.color.split(","))

    if a.prueba:
        piezas = tira()
        nombre = "PuzzleOndas_PruebaUnion"
    else:
        izq, der = mitades()
        piezas = [("izquierda", izq), ("derecha", der)]
        nombre = "PuzzleOndas_Ovalo_Completo" if a.completo else "PuzzleOndas_Ovalo"
    for n, m in piezas:
        print(n, json.dumps(datos(m)))

    armado = M.Malla()
    for n, m in piezas:
        armado.unir(m)
    png = render.render(armado.v, armado.t, tam=512, suavizado=2, color=color,
                        direccion=render.vector_vista(20, 38), ruta=out / (nombre + ".png"))
    # separado: la derecha se corre 40 mm para que se vea la unión
    sep = M.Malla().unir(piezas[0][1]).unir(piezas[1][1].trasladada(40, 0, 0))
    render.render(sep.v, sep.t, tam=512, suavizado=2, color=color,
                  direccion=render.vector_vista(200, 40), ruta=out / (nombre + "_separado.png"))
    from nucleo import exportar
    if a.prueba:
        acomodo = exportar.acomodar(piezas, PP.CENTRO_PLATO, hueco=6.0)
    else:
        acomodo = en_placa(piezas)
    if a.completo:
        ocupado = [(x + dx, y + dy) for _, m, dx, dy in acomodo for x, y, z in m.v if z < 0.01]
        acomodo += en_esquinas(tira(), ocupado)
    exportar.guardar_3mf(acomodo, out / (nombre + ".3mf"), nombre, miniatura=png, notas=nombre,
                         parametros={k: v for k, v in P.items() if not k.startswith("_")})
    PP.aplicar_ajustes(out / (nombre + ".3mf"))


if __name__ == "__main__":
    main()
