#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dispensador de bolsas para popó de perro con maceta, pared de punto tejido.

Sale de una foto de referencia (10-23): un portacontroles de esquinas
redondas con la pared de estría vertical fina, donde por bandas onduladas la
estría se vuelve una cuadrícula de bolitas, como tejido. El mecanismo es el
del «Dog poop bags roll dispenser planter» (Prints Charming) que se tomó de
ejemplo: medidas del rollo y de la salida tomadas de su malla.

    python3 dispensador_bolsas.py --salida /ruta              # STL + PNG
    python3 dispensador_bolsas.py --salida /ruta --3mf        # además el .3mf

Por dentro es un zigzag, como los dispensadores de latas:
  · adelante, el tubo: los rollos (acostados) se cargan por arriba y una
    tapa de tapón lo cierra. Caen a una repisa que baja hacia atrás.
  · al final de la repisa caen al fondo, al piso, que baja hacia la ventana
    del frente: ruedan solos a la salida, donde una charola de labio
    cóncavo los detiene y de ahí se jala la bolsa. Al sacar un rollo vacío
    baja el siguiente.
  · atrás arriba, la maceta: una charola aparte, poco honda (semillas),
    colgada de la orilla por una ceja. Su frente hace de pared con el tubo.
    Sin agujeros: el agua no cae a las bolsas.

La repisa es pieza aparte: impresa en el cuerpo volaría en el aire. Se
imprime plana y se apoya en dos rieles a 45° pegados a los costados; PLA
sobre PLA no resbala a 8°. Se mete por arriba con la maceta fuera.

Rollo de referencia ~33 mm × 60 mm (el del ejemplo). Caben ~6: 1 en la
charola de salida, 2 en el piso, 1 encima del de atrás, 1 en la repisa y 1
en el tubo. Las esquinas son chicas para que la ventana quepa en el tramo
recto del frente. Cuerpo 86 × 125 (con charola) × 104, con la tapa 106:
cabe en la caja de 20 × 16 × 11 cm.

La pared copia la textura por dentro (grueso parejo): el laminador la saca en
dos hilos con Arachne, como el portacepillos rápido.
"""

import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nucleo import exportar, malla as M, render   # noqa: E402

DENSIDAD = 1.24          # g/cm³, PLA

P = {
    "ancho": 86.0,           # x
    "fondo": 85.0,           # y
    "esquina": 10.0,         # radio de las esquinas en planta
    "alto": 104.0,
    "pared": 1.3,            # 2 hilos de 0.65 (ver LAMINADO)
    "piso": 1.6,
    # Dispensador (interior). El ejemplo: tubo de 64 × 35 para rollos de
    # ~33 mm × 60 mm; aquí todo el ancho y 40 de fondo.
    "tubo_ancho": 66.0,      # ancho de la ventana
    "tubo_fondo": 40.0,
    "caida": 8.0,            # grados del piso y de la repisa
    "pasillo": 38.0,         # alto libre para que pase el rollo (33 + holgura)
    "riel": 4.0,             # lo que sale el riel de la pared
    "repisa": 2.0,           # grueso de la repisa
    "ventana": 44.0,         # alto de la ventana: más que el rollo, que pase
    "charola": 40.0,         # lo que sale la charola al frente
    "labio": 18.0,           # alto del labio de la charola
    # Maceta (charola colgada)
    "tierra": 20.0,          # hondo por dentro
    "ceja": 2.0,             # grueso de la ceja que se apoya en la orilla
    # Tapa del dispensador
    "tapa": 2.0,             # grueso de la tapa
    "tapon": 6.0,            # lo que entra el tapón
    "holgura": 0.3,          # del tapón contra la pared, de cada lado
    # Textura
    "estria_paso": 3.0,      # mm entre estrías verticales (se ajusta al perímetro)
    "estria": 0.8,           # lo que sobresale la estría
    "bolita_paso": 3.0,      # mm entre filas de bolitas
    "banda": 34.0,           # mm entre bandas de tejido, en vertical
    "ola": 14.0,             # cuánto sube y baja la banda alrededor
    "olas": 3,               # olas por vuelta
    "liso_base": 7.0,        # abajo solo estría
    "liso_borde": 9.0,       # arriba solo estría
    "paso": 0.5,             # resolución de la malla
}


def suave(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


# ── Planta ────────────────────────────────────────────────────────────────

def perimetro(p):
    W, D, R = p["ancho"] / 2, p["fondo"] / 2, p["esquina"]
    tramos = [2 * (W - R), math.pi * R / 2, 2 * (D - R), math.pi * R / 2,
              2 * (W - R), math.pi * R / 2, 2 * (D - R), math.pi * R / 2]
    return tramos, sum(tramos)


def en_planta(p, s):
    """Punto y normal hacia afuera a la longitud s, antihorario, empezando en
    la esquina delantera izquierda del tramo recto del frente."""
    W, D, R = p["ancho"] / 2, p["fondo"] / 2, p["esquina"]
    tramos, total = perimetro(p)
    s %= total
    # (inicio, dirección) de los rectos y centros de las esquinas
    rectos = [((-W + R, -D), (1, 0), (0, -1)), ((W, -D + R), (0, 1), (1, 0)),
              ((W - R, D), (-1, 0), (0, 1)), ((-W, D - R), (0, -1), (-1, 0))]
    centros = [(W - R, -D + R, -math.pi / 2), (W - R, D - R, 0.0),
               (-W + R, D - R, math.pi / 2), (-W + R, -D + R, math.pi)]
    for i, largo in enumerate(tramos):
        if s <= largo or i == len(tramos) - 1:
            if i % 2 == 0:
                (x0, y0), (tx, ty), n = rectos[i // 2]
                return (x0 + tx * s, y0 + ty * s), n
            cx, cy, a0 = centros[i // 2]
            a = a0 + s / R
            return (cx + R * math.cos(a), cy + R * math.sin(a)), (math.cos(a), math.sin(a))
        s -= largo



# ── Textura ───────────────────────────────────────────────────────────────

def relieve(p, s, z, z_top, total):
    n_estrias = max(1, round(total / p["estria_paso"]))
    estria = 0.5 - 0.5 * math.cos(2 * math.pi * n_estrias * s / total)
    bolita = 0.5 - 0.5 * math.cos(2 * math.pi * z / p["bolita_paso"])
    ola = p["ola"] * math.sin(2 * math.pi * p["olas"] * s / total)
    banda = math.sin(2 * math.pi * (z - 18.0 + ola) / p["banda"])
    tejido = suave(-0.15, 0.55, banda)
    tejido *= suave(p["liso_base"], p["liso_base"] + 5, z)
    tejido *= 1 - suave(z_top - p["liso_borde"] - 5, z_top - p["liso_borde"], z)
    return p["estria"] * estria * (1 - tejido * (1 - bolita))


# ── Pared ─────────────────────────────────────────────────────────────────

def tubo_x(p):
    """Canto izquierdo de la ventana, centrada."""
    return -p["tubo_ancho"] / 2


def y_division(p):
    """Centro de la pared de enfrente de la maceta (el fondo del tubo)."""
    return -p["fondo"] / 2 + p["pared"] + p["tubo_fondo"] + p["pared"] / 2


def mitad_frente(p, desfase, y_atras, n=12):
    """Contorno de la mitad delantera: las dos esquinas del frente corridas
    `desfase` hacia afuera (+) o adentro (−), cerrado recto en y_atras."""
    W, D, R = p["ancho"] / 2, p["fondo"] / 2, p["esquina"]
    r = R + desfase
    pts = []
    for cx, a0 in ((-W + R, math.pi), (W - R, -math.pi / 2)):
        pts += [(cx + r * math.cos(a0 + math.pi / 2 * i / n),
                 -D + R + r * math.sin(a0 + math.pi / 2 * i / n)) for i in range(n + 1)]
    pts += [(W + desfase, y_atras), (-W - desfase, y_atras)]
    return pts


def mitad_atras(p, desfase, y_frente, n=12):
    """La mitad delantera reflejada: esquinas de atrás, cerrada recto en
    y_frente."""
    return [(x, -y) for x, y in mitad_frente(p, desfase, -y_frente, n)]


def contorno(p, desfase, n=16):
    """El contorno completo de la planta corrido `desfase`."""
    W, D, R = p["ancho"] / 2, p["fondo"] / 2, p["esquina"]
    r = R + desfase
    pts = []
    for cx, cy, a0 in ((W - R, -D + R, -math.pi / 2), (W - R, D - R, 0.0),
                       (-W + R, D - R, math.pi / 2), (-W + R, -D + R, math.pi)):
        pts += [(cx + r * math.cos(a0 + math.pi / 2 * i / n),
                 cy + r * math.sin(a0 + math.pi / 2 * i / n)) for i in range(n + 1)]
    return pts


def pared(p):
    tramos, total = perimetro(p)
    t = p["pared"]
    # Columnas a paso fijo más los dos cantos de la ventana, exactos.
    s_ini = -p["ancho"] / 2 + p["esquina"]
    sa = tubo_x(p) - s_ini
    sb = sa + p["tubo_ancho"]
    assert sa >= 0 and sb <= p["ancho"] - 2 * p["esquina"], \
        "la ventana no cabe en el tramo recto del frente"
    n = int(round(total / p["paso"]))
    cols = sorted(set([total * i / n for i in range(n)] + [sa, sb]))
    ka, kb = cols.index(sa), cols.index(sb)
    nk = len(cols)
    # Filas a paso fijo más el piso y el techo de la ventana, exactos. La
    # ventana arranca a ras del piso para que el rollo ruede a la charola.
    nz = int(round(p["alto"] / p["paso"]))
    zf = sorted(set([p["alto"] * i / nz for i in range(nz + 1)]
                    + [p["piso"], p["ventana"]]))
    ja, jb = zf.index(p["piso"]), zf.index(p["ventana"])

    m = M.Malla()
    fuera, dentro = [], []
    planta = [en_planta(p, s) for s in cols]
    for z in zf:
        fo, de = [], []
        for k, s in enumerate(cols):
            (x, y), (nx, ny) = planta[k]
            d = relieve(p, s, z, p["alto"], total)
            fo.append(m.punto(x + nx * d, y + ny * d, z))
            de.append(m.punto(x + nx * (d - t), y + ny * (d - t), z))
        fuera.append(fo)
        dentro.append(de)

    hueco = lambda j, k: ja <= j < jb and ka <= k < kb   # noqa: E731
    nj = len(fuera)
    for j in range(nj - 1):
        for k in range(nk):
            if hueco(j, k):
                continue
            k2 = (k + 1) % nk
            O, I = fuera, dentro
            m.quad(O[j][k], O[j][k2], O[j + 1][k2], O[j + 1][k])
            m.quad(I[j][k], I[j + 1][k], I[j + 1][k2], I[j][k2])
    O, I = fuera, dentro
    for k in range(nk):
        k2 = (k + 1) % nk
        m.quad(O[-1][k], O[-1][k2], I[-1][k2], I[-1][k])      # borde
        m.quad(O[0][k], I[0][k], I[0][k2], O[0][k2])          # base
    for j in range(ja, jb):                                   # costados ventana
        m.quad(O[j][ka], I[j][ka], I[j + 1][ka], O[j + 1][ka])
        m.quad(O[j][kb], O[j + 1][kb], I[j + 1][kb], I[j][kb])
    for k in range(ka, kb):                                   # piso y techo ventana
        m.quad(O[ja][k], O[ja][k + 1], I[ja][k + 1], I[ja][k])
        m.quad(O[jb][k], I[jb][k], I[jb][k + 1], O[jb][k + 1])
    return m


def pieza(p):
    m = pared(p)
    # Piso en bajada, encimado 0.4 en la pared, y la charola de salida.
    m.unir(rampa(p))
    m.unir(rieles(p))
    m.unir(charola(p))
    return m


def caja(x0, y0, z0, x1, y1, z1):
    return M.placa([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], [], z0, z1)


def z_piso(p, y):
    """Cara de arriba del piso: a ras en la ventana, sube hacia atrás."""
    y0 = -p["fondo"] / 2 + p["pared"]
    return p["piso"] + math.tan(math.radians(p["caida"])) * max(0.0, y - y0)


def y_repisa(p):
    """Del frente (por dentro) a donde termina la repisa: bajo el frente de
    la maceta, así queda el fondo libre para que caiga el rollo."""
    return -p["fondo"] / 2 + p["pared"], y_division(p) - p["pared"] / 2


def z_repisa(p, y):
    """Cara de abajo de la repisa: deja `pasillo` sobre el piso donde menos
    hay (al final) y sube hacia el frente con la misma caída."""
    _, y1 = y_repisa(p)
    return (z_piso(p, y1) + p["pasillo"]
            + math.tan(math.radians(p["caida"])) * (y1 - y))


def rampa(p):
    """Piso en bajada hacia la ventana. Una placa del contorno (encimada 0.4
    en la pared) con la cara de arriba inclinada; todos sus puntos caen en
    el plano, así sigue plana."""
    t = p["pared"]
    m = M.placa(M.orientar(contorno(p, -(t - 0.4))), [], 0.0, p["piso"])
    n = len(m.v) // 2
    m.v = m.v[:n] + [(x, y, z_piso(p, y)) for x, y, _ in m.v[n:]]
    return m


def rieles(p):
    """Dos rieles en los costados donde se apoya la repisa: triángulo de
    `riel` mm con la cara de abajo a 45°, inclinado con la repisa. Solo en el
    tramo recto de los costados (en las esquinas se saldría por la pared)."""
    W, D, R, t, r = p["ancho"] / 2, p["fondo"] / 2, p["esquina"], p["pared"], p["riel"]
    ya, yb = -D + R, y_repisa(p)[1]
    m = M.Malla()
    for lado in (-1, 1):
        xw = lado * (W - t + 0.7)              # encimado en la pared
        xr = lado * (W - t - r)
        tri = [(xw, 0.0), (xr, 0.0), (xw, -(r + 0.7))]
        riel = M.placa(M.orientar(tri), [], ya, yb)
        # (u, v, w) → (x = u, y = w, z = v + cara de abajo de la repisa)
        riel.v = [(u, w, v + z_repisa(p, w)) for u, v, w in riel.v]
        m.unir(riel.normalizar())
    return m


def repisa(p):
    """La repisa como se imprime: plana. Ancho de pared a pared menos 0.4
    por lado, esquinas del frente redondas como las de dentro."""
    t = p["pared"]
    return M.placa(M.orientar(mitad_frente(p, -(t + 0.4), y_repisa(p)[1])), [],
                   0.0, p["repisa"])


def repisa_puesta(p):
    m = repisa(p)
    m.v = [(x, y, z + z_repisa(p, y) + 0.05) for x, y, z in m.v]
    return m


def maceta(p):
    """Charola de la maceta, como se imprime (boca arriba). Cuelga de una
    ceja que se apoya en la orilla de los costados y de atrás; la ceja vuela
    2 mm sobre la pared, lo que un labio aguanta sin soporte. Pared lisa:
    no se ve, queda dentro."""
    t, c = p["pared"], 0.4                     # holgura contra la pared
    yf = y_division(p) - t / 2                 # cara de enfrente
    alto = p["piso"] + p["tierra"]
    fuera = M.orientar(mitad_atras(p, -(t + c), yf))
    dentro = M.orientar(mitad_atras(p, -(2 * t + c), yf + t))
    m = M.placa(fuera, [], 0.0, p["piso"])
    m.unir(M.placa(fuera, [dentro], p["piso"] - 0.4, alto + p["ceja"]))
    m.unir(M.placa(M.orientar(mitad_atras(p, 0.0, yf)), [dentro], alto, alto + p["ceja"]))
    return m


def tapa(p):
    """Tapa del dispensador, como se imprime: la cara de arriba en la cama y
    el tapón hacia arriba (sin soportes). El tapón es un aro de una pared que
    entra justo en el tubo; al frente una pestaña para levantarla."""
    t, h = p["pared"], p["holgura"]
    yd = y_division(p)
    exterior = mitad_frente(p, 0.8, yd - t / 2 - h)
    D = p["fondo"] / 2
    # Pestaña de 18 × 7 mm al centro del frente, entre las dos esquinas.
    frente = [(x, -D - 0.8 - 7.0 * math.sin(math.pi * (x + 9) / 18))
              for x in [-9 + 18 * i / 12 for i in range(13)]]
    ext = M.orientar(exterior[:13] + frente + exterior[13:])
    m = M.placa(ext, [], 0.0, p["tapa"])
    fuera = M.orientar(mitad_frente(p, -(t + h), yd - t / 2 - h))
    dentro = M.orientar(mitad_frente(p, -(2 * t + h), yd - t / 2 - h - t))
    m.unir(M.placa(fuera, [dentro], p["tapa"] - 0.4, p["tapa"] + p["tapon"]))
    return m


def charola(p):
    """Charola al frente de la ventana: piso a ras del del tubo y un labio
    cóncavo, como cuchara. Por fuera el labio es recto (sin voladizo); por
    dentro baja en cuarto de círculo hasta el piso, así el rollo se detiene
    sin trabarse. Perfil en (y, z), extruido a lo ancho del tubo."""
    D, t = p["fondo"] / 2, p["pared"]
    yf, h = -D - p["charola"], p["labio"]
    r = h - p["piso"]
    canto = 2.4
    perfil = [(-D + 0.8, 0.0), (-D + 0.8, p["piso"])]
    cy = yf + canto + r
    perfil += [(cy + r * math.cos(math.pi * 1.5 - math.pi / 2 * i / 16),
                 h + r * math.sin(math.pi * 1.5 - math.pi / 2 * i / 16))
               for i in range(17)]
    perfil += [(yf + 1.2, h + 0.6), (yf + 0.4, h), (yf, h - 1.2), (yf, 0.0)]
    a = p["tubo_ancho"] / 2 + t
    lam = M.placa(M.orientar(perfil), [], -a, a)
    # (u, v, w) de la placa → (x = w, y = u, z = v)
    lam.v = [(w, u, v) for u, v, w in lam.v]
    return lam.normalizar()


# ── Laminado ──────────────────────────────────────────────────────────────

# Perfil del P2S con Bambu PLA Basic (0.20 Standard), tomado del florero, como
# el portacubiertos trenzado. El florero trae relleno 0 % y 3 capas de techo:
# se regresan a los de fábrica (la rampa y la charola los necesitan).
#
# La pared copia la textura por dentro y mide 1.3: una vuelta con Arachne son
# dos hilos de 0.65 que la llenan justa, como el portacepillos rápido. Con
# pared 1.6 y 2 vueltas (4 hilos de 0.42) el plato salía en 12 h 20: la
# textura partía la pared en trazos sueltos (4.6 h solo de recorridos).
AJUSTES_P2S = (Path.home() / "Desktop" / "own design 3d"
               / "General_Vases_print_profile(5).3mf")
LAMINADO = {"sparse_infill_density": "15%", "skeleton_infill_density": "15%",
            "skin_infill_density": "15%", "top_shell_layers": "5",
            "wall_loops": "1", "wall_generator": "arachne",
            "outer_wall_line_width": "0.65", "inner_wall_line_width": "0.65",
            "filter_out_gap_fill": "2", "retraction_minimum_travel": "5",
            "resolution": "0.05", "infill_combination": "1"}
DE_FABRICA = {"sparse_infill_density", "skeleton_infill_density",
              "skin_infill_density", "top_shell_layers"}


def modelo_settings(modelo):
    """Metadata/model_settings.config: un bloque por objeto, ids uno a uno."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', "<config>"]
    objetos = re.findall(r'<object id="(\d+)" type="model" name="([^"]*)"', modelo)
    for oid, nom in objetos:
        xml += ['  <object id="%s">' % oid,
                '    <metadata key="name" value="%s"/>' % nom,
                '    <metadata key="extruder" value="1"/>',
                '    <part id="1" subtype="normal_part">',
                '      <metadata key="name" value="%s"/>' % nom,
                "    </part>", "  </object>"]
    xml += ["  <plate>", '    <metadata key="plater_id" value="1"/>']
    for oid, _ in objetos:
        xml += ["    <model_instance>",
                '      <metadata key="object_id" value="%s"/>' % oid,
                '      <metadata key="instance_id" value="0"/>',
                "    </model_instance>"]
    xml += ["  </plate>", "</config>"]
    return "\n".join(xml).encode("utf-8")


def embeber_ajustes(ruta, ajustes):
    """Copia project_settings.config de `ajustes` con LAMINADO encima y
    declara el .3mf de Bambu Studio: sin el metadato Application el laminador
    ignora los ajustes y usa los genéricos."""
    with zipfile.ZipFile(ajustes) as z:
        cfg = json.loads(z.read("Metadata/project_settings.config"))
    cfg.update(LAMINADO)
    dif = cfg.get("different_settings_to_system") or [""]
    cambios = set(filter(None, dif[0].split(";"))) | set(LAMINADO)
    dif[0] = ";".join(sorted(cambios - DE_FABRICA))
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
    todo["Metadata/model_settings.config"] = modelo_settings(modelo)
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in todo.items():
            z.writestr(n, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=".")
    ap.add_argument("--nombre", default="Dispensador_Bolsas_Maceta")
    ap.add_argument("--3mf", dest="tmf", action="store_true")
    ap.add_argument("--ajustes", default=str(AJUSTES_P2S),
                    help="otro .3mf del que copiar los ajustes de laminado ('' = ninguno)")
    for k in P:
        ap.add_argument("--" + k.replace("_", "-"), dest=k, type=float, default=None)
    a = ap.parse_args()
    p = dict(P)
    for k in P:
        if getattr(a, k) is not None:
            p[k] = getattr(a, k)
    p["olas"] = int(p["olas"])

    m, tp, mc, rp = pieza(p), tapa(p), maceta(p), repisa(p)
    # Lo que sube el rollo al dejar la repisa no debe topar con la maceta.
    holgura = (p["alto"] - p["piso"] - p["tierra"]) - (
        z_repisa(p, y_repisa(p)[1]) + p["repisa"] + 33.0)
    if holgura < 1.0:
        print("  OJO: el rollo topa con la maceta al bajar de la repisa (%.1f mm)" % holgura)
    # La tapa en su lugar, volteada, para ver el juego armado.
    z_tapa = p["alto"] + p["tapa"]
    tapa_puesta = M.Malla()
    tapa_puesta.v = [(x, y, z_tapa - z) for x, y, z in tp.v]
    tapa_puesta.t = [(i, k, j) for i, j, k in tp.t]
    z_maceta = p["alto"] - p["piso"] - p["tierra"]
    juego = (M.Malla().unir(m).unir(tapa_puesta).unir(mc.trasladada(0, 0, z_maceta))
             .unir(repisa_puesta(p)))
    carpeta = Path(a.salida).expanduser()
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / (a.nombre + ".3mf")
    png = render.render(juego.v, juego.t, tam=512, suavizado=2,
                        direccion=render.vector_vista(25, 22),
                        ruta=ruta.with_suffix(".png"))
    def en(malla, cx, cy):
        (x0, y0, _), (x1, y1, _) = malla.caja()
        return malla, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2

    piezas = [("dispensador",) + en(m, 60.0, 128.0),
              ("tapa",) + en(tp, 160.0, 215.0),
              ("maceta",) + en(mc, 160.0, 40.0),
              ("repisa",) + en(rp, 205.0, 128.0)]
    exportar.guardar_stl(piezas, ruta.with_suffix(".stl"), a.nombre)
    exportar.guardar_stl([("juego", juego, 0, 0)],
                         carpeta / (a.nombre + "_armado.stl"), a.nombre)
    if a.tmf:
        exportar.guardar_3mf(piezas, ruta, a.nombre, miniatura=png,
                             notas="%s · dispensador + tapa + maceta + repisa" % a.nombre,
                             parametros=dict(p, diseno="dispensador_bolsas"))
        if a.ajustes and Path(a.ajustes).exists():
            embeber_ajustes(ruta, a.ajustes)
    (x0, y0, z0), (x1, y1, z1) = m.caja()
    print(ruta.with_suffix(".stl"))
    print("  %.1f × %.1f × %.1f mm, %d triángulos, malla maciza ≈ %.1f g"
          % (x1 - x0, y1 - y0, z1 - z0, len(m.t),
             abs(m.volumen()) / 1000 * DENSIDAD))
    print("  Tapa ≈ %.1f g, maceta ≈ %.1f g, repisa ≈ %.1f g" % tuple(
        abs(x.volumen()) / 1000 * DENSIDAD for x in (tp, mc, rp)))
    print("  Repisa: abajo %.1f → %.1f mm, piso %.1f → %.1f mm, holgura con la maceta %.1f mm"
          % (z_repisa(p, y_repisa(p)[0]), z_repisa(p, y_repisa(p)[1]),
             z_piso(p, -p["fondo"] / 2), z_piso(p, p["fondo"] / 2), holgura))
    print("  Aristas sueltas de la pared: %d" % pared(p).aristas_sueltas())


if __name__ == "__main__":
    main()
