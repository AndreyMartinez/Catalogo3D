#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gato estriado: el cuerpo de jarrón estriado de la Jirafa estriada con la
cabeza del Gato Japandi (modelo comprado, «Katze Japandi» de ChrisB). La
cabeza se recorta del .3mf del Japandi por el cuello, se tapa abajo y se
monta sobre el cuello de la jirafa; el laminador une las dos piezas. La
malla del Japandi no se copia al repo: se lee de `own design 3d/`.

v1 con cabeza hecha a mano (bolitas de cachete y nariz) se rechazó: se veía
de juguete barato. Solo Python 3 estándar.

    python3 gato_estriado.py --salida ~/Desktop --stl     # para precheck
    python3 gato_estriado.py --salida ~/Desktop --3mf
"""

import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import jirafa_estriada as J                       # noqa: E402
from jirafa_estriada import M, render, exportar   # noqa: E402

JAPANDI = Path.home() / "Desktop" / "own design 3d" / "gato_japandi.3mf"

GATO = dict(J.JIRAFA)
GATO.update({
    # Recorte en el Japandi, en sus coordenadas crudas: la cintura más
    # angosta del cuello está en z ≈ 17.5 y la cabeza va hacia -y (la cola,
    # hacia +y, queda fuera con el filtro).
    "corte_z": 17.0,
    "corte_y_max": -5.0,
    # v3 cuello corto: el cuello de la jirafa se corta en 104 mm y la cabeza
    # crece 8 % para que su cuello (r 13.3 × 1.08) cuadre con el de abajo
    # (r 14.4). Se lee como gato sentado. v2 (cuello de jirafa, 174 mm):
    # perfil de la jirafa, nuca 140, escala 0.92, cintura en 135.
    "perfil": [(0, 23), (3, 25.5), (12, 28.5), (24, 30.5), (36, 31), (48, 29.5),
               (60, 25.5), (72, 20.5), (84, 16.5), (94, 14.8), (104, 14.4)],
    # El cuello cierra en una nuca que queda escondida dentro de la cabeza.
    # v5: cabeza 6 mm más abajo (nuca 110, cintura 103 en v3-v4) para que se
    # asiente sobre el cuerpo en vez de quedar sobre un cuellito.
    "nuca_z": 104.0,
    "cabeza_escala": 1.08,
    "cabeza_z": 97.0,               # a qué altura queda la cintura del corte
    # v4 cabeza más redonda: la bola del Japandi es achatada (41 × 42 × 34
    # en crudo). Se infla hacia un elipsoide de estos semiejes alrededor de
    # su centro; las orejas solo se mueven con su base, no se estiran.
    "bola_centro": (0.0, -32.7, 35.0),
    "bola_ejes": (20.6, 21.2, 17.0),      # como viene
    "bola_meta": (20.6, 21.2, 20.5),      # como queda; = bola_ejes la deja igual
    "bola_desde_z": (20.0, 28.0),         # de dónde a dónde entra el cambio
    # v6 frente liso. Pecho: las estrías del cuerpo se apagan al frente
    # (coseno del ángulo desde el frente donde empieza a alisar y donde ya es
    # liso). Cara: en la cabeza los surcos se rellenan hasta la cresta, con el
    # mismo criterio medido desde el centro de la bola. None = estriado.
    "pecho_liso": (0.55, 0.85),
    "pecho_hasta": 96.0,                  # arriba de aquí el cuello sigue estriado
    "cara_lisa": (0.45, 0.8),
    "cara_desde_z": 1.0,                  # sobre el corte, en crudo, donde empieza lo liso
    # v7: todo crece parejo hasta este alto para que acostado quepa en la
    # caja de 20 × 16 × 11 cm (v6: 146 mm; v7: 195 con 5 mm de holgura).
    "alto_final": 200.0,
})
# v8 (foto del gato negro, 10-22): cuerpo estriado completo, sin pecho liso;
# cabeza lisa al frente, arriba y a los lados, con las estrías solo en la
# nuca y en la parte baja de la cabeza, como gorguera.
GATO.update({
    "pecho_liso": None,
    "cara_lisa": (-0.55, -0.15),
    "cara_desde_z": 8.0,
})
# v9 (misma foto, «mira las paredes» y más económico): estrías como las de la
# foto, menos y más anchas, cresta redonda y surco en V delgado (v8: 26,
# forma 1.0). El cuello se abre en copa hasta la barbilla: la cabeza se
# apoya en él y casi no pide soporte (v8: 2 h 14 de soporte).
GATO.update({
    "estrias": 18,
    "estria_forma": 0.6,
    "perfil": [(0, 23), (3, 25.5), (12, 28.5), (24, 30.5), (36, 31), (48, 29.5),
               (60, 25.5), (72, 20.5), (82, 16.5), (90, 14.6), (97, 15.0),
               (103, 16.8), (108, 18.4)],
    "nuca_z": 112.0,
    "nuca_r": 18.0,
})

# v10 (acercamientos de la foto): la cara tiene relieve (puente de nariz,
# cuencas de ojos, hocico) y en la panza las estrías se cierran en punta y
# dejan una banda lisa antes de volver a abrirse hacia el cuello.
GATO.update({
    "panza_lisa": (40.0, 58.0, 66.0, 80.0),   # z crudo: empieza a cerrar, cerrado, abre, abierto
    "cara_relieve": {"nariz": 0.9, "ojos": 1.7, "hocico": 1.3},
})

# v11 (10-22): el relieve de la cara se rechazó («queda horrible») y se
# vuelve a la forma de la v7: 26 estrías, cuello sin copa, pecho liso y cara
# lisa al frente, a 200 mm. Las v8-v10 quedan arriba como historia.
GATO.update({
    "estrias": 26,
    "estria_forma": 1.0,
    "perfil": [(0, 23), (3, 25.5), (12, 28.5), (24, 30.5), (36, 31), (48, 29.5),
               (60, 25.5), (72, 20.5), (84, 16.5), (94, 14.8), (104, 14.4)],
    "nuca_z": 104.0,
    "nuca_r": J.JIRAFA["nuca_r"],
    "pecho_liso": (0.55, 0.85),
    "cara_lisa": (0.45, 0.8),
    "cara_desde_z": 1.0,
    "panza_lisa": None,
    "cara_relieve": None,
})

# v12 (render negro del usuario, 10-22): babero liso al frente desde la
# mitad de la panza hasta abajo del cuello; ahí los surcos del frente se
# cierran en punta. Costados, espalda y el cuello bajo la cabeza, estriados.
# El babero se hace por surcos enteros (entra o no) para que sus orillas
# sean un surco limpio, no un desvanecido.
GATO.update({
    "pecho_liso": None,
    "panza_lisa": (43.0, 57.0, 88.0, 97.0),   # z crudo: cierra, cerrado, abre, abierto
    "panza_frente": 0.62,                     # seno del ángulo: ±52° desde el frente
})

# Ajustes de laminado encima de los de la jirafa. Relleno relámpago: solo
# sostiene techos (aquí la coronilla), en vez de llenar todo el cuerpo.
LAMINADO = {
    "sparse_infill_pattern": "lightning",
    "sparse_infill_density": "10%",
    # Con el cuello en copa la barbilla se sostiene sola: a 30° no hay
    # soporte (a 50°, el de la jirafa, eran 2 h 12 y ~50 g; a 40°, 48 min).
    "support_threshold_angle": "30",
}


def cuerpo_gato(p, paso=0.6):
    """`cuello_recto` de la jirafa con el pecho liso al frente (-y)."""
    zc, rn = p["nuca_z"], p["nuca_r"]
    tramos = p["perfil"] + [(zc, rn)]
    sec = []
    for i in range(int(zc / paso) + 1):
        z = i * paso
        sec.append((0.0, z, 1.0, 0.0, J.catmull(tramos, z), 0.0, 0.0, 1.0))
    for k in range(1, 40):
        t = math.pi / 2 * k / 40
        sec.append((0.0, zc + rn * math.sin(t), 1.0, 0.0, rn * math.cos(t), 0.0, 0.0,
                    1 - J.suave(k / 20)))
    if p.get("panza_lisa"):
        return tubo_panza(p, sec, zc + rn)
    if not p.get("pecho_liso"):
        return J.tubo(p, sec, (0.0, zc + rn))
    # `tubo` alisa hacia +y; se arma así y se gira media vuelta. El alisado
    # se apaga en los 10 mm antes de `pecho_hasta` para que el cuello quede
    # estriado bajo la cabeza.
    alto = p["pecho_hasta"]
    pesos = [1 - J.suave((x[1] - (alto - 10)) / 10) for x in sec]
    m = J.tubo(p, sec, (0.0, zc + rn), frente_lisa=tuple(p["pecho_liso"]) + (pesos,))
    m.v = [(-x, -y, z) for x, y, z in m.v]
    return m


def ancho_surco(p, z):
    """1 = estría completa; hacia 0 el surco se angosta hasta cerrar en
    punta. Abajo completa, se cierra en la panza, banda lisa, y vuelve a
    abrirse en los hombros hacia el cuello."""
    a0, a1, b0, b1 = p["panza_lisa"]
    if z <= a0 or z >= b1:
        return 1.0
    if z < a1:
        return 1 - J.suave((z - a0) / (a1 - a0))
    if z > b0:
        return J.suave((z - b0) / (b1 - b0))
    return 0.0


def tubo_panza(p, sec, tope_z, por_estria=40):
    """Como `tubo` de la jirafa, pero el surco se angosta con `ancho_surco`
    en vez de solo bajar de hondo: las estrías terminan en punta, como en la
    foto del gato negro."""
    n = p["estrias"]
    cols = n * por_estria
    m = M.Malla()
    anillos = []
    umbral = p.get("panza_frente")
    for _, z, _, _, r, _, _, apaga in sec:
        kz = ancho_surco(p, z)
        esc = min(1.0, (r / p["estria_radio_pleno"]) ** 1.5) * apaga
        fila = []
        for j in range(cols):
            a = 2 * math.pi * j / cols
            c = abs(math.cos(n * a / 2)) ** p["estria_forma"]
            k = kz
            if umbral is not None:
                # solo los surcos del frente (-y, a = 90°) entran al babero
                m_s = round((a * n / math.pi - 1) / 2)
                if math.sin((2 * m_s + 1) * math.pi / n) < umbral:
                    k = 1.0
            if k < 0.02:
                g = 0.0
            else:
                # surco más angosto y un poco menos hondo conforme k baja
                g = (min(c, k) / k - 1) * k ** 0.35
            rr = r + p["estria_amplitud"] * esc * g
            # el frente (-y) queda a la mitad de una cresta
            fila.append(m.punto(rr * math.cos(a), -rr * math.sin(a), z))
        anillos.append(fila)
    abajo, arriba = m.punto(0, 0, 0), m.punto(0, 0, tope_z)
    for j in range(cols):
        j2 = (j + 1) % cols
        m.cara(abajo, anillos[0][j], anillos[0][j2])
        for f in range(len(anillos) - 1):
            a, b = anillos[f], anillos[f + 1]
            m.quad(a[j2], a[j], b[j], b[j2])
        m.cara(anillos[-1][j2], anillos[-1][j], arriba)
    return m.normalizar()


def relieve_cara(p, az, el):
    """Relieve de la cara en mm (crudo), por ángulos desde el frente: puente
    de nariz, cuencas de ojos poco hondas y hocico. 0 fuera de la cara."""
    c = p["cara_relieve"]
    e = math.exp
    nariz = c["nariz"] * e(-(az / 0.16) ** 2) * J.suave((el + 0.25) / 0.2) * J.suave((0.5 - el) / 0.25)
    ojos = -c["ojos"] * e(-((abs(az) - 0.42) / 0.22) ** 2 - ((el - 0.08) / 0.18) ** 2)
    hocico = c["hocico"] * e(-((abs(az) - 0.15) / 0.16) ** 2 - ((el + 0.27) / 0.14) ** 2)
    return (nariz + ojos + hocico) * J.suave((el + 0.55) / 0.15)


def alisar_cara(V, p, paso=1.0, ventana=6, suaviza=(2, 3)):
    """Cabeza lisa: cada vértice sale, desde el centro de la bola, hasta la
    envolvente de las crestas. La envolvente es la cresta más lejana en su
    misma latitud dentro de ±`ventana` grados de longitud (más que media
    estría), promediada con sus vecinas e interpolada para que no queden
    escalones. Se mide en esféricas para que la coronilla, donde las estrías
    se juntan, quede lisa sin tapa. `cara_lisa` dice cuánto del contorno
    (coseno con el frente, -y) va liso; las orejas no cuentan como cresta."""
    cx, cy, cz = p["bola_centro"]
    ea = p["bola_ejes"]
    s0, s1 = p["cara_lisa"]
    zc = p["corte_z"]
    nl, na = int(180 / paso), int(360 / paso)
    tabla = {}
    datos = []
    for x, y, z in V:
        d = (x - cx, y - cy, z - cz)
        r = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
        oreja = sum((d[k] / ea[k]) ** 2 for k in range(3)) > 1.1
        if z < zc or y > p["corte_y_max"] or oreja or r < 1e-6:
            datos.append(None)
            continue
        fl = math.degrees(math.acos(max(-1, min(1, d[2] / r)))) / paso
        fa = math.degrees(math.atan2(d[1], d[0]) % (2 * math.pi)) / paso
        datos.append((fl, fa, r, d))
        k = (int(fl), int(fa) % na)
        if r > tabla.get(k, 0):
            tabla[k] = r
    env = {}
    for kl in range(nl):
        for ka in range(na):
            env[(kl, ka)] = max(tabla.get((kl, (ka + e) % na), 0)
                                for e in range(-ventana, ventana + 1))
    bl, ba = suaviza
    lisa = {}
    for kl in range(nl):
        for ka in range(na):
            vals = [env.get((kl + a, (ka + b) % na), 0)
                    for a in range(-bl, bl + 1) for b in range(-ba, ba + 1)]
            vals = [v for v in vals if v > 0]
            lisa[(kl, ka)] = sum(vals) / len(vals) if vals else 0

    def tope(fl, fa):
        l0, a0 = int(math.floor(fl - 0.5)), int(math.floor(fa - 0.5))
        tl, ta = fl - 0.5 - l0, fa - 0.5 - a0
        q = [[lisa.get((l0 + i, (a0 + j) % na), 0) for j in (0, 1)] for i in (0, 1)]
        if min(min(fila) for fila in q) <= 0:
            return 0
        return ((1 - tl) * ((1 - ta) * q[0][0] + ta * q[0][1])
                + tl * ((1 - ta) * q[1][0] + ta * q[1][1]))

    salida = []
    for v, dd in zip(V, datos):
        if dd is None:
            salida.append(v)
            continue
        fl, fa, r, d = dd
        w = J.suave((-d[1] / r - s0) / (s1 - s0))
        w *= J.suave((v[2] - zc - p.get("cara_desde_z", 1.0)) / 4.0)
        t = tope(fl, fa) if w > 0 else 0
        if t <= 0:
            salida.append(v)
            continue
        t = max(t, r)        # las crestas se quedan donde están, pero sí llevan relieve
        extra = 0.0
        if p.get("cara_relieve"):
            az = math.atan2(d[0], -d[1])
            el = math.asin(max(-1, min(1, d[2] / r)))
            extra = relieve_cara(p, az, el)
        f = (r + w * (t - r) + w * extra) / r
        salida.append((cx + d[0] * f, cy + d[1] * f, cz + d[2] * f))
    return salida


def redondear(V, p):
    """Lleva la bola de la cabeza de `bola_ejes` a `bola_meta`. Dentro del
    elipsoide escala; fuera (orejas) escala solo el punto de apoyo en la
    superficie y el resto queda igual. Abajo se apaga para no mover el
    cuello."""
    cx, cy, cz = p["bola_centro"]
    ea, em = p["bola_ejes"], p["bola_meta"]
    z0, z1 = p["bola_desde_z"]
    salida = []
    for x, y, z in V:
        d = (x - cx, y - cy, z - cz)
        rho = math.sqrt(sum((d[k] / ea[k]) ** 2 for k in range(3))) or 1.0
        f = min(1.0, rho)
        n = [d[k] * f / rho for k in range(3)]           # punto de apoyo
        m = [n[k] * em[k] / ea[k] + (d[k] - n[k]) for k in range(3)]
        w = J.suave((z - z0) / (z1 - z0))
        salida.append(tuple((cx, cy, cz)[k] + d[k] + w * (m[k] - d[k])
                            for k in range(3)))
    return salida


def leer_japandi(ruta=JAPANDI):
    with zipfile.ZipFile(ruta) as z:
        x = z.read("3D/Objects/object_2.model").decode("utf-8")
    V = [tuple(map(float, m)) for m in
         re.findall(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"', x)]
    T = [tuple(map(int, m)) for m in
         re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"', x)]
    return V, T


def cabeza_japandi(p, ruta=JAPANDI):
    """Cabeza del Japandi recortada por el cuello, tapada abajo con un
    abanico al centro del borde, escalada y centrada sobre el cuello."""
    V, T = leer_japandi(ruta)
    if p.get("cara_lisa"):
        V = alisar_cara(V, p)
    V = redondear(V, p)
    zc, ymax = p["corte_z"], p["corte_y_max"]
    quedan = [t for t in T if all(V[i][2] > zc and V[i][1] < ymax for i in t)]
    # centro del cuello: promedio de los vértices justo arriba del corte
    anillo = [V[i] for t in quedan for i in t if V[i][2] < zc + 1.5]
    cx = sum(v[0] for v in anillo) / len(anillo)
    cy = sum(v[1] for v in anillo) / len(anillo)
    s, z0 = p["cabeza_escala"], p["cabeza_z"]
    m = M.Malla()
    nuevo = {}

    def idx(i):
        if i not in nuevo:
            x, y, z = V[i]
            nuevo[i] = m.punto((x - cx) * s, (y - cy) * s, z0 + (z - zc - 0.5) * s)
        return nuevo[i]

    aristas = {}
    for a, b, c in quedan:
        m.cara(idx(a), idx(b), idx(c))
        for u, w in ((a, b), (b, c), (c, a)):
            if (w, u) in aristas:
                del aristas[(w, u)]
            else:
                aristas[(u, w)] = True
    # tapa: cada arista suelta cierra contra el centro del corte
    centro = m.punto(0.0, 0.0, z0 - 0.5 * s)
    for u, w in aristas:
        m.cara(idx(w), idx(u), centro)
    return m.normalizar()


def ajustar_laminado(ruta, cambios):
    """Escribe `cambios` en el project_settings.config del .3mf y los marca
    como distintos al sistema para que Bambu Studio no los ignore."""
    with zipfile.ZipFile(ruta) as z:
        todo_zip = {n: z.read(n) for n in z.namelist()}
    cfg = json.loads(todo_zip["Metadata/project_settings.config"])
    cfg.update(cambios)
    dif = cfg.get("different_settings_to_system") or [""]
    claves = set(filter(None, dif[0].split(";"))) | set(cambios)
    dif[0] = ";".join(sorted(claves))
    cfg["different_settings_to_system"] = dif
    todo_zip["Metadata/project_settings.config"] = json.dumps(cfg, indent=4).encode()
    with zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in todo_zip.items():
            z.writestr(n, b)


def construir(p):
    todo = M.Malla()
    figura = cuerpo_gato(p)
    todo.unir(figura)
    todo.unir(cabeza_japandi(p))
    if p.get("alto_final"):
        (_, _, z0), (_, _, z1) = todo.caja()
        k = p["alto_final"] / (z1 - z0)
        for m in (todo, figura):
            m.v = [(x * k, y * k, (z - z0) * k) for x, y, z in m.v]
    return todo, figura


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=".")
    ap.add_argument("--nombre", default="GatoEstriado")
    ap.add_argument("--stl", action="store_true", help="STL para precheck")
    ap.add_argument("--3mf", dest="tres_mf", action="store_true",
                    help="guarda <nombre>.3mf con miniatura y ajustes de laminado")
    a = ap.parse_args()

    p = dict(GATO)
    todo, figura = construir(p)
    (x0, y0, z0), (x1, y1, z1) = todo.caja()
    print("Gato estriado %.0f × %.0f × %.0f mm, %d triángulos"
          % (x1 - x0, y1 - y0, z1 - z0, len(todo.t)))
    salida = Path(a.salida).expanduser()
    salida.mkdir(parents=True, exist_ok=True)
    if a.stl:
        ruta = salida / (a.nombre + ".stl")
        exportar.guardar_stl([(a.nombre, todo.trasladada(0, 0, -z0), 0.0, 0.0)],
                             ruta, a.nombre)
        print("  →", ruta)
    if a.tres_mf:
        ruta = salida / (a.nombre + ".3mf")
        png = render.render(todo.v, todo.t, tam=512, suavizado=2,
                            direccion=render.vector_vista(35, 16),
                            color=J.COLORES["salvia"])
        J.guardar(todo, ruta, a.nombre, png)
        ajustar_laminado(ruta, LAMINADO)
        print("  →", ruta)


if __name__ == "__main__":
    main()
