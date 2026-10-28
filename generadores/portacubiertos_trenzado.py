#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portacubiertos trenzado: vasos de costillas en espiral, caladas, sobre una
bandeja de un lóbulo por vaso (2 por omisión; `--vasos 3` es el de la foto).

Sale de una foto de referencia (10-22): vasos color nogal con costillas
redondas que suben inclinadas y dejan rendijas entre sí, metidos en una
bandeja beige cuyo borde baja en las cinturas entre vaso y vaso.

    python3 portacubiertos_trenzado.py --salida /ruta --nombre MiPieza
    python3 portacubiertos_trenzado.py --costillas 18 --inclinacion 40

El vaso no sale del motor (cuerpo.construir hace paredes cerradas): cada
costilla es un sólido aparte, barrido en espiral, que se encima un poco en el
anillo de la base y en el de la boca. El laminador une los sólidos encimados.
Las rendijas son huecos de verdad; su techo es la cara de abajo de la costilla,
que va inclinada lo mismo que la costilla (35° de la vertical por defecto),
así que no lleva soportes.
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

PLATO = 256.0
DENSIDAD = 1.24          # g/cm³, PLA

VASO = {
    "radio_base": 31.0,      # radio exterior (a la cresta) en el piso
    "radio_panza": 40.0,     # lo más ancho: el vaso es de huevo, panza abajo
    "altura_panza": 0.46,    # dónde cae la panza, en fracción del alto
    "radio_boca": 29.0,      # la boca cierra un poco sobre la panza
    "alto": 100.0,
    "costillas": 14,
    "inclinacion": 35.0,     # grados respecto de la vertical
    "rendija": 2.2,          # mm, medida en perpendicular a la costilla
    "canto": 1.0,            # grueso de la costilla en sus orillas
    "grueso": 2.4,           # la costilla es cáscara de este grueso
    "panza": 4.0,            # lo que sobresale la cresta sobre el canto
    "piso": 1.6,
    "drenaje": 4.0,          # diámetro de los agujeros del piso
    "zocalo": 6.0,           # anillo macizo de abajo (queda dentro de la bandeja)
    "aro": 3.0,              # anillo macizo de la boca
    "capas": 0.5,            # mm entre secciones del barrido
}

BANDEJA = {
    "vasos": 2,              # 2 caben armados en la caja de 20 × 16 × 11 (con 3,
                             # la bandeja mide 25 cm y no entra)
    "largo": 196.0,          # mm de la bandeja: los vasos se ensanchan (mismo alto,
                             # misma forma de huevo) hasta llenarlo; 0 = los de VASO
    "holgura": 0.8,          # entre vaso y bandeja, de cada lado
    "pared": 4.5,
    "piso": 1.6,
    "alto": 65.0,            # atrás, en el centro de cada lóbulo
    "alto_frente": 32.0,     # adelante: la bandeja baja de atrás hacia el frente
    "caida_atras": 0.0,      # cuánto baja el borde en cada cintura, atrás
    "caida": 0.0,            # … y al frente (0: el borde corre recto)
    "separacion": 0.6,       # entre vasos, en la panza: casi se rozan
    "cintura": 14.0,         # radio del redondeo cóncavo entre lóbulos
    "recto": 1,              # 1 = frente y espalda rectos por fuera, sin cinturas
    "patas": 1.5,            # alto de las costillitas del piso: el vaso no
                             # se queda parado en el agua que escurre
}


# ── Vaso ──────────────────────────────────────────────────────────────────

def radio_ext(v, z):
    """Perfil de barril: sube del piso a la panza con un cuarto de seno y baja
    a la boca con un cuarto de coseno, así la panza no hace pico."""
    t = min(1.0, max(0.0, z / v["alto"]))
    tp = v["altura_panza"]
    rb, rp, rc = v["radio_base"], v["radio_panza"], v["radio_boca"]
    if t <= tp:
        return rb + (rp - rb) * math.sin(math.pi / 2 * t / tp)
    return rp - (rp - rc) * (1 - math.cos(math.pi / 2 * (t - tp) / (1 - tp)))


def radio_int(v, z):
    return radio_ext(v, z) - v["canto"] - v["panza"]


def solido_de_revolucion(perfil, lados=128):
    """Sólido cerrado a partir de un perfil (r, z) en el plano, de abajo hacia
    arriba por fuera y de vuelta por dentro. r = 0 en los extremos lo cierra."""
    m = M.Malla()
    filas = []
    for r, z in perfil:
        if r <= 1e-9:
            filas.append([m.punto(0.0, 0.0, z)] * lados)
        else:
            filas.append([m.punto(r * math.cos(2 * math.pi * k / lados),
                                  r * math.sin(2 * math.pi * k / lados), z)
                          for k in range(lados)])
    for a, b in zip(filas, filas[1:] + filas[:1]):
        for k in range(lados):
            k2 = (k + 1) % lados
            m.quad(a[k], a[k2], b[k2], b[k])
    return m.normalizar()


def costilla(v, angulo0, z0, z1, puntos=13):
    """Una costilla: sección horizontal de cordón (panza redonda por fuera)
    que gira con la altura. Por dentro sigue la panza a `grueso` mm, como
    cáscara: se ve gorda sin ser maciza. Tapas en tira, cara a cara."""
    n_secc = max(2, int(math.ceil((z1 - z0) / v["capas"])) + 1)
    tan_inc = math.tan(math.radians(v["inclinacion"]))
    m = M.Malla()
    fuera, dentro = [], []
    for i in range(n_secc):
        z = z0 + (z1 - z0) * i / (n_secc - 1)
        r_e, r_i = radio_ext(v, z), radio_int(v, z)
        r_m = (r_e + r_i) / 2.0
        # Paso horizontal entre costillas y ancho horizontal de la rendija:
        # la rendija se pide en perpendicular, en horizontal mide /cos.
        paso = 2 * math.pi / v["costillas"]
        hueco = v["rendija"] / math.cos(math.radians(v["inclinacion"])) / r_m
        media = (paso - hueco) / 2.0
        # Sube y se corre a la izquierda vista de frente (como en la foto).
        centro = angulo0 - z * tan_inc / r_m
        f, d = [], []
        for k in range(puntos):
            s = -1.0 + 2.0 * k / (puntos - 1)
            r = r_i + v["canto"] + v["panza"] * math.sqrt(max(0.0, 1.0 - s * s))
            ri = max(r_i, r - v["grueso"])
            a = centro + s * media
            f.append(m.punto(r * math.cos(a), r * math.sin(a), z))
            d.append(m.punto(ri * math.cos(a), ri * math.sin(a), z))
        fuera.append(f)
        dentro.append(d)
    for i in range(n_secc - 1):
        # anillo cerrado: por fuera de un canto al otro, por dentro de regreso
        a = fuera[i] + dentro[i][::-1]
        b = fuera[i + 1] + dentro[i + 1][::-1]
        n = len(a)
        for k in range(n):
            k2 = (k + 1) % n
            m.quad(a[k], a[k2], b[k2], b[k])
    for i, abajo in ((0, True), (n_secc - 1, False)):
        for k in range(puntos - 1):
            q = (fuera[i][k], fuera[i][k + 1], dentro[i][k + 1], dentro[i][k])
            m.quad(*q) if not abajo else m.quad(*q[::-1])
    return m.normalizar()


def vaso(v):
    h, zs, aro = v["alto"], v["zocalo"], v["aro"]
    m = M.Malla()
    # Zócalo: anillo macizo hasta `zocalo`; el piso va aparte, con drenaje.
    m.unir(solido_de_revolucion([
        (radio_int(v, 0), 0.0), (radio_ext(v, 0) - 0.6, 0.0), (radio_ext(v, 0), 0.6),
        (radio_ext(v, zs), zs), (radio_int(v, zs), zs)]))
    # Piso con agujeros (uno al centro y tres alrededor) para que el agua que
    # escurre de los cubiertos baje a la bandeja. Los de alrededor caen entre
    # las costillitas de la bandeja, no encima.
    r_d = v["drenaje"] / 2.0
    huecos = [M.circulo_puntos(0, 0, r_d, 24)] + [
        M.circulo_puntos(12 * math.cos(a), 12 * math.sin(a), r_d, 24)
        for a in (math.pi / 6, 5 * math.pi / 6, 3 * math.pi / 2)]
    m.unir(M.placa(M.circulo_puntos(0, 0, radio_int(v, 0) + 0.4, 128), huecos,
                   0.0, v["piso"]))
    # Aro de la boca, con la orilla de arriba un poco redondeada.
    za = h - aro
    m.unir(solido_de_revolucion([
        (radio_int(v, za), za), (radio_ext(v, za) - 0.4, za),
        (radio_ext(v, h) - 0.4, h - 0.8), (radio_ext(v, h) - 1.2, h),
        (radio_int(v, h) + 0.4, h), (radio_int(v, h), h - 0.4)]))
    # Costillas, encimadas 0.6 mm en cada anillo para que queden soldadas.
    for j in range(v["costillas"]):
        m.unir(costilla(v, 2 * math.pi * j / v["costillas"], zs - 0.6, za + 0.6))
    return m


# ── Bandeja ───────────────────────────────────────────────────────────────

def _arco(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
             cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n)]


def centros_de(n, d):
    """Centros de n vasos en fila, a d entre sí, con el del medio en x = 0."""
    return [(i - (n - 1) / 2.0) * d for i in range(n)]


def lobulos(R, f, d, n, desfase=0.0, n_lobulo=96, n_cintura=24):
    """Contorno de n círculos de radio R en fila (a d entre centros) unidos
    por redondeos cóncavos de radio f. Con `desfase` se corre todo el contorno
    hacia afuera (+) o adentro (−) sin perder la correspondencia punto a punto:
    los centros de los arcos no cambian, solo sus radios."""
    Rc, fc = R + desfase, f - desfase
    yf = math.sqrt((R + f) ** 2 - (d / 2.0) ** 2)
    hacia_der = math.atan2(yf, d / 2.0)        # de un centro al redondeo de su derecha
    hacia_izq = math.atan2(yf, -d / 2.0)
    cs = centros_de(n, d)
    pts = _arco(cs[-1], 0, Rc, -hacia_izq, hacia_izq, 2 * n_lobulo)    # lóbulo der.
    for i in range(n - 2, -1, -1):                                     # por arriba
        pts += _arco(cs[i] + d / 2, yf, fc, -hacia_der, -math.pi + hacia_der, n_cintura)
        if i > 0:
            pts += _arco(cs[i], 0, Rc, hacia_der, hacia_izq, n_lobulo)
    pts += _arco(cs[0], 0, Rc, hacia_der, 2 * math.pi - hacia_der, 2 * n_lobulo)  # izq.
    for i in range(n - 1):                                             # por abajo
        pts += _arco(cs[i] + d / 2, -yf, fc, math.pi - hacia_der, hacia_der, n_cintura)
        if i < n - 2:
            pts += _arco(cs[i + 1], 0, Rc, -hacia_izq, -hacia_der, n_lobulo)
    return pts


def bandeja(v, b):
    """La pared del plato sigue al vaso: a cada altura, el asiento es el radio
    del vaso más la holgura. Como el borde queda por debajo de la panza, el
    vaso entra desde arriba y el plato lo abraza como un huevo en su copa."""
    alza = b["piso"] + b["patas"]                # donde asienta el vaso

    z_panza = alza + v["altura_panza"] * v["alto"]

    def r_asiento(z):
        # Arriba de la panza ya no cierra: si siguiera al vaso, no entraría.
        return radio_ext(v, min(z, z_panza) - alza) + b["holgura"]

    d = 2 * v["radio_panza"] + b["separacion"]
    n_vasos = int(b["vasos"])
    cs = centros_de(n_vasos, d)
    f_int, pared = b["cintura"], b["pared"]
    r_lab = pared / 2.0
    z_max = b["alto"]
    r_min, r_max = r_asiento(0.0), max(r_asiento(z_max * i / 60) for i in range(61))
    fondo = r_max + pared

    # Contornos de tres lóbulos para una rejilla de radios; un punto a una
    # altura dada se interpola entre los dos vecinos (misma topología).
    N = 48
    cache = {}

    def contorno(desfase, i):
        if (desfase, i) not in cache:
            R = r_min + (r_max - r_min) * i / (N - 1)
            pts = lobulos(R, f_int, d, n_vasos, desfase)
            if desfase > 0 and b["recto"]:
                # Por fuera, frente y espalda van rectos de lóbulo a lóbulo:
                # las cinturas se rellenan hasta la línea que toca los tres.
                y_linea = R + desfase
                pts = [(x, math.copysign(y_linea, y)) if abs(x) <= cs[-1] else (x, y)
                       for x, y in pts]
            cache[(desfase, i)] = pts
        return cache[(desfase, i)]

    def punto(desfase, k, z):
        u = (min(r_max, r_asiento(z)) - r_min) / (r_max - r_min) * (N - 1)
        i = min(N - 2, max(0, int(u)))
        w = u - i
        (x0, y0), (x1, y1) = contorno(desfase, i)[k], contorno(desfase, i + 1)[k]
        return x0 + (x1 - x0) * w, y0 + (y1 - y0) * w

    def alto(x, y):
        # De atrás (+y) alta a adelante (−y) baja, con una S suave. En las
        # cinturas (x = ±d/2) baja con una campana, más al frente que atrás.
        s = 0.5 + 0.5 * math.sin(math.pi / 2 * max(-1.0, min(1.0, y / fondo)))
        h = b["alto_frente"] + (b["alto"] - b["alto_frente"]) * s
        caida = b["caida"] + (b["caida_atras"] - b["caida"]) * s
        u = min(abs(x - c - d / 2.0) for c in cs[:-1])
        return h - caida * math.exp(-(u / (0.32 * d)) ** 2)

    medio = contorno(r_lab, N - 1)
    n = len(medio)
    h = [alto(x, y) for x, y in medio]
    m = M.Malla()
    filas, planos = [], []

    def fila(desfase, z_de):
        pts = []
        for k in range(n):
            z = z_de(k)
            pts.append((punto(desfase, k, z), z))
        filas.append([m.punto(x, y, z) for (x, y), z in pts])
        planos.append([xy for xy, _ in pts])

    # Por fuera: orilla de abajo suavizada, pared que sube siguiendo al vaso,
    # labio de medio círculo y de regreso por dentro hasta el piso.
    fila(pared - 1.2, lambda k: 0.0)
    fila(pared - 0.35, lambda k: 0.35)
    tramos = 12
    for j in range(tramos + 1):
        t = j / tramos
        fila(pared, lambda k, t=t: 1.2 + t * (h[k] - r_lab - 1.2))
    pasos = 10
    for j in range(1, pasos):
        phi = math.pi * j / pasos
        fila(r_lab + r_lab * math.cos(phi),
             lambda k, phi=phi: h[k] - r_lab + r_lab * math.sin(phi))
    for j in range(tramos + 1):
        t = j / tramos
        fila(0.0, lambda k, t=t: h[k] - r_lab - t * (h[k] - r_lab - b["piso"]))
    for a, bb in zip(filas, filas[1:]):
        for k in range(n):
            k2 = (k + 1) % n
            m.quad(a[k], a[k2], bb[k2], bb[k])
    # Piso de abajo y piso de adentro, triangulados por oreja. El contorno va
    # antihorario, así que triangular no lo voltea y sus índices son los de
    # las filas.
    for anillo, poly, abajo in ((filas[0], planos[0], True),
                                (filas[-1], planos[-1], False)):
        assert M.area_con_signo(poly) > 0
        _, tris, ok = M.triangular(poly)
        assert ok, "no se pudo triangular el piso de la bandeja"
        for i, j, k in tris:
            a, bb, c = anillo[i], anillo[j], anillo[k]
            m.cara(a, c, bb) if abajo else m.cara(a, bb, c)
    r_patas = r_asiento(b["piso"])
    # Tres costillitas por lóbulo, radiales a 90°, 210° y 330°: el agua corre
    # entre ellas y los agujeros del vaso (30°, 150°, 270°) caen en los huecos.
    m.normalizar()
    for cx in cs:
        for a in (math.pi / 2, 7 * math.pi / 6, 11 * math.pi / 6):
            ca, sa = math.cos(a), math.sin(a)
            r0, r1, w = 6.0, r_patas - 4.0, 1.0
            pata = [(cx + r * ca - t * sa, r * sa + t * ca)
                    for r, t in ((r0, -w), (r1, -w), (r1, w), (r0, w))]
            m.unir(M.placa(M.orientar(pata), [], b["piso"] - 0.01,
                           b["piso"] + b["patas"]))
    return m, cs


def ajustar_al_largo(v, b):
    """Ensancha (o angosta) los vasos para que la bandeja mida `largo`: los
    tres radios del huevo crecen parejo y las costillas se multiplican igual,
    así cada costilla sigue del mismo ancho. El alto no cambia."""
    n = int(b["vasos"])
    rp = ((b["largo"] - (n - 1) * b["separacion"] - 2 * (b["holgura"] + b["pared"]))
          / (2.0 * n))
    k = rp / v["radio_panza"]
    for clave in ("radio_base", "radio_panza", "radio_boca"):
        v[clave] = round(v[clave] * k, 2)
    v["costillas"] = int(round(v["costillas"] * k))


# ── Salida ────────────────────────────────────────────────────────────────

# Perfil del P2S con Bambu PLA Basic (0.20 Standard), tomado del florero. El
# florero trae relleno 0 % y 3 capas de techo: aquí se regresan a los de
# fábrica (15 %, 5), que la bandeja y el zócalo los necesitan. Se quedan
# Arachne (las costillas de cordón son cáscara curva de 2.4 mm) y resolución
# 0.05: con 0.012 la malla redonda da tramitos que nunca alcanzan velocidad.
AJUSTES_P2S = (Path.home() / "Desktop" / "own design 3d"
               / "General_Vases_print_profile(5).3mf")
LAMINADO = {"sparse_infill_density": "15%", "skeleton_infill_density": "15%",
            "skin_infill_density": "15%", "top_shell_layers": "5",
            "wall_generator": "arachne", "resolution": "0.05",
            "infill_combination": "1",
            # Cada costilla es una isla por capa (14 por vaso): con 1 mm el
            # laminador retraía también al saltar de pared a pared dentro de
            # la misma costilla. Con 5 solo retrae entre costillas: 24 mil →
            # 16 mil retracciones y 2 h 45 → 2 h 29 por vaso.
            "retraction_minimum_travel": "5"}
DE_FABRICA = {"sparse_infill_density", "skeleton_infill_density",
              "skin_infill_density", "top_shell_layers"}
# Por objeto (por nombre): el peso de la bandeja es el relleno de sus paredes
# de 4.5 mm. Al 10 % pesa 115 g en vez de 125 y tarda 11 min menos. Hacer
# huecas las cinturas por dentro salió peor (133 g, +22 min): el relleno ya
# las dejaba huecas y la cavidad suma paredes.
#
# Las costillas del vaso (cáscara de 2.4 mm) tienen por dentro menos de 15 mm²
# y el laminador las llenaba de relleno sólido. Con el área mínima en 0 llevan
# relleno ligero entre sus dos paredes: 54.5 → 49.3 g y 2 h 29 → 2 h 03 por
# vaso, sin cambiar la forma. Con una sola pared bajaba a 37.4 g, pero la piel
# de la costilla queda de 0.45 mm: se descartó por frágil.
POR_OBJETO = {"bandeja": {"sparse_infill_density": "10%"},
              "vaso": {"minimum_sparse_infill_area": "0"}}


def modelo_settings(modelo):
    """Metadata/model_settings.config: un bloque por objeto (ids uno a uno)
    con los ajustes de POR_OBJETO."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', "<config>"]
    objetos = re.findall(r'<object id="(\d+)" type="model" name="([^"]*)"', modelo)
    for oid, nom in objetos:
        xml += ['  <object id="%s">' % oid,
                '    <metadata key="name" value="%s"/>' % nom,
                '    <metadata key="extruder" value="1"/>']
        for clave, ajustes in POR_OBJETO.items():
            if clave in nom:
                xml += ['    <metadata key="%s" value="%s"/>' % kv
                        for kv in sorted(ajustes.items())]
        xml += ['    <part id="1" subtype="normal_part">',
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
    """Copia project_settings.config de `ajustes` (un .3mf de Bambu Studio)
    con LAMINADO encima, y declara el .3mf de Bambu Studio: sin el metadato
    Application el laminador ignora los ajustes y usa los genéricos."""
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


def gramos(m):
    return round(abs(m.volumen()) / 1000.0 * DENSIDAD, 1)


def juego_armado(vaso_m, ban, centros, piso):
    j = M.Malla()
    j.unir(ban)
    for c in centros:
        j.unir(vaso_m.trasladada(c, 0.0, piso))
    return j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=".")
    ap.add_argument("--nombre", default="Portacubiertos_Trenzado")
    for k, val in list(VASO.items()) + list(BANDEJA.items()):
        if k in ("alto", "piso"):
            continue
        ap.add_argument("--" + k.replace("_", "-"), dest=k, type=float, default=None)
    ap.add_argument("--alto-vaso", type=float, default=None)
    ap.add_argument("--alto-bandeja", type=float, default=None)
    ap.add_argument("--ajustes", default=str(AJUSTES_P2S),
                    help="otro .3mf del que copiar los ajustes de laminado ('' = ninguno)")
    a = ap.parse_args()

    v, b = dict(VASO), dict(BANDEJA)
    for dic in (v, b):
        for k in dic:
            val = getattr(a, k, None)
            if val is not None:
                dic[k] = val
    if b["largo"]:
        ajustar_al_largo(v, b)
    v["costillas"] = int(v["costillas"])
    if a.alto_vaso:
        v["alto"] = a.alto_vaso
    if a.alto_bandeja:
        b["alto"] = a.alto_bandeja

    vaso_m = vaso(v)
    ban, centros = bandeja(v, b)
    carpeta = Path(a.salida).expanduser()
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / (a.nombre + ".3mf")

    juego = juego_armado(vaso_m, ban, centros, b["piso"] + b["patas"])
    png = render.render(juego.v, juego.t, tam=512, suavizado=2,
                        direccion=render.vector_vista(20, 24),
                        ruta=ruta.with_suffix(".png"))
    (bx0, by0, _), (bx1, by1, bz1) = ban.caja()
    r_max = v["radio_panza"]
    # Plato: la bandeja arriba, los vasos en fila abajo.
    piezas = [("bandeja", ban, PLATO / 2, 8 + (by1 - by0) / 2)]
    y_vasos = 8 + (by1 - by0) + 6 + r_max
    for i, x in enumerate(centros_de(len(centros), 2 * r_max + 6)):
        piezas.append(("vaso %d" % (i + 1), vaso_m, PLATO / 2 + x, y_vasos))
    notas = "%s · %d vasos + bandeja" % (a.nombre, len(centros))
    exportar.guardar_3mf(piezas, ruta, a.nombre, miniatura=png, notas=notas,
                         parametros=dict(v, **{"bandeja_" + k: x for k, x in b.items()},
                                         diseno="portacubiertos_trenzado"))
    if a.ajustes and Path(a.ajustes).exists():
        embeber_ajustes(ruta, a.ajustes)
    exportar.guardar_stl(piezas, ruta.with_suffix(".stl"), a.nombre)
    exportar.guardar_stl([("juego", juego, 0, 0)],
                         carpeta / (a.nombre + "_armado.stl"), a.nombre)

    gv, gb = gramos(vaso_m), gramos(ban)
    print("%s" % ruta)
    print("  Vaso     %.0f × %.0f mm, %d costillas a %.0f°  ≈ %s g (suma de sólidos encimados)"
          % (2 * r_max, v["alto"], v["costillas"], v["inclinacion"], gv))
    print("  Bandeja  %.1f × %.1f × %.0f mm  ≈ %s g de malla maciza (el relleno"
          " al 10 %% la deja en menos de la mitad)" % (bx1 - bx0, by1 - by0, bz1, gb))
    print("  Juego    %.1f × %.1f × %.1f mm armado"
          % tuple(hi - lo for lo, hi in zip(*juego.caja())))
    print("  Aristas sueltas bandeja: %d" % ban.aristas_sueltas())


if __name__ == "__main__":
    main()
