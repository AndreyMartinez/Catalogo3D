#!/usr/bin/env python3
"""Las cifras de una semana de ventas, sacadas siempre de la misma manera.

Lee lo que dejó `colecta-full/scripts/traer_datos.py` en ~/.catalogo3d/ml_datos.json
y lo cruza con el catálogo (peso, retorno y paquetería de cada diseño). No le
pega a la API: si los datos son viejos, lo dice y sigue.

Uso:
  python3 semana.py                      # la última semana cerrada (lunes a domingo)
  python3 semana.py --hasta 2026-10-04   # la semana que termina ese domingo

Deja dos archivos en .claude/mercado/:
  datos/AAAA-Www.json   las cifras crudas, para comparar semanas después
  datos/AAAA-Www.md     las tablas, listas para pegar en el reporte

La semana es lunes a domingo en hora local. Un día es de la semana si la
orden se creó ese día según MercadoLibre (por_dia de traer_datos).
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DATOS_ML = Path.home() / ".catalogo3d" / "ml_datos.json"
CARPETA_DISENOS = Path.home() / "Desktop" / "own design 3d"
RAIZ = Path(__file__).resolve().parents[4]          # .../Catalogo3D
SALIDA = RAIZ / ".claude" / "mercado" / "datos"

# El título manda la categoría. Orden importa: "control" antes que cualquier
# cosa que también diga "organizador".
CATEGORIAS = [
    ("control", "Portacontroles"), ("cubiertos", "Portacubiertos"),
    ("cepillos", "Portacepillos"), ("lapices", "Portalápices"),
    ("lápices", "Portalápices"), ("origami", "Figuras"), ("gato", "Figuras"),
    ("perro", "Figuras"), ("jirafa", "Figuras"), ("florero", "Floreros"),
    ("maceta", "Macetas"), ("huevos", "Cocina"),
]


def categoria(titulo):
    t = titulo.lower()
    for clave, nombre in CATEGORIAS:
        if clave in t:
            return nombre
    return "Otros"


def semana_de(hasta):
    """(lunes, domingo) de la semana que termina en `hasta` o antes."""
    domingo = hasta - timedelta(days=(hasta.weekday() + 1) % 7)
    return domingo - timedelta(days=6), domingo


def unidades(por_dia, desde, hasta):
    return sum(n for d, n in por_dia.items()
               if desde <= date.fromisoformat(d) <= hasta)


def catalogo():
    """MLM id -> datos del diseño (peso, retorno, costo por pieza)."""
    try:
        ml = json.loads((CARPETA_DISENOS / ".catalogo3d_mercadolibre.json")
                        .read_text(encoding="utf-8"))
        costos = json.loads((CARPETA_DISENOS / ".catalogo3d_costos.json")
                            .read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, None
    precio_kg = float(costos.get("precio_kg", 0) or 0)
    paquetes = costos.get("paquetes") or []
    activo = int(costos.get("paquete_activo", 0) or 0)

    def total_paquete(i):
        if i is None or not (0 <= i < len(paquetes)):
            return 0.0
        p = paquetes[i]
        if "total" in p:
            return float(p["total"])
        return sum(e["costo_compra"] / max(e["unidades"], 1) for e in p["elementos"])

    mapa = {}
    for archivo, d in ml.items():
        ids = re.findall(r"MLM\d{6,}", d.get("link", "") or "")
        if not ids:
            continue
        peso = d.get("peso_g")
        # La misma cuenta que la tarjeta: material + paquetería (la del diseño
        # si la trae, si no la del catálogo). Un costo escrito a mano manda.
        costo = d.get("costo")
        if costo is None and peso:
            paq = d.get("paquete", activo)
            costo = peso / 1000.0 * precio_kg + total_paquete(paq)
        info = {"archivo": archivo, "peso_g": peso, "retorno": d.get("retorno"),
                "costo": round(costo, 2) if costo is not None else None}
        for i in ids:
            mapa[i] = info
    return mapa, {"precio_kg": precio_kg,
                  "paquete": total_paquete(activo)}


def tendencia(u, prom4):
    if prom4 >= 2 and u >= 1.5 * prom4 and u >= 3:
        return "sube"
    if prom4 >= 2 and u <= 0.5 * prom4:
        return "baja"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hasta", help="un día de la semana a reportar (AAAA-MM-DD); "
                    "por defecto, el último domingo")
    a = ap.parse_args()

    if not DATOS_ML.exists():
        print("No hay datos. Corre antes colecta-full/scripts/traer_datos.py")
        return 1
    crudo = json.loads(DATOS_ML.read_text(encoding="utf-8"))
    generado = datetime.fromisoformat(crudo["generado"])
    hoy = date.today()
    lunes, domingo = semana_de(date.fromisoformat(a.hasta) if a.hasta else hoy)
    lunes_prev, domingo_prev = lunes - timedelta(days=7), domingo - timedelta(days=7)
    lunes_4 = lunes - timedelta(days=28)
    viejo = generado.astimezone().date() < domingo
    iso = lunes.isocalendar()
    etiqueta = "%d-W%02d" % (iso[0], iso[1])

    pubs, ventas = crudo.get("publicaciones", {}), crudo.get("ventas", {})
    mapa, costos = catalogo()

    filas = []
    for mid, v in ventas.items():
        pd = v.get("por_dia", {})
        p = pubs.get(mid, {})
        u = unidades(pd, lunes, domingo)
        up = unidades(pd, lunes_prev, domingo_prev)
        u4 = unidades(pd, lunes_4, lunes - timedelta(days=1)) / 4.0
        dias = sorted(pd)
        primera = date.fromisoformat(dias[0]) if dias else None
        ultima = date.fromisoformat(dias[-1]) if dias else None
        info = mapa.get(mid, {})
        ganancia_u = (info["retorno"] - info["costo"]
                      if info.get("retorno") is not None and info.get("costo") is not None
                      else None)
        alertas = []
        t = tendencia(u, u4)
        if t:
            alertas.append(t)
        if ultima and (domingo - ultima).days >= 14 and v.get("unidades", 0) >= 4:
            alertas.append("dormida")
        if primera and (domingo - primera).days <= 21:
            alertas.append("nueva")
        filas.append({
            "id": mid, "titulo": v.get("titulo", ""), "categoria": categoria(v.get("titulo", "")),
            "full": p.get("logistic_type") == "fulfillment", "precio": p.get("precio"),
            "semana": u, "semana_previa": up, "promedio_4": round(u4, 2),
            "unidades_90d": v.get("unidades", 0), "diseno": info.get("archivo"),
            "ganancia_u": round(ganancia_u, 2) if ganancia_u is not None else None,
            "ganancia_semana": round(ganancia_u * u, 2) if ganancia_u is not None else None,
            "alertas": alertas,
        })
    filas.sort(key=lambda f: (-f["semana"], -f["promedio_4"]))

    cats = defaultdict(lambda: {"semana": 0, "semana_previa": 0, "promedio_4": 0.0,
                                "publicaciones": 0, "en_full": 0})
    for f in filas:
        c = cats[f["categoria"]]
        c["semana"] += f["semana"]
        c["semana_previa"] += f["semana_previa"]
        c["promedio_4"] += f["promedio_4"]
        c["publicaciones"] += 1
        c["en_full"] += f["full"]
    total = sum(f["semana"] for f in filas)
    total_prev = sum(f["semana_previa"] for f in filas)
    prom4 = sum(f["promedio_4"] for f in filas)
    con_ganancia = [f for f in filas if f["ganancia_semana"] is not None]
    u_con = sum(f["semana"] for f in con_ganancia)

    resumen = {
        "semana": etiqueta, "desde": lunes.isoformat(), "hasta": domingo.isoformat(),
        "datos_generados": crudo["generado"], "datos_viejos": viejo,
        "unidades": total, "unidades_previa": total_prev, "promedio_4": round(prom4, 1),
        "ganancia_estimada": round(sum(f["ganancia_semana"] for f in con_ganancia), 2),
        "unidades_con_costo": u_con, "costos": costos,
        "categorias": {k: dict(v, promedio_4=round(v["promedio_4"], 1))
                       for k, v in sorted(cats.items(), key=lambda kv: -kv[1]["semana"])},
        "publicaciones": filas,
    }

    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / (etiqueta + ".json")).write_text(
        json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")

    def flecha(a, b):
        return "→" if a == b else ("↑" if a > b else "↓")

    md = ["## Cifras %s (%s a %s)" % (etiqueta, lunes.strftime("%d/%m"), domingo.strftime("%d/%m")), ""]
    if viejo:
        md += ["> ⚠️ Los datos se bajaron el %s, antes de que cerrara la semana: "
               "faltan días." % generado.astimezone().strftime("%d/%m %H:%M"), ""]
    md += ["**%d unidades** %s %d la semana anterior · promedio de las 4 previas: %.1f"
           % (total, flecha(total, total_prev), total_prev, prom4), ""]
    if con_ganancia:
        md += ["Ganancia estimada: **$%.2f** sobre %d de %d unidades (las que tienen "
               "peso y retorno en el catálogo)." % (resumen["ganancia_estimada"], u_con, total), ""]
    md += ["| Categoría | Semana | Anterior | Prom. 4 sem | Publicaciones | En Full |",
           "|---|---|---|---|---|---|"]
    for k, c in resumen["categorias"].items():
        md.append("| %s | %d | %d | %.1f | %d | %d |" % (
            k, c["semana"], c["semana_previa"], c["promedio_4"], c["publicaciones"], c["en_full"]))
    md += ["", "| Publicación | Cat. | Full | Semana | Ant. | Prom. 4 | Ganancia/u | Alertas |",
           "|---|---|---|---|---|---|---|---|"]
    for f in filas:
        if f["semana"] == 0 and f["promedio_4"] < 0.5 and not f["alertas"]:
            continue
        md.append("| %s · %s | %s | %s | %d | %d | %.1f | %s | %s |" % (
            f["titulo"][:48], f["id"], f["categoria"], "sí" if f["full"] else "no",
            f["semana"], f["semana_previa"], f["promedio_4"],
            "$%.2f" % f["ganancia_u"] if f["ganancia_u"] is not None else "—",
            ", ".join(f["alertas"])))
    sin_mapa = sorted({f["titulo"][:40] for f in filas if f["diseno"] is None and f["semana"]})
    if sin_mapa:
        md += ["", "Sin diseño vinculado en el catálogo (no entran a la ganancia): "
               + "; ".join(sin_mapa)]
    (SALIDA / (etiqueta + ".md")).write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print("\n→ %s" % (SALIDA / (etiqueta + ".json")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
