#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recupera los parámetros de un .3mf viejo midiendo su malla.

    python3 rescatar.py "ruta/al/archivo.3mf"
    python3 rescatar.py "ruta/al/archivo.3mf" --escribir

Los .3mf que guarda el motor hoy llevan sus parámetros adentro, así que
volverlos a generar con el motor mejorado es exacto. Los de antes no los
llevan: son una malla y nada más. Esto es para ésos.

Lo que se mide sale de la propia geometría y es exacto —comprobado contra
piezas de parámetros conocidos—: la planta, el alto, la pared, el piso, el
relieve, cuántas estrías hay y cuántos divisores. El perfil vertical se
ajusta contra la curva de radio por altura, y el ajuste viene con su error en
milímetros para que se pueda decidir si creérselo.

Lo que no se puede medir no se inventa: se dice que no se pudo. Una pieza
reconstruida a medias con los valores de la receta no es la pieza del
usuario, es otra con su nombre.
"""

import argparse
import math
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import disenos                                       # noqa: E402
from nucleo import exportar                          # noqa: E402
from nucleo.contornos import CONTORNOS               # noqa: E402
from nucleo.cuerpo import _redondeo_base             # noqa: E402
from nucleo.perfiles import PERFILES                 # noqa: E402

# Hasta qué error del ajuste de perfil se considera reconocida la silueta.
# Medio milímetro sobre una pieza de 150: por debajo de eso la curva de radio
# por altura coincide, y por encima se está forzando una forma que no es.
TOLERANCIA_PERFIL = 0.5


# ── Leer la malla ──────────────────────────────────────────────────────────

def leer_malla(ruta):
    xml = zipfile.ZipFile(ruta).read("3D/3dmodel.model").decode("utf-8")
    v = [(float(a), float(b), float(c)) for a, b, c in
         re.findall(r'<vertex x="([-\d.]+)" y="([-\d.]+)" z="([-\d.]+)"/>', xml)]
    t = [(int(a), int(b), int(c)) for a, b, c in
         re.findall(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"/>', xml)]
    return v, t


def _volumen(v, t):
    s = 0.0
    for i, j, k in t:
        ax, ay, az = v[i]
        bx, by, bz = v[j]
        cx, cy, cz = v[k]
        s += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx)
              + az * (bx * cy - by * cx))
    return abs(s) / 6.0


# ── Emparejar las dos caras de la pared ────────────────────────────────────
#
# Hay dos formatos en circulación. El motor de hoy recorre el contorno
# poniendo un punto de afuera y uno de adentro, alternados; el que hizo los
# archivos viejos ponía el anillo exterior entero y luego el interior. Encima,
# cuando la pieza lleva drenaje las dos caras arrancan a la misma altura, así
# que la altura tampoco alcanza para distinguirlos. Se prueban todas.

def _caras(v, ini, n, alterno):
    if alterno:
        return [v[ini + 2 * k] for k in range(n)], [v[ini + 2 * k + 1] for k in range(n)]
    return [v[ini + k] for k in range(n)], [v[ini + n + k] for k in range(n)]


def _candidatos(v):
    corrida = 0
    while corrida < len(v) and abs(v[corrida][2] - v[0][2]) < 1e-9:
        corrida += 1
    alternos = 0
    if len(v) > 4 and abs(v[0][2] - v[2][2]) < 1e-9 and abs(v[0][2] - v[1][2]) > 1e-9:
        while 2 * alternos + 1 < len(v) and abs(v[2 * alternos][2] - v[0][2]) < 1e-9:
            alternos += 1
    vistos = set()
    for n, alterno in ((alternos, True), (corrida, False), (corrida // 2, False),
                       (corrida // 2, True), (corrida, True)):
        if n >= 16 and (n, alterno) not in vistos:
            vistos.add((n, alterno))
            yield n, alterno


def _aros_del_casco(v, n, alterno):
    """Dónde empieza cada anillo del casco, y dónde deja de haber casco.

    El casco se recorre en bloques de 2n vértices, pero después vienen los
    divisores y el plato del fondo, que no son anillos. Se distinguen porque
    un anillo del casco es plano: sus n puntos exteriores están todos a la
    misma altura. Un tabique, no.

    Sin este corte, el recorrido seguía de largo y metía la geometría de los
    divisores en la curva de radio por altura. Con eso, el ajuste del perfil
    de una pieza fallaba por cuatro milímetros y parecía que su silueta no
    era de este motor — y sí lo era; lo que no era del casco era la cola de
    la curva.
    """
    aros = []
    for i in range(0, len(v) - 2 * n + 1, 2 * n):
        z = v[i][2]
        ext = [v[i + 2 * k] for k in range(n)] if alterno else v[i:i + n]
        if any(abs(p[2] - z) > 1e-6 for p in ext):
            break
        aros.append(i)
    return aros


def _espesores(ext, inte, cx, cy):
    """Las distancias entre cara y cara, o None si este emparejamiento no es.

    El bueno no es el de espesor más parejo —el correcto varía a propósito lo
    que mide el relieve— sino el único donde la cara de adentro queda de
    verdad por dentro en todo el contorno. Un emparejamiento equivocado junta
    puntos vecinos de la misma cara, y ahí la diferencia de radio cambia de
    signo a cada paso.
    """
    dentro, dist = 0, []
    for a, b in zip(ext, inte):
        if math.hypot(b[0] - cx, b[1] - cy) < math.hypot(a[0] - cx, a[1] - cy):
            dentro += 1
        dist.append(math.dist(a[:2], b[:2]))
    dist.sort()
    if dentro < 0.90 * len(ext) or not (0.3 <= dist[len(dist) // 2] <= 6.0):
        return None
    return dist


# ── Medir ──────────────────────────────────────────────────────────────────

def medir(ruta):
    """Lo que se puede leer de la malla. None si no parece de este motor."""
    v, t = leer_malla(ruta)
    if len(v) < 64:
        return None
    xs = [p[0] for p in v]
    ys = [p[1] for p in v]
    zs = [p[2] for p in v]
    caja = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    elegido = None
    for n, alterno in _candidatos(v):
        if 2 * n > len(v):
            continue
        ext, inte = _caras(v, 0, n, alterno)
        if _espesores(ext, inte, cx, cy) is not None:
            elegido = (n, alterno)
            break
    if elegido is None:
        return None
    n, alterno = elegido

    aros = _aros_del_casco(v, n, alterno)
    medio = min(aros, key=lambda i: abs(v[i][2] - caja[2] * 0.5))
    ext, inte = _caras(v, medio, n, alterno)
    z_medida = ext[0][2]
    d = _espesores(ext, inte, cx, cy) or _espesores(*_caras(v, 0, n, alterno), cx, cy)
    pared, amp = (d[-1] + d[0]) / 2, (d[-1] - d[0]) / 2

    # Estrías: el radio menos su propio promedio de ventana ancha. Lo que
    # queda es el relieve, y cada vez que cruza el cero empieza una estría.
    r = [math.hypot(p[0] - cx, p[1] - cy) for p in ext]
    w = max(2, n // 60)
    suave = [sum(r[(i + k) % n] for k in range(-w, w + 1)) / (2 * w + 1)
             for i in range(n)]
    dif = [r[i] - suave[i] for i in range(n)]
    estrias = sum(1 for i in range(n) if dif[i] <= 0 < dif[(i + 1) % n])
    perimetro = sum(math.dist(ext[i][:2], ext[(i + 1) % n][:2]) for i in range(n))

    # El radio medio por altura, no el máximo: con torsión el máximo gira y
    # la curva sale ondulada por el giro y no por la silueta.
    curva = sorted((v[i][2],
                    sum(math.hypot(p[0] - cx, p[1] - cy)
                        for p in _caras(v, i, n, alterno)[0]) / n)
                   for i in aros)

    vueltas = _torsion(v, n, alterno, aros, cx, cy, estrias, caja[2])
    sobrante = v[len(aros) * 2 * n:]
    return {
        "torsion_vueltas": round(vueltas, 2),
        "drenaje": _drenaje(sobrante),
        "puntos": n, "alterno": alterno, "aros": len(aros),
        "caja": caja, "gramos": round(_volumen(v, t) / 1000 * 1.24),
        "ancho": round(caja[0] - 2 * amp, 1), "fondo": round(caja[1] - 2 * amp, 1),
        "alto": round(caja[2], 1), "pared": round(pared, 2),
        "onda_amplitud": round(amp, 2), "piso": round(_caras(v, 0, n, alterno)[1][0][2], 2),
        "estrias": estrias, "onda_paso": round(perimetro / max(1, estrias), 1),
        "valle": round(pared - amp, 2),
        "divisores": _divisores(sobrante), "curva": curva,
        "planta": suave, "z_medida": z_medida,
    }


def _agrupar(valores, junta=0.6):
    """Agrupa coordenadas casi iguales y devuelve el centro de cada grupo."""
    grupos, actual = [], [valores[0]]
    for v in valores[1:]:
        if v - actual[-1] < junta:
            actual.append(v)
        else:
            grupos.append(actual)
            actual = [v]
    grupos.append(actual)
    return [sum(g) / len(g) for g in grupos if len(g) > 30]


def _divisores(sobrante):
    """Cuántos tabiques hay y de qué grosor, mirando lo que sobra del casco.

    Un tabique perpendicular a un eje tiene todos sus puntos en dos planos
    paralelos separados por el grosor. Agrupando las coordenadas de ese eje
    aparecen esos planos, y cada par cercano es un divisor.

    Dos trampas, y las dos daban divisores inventados. La primera: los
    extremos de un tabique también forman un par de planos, pero separados
    por el ancho de la pieza, así que sólo cuenta un par si cabe en el rango
    del grosor declarado. La segunda: en el eje que el tabique recorre a lo
    largo, sus puntos se reparten por todo el fondo, y un reparto continuo
    partido en grupitos da pares cercanos por todos lados. Por eso un par
    sólo vale si está aislado — con hueco a los dos lados. Un tabique de
    verdad es un plano solo en medio de nada; un reparto continuo, no.
    """
    vacio = {"ranuras": 1, "filas": 1, "grosor": None, "alto": None}
    if len(sobrante) < 40:
        return vacio
    spec = {p["clave"]: p for p in disenos.PARAMETROS}["divisor_grosor"]
    aislamiento = spec["max"] + 2.0
    salida = dict(vacio)
    for eje, clave in ((0, "ranuras"), (1, "filas")):
        planos = _agrupar(sorted(round(p[eje], 1) for p in sobrante))
        pares = []
        for i in range(len(planos) - 1):
            a, b = planos[i], planos[i + 1]
            if not (spec["min"] - 0.3 <= b - a <= spec["max"] + 0.3):
                continue
            antes = a - planos[i - 1] if i > 0 else float("inf")
            despues = planos[i + 2] - b if i + 2 < len(planos) else float("inf")
            if antes > aislamiento and despues > aislamiento:
                pares.append((a, b))
        salida[clave] = len(pares) + 1
        if pares:
            salida["grosor"] = round(sum(b - a for a, b in pares) / len(pares), 1)
    salida["alto"] = round(max(p[2] for p in sobrante), 1)
    return salida


def _drenaje(sobrante):
    """Los agujeros del piso: cuántos, de qué diámetro y cada cuánto.

    El motor dibuja cada agujero como un círculo de diez puntos, así que en
    lo que sobra del casco los agujeros aparecen como grupitos apretados y
    redondos. Se agrupan por cercanía y se queda con los que tienen forma de
    círculo: todos sus puntos a la misma distancia de su centro.

    La cercanía se mide corta —tres milímetros— y eso es lo que hace que
    funcione. En la misma placa está el contorno del piso, con sus puntos
    repartidos cada ocho milímetros o más; con un umbral ancho, el contorno
    hace de puente entre agujero y agujero y todo acaba en un solo grupo.

    Hace falta medirlo porque un piso perforado se delata sólo por omisión
    —la cara interior arranca en cero en vez de sobre el piso— y con eso no
    se sabe ni el diámetro ni la separación.
    """
    bajos = [p for p in sobrante if p[2] < 0.05]
    if len(bajos) < 40:
        return None
    # La placa va de z=0 a su espesor, y ése es el piso que no se puede leer
    # de la cara interior cuando hay drenaje: con drenaje la cara interior
    # arranca en cero.
    altos = sorted(p[2] for p in sobrante if 0.05 <= p[2] <= 8.0)
    espesor = altos[len(altos) // 2] if len(altos) > 20 else None

    # Agrupación por rejilla: cada punto cae en una celda de 3 mm y se une con
    # los de las celdas vecinas. Evita comparar todos contra todos.
    lado = 3.0
    celdas = {}
    for i, p in enumerate(bajos):
        celdas.setdefault((int(p[0] // lado), int(p[1] // lado)), []).append(i)
    padre = list(range(len(bajos)))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    for (cx_, cy_), idxs in celdas.items():
        for dx in (0, 1):
            for dy in (-1, 0, 1):
                if (dx, dy) < (0, 0):
                    continue
                for j in celdas.get((cx_ + dx, cy_ + dy), []):
                    for i in idxs:
                        if math.dist(bajos[i][:2], bajos[j][:2]) <= lado:
                            ri, rj = raiz(i), raiz(j)
                            if ri != rj:
                                padre[ri] = rj

    grupos = {}
    for i in range(len(bajos)):
        grupos.setdefault(raiz(i), []).append(bajos[i])

    circulos = []
    for g in grupos.values():
        if not (6 <= len(g) <= 14):
            continue
        mx = sum(p[0] for p in g) / len(g)
        my = sum(p[1] for p in g) / len(g)
        rr = [math.hypot(p[0] - mx, p[1] - my) for p in g]
        if max(rr) - min(rr) < 0.3 and 0.5 < sum(rr) / len(rr) < 8.0:
            circulos.append((mx, my, sum(rr) / len(rr)))
    if len(circulos) < 3:
        return None
    sep = min(math.dist(a[:2], b[:2]) for i, a in enumerate(circulos)
              for b in circulos[i + 1:])
    return {"agujeros": len(circulos), "piso": espesor,
            "diametro": round(2 * sum(c[2] for c in circulos) / len(circulos), 1),
            "separacion": round(sep, 1)}


def _torsion(v, n, alterno, aros, cx, cy, estrias, alto):
    """Cuántas vueltas da el dibujo al subir, y por tanto si hay torsión.

    Cada anillo se proyecta sobre la frecuencia de las estrías —una
    transformada de Fourier de un solo término— y de ahí sale la fase: dónde
    está la cresta en ese anillo. Si la fase se corre parejo conforme sube la
    pieza, el relieve es una hélice y no una estría vertical.

    Medirlo importa más de lo que parece: el nombre del archivo decía «ondas»
    y la pieza era una torsión. Reconstruirla como ondulado le habría
    enderezado el dibujo sin que nadie lo pidiera.
    """
    if estrias < 2:
        return 0.0
    fases = []
    for i in aros:
        ext, _ = _caras(v, i, n, alterno)
        re_, im_ = 0.0, 0.0
        for j, p in enumerate(ext):
            ang = 2 * math.pi * estrias * j / n
            r = math.hypot(p[0] - cx, p[1] - cy)
            re_ += r * math.cos(ang)
            im_ += r * math.sin(ang)
        fases.append((ext[0][2], math.atan2(im_, re_)))
    fases.sort()
    # Desenrollar: la fase vive en un círculo y salta de +π a −π.
    corrido, previa, total = [], fases[0][1], 0.0
    for z, ph in fases:
        d = ph - previa
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        total += d
        previa = ph
        corrido.append((z, total))
    deriva = corrido[-1][1] - corrido[0][1]
    return deriva / (2 * math.pi * estrias)


def ajustar_contorno(planta, contorno, ancho, fondo):
    """El redondeo de esquina que mejor explica la planta medida.

    Se compara la planta de la malla contra la que da el contorno con cada
    redondeo, las dos como lista de radios ordenada: así la comparación no
    depende de por dónde empiece a recorrer cada una. Devuelve (redondeo,
    error en mm).
    """
    objetivo = sorted(planta)
    mejor = None
    spec = {p["clave"]: p for p in disenos.PARAMETROS}["redondeo"]
    base = {"ancho": ancho, "fondo": fondo, "arco_plano": 0.6, "pliegues": 9,
            "pliegue_profundidad": 0.07, "guijarro_irregular": 0.18, "trazo": ""}
    r = spec["min"]
    while r <= min(spec["max"], min(ancho, fondo) / 2.0):
        fn = CONTORNOS[contorno][1](dict(base, redondeo=r))
        pred = sorted(math.hypot(*fn(k / len(objetivo)))
                      for k in range(len(objetivo)))
        err = math.sqrt(sum((a - b) ** 2 for a, b in zip(pred, objetivo))
                        / len(objetivo))
        if mejor is None or err < mejor[1]:
            mejor = (r, err)
        r += spec["paso"]
    return mejor


def ajustar_perfil(curva, alto):
    """(perfil, intensidad, redondeo de base, error en mm) que mejor explican
    la curva de radio por altura.

    El error es el dato que importa: por encima de la tolerancia no hay
    silueta reconocida, y entonces no hay nada que reconstruir.
    """
    mejor = None
    for nombre, (_, constructor) in PERFILES.items():
        for i in range(0, 36):
            k = i / 100.0
            perfil = constructor({"perfil_intensidad": k})
            for r_base in range(0, 61, 2):
                filete, _h = _redondeo_base(100.0, r_base, 0.0)
                f = [perfil(min(1.0, z / alto)) * filete(z) for z, _ in curva]
                den = sum(x * x for x in f)
                if den <= 0:
                    continue
                escala = sum(x * rr for x, (_, rr) in zip(f, curva)) / den
                err = math.sqrt(sum((escala * x - rr) ** 2
                                    for x, (_, rr) in zip(f, curva)) / len(curva))
                if mejor is None or err < mejor[3]:
                    mejor = (nombre, k, r_base, err)
    return mejor


def informe(ruta):
    """Imprime lo que se pudo recuperar. Devuelve (medida, ajuste) o None."""
    guardados = exportar.leer_parametros(ruta)
    if guardados:
        print("  El archivo trae sus parámetros adentro: no hay nada que "
              "adivinar. Vuélvelo a generar con ellos.")
        return guardados, None
    m = medir(ruta)
    if m is None:
        print("  No salió de este generador (o no se le reconoce la malla). "
              "No se toca.")
        return None
    ajuste = ajustar_perfil(m["curva"], m["alto"])
    print("  formato      %s · %d puntos por anillo · %d anillos"
          % ("alternado" if m["alterno"] else "por bloques (motor viejo)",
             m["puntos"], m["aros"]))
    print("  caja         %.1f × %.1f × %.1f mm · %d g"
          % (m["caja"] + (m["gramos"],)))
    print("  planta       %.1f × %.1f mm" % (m["ancho"], m["fondo"]))
    print("  pared        %.2f mm       piso %.2f mm" % (m["pared"], m["piso"]))
    print("  relieve      %.2f mm       %d estrías de %.1f mm"
          % (m["onda_amplitud"], m["estrias"], m["onda_paso"]))
    print("  VALLE        %.2f mm%s" % (m["valle"],
          "   ← menos de dos hilos de boquilla: sale traslúcido"
          if m["valle"] < 0.8 else "   ✓"))
    d = m["divisores"]
    print("  divisores    %s"
          % ("ninguno" if d["ranuras"] == 1 and d["filas"] == 1 else
             "%d ranuras × %d filas, de %s mm, hasta z=%s"
             % (d["ranuras"], d["filas"], d["grosor"], d["alto"])))
    dr = m["drenaje"]
    print("  drenaje      %s"
          % ("piso sólido" if not dr else
             "%d agujeros de %.1f mm cada %.1f mm, en placa de %.1f mm"
             % (dr["agujeros"], dr["diametro"], dr["separacion"],
                dr["piso"] or 0.0)))
    print("  torsión      %.2f vueltas%s" % (m["torsion_vueltas"],
          "  → el acabado es una hélice, no una estría vertical"
          if abs(m["torsion_vueltas"]) > 0.02 else "  → estría vertical"))
    print("  perfil       %s intensidad %.2f, filete %d mm — error %.2f mm%s"
          % (ajuste[0], ajuste[1], ajuste[2], ajuste[3],
             "" if ajuste[3] <= TOLERANCIA_PERFIL else
             "   ← no se reconoce la silueta"))
    return m, ajuste


def parametros(m, ajuste, diseno, acabado, contorno, paso):
    """Los parámetros con los que volver a generar la pieza.

    Lo medido manda. Lo que cambia respecto al original es sólo lo que el
    motor de hoy hace distinto y mejor: el relieve baja a lo que la pared
    aguante —que es el defecto que se vino a arreglar— y el paso de la estría
    baja a la regla de la casa, estrías finas en vez de pocas y gordas.
    """
    p = dict(disenos.parametros_de(diseno))
    d = m["divisores"]
    # La planta se midió a media altura, y ahí el perfil ya la ensanchó o la
    # estrechó. El parámetro «ancho» es la planta nominal, antes del perfil,
    # así que hay que deshacer el factor de esa altura. Sin esto, un barril de
    # 0.09 devolvía una pieza once milímetros más ancha que la original.
    perfil = PERFILES[ajuste[0]][1]({"perfil_intensidad": ajuste[1]})
    filete, _h = _redondeo_base(100.0, ajuste[2], 0.0)
    z = m["z_medida"]
    factor = perfil(min(1.0, z / m["alto"])) * filete(z) or 1.0
    ancho = m["ancho"] / factor
    fondo = m["fondo"] / factor
    if abs(m["torsion_vueltas"]) > 0.02 and acabado in ("ondulado", "auto"):
        acabado = "torsion"
    elif acabado == "auto":
        acabado = "ondulado"
    p.update({
        "contorno": contorno, "acabado": acabado,
        "torsion_vueltas": m["torsion_vueltas"],
        "ancho": round(ancho), "fondo": round(fondo),
        "alto": round(m["alto"]), "onda_paso": paso, "pared": m["pared"],
        # Con drenaje, la cara interior arranca en cero y el piso medido sale
        # 0: ahí no se puede leer el espesor, así que se deja el de la receta.
        "piso": (m["piso"] if m["piso"] > 0.5
                 else (m["drenaje"] or {}).get("piso") or p["piso"]),
        "drenaje_diametro": m["drenaje"]["diametro"] if m["drenaje"] else 0.0,
        "drenaje_separacion": (m["drenaje"]["separacion"] if m["drenaje"]
                               else p["drenaje_separacion"]),
        "onda_amplitud": min(m["onda_amplitud"], m["pared"] - 0.8),
        "perfil": ajuste[0], "perfil_intensidad": ajuste[1],
        "base_redondeo": ajuste[2],
        "ranuras": d["ranuras"], "filas": d["filas"],
    })
    if d["grosor"]:
        p["divisor_grosor"] = d["grosor"]
    if d["alto"]:
        p["divisor_alto"] = d["alto"]
    redondeo, err_planta = ajustar_contorno([r / factor for r in m["planta"]],
                                            contorno, p["ancho"], p["fondo"])
    p["redondeo"] = redondeo
    return p, err_planta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("archivos", nargs="+")
    ap.add_argument("--escribir", action="store_true",
                    help="regenera el archivo; el original se guarda antes en "
                         "una carpeta «_originales» al lado")
    ap.add_argument("--diseno", default="libre")
    ap.add_argument("--forzar", action="store_true",
                    help="regenera aunque no se reconozca la silueta. Lo que "
                         "sale no es la pieza original sino la más parecida "
                         "que el motor de hoy sabe hacer; úsalo con --sufijo "
                         "para dejarla al lado y poder compararlas.")
    ap.add_argument("--sufijo", default="",
                    help="deja la pieza regenerada como un archivo nuevo con "
                         "este sufijo, en vez de reemplazar el original.")
    ap.add_argument("--acabado", default="auto",
                    help="por defecto se deduce de la malla")
    ap.add_argument("--contorno", default="rectangulo")
    ap.add_argument("--paso", type=float, default=None,
                    help="paso de la estría al regenerar. Por defecto se "
                         "conserva el dibujo original: el paso se ajusta para "
                         "que salgan las mismas estrías que tenía. Poniendo 4 "
                         "se aplica la regla de la casa —muchas estrías finas "
                         "se ven caras, pocas y gordas baratas— pero eso ya es "
                         "reestilizar la pieza, no arreglarla.")
    args = ap.parse_args()
    for ruta in args.archivos:
        ruta = Path(ruta).expanduser()
        print("\n" + "=" * 70)
        print(ruta.name)
        salida = informe(ruta)
        if not args.escribir or not salida or salida[1] is None:
            continue
        m, ajuste = salida
        if ajuste[3] > TOLERANCIA_PERFIL and not args.forzar:
            print("  NO SE REGENERA: sin silueta reconocida habría que "
                  "inventarle el perfil, y eso es devolver otra pieza con el "
                  "mismo nombre. Con --forzar y --sufijo sale al lado, sin "
                  "reemplazar nada.")
            continue
        if ajuste[3] > TOLERANCIA_PERFIL:
            print("  FORZADO: la silueta no se reconoce, así que ésta no es "
                  "la pieza original sino la más parecida (error %.1f mm)."
                  % ajuste[3])
        p, err_planta = parametros(m, ajuste, args.diseno, args.acabado,
                                   args.contorno, args.paso or 4.0)
        if args.paso is None:
            p["onda_paso"] = _paso_que_conserva(p, m["estrias"])
        _regenerar(ruta, p, m, err_planta, args.sufijo)


def _paso_que_conserva(p, estrias):
    """El paso con el que vuelven a salir las mismas estrías que había.

    El paso se mide sobre el perímetro de la planta nominal, y ése no se
    conoce hasta construir la pieza. Así que se construye una vez, se mira
    cuántas estrías salieron y se corrige la regla de tres. Con una pasada
    basta: la relación entre paso y estrías es exacta salvo el redondeo a
    entero que hace el motor.
    """
    from nucleo import cuerpo
    datos = cuerpo.construir(disenos.normalizar(p), calidad="borrador")[1]
    salieron = datos["estrias"] or estrias
    return round(p["onda_paso"] * salieron / max(1, estrias), 2)


def _regenerar(ruta, p, medido, err_planta, sufijo=""):
    import crear
    nombre = ruta.stem + sufijo
    if sufijo:
        print("  el original no se toca; la nueva sale como «%s»" % nombre)
    else:
        respaldo = ruta.parent / "_originales"
        respaldo.mkdir(exist_ok=True)
        destino = respaldo / ruta.name
        if not destino.exists():
            destino.write_bytes(ruta.read_bytes())
        print("  original respaldado en %s" % destino)
    print("  redondeo de esquina ajustado a %.1f mm (error %.2f mm)"
          % (p["redondeo"], err_planta))
    datos, rutas = crear.generar("libre", p, ruta.parent, nombre)
    print("  regenerado: %s × %s × %s mm · %d g (antes %d g) · %d estrías"
          % (datos["ancho"], datos["fondo"], datos["alto"], datos["gramos"],
             medido["gramos"], datos["estrias"]))
    print("  resolución: %d puntos × %d capas" % (datos["segmentos"], datos["capas"]))
    for a in datos["avisos"]:
        print("  ⚠  " + a)


if __name__ == "__main__":
    main()
