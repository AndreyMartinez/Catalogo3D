#!/usr/bin/env python3
"""Tablero de productos nuevos: de la idea al veredicto.

    tablero.py ver [slug]
    tablero.py nuevo <slug> --nombre N --categoria C [--origen archivo.md]
    tablero.py fase <slug> <fase> [--nota T] [--gramos G] [--horas H]
    tablero.py publicar <slug> <MLM...> [--precio P]
    tablero.py veredicto <slug> <escalar|potenciar|iterar|retirar> [--nota T]

Solo biblioteca estándar. Las ventas salen de ~/.catalogo3d/ml_datos.json,
el archivo que baja colecta-full; este script no habla con la API.
"""
import argparse
import json
import os
import statistics
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CONFIG = json.loads((SKILL / "config.json").read_text(encoding="utf-8"))
ML_DATOS = Path.home() / ".catalogo3d" / "ml_datos.json"

FASES = ["investigado", "propuesto", "diseno", "impreso", "publicado", "cerrado"]
VEREDICTOS = ["escalar", "potenciar", "iterar", "retirar"]


def carpeta_datos():
    """`.claude/productos` del repo principal, aunque se corra en un worktree:
    lo que se registra tiene que sobrevivir a que el worktree se borre."""
    if os.environ.get("PRODUCTOS_DIR"):
        return Path(os.environ["PRODUCTOS_DIR"]).expanduser()
    try:
        comun = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=SKILL, capture_output=True, text=True, check=True).stdout.strip()
        return Path(comun).parent / ".claude" / "productos"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return SKILL.parent.parent / "productos"


DATOS = carpeta_datos()
TABLERO = DATOS / "tablero.json"


def hoy():
    return date.today().isoformat()


def cargar():
    if TABLERO.exists():
        return json.loads(TABLERO.read_text(encoding="utf-8"))
    return {"productos": {}}


def guardar(t):
    DATOS.mkdir(parents=True, exist_ok=True)
    TABLERO.write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding="utf-8")


def anotar(slug, texto):
    """Deja la huella en el archivo del producto: el tablero dice dónde está,
    el .md dice por qué."""
    ruta = DATOS / f"{slug}.md"
    with ruta.open("a", encoding="utf-8") as f:
        f.write(f"- **{hoy()}** — {texto}\n")


def producto(t, slug):
    if slug not in t["productos"]:
        sys.exit(f"No existe «{slug}». Productos: {', '.join(t['productos']) or 'ninguno'}")
    return t["productos"][slug]


# ---------------------------------------------------------------- ventas

def ventas_ml():
    if not ML_DATOS.exists():
        return None
    return json.loads(ML_DATOS.read_text(encoding="utf-8"))


def categoria_de(titulo):
    t = (titulo or "").lower()
    for cat, palabras in CONFIG["categorias"].items():
        if any(p in t for p in palabras):
            return cat
    return "otras"


def _fecha(s):
    """Fecha local: ml_datos.json guarda `generado` en UTC y de noche en
    México eso ya es mañana."""
    if "T" in s:
        return datetime.fromisoformat(s).astimezone().date()
    return date.fromisoformat(s[:10])


def lineas_base(ml):
    """Mediana de unidades/semana por publicación, por categoría.

    Las semanas se cuentan desde la primera venta dentro de la ventana (o el
    inicio de la ventana si vendía desde antes): una publicación nueva no se
    castiga por las semanas en que no existía. Es una aproximación — la
    fecha real de alta no viene en ml_datos.json."""
    generado = _fecha(ml["generado"])
    inicio = generado.toordinal() - ml.get("dias_historial", 90)
    por_cat = {}
    titulos = {k: p.get("titulo") for k, p in ml.get("publicaciones", {}).items()}
    for iid, v in ml.get("ventas", {}).items():
        dias = sorted(v.get("por_dia", {}))
        if not dias:
            continue
        desde = max(inicio, _fecha(dias[0]).toordinal())
        semanas = max(1.0, (generado.toordinal() - desde) / 7)
        cat = categoria_de(titulos.get(iid) or v.get("titulo"))
        por_cat.setdefault(cat, []).append(v.get("unidades", 0) / semanas)
    return {c: (statistics.median(x), len(x)) for c, x in por_cat.items()}


def ventas_desde(ml, item_id, desde):
    v = (ml or {}).get("ventas", {}).get(item_id)
    if not v:
        return 0
    return sum(n for d, n in v.get("por_dia", {}).items() if d >= desde)


# ---------------------------------------------------------------- comandos

def semanas_publicado(p):
    if not p.get("publicado"):
        return None
    return (date.today() - date.fromisoformat(p["publicado"])).days / 7


def revision_pendiente(p):
    s = semanas_publicado(p)
    if s is None or p["fase"] == "cerrado":
        return None
    hechas = set(p.get("revisiones", []))
    vencidas = [w for w in CONFIG["revisiones_semanas"] if s >= w and w not in hechas]
    return vencidas[-1] if vencidas else None


def evaluar(p, ml, bases):
    """Unidades, ritmo y comparación contra su categoría; None si no aplica."""
    if not (p.get("publicado") and p.get("ml_id") and ml):
        return None
    if _fecha(ml["generado"]) < date.fromisoformat(p["publicado"]):
        return {"aviso": "ml_datos.json es anterior a la publicación; refresca ventas"}
    u = ventas_desde(ml, p["ml_id"], p["publicado"])
    s = max(1.0, semanas_publicado(p))
    ritmo = u / s
    base, n = bases.get(p["categoria"], (None, 0))
    r = {"unidades": u, "semanas": round(s, 1), "ritmo": round(ritmo, 2),
         "base": round(base, 2) if base else None, "n_base": n}
    if base:
        frac = ritmo / base
        r["fraccion"] = round(frac, 2)
        r["sugerido"] = ("escalar" if frac >= CONFIG["umbral_escalar"] else
                         "potenciar" if frac >= CONFIG["umbral_potenciar"] else
                         "iterar o retirar")
    if u < CONFIG["ventas_minimas_para_confiar"]:
        r["ruido"] = True
    return r


def cmd_ver(a):
    t = cargar()
    ml = ventas_ml()
    bases = lineas_base(ml) if ml else {}

    if ml:
        edad = (date.today() - _fecha(ml["generado"])).days
        aviso = "  ⚠️ viejos, refresca con colecta-full" if edad > CONFIG["dias_datos_viejos"] else ""
        print(f"Ventas ML: {_fecha(ml['generado'])} ({edad} días){aviso}")
        print("Línea base (mediana u/semana por publicación):")
        for c, (m, n) in sorted(bases.items(), key=lambda x: -x[1][0]):
            print(f"  {c:16s} {m:5.2f}  ({n} publicaciones)")
    else:
        print("Sin ~/.catalogo3d/ml_datos.json — corre colecta-full/scripts/traer_datos.py")
    print()

    prods = t["productos"]
    if a.slug:
        prods = {a.slug: producto(t, a.slug)}
    if not prods:
        print(f"Tablero vacío ({TABLERO}). Arranca con la fase 1: investigar mercado.")
        return

    for slug, p in prods.items():
        rev = revision_pendiente(p)
        marca = f"  ⏰ revisión semana {rev}" if rev else ""
        print(f"[{p['fase']:>10}] {slug} — {p['nombre']} ({p['categoria']}){marca}")
        if p.get("ml_id"):
            print(f"             {p['ml_id']} desde {p['publicado']}, ${p.get('precio', '?')}")
        ev = evaluar(p, ml, bases)
        if ev and "aviso" in ev:
            print(f"             {ev['aviso']}")
        elif ev:
            linea = f"             {ev['unidades']} u en {ev['semanas']} sem = {ev['ritmo']}/sem"
            if ev.get("base"):
                linea += (f" · {int(ev['fraccion'] * 100)} % de la mediana "
                          f"({ev['base']}/sem, n={ev['n_base']}) → {ev['sugerido']}")
            if ev.get("ruido"):
                linea += "  (pocas ventas: es ruido)"
            print(linea)
        if p.get("veredicto"):
            print(f"             veredicto: {p['veredicto']}")
        if a.slug:
            for h in p.get("historial", []):
                print(f"             {h['fecha']} {h['evento']}: {h.get('nota', '')}")


def cmd_nuevo(a):
    t = cargar()
    if a.slug in t["productos"]:
        sys.exit(f"«{a.slug}» ya existe")
    p = {"nombre": a.nombre, "categoria": a.categoria, "fase": "propuesto",
         "creado": hoy(), "origen": a.origen, "historial": []}
    p["historial"].append({"fecha": hoy(), "evento": "propuesto", "nota": a.origen or ""})
    t["productos"][a.slug] = p
    guardar(t)
    ruta = DATOS / f"{a.slug}.md"
    if not ruta.exists():
        ruta.write_text(
            f"# {a.nombre}\n\n"
            f"Categoría: {a.categoria} · Origen: {a.origen or '—'} · Creado: {hoy()}\n\n"
            "## Ficha elegida\n\n(pegar aquí la ficha de la propuesta)\n\n"
            "## Rondas de diseño\n\n## Prototipo\n\n## Publicación\n\n"
            "## Seguimiento\n\n## Qué aprendimos\n\n## Bitácora\n\n",
            encoding="utf-8")
    anotar(a.slug, f"registrado como propuesta ({a.categoria})")
    print(f"Registrado {a.slug} → {ruta}")


def cmd_fase(a):
    t = cargar()
    p = producto(t, a.slug)
    p["fase"] = a.fase
    ev = {"fecha": hoy(), "evento": a.fase, "nota": a.nota or ""}
    if a.gramos is not None:
        p["gramos"] = ev["gramos"] = a.gramos
        p["costo"] = round(a.gramos / 1000 * CONFIG["precio_kg"] + CONFIG["paqueteria"], 2)
    if a.horas is not None:
        p["horas"] = ev["horas"] = a.horas
    p["historial"].append(ev)
    guardar(t)
    extra = f" · {a.gramos} g (${p['costo']})" if a.gramos is not None else ""
    extra += f" · {a.horas} h" if a.horas is not None else ""
    anotar(a.slug, f"fase **{a.fase}**{extra}. {a.nota or ''}")
    print(f"{a.slug} → {a.fase}")


def cmd_publicar(a):
    t = cargar()
    p = producto(t, a.slug)
    p.update(fase="publicado", ml_id=a.ml_id, publicado=a.fecha or hoy(), revisiones=[])
    if a.precio:
        p["precio"] = a.precio
    p["historial"].append({"fecha": hoy(), "evento": "publicado", "nota": a.ml_id})
    guardar(t)
    anotar(a.slug, f"publicado {a.ml_id} a ${a.precio or '?'}; revisiones en semanas "
                   f"{CONFIG['revisiones_semanas']}")
    print(f"{a.slug} publicado como {a.ml_id}")


def cmd_veredicto(a):
    t = cargar()
    p = producto(t, a.slug)
    rev = revision_pendiente(p)
    if rev:
        # Una revisión cubre todas las vencidas: si se revisa tarde, en la
        # semana 5, no tiene sentido que luego pida la de la semana 2.
        p.setdefault("revisiones", []).extend(
            w for w in CONFIG["revisiones_semanas"]
            if w <= rev and w not in p["revisiones"])
    p["veredicto"] = a.veredicto
    if a.veredicto == "retirar" or a.cerrar:
        p["fase"] = "cerrado"
    ev = evaluar(p, ventas_ml(), lineas_base(ventas_ml()) if ventas_ml() else {})
    resumen = ""
    if ev and "ritmo" in ev:
        resumen = f" ({ev['unidades']} u, {ev['ritmo']}/sem)"
    p["historial"].append({"fecha": hoy(), "evento": f"veredicto {a.veredicto}",
                           "nota": (a.nota or "") + resumen})
    guardar(t)
    sem = f" semana {rev}" if rev else ""
    anotar(a.slug, f"veredicto{sem}: **{a.veredicto}**{resumen}. {a.nota or ''}")
    print(f"{a.slug}: {a.veredicto}{sem}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ver")
    s.add_argument("slug", nargs="?")
    s.set_defaults(fn=cmd_ver)

    s = sub.add_parser("nuevo")
    s.add_argument("slug")
    s.add_argument("--nombre", required=True)
    s.add_argument("--categoria", required=True)
    s.add_argument("--origen")
    s.set_defaults(fn=cmd_nuevo)

    s = sub.add_parser("fase")
    s.add_argument("slug")
    s.add_argument("fase", choices=FASES)
    s.add_argument("--nota")
    s.add_argument("--gramos", type=float)
    s.add_argument("--horas", type=float)
    s.set_defaults(fn=cmd_fase)

    s = sub.add_parser("publicar")
    s.add_argument("slug")
    s.add_argument("ml_id")
    s.add_argument("--precio", type=float)
    s.add_argument("--fecha", help="AAAA-MM-DD si se publicó antes de hoy")
    s.set_defaults(fn=cmd_publicar)

    s = sub.add_parser("veredicto")
    s.add_argument("slug")
    s.add_argument("veredicto", choices=VEREDICTOS)
    s.add_argument("--nota")
    s.add_argument("--cerrar", action="store_true", help="cierra el producto aunque no sea retirar")
    s.set_defaults(fn=cmd_veredicto)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
