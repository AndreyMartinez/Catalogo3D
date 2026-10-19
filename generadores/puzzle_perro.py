#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Puzzle de comida para perro: disco macizo de una pieza con relieve suave.

La croqueta cae entre el relieve y el perro la saca con la lengua y el hocico.
Sin piezas móviles ni soporte: la cara de arriba es un campo de alturas sobre
una base plana, así que nada queda en voladizo.

    python3 puzzle_perro.py --concepto ondas --salida /ruta
    python3 puzzle_perro.py --todos --salida /ruta

Conceptos: ondas (anillos concéntricos que suben hacia el centro), petalos
(valles radiales, roseta), guijarros (domos en filotaxis).
"""

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path

GEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GEN))

from nucleo import exportar, malla as M, render   # noqa: E402

DENSIDAD_PETG = 1.27
CENTRO_PLATO = 128.0
AJUSTES = Path.home() / "Desktop" / "own design 3d" / "General_Vases_print_profile(5).3mf"
# Pieza maciza: perímetros y relleno normales, no los del florero.
LAMINADO = {"resolution": "0.05", "wall_loops": "2", "sparse_infill_density": "12%",
            "top_shell_layers": "5", "bottom_shell_layers": "4", "spiral_mode": "0"}

BASE = {
    "radio": 115.0,        # Ø230: perro mediano, cabe en la placa de 256
    "piso": 3.0,           # altura del fondo de los valles
    "relieve": 18.0,       # alto máximo del relieve sobre el piso
    "labio_ancho": 13.0,   # borde perimetral redondeado
    "labio_alto": 24.0,
    "chaflan": 1.2,        # chaflán de 45° al pie, contra la pata de elefante
    "anillos": 300,        # resolución radial
    "gajos": 360,          # resolución angular
}

CONCEPTOS = {
    "ondas": dict(BASE, onda=26.0, cresta=2.2),
    "petalos": dict(BASE, petalos=11, filo=2.6, giro=0.35),
    "guijarros": dict(BASE, domos=30, domo_radio=15.5, domo_paso=28.5),
}


def suave(t):
    """Escalón suave de 0 a 1 (smoothstep)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def labio(r, p):
    """Altura del borde: un cuarto de óvalo que sube desde el piso y cae
    redondeado hacia afuera."""
    r_in = p["radio"] - p["labio_ancho"]
    if r <= r_in:
        return None
    u = (r - r_in) / p["labio_ancho"]          # 0 adentro, 1 en la orilla
    alto = p["labio_alto"] - p["piso"]
    # sube con un coseno (sin arista) y redondea la orilla exterior
    sube = 0.5 - 0.5 * math.cos(math.pi * min(1.0, u / 0.55))
    cae = math.sqrt(max(0.0, 1 - ((u - 0.55) / 0.45) ** 2)) if u > 0.55 else 1.0
    return p["piso"] + alto * sube * (0.82 + 0.18 * cae) if u <= 0.55 else \
        p["piso"] + alto * (0.82 + 0.18 * cae) * cae ** 0.35


def relieve(concepto, r, th, p):
    """Altura sobre el piso, de 0 a 1, del relieve central."""
    r_in = p["radio"] - p["labio_ancho"]
    if concepto == "ondas":
        # Anillos con cresta afinada; más altos hacia el centro (más difícil).
        fase = (r / p["onda"]) % 1.0
        ola = 0.5 + 0.5 * math.cos(2 * math.pi * fase)
        if r < p["onda"] / 2:            # el centro es un domo ancho, no un pico
            return 0.42 * ola ** 0.5
        c = ola ** p["cresta"]
        return c * (0.45 + 0.55 * (1 - r / r_in)) * (1 - suave((r - r_in + 12) / 12))
    if concepto == "petalos":
        # Crestas radiales que giran un poco, se apagan al centro.
        ang = p["petalos"] * (th + p["giro"] * r / r_in)
        c = (0.5 + 0.5 * math.cos(ang)) ** p["filo"]
        apaga = 1 - suave((r - r_in + 24) / 22)   # foso antes del borde
        return (c * suave((r - 14) / 30) + 0.45 * (1 - suave(r / 24))) * apaga
    if concepto == "guijarros":
        mejor = 0.0
        x, y = r * math.cos(th), r * math.sin(th)
        for cx, cy, h in p["_domos"]:
            d = math.hypot(x - cx, y - cy) / p["domo_radio"]
            if d < 1:
                mejor = max(mejor, h * (1 - d * d) ** 1.5)
        return mejor
    raise ValueError(concepto)


def domos(p):
    """Centros en filotaxis (ángulo áureo), alturas que bajan hacia afuera."""
    r_in = p["radio"] - p["labio_ancho"] - p["domo_radio"] * 0.6
    sal, k = [], 0
    while len(sal) < p["domos"] and k < 400:
        r = p["domo_paso"] * 0.56 * math.sqrt(k + 0.5)
        if r > r_in:
            break
        a = k * math.radians(137.508)
        sal.append((r * math.cos(a), r * math.sin(a), 0.55 + 0.45 * (1 - r / r_in) * (0.7 + 0.3 * math.cos(3 * a))))
        k += 1
    return sal


def altura(concepto, r, th, p):
    z = labio(r, p)
    if z is not None:
        return z
    return p["piso"] + p["relieve"] * relieve(concepto, r, th, p)


def construir(concepto, p=None):
    p = dict(p or CONCEPTOS[concepto])
    if concepto == "guijarros":
        p["_domos"] = domos(p)
    R, nr, nt, ch = p["radio"], int(p["anillos"]), int(p["gajos"]), p["chaflan"]
    m = M.Malla()
    centro = m.punto(0.0, 0.0, altura(concepto, 0.0, 0.0, p))
    anillos = []
    for i in range(1, nr + 1):
        r = R * i / nr
        fila = []
        for j in range(nt):
            th = 2 * math.pi * j / nt
            fila.append(m.punto(r * math.cos(th), r * math.sin(th), altura(concepto, r, th, p)))
        anillos.append(fila)
    # cara de arriba (vista desde arriba, antihorario)
    a0 = anillos[0]
    for j in range(nt):
        m.cara(centro, a0[j], a0[(j + 1) % nt])
    for i in range(nr - 1):
        a, b = anillos[i], anillos[i + 1]
        for j in range(nt):
            k = (j + 1) % nt
            m.quad(a[j], b[j], b[k], a[k])
    # costado: orilla del labio → pared vertical → chaflán → base
    orilla = anillos[-1]
    z_pared = ch
    pie, base = [], []
    for j in range(nt):
        th = 2 * math.pi * j / nt
        c, s = math.cos(th), math.sin(th)
        pie.append(m.punto(R * c, R * s, z_pared))
        base.append(m.punto((R - ch) * c, (R - ch) * s, 0.0))
    for j in range(nt):
        k = (j + 1) % nt
        m.quad(orilla[j], pie[j], pie[k], orilla[k])
        m.quad(pie[j], base[j], base[k], pie[k])
    fondo = m.punto(0.0, 0.0, 0.0)
    for j in range(nt):
        m.cara(fondo, base[(j + 1) % nt], base[j])
    m.normalizar()
    datos = {"ancho": round(2 * R, 1), "alto": round(max(v[2] for v in m.v), 1),
             "volumen_cm3": round(m.volumen() / 1000, 1),
             "sueltas": m.aristas_sueltas()}
    return m, datos


def guardar(m, ruta, nombre, png=None, parametros=None):
    piezas = exportar.acomodar([(nombre, m)], CENTRO_PLATO)
    exportar.guardar_3mf(piezas, ruta, nombre, miniatura=png, notas=nombre,
                         parametros=parametros)
    aplicar_ajustes(ruta)


def aplicar_ajustes(ruta):
    """Copia el perfil P2S del florero con LAMINADO encima y declara el .3mf
    de Bambu Studio, para que el laminador por CLI lo tome tal cual."""
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
    ap.add_argument("--concepto", default="ondas", choices=sorted(CONCEPTOS))
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--salida", default=".")
    ap.add_argument("--color", default="223,214,201")
    a = ap.parse_args()
    color = tuple(int(c) for c in a.color.split(","))
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    for c in (sorted(CONCEPTOS) if a.todos else [a.concepto]):
        m, d = construir(c)
        nombre = "PuzzlePerro_" + c
        png = render.render(m.v, m.t, tam=512, suavizado=2, color=color,
                            direccion=render.vector_vista(20, 38),
                            ruta=salida / (nombre + ".png"))
        guardar(m, salida / (nombre + ".3mf"), nombre, png, dict(CONCEPTOS[c], concepto=c))
        print(c, json.dumps(d))


if __name__ == "__main__":
    main()
