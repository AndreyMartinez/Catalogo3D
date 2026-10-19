#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portacepillos doble de pared delgada: dos vasos acanalados sobre una bandeja.

Es el mismo producto que el Portacepillos01O (dos vasos sobre un plato) pero
hecho como el florero, que imprime en horas y no en días: pared de ~1.2 mm en
vez de 4.7, bandeja de plato con borde en vez de losa. Los vasos salen del
motor de siempre (cuerpo.construir); lo único nuevo es la bandeja doble.

    python3 portacepillos_rapido.py --salida /ruta --juegos 2 --nombre MiPieza

Cualquier parámetro del motor se puede pasar como --clave valor (ver crear.py).
Por defecto copia los ajustes de laminado del florero (`--ajustes`), que son
con los que se midió el tiempo.

Lo que lo hace rápido, medido con el laminador de Bambu Studio sobre el
plato con dos juegos (4 vasos + 2 bandejas), con los ajustes del florero:

    Portacepillos01O actual (pared 4.7 mm, bandeja losa)     ~26 h   ~380 g
    pared 1.2 mm, lisa por dentro                              9.2 h    169 g
    pared 1.0 mm, la cara interior copia el relieve,
      pisos de 1.2 mm                                          3.8 h    136 g
    + resolución del laminador 0.012 → 0.05 mm                 3.1 h    136 g

El salto grande no es el peso sino el número de trazos. Una pared de 1.2 mm
con el relieve por fuera y liso por dentro no se parte en dos hilos limpios:
deja 40 mil trazos sueltos por plato, cada uno con su retracción. Con 1.0 mm y
la cara interior copiando el relieve (pared_forma = sigue) quedan 3 mil. Los
pisos van a 1.2 mm porque son las seis capas sólidas (3 de piso + 3 de techo);
con 2.0 mm el laminador dejaba un hueco en medio y lo puenteaba.

El .3mf tiene que declararse de Bambu Studio (metadato Application) o el
laminador ignora los ajustes que lleva y usa los genéricos, 4 veces más lentos.
"""

import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import disenos                                    # noqa: E402
from nucleo import cuerpo, exportar, malla as M, render   # noqa: E402

PLATO = 256.0

# Lo que se le pide al vaso: recto, 62 × 105 mm, estría de cresta plana (la del
# Portacepillos01O) pero más junta y más honda —cada 3 mm, 1.2 mm de surco— y
# la boca cerrada con un aro liso a ras de las crestas, como remata el original.
#
# La pared va lisa por dentro y se imprime con UN perímetro, que en el
# laminador son dos hilos: uno sigue la estría por fuera y otro va liso por
# dentro. Se tocan en el fondo de cada surco y cada cresta queda como un
# cajoncito hueco, como cartón corrugado. Por eso la pared mide 1.9 con
# hilos de 0.65: en el surco quedan 1.3 mm, justo los dos hilos pegados.
# Engrosar es subir las dos cosas juntas: 1.6/0.5 se sentía demasiado liviano,
# 1.75/0.58 y 1.9/0.65 dan el mismo tiempo (~6.5 h) y con 0.65 la estría sigue
# igual de honda en el G-code (1.24 mm de cresta a valle, ejes a 0.62 mm en el
# fondo). El piso del vaso va a 2.4 por el peso en mano (macizo con las 7
# capas de fondo de LAMINADO). Con más perímetros no
# caben en el surco, se parten en una isla por estría y el plato se va de
# 6 h a 15-26 h. Con el generador clásico los dos hilos quedan separados
# 0.3 mm (dos cáscaras sueltas): tiene que ser Arachne.
VASO = {
    "contorno": "circulo", "ancho": 62, "fondo": 62, "alto": 105,
    "acabado": "canal", "onda_amplitud": 0.6, "onda_paso": 3.0,
    "perfil": "recto",
    "pared": 1.9, "pared_forma": "lisa", "piso": 2.4, "ranuras": 1,
    "base_redondeo": 6, "grano": 0.5, "segmentos": 480,
    "acabado_desvanece": 3, "acabado_cierre": 1,
}


def capsula(largo, ancho, lados=96):
    """Óvalo de extremos redondos de largo × ancho, centrado en el origen."""
    r = ancho / 2.0
    media = largo / 2.0 - r
    pts = []
    n = lados // 2
    for i in range(n + 1):                       # semicírculo derecho
        a = -math.pi / 2 + math.pi * i / n
        pts.append((media + r * math.cos(a), r * math.sin(a)))
    for i in range(n + 1):                       # semicírculo izquierdo
        a = math.pi / 2 + math.pi * i / n
        pts.append((-media + r * math.cos(a), r * math.sin(a)))
    return pts


def anillo(cx, cy, r_int, r_ext, lados=96):
    return (M.circulo_puntos(cx, cy, r_ext, lados),
            [M.circulo_puntos(cx, cy, r_int, lados)])


def media_luna(cx, r, grueso, hacia, lados=96):
    """Aro de asiento solo del lado que mira al otro vaso (`hacia` = +1 o -1),
    como luna: `grueso` mm en el centro y afinándose a cero donde topa con el
    borde. Es la franja entre el círculo del vaso (radio r) y otro de radio
    r + grueso/2 corrido grueso/2 hacia el centro, cortada en x = cx."""
    t = grueso / 2.0
    co, ro = cx + hacia * t, r + t
    yo = math.sqrt(ro * ro - t * t)
    mira = 0.0 if hacia > 0 else math.pi           # ángulo que apunta al centro

    def barrido(a, b):                             # de a a b pasando por `mira`
        ida = (mira - a) % (2 * math.pi)
        vuelta = (b - mira) % (2 * math.pi)
        if ida + vuelta > 2 * math.pi - 1e-9:
            ida = -((a - mira) % (2 * math.pi))
            vuelta = -((mira - b) % (2 * math.pi))
        return [a + (ida + vuelta) * i / lados for i in range(lados + 1)]

    pts = [(co + ro * math.cos(a), ro * math.sin(a))
           for a in barrido(math.atan2(yo, cx - co), math.atan2(-yo, cx - co))]
    pts += [(cx + r * math.cos(a), r * math.sin(a))
            for a in barrido(-math.pi / 2, math.pi / 2)]
    return M.orientar(pts)


def bandeja(radio_vaso, piso=2.4, holgura=0.6, aro_alto=3.0, aro_grueso=1.2,
            hueco=1.6, borde_alto=7.0, borde_pared=3.0):
    """Plato de cápsula con borde (el de la primera versión) que abraza la
    mitad de afuera de cada vaso; adentro, solo una media luna de aro del lado
    que mira al otro vaso.

    Devuelve (malla, centros_x). Sin hueco entre aro y borde el plato queda
    tan angosto como los vasos más el borde. El borde de 3 mm y el piso de 2.4
    son para que pese en mano: salen macizos solo con los ajustes de
    POR_OBJETO y `bottom_shell_layers` (con un perímetro el borde salía como
    dos hilos sueltos y hueco en medio)."""
    r = radio_vaso + holgura                      # radio del asiento del vaso
    sep = r + aro_grueso + hueco / 2.0            # centro de cada vaso
    exterior = capsula(2 * (sep + r + borde_pared), 2 * (r + borde_pared))
    m = M.Malla()
    m.unir(M.placa(exterior, [], 0.0, piso))
    m.unir(M.placa(exterior, [capsula(2 * (sep + r), 2 * r)],
                   piso - 0.01, borde_alto))
    centros = (-sep, sep)
    for cx in centros:
        luna = media_luna(cx, r, aro_grueso, 1 if cx < 0 else -1)
        m.unir(M.placa(luna, [], piso - 0.01, piso + aro_alto))
    return m.normalizar(), centros


def construir(p_vaso):
    malla_vaso, datos = cuerpo.construir(disenos.normalizar(p_vaso))
    (x0, y0, z0), (x1, y1, z1) = malla_vaso.caja()
    return malla_vaso, datos, ((x0 + x1) / 2, (y0 + y1) / 2, z0, z1)


def radio_en_la_base(malla_vaso):
    """El radio más ancho del vaso en sus primeros 8 mm (donde asienta)."""
    (_, _, z0), _ = malla_vaso.caja()
    return max(math.hypot(x, y) for x, y, z in malla_vaso.v if z < z0 + 8.0)


def disponer(vaso, bandeja_m, juegos, ancho_b, fondo_b, ancho_v):
    """Coloca los juegos en el plato. Bandejas apiladas arriba a la izquierda;
    los vasos van en la columna que queda a su derecha y, si no caben ahí, en
    una fila debajo. Devuelve la lista de (nombre, malla, dx, dy)."""
    margen, hueco = 8.0, 4.0
    piezas = []
    y = margen + fondo_b / 2.0
    for j in range(juegos):
        piezas.append(("bandeja %d" % (j + 1), bandeja_m,
                       margen + ancho_b / 2.0, y))
        y += fondo_b + hueco
    fin_y = margen + juegos * fondo_b + (juegos - 1) * hueco   # donde terminan
    fin_x = margen + ancho_b
    r, paso = ancho_v / 2.0, ancho_v + hueco
    sitios = []
    x = fin_x + hueco + r                 # columna a la derecha de las bandejas
    yy = margen + r
    while x + r <= PLATO - margen and yy + r <= fin_y:
        sitios.append((x, yy))
        yy += paso
    yy = fin_y + hueco + r                # fila debajo de las bandejas
    while yy + r <= PLATO - margen:
        xx = margen + r
        while xx + r <= PLATO - margen:
            sitios.append((xx, yy))
            xx += paso
        yy += paso
    n = 2 * juegos
    if len(sitios) < n:
        raise SystemExit("No caben %d vasos con %d bandejas en el plato." % (n, juegos))
    for k in range(n):
        piezas.append(("vaso %d" % (k + 1), vaso, sitios[k][0], sitios[k][1]))
    return piezas


AJUSTES_FLORERO = (Path.home() / "Desktop" / "own design 3d"
                   / "General_Vases_print_profile(5).3mf")
RESOLUCION = "0.05"      # mm; el valor de fábrica (0.012) deja ~1 millón de trazos
# Ver la nota de VASO: un perímetro, Arachne, y sin los rellenos de hueco de
# menos de 2 mm que dejaba cada cresta (eran 300 trazos sueltos por capa).
LAMINADO = {"wall_loops": "1", "wall_generator": "arachne",
            "filter_out_gap_fill": "2", "outer_wall_line_width": "0.65",
            "bottom_shell_layers": "7"}
# Ajustes que solo lleva la bandeja (por nombre del objeto): con un perímetro su
# borde de 3 mm salía como dos hilos sueltos; con 3 sale macizo. A los vasos
# no se les puede subir (ver la nota de VASO).
POR_OBJETO = {"bandeja": {"wall_loops": "3"}}


def ajustes_por_objeto(modelo):
    """Metadata/model_settings.config con un bloque por objeto del modelo (los
    ids tienen que coincidir uno a uno) y los ajustes de POR_OBJETO."""
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


def guardar(piezas, ruta, nombre, ajustes=None, miniatura=None, notas=None):
    """Escribe el .3mf. Con `ajustes` (otro .3mf de Bambu Studio) copia sus
    ajustes de laminado, que es lo que hace que salga con el perfil rápido."""
    exportar.guardar_3mf(piezas, ruta, nombre, miniatura=miniatura,
                         notas=notas or nombre)
    if not ajustes:
        return
    with zipfile.ZipFile(ajustes) as z:
        cfg = json.loads(z.read("Metadata/project_settings.config"))
    cfg["resolution"] = RESOLUCION
    cfg.update(LAMINADO)
    cambios = {"resolution"} | set(LAMINADO)
    dif = cfg.get("different_settings_to_system") or [""]
    dif[0] = ";".join(sorted(set(filter(None, dif[0].split(";"))) | cambios))
    cfg["different_settings_to_system"] = dif
    with zipfile.ZipFile(ruta) as z:
        todo = {n: z.read(n) for n in z.namelist()}
    todo["Metadata/project_settings.config"] = json.dumps(cfg, indent=4).encode()
    # Sin estas dos líneas Bambu Studio no toma el proyecto por suyo e ignora
    # project_settings.config: lamina con sus ajustes genéricos (60 mm/s,
    # aceleración 500) y el tiempo sale hasta 4 veces peor.
    modelo = todo["3D/3dmodel.model"].decode("utf-8")
    modelo = modelo.replace(
        '<metadata name="Title">',
        '<metadata name="Application">BambuStudio-02.07.01.62</metadata>\n'
        '<metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        '<metadata name="Title">', 1)
    todo["3D/3dmodel.model"] = modelo.encode("utf-8")
    todo["Metadata/model_settings.config"] = ajustes_por_objeto(modelo)
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in todo.items():
            z.writestr(n, b)


def miniatura(vaso, ban, centros, ruta_png, piso=2.4):
    """Un juego armado —los dos vasos sobre su bandeja— visto en tres cuartos."""
    juego = M.Malla()
    juego.unir(ban)
    for c in centros:
        juego.unir(vaso.trasladada(c, 0.0, piso))
    return render.render(juego.v, juego.t, tam=512, suavizado=2,
                         direccion=render.vector_vista(25, 28), ruta=ruta_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=".")
    ap.add_argument("--nombre", default="PortacepillosRapido")
    ap.add_argument("--juegos", type=int, default=2)
    ap.add_argument("--ajustes", default=str(AJUSTES_FLORERO),
                    help="otro .3mf del que copiar los ajustes de laminado ('' = ninguno)")
    claves = list(dict.fromkeys(list(VASO) + [s["clave"] for s in disenos.PARAMETROS
                                              if s["tipo"] != "trazo"]))
    for k in claves:
        ap.add_argument("--" + k.replace("_", "-"), dest=k, default=None)
    a = ap.parse_args()

    p = dict(VASO)
    for k in claves:
        if getattr(a, k) is not None:
            p[k] = getattr(a, k)
    malla_vaso, datos, (cx, cy, z0, _) = construir(p)
    r_base = radio_en_la_base(malla_vaso)
    ban, centros = bandeja(r_base)
    (bx0, by0, _), (bx1, by1, _) = ban.caja()

    # Los vasos van sobre la bandeja en el .3mf: el motor los trae centrados.
    vaso = malla_vaso.trasladada(-cx, -cy, -z0)
    r_max = max(math.hypot(x - cx, y - cy) for x, y, _ in malla_vaso.v)
    piezas = disponer(vaso, ban, a.juegos, bx1 - bx0, by1 - by0, 2 * r_max)
    ruta = Path(a.salida).expanduser() / (a.nombre + ".3mf")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    png = miniatura(vaso, ban, centros, ruta.with_suffix(".png"))
    ajustes = a.ajustes if a.ajustes and Path(a.ajustes).exists() else None
    guardar(piezas, ruta, a.nombre, ajustes, png,
            "%s · 2 vasos + bandeja por juego · %d juegos" % (a.nombre, a.juegos))

    gv, gb = datos["gramos"], round(ban.volumen() / 1000.0 * 1.24, 1)
    print("%s: %d juegos (%d vasos + %d bandejas)" % (ruta.name, a.juegos,
                                                       2 * a.juegos, a.juegos))
    print("  Vaso     %s mm  ≈ %s g" % ("×".join(str(datos[k]) for k in
                                           ("ancho", "fondo", "alto")), gv))
    print("  Bandeja  %.0f × %.0f × %.0f mm  ≈ %s g" % (bx1 - bx0, by1 - by0,
                                                       ban.caja()[1][2], gb))
    print("  Un juego ≈ %.0f g" % (2 * gv + gb))
    print("  →", ruta)


if __name__ == "__main__":
    main()
