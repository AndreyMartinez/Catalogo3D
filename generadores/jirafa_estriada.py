#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jirafa estriada: la figura de bolo con estrías verticales del reno de
referencia (foto de 2026-10-18: tres renos verde salvia, beige y rojo), pero
con cuello largo, cabeza con hocico, osiconos y orejas de jirafa. Solo
Python 3 estándar.

El cuerpo es UN tubo estriado barrido a lo largo de una columna: sube recto
como bolo —panza abajo, cintura larga que hace de cuello— y arriba se dobla
hacia el frente para volverse cabeza y hocico. Así las estrías corren sin
corte del pie a la punta de la nariz; un hocico pegado aparte se leía como
concha (v1, rechazado). Las estrías son crestas redondas con surco en V y se
apagan donde el radio se achica. Osiconos y orejas son piezas aparte que se
meten en la cabeza; el laminador las une.

    python3 jirafa_estriada.py --salida ~/Desktop --render
"""

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
# El núcleo del motor puede vivir solo en la copia principal sin versionar.
for ruta in (AQUI, Path.home() / "Desktop/codigo/Catalogo3D/generadores"):
    if (ruta / "nucleo").is_dir():
        sys.path.insert(0, str(ruta))
        break

from nucleo import exportar, malla as M, render   # noqa: E402

# Los ajustes de laminado se copian de la jirafa que ya se imprime (P2S, capa
# 0.12, soporte de árbol apoyado también en el modelo, PLA Basic).
AJUSTES = Path.home() / "Desktop" / "own design 3d" / "reduced_color.3mf"
PLATO = 256.0

# Colores medidos a ojo de la foto del reno.
COLORES = {
    "salvia": (128, 146, 124),
    "beige": (226, 206, 184),
    "rojo": (156, 52, 46),
}

JIRAFA = {
    # Tramo recto: (z, radio) en mm, de la base hasta donde empieza la curva.
    # v5 (dibujo de jirafa de frente): ni panza de bolo (v3) ni triángulo
    # (v4). El cuello baja delgado, se abre en curva cóncava hasta unos
    # hombros redondos y de ahí los costados bajan casi rectos al pie.
    # Con el hombro corto y los costados rectos se leía como botella de vino:
    # el hombro cae largo y suave, y abajo los costados cierran un poco.
    # v11 (foto del florero-jirafa café): panza de jarrón abajo, más ancha
    # que el pie, que se cierra en curva cóncava hasta un cuello largo casi
    # parejo. v10: (0, 24.5) (3, 26.5) (14, 27.2) (28, 28.2) (36, 28.4)
    # (46, 26.8) (56, 23.2) (66, 19.3) (76, 16.2) (88, 13.9) (104, 12.1)
    # (122, 11.0), nuca 140 / 13.5.
    "perfil": [(0, 23), (3, 25.5), (12, 28.5), (24, 30.5), (36, 31),
               (48, 29.5), (60, 25.5), (72, 20.5), (84, 16.5), (96, 14),
               (110, 12.8), (125, 12.2)],
    # Cómo se une la cabeza. "curva" (v2-v7): el cuello se dobla en arco y se
    # vuelve cabeza. "recta" (v9, foto de jirafa de perfil): el cuello sube
    # recto y cierra redondo en la nuca; la cabeza es una cuña estriada recta
    # que sale del cráneo hacia adelante y abajo. Donde se cruzan queda la
    # esquina de la garganta, en vez de la U que dejaba el arco.
    "cabeza_forma": "recta",
    "nuca_z": 143.0,          # centro del cráneo
    "nuca_r": 12.0,           # radio del cuello al cerrar en la nuca
    # v11: cabeza de huevo lisa como la foto: nuca redonda completa, cráneo
    # ancho que cierra hacia una trompa redonda, más agachada.
    # v10: baja 30, largo 46, r 15, alto 1.25, cuña 1.0, nariz 7.5 chata 5.
    "cabeza_baja": 52.0,      # grados bajo la horizontal
    "cabeza_largo": 46.0,     # del cráneo a la punta de la nariz
    "cabeza_r": 17.0,         # radio de la cuña en el cráneo
    "cabeza_alto": 1.1,       # la cuña es más alta que ancha, como la quijada
    "cabeza_cuna": 0.35,      # como `cuna`, para la cabeza recta: 1 = frente del todo recta
    "cabeza_nuca": 1.0,       # largo de la nuca redonda, en radios (v10: 0.6)
    "cabeza_afina": 1.4,      # >1 guarda el cráneo ancho antes de afinar (v10: 1)
    "cabeza_lisa": True,      # sin estrías en la cabeza (v10: solo la frente lisa)
    # v10: la frente (lo que se ve de frente, entre las orejas hasta la nariz)
    # va lisa; las estrías quedan en costados y quijada. Es el ángulo de la
    # sección, en seno, donde empieza a alisar y donde ya es lisa del todo.
    "frente_lisa": (0.15, 0.6),
    "nariz_r": 11.0,          # radio de la trompa antes de cerrar
    "nariz_chata": 11.0,      # largo del cierre de la nariz
    "nariz_exp": 2.0,         # 2 redonda; 2.5 chata con canto redondo (v10)
    # Curva del cuello a la cabeza (solo "curva"): arco de este radio y este
    # ángulo. 90° deja el hocico horizontal; más, lo baja.
    "curva_radio": 19.0,
    "curva_grados": 135.0,
    "craneo_r": 15.5,         # radio máximo de la cabeza, a media curva
    "hocico_largo": 18.0,     # tramo recto después de la curva
    "hocico_r": 8.0,          # radio del hocico antes de la punta
    "punta_largo": 6.0,       # la nariz se cierra redonda en este largo
    # Cabeza en cuña (v3, referencia: foto de jirafa de perfil): del cráneo a
    # la nariz el radio se afina y el centro sube, así la frente sigue recta
    # y es la quijada la que sube hacia la nariz. 1 = frente del todo recta.
    "cuna": 0.85,
    "nariz_lisa": 10.0,       # las estrías se desvanecen en este largo antes de la punta
    "ancho": 1.14,            # sección un poco más ancha que alta en la cabeza
    # v6 (dibujo de frente): la cara es un triángulo invertido, ancha arriba
    # entre las orejas y angosta en la quijada. La sección de la cabeza se
    # abre arriba y se cierra abajo en esta proporción.
    "cara_triangulo": 0.25,   # v10: 0.5
    "estrias": 26,
    # v7: el surco más hondo y más abierto para que se lea hueco entre cresta
    # y cresta (v6: 2.0 mm, forma 0.55, pleno desde r 13).
    "estria_amplitud": 4.0,   # alto de la cresta sobre el surco
    "estria_forma": 1.0,      # <1 cresta llena y surco en V; más alto, surco más abierto
    "estria_radio_pleno": 9.0,  # por debajo de este radio la estría se apaga
    # v11: osiconos más largos y delgados, punta apenas redonda (v10: 11, 3.4, 5.0)
    "osicono_largo": 15.0,
    "osicono_r": 2.6,
    "osicono_bola": 3.4,
    "osicono_abre": 12.0,     # grados hacia afuera
    "oreja_largo": 21.0,
    "oreja_ancho": 11.0,
    "oreja_grueso": 3.2,
    "oreja_sube": 28.0,       # grados sobre la horizontal
}


def catmull(puntos, z):
    """Valor interpolado en z por Catmull-Rom entre (z, valor)."""
    if z <= puntos[0][0]:
        return puntos[0][1]
    if z >= puntos[-1][0]:
        return puntos[-1][1]
    for i in range(len(puntos) - 1):
        if puntos[i][0] <= z <= puntos[i + 1][0]:
            break
    p0 = puntos[max(i - 1, 0)][1]
    p1, p2 = puntos[i][1], puntos[i + 1][1]
    p3 = puntos[min(i + 2, len(puntos) - 1)][1]
    t = (z - puntos[i][0]) / (puntos[i + 1][0] - puntos[i][0])
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                  + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


# ─── Columna: recta, curva hacia el frente (-y), hocico ────────────────────

def columna(p, s):
    """Punto, tangente y normal (en el plano y-z) a la distancia s del pie.
    La normal apunta hacia afuera de la curva: atrás/arriba en la cabeza."""
    zb = p["perfil"][-1][0]
    R, phi = p["curva_radio"], math.radians(p["curva_grados"])
    if s <= zb:
        return (0.0, s), (0.0, 1.0), (1.0, 0.0)
    if s <= zb + R * phi:
        t = (s - zb) / R
        pos = (-R + R * math.cos(t), zb + R * math.sin(t))
        return pos, (-math.sin(t), math.cos(t)), (math.cos(t), math.sin(t))
    d = s - zb - R * phi
    y0, z0 = -R + R * math.cos(phi), zb + R * math.sin(phi)
    tg = (-math.sin(phi), math.cos(phi))
    return (y0 + tg[0] * d, z0 + tg[1] * d), tg, (math.cos(phi), math.sin(phi))


def largo_total(p):
    return (p["perfil"][-1][0] + p["curva_radio"] * math.radians(p["curva_grados"])
            + p["hocico_largo"] + p["punta_largo"])


def radio(p, s):
    zb = p["perfil"][-1][0]
    arco = p["curva_radio"] * math.radians(p["curva_grados"])
    if s <= zb:
        return catmull(p["perfil"], s)
    r_cuello = p["perfil"][-1][1]
    tramos = [(zb - 12, catmull(p["perfil"], zb - 12)), (zb, r_cuello),
              (zb + arco * 0.45, p["craneo_r"]),
              (zb + arco * 0.85, p["craneo_r"] * 0.88),
              (zb + arco + p["hocico_largo"], p["hocico_r"])]
    fin = zb + arco + p["hocico_largo"]
    if s <= fin:
        return catmull(tramos, s)
    u = min(1.0, (s - fin) / p["punta_largo"])
    return p["hocico_r"] * math.sqrt(max(0.0, 1 - u * u))


def alza(p, s):
    """Cuánto sube el centro de la sección en la cabeza para hacer la cuña:
    lo que el radio pierde desde el cráneo, por `cuna`. La punta redonda
    sigue la última alza para no deformarse."""
    zb = p["perfil"][-1][0]
    s_craneo = zb + p["curva_radio"] * math.radians(p["curva_grados"]) * 0.45
    if s <= s_craneo:
        return 0.0
    fin = largo_total(p) - p["punta_largo"]
    return p["cuna"] * (p["craneo_r"] - radio(p, min(s, fin)))


def estria(p, ang, r, apaga=1.0):
    """Cresta redonda, surco en V; 0 en la cresta, negativo hacia el surco.
    Se apaga en radios chicos y donde `apaga` < 1 (la nariz)."""
    c = abs(math.cos(p["estrias"] * ang / 2)) ** p["estria_forma"]
    escala = min(1.0, (r / p["estria_radio_pleno"]) ** 1.5) * apaga
    return p["estria_amplitud"] * escala * (c - 1)


def tubo(p, secciones, punta, por_estria=10, frente_lisa=None):
    """Malla de un tubo estriado. Cada sección es (y, z, ny, nz, r, sube, h,
    apaga): centro y normal en el plano y-z, radio, cuánto sube el centro
    (cuña), cuánto es cabeza (ancho y cara en triángulo) y cuánto queda de
    estría. Cierra plano abajo y en `punta` (y, z) arriba. Con `frente_lisa`
    (seno donde empieza, seno donde ya es lisa) el lado de arriba va liso."""
    cols = p["estrias"] * por_estria
    m = M.Malla()
    anillos = []
    for py, pz, ny, nz, r, sube, h, apaga in secciones:
        k = 1 + (p["ancho"] - 1) * h
        tri = p["cara_triangulo"] * h
        fila = []
        for j in range(cols):
            a = 2 * math.pi * j / cols
            ap = apaga
            if frente_lisa:
                s0, s1 = frente_lisa
                ap *= 1 - suave((math.sin(a) - s0) / (s1 - s0))
            rr = r + estria(p, a, r, ap)
            cx = rr * k * math.cos(a) * (1 + tri * math.sin(a))
            cn = rr * math.sin(a) * (1 + (p.get("cabeza_alto", 1) - 1) * h) + sube
            fila.append(m.punto(cx, py + ny * cn, pz + nz * cn))
        anillos.append(fila)
    y0, z0, ny, nz = secciones[0][:4]
    abajo = m.punto(0, y0 + ny * secciones[0][5], z0 + nz * secciones[0][5])
    tope = m.punto(0, punta[0], punta[1])
    for j in range(cols):
        j2 = (j + 1) % cols
        m.cara(abajo, anillos[0][j2], anillos[0][j])
        for f in range(len(anillos) - 1):
            a, b = anillos[f], anillos[f + 1]
            m.quad(a[j], a[j2], b[j2], b[j])
        m.cara(anillos[-1][j], anillos[-1][j2], tope)
    return m.normalizar()


def suave(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def cuello_recto(p, paso=0.6):
    """Del pie a la nuca, recto; arriba cierra en media esfera. Las estrías
    se apagan en la coronilla para no hacer flor."""
    zb, zc, rn = p["perfil"][-1][0], p["nuca_z"], p["nuca_r"]
    tramos = p["perfil"] + [(zc, rn)]
    sec = []
    for i in range(int(zc / paso) + 1):
        z = i * paso
        sec.append((0.0, z, 1.0, 0.0, catmull(tramos, z), 0.0, 0.0, 1.0))
    for k in range(1, 40):
        t = math.pi / 2 * k / 40
        sec.append((0.0, zc + rn * math.sin(t), 1.0, 0.0, rn * math.cos(t), 0.0, 0.0,
                    1 - suave(k / 20)))
    return tubo(p, sec, (0.0, zc + rn))


def eje_cabeza(p):
    """Origen (en el cráneo), dirección y normal hacia arriba de la cuña."""
    b = math.radians(p["cabeza_baja"])
    return (2.0, p["nuca_z"]), (-math.cos(b), -math.sin(b)), (-math.sin(b), math.cos(b))


def cabeza_recta(p, paso=0.5):
    """Cuña recta: atrás cierra redonda dentro de la nuca, se afina hacia la
    nariz con la frente recta (el centro sube lo que el radio pierde) y la
    nariz cierra chata."""
    (oy, oz), (dy, dz), (ny, nz) = eje_cabeza(p)
    r0, r1 = p["cabeza_r"], p["nariz_r"]
    L, cierre = p["cabeza_largo"], p["nariz_chata"]
    recto = L - cierre
    sec = []
    # nuca de la cuña: cuarto de esfera hacia atrás
    for k in range(0, 20):
        t = math.pi / 2 * (1 - k / 20)
        d = -r0 * p.get("cabeza_nuca", 0.6) * math.sin(t)
        sec.append((d, r0 * math.cos(t)))
    # `cabeza_afina` 1 (v9-v10): se afina parejo; más alto (v11, cabeza de
    # huevo de la foto del florero-jirafa) guarda el cráneo ancho y cierra
    # hacia la trompa.
    afina = p.get("cabeza_afina", 1.0)
    for i in range(int(recto / paso) + 1):
        d = i * paso
        sec.append((d, r0 + (r1 - r0) * (d / recto) ** afina))
    # nariz: superelipse; 2.5 es chata con canto redondo (v9), 2 es redonda
    ex = p.get("nariz_exp", 2.5)
    for k in range(1, 24):
        u = k / 24
        sec.append((recto + cierre * u, r1 * (1 - u ** ex) ** (1 / ex)))
    secciones = []
    for d, r in sec:
        sube = p["cabeza_cuna"] * p["cabeza_alto"] * (r0 - max(r, r1)) if d > 0 else 0.0
        apaga = 1 - suave((d - (recto - p["nariz_lisa"])) / p["nariz_lisa"])
        if p.get("cabeza_lisa"):
            apaga = 0.0
        secciones.append((oy + dy * d, oz + dz * d, ny, nz, max(r, 0.01), sube, 1.0,
                          apaga))
    sube = p["cabeza_cuna"] * p["cabeza_alto"] * (r0 - r1)
    return tubo(p, secciones, (oy + dy * L + ny * sube, oz + dz * L + nz * sube),
                frente_lisa=p["frente_lisa"])


def craneo(p):
    """(y, z, radio) del cráneo, donde van osiconos y orejas."""
    if p["cabeza_forma"] == "recta":
        (oy, oz), _, _ = eje_cabeza(p)
        return oy, oz, p["cabeza_r"]
    zb = p["perfil"][-1][0]
    s_craneo = zb + p["curva_radio"] * math.radians(p["curva_grados"]) * 0.30
    (cy, cz), _, _ = columna(p, s_craneo)
    return cy, cz, radio(p, s_craneo)


def cuerpo(p, paso=0.6, por_estria=10):
    cols = p["estrias"] * por_estria
    total = largo_total(p)
    fin = total - p["punta_largo"]
    ss = [i * paso for i in range(int(fin / paso) + 1)]
    # la nariz se muestrea por ángulo para cerrar redondo
    ss += [fin + p["punta_largo"] * math.sin(math.pi / 2 * k / 40) for k in range(1, 40)]
    zb = p["perfil"][-1][0]
    m = M.Malla()
    anillos = []
    for s in ss:
        (py, pz), _, (ny, nz) = columna(p, s)
        r = radio(p, s)
        sube = alza(p, s)
        # en la cabeza la sección se ensancha un poco de lado
        h = min(1.0, max(0.0, (s - zb) / 12))
        k = 1 + (p["ancho"] - 1) * h
        tri = p["cara_triangulo"] * h
        # la nariz va lisa: las estrías juntas en la punta se leían como flor
        apaga = min(1.0, max(0.0, (fin - s) / p["nariz_lisa"]))
        apaga = apaga * apaga * (3 - 2 * apaga)
        fila = []
        for j in range(cols):
            a = 2 * math.pi * j / cols
            rr = r + estria(p, a, r, apaga)
            cx = rr * k * math.cos(a) * (1 + tri * math.sin(a))
            cn = rr * math.sin(a)
            cn += sube
            fila.append(m.punto(cx, py + ny * cn, pz + nz * cn))
        anillos.append(fila)
    abajo = m.punto(0, 0, 0)
    (py, pz), _, (ny, nz) = columna(p, total)
    sube = alza(p, total)
    punta = m.punto(0, py + ny * sube, pz + nz * sube)
    for j in range(cols):
        j2 = (j + 1) % cols
        m.cara(abajo, anillos[0][j2], anillos[0][j])
        for f in range(len(anillos) - 1):
            a, b = anillos[f], anillos[f + 1]
            m.quad(a[j], a[j2], b[j2], b[j])
        m.cara(anillos[-1][j], anillos[-1][j2], punta)
    return m.normalizar()


# ─── Piezas de la cabeza ───────────────────────────────────────────────────

def rotar(v, eje, grados):
    a = math.radians(grados)
    c, s = math.cos(a), math.sin(a)
    x, y, z = v
    if eje == "x":
        return (x, y * c - z * s, y * s + z * c)
    if eje == "y":
        return (x * c + z * s, y, -x * s + z * c)
    return (x * c - y * s, x * s + y * c, z)


def girar(v, giros):
    for eje, g in giros:
        v = rotar(v, eje, g)
    return v


def elipsoide(radios, giros, centro, lados=24, pisos=16):
    """Elipsoide alineado con z, girado por la lista de (eje, grados)."""
    m = M.Malla()
    rx, ry, rz = radios

    def pt(v):
        v = girar(v, giros)
        return m.punto(v[0] + centro[0], v[1] + centro[1], v[2] + centro[2])

    anillos = []
    for i in range(1, pisos):
        th = math.pi * i / pisos
        anillos.append([pt((rx * math.sin(th) * math.cos(2 * math.pi * j / lados),
                            ry * math.sin(th) * math.sin(2 * math.pi * j / lados),
                            -rz * math.cos(th))) for j in range(lados)])
    abajo, arriba = pt((0, 0, -rz)), pt((0, 0, rz))
    for j in range(lados):
        j2 = (j + 1) % lados
        m.cara(abajo, anillos[0][j2], anillos[0][j])
        for f in range(len(anillos) - 1):
            a, b = anillos[f], anillos[f + 1]
            m.quad(a[j], a[j2], b[j2], b[j])
        m.cara(anillos[-1][j], anillos[-1][j2], arriba)
    return m.normalizar()


def tallo(r0, r1, largo, giros, base, lados=20):
    """Cono truncado cerrado, de la base hacia +z antes de girar."""
    m = M.Malla()

    def pt(v):
        v = girar(v, giros)
        return m.punto(v[0] + base[0], v[1] + base[1], v[2] + base[2])

    def aro(r, z):
        return [pt((r * math.cos(2 * math.pi * j / lados),
                    r * math.sin(2 * math.pi * j / lados), z)) for j in range(lados)]

    a, b = aro(r0, 0), aro(r1, largo)
    c0, c1 = pt((0, 0, 0)), pt((0, 0, largo))
    for j in range(lados):
        j2 = (j + 1) % lados
        m.quad(a[j], a[j2], b[j2], b[j])
        m.cara(c0, a[j2], a[j])
        m.cara(c1, b[j], b[j2])
    return m.normalizar()


def cabeza(p):
    """Osiconos y orejas, sobre el cráneo."""
    cy, cz, rc = craneo(p)
    piezas = []
    for lado in (-1, 1):
        # Osiconos: salen de la coronilla, abren a los lados y se echan un
        # poco hacia atrás, como en la jirafa.
        x0 = lado * rc * 0.38
        y0 = cy + 3.0
        z0 = cz + rc * math.sqrt(1 - 0.38 ** 2) - 3.5
        giros = [("x", -12), ("y", lado * p["osicono_abre"])]
        largo = p["osicono_largo"] + 3.5
        piezas.append(tallo(p["osicono_r"] * 1.2, p["osicono_r"], largo,
                            giros, (x0, y0, z0)))
        punta = girar((0, 0, largo), giros)
        piezas.append(elipsoide((p["osicono_bola"],) * 3, [],
                                (x0 + punta[0], y0 + punta[1], z0 + punta[2])))
        # Orejas: hoja aplanada que sale de lado, algo hacia arriba, con la
        # cara al frente; detrás de los osiconos. La raíz queda metida.
        zo = cz + rc * 0.15
        xo = lado * rc * p["ancho"] * 0.80
        giros = [("y", lado * (90 - p["oreja_sube"]))]
        L = p["oreja_largo"]
        eje = girar((0, 0, L * 0.5), giros)
        piezas.append(elipsoide((p["oreja_ancho"] * 0.5, p["oreja_grueso"] * 0.5, L * 0.5),
                                giros, (xo + eje[0], cy + 5.0, zo + eje[2])))
    return piezas


def construir(p):
    todo = M.Malla()
    if p["cabeza_forma"] == "recta":
        figura = cuello_recto(p)
        todo.unir(figura)
        todo.unir(cabeza_recta(p))
    else:
        figura = cuerpo(p)
        todo.unir(figura)
    for pz in cabeza(p):
        todo.unir(pz)
    return todo, figura


def guardar(todo, ruta, nombre, png, ajustes=AJUSTES):
    """.3mf con la figura al centro del plato. Con `ajustes` copia el
    project_settings.config de ese .3mf y marca el archivo como de Bambu
    Studio; sin esa marca el laminador ignora los ajustes del proyecto."""
    (x0, y0, z0), (x1, y1, _) = todo.caja()
    pieza = todo.trasladada(PLATO / 2 - (x0 + x1) / 2, PLATO / 2 - (y0 + y1) / 2, -z0)
    exportar.guardar_3mf([(nombre, pieza, 0.0, 0.0)], ruta, nombre,
                         miniatura=png, notas=nombre)
    if not ajustes or not Path(ajustes).exists():
        return
    with zipfile.ZipFile(ajustes) as z:
        cfg = z.read("Metadata/project_settings.config")
    with zipfile.ZipFile(ruta) as z:
        todo_zip = {n: z.read(n) for n in z.namelist()}
    todo_zip["Metadata/project_settings.config"] = cfg
    modelo = todo_zip["3D/3dmodel.model"].decode("utf-8")
    todo_zip["3D/3dmodel.model"] = modelo.replace(
        '<metadata name="Title">',
        '<metadata name="Application">BambuStudio-02.07.01.62</metadata>\n'
        '<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        '<metadata name="Title">', 1).encode("utf-8")
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in todo_zip.items():
            z.writestr(n, b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=".")
    ap.add_argument("--nombre", default="JirafaEstriada")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--colores", default="salvia,beige,rojo")
    ap.add_argument("--vistas", default="frente,tres_cuartos,perfil")
    ap.add_argument("--tam", type=int, default=512)
    ap.add_argument("--3mf", dest="tres_mf", action="store_true",
                    help="guarda <nombre>.3mf con miniatura y ajustes de laminado")
    a = ap.parse_args()

    p = dict(JIRAFA)
    todo, figura = construir(p)
    (x0, y0, z0), (x1, y1, z1) = todo.caja()
    vol = figura.volumen() / 1000.0
    print("Jirafa estriada %.0f × %.0f × %.0f mm, %d triángulos, cuerpo cerrado: %s"
          % (x1 - x0, y1 - y0, z1 - z0, len(todo.t), figura.aristas_sueltas() == 0))
    print("  cuerpo ≈ %.0f cm³ (≈ %.0f g si fuera macizo)" % (vol, vol * 1.24))

    vistas = {"frente": (0, 8), "tres_cuartos": (35, 16), "perfil": (90, 6)}
    salida = Path(a.salida).expanduser()
    salida.mkdir(parents=True, exist_ok=True)
    if a.tres_mf:
        ruta = salida / (a.nombre + ".3mf")
        png = render.render(todo.v, todo.t, tam=512, suavizado=2,
                            direccion=render.vector_vista(*vistas["tres_cuartos"]),
                            color=COLORES["salvia"])
        guardar(todo, ruta, a.nombre, png)
        print("  →", ruta)
    if a.render:
        for nom in a.colores.split(","):
            for vista in a.vistas.split(","):
                ruta = salida / ("%s_%s_%s.png" % (a.nombre, nom, vista))
                render.render(todo.v, todo.t, tam=a.tam, suavizado=2,
                              direccion=render.vector_vista(*vistas[vista]),
                              color=COLORES[nom], ruta=str(ruta))
                print("  →", ruta)


if __name__ == "__main__":
    main()
