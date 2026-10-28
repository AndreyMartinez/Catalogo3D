#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portacontroles tejido: caja de esquinas redondas con el borde que baja en
diagonal de izquierda a derecha y una textura de costillas con cuentas que se
abultan en bandas onduladas, como tejido.

Sale de una foto de referencia (10-23): caja terracota, alta a la izquierda
(controles) y baja a la derecha. v2 (mismo día, a pedido): tres
compartimentos en fila, borde en diagonal casi recta en vez de curva en S,
el piso de cada compartimento subido un escalón más que el anterior. v5:
126 × 72.5: a lo hondo cabe un control de panza (~54 de ancho) o dos de
ladito (~26 c/u); el celular gordo con funda va en el primero, recargado en
diagonal. Esquinas de 8 en planta para que la curva no le coma lugar a los
huecos de las puntas.

    python3 portacontroles_tejido.py --salida /ruta --nombre MiPieza
    python3 portacontroles_tejido.py --alto 100 --alto-bajo 58 --3mf

Por defecto escribe el STL y la miniatura, que es lo que pide el precheck.
El .3mf solo con --3mf, ya con el visto bueno.

El relieve va solo por fuera y nunca hunde: la cara de la pared es el valle
y las costillas salen de ahí. El valle mide dos hilos de 0.62 (la regla de
la estría, ver portacubiertos-oleaje-m), por dentro todo liso.
"""

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nucleo import exportar, malla as M, render   # noqa: E402

DENSIDAD = 1.24          # g/cm³, PLA

P = {
    "ancho": 126.0,          # 42 + 38.75 + 38.75 por dentro, más pared y tabiques
    "fondo": 72.5,           # adentro 70: control de panza (~54) a lo hondo
                             # o dos de ladito (~26 c/u)
    "redondeo": 8.0,         # radio de las esquinas en planta
    "alto": 105.0,           # lado izquierdo
    "alto_bajo": 60.0,       # lado derecho
    "curva_desde": 0.18,     # fracción del ancho donde empieza a bajar…
    "curva_hasta": 0.82,     # … y donde ya llegó abajo
    "redondeo_borde": 14.0,  # medio largo del redondeo en cada quiebre
    "valle": 1.24,           # pared en el valle de la costilla: 2 hilos
    "relieve": 1.2,          # lo que sale la costilla más abultada
    "paso": 2.8,             # entre costillas, sobre el contorno
    "cuenta": 2.8,           # entre cuentas, a lo alto
    "base": 0.40,            # alto de la costilla lisa, en fracción del relieve
    "banda": 30.0,           # alto de una banda de cuentas
    "ondas": 4,              # vueltas de la onda de las bandas al contorno
    "vaiven": 1.6,           # cuánto se tuercen las bandas (radianes)
    "liso_arriba": 12.0,     # franja bajo el labio donde ya no hay cuentas
    "labio": 2.5,            # franja que cierra a ras de costillas
    "zoclo": 3.0,            # franja de abajo, cerrada también
    "chaflan": 0.6,          # pie de elefante
    "piso": 1.6,
    "divisor": 2.0,          # grueso de los divisores
    "baja_divisor": 10.0,    # cuánto quedan los divisores bajo el borde
    "hueco_1": 42.0,         # celular gordo (~82) recargado en diagonal:
                             # 42 × 70 da 81.6 de diagonal
    "hueco_2": 38.75,        # control de panza (~38 de grueso), justo; lo que
                             # sobra a la derecha, igual
    "alza_1": 8.0,           # cuánto sube el piso de cada compartimento
    "alza_2": 14.0,
    "alza_3": 20.0,
    "grano": 0.45,           # lo más largo de una faceta a lo alto
    "puntos_costilla": 6,
}


# ── Planta ────────────────────────────────────────────────────────────────

class Contorno:
    """Rectángulo de esquinas redondas recorrido por longitud de arco,
    antihorario, desde el centro del frente (y negativa)."""

    def __init__(self, ancho, fondo, r):
        self.a, self.b, self.r = ancho / 2 - r, fondo / 2 - r, r
        cuarto = math.pi * r / 2
        a, b = self.a, self.b
        self.tramos = [("x", 0.0, a, -1), ("c", -90.0, a, -b), ("y", -b, b, 1),
                       ("c", 0.0, a, b), ("x", a, -a, 1), ("c", 90.0, -a, b),
                       ("y", b, -b, -1), ("c", 180.0, -a, -b), ("x", -a, 0.0, -1)]
        self.largos = []
        for t in self.tramos:
            self.largos.append(cuarto if t[0] == "c" else abs(t[2] - t[1]))
        self.perimetro = sum(self.largos)

    def punto(self, s):
        """(x, y, nx, ny) a la distancia s del arranque."""
        s %= self.perimetro
        for t, largo in zip(self.tramos, self.largos):
            if s <= largo + 1e-9:
                f = s / largo if largo else 0.0
                if t[0] == "x":
                    x = t[1] + (t[2] - t[1]) * f
                    lado = self.b + self.r
                    return x, t[3] * lado, 0.0, float(t[3])
                if t[0] == "y":
                    y = t[1] + (t[2] - t[1]) * f
                    lado = self.a + self.r
                    return t[3] * lado, y, float(t[3]), 0.0
                ang = math.radians(t[1] + 90.0 * f)
                nx, ny = math.cos(ang), math.sin(ang)
                return t[2] + self.r * nx, t[3] + self.r * ny, nx, ny
            s -= largo
        return self.punto(0.0)


def borde(p, x):
    """Alto del labio en x: meseta alta, diagonal recta, meseta baja. Cada
    quiebre se redondea con una parábola tangente a los dos tramos, así la
    diagonal se lee como corte y no como ola."""
    w = p["ancho"]
    x0 = -w / 2 + p["curva_desde"] * w
    x1 = -w / 2 + p["curva_hasta"] * w
    alto, bajo = p["alto"], p["alto_bajo"]
    k = (alto - bajo) / (x1 - x0)
    e = min(p["redondeo_borde"], (x1 - x0) / 2)
    if x <= x0 - e:
        return alto
    if x < x0 + e:
        return alto - k * (x - x0 + e) ** 2 / (4 * e)
    if x <= x1 - e:
        return alto - k * (x - x0)
    if x < x1 + e:
        return bajo + k * (x1 + e - x) ** 2 / (4 * e)
    return bajo


def _suave(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


# ── Relieve ───────────────────────────────────────────────────────────────

def relieve(p, s, z, tope, perimetro):
    """Cuánto sale la pared en (s, z), en mm, de 0 a `relieve`.

    Costillas verticales redondas; encima, una onda de bandas que se tuercen
    al dar la vuelta. Donde la banda está llena la costilla se ensancha y se
    parte en cuentas; donde está vacía queda una costilla lisa más baja."""
    a = p["relieve"]
    costilla = 0.5 + 0.5 * math.cos(2 * math.pi * s / p["paso"])
    fase = (2 * math.pi * z / p["banda"]
            + p["vaiven"] * math.sin(2 * math.pi * p["ondas"] * s / perimetro))
    w = 0.08 + 0.92 * (0.5 + 0.5 * math.sin(fase)) ** 0.7
    w *= _suave((tope - p["labio"] - z) / p["liso_arriba"])
    w *= _suave((z - p["zoclo"]) / 6.0)
    cuenta = 0.5 + 0.5 * math.cos(2 * math.pi * z / p["cuenta"])
    forma = costilla ** (1.6 - 0.9 * w)
    alto = p["base"] + (1 - p["base"]) * w * cuenta
    d = a * forma * alto
    # Labio y zoclo cerrados a ras de la costilla: aro limpio.
    cierre = max(1 - _suave((tope - z) / p["labio"]), 1 - _suave(z / p["zoclo"]))
    d = d + (a - d) * cierre
    return d - max(0.0, p["chaflan"] - z)


# ── Casco ─────────────────────────────────────────────────────────────────

def casco(p):
    c = Contorno(p["ancho"], p["fondo"], p["redondeo"])
    costillas = max(8, round(c.perimetro / p["paso"]))
    p = dict(p, paso=c.perimetro / costillas)
    n = costillas * int(p["puntos_costilla"])
    cols = [(k * c.perimetro / n,) + c.punto(k * c.perimetro / n) for k in range(n)]
    tope = [borde(p, x) for _, x, _, _, _ in cols]
    capas = int(math.ceil(p["alto"] / p["grano"]))
    fr_ext = [k / capas for k in range(capas + 1)]
    fr_int = [k / 16 for k in range(17)]

    m = M.Malla()
    ext, inte = [], []
    for fr in fr_ext:
        aro = []
        for i, (s, x, y, nx, ny) in enumerate(cols):
            z = tope[i] * fr
            d = relieve(p, s, z, tope[i], c.perimetro)
            aro.append(m.punto(x + nx * d, y + ny * d, z))
        ext.append(aro)
    for fr in fr_int:
        aro = []
        for i, (s, x, y, nx, ny) in enumerate(cols):
            z = p["piso"] + (tope[i] - p["piso"]) * fr
            aro.append(m.punto(x - nx * p["valle"], y - ny * p["valle"], z))
        inte.append(aro)
    for k in range(len(ext) - 1):
        for i in range(n):
            j = (i + 1) % n
            m.quad(ext[k][i], ext[k][j], ext[k + 1][j], ext[k + 1][i])
    for k in range(len(inte) - 1):
        for i in range(n):
            j = (i + 1) % n
            m.quad(inte[k][i], inte[k + 1][i], inte[k + 1][j], inte[k][j])
    for i in range(n):
        j = (i + 1) % n
        m.quad(ext[-1][i], ext[-1][j], inte[-1][j], inte[-1][i])
    c_abajo = m.punto(0.0, 0.0, 0.0)
    c_piso = m.punto(0.0, 0.0, p["piso"])
    for i in range(n):
        j = (i + 1) % n
        m.cara(c_abajo, ext[0][j], ext[0][i])
        m.cara(c_piso, inte[0][i], inte[0][j])
    return m, costillas


# ── Divisores ─────────────────────────────────────────────────────────────

def _barrido(secciones):
    """Sólido por una lista de secciones (listas de puntos 3D, mismo número),
    con tapas en abanico."""
    m = M.Malla()
    filas = [[m.punto(*q) for q in sec] for sec in secciones]
    n = len(filas[0])
    for a, b in zip(filas, filas[1:]):
        for k in range(n):
            k2 = (k + 1) % n
            m.quad(a[k], a[k2], b[k2], b[k])
    for fila, sec, abajo in ((filas[0], secciones[0], True),
                             (filas[-1], secciones[-1], False)):
        c = m.punto(*[sum(q[i] for q in sec) / n for i in range(3)])
        for k in range(n):
            k2 = (k + 1) % n
            m.cara(c, fila[k2], fila[k]) if abajo else m.cara(c, fila[k], fila[k2])
    return m.normalizar()


def _seccion(centro, g, z0, z1, a_3d):
    """Sección de tabique de grueso g con la cima en medio círculo.
    `a_3d(u, z)` la coloca: u es la coordenada a lo ancho del tabique."""
    r = g / 2
    pts = [(centro - r, z0), (centro + r, z0)]
    zc = max(z0 + 1.0, z1 - r)
    for k in range(9):
        ang = math.pi * k / 8
        pts.append((centro + r * math.cos(ang), zc + r * math.sin(ang)))
    pts.append((centro - r, z0 + 0.01))
    pts = pts[:-1]
    return [a_3d(u, z) for u, z in pts]


def _recortar(poly, x_min, x_max):
    """Polígono convexo recortado a la franja x_min ≤ x ≤ x_max."""
    for lim, signo in ((x_min, 1), (x_max, -1)):
        sale = []
        for i, a in enumerate(poly):
            b = poly[(i + 1) % len(poly)]
            da, db = signo * (a[0] - lim), signo * (b[0] - lim)
            if da >= 0:
                sale.append(a)
            if da * db < 0:
                t = da / (da - db)
                sale.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        poly = sale
    # Sin puntos repetidos ni alineados: el triangulador por oreja se atora
    # con los tramos rectos del contorno.
    limpio = []
    for i, q in enumerate(poly):
        a, b = poly[i - 1], poly[(i + 1) % len(poly)]
        cruz = (q[0] - a[0]) * (b[1] - q[1]) - (q[1] - a[1]) * (b[0] - q[0])
        if abs(cruz) > 1e-6 and math.dist(q, a) > 1e-6:
            limpio.append(q)
    return limpio


def divisores(p):
    """Dos tabiques a lo ancho (tres compartimentos en fila) con la cima
    siguiendo el borde, y el piso de cada compartimento subido. Los pisos
    son losas que se meten media pared: el laminador las une al casco y las
    llena de relleno ligero, no de sólido."""
    g, v = p["divisor"], p["valle"]
    z0 = p["piso"] - 0.2
    medio_y = p["fondo"] / 2 - v / 2           # se meten media pared

    def cima(x):
        return borde(p, x) - p["baja_divisor"]

    piezas = []
    x_int = -p["ancho"] / 2 + v
    xs = [x_int + p["hueco_1"] + g / 2,
          x_int + p["hueco_1"] + g + p["hueco_2"] + g / 2]
    for xc in xs:
        secs = [_seccion(xc, g, z0, cima(xc), lambda u, z, y=y: (u, y, z))
                for y in (-medio_y, medio_y)]
        piezas.append(_barrido(secs))

    c = Contorno(p["ancho"], p["fondo"], p["redondeo"])
    medio = []
    for k in range(240):
        x, y, nx, ny = c.punto(k * c.perimetro / 240)
        medio.append((x - nx * v / 2, y - ny * v / 2))
    franjas = [(-p["ancho"], xs[0]), (xs[0], xs[1]), (xs[1], p["ancho"])]
    for (xa, xb), clave in zip(franjas, ("alza_1", "alza_2", "alza_3")):
        if p[clave] <= 0:
            continue
        losa = M.placa(M.orientar(_recortar(medio, xa, xb)), [], z0,
                       p["piso"] + p[clave])
        assert losa is not None, "no se pudo triangular el piso " + clave
        piezas.append(losa)
    anchos = (p["hueco_1"], p["hueco_2"], -x_int - (xs[1] + g / 2))
    alzas = (p["alza_1"], p["alza_2"], p["alza_3"])
    huecos = [(a, p["fondo"] - 2 * v, cima(x) + p["baja_divisor"] - p["piso"] - h)
              for a, h, x in zip(anchos, alzas,
                                 (x_int + anchos[0] / 2,
                                  (xs[0] + xs[1]) / 2, xs[1] + anchos[2] / 2))]
    return piezas, huecos


# ── Salida ────────────────────────────────────────────────────────────────

PLATO = 256.0
COPIAS = 3               # 3 × 75 de fondo caben a lo ancho del plato

# Perfil rápido de la P2S con Bambu PLA Basic, tomado del Oleaje M: una vuelta
# Arachne de hilo 0.62, que en el valle de dos hilos se pisa y sale maciza.
# El Oleaje M lleva relleno 0 %; aquí los pisos subidos son losas de hasta
# 20 mm, que al 0 % quedarían huecas con el techo colgando: 10 % y 4 capas.
AJUSTES_P2S = (Path.home() / "Desktop" / "own design 3d" / "Pruebas de productos"
               / "Portacubiertos_Oleaje_M.3mf")
LAMINADO = {"wall_loops": "1", "wall_generator": "arachne",
            "outer_wall_line_width": "0.62", "inner_wall_line_width": "0.62",
            "filter_out_gap_fill": "0", "resolution": "0.05",
            "infill_combination": "1", "sparse_infill_density": "10%",
            "top_shell_layers": "4"}


def embeber_ajustes(ruta, ajustes):
    """project_settings.config de `ajustes` con LAMINADO encima, declarado en
    different_settings_to_system, y el metadato Application: sin él Bambu
    Studio ignora los ajustes y lamina con los genéricos."""
    with zipfile.ZipFile(ajustes) as z:
        cfg = json.loads(z.read("Metadata/project_settings.config"))
    cfg.update(LAMINADO)
    dif = cfg.get("different_settings_to_system") or ["", "", ""]
    dif[0] = ";".join(sorted(set(filter(None, dif[0].split(";"))) | set(LAMINADO)))
    cfg["different_settings_to_system"] = dif
    with zipfile.ZipFile(ruta) as z:
        todo = {n: z.read(n) for n in z.namelist()}
    todo["Metadata/project_settings.config"] = json.dumps(cfg, indent=4).encode()
    modelo = todo["3D/3dmodel.model"].decode("utf-8")
    modelo = modelo.replace(
        '<metadata name="Title">',
        '<metadata name="Application">BambuStudio-02.07.01.62</metadata>\n'
        '<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        '<metadata name="Title">', 1)
    todo["3D/3dmodel.model"] = modelo.encode("utf-8")
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in todo.items():
            z.writestr(n, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=".")
    ap.add_argument("--nombre", default="Portacontroles_Tejido")
    ap.add_argument("--3mf", dest="tres_mf", action="store_true",
                    help="también el .3mf (después del precheck)")
    for k, val in P.items():
        ap.add_argument("--" + k.replace("_", "-"), dest=k,
                        type=type(val), default=None)
    a = ap.parse_args()
    p = dict(P)
    for k in p:
        if getattr(a, k) is not None:
            p[k] = getattr(a, k)

    cuerpo, costillas = casco(p)
    tabiques, huecos = divisores(p)
    pieza = M.Malla()
    pieza.unir(cuerpo)
    for t in tabiques:
        pieza.unir(t)

    carpeta = Path(a.salida).expanduser()
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / (a.nombre + ".3mf")
    png = render.render(pieza.v, pieza.t, tam=512, suavizado=2,
                        direccion=render.vector_vista(25, 22),
                        ruta=ruta.with_suffix(".png"))
    (x0, y0, _), (x1, y1, z1) = pieza.caja()
    piezas = [("cuerpo", pieza, 0.0, 0.0)]
    exportar.guardar_stl(piezas, ruta.with_suffix(".stl"), a.nombre)
    if a.tres_mf:
        # Copias en fila a lo ancho del plato, separadas 7 mm.
        fondo = y1 - y0
        paso = fondo + 7.0
        plato = [("pieza %d" % (i + 1), pieza, PLATO / 2,
                  PLATO / 2 + (i - (COPIAS - 1) / 2) * paso)
                 for i in range(COPIAS)]
        exportar.guardar_3mf(plato, ruta, a.nombre, miniatura=png,
                             notas="%s · portacontroles · %d por plato"
                             % (a.nombre, COPIAS),
                             parametros=dict(p, diseno="portacontroles_tejido"))
        if AJUSTES_P2S.exists():
            embeber_ajustes(ruta, AJUSTES_P2S)
        print(ruta)
    vol = abs(cuerpo.volumen()) + sum(abs(t.volumen()) for t in tabiques)
    print(ruta.with_suffix(".stl"))
    print("  %.1f × %.1f × %.1f mm, %d costillas, alto %.0f → %.0f mm"
          % (x1 - x0, y1 - y0, z1, costillas, p["alto"], p["alto_bajo"]))
    for i, h in enumerate(huecos, 1):
        print("  Compartimento %d: %.1f × %.1f mm, %.0f mm de hondo al centro" % ((i,) + h))
    print("  ≈ %.0f g de malla maciza · aristas sueltas del casco: %d"
          % (vol / 1000 * DENSIDAD, cuerpo.aristas_sueltas()))


if __name__ == "__main__":
    main()
