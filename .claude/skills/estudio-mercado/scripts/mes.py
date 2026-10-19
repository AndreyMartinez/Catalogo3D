#!/usr/bin/env python3
"""Cómo viene el mes: lo vendido del día 1 al último día completo, contra el
mes anterior al mismo día, la proyección al cierre y qué lo está moviendo.

Lee lo que dejó `colecta-full/scripts/traer_datos.py` en ~/.catalogo3d/ml_datos.json
y lo cruza con el catálogo, igual que semana.py. No le pega a la API: si los
datos son viejos, lo dice y sigue.

Uso:
  python3 mes.py                      # el mes en curso
  python3 mes.py --mes 2026-09        # un mes cerrado, sin proyección
  python3 mes.py --meta 180           # meta del mes en unidades
  python3 mes.py --meta-pesos 40000   # meta del mes en pesos

Deja dos archivos en .claude/mercado/meses/ (fuera de git):
  AAAA-MM.json   las cifras crudas
  AAAA-MM.md     el reporte legible; la recomendación la escribe el skill

Los días son de la Ciudad de México. El día de la descarga va a medias: no
entra al ritmo ni a la comparación, se muestra aparte como «hoy, parcial».
"""
import argparse
import calendar
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import semana  # noqa: E402

HUSO_MX = timezone(timedelta(hours=-6))
DATOS_ML = semana.DATOS_ML
SALIDA = semana.RAIZ / ".claude" / "mercado" / "meses"
BASE_CHICA = 10          # unidades: por debajo, un porcentaje engaña
DIAS_CONFIABLE = 7       # menos días que esto: la proyección es una corazonada
CAMBIO_RITMO = 0.20      # ritmo de 7 días contra el del mes
HISTORIA_NUEVA = 60      # días de ventana antes del mes para llamar «nueva» a una publicación


# ── Calendario ────────────────────────────────────────────────────────────

def dias_del_mes(anio, mes):
    return calendar.monthrange(anio, mes)[1]


def mes_anterior(anio, mes, atras=1):
    i = anio * 12 + (mes - 1) - atras
    return i // 12, i % 12 + 1


def etiqueta(anio, mes):
    return "%04d-%02d" % (anio, mes)


def corte(generado_mx, hoy_mx, pedido=None):
    """El rango del análisis.

    generado_mx: datetime de la descarga en la CDMX. hoy_mx: date de hoy.
    pedido: (año, mes) o None para el mes en curso.
    El último día completo es el anterior a la descarga: ese día va a medias.
    """
    anio, mes = pedido or (hoy_mx.year, hoy_mx.month)
    inicio = date(anio, mes, 1)
    fin_mes = date(anio, mes, dias_del_mes(anio, mes))
    if inicio > hoy_mx:
        raise ValueError("%s todavía no empieza" % etiqueta(anio, mes))
    ultimo_completo = generado_mx.date() - timedelta(days=1)
    hasta = min(fin_mes, ultimo_completo)
    dias = max(0, (hasta - inicio).days + 1)
    parcial = generado_mx.date() if inicio <= generado_mx.date() <= fin_mes else None
    return {
        "anio": anio, "mes": mes, "inicio": inicio,
        "hasta": hasta if dias else None, "dias": dias,
        "dias_mes": fin_mes.day, "cerrado": ultimo_completo >= fin_mes,
        "parcial": parcial,
    }


def cobertura(primer_dia, anio, mes, n):
    """¿Están los días 1..N de ese mes (recortado a su largo) dentro de la
    ventana bajada? primer_dia es el primer día completo de la ventana."""
    return date(anio, mes, 1) >= primer_dia and n > 0


def al_dia(serie, anio, mes, n):
    """Suma de los días 1..min(N, días del mes). Devuelve (suma, recortado)."""
    tope = min(n, dias_del_mes(anio, mes))
    desde, hasta = date(anio, mes, 1), date(anio, mes, tope)
    total = sum(v for f, v in serie.items()
                if f and desde <= date.fromisoformat(f) <= hasta)
    return total, tope < n


def suma_rango(serie, desde, hasta):
    if hasta is None:
        return 0
    return sum(v for f, v in serie.items()
               if f and desde <= date.fromisoformat(f) <= hasta)


def diferencia(actual, base, base_unidades):
    """Diferencia absoluta y porcentaje; sin porcentaje si la base es chica."""
    pct = None
    if base_unidades >= BASE_CHICA and base:
        pct = round((actual - base) / base * 100, 1)
    return {"valor": round(actual - base, 2), "pct": pct,
            "base_chica": base_unidades < BASE_CHICA}


# ── Proyección y meta ─────────────────────────────────────────────────────

def proyectar(serie, inicio, hasta, dias_mes):
    """Cierre estimado con el ritmo del mes y con el de los últimos 7 días
    completos. Siempre es una suposición; con menos de 7 días, además, no
    es confiable."""
    if hasta is None:
        return None
    dias = (hasta - inicio).days + 1
    llevado = suma_rango(serie, inicio, hasta)
    n7 = min(DIAS_CONFIABLE, dias)
    ult7 = suma_rango(serie, hasta - timedelta(days=n7 - 1), hasta)
    ritmo_mes, ritmo_7 = llevado / dias, ult7 / n7
    restantes = dias_mes - dias
    cambio = bool(ritmo_mes) and abs(ritmo_7 - ritmo_mes) / ritmo_mes > CAMBIO_RITMO
    return {
        "llevado": round(llevado, 2), "dias": dias, "restantes": restantes,
        "ritmo_mes": round(ritmo_mes, 2), "ritmo_7": round(ritmo_7, 2),
        "cierre_ritmo_mes": round(llevado + ritmo_mes * restantes, 2),
        "cierre_ritmo_7": round(llevado + ritmo_7 * restantes, 2),
        "cambio_ritmo": cambio, "nivel": "suposición",
        "confiable": dias >= DIAS_CONFIABLE,
    }


def meta(objetivo, llevado, restantes, ritmo):
    """Cuánto falta para la meta y a qué ritmo diario hay que ir."""
    falta = max(0.0, objetivo - llevado)
    necesario = None
    if falta and restantes > 0:
        necesario = round(falta / restantes, 2)
    return {"objetivo": objetivo, "llevado": round(llevado, 2),
            "falta": round(falta, 2), "alcanzada": falta == 0,
            "ritmo_necesario": necesario, "ritmo_actual": round(ritmo, 2),
            "alcanza_a_este_ritmo": falta == 0 or (
                restantes > 0 and ritmo * restantes >= falta)}


# ── Publicaciones ─────────────────────────────────────────────────────────

def alerta(u, base, vendio_mes_anterior, primera_venta, inicio, primer_dia):
    """Las mismas alertas que el reporte semanal, a escala de mes.
    `dormida` manda sobre `baja`: no vender nada es más que bajar."""
    alertas = []
    if vendio_mes_anterior and u == 0:
        alertas.append("dormida")
    else:
        t = semana.tendencia(u, base)
        if t:
            alertas.append(t)
    if (primera_venta and primera_venta >= inicio
            and (inicio - primer_dia).days >= HISTORIA_NUEVA):
        alertas.append("nueva")
    return alertas


def retorno(filas):
    """Ganancia del mes: parcial sobre las unidades con diseño vinculado
    (retorno − costo del catálogo) y extrapolada al resto con el promedio
    de las vinculadas."""
    vinc = [f for f in filas if f["ganancia_u"] is not None and f["unidades"]]
    u_total = sum(f["unidades"] for f in filas)
    u_vinc = sum(f["unidades"] for f in vinc)
    if not u_vinc:
        return {"unidades_vinculadas": 0, "unidades": u_total, "parcial": None,
                "extrapolado": None, "ganancia_u_promedio": None,
                "nota": "falta el dato: ninguna venta del mes tiene diseño "
                        "con retorno y peso en el catálogo"}
    parcial = sum(f["ganancia_u"] * f["unidades"] for f in vinc)
    prom = parcial / u_vinc
    return {"unidades_vinculadas": u_vinc, "unidades": u_total,
            "parcial": round(parcial, 2), "nivel_parcial": "correlación",
            "ganancia_u_promedio": round(prom, 2),
            "extrapolado": round(parcial + prom * (u_total - u_vinc), 2),
            "nivel_extrapolado": "suposición",
            "fuente": "retorno y costo por diseño de .catalogo3d_mercadolibre.json "
                      "y .catalogo3d_costos.json"}


# ── Armado ────────────────────────────────────────────────────────────────

def a_mx(texto):
    dt = datetime.fromisoformat(texto)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(HUSO_MX)


def series_cuenta(crudo):
    """Totales por día de la cuenta. Con un archivo viejo (sin `por_dia`
    raíz) solo se pueden reconstruir las unidades."""
    raiz = crudo.get("por_dia")
    if raiz:
        return {k: {f: d.get(k, 0) for f, d in raiz.items()}
                for k in ("unidades", "ordenes", "ingreso", "canceladas")}, True
    unidades = defaultdict(int)
    for v in (crudo.get("ventas") or {}).values():
        for f, n in (v.get("por_dia") or {}).items():
            unidades[f] += n
    return {"unidades": dict(unidades)}, False


def analizar(crudo, ahora_mx, pedido=None, meta_u=None, meta_pesos=None, mapa=None):
    generado = a_mx(crudo["generado"])
    if crudo.get("desde"):
        desde = a_mx(crudo["desde"])
    else:
        desde = generado - timedelta(days=int(crudo.get("dias_historial") or 90))
    primer_dia = desde.date() + timedelta(days=1)       # el primero va a medias
    c = corte(generado, ahora_mx.date(), pedido)
    anio, mes, inicio, hasta, n = c["anio"], c["mes"], c["inicio"], c["hasta"], c["dias"]
    series, completo = series_cuenta(crudo)
    u_serie = series["unidades"]
    avisos = []
    if ahora_mx - generado > timedelta(hours=24):
        avisos.append("datos_viejos")
    if not completo:
        avisos.append("formato_viejo")
    cubierto = cobertura(primer_dia, anio, mes, 1)
    if not cubierto:
        avisos.append("mes_incompleto")

    # Mes cerrado: mes contra mes. Mes en curso: al mismo día N.
    n_cmp = 31 if c["cerrado"] else n

    def totales(desde_d, hasta_d):
        t = {k: round(suma_rango(s, desde_d, hasta_d), 2) for k, s in series.items()}
        if "ordenes" in t:
            t["ticket"] = round(t["ingreso"] / t["ordenes"], 2) if t["ordenes"] else None
        return t

    def al_dia_todo(a, m, n_):
        out, recortado = {}, False
        for k, s in series.items():
            out[k], recortado = al_dia(s, a, m, n_)
            out[k] = round(out[k], 2)
        if "ordenes" in out:
            out["ticket"] = round(out["ingreso"] / out["ordenes"], 2) if out["ordenes"] else None
        return out, recortado

    tot = totales(inicio, hasta)

    # Mes anterior.
    pa, pm = mes_anterior(anio, mes)
    anterior = None
    if n_cmp and cobertura(primer_dia, pa, pm, n_cmp):
        ad, recortado = al_dia_todo(pa, pm, n_cmp)
        completo_prev, _ = al_dia_todo(pa, pm, 31)
        anterior = {
            "mes": etiqueta(pa, pm), "al_dia": ad, "recortado": recortado,
            "completo": completo_prev,
            "diferencia": {k: diferencia(tot.get(k, 0), ad[k], ad["unidades"])
                           for k in ("unidades", "ingreso", "ordenes") if k in ad},
        }
    elif n_cmp:
        anterior = {"mes": etiqueta(pa, pm), "omitido": "la descarga empieza el %s"
                    % primer_dia.isoformat()}

    # Promedio de tres meses al mismo día.
    previos = [mes_anterior(anio, mes, i) for i in (1, 2, 3)]
    promedio = None
    if n_cmp and all(cobertura(primer_dia, a, m, n_cmp) for a, m in previos):
        suma = defaultdict(float)
        for a, m in previos:
            ad, _ = al_dia_todo(a, m, n_cmp)
            for k in ("unidades", "ingreso", "ordenes"):
                if k in ad:
                    suma[k] += ad[k]
        prom = {k: round(v / 3, 2) for k, v in suma.items()}
        promedio = {"meses": [etiqueta(a, m) for a, m in previos], "al_dia": prom,
                    "diferencia": {k: diferencia(tot.get(k, 0), prom[k], prom["unidades"])
                                   for k in prom}}
    elif n_cmp:
        promedio = {"meses": [etiqueta(a, m) for a, m in previos],
                    "omitido": "no hay tres meses completos en la descarga (empieza el %s)"
                    % primer_dia.isoformat()}

    # Proyección y meta.
    proy = None
    if not c["cerrado"] and hasta is not None:
        proy = {k: proyectar(series[k], inicio, hasta, c["dias_mes"])
                for k in ("unidades", "ingreso") if k in series}
    metas = {}
    if not c["cerrado"]:
        restantes = c["dias_mes"] - n
        for clave, objetivo in (("unidades", meta_u), ("ingreso", meta_pesos)):
            if objetivo is None or clave not in series:
                continue
            ritmo = proy[clave]["ritmo_mes"] if proy else 0.0
            metas[clave] = meta(float(objetivo), tot.get(clave, 0), restantes, ritmo)

    # Hoy, parcial.
    hoy_parcial = None
    if c["parcial"]:
        f = c["parcial"].isoformat()
        hoy_parcial = {k: s.get(f, 0) for k, s in series.items()
                       if k in ("unidades", "ingreso", "ordenes")}
        hoy_parcial["hasta"] = generado.strftime("%H:%M")

    # Publicaciones y categorías.
    pubs, ventas = crudo.get("publicaciones") or {}, crudo.get("ventas") or {}
    mapa = mapa or {}
    filas = []
    for mid, v in ventas.items():
        pd = v.get("por_dia") or {}
        ip = v.get("ingreso_por_dia") or {}
        u = suma_rango(pd, inicio, hasta)
        base = al_dia(pd, pa, pm, n_cmp)[0] if n_cmp else 0
        prev_completo = al_dia(pd, pa, pm, 31)[0]
        dias_venta = sorted(f for f in pd if f and pd[f])
        primera = date.fromisoformat(dias_venta[0]) if dias_venta else None
        info = mapa.get(mid, {})
        gan = (info["retorno"] - info["costo"]
               if info.get("retorno") is not None and info.get("costo") is not None
               else None)
        filas.append({
            "id": mid, "titulo": v.get("titulo") or "",
            "categoria": semana.categoria(v.get("titulo") or ""),
            "full": (pubs.get(mid) or {}).get("logistic_type") == "fulfillment",
            "unidades": u, "ingreso": round(suma_rango(ip, inicio, hasta), 2),
            "mes_anterior_al_dia": base, "mes_anterior": prev_completo,
            "diseno": info.get("archivo"),
            "ganancia_u": round(gan, 2) if gan is not None else None,
            "alertas": alerta(u, base, prev_completo > 0, primera, inicio, primer_dia),
        })
    filas.sort(key=lambda f: (-f["unidades"], -f["mes_anterior_al_dia"], f["id"]))
    u_total = sum(f["unidades"] for f in filas) or 0
    for f in filas:
        f["participacion"] = round(f["unidades"] / u_total * 100, 1) if u_total else None

    cats = defaultdict(lambda: {"unidades": 0, "ingreso": 0.0, "mes_anterior_al_dia": 0,
                                "publicaciones": 0, "unidades_full": 0})
    for f in filas:
        k = cats[f["categoria"]]
        k["unidades"] += f["unidades"]
        k["ingreso"] = round(k["ingreso"] + f["ingreso"], 2)
        k["mes_anterior_al_dia"] += f["mes_anterior_al_dia"]
        k["publicaciones"] += 1
        if f["full"]:
            k["unidades_full"] += f["unidades"]
    for k in cats.values():
        k["participacion"] = round(k["unidades"] / u_total * 100, 1) if u_total else None
    categorias = dict(sorted(cats.items(), key=lambda kv: (-kv[1]["unidades"], kv[0])))
    full = {"full": sum(f["unidades"] for f in filas if f["full"]),
            "no_full": sum(f["unidades"] for f in filas if not f["full"])}

    return {
        "mes": etiqueta(anio, mes), "desde": inicio.isoformat(),
        "hasta": hasta.isoformat() if hasta else None,
        "dias_transcurridos": n, "dias_mes": c["dias_mes"], "cerrado": c["cerrado"],
        "datos_generados": crudo["generado"], "datos_desde": primer_dia.isoformat(),
        "datos_viejos": "datos_viejos" in avisos, "avisos": avisos,
        "hoy_parcial": hoy_parcial, "totales": tot, "full": full,
        "mes_anterior": anterior, "promedio_3": promedio, "proyeccion": proy,
        "meta": metas or None, "retorno": retorno(filas),
        "categorias": categorias, "publicaciones": filas,
    }


# ── Reporte ───────────────────────────────────────────────────────────────

def pesos(x):
    return "—" if x is None else "$%s" % format(round(x), ",")


def dif_txt(d, pesos_=False):
    if d is None:
        return "—"
    v = d["valor"]
    num = (("+" if v >= 0 else "−") + pesos(abs(v))) if pesos_ else "%+d" % round(v)
    if d["pct"] is not None:
        return "%s (%+.0f %%)" % (num, d["pct"])
    return "%s (base chica)" % num if d["base_chica"] else num


def lo_que_mas_se_movio(r):
    if not r["categorias"] or not r.get("mes_anterior") or "al_dia" not in r["mes_anterior"]:
        return None
    k, c = max(r["categorias"].items(),
               key=lambda kv: abs(kv[1]["unidades"] - kv[1]["mes_anterior_al_dia"]))
    d = c["unidades"] - c["mes_anterior_al_dia"]
    if d == 0:
        return None
    return "%s, %+d unidades contra el mes pasado %s (%d → %d)" % (
        k, d, "completo" if r["cerrado"] else "al mismo día",
        c["mes_anterior_al_dia"], c["unidades"])


def reporte(r):
    t, ant, prom, proy = r["totales"], r["mes_anterior"], r["promedio_3"], r["proyeccion"]
    gen = a_mx(r["datos_generados"]).strftime("%d/%m %H:%M")
    md = ["# Ventas del mes %s" % r["mes"], ""]
    if r["datos_viejos"]:
        md += ["> ⚠️ Los datos se bajaron el %s (hora CDMX), hace más de 24 horas. "
               "Corre `python3 .claude/skills/colecta-full/scripts/traer_datos.py` "
               "antes de decidir con este reporte." % gen, ""]
    if "formato_viejo" in r["avisos"]:
        md += ["> ⚠️ El archivo de datos es de antes de que la descarga guardara pesos y "
               "órdenes: este reporte va solo en unidades. Vuelve a correr "
               "`traer_datos.py`.", ""]
    if "mes_incompleto" in r["avisos"]:
        md += ["> ⚠️ La descarga empieza el %s: faltan los primeros días del mes y no "
               "se rellenan con ceros." % r["datos_desde"], ""]
    md += ["Datos del %s (hora CDMX) · días %s" % (
        gen, "del 1 al %s" % r["hasta"][8:] if r["hasta"] else "— ninguno completo todavía"), ""]

    # Resumen en 5 líneas.
    llev = "**%d unidades**" % t["unidades"]
    if "ordenes" in t:
        llev += " en %d órdenes, %s de ingreso bruto" % (t["ordenes"], pesos(t["ingreso"]))
    linea1 = "1. Llevamos %s en %d de %d días%s." % (
        llev, r["dias_transcurridos"], r["dias_mes"], " (mes cerrado)" if r["cerrado"] else "")
    if ant and "al_dia" in ant:
        cuando = "el mes completo" if r["cerrado"] else "al mismo día"
        linea2 = "2. Contra %s %s: %d unidades → %s" % (
            ant["mes"], cuando, ant["al_dia"]["unidades"], dif_txt(ant["diferencia"]["unidades"]))
        if prom and "al_dia" in prom:
            linea2 += "; contra el promedio de 3 meses (%.0f): %s" % (
                prom["al_dia"]["unidades"], dif_txt(prom["diferencia"]["unidades"]))
        linea2 += "."
    else:
        linea2 = "2. Sin comparación contra el mes anterior: %s." % (
            ant["omitido"] if ant else "todavía no hay días completos")
    if r["cerrado"]:
        linea3 = "3. Mes cerrado: sin proyección."
    elif proy:
        pu = proy["unidades"]
        linea3 = "3. Vamos a cerrar cerca de **%.0f unidades** al ritmo del mes y %.0f al de " \
                 "los últimos 7 días (suposición%s)." % (
                     pu["cierre_ritmo_mes"], pu["cierre_ritmo_7"],
                     "" if pu["confiable"] else "; con menos de 7 días todavía no es confiable")
    else:
        linea3 = "3. Sin proyección: todavía no hay un día completo del mes."
    movio = lo_que_mas_se_movio(r)
    linea4 = "4. Lo que más se movió: %s." % (movio or "nada se movió frente al mes pasado")
    md += ["## Resumen", "", linea1, linea2, linea3, linea4,
           "5. _Recomendación: (la escribe el skill)_", ""]

    # Totales y comparación.
    md += ["## Cifras", "",
           "| | Este mes | %s | Diferencia | Prom. 3 meses | Diferencia |" % (
               ant["mes"] + (" (completo)" if r["cerrado"] else " al día") if ant and "al_dia" in ant else "Mes anterior"),
           "|---|---|---|---|---|---|"]
    filas = [("Unidades", "unidades", False), ("Órdenes", "ordenes", False),
             ("Ingreso bruto", "ingreso", True)]
    for nombre, k, es_pesos in filas:
        if k not in t:
            continue
        fmt = pesos if es_pesos else (lambda x: "%.0f" % x)
        a_val = ant["al_dia"][k] if ant and "al_dia" in ant else None
        p_val = prom["al_dia"].get(k) if prom and "al_dia" in prom else None
        md.append("| %s | %s | %s | %s | %s | %s |" % (
            nombre, fmt(t[k]), fmt(a_val) if a_val is not None else "—",
            dif_txt(ant["diferencia"].get(k), es_pesos) if a_val is not None else "—",
            fmt(p_val) if p_val is not None else "—",
            dif_txt(prom["diferencia"].get(k), es_pesos) if p_val is not None else "—"))
    if "ticket" in t:
        md.append("| Ticket promedio | %s | %s | | | |" % (
            pesos(t["ticket"]),
            pesos(ant["al_dia"].get("ticket")) if ant and "al_dia" in ant else "—"))
    if "canceladas" in t:
        md.append("| Canceladas (aparte) | %d | %s | | | |" % (
            t["canceladas"], "%d" % ant["al_dia"]["canceladas"] if ant and "al_dia" in ant else "—"))
    md.append("")
    md.append("Full / no Full (según la logística actual de cada publicación): "
              "%d / %d unidades." % (r["full"]["full"], r["full"]["no_full"]))
    if ant and "al_dia" in ant:
        nota = []
        if ant["recortado"]:
            nota.append("%s tiene menos días: se compara contra el mes completo" % ant["mes"])
        if not r["cerrado"]:
            nota.append("%s completo: %d unidades" % (ant["mes"], ant["completo"]["unidades"]))
        if nota:
            md.append("; ".join(nota).capitalize() + ".")
    if prom and "omitido" in prom:
        md.append("Promedio de 3 meses omitido: %s." % prom["omitido"])
    if r["hoy_parcial"]:
        h = r["hoy_parcial"]
        md.append("Hoy, parcial hasta las %s: %d unidades (no entran al ritmo ni a la "
                  "comparación)." % (h["hasta"], h["unidades"]))
    md.append("")

    # Proyección.
    if proy:
        md += ["## Proyección al cierre (suposición)", "",
               "| | Ritmo del mes | Cierre | Ritmo 7 días | Cierre |", "|---|---|---|---|---|"]
        for k, nombre in (("unidades", "Unidades"), ("ingreso", "Ingreso")):
            if k not in proy:
                continue
            p = proy[k]
            fmt = pesos if k == "ingreso" else (lambda x: "%.1f" % x)
            fmtc = pesos if k == "ingreso" else (lambda x: "%.0f" % x)
            md.append("| %s | %s/día | %s | %s/día | %s |" % (
                nombre, fmt(p["ritmo_mes"]), fmtc(p["cierre_ritmo_mes"]),
                fmt(p["ritmo_7"]), fmtc(p["cierre_ritmo_7"])))
        pu = proy["unidades"]
        md.append("")
        if not pu["confiable"]:
            md.append("Van %d días: la proyección todavía no es confiable." % pu["dias"])
        if pu["cambio_ritmo"]:
            md.append("⚡ Cambio de ritmo: los últimos 7 días van %s que el promedio del mes "
                      "(%.1f contra %.1f unidades/día)." % (
                          "más rápido" if pu["ritmo_7"] > pu["ritmo_mes"] else "más lento",
                          pu["ritmo_7"], pu["ritmo_mes"]))
        md.append("")
    if r["meta"]:
        md += ["## Meta", ""]
        for k, m in r["meta"].items():
            fmt = pesos if k == "ingreso" else (lambda x: "%.0f unidades" % x)
            if m["alcanzada"]:
                md.append("- %s: meta de %s alcanzada." % (k.capitalize(), fmt(m["objetivo"])))
            else:
                md.append("- %s: faltan %s para %s; hace falta %s/día, vamos a %s/día → %s." % (
                    k.capitalize(), fmt(m["falta"]), fmt(m["objetivo"]),
                    "%.1f" % m["ritmo_necesario"] if m["ritmo_necesario"] is not None else "—",
                    "%.1f" % m["ritmo_actual"],
                    "alcanza" if m["alcanza_a_este_ritmo"] else "no alcanza a este ritmo"))
        md.append("")

    # Desglose.
    md += ["## Por categoría", "",
           "| Categoría | Unidades | % | Ingreso | Mes ant. al día | En Full (u) | Publicaciones |",
           "|---|---|---|---|---|---|---|"]
    for k, c in r["categorias"].items():
        if not c["unidades"] and not c["mes_anterior_al_dia"]:
            continue
        md.append("| %s | %d | %s | %s | %d | %d | %d |" % (
            k, c["unidades"], "%.0f" % c["participacion"] if c["participacion"] is not None else "—",
            pesos(c["ingreso"]), c["mes_anterior_al_dia"], c["unidades_full"], c["publicaciones"]))
    md += ["", "## Por publicación", "",
           "| Publicación | Cat. | Full | Unidades | % | Ingreso | Mes ant. al día | Ganancia/u | Alertas |",
           "|---|---|---|---|---|---|---|---|---|"]
    for f in r["publicaciones"]:
        if not f["unidades"] and not f["mes_anterior_al_dia"] and not f["alertas"]:
            continue
        md.append("| %s · %s | %s | %s | %d | %s | %s | %d | %s | %s |" % (
            f["titulo"][:48], f["id"], f["categoria"], "sí" if f["full"] else "no",
            f["unidades"], "%.0f" % f["participacion"] if f["participacion"] is not None else "—",
            pesos(f["ingreso"]) if "ordenes" in t else "—", f["mes_anterior_al_dia"],
            "$%.2f" % f["ganancia_u"] if f["ganancia_u"] is not None else "—",
            ", ".join(f["alertas"])))
    md.append("")

    # Retorno.
    rt = r["retorno"]
    md += ["## Cuánto deja", ""]
    if "ingreso" in t:
        md.append("Ingreso bruto (precio de venta × unidades, sin envío ni cargos de ML): "
                  "%s — medido." % pesos(t["ingreso"]))
    if rt["parcial"] is None:
        md.append("Ganancia: %s." % rt["nota"])
    else:
        md.append("Ganancia estimada sobre %d de %d unidades con diseño vinculado: **%s** "
                  "(%s/u en promedio) — correlación." % (
                      rt["unidades_vinculadas"], rt["unidades"], pesos(rt["parcial"]),
                      pesos(rt["ganancia_u_promedio"])))
        md.append("Extrapolada a todas las unidades con ese promedio: %s — suposición." %
                  pesos(rt["extrapolado"]))
        md.append("Fuente: %s. No se usa el neto de `/orders`." % rt["fuente"])
    return "\n".join(md) + "\n"


# ── Entrada ───────────────────────────────────────────────────────────────

def leer_mes(texto):
    m = re.fullmatch(r"(\d{4})-(\d{2})", texto or "")
    if not m or not 1 <= int(m.group(2)) <= 12:
        raise ValueError("--mes va como AAAA-MM, por ejemplo 2026-09")
    return int(m.group(1)), int(m.group(2))


def main(argv=None, datos=DATOS_ML, salida=SALIDA, ahora=None, mapa=None):
    ap = argparse.ArgumentParser(description="Cómo viene el mes de ventas.")
    ap.add_argument("--mes", help="AAAA-MM; por defecto, el mes en curso")
    ap.add_argument("--meta", type=float, help="meta del mes en unidades")
    ap.add_argument("--meta-pesos", type=float, help="meta del mes en pesos")
    a = ap.parse_args(argv)

    if not Path(datos).exists():
        print("No hay datos. Corre antes:\n"
              "  python3 .claude/skills/colecta-full/scripts/traer_datos.py")
        return 1
    ahora_mx = (ahora or datetime.now(timezone.utc)).astimezone(HUSO_MX)
    try:
        pedido = leer_mes(a.mes) if a.mes else None
        crudo = json.loads(Path(datos).read_text(encoding="utf-8"))
        if mapa is None:
            mapa, _ = semana.catalogo()
        r = analizar(crudo, ahora_mx, pedido, a.meta, a.meta_pesos, mapa)
    except ValueError as e:
        print("No se pudo: %s" % e)
        return 2

    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / (r["mes"] + ".json")).write_text(
        json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    md = reporte(r)
    (salida / (r["mes"] + ".md")).write_text(md, encoding="utf-8")
    print(md)
    print("→ %s" % (salida / (r["mes"] + ".md")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
