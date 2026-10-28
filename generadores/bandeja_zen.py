#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bandeja Zen deslizante: bandeja de cápsula (estadio) y un tazón redondo
con cuello que corre a lo largo de ella. Pared estriada japandi: canales
finos y hondos de arriba abajo.

El tazón no toca el piso: cuelga del borde. El borde interior de la bandeja
lleva un chaflán a 45° y el pie del tazón un cono igual, con holgura; en el
tramo recto el cono asienta en los dos chaflanes y desliza. En las puntas
redondas el chaflán es un cono del mismo radio, así que ahí asienta completo
y hace de tope. Arriba del borde se ve el cuello liso y luego el cuerpo se
abre a 45° hasta el ancho de la bandeja. Nada pasa de 45°: sin soportes.

Las piezas son barridos de un perfil (d, z) alrededor de un segmento sobre X
(estadio; largo 0 = círculo): d es la distancia al segmento. Los puntos del
perfil marcados «de fuera» se hunden lo que pida la estría en cada punto del
contorno.

    python3 bandeja_zen.py --salida /ruta            # STL de cada pieza + renders
    python3 bandeja_zen.py --salida /ruta --3mf      # además el 3MF con las dos en la placa
"""

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nucleo import exportar, malla as M, render       # noqa: E402
import estante_tazas                                  # noqa: E402

LAMINADO = dict(estante_tazas.LAMINADO, infill_combination="1")

P = dict(
    largo=190.0, ancho=90.0, alto=20.0,   # bandeja, mm
    pared=6.0,            # grueso del muro arriba (da el chaflán y deja hondo a la estría)
    canto=2.8,            # plano de arriba del borde
    piso=2.4,
    holgura=0.3,          # horizontal entre el cono del tazón y el chaflán
    taza_pie=8.0,         # lo que el tazón baja dentro de la bandeja bajo el chaflán
    taza_cuello=6.0,      # aro liso visible entre la bandeja y el cuerpo
    taza_cuerpo=20.0,     # alto del cuerpo estriado
    taza_pared=3.0, taza_piso=2.4, taza_curva=8.0,   # curva entre piso y pared por dentro
    estria_forma="costilla",   # costilla: medias cañas pegadas, línea fina entre ellas · canal
    estria_paso=2.5, estria_ancho=2.0, estria_hondo=1.2,   # ancho: solo para «canal»
    paso=0.15,            # separación de puntos a lo largo del contorno
)


# ── Barrido ────────────────────────────────────────────────────────────────

def guia(a, R, paso):
    """Puntos base, normales y largo recorrido (medido a la distancia R) de un
    estadio de medio largo `a` (0 = círculo), antihorario. El contorno a
    distancia d es base + d·normal, con el mismo número de puntos para
    cualquier d."""
    n_recto = int(round(2 * a / paso)) if a > 0 else 0
    n_arco = max(8, int(round(math.pi * R / paso)))
    g = []
    for i in range(n_recto):                             # abajo, hacia +x
        g.append((-a + 2 * a * i / n_recto, 0.0, 0.0, -1.0))
    for i in range(n_arco):                              # punta derecha
        t = -math.pi / 2 + math.pi * i / n_arco
        g.append((a, 0.0, math.cos(t), math.sin(t)))
    for i in range(n_recto):                             # arriba, hacia -x
        g.append((a - 2 * a * i / n_recto, 0.0, 0.0, 1.0))
    for i in range(n_arco):                              # punta izquierda
        t = math.pi / 2 + math.pi * i / n_arco
        g.append((-a, 0.0, math.cos(t), math.sin(t)))
    s, total = [], 0.0
    for i, (bx, by, nx, ny) in enumerate(g):
        s.append(total)
        cx, cy, mx, my = g[(i + 1) % len(g)]
        total += math.hypot(cx + R * mx - bx - R * nx, cy + R * my - by - R * ny)
    return g, s, total


def estrias(s, total, p):
    """Cuánto se hunde la pared en cada punto (0 = cara de fuera). «canal»:
    canal de fondo redondo con filo plano entre canales. «costilla»: medias
    cañas pegadas; donde se juntan queda una línea vertical a `hondo`. El
    paso se ajusta para que cierre entero."""
    n = max(1, int(round(total / p["estria_paso"])))
    paso = total / n
    w = p["estria_ancho"]
    salida = []
    if p["estria_forma"] == "costilla":
        return [-p["estria_hondo"] * (1 - math.sqrt(max(0.0, 1 - (2 * (x % paso) / paso - 1) ** 2)))
                for x in s]
    for x in s:
        u = (x % paso) / w
        salida.append(-p["estria_hondo"] * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 2))
                      if u < 1 else 0.0)
    return salida


def barrer(perfil, guia_, hundir):
    """Sólido cerrado. El perfil, lista de (d, z, de_fuera), va del centro
    arriba, por fuera, al centro abajo; el primer y el último anillo se tapan
    con un abanico al eje."""
    g, _, _ = guia_
    m = M.Malla()
    anillos = [[m.punto(bx + (d + f * h) * nx, by + (d + f * h) * ny, z)
                for (bx, by, nx, ny), h in zip(g, hundir)]
               for d, z, f in perfil]
    n = len(g)
    for k in range(len(anillos) - 1):
        r0, r1 = anillos[k], anillos[k + 1]
        for i in range(n):
            j = (i + 1) % n
            m.quad(r0[i], r0[j], r1[j], r1[i])
    for anillo, z, arriba in ((anillos[0], perfil[0][1], True),
                              (anillos[-1], perfil[-1][1], False)):
        c = m.punto(0.0, 0.0, z)
        for i in range(n):
            j = (i + 1) % n
            m.cara(c, anillo[j], anillo[i]) if arriba else m.cara(c, anillo[i], anillo[j])
    if m.aristas_sueltas():
        raise RuntimeError("malla abierta: %d aristas" % m.aristas_sueltas())
    return m.normalizar()


# ── Perfiles ───────────────────────────────────────────────────────────────

def perfil_bandeja(p):
    R, H, t, c, f = p["ancho"] / 2, p["alto"], p["pared"], p["canto"], p["piso"]
    return [(1.0, f, 0), (R - t - 1.0, f, 0), (R - t, f + 1.0, 0),
            (R - t, H - (t - c), 0),         # muro interior
            (R - c, H, 0),                   # chaflán 45° donde corre el tazón
            (R - 0.8, H, 1), (R, H - 0.8, 1),     # canto redondeado
            (R, 0.6, 1), (R - 0.6, 0.0, 1),       # pata de elefante
            (1.0, 0.0, 0)]


def _arco(cx, cz, r, a0, a1, n=8):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
             cz + r * math.sin(a0 + (a1 - a0) * i / n), 0) for i in range(n + 1)]


def perfil_taza(p):
    R, t, c, g = p["ancho"] / 2, p["pared"], p["canto"], p["holgura"]
    Rf = R - t - g                    # pie: entra entre los muros
    Rn = R - c - g                    # cuello: lo que asoma sobre el borde
    z1 = p["taza_pie"]                # empieza el cono
    z2 = z1 + (Rn - Rf)               # termina el cono (a la altura del borde)
    z3 = z2 + p["taza_cuello"]        # empieza a abrirse el cuerpo
    z4 = z3 + (R - Rn)                # cuerpo a ancho completo
    Hb = z4 + p["taza_cuerpo"]
    w, fp, rc = p["taza_pared"], p["taza_piso"], p["taza_curva"]
    Ri = R - w - p["estria_hondo"]    # pared de dentro del cuerpo
    Rp = Rf - 2.4                     # pared de dentro del pie
    zi = z3 - 1.0                     # por dentro se abre igual, un poco antes
    pts = [(1.0, fp, 0), (Rp - rc, fp, 0)]
    pts += _arco(Rp - rc, fp + rc, rc, -math.pi / 2, 0.0)[1:]   # curva piso-pared
    pts += [(Rp, zi, 0), (Ri, zi + (Ri - Rp), 0),
            (Ri, Hb - 1.0, 0), (Ri + 1.0, Hb, 0),
            (R - 0.8, Hb, 1), (R, Hb - 0.8, 1),   # canto
            (R, z4, 1), (Rn, z3, 0),              # el cuerpo se abre a 45°
            (Rn, z2, 0), (Rf, z1, 0),             # cuello liso y cono de apoyo
            (Rf, 0.6, 0), (Rf - 0.6, 0.0, 0), (1.0, 0.0, 0)]
    return pts, z1


def construir(p):
    R = p["ancho"] / 2
    a = (p["largo"] - p["ancho"]) / 2
    gb, gt = guia(a, R, p["paso"]), guia(0.0, R, p["paso"])
    bandeja = barrer(perfil_bandeja(p), gb, estrias(gb[1], gb[2], p))
    perfil, z1 = perfil_taza(p)
    taza = barrer(perfil, gt, estrias(gt[1], gt[2], p))
    # Armado: el cono del tazón (empieza en z1) asienta al pie del chaflán.
    z_taza = p["alto"] - (p["pared"] - p["canto"]) - z1
    return bandeja, taza, a, z_taza


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=".")
    ap.add_argument("--nombre", default="BandejaZen")
    ap.add_argument("--3mf", dest="tres_mf", action="store_true")
    for k, v in P.items():
        ap.add_argument("--" + k.replace("_", "-"), dest=k, type=type(v), default=v)
    args = ap.parse_args()
    p = {k: getattr(args, k) for k in P}

    bandeja, taza, recorrido, z_taza = construir(p)
    sal = Path(args.salida).expanduser()
    sal.mkdir(parents=True, exist_ok=True)
    for nombre, m in (("bandeja", bandeja), ("tazon", taza)):
        exportar.guardar_stl([(nombre, m, 0, 0)], sal / ("%s_%s.stl" % (args.nombre, nombre)),
                             args.nombre)

    vista = render.vector_vista(-32, 30)
    for x, sufijo in ((-recorrido, "armado"), (recorrido * 0.15, "deslizando")):
        armado = M.Malla().unir(bandeja).unir(taza.trasladada(x, 0, z_taza))
        render.render(armado.v, armado.t, tam=640, suavizado=2, direccion=vista,
                      ruta=sal / ("%s_%s.png" % (args.nombre, sufijo)))

    if args.tres_mf:
        png = render.render(bandeja.v, bandeja.t, tam=320, suavizado=1, direccion=vista)
        ruta = sal / (args.nombre + ".3mf")
        # En la P2S (256 × 256) no caben en fila: la bandeja atrás, el tazón al frente.
        piezas = []
        for nombre, m, cy in (("bandeja", bandeja, 128.0 + 51.0), ("tazon", taza, 128.0 - 51.0)):
            (x0, y0, _), (x1, y1, _) = m.caja()
            piezas.append((nombre, m, 128.0 - (x0 + x1) / 2, cy - (y0 + y1) / 2))
        exportar.guardar_3mf(piezas, ruta, args.nombre, miniatura=png,
                             notas="Bandeja Zen: bandeja de cápsula + tazón deslizante, estría japandi",
                             parametros=p)
        estante_tazas.aplicar_perfil(ruta, LAMINADO)
        print(ruta)

    for nombre, m in (("bandeja", bandeja), ("tazón", taza)):
        (x0, y0, z0), (x1, y1, z1) = m.caja()
        print("  %-8s %.0f × %.0f × %.1f mm  sólido %.0f cm³  %d triángulos"
              % (nombre, x1 - x0, y1 - y0, z1 - z0, m.volumen() / 1000, len(m.t)))
    print("  recorrido del tazón  %.0f mm · sobresale de la bandeja %.1f mm"
          % (2 * recorrido, z_taza + taza.caja()[1][2] - p["alto"]))


if __name__ == "__main__":
    main()
