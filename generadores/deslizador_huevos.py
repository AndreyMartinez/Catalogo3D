#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deslizador de huevos de dos carriles que cabe en la caja de 20 × 16 × 11 cm.

La idea es la del «Kiki Egg Slide»: el huevo rueda de lado por un piso
inclinado, cae a un segundo nivel y regresa hasta la boca de donde se toma.
Lo que cambia es la caja: con 11 cm de alto no caben dos niveles techados
(el carril de un huevo extra grande pide ~51 mm de claro, dos niveles más
pisos y pendiente dan ~125 mm). Por eso:

  * el nivel de arriba va ABIERTO: es una repisa donde se cargan los huevos;
  * los 16 cm de ancho se usan para DOS carriles lado a lado;
  * la boca de cada carril queda al frente, descubierta, con un tope bajo
    para sacar el huevo rodándolo hacia uno.

Recorrido de un huevo (vista de lado, x = largo, frente a la izquierda):

        carga →  ___________________     ← repisa, baja hacia atrás
                |___________________|  ↓ cae al fondo
     boca  ___________________________/  ← piso de abajo, baja hacia el frente

La pared es una sola cinta de esquinas redondas que se ondula entera con
grosor parejo (piel japandi: estría de media caña; o ondas diagonales). El
borde baja en una sola curva de la parte de arriba al tope de la boca.

Se imprime parado, como se usa, sin soportes: el techo del carril de abajo
es un puente entre dos chaflanes de 45°, y todo lo demás es pared vertical
o sube desde el piso.

    python3 deslizador_huevos.py --salida "~/Desktop/own design 3d"
"""

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path

# nucleo/ vive junto a este archivo o, desde un worktree, en la copia de
# trabajo principal (generadores/ no está versionado).
for _dir in Path(__file__).resolve().parents:
    if (_dir / "nucleo").is_dir() or (_dir / "generadores" / "nucleo").is_dir():
        sys.path.insert(0, str(_dir if (_dir / "nucleo").is_dir()
                               else _dir / "generadores"))
        break

from nucleo import exportar, malla as M, render   # noqa: E402

# Medidas en mm. Huevo «extra grande» mexicano: ~62 de largo × 46-47 de
# diámetro. Rueda de lado, así que el largo va a lo ancho del carril y el
# diámetro a lo alto.
P = {
    "huevo_d": 48.0,        # diámetro del huevo más grande que debe pasar
    "huevo_l": 64.0,        # largo del huevo más grande
    "carril": 68.0,         # ancho libre de cada carril (huevo_l + 4)
    "claro": 54.0,          # alto libre del carril de abajo (huevo_d + 6)
    "hueco": 60.0,          # de la punta de la repisa al fondo, por donde cae
    "huevos_arriba": 2,     # huevos por carril en la repisa (fija su largo)
    "carriles": 2,
    "largo": 192.0,         # + relieve ≈ 195: 5 mm de holgura en la caja de 200
    "pared": 1.2,           # lisa por dentro; la estría sale hacia afuera
        "piso_frente": 1.6,     # piso del carril de abajo en la boca
    "pendiente": 6.0,       # grados, los dos niveles (lo más que cabe en 11 cm)
    "repisa": 2.4,          # grueso de la repisa en su punta de atrás
    "tope_boca": 12.0,      # alto del tope de la boca sobre el piso
    "tope_carga": 4.0,      # pestaña al frente de la repisa
    "borde_arriba": 22.0,   # pared sobre el piso de la repisa, al frente
    "chaflan": 8.0,         # chaflanes bajo la repisa: el puente baja a 52 mm
    "radio_vuelta": 40.0,   # redondeo cóncavo piso-fondo abajo
    "radio_planta": 12.0,   # esquinas redondas de la cinta, vistas desde arriba
    "riel": 12.0,           # alto del divisor entre carriles donde se ve
    "relieve": "japandi",   # japandi (estría vertical) · ondas (diagonales) · liso
    "relieve_alto": 1.5,    # cuánto se ondula la pared (≤ pared - 0.3)
    "relieve_paso": 0.0,    # 0 = el de cada estilo (japandi 9, ondas 42)
    "relieve_angulo": 45.0, # inclinación de las ondas
    "relieve_borde": 6.0,   # franja lisa arriba
}


# ─── Prismas ───────────────────────────────────────────────────────────────

def _cerrar(m):
    if m is None:
        raise RuntimeError("no se pudo triangular un perfil")
    return m.normalizar()


def perfil_xz(poligono, y0, y1, huecos=()):
    """Perfil dibujado en el plano x-z (de lado), extruido a lo ancho en y."""
    m = _cerrar(M.placa(M.orientar(poligono), list(huecos), y0, y1))
    m.v = [(a, w, b) for a, b, w in m.v]
    return m.normalizar()


def arco(cx, cz, r, a0, a1, n=16):
    """Puntos de un arco entre los ángulos a0 y a1 (grados), extremos incluidos."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(n + 1)]


# ─── Geometría ─────────────────────────────────────────────────────────────

def medidas(p):
    """Todas las cotas derivadas, en un solo lugar."""
    s = math.tan(math.radians(p["pendiente"]))
    L, w = p["largo"], p["pared"]
    d = dict(s=s, L=L)
    d["W"] = p["carriles"] * p["carril"] + (p["carriles"] + 1) * w
    d["x_frente"] = w                                   # cara interior del tope
    d["x_fondo"] = L - w                               # cara interior del fondo
    # La repisa termina dejando atrás un hueco por donde cae el huevo.
    # Ancho de sobra: un huevo que llega girado ocupa más que su diámetro.
    d["x_s1"] = d["x_fondo"] - p["hueco"]
    d["x_s0"] = d["x_s1"] - p["huevos_arriba"] * (p["huevo_d"] + 1.0) - 1.0

    def piso(x):
        return p["piso_frente"] + s * (x - d["x_frente"])
    d["piso"] = piso
    # Techo del carril de abajo en la punta de la repisa, donde el claro es
    # el justo; hacia el frente la repisa sube y el piso baja.
    d["z_techo"] = piso(d["x_s1"]) + p["claro"]
    d["z_rep_atras"] = d["z_techo"] + p["repisa"]
    d["z_rep_frente"] = d["z_rep_atras"] + s * (d["x_s1"] - d["x_s0"])
    d["H"] = d["z_rep_frente"] + p["borde_arriba"]
    d["caida"] = d["z_rep_atras"] - piso(d["x_s1"])
    return d


def recortar_x(poligono, x0, x1):
    """El polígono recortado a la franja x0 ≤ x ≤ x1 (Sutherland-Hodgman)."""
    def corte(pts, borde, dentro):
        salida = []
        for i, q in enumerate(pts):
            r = pts[i - 1]
            if dentro(q):
                if not dentro(r):
                    salida.append(_cruce(r, q, borde))
                salida.append(q)
            elif dentro(r):
                salida.append(_cruce(r, q, borde))
        return salida

    def _cruce(r, q, x):
        u = (x - r[0]) / (q[0] - r[0])
        return (x, r[1] + u * (q[1] - r[1]))

    pts = corte(list(poligono), x0, lambda q: q[0] >= x0)
    return corte(pts, x1, lambda q: q[0] <= x1)


def cuerpo_bajo(p, d):
    """Piso inclinado y la vuelta cóncava contra el fondo, solo lo de adentro
    de la cinta (el tope de la boca y el fondo los pone la cinta)."""
    rf, w, L = p["radio_vuelta"], p["pared"], d["L"]
    xf, xb, piso = d["x_frente"], d["x_fondo"], d["piso"]
    x_arco = xb - rf
    z_arco = piso(x_arco)
    pts = [(0.2, 0.0), (L - 0.2, 0.0), (L - 0.2, z_arco + rf)]
    pts += arco(x_arco, z_arco + rf, rf, 0, -90, 20)
    pts += [(0.2, piso(0.2))]
    return pts


def repisa(p, d):
    """Repisa de carga: placa de grosor parejo que baja hacia atrás (el techo
    del carril de abajo le corre paralelo), pestaña al frente y la punta de
    atrás redondeada por donde rueda el huevo. Pareja en vez de cuña: la cuña
    de 3 a 10 mm eran ~45 g de plástico que nadie ve."""
    x0, x1, s = d["x_s0"], d["x_s1"], d["s"]
    zc, za = d["z_techo"], d["z_rep_atras"]
    t = p["tope_carga"]
    r = min(1.4, (za - zc) / 2.0)
    sube = s * (x1 - x0 + 3.0)
    pts = [(x0 - 3.0, zc + sube)]
    pts += arco(x1 - r, zc + r, r, -90, 0, 4)
    pts += arco(x1 - r, za - r, r, 0, 90, 4)[1:]
    pts += [(x0, d["z_rep_frente"]), (x0, d["z_rep_frente"] + t),
            (x0 - 3.0, d["z_rep_frente"] + t)]
    return pts


def prisma(caras):
    """Prisma de dos triángulos 3D (uno en cada punta), cerrado."""
    m = M.Malla()
    a = [m.punto(*q) for q in caras[0]]
    b = [m.punto(*q) for q in caras[1]]
    m.cara(a[0], a[2], a[1])
    m.cara(b[0], b[1], b[2])
    for i in range(3):
        j = (i + 1) % 3
        m.quad(a[i], a[j], b[j], b[i])
    return m.normalizar()


def alto_borde(p, d, x):
    """Alto del borde de la cinta en cada x: plano atrás y, hacia el frente,
    una sola curva (coseno) que baja hasta el tope de la boca."""
    hb = d["piso"](d["x_frente"]) + p["tope_boca"]
    x0, x1 = p["radio_planta"], d["x_s0"] + 5.0
    if x <= x0:
        return hb
    if x >= x1:
        return d["H"]
    u = (x - x0) / (x1 - x0)
    return hb + (d["H"] - hb) * (1 - math.cos(math.pi * u)) / 2.0


def piso_en(p, d, x):
    """Alto del piso de abajo en x, con la vuelta cóncava contra el fondo."""
    rf = p["radio_vuelta"]
    x_arco = d["x_fondo"] - rf
    if x <= x_arco:
        return d["piso"](x)
    dx = min(x, d["x_fondo"]) - x_arco
    return d["piso"](x_arco) + rf - math.sqrt(max(0.0, rf * rf - dx * dx))


def columna(planta, alto):
    """Prisma vertical de planta convexa con la tapa a la altura alto(x) en
    cada vértice (abanico desde el primero)."""
    m = M.Malla()
    n = len(planta)
    abajo = [m.punto(x, y, 0.0) for x, y in planta]
    arriba = [m.punto(x, y, alto(x)) for x, y in planta]
    for i in range(1, n - 1):
        m.cara(abajo[0], abajo[i + 1], abajo[i])
        m.cara(arriba[0], arriba[i], arriba[i + 1])
    for i in range(n):
        j = (i + 1) % n
        m.quad(abajo[i], abajo[j], arriba[j], arriba[i])
    return m.normalizar()


def camino(L, W, R, paso):
    """Contorno de la cinta en planta (rectángulo de esquinas redondas), en
    sentido antihorario: lista de (x, y, nx, ny) con la normal hacia afuera."""
    tramos = []

    def recta(x0, y0, x1, y1, nx, ny):
        n = max(1, int(round(math.hypot(x1 - x0, y1 - y0) / paso)))
        tramos.extend((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, nx, ny)
                      for i in range(n))

    def curva(cx, cy, a0):
        n = max(4, int(round(R * math.pi / 2 / paso)))
        for i in range(n):
            a = math.radians(a0 + 90.0 * i / n)
            tramos.append((cx + R * math.cos(a), cy + R * math.sin(a),
                           math.cos(a), math.sin(a)))

    recta(R, 0.0, L - R, 0.0, 0.0, -1.0)
    curva(L - R, R, -90)
    recta(L, R, L, W - R, 1.0, 0.0)
    curva(L - R, W - R, 0)
    recta(L - R, W, R, W, 0.0, 1.0)
    curva(R, W - R, 90)
    recta(0.0, W - R, 0.0, R, -1.0, 0.0)
    curva(R, R, 180)
    return tramos


def _suave(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def relieve(p, s, z, z_tope, perimetro):
    """Cuánto sale la pared hacia afuera (mm) en el punto s del contorno a la
    altura z. Se desvanece abajo y deja una franja lisa arriba: el borde se
    lee limpio y la pieza asienta sobre una base pareja."""
    estilo, A = p["relieve"], p["relieve_alto"]
    if estilo == "liso" or A <= 0:
        return 0.0
    paso = p["relieve_paso"] or {"japandi": 9.0, "ondas": 42.0}[estilo]
    # El paso se ajusta para que el dibujo cierre exacto al dar la vuelta.
    paso = perimetro / max(1, round(perimetro / paso))
    fade = _suave(z / 3.0) * _suave((z_tope - z - p["relieve_borde"]) / 4.0)
    if estilo == "japandi":
        # Estría de media caña, una junto a otra: varilla redonda y canal fino.
        u = (s / paso) % 1.0
        return A * fade * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 2))
    # Ondas: bandas inclinadas que suben dando la vuelta a la pieza.
    k = math.tan(math.radians(p["relieve_angulo"]))
    return A * fade * 0.5 * (1 - math.cos(2 * math.pi * (s + z * k) / paso))


def cinta(p, d):
    """La pared que envuelve la pieza: una sola cinta, lisa por dentro (en
    v5 se ondulaba entera y las puntas del huevo se atoraban en las estrías)
    y con el relieve solo por fuera. Lo de adentro llega hasta la cara de
    afuera del contorno liso y queda siempre metido en la pared.

    Las esquinas llevan además un cuarto de cilindro macizo por dentro: lo de
    adentro es rectangular y así no queda hueco entre él y la curva."""
    L, W, w, R = d["L"], d["W"], p["pared"], p["radio_planta"]
    alto = lambda x: alto_borde(p, d, x)
    tramos = camino(L, W, R, 0.7)
    s_acum, s = [], 0.0
    for i, (x, y, _, _) in enumerate(tramos):
        s_acum.append(s)
        x2, y2 = tramos[(i + 1) % len(tramos)][:2]
        s += math.hypot(x2 - x, y2 - y)
    perimetro = s
    filas = 70
    m = M.Malla()
    afuera, adentro = [], []
    for (x, y, nx, ny), si in zip(tramos, s_acum):
        zt = alto(x)
        fa, fd = [], []
        for j in range(filas + 1):
            z = zt * j / filas
            r = relieve(p, si, z, zt, perimetro)
            fa.append(m.punto(x + nx * r, y + ny * r, z))
            fd.append(m.punto(x - nx * w, y - ny * w, z))
        afuera.append(fa)
        adentro.append(fd)
    n, t = len(tramos), filas
    for i in range(n):
        k = (i + 1) % n
        o0, o1, d0, d1 = afuera[i], afuera[k], adentro[i], adentro[k]
        for j in range(t):
            m.quad(o0[j], o1[j], o1[j + 1], o0[j + 1])
            m.quad(d0[j], d0[j + 1], d1[j + 1], d1[j])
        m.quad(o0[t], o1[t], d1[t], d0[t])
        m.quad(o1[0], o0[0], d0[0], d1[0])
    piezas = [m.normalizar()]
    # Solo hasta el piso (o la vuelta) que tapan: en v5 subían hasta lo alto
    # de la vuelta y se metían 10 mm en el hueco de la caída, justo donde
    # pasan las puntas del huevo, y lo atoraban.
    for cx, cy, a0 in ((R, R, 180), (L - R, R, 270), (L - R, W - R, 0),
                       (R, W - R, 90)):
        planta = [(cx, cy)] + arco(cx, cy, R - 0.2, a0, a0 + 90, 12)
        piezas.append(columna(planta, lambda x: min(alto(x) - 0.2, piso_en(p, d, x))))
    return piezas


def divisor(p, d):
    """Divisor entre carriles: alto (llega a la repisa y la sostiene) solo
    debajo de ella; arriba y en la boca es un riel bajo que apenas se ve."""
    L, w = d["L"], p["pared"]
    xf, xb, piso, s = d["x_frente"], d["x_fondo"], d["piso"], d["s"]
    riel = p["riel"]
    x0 = d["x_s0"] - 3.0
    z_rep = lambda x: d["z_rep_atras"] + s * (d["x_s1"] - x)
    r = 2.0
    pts = [(0.2, 0.0), (L - 0.2, 0.0), (L - 0.2, z_rep(xb) + riel)]
    pts += [(x0 + r, z_rep(x0) + riel)]
    pts += arco(x0 + r, z_rep(x0) + riel - r, r, 90, 180, 4)[1:]
    pts += [(x0, piso(x0) + riel + r)]
    pts += arco(x0 - r, piso(x0) + riel + r, r, 0, -90, 4)[1:]
    pts += [(0.2, piso(xf) + riel)]
    return pts


def construir(p):
    d = medidas(p)
    W, w, c = d["W"], p["pared"], p["chaflan"]
    pieza = M.Malla()
    for parte in cinta(p, d):
        pieza.unir(parte)
    # Lo de adentro va de pared a pared; cerca de las esquinas se recorta para
    # que no se salga de la curva.
    R, L = p["radio_planta"], d["L"]
    bajo = cuerpo_bajo(p, d)
    pieza.unir(perfil_xz(recortar_x(bajo, R, L - R), 0.2, W - 0.2))
    for xa, xb in ((0.0, R + 0.3), (L - R - 0.3, L)):
        pieza.unir(perfil_xz(recortar_x(bajo, xa, xb), R - 0.3, W - R + 0.3))
    pieza.unir(perfil_xz(repisa(p, d), 0.2, W - 0.2))
    carriles = []
    y = w
    for k in range(p["carriles"]):
        carriles.append((y, y + p["carril"]))
        y += p["carril"]
        if k < p["carriles"] - 1:
            pieza.unir(perfil_xz(divisor(p, d), y, y + w))
            y += w
    # Chaflanes bajo la repisa: el puente del techo baja de 66 a 46 mm y
    # no estorban al huevo, que en las puntas es más bajo que en medio.
    zc, x0, x1 = d["z_techo"], d["x_s0"] - 3.0, d["x_s1"] - 1.0
    for ya, yb in carriles:
        # Contra la cinta el chaflán arranca desde su cara de afuera, porque
        # por dentro la cinta se ondula; contra el divisor, desde el divisor.
        qa = 0.2 if ya == w else ya - 0.5
        qb = W - 0.2 if yb == W - w else yb + 0.5
        for tri in ([(qa, 1.0), (ya + c + 1.0, 1.0), (qa, -c - (ya - qa))],
                    [(qb, 1.0), (qb, -c - (qb - yb)), (yb - c - 1.0, 1.0)]):
            pieza.unir(prisma([[(x, yy, zc + d["s"] * (d["x_s1"] - x) + dz)
                                for yy, dz in tri] for x in (x0, x1)]))
    d["carriles"] = carriles
    return pieza, d


# ─── Revisión: ¿pasa el huevo? ¿cuántos caben? ─────────────────────────────

def revisar(p, d):
    avisos = []
    R, Lh = p["huevo_d"] / 2.0, p["huevo_l"] / 2.0
    zc, c, media = d["z_techo"], p["chaflan"], p["carril"] / 2.0
    # Claro bajo la repisa, de punta a punta del huevo, contra el techo con
    # sus chaflanes. Silueta del huevo de frente: elipse Lh (y) × R (z).
    for x in (d["x_s0"], d["x_s1"]):
        piso = d["piso"](x)
        for i in range(31):
            dy = Lh * i / 30.0
            alto = piso + R + R * math.sqrt(max(0.0, 1 - (dy / Lh) ** 2))
            techo = zc - max(0.0, c - (media - dy))
            if techo - alto < 1.5:
                avisos.append("roza el techo en x=%.0f, a %.0f mm del centro "
                              "(%.1f mm)" % (x, dy, techo - alto))
                break
    if d["H"] > 104:
        avisos.append("mide %.1f de alto: no deja holgura en la caja de 110" % d["H"])
    # Cuántos huevos por carril: abajo, de la boca a la vuelta; uno en el
    # hueco de la caída, apoyado sobre el último; arriba, de la pestaña a la
    # punta.
    D = p["huevo_d"]
    abajo = int((d["x_fondo"] - d["x_frente"] - p["radio_vuelta"] * 0.35) // D)
    arriba = int((d["x_s1"] - d["x_s0"]) // D)
    return avisos, abajo, 1, arriba


def huevos(p, d, abajo, arriba):
    """Huevos de muestra (elipsoides) para la vista con carga."""
    R, Lh = p["huevo_d"] / 2.0 - 0.5, p["huevo_l"] / 2.0 - 1.0
    centros = []
    for ya, yb in d["carriles"]:
        yc = (ya + yb) / 2.0
        for k in range(abajo):
            x = d["x_frente"] + R + 0.5 + k * p["huevo_d"]
            centros.append((x, yc, d["piso"](x) + R + 0.5))
        x_hueco = d["x_fondo"] - R - 6.0
        centros.append((x_hueco, yc, d["z_rep_atras"] + R - 10.0))
        for k in range(arriba):
            x = d["x_s1"] - R - 1.0 - k * p["huevo_d"]
            centros.append((x, yc, d["z_rep_atras"]
                            + d["s"] * (d["x_s1"] - x) + R + 0.5))
    m = M.Malla()
    nu, nv = 24, 14
    for cx, cy, cz in centros:
        base = len(m.v)
        for i in range(nv + 1):
            th = math.pi * i / nv
            for j in range(nu):
                ph = 2 * math.pi * j / nu
                m.v.append((cx + R * math.sin(th) * math.cos(ph),
                            cy + Lh * math.cos(th),
                            cz + R * math.sin(th) * math.sin(ph)))
        for i in range(nv):
            for j in range(nu):
                a = base + i * nu + j
                b = base + i * nu + (j + 1) % nu
                m.t.append((a, a + nu, b))
                m.t.append((b, a + nu, b + nu))
    return m


# ─── Guardado ──────────────────────────────────────────────────────────────

AJUSTES = (Path.home() / "Desktop" / "own design 3d"
           / "General_Vases_print_profile(5).3mf")
LAMINADO = {"wall_loops": "2", "sparse_infill_density": "10%",
            "sparse_infill_pattern": "grid", "enable_support": "0",
            "top_shell_layers": "3", "bottom_shell_layers": "3",
            "resolution": "0.05"}


def guardar(pieza, ruta, nombre, png, notas, parametros):
    (x0, y0, _), (x1, y1, _) = pieza.caja()
    dx, dy = 128.0 - (x0 + x1) / 2.0, 128.0 - (y0 + y1) / 2.0
    exportar.guardar_3mf([("pieza", pieza, dx, dy)], ruta, nombre,
                         miniatura=png, notas=notas, parametros=parametros)
    if not AJUSTES.exists():
        return
    with zipfile.ZipFile(AJUSTES) as z:
        cfg = json.loads(z.read("Metadata/project_settings.config"))
    cfg.update(LAMINADO)
    dif = cfg.get("different_settings_to_system") or [""]
    dif[0] = ";".join(sorted(set(filter(None, dif[0].split(";"))) | set(LAMINADO)))
    cfg["different_settings_to_system"] = dif
    with zipfile.ZipFile(ruta) as z:
        todo = {n: z.read(n) for n in z.namelist()}
    todo["Metadata/project_settings.config"] = json.dumps(cfg, indent=4).encode()
    # Sin el metadato Application, Bambu Studio ignora project_settings.config.
    modelo = todo["3D/3dmodel.model"].decode("utf-8").replace(
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
    ap.add_argument("--nombre", default="DeslizadorHuevos")
    ap.add_argument("--giro", type=float, default=34)
    ap.add_argument("--elevacion", type=float, default=28)
    for k, v in P.items():
        ap.add_argument("--" + k.replace("_", "-"), dest=k, type=type(v), default=v)
    a = ap.parse_args()
    p = {k: getattr(a, k) for k in P}

    pieza, d = construir(p)
    avisos, abajo, hueco, arriba = revisar(p, d)
    por_carril = abajo + hueco + arriba
    (x0, y0, z0), (x1, y1, z1) = pieza.caja()

    ruta = Path(a.salida).expanduser() / (a.nombre + ".3mf")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    vista = render.vector_vista(a.giro, a.elevacion)
    png = render.render(pieza.v, pieza.t, tam=512, suavizado=2, direccion=vista,
                        ruta=ruta.with_suffix(".png"))
    con = M.Malla().unir(pieza).unir(huevos(p, d, abajo, arriba))
    render.render(con.v, con.t, tam=640, suavizado=2, direccion=vista,
                  ruta=ruta.with_name(a.nombre + "_con_huevos.png"))
    guardar(pieza, ruta, a.nombre, png,
            "%s · %d carriles · %d huevos" % (a.nombre, p["carriles"],
                                              por_carril * p["carriles"]), p)

    print("%s" % ruta)
    print("  Medidas      %.1f × %.1f × %.1f mm (caja 200 × 160 × 110)"
          % (x1 - x0, y1 - y0, z1 - z0))
    print("  Pendiente    %.1f° en los dos niveles" % p["pendiente"])
    print("  Techo abajo  %.1f mm libres (huevo %.0f)" % (p["claro"], p["huevo_d"]))
    print("  Caída        %.1f mm del nivel de arriba al de abajo" % d["caida"])
    print("  Huevos       %d por carril (%d abajo + %d en la caída + %d arriba)"
          " → %d en total" % (por_carril, abajo, hueco, arriba,
                              por_carril * p["carriles"]))
    for av in avisos:
        print("  AVISO", av)


if __name__ == "__main__":
    main()
