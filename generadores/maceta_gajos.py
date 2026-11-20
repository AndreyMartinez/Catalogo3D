#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maceta de gajos: cubremaceta alta con lóbulos en anillo, estría vertical
fina y la boca ondulada siguiendo cada gajo.

Sale de una foto de referencia (11-19): cuenco crema de lóbulos fundidos,
cada uno como una bola, con pliegues hondos entre ellos y estría fina en toda
la cara. Aquí se estira a lo alto (≈1.6× el ancho) para que los lóbulos se
lean como gajos.

    python3 maceta_gajos.py --solo-stl --salida /ruta     # para el precheck
    python3 maceta_gajos.py --lobulos 8 --pliegue 6

La planta es un anillo de círculos (los gajos) unidos por redondeos cóncavos,
igual que los tres lóbulos del portacubiertos ondas pero en corona. A cada
altura la planta entera se escala con el perfil (base angosta, panza abajo
de la mitad, boca que cierra un poco), así la estría —repartida por fracción
del perímetro— sube recta por el gajo. La boca baja en cada pliegue como en
la foto. Sin hoyo: va una maceta de vivero adentro.
"""

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nucleo import exportar, malla as M, render                 # noqa: E402
from portacubiertos_ondas import (copiar_ajustes, estria, gramos,  # noqa: E402
                                  normales, remuestrear)

PRUEBAS = Path.home() / "Desktop" / "own design 3d" / "Pruebas de productos"
AJUSTES = PRUEBAS / "Portacubiertos_Oleaje_M.3mf"
PLATO = 256.0

P = {
    "diametro": 106.0,       # en las crestas de los gajos: acostada cabe en
    "alto": 170.0,           # la caja 20×16×11
    "lobulos": 6,
    "pliegue": 8.0,          # lo que entra el pliegue respecto a la cresta
    "redondeo": 4.0,         # radio del fondo del pliegue
    "base": 0.74,            # escala de la planta en el piso
    "panza": 0.38,           # altura de la panza, fracción del alto
    "boca": 0.88,            # escala de la planta en la boca
    "cierre": 1.0,           # 1 cierra parejo; menos de 1 cierra pronto y
                             # deja la panza abajo como bulbo, sin quiebre
    "ola": 6.0,              # lo que baja la boca en cada pliegue
    "giro": 0.0,             # grados que gira la corona del piso a la boca:
                             # los gajos suben en espiral, trenzados
    "paso": 2.6,             # estría
    "relieve": 0.7,          # cresta sobre el valle
    "pared": 1.24,           # en el valle: dos hilos de 0.62
    "piso": 1.6,
    "dz": 0.8,
    "puntos_estria": 6,
}


# ── Planta: corona de gajos ─────────────────────────────────────────────

def _centro_redondeo(c, rho, f, a):
    """Distancia al centro del redondeo tangente a dos gajos vecinos."""
    return c * math.cos(a) + math.sqrt((rho + f) ** 2 - (c * math.sin(a)) ** 2)


def radio_gajo(R, n, pliegue, f):
    """Radio del gajo para que el fondo del pliegue quede `pliegue` mm adentro
    de la cresta (R). Bisección: entre más grande el gajo, menos hondo."""
    a = math.pi / n
    lo, hi = R * math.sin(a) / (1 + math.sin(a)) + 1e-6, R - 1e-6
    for _ in range(80):
        rho = (lo + hi) / 2
        hondo = R - (_centro_redondeo(R - rho, rho, f, a) - f)
        lo, hi = (rho, hi) if hondo > pliegue else (lo, rho)
    return (lo + hi) / 2


def _giro(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def corona(R, n, pliegue, f, por_arco=240):
    """Contorno antihorario que arranca a media cintura del último pliegue."""
    rho = radio_gajo(R, n, pliegue, f)
    c, a = R - rho, math.pi / n
    cf = _centro_redondeo(c, rho, f, a)
    C = [(c * math.cos(2 * a * k), c * math.sin(2 * a * k)) for k in range(n)]
    F = [(cf * math.cos(2 * a * k + a), cf * math.sin(2 * a * k + a)) for k in range(n)]
    pts, inicio = [], 0
    for k in range(n):
        (cx, cy), (fx, fy), (px, py) = C[k], F[k], F[k - 1]
        g0 = math.atan2(py - cy, px - cx)
        d = (math.atan2(fy - cy, fx - cx) - g0) % (2 * math.pi)
        pts += [(cx + rho * math.cos(g0 + d * i / por_arco),
                 cy + rho * math.sin(g0 + d * i / por_arco)) for i in range(por_arco)]
        nx, ny = C[(k + 1) % n]
        a0 = math.atan2(cy - fy, cx - fx)
        d = _giro(math.atan2(ny - fy, nx - fx) - a0)
        m = por_arco // 4
        if k == n - 1:
            inicio = len(pts) + m // 2
        pts += [(fx + f * math.cos(a0 + d * i / m),
                 fy + f * math.sin(a0 + d * i / m)) for i in range(m)]
    return pts[inicio:] + pts[:inicio]


def escala(p, t):
    """Perfil: de la base a la panza abre como cuarto de seno; de la panza a
    la boca cierra suave. 1 = la planta de las crestas."""
    tp = p["panza"]
    if t <= tp:
        return p["base"] + (1 - p["base"]) * math.sin(math.pi / 2 * t / tp)
    s = (t - tp) / (1 - tp)
    return 1 - (1 - p["boca"]) * math.sin(math.pi / 2 * s ** p["cierre"]) ** 2


def cuerpo(p):
    n, R = int(p["lobulos"]), p["diametro"] / 2.0 - p["relieve"]
    dense = corona(R, n, p["pliegue"], p["redondeo"])
    _, largo = remuestrear(dense, len(dense))
    por_gajo = max(1, round(largo / n / p["paso"]))
    estrias = por_gajo * n
    base, _ = remuestrear(dense, estrias * p["puntos_estria"])
    nor = normales(base)
    # La boca baja hacia cada pliegue: coseno del ángulo al eje del gajo, que
    # deja una cúspide en el pliegue como en la foto.
    a = math.pi / n
    alto = [p["alto"] - p["ola"] * (1 - math.cos(n / 2.0 *
            (((math.atan2(y, x) + a) % (2 * a)) - a))) for x, y in base]

    pasos = max(2, round(p["alto"] / p["dz"]))
    m = M.Malla()
    fuera, dentro = [], []
    for i in range(pasos + 1):
        t = i / pasos
        s = escala(p, t)
        g = math.radians(p["giro"]) * t
        cg, sg = math.cos(g), math.sin(g)
        f_, d_ = [], []
        for k, ((x0, y0), (nx0, ny0)) in enumerate(zip(base, nor)):
            # La estría gira con la corona, así sigue al gajo en la espiral.
            x, y = x0 * cg - y0 * sg, x0 * sg + y0 * cg
            nx, ny = nx0 * cg - ny0 * sg, nx0 * sg + ny0 * cg
            e = estria(p, k / p["puntos_estria"] + 0.5)
            z = t * alto[k]
            f_.append(m.punto(s * x + nx * e, s * y + ny * e, z))
            d_.append(m.punto(s * x - nx * p["pared"], s * y - ny * p["pared"], z))
        fuera.append(f_)
        dentro.append(d_)
    N = len(base)
    for i in range(pasos):
        for k in range(N):
            k2 = (k + 1) % N
            m.quad(fuera[i][k], fuera[i][k2], fuera[i + 1][k2], fuera[i + 1][k])
            m.quad(dentro[i][k], dentro[i + 1][k], dentro[i + 1][k2], dentro[i][k2])
    for k in range(N):
        k2 = (k + 1) % N
        m.quad(fuera[-1][k], fuera[-1][k2], dentro[-1][k2], dentro[-1][k])
        m.quad(fuera[0][k], dentro[0][k], dentro[0][k2], fuera[0][k2])
    m.normalizar()

    # Piso: la planta de adentro en la base, metida medio milímetro en la pared.
    b, _ = remuestrear(dense, 720)
    s0 = escala(p, 0.0)
    piso = [(s0 * x - nx * (p["pared"] - 0.5), s0 * y - ny * (p["pared"] - 0.5))
            for (x, y), (nx, ny) in zip(b, normales(b))]
    placa = M.placa(M.orientar(piso), [], 0.0, p["piso"])
    assert placa is not None, "no se pudo triangular el piso"
    m.unir(placa)
    return m, estrias


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(PRUEBAS))
    ap.add_argument("--nombre", default="Maceta_Gajos")
    ap.add_argument("--copias", type=int, default=4, help="por plato, en 2×2")
    ap.add_argument("--ajustes", default=str(AJUSTES),
                    help="otro .3mf de Bambu Studio del que copiar el laminado")
    ap.add_argument("--solo-stl", action="store_true",
                    help="para el precheck: una pieza, sin 3MF")
    for k, val in P.items():
        ap.add_argument("--" + k.replace("_", "-"), dest=k, type=type(val), default=None)
    a = ap.parse_args()
    p = dict(P)
    for k in p:
        if getattr(a, k) is not None:
            p[k] = getattr(a, k)

    m, estrias = cuerpo(p)
    carpeta = Path(a.salida).expanduser()
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / (a.nombre + ".3mf")
    (x0, y0, _), (x1, y1, z1) = m.caja()
    if a.solo_stl:
        exportar.guardar_stl([("maceta", m, PLATO / 2, PLATO / 2)],
                             ruta.with_suffix(".stl"), a.nombre)
        print(ruta.with_suffix(".stl"))
    else:
        # Rejilla de columnas × filas, 8 mm entre piezas, centrada en el plato.
        hueco, w, h = 8.0, x1 - x0, y1 - y0
        cols = min(a.copias, max(1, int((PLATO - 10 + hueco) // (w + hueco))))
        filas = -(-a.copias // cols)
        assert filas * h + (filas - 1) * hueco <= PLATO - 10, \
            "no caben %d en el plato" % a.copias
        piezas = []
        for i in range(a.copias):
            c, r = i % cols, i // cols
            piezas.append(("maceta %d" % (i + 1), m,
                           PLATO / 2 + (c - (cols - 1) / 2) * (w + hueco),
                           PLATO / 2 + (r - (filas - 1) / 2) * (h + hueco)))
        png = render.render(m.v, m.t, tam=512, suavizado=2,
                            direccion=render.vector_vista(20, 24),
                            ruta=ruta.with_suffix(".png"))
        exportar.guardar_3mf(piezas, ruta, a.nombre, miniatura=png,
                             notas="%s · %.0f×%.0f×%.0f mm" % (a.nombre, w, h, z1),
                             parametros=dict(p, diseno="maceta_gajos"))
        exportar.guardar_stl(piezas[:1], ruta.with_suffix(".stl"), a.nombre)
        if a.ajustes and Path(a.ajustes).exists():
            copiar_ajustes(ruta, a.ajustes)
        print(ruta)
    r_in = escala(p, 1.0) * (p["diametro"] / 2 - p["relieve"] - p["pliegue"]) - p["pared"]
    print("  %.1f × %.1f × %.1f mm, %d estrías, boca libre ≈ %.0f mm de diámetro"
          % (x1 - x0, y1 - y0, z1, estrias, 2 * r_in))
    print("  ≈ %s g por pieza (suma de sólidos encimados)" % gramos(m))


if __name__ == "__main__":
    main()
