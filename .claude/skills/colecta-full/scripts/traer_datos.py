#!/usr/bin/env python3
"""Baja de MercadoLibre lo que hace falta para planear la colecta:
publicaciones, stock en Full y ventas de los últimos N días.

Deja todo crudo en ~/.catalogo3d/ml_datos.json para que plan.py calcule
sin volver a pegarle a la API.

Uso:  python3 scripts/traer_datos.py [--dias 90]
"""
import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ml_api  # noqa: E402

SALIDA = ml_api.CARPETA / "ml_datos.json"
# Se piden las órdenes por ventanas: los rangos largos a veces los corta
# la API sin avisar, y así además se nota si una ventana viene vacía.
DIAS_POR_VENTANA = 30


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000-00:00")


def listar_publicaciones(seller_id):
    """Todas las publicaciones del vendedor. Usa scan porque el offset
    normal se topa a las 1000."""
    ids, scroll = [], None
    while True:
        params = {"search_type": "scan", "limit": 100}
        if scroll:
            params["scroll_id"] = scroll
        r = ml_api.pedir(f"/users/{seller_id}/items/search", params)
        lote = r.get("results") or []
        ids.extend(lote)
        scroll = r.get("scroll_id")
        if not lote or not scroll:
            break
    return ids


def detalle_publicaciones(ids):
    """Multiget de 20 en 20."""
    salida = {}
    for i in range(0, len(ids), 20):
        trozo = ids[i:i + 20]
        r = ml_api.pedir("/items", {"ids": ",".join(trozo)})
        for entrada in r:
            if entrada.get("code") != 200:
                continue
            it = entrada.get("body") or {}
            salida[it.get("id")] = it
        time.sleep(0.2)
    return salida


def inventarios_de(item):
    """Los inventory_id de una publicación en Full: al nivel del ítem o,
    si tiene variantes, uno por variante."""
    encontrados = []
    if item.get("inventory_id"):
        encontrados.append((None, item["inventory_id"]))
    for v in item.get("variations") or []:
        if v.get("inventory_id"):
            encontrados.append((v.get("id"), v["inventory_id"]))
    return encontrados


def stock_full(inventory_id, seller_id):
    try:
        return ml_api.pedir(
            f"/marketplace/inventories/{inventory_id}/stock/fulfillment",
            {"seller_id": seller_id})
    except ml_api.ErrorML as e:
        return {"error": str(e)}


def traer_ordenes(seller_id, desde, hasta):
    ordenes, ventana = [], desde
    while ventana < hasta:
        fin = min(ventana + timedelta(days=DIAS_POR_VENTANA), hasta)
        offset = 0
        while True:
            r = ml_api.pedir("/orders/search", {
                "seller": seller_id,
                "order.status": "paid",
                "order.date_created.from": iso(ventana),
                "order.date_created.to": iso(fin),
                "sort": "date_desc",
                "offset": offset,
                "limit": 50,
            })
            lote = r.get("results") or []
            ordenes.extend(lote)
            paging = r.get("paging") or {}
            offset += 50
            if not lote or offset >= int(paging.get("total") or 0):
                break
            time.sleep(0.2)
        ventana = fin
    return ordenes


def resumir_ordenes(ordenes):
    """Unidades vendidas por publicación y por día, separando Full del
    resto: lo que sale de tu casa no se repone con una colecta."""
    por_item = {}
    for o in ordenes:
        fecha = (o.get("date_created") or "")[:10]
        # 'fulfilled' no distingue el canal; el tipo de logística vive en
        # el envío, así que se marca la orden y plan.py decide.
        for li in o.get("order_items") or []:
            item = li.get("item") or {}
            iid = item.get("id")
            if not iid:
                continue
            reg = por_item.setdefault(iid, {
                "titulo": item.get("title"),
                "seller_sku": item.get("seller_sku"),
                "variantes": {},
                "por_dia": {},
                "unidades": 0,
            })
            cant = int(li.get("quantity") or 0)
            reg["unidades"] += cant
            reg["por_dia"][fecha] = reg["por_dia"].get(fecha, 0) + cant
            vid = str(item.get("variation_id") or "")
            if vid:
                reg["variantes"][vid] = reg["variantes"].get(vid, 0) + cant
    return por_item


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=90,
                    help="ventana de historial de ventas (por defecto 90)")
    args = ap.parse_args()

    try:
        yo = ml_api.pedir("/users/me")
    except ml_api.ErrorML as e:
        print(e)
        return 1
    seller_id = yo["id"]
    print(f"Vendedor {yo.get('nickname')} ({seller_id}), sitio {yo.get('site_id')}")

    print("Publicaciones...", end=" ", flush=True)
    ids = listar_publicaciones(seller_id)
    print(f"{len(ids)}")

    detalles = detalle_publicaciones(ids)
    publicaciones = {}
    en_full = 0
    for iid, it in detalles.items():
        envio = it.get("shipping") or {}
        logistica = envio.get("logistic_type")
        reg = {
            "id": iid,
            "titulo": it.get("title"),
            "estado": it.get("status"),
            "seller_sku": it.get("seller_custom_field"),
            "precio": it.get("price"),
            "logistic_type": logistica,
            "disponible_publicado": it.get("available_quantity"),
            "full": {},
        }
        for var_id, inv_id in inventarios_de(it):
            reg["full"][inv_id] = {
                "variation_id": var_id,
                "stock": stock_full(inv_id, seller_id),
            }
            time.sleep(0.15)
        if reg["full"]:
            en_full += 1
        publicaciones[iid] = reg
    print(f"En Full: {en_full} de {len(publicaciones)}")

    hasta = datetime.now(timezone.utc)
    desde = hasta - timedelta(days=args.dias)
    print(f"Ventas de los últimos {args.dias} días...", end=" ", flush=True)
    ordenes = traer_ordenes(seller_id, desde, hasta)
    ventas = resumir_ordenes(ordenes)
    print(f"{len(ordenes)} órdenes, {sum(v['unidades'] for v in ventas.values())} unidades")

    datos = {
        "generado": hasta.isoformat(),
        "seller_id": seller_id,
        "site_id": yo.get("site_id"),
        "dias_historial": args.dias,
        "publicaciones": publicaciones,
        "ventas": ventas,
    }
    ml_api._guardar_privado(SALIDA, datos)
    print(f"Guardado en {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
