#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estante de tazas de dos pisos que cabe en la caja de 20 × 16 × 11 cm.

La referencia es el estante en Z «sin soportes» de ML: una mesa baja que se
pone dentro de la alacena; tazas abajo y arriba. Aquí la mesa es una cubierta
sobre dos costados, con un divisor al centro abajo y una baranda arriba
(costados y fondo) para que las tazas no se vayan de lado ni para atrás.

Vista de frente (x = largo, z = alto):

     ┌┐                            ┌┐   ← baranda: costados y fondo
     │└────────────────────────────┘│   ← cubierta (tazas arriba)
     │◣            ◢┃◣            ◢│   ← chaflanes de refuerzo
     │      taza    ┃     taza      │   ← divisor al centro
     └┘             ┻              └┘

Costados (cara de afuera):
  * japandi  — pared llena con estría vertical de media caña.
  * arco     — puente: dos patas y un arco de medio punto.
  * celosia  — pared calada con rombos a 45°.

Con baranda ya no cabe con 11 cm de alto: el estante va PARADO en la caja
(alto 14.6 → lado de 16; fondo 10.4 → lado de 11). Se imprime ACOSTADO SOBRE
EL FONDO, como el de la referencia: todo es un perfil de frente extruido
hacia atrás, y la baranda del fondo es la primera capa. Cero soportes, y la
cubierta flexiona dentro de cada capa, no entre capas. La estría japandi
queda atravesada a las capas (1.2 mm de hondo: escalonado fino, sin volado).

    python3 estante_tazas.py --estilo japandi --salida "~/Desktop/own design 3d"
"""

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path

for _dir in Path(__file__).resolve().parents:
    if (_dir / "nucleo").is_dir() or (_dir / "generadores" / "nucleo").is_dir():
        sys.path.insert(0, str(_dir if (_dir / "nucleo").is_dir()
                               else _dir / "generadores"))
        break

from nucleo import exportar, malla as M, render   # noqa: E402

# Medidas en mm. La caja es de 200 × 160 × 110; se dejan ~4 mm de holgura.
P = {
    "largo": 194.0,         # x: de costado a costado por fuera   (caja 200)
    "fondo": 104.0,         # y: de frente a fondo                (caja 110)
    "alto": 106.0,          # z: del piso a la cara de arriba de la cubierta
    "baranda": 40.0,        # alto de la baranda sobre la cubierta (total ≤ 156)
    "baranda_grueso": 4.0,  # grueso de la baranda del fondo
    "pared": 6.0,           # grueso de cada costado
    "cubierta": 5.0,        # grueso de la cubierta
    "divisor": 5.0,         # grueso del divisor del centro (0 = sin divisor)
    "chaflan": 9.0,         # refuerzo a 45° bajo la cubierta
    "chaflan_baranda": 5.0, # refuerzo a 45° al pie de la baranda
    "estilo": "japandi",    # japandi · arco · celosia
    "estria_paso": 9.0,     # japandi: de estría a estría
    "estria_hondo": 1.2,    # japandi: hondo de la media caña (≤ pared - 3)
    "estria_canto": 1.2,    # japandi: filo plano entre estrías
    "estria_margen": 3.0,   # japandi: franja lisa al frente y al fondo
    "pata": 16.0,           # arco: ancho de cada pata
    "dintel": 10.0,         # arco: pared entre la clave y la cubierta
    "rombo_paso": 26.0,     # celosia: distancia entre rombos de una misma fila
    "rombo_barra": 4.0,     # celosia: grueso de la barra entre rombos
    "rombo_margen": 9.0,    # celosia: marco liso alrededor
    "taza_d": 84.0,         # taza de muestra, solo para el render
    "taza_h": 95.0,
}


def _cerrar(m):
    if m is None:
        raise RuntimeError("no se pudo triangular un perfil")
    return m.normalizar()


def extruir_yz(lamina, x0, x1):
    """Lámina dibujada de costado (u = y, v = z) como (puntos, triángulos),
    extruida a lo largo en x. Mismo cierre que `malla.placa`."""
    puntos, tris = lamina
    m = M.Malla()
    a = [m.punto(x0, u, v) for u, v in puntos]
    b = [m.punto(x1, u, v) for u, v in puntos]
    conteo = {}
    for i, j, k in tris:
        m.cara(a[i], a[k], a[j])
        m.cara(b[i], b[j], b[k])
        for e in ((i, j), (j, k), (k, i)):
            conteo[e] = conteo.get(e, 0) + 1
    for (i, j), n in conteo.items():
        if n == 1 and (j, i) not in conteo:
            m.quad(a[i], a[j], b[j], b[i])
    return m.normalizar()


class Lamina:
    """Junta triángulos 2D de varias fuentes con vértices compartidos."""

    def __init__(self):
        self.puntos, self.tris, self._idx = [], [], {}

    def _i(self, q):
        k = (round(q[0], 5), round(q[1], 5))
        if k not in self._idx:
            self._idx[k] = len(self.puntos)
            self.puntos.append(q)
        return self._idx[k]

    def tri(self, p0, p1, p2):
        if M.area_con_signo([p0, p1, p2]) < 0:
            p1, p2 = p2, p1
        self.tris.append((self._i(p0), self._i(p1), self._i(p2)))

    def poligono(self, exterior, huecos=()):
        pts, tris, ok = M.triangular(exterior, huecos)
        if not ok:
            raise RuntimeError("no se pudo triangular un perfil")
        for i, j, k in tris:
            self.tri(pts[i], pts[j], pts[k])

    def tupla(self):
        return self.puntos, self.tris


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


# ─── Costados ──────────────────────────────────────────────────────────────

def costado_arco(p):
    D, H = p["fondo"], p["alto"]
    r = (D - 2 * p["pata"]) / 2.0
    clave = H - p["cubierta"] - p["dintel"]
    arranque = clave - r
    if arranque < 0:
        raise SystemExit("el arco no cabe: baja la pata o el dintel")
    pts = [(0, 0), (p["pata"], 0), (p["pata"], arranque)]
    n = 40
    for i in range(1, n):
        a = math.pi * (1 - i / n)
        pts.append((D / 2 + r * math.cos(a), arranque + r * math.sin(a)))
    pts += [(D - p["pata"], arranque), (D - p["pata"], 0), (D, 0), (D, H), (0, H)]
    lam = Lamina()
    lam.poligono(pts)
    return lam.tupla(), {"clave del arco": clave, "ancho del arco": 2 * r}


def _rombo(u, v, h):
    return [(u, v - h), (u + h, v), (u, v + h), (u - h, v)]


def costado_celosia(p):
    """Pared llena con rombos pasantes a 45°. Cada rombo es un anillo (su
    celda de la red menos el hueco); las celdas encajan como mosaico, y lo
    que sobra hasta el canto es un marco con un solo hueco dentado."""
    D, H = p["fondo"], p["alto"]
    m, paso, b = p["rombo_margen"], p["rombo_paso"], p["rombo_barra"]
    a = (paso - b * math.sqrt(2)) / 2.0           # media diagonal del hueco
    c = paso / 2.0                                 # media diagonal de la celda
    u0, u1, v0, v1 = m, D - m, m, H - p["cubierta"] - p["chaflan"] - m / 2
    filas = int((v1 - v0 - 2 * c) // c) + 1
    vb = v0 + (v1 - v0 - (filas + 1) * c) / 2 + c   # red centrada en la pared
    lam, aristas, centros = Lamina(), {}, []
    for j in range(filas):
        cols = int((u1 - u0 - 2 * c - (j % 2) * paso) // paso) + 1
        ub = u0 + (u1 - u0 - (cols - 1) * paso) / 2
        centros += [(ub + i * paso, vb + j * c) for i in range(cols)]
    for u, v in centros:
        fuera, dentro = _rombo(u, v, c), _rombo(u, v, a)
        for k in range(4):
            q = (k + 1) % 4
            lam.tri(fuera[k], fuera[q], dentro[q])
            lam.tri(fuera[k], dentro[q], dentro[k])
            e = tuple((round(x, 5), round(y, 5)) for x, y in (fuera[k], fuera[q]))
            aristas[e] = fuera[k], fuera[q]
    # Contorno de la unión de celdas: las aristas sin su pareja inversa.
    borde = {e[0]: (e, pq) for e, pq in aristas.items() if (e[1], e[0]) not in aristas}
    inicio = next(iter(borde))
    lazo, k = [], inicio
    while True:
        e, pq = borde[k]
        lazo.append(pq[0])
        k = e[1]
        if k == inicio:
            break
    if len(lazo) != len(borde):
        raise RuntimeError("la red de rombos no salió de una sola pieza")
    lam.poligono([(0, 0), (D, 0), (D, H), (0, H)], [lazo])
    return lam.tupla(), {"rombos por costado": len(centros), "filas": filas}


# ─── Pieza ─────────────────────────────────────────────────────────────────

def costado_japandi(p):
    """Planta (x, y) del costado izquierdo: liso por dentro (x = pared) y con
    medias cañas por fuera (x = 0), que corren de arriba abajo."""
    D, w = p["fondo"], p["pared"]
    paso, h, canto, mg = (p["estria_paso"], p["estria_hondo"],
                          p["estria_canto"], p["estria_margen"])
    n = int((D - 2 * mg + canto) // paso)
    y0 = (D - n * paso + canto) / 2                 # estrías centradas
    ancho = paso - canto
    fuera = [(0.0, D)]
    for i in reversed(range(n)):
        ya = y0 + i * paso
        for k in range(12, -1, -1):                 # de ya + ancho a ya
            t = math.pi * k / 12
            fuera.append((h * math.sin(t), ya + ancho * (1 - math.cos(t)) / 2))
    fuera.append((0.0, 0.0))
    return [(w, 0.0), (w, D)] + fuera, {"estrías por costado": n}


def construir(p):
    L, D, H, w, t, c = (p["largo"], p["fondo"], p["alto"], p["pared"],
                        p["cubierta"], p["chaflan"])
    B, tb, cb, td = (p["baranda"], p["baranda_grueso"], p["chaflan_baranda"],
                     p["divisor"])
    e = 0.05                                          # traslape para unir
    partes = []
    if p["estilo"] == "japandi":
        planta, info = costado_japandi(p)
        for espejo in (False, True):
            pts = [(L - x, y) for x, y in planta] if espejo else planta
            partes.append(_cerrar(M.placa(M.orientar(pts), [], 0.0, H + B)))
    else:
        perfil = costado_arco if p["estilo"] == "arco" else costado_celosia
        lamina, info = perfil(p)
        partes += [extruir_yz(lamina, x0, x0 + w) for x0 in (0.0, L - w)]
        if B > 0:                                     # barandas de los costados
            partes += [_cerrar(M.placa(M.orientar([(x0, 0), (x0 + w, 0),
                                                   (x0 + w, D), (x0, D)]),
                                       [], H - e, H + B)) for x0 in (0.0, L - w)]

    def caja(x0, x1, y0, y1, z0, z1):
        return _cerrar(M.placa(M.orientar([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]),
                               [], z0, z1))

    def chaflan_y(xw, s, z, dz, tam, y1=D):           # prisma a lo largo de y
        return prisma([[(xw, y, z), (xw, y, z + dz * tam), (xw + s * tam, y, z)]
                       for y in (0.0, y1)])

    partes.append(caja(w - e, L - w + e, 0, D, H - t, H))
    zb = H - t + e
    for xw, s in ((w - e, 1), (L - w + e, -1)):
        partes.append(chaflan_y(xw, s, zb, -1, c))
    if td > 0:
        x0, x1 = L / 2 - td / 2, L / 2 + td / 2
        partes.append(caja(x0, x1, 0, D, 0, zb))
        partes.append(chaflan_y(x0 + e, -1, zb, -1, c))
        partes.append(chaflan_y(x1 - e, 1, zb, -1, c))
    if B > 0:
        yb = D - tb
        partes.append(caja(w - e, L - w + e, yb, D, H - e, H + B))
        zt = H - e
        for xw, s in ((w - e, 1), (L - w + e, -1)):
            partes.append(chaflan_y(xw, s, zt, 1, cb, yb + e))
        partes.append(prisma([[(x, yb + e, zt), (x, yb + e, zt + cb), (x, yb - cb, zt)]
                              for x in (w, L - w)]))
    pieza = M.Malla()
    for m in partes:
        if m.aristas_sueltas():
            raise RuntimeError("una parte salió abierta")
        pieza.unir(m)
    hueco = (L - 2 * w - td) / 2 if td > 0 else L - 2 * w
    info["hueco de cada taza abajo"] = hueco
    info["claro bajo cubierta"] = H - t
    info["claro bajo chaflán"] = H - t - c
    info["fondo libre arriba"] = D - tb
    return pieza, info


def cilindro(cx, cy, z0, r, h, n=40):
    pts = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
           for i in range(n)]
    return _cerrar(M.placa(pts, [], z0, z0 + h))


def tazas(p):
    """Tazas de muestra con el asa al frente: una por hueco abajo, dos arriba
    recargadas en la baranda del fondo."""
    L, D, H, w, td = p["largo"], p["fondo"], p["alto"], p["pared"], p["divisor"]
    r, h = p["taza_d"] / 2, p["taza_h"]
    hueco = (L - 2 * w - td) / 2
    abajo = [(0.0, w + hueco / 2), (0.0, L - w - hueco / 2)]
    arriba = [(H, L / 2 - r - 3), (H, L / 2 + r + 3)]
    m = M.Malla()
    for z0, cx in abajo + arriba:
        cy = D / 2 if z0 == 0 else D - p["baranda_grueso"] - r - 2
        m.unir(cilindro(cx, cy, z0, r, h))
        m.unir(_cerrar(M.placa([(cx - 5, cy - r - 26), (cx + 5, cy - r - 26),
                                (cx + 5, cy - r + 4), (cx - 5, cy - r + 4)],
                               [], z0 + h * 0.2, z0 + h * 0.8)))
    return m


def acostar(pieza, p):
    """De como se usa a como se imprime: acostado sobre el fondo (y = fondo
    queda en la cama; el frente mira hacia arriba)."""
    m = M.Malla()
    m.v = [(x, z, p["fondo"] - y) for x, y, z in pieza.v]
    m.t = list(pieza.t)
    return m.normalizar()


AJUSTES = (Path.home() / "Desktop" / "own design 3d"
           / "General_Vases_print_profile(5).3mf")
LAMINADO = {"wall_loops": "2", "sparse_infill_density": "10%",
            "sparse_infill_pattern": "grid", "enable_support": "0",
            "top_shell_layers": "3", "bottom_shell_layers": "3",
            "resolution": "0.05"}


def guardar(pieza, ruta, nombre, png, notas, parametros):
    """3MF centrado en la placa con el perfil de la casa (igual que el
    deslizador de huevos)."""
    (x0, y0, _), (x1, y1, _) = pieza.caja()
    dx, dy = 128.0 - (x0 + x1) / 2.0, 128.0 - (y0 + y1) / 2.0
    exportar.guardar_3mf([("pieza", pieza, dx, dy)], ruta, nombre,
                         miniatura=png, notas=notas, parametros=parametros)
    aplicar_perfil(ruta, LAMINADO)


def aplicar_perfil(ruta, laminado):
    """Mete en el 3MF el perfil de la casa (AJUSTES) con los cambios de
    `laminado`, para que Bambu Studio y su CLI lo laminen igual."""
    if not AJUSTES.exists():
        return
    with zipfile.ZipFile(AJUSTES) as z:
        cfg = json.loads(z.read("Metadata/project_settings.config"))
    cfg.update(laminado)
    dif = cfg.get("different_settings_to_system") or [""]
    dif[0] = ";".join(sorted(set(filter(None, dif[0].split(";"))) | set(laminado)))
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
    ap.add_argument("--nombre", default="")
    ap.add_argument("--3mf", dest="tres_mf", action="store_true",
                    help="arma también el 3MF acostado, listo para laminar")
    for k, v in P.items():
        ap.add_argument("--" + k.replace("_", "-"), dest=k, type=type(v), default=v)
    a = ap.parse_args()
    p = {k: getattr(a, k) for k in P}
    nombre = a.nombre or "EstanteTazas_" + p["estilo"]

    pieza, info = construir(p)
    (x0, y0, z0), (x1, y1, z1) = pieza.caja()
    sal = Path(a.salida).expanduser()
    sal.mkdir(parents=True, exist_ok=True)
    stl = sal / (nombre + ".stl")
    exportar.guardar_stl([("pieza", pieza, 0, 0)], stl, nombre)

    vista = render.vector_vista(-32, 26)
    png = render.render(pieza.v, pieza.t, tam=640, suavizado=2, direccion=vista,
                        ruta=sal / (nombre + ".png"))
    if a.tres_mf:
        ruta = sal / (nombre + ".3mf")
        guardar(acostar(pieza, p), ruta, nombre, png,
                "%s · %.0f × %.0f × %.0f mm · se imprime acostado sobre el fondo"
                % (nombre, x1 - x0, y1 - y0, z1 - z0), p)
        print(ruta)
    con = M.Malla().unir(pieza).unir(tazas(p))
    render.render(con.v, con.t, tam=640, suavizado=2, direccion=vista,
                  ruta=sal / (nombre + "_con_tazas.png"))

    print(stl)
    print("  Medidas      %.1f × %.1f × %.1f mm (caja 200 × 160 × 110, parado: 200 × 110 × 160)"
          % (x1 - x0, y1 - y0, z1 - z0))
    for k, v in info.items():
        print("  %-20s %s" % (k, round(v, 1) if isinstance(v, float) else v))
    print("  Volumen sólido     %.0f cm³" % (pieza.volumen() / 1000.0))


if __name__ == "__main__":
    main()
