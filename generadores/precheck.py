#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hoja de vistas de una pieza desde todos los lados, antes de armar el 3MF.

    python3 precheck.py pieza.3mf
    python3 precheck.py pieza.stl --salida vistas.png
    python3 precheck.py pieza.3mf --zona 40,70     # acercamiento entre z=40 y 70 mm

Arma un mosaico 3×3 con perspectiva, en este orden:

    frente           3/4 delante der.   costado der.
    3/4 atrás der.   atrás              3/4 atrás izq.
    costado izq.     3/4 delante izq.   desde arriba

Con `--zona` agrega una cuarta fila: la franja de alturas indicada vista de
frente, de 3/4 y de atrás, para revisar de cerca lo que se acaba de tocar.

De un .3mf toma la primera pieza del plato (con sus transformaciones), no
las copias: lo que se juzga es la forma. `--todo` renderiza el plato entero.
Solo biblioteca estándar.
"""

import argparse
import struct
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nucleo import render                            # noqa: E402

# (nombre, giro, elevación). Giro 0 es el frente (desde -Y), crece horario.
VISTAS = [
    ("frente", 0, 12), ("3/4 delante der.", 45, 28), ("costado der.", 90, 12),
    ("3/4 atrás der.", 135, 28), ("atrás", 180, 12), ("3/4 atrás izq.", 225, 28),
    ("costado izq.", 270, 12), ("3/4 delante izq.", 315, 28), ("desde arriba", 0, 78),
]
VISTAS_ZONA = [("zona frente", 0, 15), ("zona 3/4", 40, 30), ("zona atrás", 180, 15)]
SEPARACION = 6


# ── Leer la malla ──────────────────────────────────────────────────────────

def _matriz(texto):
    if not texto:
        return None
    m = [float(x) for x in texto.split()]
    return m if len(m) == 12 else None


def _aplicar(m, v):
    if m is None:
        return v
    x, y, z = v
    return (x * m[0] + y * m[3] + z * m[6] + m[9],
            x * m[1] + y * m[4] + z * m[7] + m[10],
            x * m[2] + y * m[5] + z * m[8] + m[11])


def _componer(a, b):
    """Primero a, luego b (convención fila-vector del 3MF)."""
    if a is None:
        return b
    if b is None:
        return a
    r = [0.0] * 12
    for i in range(3):
        for j in range(3):
            r[i * 3 + j] = sum(a[i * 3 + k] * b[k * 3 + j] for k in range(3))
    for j in range(3):
        r[9 + j] = sum(a[9 + k] * b[k * 3 + j] for k in range(3)) + b[9 + j]
    return r


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _attr(el, nombre):
    for k, v in el.attrib.items():
        if _local(k) == nombre:
            return v
    return None


def leer_3mf(ruta, todo=False):
    zf = zipfile.ZipFile(ruta)
    objetos = {}   # (archivo, id) -> elemento <object>
    raiz = None
    for nombre in zf.namelist():
        if not nombre.endswith(".model"):
            continue
        arbol = ET.fromstring(zf.read(nombre))
        clave = "/" + nombre.lstrip("/")
        if nombre == "3D/3dmodel.model":
            raiz = arbol
        for el in arbol.iter():
            if _local(el.tag) == "object":
                objetos[(clave, el.get("id"))] = el
    if raiz is None:
        sys.exit("El .3mf no tiene 3D/3dmodel.model")

    vertices, triangulos = [], []

    def agregar(archivo, oid, m):
        obj = objetos.get((archivo, oid))
        if obj is None:
            return
        for hijo in obj:
            t = _local(hijo.tag)
            if t == "mesh":
                base = len(vertices)
                for el in hijo.iter():
                    lt = _local(el.tag)
                    if lt == "vertex":
                        vertices.append(_aplicar(m, (float(el.get("x")),
                                                     float(el.get("y")),
                                                     float(el.get("z")))))
                    elif lt == "triangle":
                        triangulos.append((base + int(el.get("v1")),
                                           base + int(el.get("v2")),
                                           base + int(el.get("v3"))))
            elif t == "components":
                for c in hijo:
                    destino = _attr(c, "path") or archivo
                    agregar(destino, c.get("objectid"),
                            _componer(_matriz(c.get("transform")), m))

    items = [el for el in raiz.iter() if _local(el.tag) == "item"]
    if not items:
        sys.exit("El .3mf no tiene piezas en <build>")
    for it in (items if todo else items[:1]):
        agregar("/3D/3dmodel.model", it.get("objectid"), _matriz(it.get("transform")))
    return vertices, triangulos


def leer_stl(ruta):
    datos = Path(ruta).read_bytes()
    vertices, triangulos = [], []
    n = struct.unpack("<I", datos[80:84])[0] if len(datos) >= 84 else 0
    if len(datos) == 84 + n * 50:
        for i in range(n):
            base = 84 + i * 50 + 12
            for k in range(3):
                vertices.append(struct.unpack("<3f", datos[base + k * 12:base + k * 12 + 12]))
            triangulos.append((3 * i, 3 * i + 1, 3 * i + 2))
    else:
        for linea in datos.decode("utf-8", "replace").splitlines():
            p = linea.split()
            if p and p[0] == "vertex":
                vertices.append(tuple(float(x) for x in p[1:4]))
        triangulos = [(i, i + 1, i + 2) for i in range(0, len(vertices) - 2, 3)]
    return vertices, triangulos


def leer(ruta, todo=False):
    if str(ruta).lower().endswith(".stl"):
        return leer_stl(ruta)
    return leer_3mf(ruta, todo)


def recortar(vertices, triangulos, zmin, zmax):
    """Triángulos con algún vértice dentro de la franja de alturas."""
    t = [tr for tr in triangulos
         if any(zmin <= vertices[i][2] <= zmax for i in tr)]
    usados = sorted({i for tr in t for i in tr})
    nuevo = {v: k for k, v in enumerate(usados)}
    return ([vertices[i] for i in usados],
            [(nuevo[a], nuevo[b], nuevo[c]) for a, b, c in t])


# ── Mosaico ────────────────────────────────────────────────────────────────

def mosaico(cuadros, columnas, tam):
    filas = (len(cuadros) + columnas - 1) // columnas
    ancho = columnas * tam + (columnas + 1) * SEPARACION
    alto = filas * tam + (filas + 1) * SEPARACION
    lienzo = bytearray(bytes((255, 255, 255)) * (ancho * alto))
    for k, px in enumerate(cuadros):
        ox = SEPARACION + (k % columnas) * (tam + SEPARACION)
        oy = SEPARACION + (k // columnas) * (tam + SEPARACION)
        for y in range(tam):
            i = ((oy + y) * ancho + ox) * 3
            lienzo[i:i + tam * 3] = px[y * tam * 3:(y + 1) * tam * 3]
    return ancho, alto, lienzo


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pieza", help=".3mf o .stl")
    ap.add_argument("--salida", help="PNG de salida (por omisión, <pieza>.precheck.png)")
    ap.add_argument("--tam", type=int, default=420, help="lado de cada vista en px")
    ap.add_argument("--suavizado", type=int, default=1, help="2 = más fino y 4× más lento")
    ap.add_argument("--zona", help="zmin,zmax en mm para la fila de acercamiento")
    ap.add_argument("--todo", action="store_true", help="todas las piezas del plato")
    a = ap.parse_args()

    inicio = time.time()
    v, t = leer(a.pieza, a.todo)
    if not t:
        sys.exit("No encontré triángulos en " + a.pieza)
    xs, ys, zs = zip(*v)
    print("%s: %d triángulos, %.1f × %.1f × %.1f mm"
          % (Path(a.pieza).name, len(t), max(xs) - min(xs), max(ys) - min(ys),
             max(zs) - min(zs)))

    cuadros = []
    for nombre, giro, elev in VISTAS:
        cuadros.append(render.render(v, t, tam=a.tam, suavizado=a.suavizado,
                                     direccion=render.vector_vista(giro, elev),
                                     crudo=True))
    if a.zona:
        zmin, zmax = (float(x) for x in a.zona.split(","))
        vz, tz = recortar(v, t, zmin, zmax)
        if tz:
            for nombre, giro, elev in VISTAS_ZONA:
                cuadros.append(render.render(vz, tz, tam=a.tam, suavizado=a.suavizado,
                                             direccion=render.vector_vista(giro, elev),
                                             crudo=True))
        else:
            print("La zona %s no tiene triángulos; la omito." % a.zona)

    salida = a.salida or str(Path(a.pieza).with_suffix("")) + ".precheck.png"
    ancho, alto, px = mosaico(cuadros, 3, a.tam)
    render.escribir_png(salida, ancho, alto, px)
    print("Orden: " + " · ".join(n for n, _, _ in VISTAS)
          + (" · " + " · ".join(n for n, _, _ in VISTAS_ZONA) if len(cuadros) > 9 else ""))
    print("Listo en %.0f s → %s" % (time.time() - inicio, salida))


if __name__ == "__main__":
    main()
