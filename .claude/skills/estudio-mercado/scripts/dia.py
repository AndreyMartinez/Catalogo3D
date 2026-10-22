#!/usr/bin/env python3
"""Ganancia o pérdida día por día: ventas − comisión − envío − publicidad −
material − luz, y después los cargos que la API no ve (estimados).

Uso:
    python3 dia.py                       # últimos 30 días cerrados
    python3 dia.py --desde 2026-10-01 --hasta 2026-10-21
    python3 dia.py --corte 2026-10-21    # marca el antes/después de un cambio

Lee la API de ML en vivo (solo lectura):
- /orders/search por fecha: precio, cantidad y comisión (sale_fee) de cada orden.
- /shipments/{id}/costs: lo que pagó el vendedor de envío (se guarda en caché).
- Product Ads /ads/search con aggregation_type=DAILY: gasto diario de TODOS
  los anuncios, también los de campañas borradas (campaigns/search no las ve).
  La API lo da sin IVA; aquí se multiplica por 1.16.

Material = costo de la tarjeta (filamento + paquetería) de cada publicación
vinculada en el catálogo; si no está vinculada, el promedio de su categoría.

Deja .claude/mercado/dias/tendencia.md y .json.
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parents[1] / "colecta-full" / "scripts"))
import semana  # noqa: E402
import ml_api  # noqa: E402

HUSO_MX = timezone(timedelta(hours=-6))
IVA = 1.16
CACHE_ENVIOS = Path.home() / ".catalogo3d" / "ml_envios.json"
SALIDA = semana.RAIZ / ".claude" / "mercado" / "dias"

# Del reporte «Distribución de tus costos» de septiembre 2026 (144 ventas):
# otros cargos $1,295 + Full $393 + devoluciones $139 → $12.7 por venta;
# retenciones $2,173 sobre $27,791 → 7.8 %. Suposición mientras no haya otro.
OTROS_POR_VENTA = 12.7
RETENCION = 0.078
LUZ_MES = 1000.0


def pedir_ads(ruta, params):
    url = ml_api.API + ruta + "?" + urllib.parse.urlencode(params)
    pedido = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {ml_api._token_vigente()}",
        "Accept": "application/json", "api-version": "2"})
    with urllib.request.urlopen(pedido, timeout=45) as r:
        return json.loads(r.read())


def ordenes(seller, desde, hasta):
    todas, offset = [], 0
    while True:
        r = ml_api.pedir("/orders/search", {
            "seller": seller, "sort": "date_asc", "limit": 50, "offset": offset,
            "order.date_created.from": f"{desde}T00:00:00.000-06:00",
            "order.date_created.to": f"{hasta}T23:59:59.999-06:00"})
        todas += r["results"]
        offset += 50
        if offset >= r["paging"]["total"]:
            return todas


def costo_envio(sid, cache):
    clave = str(sid)
    if clave not in cache:
        try:
            c = ml_api.pedir(f"/shipments/{sid}/costs")
            cache[clave] = sum(s.get("cost", 0) or 0 for s in c.get("senders", []))
        except ml_api.ErrorML:
            return None
    return cache[clave]


def publicidad(desde, hasta):
    adv = pedir_ads("/advertising/advertisers", {"product_id": "PADS"})
    aid = adv["advertisers"][0]["advertiser_id"]
    r = pedir_ads(f"/advertising/MLM/advertisers/{aid}/product_ads/ads/search", {
        "date_from": desde, "date_to": hasta, "metrics": "cost",
        "limit": 1, "aggregation_type": "DAILY"})
    return {x["date"]: x["cost"] * IVA for x in r["results"]}


def main(argv=None):
    p = argparse.ArgumentParser()
    ayer = datetime.now(HUSO_MX).date() - timedelta(days=1)
    p.add_argument("--desde", type=date.fromisoformat, default=ayer - timedelta(days=29))
    p.add_argument("--hasta", type=date.fromisoformat, default=ayer)
    p.add_argument("--corte", type=date.fromisoformat,
                   help="día en que empezó un cambio, para comparar antes/después")
    p.add_argument("--luz-mes", type=float, default=LUZ_MES)
    a = p.parse_args(argv)

    seller = ml_api.pedir("/users/me")["id"]
    mapa, _ = semana.catalogo()
    costo_pub = {k: v["costo"] for k, v in mapa.items() if v.get("costo")}

    try:
        cache = json.loads(CACHE_ENVIOS.read_text())
    except (OSError, ValueError):
        cache = {}

    lista = ordenes(seller, a.desde.isoformat(), a.hasta.isoformat())
    print(f"{len(lista)} órdenes del {a.desde} al {a.hasta}", file=sys.stderr)

    # Costo de material por categoría, para lo que no está vinculado.
    cat_costos = defaultdict(list)
    titulos = {}
    for o in lista:
        for it in o["order_items"]:
            iid = it["item"]["id"]
            titulos[iid] = it["item"]["title"]
    for iid, c in costo_pub.items():
        if iid in titulos:
            cat_costos[semana.categoria(titulos[iid])].append(c)
    todos = [c for v in cat_costos.values() for c in v] or list(costo_pub.values())
    prom_general = sum(todos) / len(todos)
    prom_cat = {k: sum(v) / len(v) for k, v in cat_costos.items()}

    dias = defaultdict(lambda: defaultdict(float))
    envios_vistos = set()
    for o in lista:
        if o["status"] != "paid":
            continue
        d = datetime.fromisoformat(o["date_created"]).astimezone(HUSO_MX).date().isoformat()
        x = dias[d]
        x["ordenes"] += 1
        for it in o["order_items"]:
            q, iid = it["quantity"], it["item"]["id"]
            x["unidades"] += q
            x["ventas"] += it["unit_price"] * q
            x["comision"] += (it.get("sale_fee") or 0) * q
            c = costo_pub.get(iid)
            if c is None:
                c = prom_cat.get(semana.categoria(it["item"]["title"]), prom_general)
                x["u_material_estimado"] += q
            x["material"] += c * q
        sid = (o.get("shipping") or {}).get("id")
        if sid and sid not in envios_vistos:
            envios_vistos.add(sid)
            e = costo_envio(sid, cache)
            if e is None:
                x["envios_sin_dato"] += 1
            else:
                x["envio"] += e

    CACHE_ENVIOS.write_text(json.dumps(cache))
    try:
        CACHE_ENVIOS.chmod(0o600)
    except OSError:
        pass

    ads = publicidad(a.desde.isoformat(), a.hasta.isoformat())
    luz_dia = a.luz_mes / 30.0

    filas = []
    d = a.desde
    while d <= a.hasta:
        k = d.isoformat()
        x = dias.get(k, defaultdict(float))
        f = {"dia": k, "ordenes": int(x["ordenes"]), "unidades": int(x["unidades"]),
             "ventas": x["ventas"], "comision": x["comision"], "envio": x["envio"],
             "publicidad": ads.get(k, 0.0), "material": x["material"], "luz": luz_dia,
             "u_material_estimado": int(x["u_material_estimado"]),
             "envios_sin_dato": int(x["envios_sin_dato"])}
        f["ganancia_api"] = (f["ventas"] - f["comision"] - f["envio"] - f["publicidad"]
                             - f["material"] - f["luz"])
        f["otros_estimados"] = OTROS_POR_VENTA * f["ordenes"] + RETENCION * f["ventas"]
        f["ganancia"] = f["ganancia_api"] - f["otros_estimados"]
        filas.append(f)
        d += timedelta(days=1)

    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "tendencia.json").write_text(json.dumps(
        {"generado": datetime.now(HUSO_MX).isoformat(timespec="minutes"),
         "corte": a.corte.isoformat() if a.corte else None, "dias": filas},
        ensure_ascii=False, indent=1))
    md = reporte(filas, a.corte)
    (SALIDA / "tendencia.md").write_text(md)
    print(md)
    print(f"→ {SALIDA / 'tendencia.md'}", file=sys.stderr)


def m(x):
    return f"-${-x:,.0f}" if x < 0 else f"${x:,.0f}"


def suma(filas):
    claves = ["ordenes", "unidades", "ventas", "comision", "envio", "publicidad",
              "material", "luz", "ganancia_api", "otros_estimados", "ganancia"]
    return {k: sum(f[k] for f in filas) for k in claves}


def bloque(nombre, filas):
    s = suma(filas)
    n, o = len(filas), max(s["ordenes"], 1)
    return (f"| {nombre} | {n} | {s['unidades'] / n:.1f} | {m(s['ventas'] / o)} | "
            f"{m(s['comision'] / o)} | {m(s['envio'] / o)} | {m(s['publicidad'] / o)} | "
            f"{m(s['material'] / max(s['unidades'], 1))} | {m(s['ganancia'] / o)} | "
            f"**{m(s['ganancia'] / n)}** | {m(s['ganancia'])} |")


def reporte(filas, corte):
    out = ["# Ganancia por día", "",
           "Ventas − comisión − envío − publicidad (con IVA) − material − luz = "
           "**API**. Menos otros cargos ML ($12.7/orden) y retenciones (7.8 %) "
           "estimados de septiembre = **Neta**.", "",
           "Ventas, comisión, envío y publicidad: medido (API). Material: "
           "costo de tarjeta del catálogo (correlación). Luz, otros cargos y "
           "retenciones: suposición.", ""]

    out += ["## Por periodo", "",
            "| Periodo | Días | u/día | Ticket | Comisión/orden | Envío/orden | "
            "Publicidad/orden | Material/u | Neta/orden | Neta/día | Neta total |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    semanas = defaultdict(list)
    for f in filas:
        lunes = date.fromisoformat(f["dia"])
        lunes -= timedelta(days=lunes.weekday())
        semanas[lunes].append(f)
    for lunes in sorted(semanas):
        out.append(bloque(f"Semana del {lunes:%d/%m}", semanas[lunes]))
    if corte:
        antes = [f for f in filas if date.fromisoformat(f["dia"]) < corte]
        despues = [f for f in filas if date.fromisoformat(f["dia"]) >= corte]
        if antes:
            out.append(bloque(f"Antes del {corte:%d/%m}", antes))
        if despues:
            out.append(bloque(f"Desde el {corte:%d/%m}", despues))
    out.append(bloque("Todo", filas))

    out += ["", "## Día por día", "",
            "| Día | Órd. | Ventas | Comisión | Envío | Publicidad | Material | "
            "API | Neta |", "|---|---|---|---|---|---|---|---|---|"]
    for f in filas:
        dia = date.fromisoformat(f["dia"])
        nota = []
        if f["u_material_estimado"]:
            nota.append(f"{f['u_material_estimado']} u material estimado")
        if f["envios_sin_dato"]:
            nota.append(f"{f['envios_sin_dato']} envíos sin dato")
        marca = " ←" if corte and dia == corte else ""
        out.append(
            f"| {dia:%a %d/%m}{marca} | {f['ordenes']} | {m(f['ventas'])} | "
            f"{m(-f['comision'])} | {m(-f['envio'])} | {m(-f['publicidad'])} | "
            f"{m(-f['material'])} | {m(f['ganancia_api'])} | **{m(f['ganancia'])}**"
            f"{' (' + ', '.join(nota) + ')' if nota else ''} |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    main()
