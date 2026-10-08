#!/usr/bin/env python3
"""Calcula cuándo programar la colecta, cuánto mandar de cada diseño y en
qué orden imprimirlo.

Lee lo que dejó traer_datos.py, el config.json del skill y el archivo de
vínculos con MercadoLibre del propio catálogo (para el peso de cada pieza).

Uso:  python3 scripts/plan.py [--json] [--config ruta]
"""
import argparse
import json
import math
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ml_api  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
DATOS = ml_api.CARPETA / "ml_datos.json"
NOMBRE_ARCHIVO_ML = ".catalogo3d_mercadolibre.json"
VENTANAS = (14, 30, 60)
RE_ITEM = re.compile(r"\bML[ABCMU]?[A-Z]?(\d{8,})\b")


# ---------------------------------------------------------------- catálogo
def item_del_link(link: str):
    """Saca el id de publicación de un link de ML. Los links de la vista
    de vendedor traen /publicaciones/MLM...; los públicos lo esconden en
    wid=MLM... y además traen un MLMU..., que es el producto, no el ítem."""
    if not link:
        return None
    m = re.search(r"/publicaciones/(ML[A-Z]\d{8,})", link)
    if m:
        return m.group(1)
    m = re.search(r"[?&]wid=(ML[A-Z]\d{8,})", link)
    if m:
        return m.group(1)
    for cand in re.findall(r"\bML[A-Z]\d{8,}\b", link):
        if not cand.startswith(("MLMU", "MLAU", "MLBU", "MLCU")):
            return cand
    return None


def cargar_catalogo(carpeta: Path):
    """{item_id: {archivo, peso_g, retorno}} + los diseños sin vincular."""
    ruta = carpeta / NOMBRE_ARCHIVO_ML
    if not ruta.exists():
        return {}, []
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    por_item, sueltos = {}, []
    for archivo, d in datos.items():
        iid = item_del_link(d.get("link"))
        reg = {"archivo": archivo, "peso_g": d.get("peso_g"),
               "retorno": d.get("retorno"), "precio_venta": d.get("precio_venta")}
        if iid:
            por_item[iid] = reg
        else:
            sueltos.append(reg)
    return por_item, sueltos


# ------------------------------------------------------------------ ventas
def tasa_diaria(por_dia: dict, hoy: date, dias_hist: int):
    """Unidades por día. Se miran tres ventanas y se pondera hacia lo
    reciente, pero solo con las ventanas que de verdad tienen historial."""
    conteos = {}
    for v in VENTANAS:
        corte = hoy - timedelta(days=v)
        u = sum(c for f, c in por_dia.items()
                if f and date.fromisoformat(f) > corte)
        conteos[v] = {"unidades": u, "dias": min(v, dias_hist),
                      "tasa": u / max(1, min(v, dias_hist))}

    pesos = {14: 0.5, 30: 0.3, 60: 0.2}
    usables = {v: p for v, p in pesos.items() if conteos[v]["dias"] >= v * 0.8}
    if not usables:
        usables = {max(conteos, key=lambda v: conteos[v]["dias"]): 1.0}
    total_peso = sum(usables.values())
    tasa = sum(conteos[v]["tasa"] * p for v, p in usables.items()) / total_peso

    u60 = conteos[60]["unidades"]
    confianza = "alta" if u60 >= 20 else "media" if u60 >= 8 else "baja"
    return round(tasa, 4), conteos, confianza


def stock_en_full(pub: dict):
    total, roto = 0, False
    for inv in (pub.get("full") or {}).values():
        st = inv.get("stock") or {}
        if "error" in st:
            roto = True
            continue
        total += int(st.get("available_quantity") or 0)
    return total, roto


# ------------------------------------------------------------------- plan
def construir(datos, cfg, catalogo, hoy):
    dias_hist = int(datos.get("dias_historial") or 90)
    lead = int(cfg["dias_lead_full"])
    colchon = int(cfg["colchon_dias"])
    cobertura = int(cfg["cobertura_objetivo_dias"])

    filas = []
    for iid, pub in (datos.get("publicaciones") or {}).items():
        if pub.get("estado") not in (None, "active", "paused"):
            continue
        venta = (datos.get("ventas") or {}).get(iid) or {}
        tasa, conteos, confianza = tasa_diaria(
            venta.get("por_dia") or {}, hoy, dias_hist)
        stock, stock_roto = stock_en_full(pub)
        esta_en_full = bool(pub.get("full")) or pub.get("logistic_type") == "fulfillment"

        if not esta_en_full and not cfg.get("incluir_no_full", True):
            continue

        dias_quiebre = stock / tasa if tasa > 0 else None
        objetivo = tasa * (cobertura + lead)
        enviar = max(0, math.ceil(objetivo - stock))
        if not esta_en_full:
            # aún no está en Full: no hay stock que reponer, es un alta
            enviar = max(enviar, int(cfg.get("minimo_por_sku", 0)))
        if tasa == 0 and esta_en_full:
            enviar = 0  # no se vendió nada en la ventana: no mandes más

        cat = catalogo.get(iid) or {}
        peso = cat.get("peso_g")
        override = (cfg.get("horas_por_pieza") or {}).get(cat.get("archivo") or "")
        if override:
            horas_pieza = float(override)
            origen_horas = "manual"
        elif peso:
            horas_pieza = float(peso) / float(cfg["gramos_por_hora"])
            origen_horas = "estimado del peso"
        else:
            horas_pieza = None
            origen_horas = "sin dato"

        filas.append({
            "item_id": iid,
            "titulo": pub.get("titulo") or venta.get("titulo") or iid,
            "archivo": cat.get("archivo"),
            "en_full": esta_en_full,
            "stock_full": stock,
            "stock_incompleto": stock_roto,
            "tasa_dia": tasa,
            "confianza": confianza,
            "ventana": {str(v): conteos[v]["unidades"] for v in VENTANAS},
            "dias_hasta_quiebre": (round(dias_quiebre, 1)
                                   if esta_en_full and dias_quiebre is not None else None),
            "fecha_quiebre": ((hoy + timedelta(days=dias_quiebre)).isoformat()
                              if esta_en_full and dias_quiebre is not None else None),
            "enviar": enviar,
            "peso_g": peso,
            "horas_pieza": round(horas_pieza, 2) if horas_pieza else None,
            "origen_horas": origen_horas,
            "retorno": cat.get("retorno"),
        })

    # La colecta se programa contra el diseño que se queda sin stock primero,
    # mirando solo lo que ya está en Full y de verdad se vende.
    quiebres = [f["dias_hasta_quiebre"] for f in filas
                if f["en_full"] and f["dias_hasta_quiebre"] is not None]
    if quiebres:
        margen = min(quiebres) - lead - colchon
        dias_a_colecta = max(0, math.floor(margen))
        apremia = margen < 0
    else:
        dias_a_colecta = max(0, cobertura - lead - colchon)
        apremia = False
    fecha_colecta = hoy + timedelta(days=dias_a_colecta)

    horas_dia_total = float(cfg["impresoras"]) * float(cfg["horas_por_dia"])
    if horas_dia_total <= 0:
        raise SystemExit("config.json: 'impresoras' y 'horas_por_dia' tienen "
                         "que ser mayores que cero.")

    # Prioridad: lo que se acaba antes va primero; a igualdad, lo que deja
    # más dinero por hora de impresora.
    def orden(f):
        urgencia = f["dias_hasta_quiebre"]
        if urgencia is None:
            urgencia = 9999 if f["en_full"] else 900  # altas nuevas, a media tabla
        rendimiento = 0.0
        if f["retorno"] and f["horas_pieza"]:
            rendimiento = f["retorno"] / f["horas_pieza"]
        return (urgencia, -rendimiento)

    # Se imprime en fila, una cosa tras otra, así que lo que vale es cuándo
    # queda lista cada pieza — no si "cabe" en una bolsa de horas.
    cola = sorted([f for f in filas if f["enviar"] > 0], key=orden)
    acumulado, secuencia, tarde, sin_estimar = 0.0, [], [], []
    for f in cola:
        hp = f["horas_pieza"]
        if hp is None:
            sin_estimar.append(f)
            secuencia.append({**f, "horas_total": None, "fecha_lista": None,
                              "llega": None})
            continue
        necesita = hp * f["enviar"]
        acumulado += necesita
        lista = hoy + timedelta(days=math.ceil(acumulado / horas_dia_total))
        registro = {**f, "horas_total": round(necesita, 1),
                    "horas_acumuladas": round(acumulado, 1),
                    "fecha_lista": lista.isoformat(),
                    "llega": lista <= fecha_colecta}
        llega = registro["llega"]
        secuencia.append(registro)
        if not llega:
            tarde.append(registro)

    dias_necesarios = math.ceil(acumulado / horas_dia_total)
    fecha_todo_listo = hoy + timedelta(days=dias_necesarios)

    return {
        "hoy": hoy.isoformat(),
        "fecha_colecta": fecha_colecta.isoformat(),
        "dias_a_colecta": dias_a_colecta,
        "apremia": apremia,
        "lead": lead,
        "horas_dia_total": horas_dia_total,
        "horas_necesarias": round(acumulado, 1),
        "dias_necesarios": dias_necesarios,
        "fecha_todo_listo": fecha_todo_listo.isoformat(),
        "fecha_colecta_realista": max(fecha_colecta,
                                      fecha_todo_listo + timedelta(days=1)).isoformat(),
        "secuencia": secuencia,
        "tarde": tarde,
        "sin_estimar": [f["item_id"] for f in sin_estimar],
        "filas": filas,
    }


# ---------------------------------------------------------------- reporte
def imprimir(p, sueltos, dias_hist):
    print(f"\n# Plan de colecta — {p['hoy']}\n")
    if p["apremia"]:
        print(f"⚠️  Vas tarde: al ritmo actual algo se queda sin stock antes de "
              f"que una colecta de hoy alcance a activarse ({p['lead']} días de lead).")
        print("   La fecha de abajo es 'lo antes posible', no 'con margen'.\n")
    print(f"**Colecta sugerida: {p['fecha_colecta']}** "
          f"(en {p['dias_a_colecta']} días)")
    print(f"Para esa fecha necesitas {p['horas_necesarias']} h de impresión; "
          f"a {p['horas_dia_total']:.0f} h/día eso son {p['dias_necesarios']} días "
          f"(terminas el {p['fecha_todo_listo']}).")
    if p["tarde"]:
        print(f"→ **No llegas.** {len(p['tarde'])} diseños quedan listos después "
              f"de la colecta. La fecha que sí aguanta es "
              f"**{p['fecha_colecta_realista']}**.")
    else:
        print("→ Llegas con lo que tienes.")

    print("\n## Qué mandar\n")
    print("| Diseño | En Full | Venta/día | Se acaba | Mandar | Horas |")
    print("|---|---:|---:|---|---:|---:|")
    for f in sorted(p["filas"], key=lambda x: (x["dias_hasta_quiebre"] is None,
                                               x["dias_hasta_quiebre"] or 0)):
        if f["enviar"] == 0 and f["stock_full"] == 0 and f["tasa_dia"] == 0:
            continue
        nombre = f["archivo"] or f["titulo"][:38]
        quiebre = f["fecha_quiebre"] or ("—" if f["en_full"] else "no está en Full")
        horas = (f"{f['horas_pieza'] * f['enviar']:.1f}"
                 if f["horas_pieza"] and f["enviar"] else "—")
        marca = "" if f["confianza"] == "alta" else f" ({f['confianza']})"
        print(f"| {nombre} | {f['stock_full'] if f['en_full'] else '–'} "
              f"| {f['tasa_dia']:.2f}{marca} | {quiebre} | **{f['enviar']}** | {horas} |")

    print("\n## Orden de impresión\n")
    if not p["secuencia"]:
        print("Nada que imprimir: el stock en Full cubre la demanda.")
    for i, f in enumerate(p["secuencia"], 1):
        nombre = f["archivo"] or f["titulo"][:38]
        if f["horas_pieza"] is None:
            print(f"{i}. {nombre} — {f['enviar']} u · sin peso en el catálogo, "
                  f"no puedo estimar horas")
            continue
        marca = "" if f["llega"] else "  ← queda lista DESPUÉS de la colecta"
        aviso = ""
        if f["fecha_quiebre"] and f["fecha_lista"] > f["fecha_quiebre"]:
            aviso = f"  ⚠️ se te acaba el stock el {f['fecha_quiebre']}"
        print(f"{i}. {nombre} — {f['enviar']} u · {f['horas_total']} h "
              f"({f['horas_pieza']} h/pieza, {f['origen_horas']}) → "
              f"lista el {f['fecha_lista']}{marca}{aviso}")

    if p["tarde"]:
        print("\n## Lo que no llega\n")
        for f in p["tarde"]:
            print(f"- **{f['archivo'] or f['titulo'][:38]}**: {f['enviar']} u, "
                  f"{f['horas_total']} h, lista el {f['fecha_lista']} "
                  f"(colecta el {p['fecha_colecta']}).")
        print(f"\nTres salidas: correr la colecta al {p['fecha_colecta_realista']}, "
              f"mandar menos unidades de los que más tardan, o subir "
              f"horas/impresoras en config.json.")

    flojos = [f for f in p["filas"] if f["confianza"] == "baja" and f["enviar"] > 0]
    sin_peso = [f for f in p["filas"] if f["enviar"] > 0 and not f["peso_g"]]
    if flojos or sin_peso or sueltos:
        print("\n## Qué tan confiable es esto\n")
        print(f"Historial usado: {dias_hist} días.")
        if flojos:
            print(f"- {len(flojos)} diseños con menos de 8 ventas en 60 días: "
                  "su número es una corazonada, no un promedio.")
        if sin_peso:
            print(f"- {len(sin_peso)} sin peso en el catálogo: no entran en el "
                  "cálculo de horas. Ponles el gramaje en la galería.")
        if sueltos:
            print(f"- {len(sueltos)} diseños del catálogo sin link de ML: no se "
                  "pueden cruzar con sus ventas. Vincúlalos con «🔗 Vincular ML».")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--config", default=str(RAIZ / "config.json"))
    ap.add_argument("--datos", default=str(DATOS),
                    help="otro ml_datos.json (para probar sin pegarle a la API)")
    args = ap.parse_args()

    ruta_datos = Path(args.datos).expanduser()
    if not ruta_datos.exists():
        print(f"Faltan los datos. Corre primero:\n"
              f"  python3 {RAIZ}/scripts/traer_datos.py")
        return 1
    datos = json.loads(ruta_datos.read_text(encoding="utf-8"))
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    carpeta = Path(cfg.get("carpeta_disenos", "~/Desktop/own design 3d")).expanduser()
    catalogo, sueltos = cargar_catalogo(carpeta)

    hoy = datetime.fromisoformat(datos["generado"]).date()
    p = construir(datos, cfg, catalogo, hoy)

    if args.json:
        print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        imprimir(p, sueltos, datos.get("dias_historial"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
