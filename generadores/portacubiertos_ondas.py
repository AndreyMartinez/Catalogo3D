#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portacubiertos ondas: tres lóbulos fundidos en una sola cinta, con panzas
apiladas al subir y estría vertical fina.

Sale de una foto de referencia (10-22): pieza negra de tres cilindros unidos
cuyo perfil sube en ondas (panza, cuello, panza…) y toda la cara lleva estría
fina. La boca queda a una sola altura.

    python3 portacubiertos_ondas.py --salida /ruta --nombre MiPieza
    python3 portacubiertos_ondas.py --ondas 4 --amplitud 2.5 --solo-stl

La planta es el contorno de tres lóbulos del trenzado; a cada altura el radio
de los lóbulos cambia con las ondas, y la estría se reparte por fracción del
perímetro, así cada canal sube recto sin torcerse. Por dentro la pared es
lisa: valle de dos hilos (ver la regla en tiempo-lo-manda-el-numero-de-trazos).
El piso y los dos divisores son sólidos aparte, encimados en la pared; el
laminador los une.
"""

import argparse
import json
import math
import zipfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nucleo import exportar, malla as M, render                 # noqa: E402
from portacubiertos_trenzado import tres_lobulos                # noqa: E402
from portacepillos_rapido import ajustes_por_objeto             # noqa: E402

PRUEBAS = Path.home() / "Desktop" / "own design 3d" / "Pruebas de productos"
# El oleaje M ya trae la receta rápida (1 vuelta Arachne, hilos de 0.62,
# Bambu PLA Basic en la P2S): se copian sus ajustes tal cual.
AJUSTES = PRUEBAS / "Portacubiertos_Oleaje_M.3mf"

PLATO = 256.0
DENSIDAD = 1.24          # g/cm³, PLA

P = {
    "ancho": 200.0,          # v3 aprobada (10-23): más corto y gordito que el
    "fondo": 88.0,           # Torsión (195.5 × 78); fondo a las crestas
    "alto": 102.0,
    "ondas": 3,              # panzas a lo alto
    "amplitud": 4.5,         # lo que entra el radio en cada cuello
    "cintura": 6.0,          # radio del redondeo cóncavo entre lóbulos
    "paso": 3.0,             # estría
    "relieve": 0.7,          # cresta sobre el valle
    "pared": 1.24,           # en el valle: dos hilos de 0.62
    "piso": 1.2,             # como el oleaje M v3: es la palanca del peso
    "divisor": 2.0,
    "boca_divisor": 3.0,     # el divisor queda este tanto abajo de la boca
    "dz": 0.8,               # entre anillos
    "puntos_estria": 6,
}


def radio(p, z):
    """Radio del lóbulo al valle de la estría. Las ondas son un coseno: la
    base y la boca caen en cuello y las panzas entre medio, como en la foto."""
    r_max = p["fondo"] / 2.0 - p["relieve"]
    t = z / p["alto"]
    return r_max - p["amplitud"] * 0.5 * (1 + math.cos(2 * math.pi * p["ondas"] * t))


def remuestrear(pts, n):
    """n puntos repartidos parejo por longitud sobre el contorno cerrado."""
    largos = [0.0]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        largos.append(largos[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = largos[-1]
    sal, j = [], 0
    for i in range(n):
        s = total * i / n
        while largos[j + 1] < s:
            j += 1
        a, b = pts[j], pts[(j + 1) % len(pts)]
        w = (s - largos[j]) / max(1e-12, largos[j + 1] - largos[j])
        sal.append((a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w))
    return sal, total


def normales(pts):
    """Normal hacia afuera de un contorno antihorario."""
    n = len(pts)
    sal = []
    for k in range(n):
        (x0, y0), (x1, y1) = pts[k - 1], pts[(k + 1) % n]
        dx, dy = x1 - x0, y1 - y0
        l = math.hypot(dx, dy) or 1.0
        sal.append((dy / l, -dx / l))
    return sal


def estria(p, s):
    """Cresta plana y surco angosto (acabado «canal» del motor), 0 a relieve."""
    d = abs(s % 1.0 - 0.5)
    if d <= 0.18:
        u = 1.0
    elif d >= 0.36:
        u = 0.0
    else:
        t = (d - 0.18) / 0.18
        u = 1.0 - t * t * (3.0 - 2.0 * t)
    return p["relieve"] * u


def separacion(p):
    return (p["ancho"] - p["fondo"]) / 2.0


def tramos(R, f, d):
    """Los ocho arcos del contorno de tres lóbulos, cada uno por separado: así
    cada estría queda amarrada a su arco y sube recta aunque el radio cambie."""
    pts = tres_lobulos(R, f, d, n_lobulo=240, n_cintura=60)
    cortes = [0, 480, 540, 780, 840, 1320, 1380, 1620, 1680]
    return [pts[a:b + 1] if b < len(pts) else pts[a:] + pts[:1]
            for a, b in zip(cortes, cortes[1:])]


def contorno(R, f, d, por_tramo, puntos_estria):
    """Contorno remuestreado parejo dentro de cada arco, con `por_tramo[j]`
    estrías en el arco j."""
    sal = []
    for tr, ne in zip(tramos(R, f, d), por_tramo):
        largos = [0.0]
        for a, b in zip(tr, tr[1:]):
            largos.append(largos[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        n, j = ne * puntos_estria, 0
        for i in range(n):
            s = largos[-1] * i / n
            while largos[j + 1] < s:
                j += 1
            a, b = tr[j], tr[j + 1]
            w = (s - largos[j]) / max(1e-12, largos[j + 1] - largos[j])
            sal.append((a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w))
    return sal


def cuerpo(p):
    d = separacion(p)
    largos = []
    for tr in tramos(radio(p, 0.0), p["cintura"], d):
        largos.append(sum(math.hypot(b[0] - a[0], b[1] - a[1])
                          for a, b in zip(tr, tr[1:])))
    por_tramo = [max(1, round(l / p["paso"])) for l in largos]
    estrias = sum(por_tramo)
    n = estrias * p["puntos_estria"]
    pasos = max(2, round(p["alto"] / p["dz"]))
    m = M.Malla()
    fuera, dentro = [], []
    for i in range(pasos + 1):
        z = p["alto"] * i / pasos
        base = contorno(radio(p, z), p["cintura"], d, por_tramo, p["puntos_estria"])
        nor = normales(base)
        f, a = [], []
        for k, ((x, y), (nx, ny)) in enumerate(zip(base, nor)):
            e = estria(p, k / p["puntos_estria"] + 0.5)
            f.append(m.punto(x + nx * e, y + ny * e, z))
            a.append(m.punto(x - nx * p["pared"], y - ny * p["pared"], z))
        fuera.append(f)
        dentro.append(a)
    for i in range(pasos):
        for k in range(n):
            k2 = (k + 1) % n
            m.quad(fuera[i][k], fuera[i][k2], fuera[i + 1][k2], fuera[i + 1][k])
            m.quad(dentro[i][k], dentro[i + 1][k], dentro[i + 1][k2], dentro[i][k2])
    for k in range(n):
        k2 = (k + 1) % n
        m.quad(fuera[-1][k], fuera[-1][k2], dentro[-1][k2], dentro[-1][k])
        m.quad(fuera[0][k], dentro[0][k], dentro[0][k2], fuera[0][k2])
    m.normalizar()

    # Piso: el contorno de adentro corrido medio milímetro hacia la pared.
    base, _ = remuestrear(tres_lobulos(radio(p, 0.0), p["cintura"], d), 720)
    piso = [(x - nx * (p["pared"] - 0.5), y - ny * (p["pared"] - 0.5))
            for (x, y), (nx, ny) in zip(base, normales(base))]
    placa = M.placa(M.orientar(piso), [], 0.0, p["piso"])
    assert placa is not None, "no se pudo triangular el piso"
    m.unir(placa)

    # Divisores en las cinturas: a cada altura llegan hasta la pared y se
    # meten 0.6 mm en ella.
    z_top = p["alto"] - p["boca_divisor"]
    for cx in (-d / 2.0, d / 2.0):
        dv = M.Malla()
        filas = []
        pasos_d = max(2, round(z_top / p["dz"]))
        for i in range(pasos_d + 1):
            z = z_top * i / pasos_d
            R, f = radio(p, z), p["cintura"]
            yf = math.sqrt((R + f) ** 2 - (d / 2.0) ** 2)
            y = yf - f - p["pared"] + 0.6
            t = p["divisor"] / 2.0
            filas.append([dv.punto(cx + sx * t, sy * y, z)
                          for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        for a, b in zip(filas, filas[1:]):
            for k in range(4):
                k2 = (k + 1) % 4
                dv.quad(a[k], a[k2], b[k2], b[k])
        dv.quad(*filas[0][::-1])
        dv.quad(*filas[-1])
        m.unir(dv.normalizar())
    return m, estrias


def gramos(m):
    return round(abs(m.volumen()) / 1000.0 * DENSIDAD, 1)


def copiar_ajustes(ruta, origen):
    """Mete en el .3mf los ajustes de laminado de otro proyecto de Bambu
    Studio. Sin la línea `Application` el CLI ignora project_settings.config."""
    with zipfile.ZipFile(origen) as z:
        cfg = z.read("Metadata/project_settings.config")
    with zipfile.ZipFile(ruta) as z:
        todo = {n: z.read(n) for n in z.namelist()}
    todo["Metadata/project_settings.config"] = cfg
    modelo = todo["3D/3dmodel.model"].decode("utf-8")
    modelo = modelo.replace(
        '<metadata name="Title">',
        '<metadata name="Application">BambuStudio-02.08.02.61</metadata>\n'
        '<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        '<metadata name="Title">', 1)
    todo["3D/3dmodel.model"] = modelo.encode("utf-8")
    todo["Metadata/model_settings.config"] = ajustes_por_objeto(modelo)
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in todo.items():
            z.writestr(n, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(PRUEBAS))
    ap.add_argument("--nombre", default="Portacubiertos_Ondas")
    ap.add_argument("--copias", type=int, default=2, help="por plato")
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
        exportar.guardar_stl([("portacubiertos", m, PLATO / 2, PLATO / 2)],
                             ruta.with_suffix(".stl"), a.nombre)
        print(ruta.with_suffix(".stl"))
    else:
        # Copias una tras otra a lo hondo del plato, 8 mm entre ellas.
        hueco, fondo = 8.0, y1 - y0
        total = a.copias * fondo + (a.copias - 1) * hueco
        assert total <= PLATO - 10, "no caben %d en el plato" % a.copias
        piezas = [("portacubiertos %d" % (i + 1), m, PLATO / 2,
                   PLATO / 2 - total / 2 + fondo / 2 + i * (fondo + hueco))
                  for i in range(a.copias)]
        png = render.render(m.v, m.t, tam=512, suavizado=2,
                            direccion=render.vector_vista(20, 24),
                            ruta=ruta.with_suffix(".png"))
        exportar.guardar_3mf(piezas, ruta, a.nombre, miniatura=png,
                             notas="%s · %.0f×%.0f×%.0f mm" % (a.nombre, x1 - x0, fondo, z1),
                             parametros=dict(p, diseno="portacubiertos_ondas"))
        exportar.guardar_stl(piezas[:1], ruta.with_suffix(".stl"), a.nombre)
        if a.ajustes and Path(a.ajustes).exists():
            copiar_ajustes(ruta, a.ajustes)
        print(ruta)
    print("  %.1f × %.1f × %.1f mm, %d estrías, cuello a %.1f mm de radio"
          % (x1 - x0, y1 - y0, z1, estrias, radio(p, 0.0)))
    print("  ≈ %s g por pieza (suma de sólidos encimados)" % gramos(m))


if __name__ == "__main__":
    main()
