#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Escritura de .3mf y .stl. Solo Python 3 estándar.

El .3mf que sale de aquí lleva adentro los parámetros con los que se generó.
No es adorno: sin ellos, una pieza guardada es una malla y nada más, y
volverla a sacar con el motor mejorado obliga a adivinar de qué valores
salió midiendo la propia malla. Se guardan como metadato del 3MF, que
Bambu Studio ignora sin quejarse.
"""

import json
import math
import struct
import zipfile

# El metadato donde viajan los parámetros. Con prefijo para no chocar con los
# que el propio formato define ni con los que mete el laminador.
CLAVE_PARAMETROS = "Catalogo3D:parametros"

TIPOS = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
<Default Extension="png" ContentType="image/png"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rel0" Target="/3D/3dmodel.model" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
<Relationship Id="rel1" Target="/Metadata/plate_1.png" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>
</Relationships>"""


def _escapar(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def acomodar(piezas, centro, hueco=12.0):
    """Reparte las piezas en fila sobre la placa, centradas en `centro`.
    Cada pieza sale como (nombre, malla, dx, dy)."""
    cajas = [m.caja() for _, m in piezas]
    anchos = [c[1][0] - c[0][0] for c in cajas]
    total = sum(anchos) + hueco * (len(piezas) - 1)
    x = centro - total / 2.0
    salida = []
    for (nombre, m), (mn, mx), ancho in zip(piezas, cajas, anchos):
        salida.append((nombre, m,
                       x + ancho / 2.0 - (mn[0] + mx[0]) / 2.0,
                       centro - (mn[1] + mx[1]) / 2.0))
        x += ancho + hueco
    return salida


def guardar_3mf(piezas, ruta, nombre, miniatura=None, notas=None,
                parametros=None):
    """`piezas` es una lista de (nombre, malla, dx, dy). Cada una sale como un
    objeto aparte, así el bote y su tapa se pueden mover y laminar por
    separado en Bambu Studio.

    `parametros` es el diccionario con el que se construyó la pieza. Va dentro
    del archivo para que se pueda volver a generar tal cual más adelante."""
    partes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<model unit="millimeter" xml:lang="es-MX" '
              'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">',
              '<metadata name="Title">%s</metadata>' % _escapar(nombre),
              '<metadata name="Designer">Catálogo 3D</metadata>']
    if notas:
        partes.append('<metadata name="Description">%s</metadata>' % _escapar(notas))
    if parametros:
        partes.append('<metadata name="%s">%s</metadata>'
                      % (CLAVE_PARAMETROS,
                         _escapar(json.dumps(parametros, sort_keys=True))))
    partes.append('<resources>')
    for idx, (nom, m, dx, dy) in enumerate(piezas, start=1):
        partes.append('<object id="%d" type="model" name="%s"><mesh><vertices>'
                      % (idx, _escapar("%s — %s" % (nombre, nom))))
        for x, y, z in m.v:
            partes.append('<vertex x="%.4f" y="%.4f" z="%.4f"/>' % (x + dx, y + dy, z))
        partes.append('</vertices><triangles>')
        for i, j, k in m.t:
            partes.append('<triangle v1="%d" v2="%d" v3="%d"/>' % (i, j, k))
        partes.append('</triangles></mesh></object>')
    partes.append('</resources><build>')
    for idx in range(1, len(piezas) + 1):
        partes.append('<item objectid="%d"/>' % idx)
    partes.append('</build></model>')

    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", "\n".join(partes))
        if miniatura:
            # El catálogo busca los PNG en Metadata/, así que la tarjeta sale
            # con imagen aunque la pieza todavía no se haya laminado.
            z.writestr("Metadata/plate_1.png", miniatura)


def guardar_stl(piezas, ruta, nombre):
    with open(ruta, "wb") as f:
        f.write(nombre.encode("ascii", "replace")[:79].ljust(80, b" "))
        f.write(struct.pack("<I", sum(len(m.t) for _, m, _, _ in piezas)))
        for _, m, dx, dy in piezas:
            _escribir_triangulos(f, m, dx, dy)


def _escribir_triangulos(f, m, dx, dy):
    for i, j, k in m.t:
        ax, ay, az = m.v[i]
        bx, by, bz = m.v[j]
        cx, cy, cz = m.v[k]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx
        largo = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        f.write(struct.pack("<3f", nx / largo, ny / largo, nz / largo))
        for x, y, z in ((ax, ay, az), (bx, by, bz), (cx, cy, cz)):
            f.write(struct.pack("<3f", x + dx, y + dy, z))
        f.write(struct.pack("<H", 0))


def leer_parametros(ruta):
    """Los parámetros guardados dentro de un .3mf, o None si no los trae.

    Devuelve None para todo lo que no haya salido de aquí —un modelo bajado
    de internet, un proyecto de Bambu Studio— en vez de inventar valores.
    """
    try:
        with zipfile.ZipFile(ruta) as z:
            nombre = next((n for n in z.namelist()
                           if n.endswith("3dmodel.model")), None)
            if nombre is None:
                return None
            # El metadato va en la cabecera, antes de la lista de vértices:
            # no hace falta leer treinta megas de malla para encontrarlo.
            with z.open(nombre) as fh:
                cabeza = fh.read(65536).decode("utf-8", "replace")
    except (zipfile.BadZipFile, OSError, StopIteration):
        return None
    marca = '<metadata name="%s">' % CLAVE_PARAMETROS
    i = cabeza.find(marca)
    if i < 0:
        return None
    j = cabeza.find("</metadata>", i)
    crudo = cabeza[i + len(marca):j]
    for viejo, nuevo in (("&quot;", '"'), ("&gt;", ">"), ("&lt;", "<"),
                         ("&amp;", "&")):
        crudo = crudo.replace(viejo, nuevo)
    try:
        datos = json.loads(crudo)
    except ValueError:
        return None
    return datos if isinstance(datos, dict) else None
