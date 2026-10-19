#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  Catálogo 3D  -  Galería local de tus diseños .3mf
============================================================
Lee tus proyectos .3mf de Bambu Studio y muestra en el navegador:
  - Miniatura de cada diseño (la que ya trae el .3mf)
  - Peso en gramos (leído del laminado del propio archivo, o el que
    escribas tú por unidad en la propia tarjeta)
  - Costo estimado (peso x precio por kg, ajustable en vivo) más el costo
    de paquetería, y frente a eso el retorno de inversión (lo que te
    deposita MercadoLibre por una venta) y la ganancia que queda
  - Pestañas "Por cargar" y "Con información": los diseños a los que aún
    les falta un dato para cerrar la cuenta, y los que ya la tienen
  - Pestaña "Mi negocio": el cierre de cada mes (ventas y gastos como
    publicidad o el recibo de luz) con margen, utilidad, punto de
    equilibrio y qué diseño deja más
  - Y con eso, el análisis: si cada producto está caro o barato, cuánto
    puedes pagar de publicidad por una venta y qué ROAS necesitas
  - Paquetería: hasta tres paquetes con sus elementos (bolsa, etiquetas,
    maceta de regalo...). De cada uno se apunta lo que costó la última
    compra y cuántas unidades traía, y de ahí sale el costo por unidad
  - Renombrar el archivo REAL en disco desde la galería
  - Eliminar el archivo REAL en disco desde la galería
  - Muestra también los .3mf de todas las subcarpetas
  - Pestaña "Descargas": ve los .3mf que tienes en ~/Downloads y
    muévelos con un botón a tu carpeta de diseños

No requiere instalar nada: solo Python 3 (stdlib).

USO:
  1) Pon este archivo donde quieras.
  2) Ejecuta:   python3 catalogo3d.py
     (por defecto busca la carpeta ~/Desktop/own design 3d)
     Para otra carpeta:  python3 catalogo3d.py "/ruta/a/mi/carpeta"
  3) Se abre solo en el navegador. Para cerrar: Ctrl+C en la terminal.
============================================================
"""

import os
import re
import errno
import sys
import json
import base64
import shutil
import zipfile
import platform
import subprocess
import threading
import webbrowser
import xml.etree.ElementTree as ET
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

# ----------------------------------------------------------
#  CONFIGURACIÓN
# ----------------------------------------------------------
PUERTO            = 8770
PRECIO_KG_DEFECTO = 179      # MXN por kg si el .3mf no trae costo
MONEDA            = "MXN"

# Carpeta por defecto (se puede pasar otra como argumento)
CARPETA_DEFECTO   = Path.home() / "Desktop" / "own design 3d"
CARPETA_DESCARGAS = Path.home() / "Downloads"

# Archivo donde se guarda el link de MercadoLibre y el precio de venta de
# cada diseño (vive dentro de la carpeta de diseños, uno por catálogo).
NOMBRE_ARCHIVO_ML = ".catalogo3d_mercadolibre.json"

# Archivo con los ajustes de costos del catálogo completo: precio del
# filamento, comisión, retorno de inversión y los paquetes de paquetería con
# sus elementos. Vive junto a los diseños, igual que el de MercadoLibre.
NOMBRE_ARCHIVO_COSTOS = ".catalogo3d_costos.json"

# Archivo del cierre de cada mes: las ventas y los gastos que no van dentro
# de la pieza (publicidad, luz, renta...). Un mes por clave, "2026-09".
NOMBRE_ARCHIVO_NEGOCIO = ".catalogo3d_negocio.json"
RE_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

# Paquetería de arranque: los mismos renglones de la hoja de cálculo. De cada
# elemento se guarda lo que costó la última compra y cuántas unidades traía;
# el costo por unidad sale de dividir una cosa entre la otra, así que basta
# con actualizar la compra para que todos los precios se recalculen.
PAQUETES_DEFECTO = [
    {"nombre": "Envío completo", "elementos": [
        {"nombre": "Bolsa semillas",    "costo_compra": 0.30, "unidades": 1},
        {"nombre": "Bolsa envío",       "costo_compra": 12.00, "unidades": 1},
        {"nombre": "Etiquetas",         "costo_compra": 0.30, "unidades": 1},
        {"nombre": "Maceta regalo",     "costo_compra": 4.00, "unidades": 1},
        {"nombre": "Nuevo tarro tierra", "costo_compra": 1.50, "unidades": 1},
    ]},
    {"nombre": "Envío simple", "elementos": [
        {"nombre": "Bolsa envío", "costo_compra": 12.00, "unidades": 1},
        {"nombre": "Etiquetas",   "costo_compra": 0.30, "unidades": 1},
    ]},
    {"nombre": "Entrega en mano", "elementos": [
        {"nombre": "Bolsa semillas", "costo_compra": 0.30, "unidades": 1},
        {"nombre": "Etiquetas",      "costo_compra": 0.30, "unidades": 1},
    ]},
]


# Rutas donde puede estar instalado Bambu Studio (se usa la primera que exista).
# Si ninguna existe, se abre el .3mf con la app por defecto del sistema.
APPS_BAMBU = {
    "Darwin": [
        "/Applications/BambuStudio.app",
        "/Applications/Bambu Studio.app",
        str(Path.home() / "Applications" / "BambuStudio.app"),
    ],
    "Windows": [
        r"C:\Program Files\Bambu Studio\bambu-studio.exe",
        r"C:\Program Files (x86)\Bambu Studio\bambu-studio.exe",
    ],
    "Linux": [
        "/usr/bin/bambu-studio",
        "/usr/local/bin/bambu-studio",
        "/opt/bambu-studio/bambu-studio",
    ],
}

# Generadores paramétricos (carpeta generadores/). Si no están, el catálogo
# funciona igual: nada más no aparece la pestaña «Crear».
CARPETA_GENERADORES = Path(__file__).resolve().parent / "generadores"
try:
    sys.path.insert(0, str(CARPETA_GENERADORES))
    import disenos as gen_disenos
    import crear as gen_crear
    from nucleo import cuerpo as gen_cuerpo, render as gen_render
    HAY_GENERADORES = True
except Exception as _e:            # pragma: no cover - depende de la instalación
    HAY_GENERADORES = False
    ERROR_GENERADORES = str(_e)


# ----------------------------------------------------------
#  LECTURA DE .3mf
# ----------------------------------------------------------
def _leer_miniatura(z):
    """Devuelve (bytes_png, nombre) de la mejor miniatura del .3mf."""
    candidatos = [n for n in z.namelist()
                  if n.lower().endswith(".png") and "metadata/" in n.lower()]
    if not candidatos:
        candidatos = [n for n in z.namelist() if n.lower().endswith(".png")]
    if not candidatos:
        return None
    # Preferir la vista de plato grande y con luz sobre las miniaturas chicas
    def rank(n):
        low = n.lower()
        score = 0
        if "plate_1.png" in low: score += 100
        if "plate_no_light" in low: score -= 40
        if "small" in low: score -= 60
        if "top_" in low or "pick_" in low: score -= 80
        # a mayor tamaño de archivo, mejor calidad
        try: score += z.getinfo(n).file_size / 5000.0
        except Exception: pass
        return score
    mejor = max(candidatos, key=rank)
    try:
        return z.read(mejor)
    except Exception:
        return None


def _leer_peso_g(z):
    """Suma los gramos de filamento del slice_info.config (todos los platos)."""
    nombre = next((n for n in z.namelist()
                   if n.lower().endswith("slice_info.config")), None)
    if not nombre:
        return None
    try:
        root = ET.fromstring(z.read(nombre))
    except Exception:
        return None
    total = 0.0
    encontrado = False
    # Los gramos vienen como atributo used_g en cada <filament>
    for el in root.iter():
        val = el.attrib.get("used_g")
        if val:
            try:
                total += float(val)
                encontrado = True
            except ValueError:
                pass
    return round(total, 1) if encontrado else None


def _leer_material(z):
    """Devuelve (tipo, color_hex) del primer filamento, si existe."""
    nombre = next((n for n in z.namelist()
                   if n.lower().endswith("slice_info.config")), None)
    if not nombre:
        return (None, None)
    try:
        root = ET.fromstring(z.read(nombre))
    except Exception:
        return (None, None)
    for el in root.iter("filament"):
        return (el.attrib.get("type"), el.attrib.get("color"))
    # fallback: cualquier elemento con atributo type
    for el in root.iter():
        if "used_g" in el.attrib:
            return (el.attrib.get("type"), el.attrib.get("color"))
    return (None, None)


def _leer_precio_kg(z):
    """Intenta leer el costo por kg de project_settings.config (JSON)."""
    nombre = next((n for n in z.namelist()
                   if n.lower().endswith("project_settings.config")), None)
    if not nombre:
        return None
    try:
        data = json.loads(z.read(nombre))
    except Exception:
        return None
    costo = data.get("filament_cost")
    if isinstance(costo, list) and costo:
        try:
            return float(costo[0])
        except (ValueError, TypeError):
            return None
    if isinstance(costo, (str, int, float)):
        try:
            return float(costo)
        except (ValueError, TypeError):
            return None
    return None


def leer_diseno(ruta: Path, carpeta: Path):
    """Extrae todos los datos de un archivo .3mf.
    'archivo' es la ruta relativa a 'carpeta' (incluye subcarpetas si las hay),
    y se usa como identificador para renombrar/eliminar.
    """
    rel = ruta.relative_to(carpeta)
    subcarpeta = str(rel.parent).replace(os.sep, "/")
    if subcarpeta == ".":
        subcarpeta = ""
    info = {
        "archivo": str(rel).replace(os.sep, "/"),
        "nombre": ruta.stem,
        "subcarpeta": subcarpeta,
        "peso_g": None,
        "precio_kg": None,
        "material": None,
        "color": None,
        "miniatura": None,   # data URI base64
        "error": None,
    }
    try:
        with zipfile.ZipFile(ruta) as z:
            info["peso_g"] = _leer_peso_g(z)
            info["precio_kg"] = _leer_precio_kg(z)
            mat, col = _leer_material(z)
            info["material"] = mat
            info["color"] = col
            png = _leer_miniatura(z)
            if png:
                b64 = base64.b64encode(png).decode("ascii")
                info["miniatura"] = "data:image/png;base64," + b64
    except zipfile.BadZipFile:
        info["error"] = "No es un .3mf válido (zip dañado)"
    except Exception as e:
        info["error"] = str(e)
    return info


def escanear(carpeta: Path):
    """Busca .3mf en 'carpeta' y en todas sus subcarpetas.

    Las subcarpetas cuyo nombre empieza con guion bajo no se miran: son de
    trastienda, no de catálogo. Es donde `rescatar.py` deja el original antes
    de volver a generar una pieza, y sin esta regla cada respaldo salía en la
    galería como una tarjeta repetida de la pieza que acababa de mejorar.
    """
    archivos = sorted((a for a in carpeta.rglob("*.3mf")
                       if not any(parte.startswith("_")
                                  for parte in a.relative_to(carpeta).parts[:-1])),
                      key=lambda p: str(p.relative_to(carpeta)).lower())
    disenos = [leer_diseno(a, carpeta) for a in archivos]
    ml = cargar_ml(carpeta)
    for d in disenos:
        entrada = ml.get(d["archivo"]) or {}
        d["ml_link"] = entrada.get("link")
        d["ml_precio_venta"] = entrada.get("precio_venta")
        # peso y costo escritos a mano: mandan sobre lo que trae el .3mf
        d["peso_manual"] = entrada.get("peso_g")
        d["costo_pieza"] = entrada.get("costo_pieza")
        d["retorno"] = entrada.get("retorno")
        d["competencia"] = entrada.get("competencia")
        d["paquete"] = entrada.get("paquete")
    return disenos


# ----------------------------------------------------------
#  RUTAS SEGURAS (anti path-traversal)
# ----------------------------------------------------------
def _resolver_relativo(carpeta: Path, rel: str):
    """Valida que 'rel' sea una ruta relativa que quede dentro de 'carpeta'.
    Devuelve el Path resuelto, o None si es inválida / intenta salir de la carpeta."""
    if not rel:
        return None
    rel = rel.strip().lstrip("/\\")
    if not rel:
        return None
    carpeta_res = carpeta.resolve()
    destino = (carpeta_res / rel).resolve()
    if destino != carpeta_res and carpeta_res not in destino.parents:
        return None
    return destino


# ----------------------------------------------------------
#  RENOMBRADO SEGURO EN DISCO
# ----------------------------------------------------------
def renombrar(carpeta: Path, viejo: str, nuevo: str):
    """Renombra viejo -> nuevo, conservando la subcarpeta del original.
    'viejo' es la ruta relativa a 'carpeta' (puede incluir subcarpetas).
    Devuelve (ok, mensaje, ruta_relativa_final)."""
    nuevo = nuevo.strip()
    if not nuevo:
        return (False, "El nombre está vacío", None)
    # el nuevo nombre es solo el nombre de archivo, sin ruta
    nuevo = os.path.basename(nuevo)
    # caracteres problemáticos
    if re.search(r'[\\/:*?"<>|]', nuevo):
        return (False, "El nombre tiene caracteres no permitidos", None)
    # asegurar extensión .3mf
    if not nuevo.lower().endswith(".3mf"):
        nuevo += ".3mf"

    origen = _resolver_relativo(carpeta, viejo)
    if origen is None:
        return (False, "Origen fuera de la carpeta", None)
    if not origen.exists():
        return (False, "El archivo original ya no existe", None)

    destino = origen.parent / nuevo
    if destino.exists() and destino != origen:
        return (False, f"Ya existe un archivo llamado «{nuevo}»", None)

    try:
        origen.rename(destino)
        rel_final = str(destino.relative_to(carpeta.resolve())).replace(os.sep, "/")
        return (True, "Renombrado", rel_final)
    except Exception as e:
        return (False, str(e), None)


# ----------------------------------------------------------
#  ELIMINAR ARCHIVO
# ----------------------------------------------------------
def eliminar(carpeta: Path, archivo: str):
    """Elimina un .3mf dentro de 'carpeta' (o subcarpeta). Devuelve (ok, mensaje)."""
    ruta = _resolver_relativo(carpeta, archivo)
    if ruta is None:
        return (False, "Ruta fuera de la carpeta")
    if ruta.suffix.lower() != ".3mf":
        return (False, "Solo se pueden eliminar archivos .3mf")
    if not ruta.exists():
        return (False, "El archivo ya no existe")
    try:
        ruta.unlink()
        return (True, "Eliminado")
    except Exception as e:
        return (False, str(e))


# ----------------------------------------------------------
#  MOVER DESDE DESCARGAS
# ----------------------------------------------------------
def mover_desde_descargas(carpeta_descargas: Path, carpeta_destino: Path, archivo: str):
    """Mueve un .3mf de 'carpeta_descargas' a la raíz de 'carpeta_destino'.
    Si ya existe un archivo con ese nombre, agrega ' (2)', ' (3)'... para no pisarlo.
    Devuelve (ok, mensaje, nombre_final)."""
    origen = _resolver_relativo(carpeta_descargas, archivo)
    if origen is None:
        return (False, "Ruta de origen inválida", None)
    if origen.suffix.lower() != ".3mf":
        return (False, "Solo se pueden mover archivos .3mf", None)
    if not origen.exists():
        return (False, "El archivo ya no existe en Descargas", None)

    carpeta_destino_res = carpeta_destino.resolve()
    carpeta_destino_res.mkdir(parents=True, exist_ok=True)
    destino = carpeta_destino_res / origen.name
    if destino.exists():
        base, ext = origen.stem, origen.suffix
        n = 2
        while destino.exists():
            destino = carpeta_destino_res / f"{base} ({n}){ext}"
            n += 1

    try:
        shutil.move(str(origen), str(destino))
        return (True, "Movido", destino.name)
    except Exception as e:
        return (False, str(e), None)


# ----------------------------------------------------------
#  MOVER A PRUEBAS DE PRODUCTOS
# ----------------------------------------------------------
CARPETA_PRUEBAS = "Pruebas de productos"


def mover_a_pruebas(carpeta: Path, archivo: str):
    """Mueve un diseño a la subcarpeta de pruebas, con todo lo que comparte
    su nombre: la miniatura, el .stl y los respaldos (.bak, .vN.bak). Nunca
    pisa nada: si algo con ese nombre ya está en pruebas, no mueve ninguno.
    Devuelve (ok, mensaje, ruta_relativa_final)."""
    origen = _resolver_relativo(carpeta, archivo)
    if origen is None:
        return (False, "Ruta fuera de la carpeta", None)
    if origen.suffix.lower() != ".3mf":
        return (False, "Solo se pueden mover archivos .3mf", None)
    if not origen.exists():
        return (False, "El archivo ya no existe", None)
    destino_dir = carpeta.resolve() / CARPETA_PRUEBAS
    if origen.parent == destino_dir:
        return (False, "Ya está en %s" % CARPETA_PRUEBAS, None)

    base = origen.stem
    hermanos = [p for p in origen.parent.iterdir()
                if p.is_file() and (p.name == origen.name
                                    or p.name.startswith(base + "."))]
    choques = [p.name for p in hermanos if (destino_dir / p.name).exists()]
    if choques:
        return (False, "Ya existe «%s» en %s" % (choques[0], CARPETA_PRUEBAS), None)

    try:
        destino_dir.mkdir(exist_ok=True)
        for p in hermanos:
            shutil.move(str(p), str(destino_dir / p.name))
    except Exception as e:
        return (False, str(e), None)
    final = "%s/%s" % (CARPETA_PRUEBAS, origen.name)
    return (True, "Movido a %s" % CARPETA_PRUEBAS, final)


# ----------------------------------------------------------
#  COSTOS: FILAMENTO, PAQUETERÍA Y RETORNO DE INVERSIÓN
# ----------------------------------------------------------
def _num(valor, defecto=0.0, minimo=0.0):
    """Número usable o el de respaldo: lo que llega del navegador viene como
    texto y a veces vacío."""
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return defecto
    if n != n or n in (float("inf"), float("-inf")):
        return defecto
    return max(minimo, n)


def _num_opcional(valor, defecto):
    if valor is None or valor == "":
        return defecto
    return round(_num(valor, defecto), 2)


def costo_unitario(elemento):
    """Lo que cuesta UNA pieza del elemento: la última compra dividida entre
    las unidades que traía esa compra."""
    unidades = _num(elemento.get("unidades"), 1.0)
    if unidades <= 0:
        unidades = 1.0
    return _num(elemento.get("costo_compra")) / unidades


def total_paquete(paquete):
    """Costo de mandar un pedido con ese paquete: la suma de sus elementos."""
    return round(sum(costo_unitario(e) for e in (paquete.get("elementos") or [])), 2)


def _normalizar_elemento(e):
    if not isinstance(e, dict):
        return None
    nombre = str(e.get("nombre", "")).strip()[:60]
    if not nombre:
        return None
    unidades = _num(e.get("unidades"), 1.0)
    if unidades <= 0:
        unidades = 1.0
    return {"nombre": nombre,
            "costo_compra": round(_num(e.get("costo_compra")), 4),
            "unidades": round(unidades, 4)}


def _normalizar_paquete(p):
    if not isinstance(p, dict):
        return None
    elementos = [x for x in (_normalizar_elemento(e)
                             for e in (p.get("elementos") or [])) if x]
    limpio = {"nombre": str(p.get("nombre", "")).strip()[:60] or "Paquetería",
              "elementos": elementos}
    limpio["total"] = total_paquete(limpio)
    return limpio


def normalizar_config(data):
    """Deja la configuración con la forma que espera la galería, venga de
    donde venga: del archivo, del navegador o de ningún lado todavía."""
    data = data if isinstance(data, dict) else {}
    paquetes = [x for x in (_normalizar_paquete(p)
                            for p in (data.get("paquetes") or [])) if x]
    if not paquetes:
        paquetes = [_normalizar_paquete(p) for p in PAQUETES_DEFECTO]
    paquetes = paquetes[:6]

    try:
        activo = int(data.get("paquete_activo"))
    except (TypeError, ValueError):
        activo = 0
    if not -1 <= activo < len(paquetes):
        activo = 0

    precio_kg = _num_opcional(data.get("precio_kg"), None)
    if precio_kg is not None and precio_kg <= 0:
        precio_kg = None

    return {
        "precio_kg": precio_kg,
        "utilidad_objetivo": max(0.0, _num_opcional(data.get("utilidad_objetivo"), 0.0)),
        "paquete_activo": activo,
        "paquetes": paquetes,
    }


# Los archivos de ajustes se leen y se reescriben enteros. El servidor
# atiende varias peticiones a la vez, así que sin candado dos guardados
# simultáneos se pisan: el segundo escribe encima de lo que leyó antes.
_CANDADO = threading.Lock()


def cargar_config(carpeta: Path):
    ruta = carpeta / NOMBRE_ARCHIVO_COSTOS
    datos = {}
    if ruta.exists():
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            datos = {}
    return normalizar_config(datos)


def guardar_config(carpeta: Path, data):
    """Guarda los ajustes de costos ya normalizados. Devuelve (ok, config)."""
    cfg = normalizar_config(data)
    try:
        with _CANDADO:
            (carpeta / NOMBRE_ARCHIVO_COSTOS).write_text(
                json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, cfg
    except Exception:
        return False, cfg


# ----------------------------------------------------------
#  CIERRE DEL MES (ventas y gastos generales)
# ----------------------------------------------------------
def _normalizar_gasto(g):
    """Un renglón de gasto del mes: publicidad, luz, renta, un rollo de
    filamento... lo que no se reparte pieza por pieza."""
    if not isinstance(g, dict):
        return None
    concepto = str(g.get("concepto", "")).strip()[:60]
    monto = round(_num(g.get("monto")), 2)
    if not concepto:
        # un renglón a medio escribir no es un gasto, pero si ya trae dinero
        # no se tira: se guarda con un nombre provisional
        if monto <= 0:
            return None
        concepto = "Sin concepto"
    # la publicidad se separa del resto porque es el único gasto que se
    # decide venta a venta: de ahí sale el ROAS
    tipo = "publicidad" if g.get("tipo") == "publicidad" else "general"
    return {"concepto": concepto, "monto": monto, "tipo": tipo}


def _normalizar_venta(v):
    """Una venta del mes. El retorno y el costo se guardan tal como estaban
    el día de la venta: si mañana sube el filamento, el mes cerrado no se
    mueve."""
    if not isinstance(v, dict):
        return None
    unidades = _num(v.get("unidades"), 1.0)
    if unidades <= 0:
        unidades = 1.0
    archivo = str(v.get("archivo", "")).strip()[:300]
    return {"archivo": archivo,
            "nombre": str(v.get("nombre", "")).strip()[:120] or "Sin diseño",
            "unidades": round(unidades, 2),
            "retorno": round(_num(v.get("retorno")), 2),
            "costo": round(_num(v.get("costo")), 2),
            # lo que pagó el comprador: es la base con la que las
            # plataformas reportan el ROAS de sus anuncios
            "publicado": round(_num(v.get("publicado")), 2)}


def normalizar_mes(datos):
    datos = datos if isinstance(datos, dict) else {}
    gastos = [x for x in (_normalizar_gasto(g)
                          for g in (datos.get("gastos") or [])) if x]
    ventas = [x for x in (_normalizar_venta(v)
                          for v in (datos.get("ventas") or [])) if x]
    return {"gastos": gastos[:200], "ventas": ventas[:1000]}


def cargar_negocio(carpeta: Path):
    ruta = carpeta / NOMBRE_ARCHIVO_NEGOCIO
    if not ruta.exists():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(datos, dict):
        return {}
    return {mes: normalizar_mes(d) for mes, d in datos.items()
            if RE_MES.match(str(mes))}


def guardar_mes(carpeta: Path, mes: str, datos):
    """Reescribe un solo mes y deja los demás como estaban. Devuelve
    (ok, mes_guardado)."""
    if not RE_MES.match(str(mes or "")):
        return False, None
    limpio = normalizar_mes(datos)
    try:
        with _CANDADO:
            todo = cargar_negocio(carpeta)
            if limpio["gastos"] or limpio["ventas"]:
                todo[mes] = limpio
            else:
                todo.pop(mes, None)       # mes vacío: no ensucia el archivo
            (carpeta / NOMBRE_ARCHIVO_NEGOCIO).write_text(
                json.dumps(todo, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, limpio
    except Exception:
        return False, limpio


# ----------------------------------------------------------
#  DATOS DE CADA DISEÑO (MercadoLibre, peso y costos a mano)
# ----------------------------------------------------------
def cargar_ml(carpeta: Path):
    """Lee el archivo con los links y precios de venta de MercadoLibre.
    Vive junto a los diseños, uno por carpeta; si no existe, no hay nada
    que vincular todavía."""
    ruta = carpeta / NOMBRE_ARCHIVO_ML
    if not ruta.exists():
        return {}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return {}


def guardar_ml(carpeta: Path, datos):
    try:
        ruta = carpeta / NOMBRE_ARCHIVO_ML
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


# Campos que un diseño puede guardar a mano. 'peso_g' y 'costo_pieza' pisan
# lo que trae el .3mf; 'retorno' es lo que te deposita MercadoLibre por una
# venta (si no se escribe, sale del precio de venta menos la comisión) y
# 'paquete' pisa la paquetería que trae el catálogo.
CAMPOS_NUMERICOS = ("precio_venta", "peso_g", "costo_pieza", "retorno",
                    "competencia")


def set_datos(carpeta: Path, archivo: str, campos):
    """Mezcla los campos que manda la galería con lo que ya estaba guardado
    de ese diseño. Un campo vacío borra lo que hubiera, para volver a lo
    automático. Devuelve (ok, entrada_guardada)."""
    with _CANDADO:
        return _set_datos(carpeta, archivo, campos)


def _set_datos(carpeta: Path, archivo: str, campos):
    datos = cargar_ml(carpeta)
    entrada = dict(datos.get(archivo) or {})

    for clave, valor in (campos or {}).items():
        if clave == "link":
            entrada["link"] = (str(valor).strip() or None) if valor else None
        elif clave == "paquete":
            # None = el paquete activo del catálogo, -1 = sin paquetería,
            # 0..n = ese paquete en concreto.
            try:
                indice = int(valor)
            except (TypeError, ValueError):
                indice = None
            entrada["paquete"] = indice if indice is not None and indice >= -1 else None
        elif clave in CAMPOS_NUMERICOS:
            if valor is None or valor == "":
                entrada[clave] = None
                continue
            try:
                n = round(float(valor), 4)
            except (TypeError, ValueError):
                continue
            # un peso, un precio o un retorno en 0 es un campo vacío
            # disfrazado: vuelve a lo automático
            entrada[clave] = n if n > 0 else None

    entrada = {k: v for k, v in entrada.items() if v is not None}
    if entrada:
        datos[archivo] = entrada
    else:
        datos.pop(archivo, None)
    return guardar_ml(carpeta, datos), entrada


def migrar_ml(carpeta: Path, viejo: str, nuevo: str):
    """Cuando un diseño se renombra o se mueve, su link/precio de venta lo
    sigue en vez de perderse."""
    if not viejo or viejo == nuevo:
        return
    datos = cargar_ml(carpeta)
    if viejo in datos:
        if nuevo:
            datos[nuevo] = datos.pop(viejo)
        else:
            datos.pop(viejo)
        guardar_ml(carpeta, datos)


# ----------------------------------------------------------
#  ACCIONES EN LOTE
# ----------------------------------------------------------
def _lista_archivos(data):
    """Saca una lista limpia de rutas relativas del cuerpo de la petición."""
    archivos = data.get("archivos")
    if not isinstance(archivos, list):
        return []
    return [a for a in archivos if isinstance(a, str) and a.strip()]


def eliminar_varios(carpeta: Path, archivos):
    """Elimina varios .3mf. Devuelve una lista con el resultado de cada uno,
    para que la galería sepa cuáles quitar y cuáles fallaron."""
    return [dict(zip(("archivo", "ok", "mensaje"), (a,) + eliminar(carpeta, a)))
            for a in archivos]


def mover_varios(carpeta_descargas: Path, carpeta_destino: Path, archivos):
    """Mueve varios .3mf de Descargas a la carpeta de diseños."""
    resultados = []
    for a in archivos:
        ok, msg, final = mover_desde_descargas(carpeta_descargas, carpeta_destino, a)
        resultados.append({"archivo": a, "ok": ok,
                           "mensaje": msg, "nombre_final": final})
    return resultados


# ----------------------------------------------------------
#  ABRIR EN BAMBU STUDIO
# ----------------------------------------------------------
def _ruta_bambu():
    """Devuelve la ruta de Bambu Studio instalada, o None si no se encuentra."""
    for candidata in APPS_BAMBU.get(platform.system(), []):
        if Path(candidata).exists():
            return candidata
    return None


def abrir_en_bambu(carpeta: Path, archivo: str):
    """Abre un .3mf de 'carpeta' en Bambu Studio (o en la app por defecto
    del sistema si no se encuentra instalado). Devuelve (ok, mensaje)."""
    ruta = _resolver_relativo(carpeta, archivo)
    if ruta is None:
        return (False, "Ruta fuera de la carpeta")
    if ruta.suffix.lower() != ".3mf":
        return (False, "Solo se pueden abrir archivos .3mf")
    if not ruta.exists():
        return (False, "El archivo ya no existe")

    app = _ruta_bambu()
    sistema = platform.system()
    try:
        if sistema == "Darwin":
            cmd = ["open", "-a", app, str(ruta)] if app else ["open", str(ruta)]
            subprocess.run(cmd, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        elif sistema == "Windows":
            if app:
                subprocess.Popen([app, str(ruta)])
            else:
                os.startfile(str(ruta))  # noqa: F821  (solo existe en Windows)
        else:  # Linux
            cmd = [app, str(ruta)] if app else ["xdg-open", str(ruta)]
            subprocess.Popen(cmd,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        detalle = (e.stderr or b"").decode("utf-8", "replace").strip()
        return (False, detalle or "No se pudo abrir el archivo")
    except FileNotFoundError:
        return (False, "No se encontró Bambu Studio ni una app por defecto")
    except Exception as e:
        return (False, str(e))

    return (True, "Abriendo en Bambu Studio" if app else "Abriendo con la app por defecto")


def nombre_app():
    """Etiqueta para los botones de la galería."""
    return "Bambu Studio" if _ruta_bambu() else "el visor del sistema"


# ----------------------------------------------------------
#  GENERADORES PARAMÉTRICOS
# ----------------------------------------------------------
def catalogo_generadores():
    """Lo que la pestaña «Crear» necesita para dibujarse sola: la lista de
    parámetros declarados y los valores de arranque de cada receta."""
    if not HAY_GENERADORES:
        return {"disponible": False, "error": ERROR_GENERADORES,
                "parametros": [], "disenos": []}
    return {
        "disponible": True,
        "parametros": gen_disenos.PARAMETROS,
        "disenos": [{"clave": d["clave"], "nombre": d["nombre"],
                     "descripcion": d["descripcion"], "carpeta": d["carpeta"],
                     "valores": gen_disenos.parametros_de(d["clave"])}
                    for d in gen_disenos.DISENOS],
    }


def _vista_pedida(data, p):
    """(giro, elevación) del render: la que mandó el navegador, o la que le
    toca al diseño si el usuario todavía no movió la vista."""
    v = data.get("vista")
    if isinstance(v, dict):
        try:
            return (float(v.get("giro", 0)) % 360.0,
                    max(2.0, min(88.0, float(v.get("elevacion", 30)))))
        except (TypeError, ValueError):
            pass
    return gen_render.camara(p)


def vista_previa(data):
    """Construye la malla y devuelve un render en borrador, sin tocar disco.

    La malla también va en borrador: el acabado se muestrea con grano grueso
    para que el deslizador siga siendo un deslizador. Lo que el borrador
    conserva —y es lo que hay que juzgar aquí— es que todas las estrías caigan
    iguales; el archivo que se guarda se construye en calidad final.
    """
    p = gen_disenos.normalizar(data.get("valores") or {})
    malla, info = gen_cuerpo.construir(p, calidad="borrador")
    vista = _vista_pedida(data, p)
    png = gen_render.render(malla.v, malla.t, tam=360, suavizado=1,
                            direccion=gen_render.vector_vista(*vista))
    # «piezas» trae las mallas en crudo: no viaja al navegador.
    datos = {k: v for k, v in info.items() if k != "piezas"}
    datos["n_piezas"] = len(info["piezas"])
    return {"ok": True, "datos": datos,
            "vista": {"giro": round(vista[0]), "elevacion": round(vista[1])},
            "png": "data:image/png;base64," + base64.b64encode(png).decode("ascii")}


# El muestrario: la misma pieza repetida en todas las plantas, para elegir
# viéndolas y no leyendo una lista. Las miniaturas se calculan con grano
# grueso porque lo que se juzga ahí es la silueta y no el acabado —de cerca
# ya está la vista previa grande—, y eso baja cada una de tres cuartos de
# segundo a un cuarto. El peso sale del mismo cálculo grueso: se midió contra
# la malla final en las catorce plantas de las dos recetas y no se separa más
# de un gramo, así que se enseña con «≈» y no como número firme.
MUESTRA = {"grano": 1.4, "segmentos": 200, "capas": 16}
MUESTRA_TAM = 200
# Picada: lo que se está eligiendo es la planta, y la planta se lee desde
# arriba. Bastante inclinada, eso sí, para que la pared siga contando.
MUESTRA_VISTA = (26, 46)


def muestra_planta(data):
    """Una casilla del muestrario: la pieza de hoy con otra planta puesta."""
    clave = data.get("contorno")
    if clave not in gen_disenos.CONTORNOS:
        return {"ok": False, "mensaje": "No conozco esa planta."}
    valores = dict(data.get("valores") or {})
    valores["contorno"] = clave
    valores.update(MUESTRA)
    p = gen_disenos.normalizar(valores)
    malla, info = gen_cuerpo.construir(p, calidad="borrador")
    png = gen_render.render(malla.v, malla.t, tam=MUESTRA_TAM, suavizado=1,
                            direccion=gen_render.vector_vista(*MUESTRA_VISTA))
    return {"ok": True, "contorno": clave, "gramos": info["gramos"],
            "ancho": info["ancho"], "fondo": info["fondo"], "alto": info["alto"],
            "ranuras": info["ranuras"], "cerrada": info["cerrada"],
            "avisos": info["avisos"],
            "png": "data:image/png;base64," + base64.b64encode(png).decode("ascii")}


def _nombre_libre(carpeta: Path, nombre: str):
    """Evita pisar un archivo que ya exista, igual que al mover desde Descargas."""
    if not (carpeta / (nombre + ".3mf")).exists():
        return nombre
    for i in range(2, 100):
        if not (carpeta / ("%s_%d.3mf" % (nombre, i))).exists():
            return "%s_%d" % (nombre, i)
    return "%s_%d" % (nombre, os.getpid())


def generar_diseno(carpeta_base: Path, data):
    clave = data.get("clave")
    if clave not in gen_disenos.POR_CLAVE:
        return False, "No conozco ese diseño.", None

    p = gen_disenos.normalizar(data.get("valores") or {})
    pedido = re.sub(r'[/\\:*?"<>|]', "", (data.get("nombre") or "").strip())
    nombre = pedido or gen_disenos.nombre_sugerido(clave, p)

    destino = carpeta_base / gen_disenos.POR_CLAVE[clave]["carpeta"]
    destino.mkdir(parents=True, exist_ok=True)
    final = _nombre_libre(destino, nombre)

    try:
        info, rutas = gen_crear.generar(clave, p, destino, final,
                                        vista=_vista_pedida(data, p))
    except Exception as e:
        return False, "No se pudo generar: %s" % e, None
    if not info["cerrada"]:
        return False, "La malla salió abierta; no se guardó nada útil.", None

    aviso = (" ⚠ " + info["avisos"][0]) if info["avisos"] else ""
    renombrado = "" if final == nombre else " (ya existía, se guardó como «%s»)" % final
    return True, "Guardado en %s · %s g%s%s" % (
        gen_disenos.POR_CLAVE[clave]["carpeta"], info["gramos"], renombrado, aviso), final


# ----------------------------------------------------------
#  PÁGINA HTML (galería)
# ----------------------------------------------------------
def pagina_html(carpeta: Path):
    return """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Catálogo 3D</title>
<style>
  :root{
    --bg:#f4f2ee; --card:#fffdfa; --ink:#2b2a27; --muted:#8a857c;
    --line:#e6e2da; --accent:#c56b47; --ok:#3f7d5a;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
  header{position:sticky;top:0;z-index:5;background:rgba(244,242,238,.92);
         backdrop-filter:blur(8px);border-bottom:1px solid var(--line);
         padding:16px 24px;display:flex;gap:20px;align-items:center;flex-wrap:wrap}
  h1{font-size:18px;margin:0;font-weight:600;letter-spacing:.2px}
  .sub{color:var(--muted);font-size:13px}
  .tabs{display:flex;gap:6px}
  .tab{border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 14px;
       font-size:13px;cursor:pointer;color:var(--muted)}
  .tab.activo{background:var(--ink);color:#fff;border-color:var(--ink)}
  .controls{margin-left:auto;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
  .field{display:flex;flex-direction:column;gap:2px}
  .field label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}
  .field input{border:1px solid var(--line);border-radius:8px;padding:6px 10px;
               font-size:14px;background:var(--card);width:110px}
  .stat{font-size:13px;color:var(--muted)}
  .stat b{color:var(--ink);font-weight:600}
  main{padding:24px;max-width:1400px;margin:0 auto}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:20px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;
        overflow:hidden;display:flex;flex-direction:column;
        transition:transform .12s ease,box-shadow .12s ease}
  .card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.06)}
  .thumb{aspect-ratio:1/1;background:#efeae2 center/cover no-repeat;
         display:flex;align-items:center;justify-content:center;
         position:relative;cursor:pointer}
  .thumb img{width:100%;height:100%;object-fit:cover;display:block}
  .thumb .noimg{color:var(--muted);font-size:13px}
  .thumb .abrir{position:absolute;inset:0;display:flex;align-items:center;
                justify-content:center;background:rgba(43,42,39,.55);color:#fff;
                font-size:13px;font-weight:600;letter-spacing:.2px;
                opacity:0;transition:opacity .15s}
  .thumb:hover .abrir{opacity:1}
  .body{padding:14px;display:flex;flex-direction:column;gap:10px}
  .nombre{display:flex;gap:6px}
  .nombre input{flex:1;min-width:0;border:1px solid transparent;border-radius:8px;padding:6px 8px;
                font-size:15px;font-weight:600;background:transparent;color:var(--ink)}
  .nombre input:hover{border-color:var(--line)}
  .nombre input:focus{border-color:var(--accent);background:#fff;outline:none}
  .btn{border:1px solid var(--line);background:#fff;border-radius:8px;padding:6px 10px;
       font-size:13px;cursor:pointer;color:var(--ink);white-space:nowrap;flex-shrink:0}
  .btn:hover{border-color:var(--accent);color:var(--accent)}
  .btn.save{border-color:var(--ok);color:var(--ok);padding:6px 9px;opacity:0;pointer-events:none;transition:opacity .15s}
  .btn.save.show{opacity:1;pointer-events:auto}
  .btn.del{border-color:var(--line);color:#a53b3b;padding:6px 9px}
  .btn.del:hover{border-color:#a53b3b;background:#fbeaea}
  .btn.mover{border-color:var(--accent);color:var(--accent);width:100%;text-align:center;font-weight:600}
  .btn.mover:hover{background:var(--accent);color:#fff}
  .btn.apruebas{flex-shrink:0}
  .btn.abrir{width:100%;text-align:center;font-weight:600}
  .btn.abrir:hover{background:var(--ink);color:#fff;border-color:var(--ink)}
  .nombre.solo span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                     padding:6px 8px;font-size:15px;font-weight:600}
  .meta{display:flex;gap:8px;flex-wrap:wrap}
  .chip{font-size:12px;background:#efeae2;color:#5b564d;padding:3px 9px;border-radius:999px}
  .chip.peso{background:#e7efe9;color:#356b4c}
  .chip.costo{background:#f5e7df;color:#a85a38;font-weight:600}
  .chip.mat{background:#eae6f0;color:#5b4c78}
  .chip.warn{background:#fbeaea;color:#a53b3b}
  .chip.folder{background:#eef1f5;color:#4a5b73}
  .chip.ganancia{background:#e7efe9;color:#2f6b45;font-weight:600}
  .chip.perdida{background:#fbeaea;color:#a53b3b;font-weight:600}
  .ml{display:flex;gap:8px}
  .btn.ml-ver{background:#fff3ea;border-color:var(--accent);color:var(--accent);
              text-decoration:none;display:flex;align-items:center;justify-content:center;
              flex-shrink:0;font-weight:600}
  .btn.ml-ver:hover{background:var(--accent);color:#fff}
  .btn.ml-editar{flex-shrink:0}
  .card.sel{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent) inset}
  .selbox{position:absolute;top:10px;left:10px;z-index:2;background:rgba(255,253,250,.9);
          border-radius:8px;padding:4px;line-height:0;box-shadow:0 1px 4px rgba(0,0,0,.12)}
  .selbox input{width:20px;height:20px;margin:0;cursor:pointer;accent-color:var(--accent)}
  .thumb .del{position:absolute;top:10px;right:10px;z-index:2;background:rgba(255,253,250,.9);
              box-shadow:0 1px 4px rgba(0,0,0,.12)}
  .etiqueta{position:absolute;left:10px;bottom:10px;right:10px;z-index:2;
            display:flex;gap:6px;align-items:center;pointer-events:none}
  .etiqueta>*{pointer-events:auto}
  .etiqueta input,.etiqueta span{max-width:100%;min-width:0;field-sizing:content;
            border:1px solid transparent;border-radius:999px;padding:5px 11px;
            font-size:13.5px;font-weight:600;color:var(--ink);background:rgba(255,253,250,.92);
            box-shadow:0 1px 4px rgba(0,0,0,.12);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .etiqueta input:hover{border-color:var(--line)}
  .etiqueta input:focus{border-color:var(--accent);background:#fff;outline:none}
  .etiqueta .btn.save{border-radius:999px;background:#fff}
  .barra{position:fixed;bottom:20px;left:50%;transform:translateX(-50%) translateY(80px);
         background:var(--ink);color:#fff;border-radius:14px;padding:10px 14px;
         display:flex;gap:10px;align-items:center;font-size:14px;z-index:20;
         box-shadow:0 10px 30px rgba(0,0,0,.22);opacity:0;pointer-events:none;
         transition:opacity .18s,transform .18s;flex-wrap:wrap;max-width:92vw}
  .barra.show{opacity:1;transform:translateX(-50%) translateY(0);pointer-events:auto}
  .barra b{font-weight:600}
  .barra .btn{background:transparent;color:#fff;border-color:rgba(255,255,255,.35)}
  .barra .btn:hover{background:rgba(255,255,255,.14);color:#fff;border-color:#fff}
  .barra .btn.peligro{border-color:rgba(255,150,150,.5);color:#ffb4b4}
  .barra .btn.peligro:hover{background:#a53b3b;color:#fff;border-color:#a53b3b}
  .barra .btn.mover{width:auto;border-color:rgba(255,255,255,.35);color:#fff}
  .barra .btn.mover:hover{background:var(--accent);border-color:var(--accent);color:#fff}
  .toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(40px);
         background:var(--ink);color:#fff;padding:10px 18px;border-radius:10px;font-size:14px;
         opacity:0;transition:.25s;pointer-events:none}
  .toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
  body.conbarra .toast{bottom:96px}
  .empty{text-align:center;color:var(--muted);padding:80px 20px}

  /* ---- Costos de cada tarjeta ---- */
  .paqsel{display:flex;gap:6px;align-items:center}
  .paqsel select{border:1px solid var(--line);border-radius:8px;padding:6px 8px;
                 font-size:14px;background:var(--card);color:var(--ink);max-width:210px}
  .paqsel .btn{padding:6px 9px}
  .chip.precio{background:#e9eef6;color:#3c5680;font-weight:600}
  .chip.manual{background:#f3ecdd;color:#7a6320}
  details.costos{border-top:1px solid var(--line);padding-top:10px}
  details.costos summary{cursor:pointer;font-size:12.5px;color:var(--muted);
                         list-style:none;user-select:none}
  details.costos summary::-webkit-details-marker{display:none}
  details.costos summary:hover{color:var(--accent)}
  details.costos[open] summary{color:var(--ink);font-weight:600}
  .cgrid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}
  .cgrid label{display:flex;flex-direction:column;gap:3px;font-size:10.5px;
               color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
  .cgrid input,.cgrid select{border:1px solid var(--line);border-radius:8px;
               padding:5px 7px;font-size:13.5px;background:#fff;color:var(--ink);
               width:100%;text-transform:none;letter-spacing:0}
  .cgrid input:focus,.cgrid select:focus{border-color:var(--accent);outline:none}
  .cgrid .ancho{grid-column:1 / -1}
  .resumen{margin-top:10px;display:flex;flex-direction:column;gap:3px;font-size:13px}
  .resumen .linea{display:flex;justify-content:space-between;gap:10px;
                  color:var(--muted);font-variant-numeric:tabular-nums}
  .resumen .linea b{color:var(--ink);font-weight:600}
  .resumen .linea.fuerte{color:var(--ink);border-top:1px dashed var(--line);
                         padding-top:4px;margin-top:2px}
  .resumen .linea.gana b{color:var(--ok);font-size:15px}
  .resumen .linea.pierde b{color:#a53b3b;font-size:15px}
  .chip.pendiente{background:#fbf3e6;color:#8a6420;font-weight:600}

  /* ---- Editor de paquetería ---- */
  .modal{position:fixed;inset:0;background:rgba(43,42,39,.45);z-index:30;
         display:none;align-items:flex-start;justify-content:center;padding:40px 16px;
         overflow:auto}
  .modal.show{display:flex}
  .modal .caja{background:var(--card);border-radius:18px;padding:22px;width:100%;
               max-width:720px;box-shadow:0 20px 50px rgba(0,0,0,.22)}
  .modal h2{margin:0 0 4px;font-size:17px}
  .modal .hint{margin:0 0 16px;font-size:13px;color:var(--muted)}
  .modal .tabs{margin-bottom:14px;flex-wrap:wrap}
  .modal .nombrepaq{width:100%;border:1px solid var(--line);border-radius:8px;
                    padding:7px 10px;font-size:14px;font-weight:600;background:#fff;
                    color:var(--ink);margin-bottom:12px}
  table.paq{width:100%;border-collapse:collapse;font-size:13px}
  table.paq th{text-align:left;font-size:10.5px;text-transform:uppercase;
               letter-spacing:.4px;color:var(--muted);font-weight:600;
               padding:0 6px 6px 0}
  table.paq td{padding:3px 6px 3px 0;vertical-align:middle}
  table.paq input{width:100%;border:1px solid var(--line);border-radius:8px;
                  padding:5px 7px;font-size:13.5px;background:#fff;color:var(--ink)}
  table.paq input:focus{border-color:var(--accent);outline:none}
  table.paq td.unit{font-variant-numeric:tabular-nums;font-weight:600;
                    white-space:nowrap;color:var(--ok)}
  table.paq td.quita{width:34px}
  .paqpie{display:flex;justify-content:space-between;align-items:center;
          gap:10px;margin-top:14px;flex-wrap:wrap}
  .paqtotal{font-size:15px;font-weight:600}
  .paqtotal span{color:var(--muted);font-weight:400;font-size:13px}
  .modal .acciones{display:flex;gap:8px;justify-content:flex-end;margin-top:16px}
  .btn.principal{background:var(--ink);color:#fff;border-color:var(--ink);font-weight:600}
  .btn.principal:hover{background:var(--accent);border-color:var(--accent);color:#fff}
  @media(max-width:620px){ .cgrid{grid-template-columns:1fr} }

  /* ---- Pestaña Mi negocio ---- */
  .mescab{display:flex;gap:10px;align-items:center;margin-bottom:18px;flex-wrap:wrap}
  .mescab input[type=month]{border:1px solid var(--line);border-radius:10px;padding:7px 10px;
        font-size:15px;font-weight:600;background:var(--card);color:var(--ink)}
  .mescab .btn{padding:7px 12px;font-size:15px;line-height:1}
  .negcols{display:grid;grid-template-columns:1.45fr 1fr;gap:20px;align-items:start}
  .tablacaja{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px}
  .tablacaja h3{margin:0 0 4px;font-size:14px}
  .tablacaja .pista{margin:0 0 12px;font-size:12.5px;color:var(--muted)}
  .tablacaja table{width:100%;border-collapse:collapse;font-size:13px}
  .tablacaja th{text-align:left;font-size:10.5px;text-transform:uppercase;letter-spacing:.4px;
                color:var(--muted);font-weight:600;padding:0 6px 6px 0}
  .tablacaja td{padding:3px 6px 3px 0;vertical-align:middle}
  .tablacaja input,.tablacaja select{width:100%;border:1px solid var(--line);border-radius:8px;
                padding:5px 7px;font-size:13.5px;background:#fff;color:var(--ink)}
  .tablacaja input:focus,.tablacaja select:focus{border-color:var(--accent);outline:none}
  .tablacaja td.nums{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap;
                     text-align:right}
  .tablacaja td.quita{width:34px}
  .tablacaja .vacio{color:var(--muted);padding:10px 0;font-size:13px}
  .tablacaja .masbtn{margin-top:12px}
  .kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;
        margin-top:22px}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:13px 15px}
  .kpi .et{font-size:10.5px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
  .kpi .n{font-size:21px;font-weight:600;margin-top:5px;font-variant-numeric:tabular-nums}
  .kpi .pie{font-size:12px;color:var(--muted);margin-top:3px}
  .kpi.fuerte{border-color:var(--ink)}
  .kpi.bien .n{color:var(--ok)}
  .kpi.mal .n{color:#a53b3b}
  .ranking{background:var(--card);border:1px solid var(--line);border-radius:16px;
           padding:16px;margin-top:20px}
  .ranking h3{margin:0 0 12px;font-size:14px}
  .rfila{display:grid;grid-template-columns:minmax(90px,1.1fr) 2fr auto;gap:12px;
         align-items:center;font-size:13px;margin-bottom:8px}
  .rfila .nom{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .rfila .val{font-variant-numeric:tabular-nums;font-weight:600;white-space:nowrap}
  .barrita{height:10px;background:#efeae2;border-radius:6px;overflow:hidden}
  .barrita i{display:block;height:100%;background:var(--ok);border-radius:6px}
  .barrita i.mal{background:#c9736f}
  .analisis{background:var(--card);border:1px solid var(--line);border-radius:16px;
            padding:16px;margin-top:20px}
  .preciocab{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
  .preciocab h3{margin:0;font-size:14px}
  .preciocab label{font-size:11px;color:var(--muted);text-transform:uppercase;
                   letter-spacing:.5px;display:flex;align-items:center;gap:8px;
                   margin-left:auto}
  .preciocab input{width:110px;border:1px solid var(--line);border-radius:8px;
                   padding:5px 8px;font-size:13.5px;background:#fff;color:var(--ink);
                   text-transform:none;letter-spacing:0}
  .analisis .pista{margin:0 0 12px;font-size:12.5px;color:var(--muted)}
  table.precios{width:100%;border-collapse:collapse;font-size:13px}
  table.precios th{text-align:right;font-size:10.5px;text-transform:uppercase;
                   letter-spacing:.4px;color:var(--muted);font-weight:600;
                   padding:0 0 7px 10px;white-space:nowrap}
  table.precios th:first-child,table.precios td:first-child{text-align:left;padding-left:0}
  table.precios td{text-align:right;padding:6px 0 6px 10px;
                   font-variant-numeric:tabular-nums;white-space:nowrap;
                   border-top:1px solid var(--line)}
  table.precios td.nom{max-width:190px;overflow:hidden;text-overflow:ellipsis;
                       white-space:nowrap;font-weight:600}
  table.precios td.dic{text-align:left;white-space:normal;color:var(--muted);
                       font-size:12.5px;min-width:150px}
  table.precios td.dic b{font-weight:600}
  table.precios .ojo b{color:#8a6420}
  table.precios .mal b{color:#a53b3b}
  table.precios .bien b{color:var(--ok)}
  table.precios tr.flojo td{opacity:.55}
  .roas{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
        gap:12px;margin:2px 0 18px}
  @media(max-width:900px){ .negcols{grid-template-columns:1fr} }

  /* ---- Pestaña Crear ---- */
  .crear{display:grid;grid-template-columns:330px 1fr;gap:24px;align-items:start}
  .panelp{background:var(--card);border:1px solid var(--line);border-radius:16px;
          padding:16px;display:flex;flex-direction:column;gap:16px;
          position:sticky;top:96px;max-height:calc(100vh - 132px);overflow:auto}
  .grupo{display:flex;flex-direction:column;gap:11px}
  .grupo h3{margin:0;font-size:11px;text-transform:uppercase;letter-spacing:.6px;
            color:var(--muted);border-top:1px solid var(--line);padding-top:13px}
  .par{display:flex;flex-direction:column;gap:4px}
  .par .fila{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
  .par label{font-size:13px}
  .par .val{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}
  .par input[type=range]{width:100%;accent-color:var(--accent);margin:0}
  .par select{border:1px solid var(--line);border-radius:8px;padding:6px 8px;
              font-size:14px;background:#fff;color:var(--ink);width:100%}
  .vistaprev{background:var(--card);border:1px solid var(--line);border-radius:16px;
             padding:18px;display:flex;flex-direction:column;gap:14px}
  .lienzo{position:relative;background:#efeae2;border-radius:12px;overflow:hidden;
          aspect-ratio:1/1;width:100%;max-width:460px;margin:0 auto}
  .lienzo img{width:100%;height:100%;object-fit:contain;display:block}
  .lienzo .cargando{position:absolute;inset:0;display:flex;align-items:center;
                    justify-content:center;background:rgba(239,234,226,.72);
                    font-size:13px;color:var(--muted);opacity:0;transition:opacity .15s}
  .lienzo.trabajando .cargando{opacity:1}
  .vistactrl{display:flex;align-items:center;gap:10px;max-width:460px;
             margin:0 auto;width:100%}
  .vistactrl label{font-size:11px;color:var(--muted);text-transform:uppercase;
                   letter-spacing:.5px;white-space:nowrap}
  .vistactrl input[type=range]{flex:1;min-width:0;accent-color:var(--accent);margin:0}
  .vistactrl .btn{padding:4px 9px;line-height:1.2}
  .guardar{display:flex;gap:8px}
  .guardar input{flex:1;min-width:0;border:1px solid var(--line);border-radius:8px;
                 padding:8px 10px;font-size:14px;background:#fff;color:var(--ink)}
  .aviso{font-size:12.5px;background:#fbf3e6;color:#8a6420;padding:7px 10px;
         border-radius:8px;margin-bottom:6px}
  /* ---- Muestrario de plantas ---- */
  .btn.muestra{width:100%;text-align:center;margin-top:5px;border-color:var(--accent);
               color:var(--accent);font-weight:600}
  .btn.muestra:hover{background:var(--accent);color:#fff}
  .modal .caja.ancha{max-width:1060px}
  .rejilla{display:grid;gap:12px;
           grid-template-columns:repeat(auto-fill,minmax(148px,1fr))}
  .forma{border:1px solid var(--line);border-radius:12px;background:#fff;padding:8px;
         cursor:pointer;display:flex;flex-direction:column;gap:5px;text-align:left;
         font:inherit;color:inherit}
  .forma:hover{border-color:var(--accent)}
  .forma.puesta{border-color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink)}
  .forma .lam{background:#efeae2;border-radius:8px;aspect-ratio:1/1;overflow:hidden;
              display:flex;align-items:center;justify-content:center}
  .forma .lam img{width:100%;height:100%;object-fit:contain;display:block}
  .forma .lam span{font-size:11px;color:var(--muted);text-align:center;padding:0 6px}
  .forma b{font-size:13px;font-weight:600;line-height:1.25}
  .forma .g{font-size:11.5px;color:var(--muted);font-variant-numeric:tabular-nums}
  .forma .g.warn{color:#8a6420}
  @media(max-width:900px){
    .crear{grid-template-columns:1fr}
    .panelp{position:static;max-height:none}
  }
</style>
</head>
<body>
<header>
  <div>
    <h1>Catálogo 3D</h1>
    <div class="sub" id="carpeta"></div>
  </div>
  <div class="tabs">
    <button class="tab activo" id="tab-mios" onclick="cambiarVista('mios')">Mis diseños</button>
    <button class="tab" id="tab-pruebas" onclick="cambiarVista('pruebas')">🧪 Pruebas de productos</button>
    <button class="tab" id="tab-pendientes" onclick="cambiarVista('pendientes')">⏳ Por cargar</button>
    <button class="tab" id="tab-cargados" onclick="cambiarVista('cargados')">✓ Con información</button>
    <button class="tab" id="tab-descargas" onclick="cambiarVista('descargas')">Descargas</button>
    <button class="tab" id="tab-negocio" onclick="cambiarVista('negocio')">📊 Mi negocio</button>
    <button class="tab" id="tab-crear" onclick="cambiarVista('crear')">✦ Crear</button>
  </div>
  <div class="controls">
    <div class="stat">Piezas: <b id="total">0</b></div>
    <div class="field">
      <label>Costo filamento / kg</label>
      <input id="precio" type="number" min="0" step="10" value="350">
    </div>
    <div class="field">
      <label>Costo paquetería</label>
      <div class="paqsel">
        <select id="paquete" title="Paquetería que se usa por defecto en todas las tarjetas"></select>
        <button class="btn" onclick="abrirPaqueteria()" title="Editar los costos de paquetería">⚙</button>
      </div>
    </div>
    <button class="btn" onclick="alternarTodo()" id="btnTodo">☑ Seleccionar todo</button>
    <button class="btn" onclick="cargar()">↻ Recargar</button>
  </div>
</header>
<main>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">
    No se encontraron archivos .3mf.
  </div>
  <section id="panelNegocio" style="display:none">
    <div class="mescab">
      <button class="btn" onclick="cambiarMes(-1)" title="Mes anterior">‹</button>
      <input type="month" id="negMes" onchange="elegirMes(this.value)">
      <button class="btn" onclick="cambiarMes(1)" title="Mes siguiente">›</button>
      <span class="sub" id="negEstado"></span>
    </div>
    <div class="negcols">
      <div class="tablacaja">
        <h3>Ventas del mes</h3>
        <p class="pista">Lo que te retornó cada venta y lo que te costó producirla.
          Al elegir el diseño se llenan solos con lo que tiene cargado, y se
          quedan congelados: si mañana sube el filamento, el mes cerrado no cambia.</p>
        <table><thead><tr>
          <th>Diseño</th><th>Piezas</th><th>Me retornó c/u</th>
          <th>Me costó c/u</th><th>Margen</th><th></th>
        </tr></thead><tbody id="negVentas"></tbody></table>
        <button class="btn masbtn" onclick="agregarVenta()">+ Registrar venta</button>
      </div>
      <div class="tablacaja">
        <h3>Gastos del mes</h3>
        <p class="pista">Lo que no va dentro de la pieza: publicidad, luz, renta,
          la compra de un rollo…</p>
        <table><thead><tr>
          <th>Concepto</th><th>Tipo</th><th>Monto</th><th></th>
        </tr></thead><tbody id="negGastos"></tbody></table>
        <datalist id="conceptos">
          <option value="Publicidad">
          <option value="Recibo de luz">
          <option value="Compra de filamento">
          <option value="Insumos de paquetería">
          <option value="Renta">
          <option value="Mantenimiento de impresora">
          <option value="Comisiones y envíos">
        </datalist>
        <button class="btn masbtn" onclick="agregarGasto()">+ Agregar gasto</button>
      </div>
    </div>
    <div id="negResumen"></div>
    <div class="analisis">
      <div class="preciocab">
        <h3>Precios y publicidad</h3>
        <label>Quiero ganar por pieza
          <input type="number" id="negObjetivo" min="0" step="10" value="0"
                 oninput="cambioObjetivo(this.value)">
        </label>
      </div>
      <p class="pista">El ROAS está calculado sobre el precio que paga el
        comprador, que es como lo reporta MercadoLibre. El de equilibrio solo
        paga la pieza; el objetivo paga además los gastos generales del mes
        repartidos entre lo que vendiste y la utilidad que pediste arriba.</p>
      <div id="negPrecios"></div>
    </div>
  </section>
  <section id="panelCrear" style="display:none">
    <div id="crearNo" class="empty" style="display:none">
      No encontré la carpeta <b>generadores/</b> junto a catalog3d.py.
    </div>
    <div class="crear" id="crearSi">
      <aside class="panelp">
        <div class="par">
          <div class="fila"><label>Diseño base</label></div>
          <select id="crDiseno"></select>
          <span class="val" id="crDesc"></span>
        </div>
        <div id="crGrupos"></div>
      </aside>
      <div class="vistaprev">
        <div class="lienzo" id="crLienzo">
          <img id="crImg" alt="Vista previa">
          <div class="cargando">Calculando…</div>
        </div>
        <div class="vistactrl">
          <label for="crGiro">Girar</label>
          <input type="range" id="crGiro" min="0" max="355" step="5" value="32">
          <label for="crElev">Altura</label>
          <input type="range" id="crElev" min="5" max="85" step="5" value="31">
          <button class="btn" onclick="vistaAuto()" title="Volver a la vista automática">↺</button>
        </div>
        <div class="meta" id="crDatos"></div>
        <div id="crAvisos"></div>
        <div class="guardar">
          <input id="crNombre" placeholder="Nombre del archivo (automático)">
          <button class="btn abrir" id="crGuardar" style="width:auto"
                  onclick="guardarDiseno()">Guardar en mi carpeta</button>
        </div>
      </div>
    </div>
  </section>
</main>
<div class="barra" id="barra">
  <b id="barraCuenta">0 seleccionados</b>
  <button class="btn mover" id="barraMover" onclick="moverSeleccionados()">→ Mover a mi carpeta</button>
  <button class="btn peligro" onclick="eliminarSeleccionados()">🗑 Eliminar</button>
  <button class="btn" onclick="limpiarSeleccion()">Cancelar</button>
</div>
<div class="modal" id="modalPaq" onclick="if(event.target===this)cerrarPaqueteria()">
  <div class="caja">
    <h2>Costos de paquetería</h2>
    <p class="hint">Apunta lo que te costó la última compra de cada elemento y
      cuántas unidades traía: el costo por unidad se calcula solo. La suma de
      un paquete es lo que le cuesta el envío a cada pieza.</p>
    <div class="tabs" id="paqTabs"></div>
    <input class="nombrepaq" id="paqNombre" placeholder="Nombre del paquete"
           oninput="paqRenombrar(this.value)">
    <table class="paq">
      <thead><tr>
        <th>Elemento</th><th>Última compra</th><th>Unidades</th>
        <th>Por unidad</th><th></th>
      </tr></thead>
      <tbody id="paqFilas"></tbody>
    </table>
    <div class="paqpie">
      <button class="btn" onclick="paqAgregar()">+ Agregar elemento</button>
      <div class="paqtotal">Total costos generales:
        <b id="paqTotal">$0.00</b> <span>por pedido</span></div>
    </div>
    <div class="acciones">
      <button class="btn" onclick="cerrarPaqueteria()">Cancelar</button>
      <button class="btn principal" onclick="paqGuardar()">Guardar paquetería</button>
    </div>
  </div>
</div>
<div class="modal" id="modalFormas" onclick="if(event.target===this)cerrarMuestrario()">
  <div class="caja ancha">
    <h2>Las plantas, una al lado de la otra</h2>
    <p class="hint" id="formasHint"></p>
    <div class="rejilla" id="formasRejilla"></div>
    <div class="acciones">
      <button class="btn" onclick="cerrarMuestrario()">Cerrar</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
const MONEDA = "__MONEDA__";
const APP_NOMBRE = "__APP_NOMBRE__";
let disenosMios = [];
let disenosDescargas = [];
let descargasCargadas = false;
let vista = 'mios';

/* «Por cargar» y «Con información» son la misma carpeta vista con un
   filtro: los diseños a los que todavía les falta un dato para cerrar la
   cuenta, y los que ya la tienen completa. */
function esMio(){ return vista==='mios' || vista==='pendientes' || vista==='cargados' || vista==='pruebas'; }

/* «Pruebas de productos» es la subcarpeta de lo que se está probando: se ve
   en su propia pestaña y no se mezcla con «Mis diseños» ni sus filtros. */
const CARPETA_PRUEBAS = 'Pruebas de productos';
function enPruebas(d){ return d.subcarpeta === CARPETA_PRUEBAS; }
function misSinPruebas(){ return disenosMios.filter(d => !enPruebas(d)); }

function hayTarjetas(){ return vista!=='crear' && vista!=='negocio'; }

function activos(){
  if(!hayTarjetas()) return [];    // Crear y Mi negocio no tienen tarjetas
  if(vista==='descargas') return disenosDescargas;
  if(vista==='pruebas') return disenosMios.filter(enPruebas);
  if(vista==='pendientes') return misSinPruebas().filter(d => !tieneInfo(d));
  if(vista==='cargados') return misSinPruebas().filter(d => tieneInfo(d));
  return misSinPruebas();
}

/* Lo que está pintado ahora mismo, en su orden. Los botones de cada tarjeta
   mandan su posición, y en una vista filtrada esa posición no es la de la
   lista completa; si además el diseño deja de cumplir el filtro mientras
   escribes, recalcularlo movería las tarjetas debajo del cursor. */
let listaVista = [];
function enVista(i){ return listaVista[i]; }

/* Al borrar o mover hay que sacarlo de la lista de verdad, no de la copia
   filtrada que se está viendo. */
function quitar(archivo){
  [disenosMios, disenosDescargas].forEach(lista => {
    const k = lista.findIndex(d => d.archivo === archivo);
    if(k >= 0) lista.splice(k, 1);
  });
}

// Selección múltiple: se guarda por carpeta y por ruta de archivo, así
// sobrevive a los re-render y no se mezcla entre pestañas.
const seleccion = {mios: new Set(), descargas: new Set()};
function claveSel(){ return vista==='descargas' ? 'descargas' : 'mios'; }
function selActual(){ return seleccion[claveSel()]; }

function alternarSel(i, marcado){
  const d = enVista(i);
  if(!d) return;
  if(marcado) selActual().add(d.archivo); else selActual().delete(d.archivo);
  render();
}

function alternarTodo(){
  const lista = listaVista;
  const sel = selActual();
  if(sel.size === lista.length && lista.length){ sel.clear(); }
  else { lista.forEach(d => sel.add(d.archivo)); }
  render();
}

function limpiarSeleccion(){ selActual().clear(); render(); }

/* Tras recargar del disco, olvida lo seleccionado que ya no existe. */
function purgarSeleccion(clave, lista){
  const vivos = new Set(lista.map(d => d.archivo));
  seleccion[clave].forEach(a => { if(!vivos.has(a)) seleccion[clave].delete(a); });
}

function actualizarBarra(){
  const n = hayTarjetas() ? selActual().size : 0;
  const total = listaVista.length;
  const barra = document.getElementById('barra');
  barra.classList.toggle('show', n > 0);
  document.body.classList.toggle('conbarra', n > 0);
  document.getElementById('barraCuenta').textContent =
    n === 1 ? '1 seleccionado' : n + ' seleccionados';
  // Mover solo tiene sentido desde Descargas
  document.getElementById('barraMover').style.display =
    vista === 'descargas' ? '' : 'none';
  document.getElementById('btnTodo').textContent =
    (n === total && total) ? '☐ Quitar selección' : '☑ Seleccionar todo';
}

function fmtCosto(n){
  return new Intl.NumberFormat('es-MX',{style:'currency',currency:MONEDA,
    maximumFractionDigits:2}).format(n);
}
function precioKg(){ return parseFloat(document.getElementById('precio').value)||0; }
function escapa(s){ return String(s==null?'':s)
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function escapaAttr(s){ return escapa(s).replace(/"/g,'&quot;'); }
function num(v){ const n = parseFloat(v); return isFinite(n) ? n : 0; }

/* ---------- Paquetería ---------- */
/* El costo por unidad sale de la última compra: lo que costó entre lo que
   traía. Se calcula aquí y no en el servidor para que el editor enseñe el
   número mientras se escribe. */
function costoUnidad(e){
  const u = num(e.unidades) > 0 ? num(e.unidades) : 1;
  return num(e.costo_compra) / u;
}
function totalPaquete(p){
  return p ? (p.elementos||[]).reduce((s,e) => s + costoUnidad(e), 0) : 0;
}
function paqPorIndice(i){
  return (i!=null && i>=0 && config.paquetes[i]) ? config.paquetes[i] : null;
}
function paqueteActivo(){ return paqPorIndice(config.paquete_activo); }
/* Cada diseño puede seguir al catálogo (null), elegir otro paquete, o no
   llevar paquetería (-1), por ejemplo si se entrega en mano. */
function paqueteDe(d){
  if(d.paquete === -1) return null;
  if(d.paquete == null) return paqueteActivo();
  return paqPorIndice(d.paquete);
}

/* ---------- Cuentas de una pieza ---------- */
function pesoDe(d){ return d.peso_manual != null ? d.peso_manual : d.peso_g; }
function costoMaterial(d){
  if(d.costo_pieza != null) return d.costo_pieza;   // costo escrito a mano
  const p = pesoDe(d);
  return p != null ? p/1000*precioKg() : null;
}
/* El retorno de inversión es lo que te DEPOSITAN cuando alguien compra: no
   un porcentaje, sino el dinero que te llega a la cuenta. Es el número que
   ves en MercadoLibre, así que se escribe tal cual. */
function retornoDe(d){ return d.retorno != null ? d.retorno : null; }

function cuentas(d){
  const material = costoMaterial(d);
  const paq = paqueteDe(d);
  const envio = totalPaquete(paq);
  const total = material != null ? material + envio : null;
  const retorno = retornoDe(d);
  return {material, paq, envio, total, retorno,
          ganancia: (total != null && retorno != null) ? retorno - total : null};
}

/* Lo que le falta a un diseño para tener la cuenta completa. Es lo que
   separa la pestaña «Por cargar» de la de «Con información». */
function faltantes(d){
  const f = [];
  if(pesoDe(d) == null && d.costo_pieza == null) f.push('peso');
  if(retornoDe(d) == null) f.push('retorno');
  return f;
}
function tieneInfo(d){ return faltantes(d).length === 0; }

/* La tarjeta solo enseña lo que se usa para decidir: gramos, lo que cuesta
   y, si ya tiene precio, la ganancia. El resto vive en «Costos y precio». */
function chipsHTML(d){
  const chips = [];
  const peso = pesoDe(d);
  if(peso!=null) chips.push(`<span class="chip peso">${peso.toFixed(1)} g${d.peso_manual!=null?' ✎':''}</span>`);
  else chips.push(`<span class="chip warn">sin laminar</span>`);

  if(!esMio()){
    if(peso!=null) chips.push(`<span class="chip costo">${fmtCosto(peso/1000*precioKg())}</span>`);
    return chips.join('');
  }

  const c = cuentas(d);
  if(c.total!=null){
    chips.push(`<span class="chip costo" title="Material ${fmtCosto(c.material)} + paquetería ${fmtCosto(c.envio)}">${fmtCosto(c.total)} me cuesta</span>`);
  }
  if(c.ganancia!=null){
    const clase = c.ganancia >= 0 ? 'ganancia' : 'perdida';
    const signo = c.ganancia >= 0 ? '+' : '';
    chips.push(`<span class="chip ${clase}" title="Retorno ${fmtCosto(c.retorno)} menos costo total ${fmtCosto(c.total)}">
      ${signo}${fmtCosto(c.ganancia)} ganancia</span>`);
  }
  return chips.join('');
}

function linea(txt, valor, clase){
  return `<div class="linea ${clase||''}"><span>${txt}</span><b>${valor}</b></div>`;
}

function resumenHTML(d){
  const c = cuentas(d);
  if(c.total == null){
    return linea('Escribe el peso o el costo de la pieza', '—');
  }
  const etiquetaPaq = c.paq ? 'Paquetería · ' + escapa(c.paq.nombre) : 'Sin paquetería';
  let cuenta = linea(d.costo_pieza!=null ? 'Pieza (a mano)' : 'Pieza · filamento', fmtCosto(c.material))
             + linea(etiquetaPaq, fmtCosto(c.envio))
             + linea('Me cuesta el producto', fmtCosto(c.total), 'fuerte');
  if(d.ml_precio_venta != null){
    cuenta += linea('Precio publicado', fmtCosto(d.ml_precio_venta));
  }
  if(c.retorno == null){
    return cuenta + linea('Me retorna la venta', 'falta cargarlo');
  }
  return cuenta
       + linea('Me retorna la venta', fmtCosto(c.retorno))
       + linea('Ganancia por venta', fmtCosto(c.ganancia),
               'fuerte ' + (c.ganancia >= 0 ? 'gana' : 'pierde'));
}

function panelCostosHTML(d, i){
  const opciones = ['<option value=""' + (d.paquete==null?' selected':'') + '>Del catálogo · ' +
                    (paqueteActivo() ? escapa(paqueteActivo().nombre) : 'ninguna') + '</option>']
    .concat(config.paquetes.map((p,k) =>
      `<option value="${k}"${d.paquete===k?' selected':''}>${escapa(p.nombre)} · ${fmtCosto(totalPaquete(p))}</option>`))
    .concat([`<option value="-1"${d.paquete===-1?' selected':''}>Sin paquetería</option>`])
    .join('');
  const pesoVal = d.peso_manual != null ? d.peso_manual : (d.peso_g != null ? d.peso_g : '');
  const autoTxt = costoMaterialAuto(d);
  return `<details class="costos"${abiertos.has(d.archivo)?' open':''}
             ontoggle="alternarPanel(${i}, this.open)">
    <summary>💰 Costos y precio</summary>
    <div class="cgrid">
      <label>Peso por unidad (g)
        <input type="number" min="0" step="0.1" value="${pesoVal}"
               placeholder="${d.peso_g!=null?d.peso_g:'—'}"
               oninput="cambioCosto(${i},'peso_g',this.value)"></label>
      <label>Costo de la pieza
        <input type="number" min="0" step="0.5" value="${d.costo_pieza!=null?d.costo_pieza:''}"
               placeholder="${autoTxt}"
               oninput="cambioCosto(${i},'costo_pieza',this.value)"></label>
      <label class="ancho">Paquetería
        <select onchange="cambioCosto(${i},'paquete',this.value)">${opciones}</select></label>
      <label class="ancho">Retorno de inversión (lo que me depositan)
        <input type="number" min="0" step="10" value="${d.retorno!=null?d.retorno:''}"
               placeholder="cuánto te depositan"
               oninput="cambioCosto(${i},'retorno',this.value)"></label>
      <label class="ancho">Precio de la competencia (opcional)
        <input type="number" min="0" step="10" value="${d.competencia!=null?d.competencia:''}"
               placeholder="para saber si vas caro o barato"
               oninput="cambioCosto(${i},'competencia',this.value)"></label>
    </div>
    <div class="resumen" id="resumen-${i}">${resumenHTML(d)}</div>
  </details>`;
}

/* Lo que costaría la pieza solo por filamento: es la pista del campo
   «costo de la pieza», para saber qué número estás pisando. */
function costoMaterialAuto(d){
  const p = pesoDe(d);
  return p != null ? fmtCosto(p/1000*precioKg()) + ' auto' : 'sin peso';
}

/* Los paneles abiertos se recuerdan por archivo: render() rehace las
   tarjetas y si no, se cerrarían solos a cada rato. */
const abiertos = new Set();
function alternarPanel(i, abierto){
  const d = enVista(i);
  if(!d) return;
  if(abierto) abiertos.add(d.archivo); else abiertos.delete(d.archivo);
}

/* Al escribir en una tarjeta no se rehace la galería entera: solo se
   recalculan sus chips y su resumen, para no perder el cursor. */
function refrescarTarjeta(i){
  const d = enVista(i);
  if(!d) return;
  const chips = document.getElementById('chips-'+i);
  const res = document.getElementById('resumen-'+i);
  if(chips) chips.innerHTML = chipsHTML(d);
  if(res) res.innerHTML = resumenHTML(d);
  // la tarjeta puede acabar de cambiar de pestaña, pero no se mueve de
  // sitio hasta que tú cambies de vista: solo se actualiza la cuenta
  actualizarPestanas();
}

function cambioCosto(i, campo, valor){
  const d = enVista(i);
  if(!d) return;
  let v;
  if(campo === 'paquete'){
    v = valor === '' ? null : parseInt(valor, 10);
    d.paquete = v;
  } else {
    const txt = String(valor).trim();
    v = txt === '' ? null : parseFloat(txt);
    if(v != null && (!isFinite(v) || v < 0)) return;   // medio número: aún no
    // un 0 es el campo vacío: vuelve a lo automático, igual que lo
    // entiende el servidor
    if(v === 0) v = null;
    if(campo === 'peso_g') d.peso_manual = v;
    else if(campo === 'costo_pieza') d.costo_pieza = v;
    else if(campo === 'competencia') d.competencia = v;
    else d.retorno = v;
  }
  refrescarTarjeta(i);
  guardarCampo(d.archivo, campo, v);
}

/* Se guarda en disco poco después de la última tecla, no en cada una, y
   todos los campos de un diseño viajan juntos: si cada uno se fuera por su
   cuenta, dos guardados a la vez se pisarían en el archivo. */
const pendientes = {}, relojes = {};
function guardarCampo(archivo, campo, valor){
  pendientes[archivo] = Object.assign(pendientes[archivo] || {}, {[campo]: valor});
  clearTimeout(relojes[archivo]);
  relojes[archivo] = setTimeout(async () => {
    const campos = pendientes[archivo];
    delete pendientes[archivo];
    try{
      const r = await fetch('/api/datos_set', {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({archivo, campos})});
      const res = await r.json();
      if(!res.ok) toast('✗ ' + (res.mensaje || 'No se pudo guardar'));
    }catch(e){ toast('✗ Error de conexión'); }
  }, 500);
}

/* ---------- Configuración del catálogo ---------- */
let config = {precio_kg:null, paquete_activo:0, paquetes:[]};
let relojConfig = null;

function guardarConfig(){
  clearTimeout(relojConfig);
  relojConfig = setTimeout(async () => {
    try{
      const r = await fetch('/api/config_set', {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({config})});
      const res = await r.json();
      if(res.ok && res.config) config = res.config;
      else if(!res.ok) toast('✗ No pude guardar los ajustes de costos');
    }catch(e){ toast('✗ Error de conexión'); }
  }, 500);
}

function pintarPaquetes(){
  const sel = document.getElementById('paquete');
  sel.innerHTML = config.paquetes.map((p,i) =>
      `<option value="${i}"${config.paquete_activo===i?' selected':''}>${escapa(p.nombre)} · ${fmtCosto(totalPaquete(p))}</option>`)
    .concat([`<option value="-1"${config.paquete_activo===-1?' selected':''}>Sin paquetería</option>`])
    .join('');
}

/* ---------- Editor de paquetería ---------- */
let paqEdit = null, paqTab = 0;

function abrirPaqueteria(){
  paqEdit = JSON.parse(JSON.stringify(config.paquetes));
  paqTab = Math.max(0, config.paquete_activo);
  if(paqTab >= paqEdit.length) paqTab = 0;
  document.getElementById('modalPaq').classList.add('show');
  dibujarPaqueteria();
}
function cerrarPaqueteria(){
  document.getElementById('modalPaq').classList.remove('show');
}

function dibujarPaqueteria(){
  const p = paqEdit[paqTab];
  document.getElementById('paqTabs').innerHTML = paqEdit.map((x,i) =>
    `<button class="tab${i===paqTab?' activo':''}" onclick="paqTab=${i};dibujarPaqueteria()">${escapa(x.nombre)} · ${fmtCosto(totalPaquete(x))}</button>`).join('');
  document.getElementById('paqNombre').value = p.nombre;
  document.getElementById('paqFilas').innerHTML = (p.elementos||[]).map((e,k) => `
    <tr>
      <td><input value="${escapaAttr(e.nombre)}" oninput="paqCampo(${k},'nombre',this.value)"></td>
      <td><input type="number" min="0" step="0.5" value="${e.costo_compra}"
                 oninput="paqCampo(${k},'costo_compra',this.value)"></td>
      <td><input type="number" min="0" step="1" value="${e.unidades}"
                 oninput="paqCampo(${k},'unidades',this.value)"></td>
      <td class="unit" id="paqUnit-${k}">${fmtCosto(costoUnidad(e))}</td>
      <td class="quita"><button class="btn del" title="Quitar elemento"
                                onclick="paqQuitar(${k})">🗑</button></td>
    </tr>`).join('') ||
    '<tr><td colspan="5" style="color:var(--muted);padding:10px 0">Este paquete no lleva nada todavía.</td></tr>';
  document.getElementById('paqTotal').textContent = fmtCosto(totalPaquete(p));
}

/* Al teclear solo se refresca el costo por unidad y el total: redibujar la
   tabla entera dejaría el cursor fuera del campo. */
function paqCampo(k, campo, valor){
  const e = paqEdit[paqTab].elementos[k];
  if(!e) return;
  e[campo] = campo === 'nombre' ? valor : num(valor);
  const celda = document.getElementById('paqUnit-'+k);
  if(celda) celda.textContent = fmtCosto(costoUnidad(e));
  document.getElementById('paqTotal').textContent = fmtCosto(totalPaquete(paqEdit[paqTab]));
}
function paqRenombrar(v){ paqEdit[paqTab].nombre = v; }
function paqAgregar(){
  paqEdit[paqTab].elementos.push({nombre:'Elemento nuevo', costo_compra:0, unidades:1});
  dibujarPaqueteria();
}
function paqQuitar(k){
  paqEdit[paqTab].elementos.splice(k, 1);
  dibujarPaqueteria();
}
async function paqGuardar(){
  config.paquetes = paqEdit;
  try{
    const r = await fetch('/api/config_set', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({config})});
    const res = await r.json();
    if(res.ok){
      if(res.config) config = res.config;
      pintarPaquetes();
      render();
      cerrarPaqueteria();
      toast('✓ Paquetería guardada');
    } else { toast('✗ No pude guardar la paquetería'); }
  }catch(e){ toast('✗ Error de conexión'); }
}

function render(){
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  const disenos = listaVista = activos();
  grid.innerHTML = '';
  if(!disenos.length){
    empty.style.display='block';
    empty.textContent =
      vista==='pendientes' ? 'Todos tus diseños ya tienen su información cargada.' :
      vista==='cargados'   ? 'Todavía no le has cargado la información a ningún diseño.' :
      vista==='pruebas'    ? 'No hay productos en prueba. Usa «🧪 A pruebas» en una tarjeta de Mis diseños.' :
                             'No se encontraron archivos .3mf.';
  }
  else empty.style.display='none';

  disenos.forEach((d, i) => {
    const marcado = selActual().has(d.archivo);

    const card = document.createElement('div');
    card.className = 'card' + (marcado ? ' sel' : '');

    const interior = d.miniatura
      ? `<img src="${d.miniatura}" alt="">`
      : `<span class="noimg">sin miniatura</span>`;
    const nombreEscapado = d.nombre.replace(/"/g,'&quot;');

    // El nombre va como etiqueta en la esquina inferior de la imagen (se
    // edita ahí mismo) y el bote de basura arriba a la derecha, frente al check.
    const etiqueta = esMio()
      ? `<div class="etiqueta" onclick="event.stopPropagation()">
          <input value="${nombreEscapado}" size="${Math.max(4, d.nombre.length)}"
                 title="${nombreEscapado} · clic para renombrar"
                 data-archivo="${d.archivo.replace(/"/g,'&quot;')}"
                 data-idx="${i}"
                 oninput="marcar(${i})"
                 onkeydown="if(event.key==='Enter'){guardar(${i})}">
          <button class="btn save" id="save-${i}" onclick="guardar(${i})" title="Guardar nombre">💾</button>
        </div>`
      : `<div class="etiqueta"><span title="${nombreEscapado}">${nombreEscapado}</span></div>`;

    const thumb = `<div class="thumb" onclick="abrir(${i})" title="Abrir en ${APP_NOMBRE}">
        <label class="selbox" onclick="event.stopPropagation()" title="Seleccionar">
          <input type="checkbox" ${marcado ? 'checked' : ''}
                 onchange="alternarSel(${i}, this.checked)">
        </label>
        <button class="btn del" onclick="event.stopPropagation();eliminar(${i})"
                title="${esMio() ? 'Eliminar archivo' : 'Eliminar de Descargas'}">🗑</button>
        ${interior}<span class="abrir">▶ Abrir en ${APP_NOMBRE}</span>
        ${etiqueta}
      </div>`;

    const botonMover = vista==='descargas'
      ? `<button class="btn mover" onclick="mover(${i})">→ Mover a mi carpeta</button>`
      : '';

    // va en la fila de MercadoLibre, del mismo tamaño que «Vincular ML»
    const botonPruebas = esMio() && !enPruebas(d)
      ? `<button class="btn apruebas" onclick="moverAPruebas(${i})" title="Mover a Pruebas de productos">🧪 A pruebas</button>`
      : '';

    const filaML = esMio() ? `
      <div class="ml">
        ${d.ml_link ? `<a class="btn ml-ver" href="${d.ml_link}" target="_blank" rel="noopener" title="Ver en MercadoLibre">🛒 Ir</a>` : ''}
        <button class="btn ml-editar" onclick="editarML(${i})">${d.ml_link ? '✎' : '🔗 Vincular ML'}</button>
        ${botonPruebas}
      </div>` : '';

    card.innerHTML = thumb + `
      <div class="body">
        <div class="meta" id="chips-${i}">${chipsHTML(d)}</div>
        <button class="btn abrir" onclick="abrir(${i})">▶ Abrir en ${APP_NOMBRE}</button>
        ${botonMover}
        ${filaML}
        ${esMio() ? panelCostosHTML(d, i) : ''}
      </div>`;
    grid.appendChild(card);
  });

  document.getElementById('total').textContent = disenos.length;
  actualizarPestanas();
  actualizarBarra();
}

/* Las pestañas llevan la cuenta: cuántos diseños esperan información y
   cuántos ya la tienen. */
function actualizarPestanas(){
  const mios = misSinPruebas();
  const pendientes = mios.filter(d => !tieneInfo(d)).length;
  document.getElementById('tab-pendientes').textContent = '⏳ Por cargar · ' + pendientes;
  document.getElementById('tab-cargados').textContent =
    '✓ Con información · ' + (mios.length - pendientes);
  document.getElementById('tab-pruebas').textContent =
    '🧪 Pruebas de productos · ' + (disenosMios.length - mios.length);
}

function marcar(i){
  document.getElementById('save-'+i).classList.add('show');
}

async function guardar(i){
  const input = document.querySelector(`input[data-idx="${i}"]`);
  const viejo = input.dataset.archivo;
  const nuevo = input.value.trim();
  if(!nuevo){ toast('El nombre está vacío'); return; }
  try{
    const r = await fetch('/api/rename', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({viejo, nuevo})
    });
    const res = await r.json();
    if(res.ok){
      const d = enVista(i);
      // la ruta es la clave de la selección y del panel abierto: hay que
      // moverlas al nombre nuevo
      if(seleccion.mios.delete(d.archivo)) seleccion.mios.add(res.nombre_final);
      if(abiertos.delete(d.archivo)) abiertos.add(res.nombre_final);
      d.archivo = res.nombre_final;
      const base = res.nombre_final.split('/').pop();
      d.nombre = base.replace(/\\.3mf$/i,'');
      input.dataset.archivo = res.nombre_final;
      document.getElementById('save-'+i).classList.remove('show');
      toast('✓ Renombrado en disco');
    } else {
      toast('✗ '+res.mensaje);
    }
  }catch(e){ toast('✗ Error de conexión'); }
}

async function eliminar(i){
  const d = enVista(i);
  if(!d) return;
  const donde = vista==='descargas' ? 'de Descargas' : 'del disco';
  if(!confirm(`¿Eliminar «${d.nombre}» ${donde}? Esta acción no se puede deshacer.`)) return;
  try{
    const r = await fetch('/api/delete', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivo: d.archivo, origen: vista})
    });
    const res = await r.json();
    if(res.ok){
      selActual().delete(d.archivo);
      quitar(d.archivo);
      render();
      toast(`✓ Eliminado ${donde}`);
    } else {
      toast('✗ '+res.mensaje);
    }
  }catch(e){ toast('✗ Error de conexión'); }
}

async function abrir(i){
  const d = enVista(i);
  if(!d) return;
  toast(`Abriendo «${d.nombre}» en ${APP_NOMBRE}…`);
  try{
    const r = await fetch('/api/abrir', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivo: d.archivo, origen: vista})
    });
    const res = await r.json();
    if(!res.ok) toast('✗ '+res.mensaje);
  }catch(e){ toast('✗ Error de conexión'); }
}

async function mover(i){
  const d = enVista(i);
  if(!d) return;
  try{
    const r = await fetch('/api/mover', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivo: d.archivo})
    });
    const res = await r.json();
    if(res.ok){
      seleccion.descargas.delete(d.archivo);
      quitar(d.archivo);
      render();
      toast(`✓ Movido a Mis diseños (${res.nombre_final})`);
      cargarMios();
    } else {
      toast('✗ '+res.mensaje);
    }
  }catch(e){ toast('✗ Error de conexión'); }
}

async function moverAPruebas(i){
  const d = enVista(i);
  if(!d) return;
  try{
    const r = await fetch('/api/mover_pruebas', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivo: d.archivo})
    });
    const res = await r.json();
    if(res.ok){
      selActual().delete(d.archivo);
      toast(`✓ «${d.nombre}» movido a la pestaña Pruebas de productos`);
      cargarMios();
    } else {
      toast('✗ '+res.mensaje);
    }
  }catch(e){ toast('✗ Error de conexión'); }
}

async function editarML(i){
  const d = enVista(i);
  if(!d) return;
  const link = prompt('Link de la publicación en MercadoLibre:', d.ml_link || '');
  if(link === null) return;
  const precioTxt = prompt('Precio de venta en MercadoLibre (MXN):',
                            d.ml_precio_venta!=null ? d.ml_precio_venta : '');
  if(precioTxt === null) return;
  try{
    const r = await fetch('/api/datos_set', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivo: d.archivo,
                            campos: {link, precio_venta: precioTxt}})
    });
    const res = await r.json();
    if(res.ok){
      d.ml_link = res.datos.link || null;
      d.ml_precio_venta = res.datos.precio_venta != null ? res.datos.precio_venta : null;
      render();
      toast('✓ Guardado');
    } else {
      toast('✗ '+(res.mensaje||'No se pudo guardar'));
    }
  }catch(e){ toast('✗ Error de conexión'); }
}

async function eliminarSeleccionados(){
  const sel = selActual();
  const archivos = listaVista.filter(d => sel.has(d.archivo)).map(d => d.archivo);
  if(!archivos.length) return;
  const donde = vista==='descargas' ? 'de Descargas' : 'del disco';
  if(!confirm(`¿Eliminar ${archivos.length} archivo(s) ${donde}? Esta acción no se puede deshacer.`)) return;
  try{
    const r = await fetch('/api/delete_multi', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivos, origen: vista})
    });
    const res = await r.json();
    aplicarResultados(res.resultados, `Eliminados ${donde}`);
  }catch(e){ toast('✗ Error de conexión'); }
}

async function moverSeleccionados(){
  const sel = selActual();
  const archivos = disenosDescargas.filter(d => sel.has(d.archivo)).map(d => d.archivo);
  if(!archivos.length) return;
  try{
    const r = await fetch('/api/mover_multi', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({archivos})
    });
    const res = await r.json();
    aplicarResultados(res.resultados, 'Movidos a Mis diseños');
    cargarMios();
  }catch(e){ toast('✗ Error de conexión'); }
}

/* Quita de la galería solo los que sí se procesaron y avisa de los que fallaron. */
function aplicarResultados(resultados, etiqueta){
  if(!resultados){ toast('✗ Respuesta inesperada del servidor'); return; }
  const hechos = new Set(resultados.filter(r => r.ok).map(r => r.archivo));
  const fallos = resultados.filter(r => !r.ok);
  hechos.forEach(a => { quitar(a); selActual().delete(a); });
  render();
  if(fallos.length){
    toast(`✓ ${hechos.size} ${etiqueta} · ✗ ${fallos.length} con error: ${fallos[0].mensaje}`);
  } else {
    toast(`✓ ${hechos.size} ${etiqueta}`);
  }
}

let toastT;
function toast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(toastT);
  toastT = setTimeout(()=>t.classList.remove('show'), 2200);
}

let carpetaMiosTexto = '';
let carpetaDescargasTexto = '';

async function cargarMios(){
  const r = await fetch('/api/designs');
  const data = await r.json();
  disenosMios = data.disenos;
  purgarSeleccion('mios', disenosMios);
  carpetaMiosTexto = data.carpeta;
  if(data.config) config = data.config;
  // el precio guardado manda; si nunca se tocó, el que traen los .3mf
  document.getElementById('precio').value =
    config.precio_kg != null ? config.precio_kg : (data.precio_sugerido || precioKg());
  pintarPaquetes();
  actualizarPestanas();
  if(esMio()){
    document.getElementById('carpeta').textContent = carpetaMiosTexto;
    render();
  }
}

async function cargarDescargas(){
  const r = await fetch('/api/downloads');
  const data = await r.json();
  disenosDescargas = data.disenos;
  purgarSeleccion('descargas', disenosDescargas);
  descargasCargadas = true;
  carpetaDescargasTexto = data.carpeta;
  if(vista==='descargas'){
    document.getElementById('carpeta').textContent = carpetaDescargasTexto;
    render();
  }
}

function cambiarVista(v){
  vista = v;
  ['mios','pruebas','pendientes','cargados','descargas','negocio','crear'].forEach(k =>
    document.getElementById('tab-'+k).classList.toggle('activo', v===k));

  const esCrear = v==='crear', esNegocio = v==='negocio';
  document.getElementById('panelCrear').style.display = esCrear ? '' : 'none';
  document.getElementById('panelNegocio').style.display = esNegocio ? '' : 'none';
  document.getElementById('grid').style.display = hayTarjetas() ? '' : 'none';
  document.getElementById('btnTodo').style.display = hayTarjetas() ? '' : 'none';
  if(!hayTarjetas()){
    document.getElementById('empty').style.display = 'none';
    document.getElementById('carpeta').textContent = carpetaMiosTexto;
    actualizarBarra();      // esconde la barra flotante de selección
    if(esCrear) cargarCrear(); else cargarNegocio();
    return;
  }

  document.getElementById('carpeta').textContent =
    v==='descargas' ? carpetaDescargasTexto : carpetaMiosTexto;
  if(v==='descargas' && !descargasCargadas){
    cargarDescargas();
  } else {
    render();
    // lo seleccionado que esta pestaña no enseña deja de contar: si no, la
    // barra ofrecería borrar tarjetas que no están a la vista
    purgarSeleccion(claveSel(), listaVista);
    actualizarBarra();
  }
}

async function cargar(){
  if(vista==='crear'){
    pedirVista();
  } else if(vista==='negocio'){
    negCargado = false;
    await cargarNegocio();
  } else if(esMio()){
    await cargarMios();
  } else {
    await cargarDescargas();
  }
}

/* ---------------- Pestaña Mi negocio ---------------- */
/* El cierre del mes: lo que vendiste y lo que gastaste fuera de la pieza.
   De ahí salen el margen, la utilidad y cuántas piezas hay que vender para
   cubrir los gastos. Cada mes se guarda aparte en .catalogo3d_negocio.json */
let negocio = {}, negMes = mesDeHoy(), negCargado = false, relojNeg = null;

function mesDeHoy(){
  const f = new Date();
  return f.getFullYear() + '-' + String(f.getMonth()+1).padStart(2, '0');
}
function mesVecino(m, paso){
  const p = m.split('-').map(Number);
  const f = new Date(p[0], p[1]-1+paso, 1);
  return f.getFullYear() + '-' + String(f.getMonth()+1).padStart(2, '0');
}
function nombreMes(m){
  const p = m.split('-').map(Number);
  return new Date(p[0], p[1]-1, 1)
    .toLocaleDateString('es-MX', {month:'long', year:'numeric'});
}
function mesDatos(m){
  const clave = m || negMes;
  if(!negocio[clave]) negocio[clave] = {gastos: [], ventas: []};
  return negocio[clave];
}

async function cargarNegocio(){
  if(!negCargado){
    try{
      const r = await fetch('/api/negocio');
      negocio = (await r.json()).meses || {};
      negCargado = true;
    }catch(e){ toast('✗ No pude cargar el resumen del mes'); return; }
  }
  document.getElementById('negMes').value = negMes;
  document.getElementById('negObjetivo').value = num(config.utilidad_objetivo);
  dibujarNegocio();
}
function elegirMes(v){
  if(/^[0-9]{4}-[0-9]{2}$/.test(v)){ negMes = v; dibujarNegocio(); }
}
function cambiarMes(paso){
  negMes = mesVecino(negMes, paso);
  document.getElementById('negMes').value = negMes;
  dibujarNegocio();
}

/* El mes que se guarda es el que se estaba editando, aunque para cuando
   toque escribir ya estés mirando otro. */
function guardarMes(){
  const mes = negMes, datos = mesDatos(mes);
  clearTimeout(relojNeg);
  relojNeg = setTimeout(async () => {
    try{
      const r = await fetch('/api/negocio_set', {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({mes, datos})});
      const res = await r.json();
      if(!res.ok) toast('✗ No pude guardar el mes');
    }catch(e){ toast('✗ Error de conexión'); }
  }, 500);
}

function margenVenta(v){ return num(v.unidades) * (num(v.retorno) - num(v.costo)); }

function opcionesDisenos(sel){
  return ['<option value="">— elige un diseño —</option>'].concat(
    disenosMios.map(d =>
      `<option value="${escapaAttr(d.archivo)}"${d.archivo===sel?' selected':''}>${escapa(d.nombre)}</option>`)
  ).join('');
}

function dibujarNegocio(){
  const m = mesDatos();
  document.getElementById('negEstado').textContent =
    nombreMes(negMes) + ' · ' + m.ventas.length + ' venta(s) y ' +
    m.gastos.length + ' gasto(s) anotados';

  document.getElementById('negVentas').innerHTML = m.ventas.map((v, k) => `
    <tr>
      <td><select onchange="ventaDiseno(${k}, this.value)">${opcionesDisenos(v.archivo)}</select></td>
      <td><input type="number" min="0" step="1" value="${v.unidades}"
                 oninput="ventaCampo(${k},'unidades',this.value)"></td>
      <td><input type="number" min="0" step="10" value="${v.retorno}"
                 oninput="ventaCampo(${k},'retorno',this.value)"></td>
      <td><input type="number" min="0" step="1" value="${v.costo}"
                 oninput="ventaCampo(${k},'costo',this.value)"></td>
      <td class="nums" id="negMargen-${k}">${fmtCosto(margenVenta(v))}</td>
      <td class="quita"><button class="btn del" title="Quitar venta"
                                onclick="quitarVenta(${k})">🗑</button></td>
    </tr>`).join('') ||
    '<tr><td colspan="6" class="vacio">Todavía no anotas ventas de este mes.</td></tr>';

  document.getElementById('negGastos').innerHTML = m.gastos.map((g, k) => `
    <tr>
      <td><input list="conceptos" value="${escapaAttr(g.concepto)}"
                 placeholder="Publicidad, luz, renta…"
                 oninput="gastoCampo(${k},'concepto',this.value)"></td>
      <td><select onchange="gastoCampo(${k},'tipo',this.value)">
            <option value="general"${g.tipo!=='publicidad'?' selected':''}>General</option>
            <option value="publicidad"${g.tipo==='publicidad'?' selected':''}>Publicidad</option>
          </select></td>
      <td><input type="number" min="0" step="10" value="${g.monto}"
                 oninput="gastoCampo(${k},'monto',this.value)"></td>
      <td class="quita"><button class="btn del" title="Quitar gasto"
                                onclick="quitarGasto(${k})">🗑</button></td>
    </tr>`).join('') ||
    '<tr><td colspan="4" class="vacio">Sin gastos anotados este mes.</td></tr>';

  pintarResumenMes();
}

/* Al elegir el diseño se copian su retorno y su costo de HOY. A partir de
   ahí son números del mes, no del catálogo: se quedan como estaban. */
function ventaDiseno(k, archivo){
  const v = mesDatos().ventas[k];
  const d = disenosMios.find(x => x.archivo === archivo);
  v.archivo = archivo;
  v.nombre = d ? d.nombre : 'Sin diseño';
  if(d){
    const c = cuentas(d);
    v.retorno = c.retorno != null ? Math.round(c.retorno*100)/100 : 0;
    v.costo   = c.total   != null ? Math.round(c.total*100)/100   : 0;
    v.publicado = d.ml_precio_venta > 0 ? d.ml_precio_venta : v.retorno;
  }
  dibujarNegocio();
  guardarMes();
}
function ventaCampo(k, campo, valor){
  const v = mesDatos().ventas[k];
  if(!v) return;
  v[campo] = num(valor);
  const celda = document.getElementById('negMargen-'+k);
  if(celda) celda.textContent = fmtCosto(margenVenta(v));
  pintarResumenMes();
  guardarMes();
}
function agregarVenta(){
  const d = disenosMios.find(x => tieneInfo(x)) || disenosMios[0];
  const c = d ? cuentas(d) : null;
  const retorno = c && c.retorno != null ? Math.round(c.retorno*100)/100 : 0;
  mesDatos().ventas.push({
    archivo: d ? d.archivo : '', nombre: d ? d.nombre : 'Sin diseño', unidades: 1,
    retorno: retorno,
    costo:   c && c.total != null ? Math.round(c.total*100)/100 : 0,
    publicado: (d && d.ml_precio_venta > 0) ? d.ml_precio_venta : retorno});
  dibujarNegocio();
  guardarMes();
}
function quitarVenta(k){ mesDatos().ventas.splice(k, 1); dibujarNegocio(); guardarMes(); }

function gastoCampo(k, campo, valor){
  const g = mesDatos().gastos[k];
  if(!g) return;
  g[campo] = (campo === 'concepto' || campo === 'tipo') ? valor : num(valor);
  pintarResumenMes();
  guardarMes();
}
function agregarGasto(){
  mesDatos().gastos.push({concepto: '', monto: 0, tipo: 'general'});
  dibujarNegocio();
  guardarMes();
}
function quitarGasto(k){ mesDatos().gastos.splice(k, 1); dibujarNegocio(); guardarMes(); }

/* La cuenta del mes. El margen bruto es lo que dejan las piezas; la
   utilidad es lo que queda ya con los gastos generales encima. */
function cuentasMes(m){
  const d = negocio[m] || {gastos: [], ventas: []};
  const piezas   = d.ventas.reduce((s,v) => s + num(v.unidades), 0);
  const ingresos = d.ventas.reduce((s,v) => s + num(v.unidades)*num(v.retorno), 0);
  const costo    = d.ventas.reduce((s,v) => s + num(v.unidades)*num(v.costo), 0);
  const gastos   = d.gastos.reduce((s,g) => s + num(g.monto), 0);
  // lo que pagaron los compradores: la base del ROAS
  const facturado = d.ventas.reduce((s,v) =>
    s + num(v.unidades) * (num(v.publicado) || num(v.retorno)), 0);
  let publicidad = 0, generales = 0;
  d.gastos.forEach(g => {
    if(g.tipo === 'publicidad') publicidad += num(g.monto);
    else generales += num(g.monto);
  });
  const bruto    = ingresos - costo;
  return {piezas, ingresos, costo, gastos, bruto, utilidad: bruto - gastos,
          facturado, publicidad, generales,
          gastosPorPieza: piezas ? generales/piezas : 0,
          margenUnit: piezas ? bruto/piezas : 0,
          ticket: piezas ? ingresos/piezas : 0,
          margenPct: ingresos ? bruto/ingresos*100 : 0,
          utilidadPct: ingresos ? (bruto-gastos)/ingresos*100 : 0};
}

function kpi(et, n, pie, clase){
  return `<div class="kpi ${clase||''}"><div class="et">${et}</div>` +
         `<div class="n">${n}</div>` +
         (pie ? `<div class="pie">${pie}</div>` : '') + `</div>`;
}

function pintarResumenMes(){
  const c = cuentasMes(negMes);
  const anterior = negocio[mesVecino(negMes, -1)] ? cuentasMes(mesVecino(negMes, -1)) : null;
  // cuántas piezas hay que vender para que los gastos del mes se paguen
  const equilibrio = c.margenUnit > 0 ? Math.ceil(c.gastos / c.margenUnit) : null;
  const faltan = equilibrio != null ? equilibrio - c.piezas : null;

  const pieUtilidad = anterior
    ? 'Mes anterior ' + fmtCosto(anterior.utilidad)
    : (c.ingresos ? Math.round(c.utilidadPct) + '% de lo que te retornaron' : '');

  const tarjetas = [
    kpi('Piezas vendidas', c.piezas,
        c.ticket ? 'Ticket promedio ' + fmtCosto(c.ticket) : ''),
    kpi('Me retornaron', fmtCosto(c.ingresos), 'Lo que te depositaron'),
    kpi('Costo de lo vendido', fmtCosto(c.costo), 'Material y paquetería'),
    kpi('Margen bruto', fmtCosto(c.bruto),
        c.ingresos ? Math.round(c.margenPct) + '% de lo que te retornaron' : ''),
    kpi('Gastos del mes', fmtCosto(c.gastos), 'Publicidad, luz, renta…'),
    kpi('Utilidad del mes', fmtCosto(c.utilidad), pieUtilidad,
        'fuerte ' + (c.utilidad >= 0 ? 'bien' : 'mal')),
    kpi('Punto de equilibrio',
        equilibrio != null ? equilibrio + ' pz' : '—',
        equilibrio == null ? 'Hace falta margen para calcularlo'
          : (faltan > 0 ? 'Te faltan ' + faltan + ' para cubrir los gastos'
                        : 'Cubierto, van ' + (c.piezas - equilibrio) + ' de más')),
  ].join('');

  document.getElementById('negResumen').innerHTML =
    `<div class="kpis">${tarjetas}</div>` + rankingHTML();
  pintarPrecios();
}

/* Qué producto deja más dinero este mes, en barras comparables entre sí. */
function rankingHTML(){
  const m = mesDatos();
  if(!m.ventas.length) return '';
  const por = {};
  m.ventas.forEach(v => {
    const k = v.nombre || 'Sin diseño';
    if(!por[k]) por[k] = {piezas: 0, margen: 0};
    por[k].piezas += num(v.unidades);
    por[k].margen += margenVenta(v);
  });
  const filas = Object.keys(por)
    .map(k => ({nombre: k, piezas: por[k].piezas, margen: por[k].margen}))
    .sort((a, b) => b.margen - a.margen);
  const tope = Math.max.apply(null, filas.map(f => Math.abs(f.margen))) || 1;
  return `<div class="ranking"><h3>Qué te deja más este mes</h3>` + filas.map(f => `
    <div class="rfila">
      <span class="nom" title="${escapaAttr(f.nombre)}">${escapa(f.nombre)}</span>
      <span class="barrita"><i class="${f.margen<0?'mal':''}"
            style="width:${Math.max(2, Math.abs(f.margen)/tope*100)}%"></i></span>
      <span class="val">${fmtCosto(f.margen)} · ${f.piezas} pz</span>
    </div>`).join('') + `</div>`;
}

/* ---------------- Precios y publicidad ---------------- */
/* Dos preguntas que el catálogo ya puede responder solo:
   1) si un producto está caro o barato — contra la competencia si la
      cargaste, y si no, cruzando su margen con lo que rota;
   2) cuánto se puede pagar de publicidad por una venta sin perder dinero,
      que es lo mismo que el ROAS mínimo. */

function cambioObjetivo(v){
  config.utilidad_objetivo = num(v);
  guardarConfig();
  pintarPrecios();
}

function mediana(xs){
  if(!xs.length) return 0;
  const a = xs.slice().sort((p, q) => p - q), m = Math.floor(a.length/2);
  return a.length % 2 ? a[m] : (a[m-1] + a[m])/2;
}

/* La pista de precio. Con precio de la competencia es una medición; sin
   él es una inferencia a partir de tu propio catálogo, y se dice así. */
function pistaPrecio(f, medMargen, medPiezas, hayVentas){
  if(f.margen <= 0)
    return {txt: 'pierdes dinero en cada venta', clase: 'mal'};
  if(f.competencia > 0){
    const dif = (f.publicado - f.competencia) / f.competencia * 100;
    if(dif > 15)  return {txt: 'caro: ' + Math.round(dif) + '% sobre la competencia', clase: 'ojo'};
    if(dif < -15) return {txt: 'barato: ' + Math.round(-dif) + '% bajo la competencia', clase: 'ojo'};
    return {txt: 'en precio de mercado', clase: 'bien'};
  }
  if(!hayVentas)
    return {txt: 'sin ventas este mes: aún no se puede juzgar', clase: ''};
  if(!f.piezas && f.margenPct > medMargen + 8)
    return {txt: 'quizá caro: deja bien pero no rota', clase: 'ojo'};
  if(f.piezas > medPiezas && f.margenPct < medMargen - 8)
    return {txt: 'quizá barato: rota mucho y deja poco', clase: 'ojo'};
  if(f.piezas > medPiezas && f.margenPct >= medMargen)
    return {txt: 'tu producto estrella', clase: 'bien'};
  return {txt: 'en equilibrio', clase: ''};
}

function filasPrecios(){
  const c = cuentasMes(negMes);
  const objetivo = num(config.utilidad_objetivo);
  const vendidas = {};
  mesDatos().ventas.forEach(v => {
    vendidas[v.archivo] = (vendidas[v.archivo] || 0) + num(v.unidades);
  });
  return disenosMios.map(d => {
    const q = cuentas(d);
    if(q.total == null || q.retorno == null) return null;
    const margen = q.retorno - q.total;
    // el comprador paga el precio publicado; si no lo tienes vinculado, lo
    // más cercano es lo que te depositan
    const publicado = d.ml_precio_venta > 0 ? d.ml_precio_venta : q.retorno;
    // lo máximo que puedes pagar por traer esa venta: primero solo la pieza,
    // después descontando los gastos generales y la utilidad que pediste
    const cpaObjetivo = margen - c.gastosPorPieza - objetivo;
    return {archivo: d.archivo, nombre: d.nombre, competencia: num(d.competencia),
            costo: q.total, retorno: q.retorno, margen, publicado,
            margenPct: q.retorno ? margen/q.retorno*100 : 0,
            piezas: vendidas[d.archivo] || 0,
            cpaObjetivo,
            roasEq:  margen > 0      ? publicado/margen      : null,
            roasObj: cpaObjetivo > 0 ? publicado/cpaObjetivo : null};
  }).filter(Boolean).sort((a, b) => b.margenPct - a.margenPct);
}

function fmtRoas(r){ return r == null ? '—' : r.toFixed(2) + 'x'; }

function pintarPrecios(){
  const caja = document.getElementById('negPrecios');
  if(!caja) return;
  const c = cuentasMes(negMes);
  const filas = filasPrecios();

  // ROAS del mes: lo que facturaste por cada peso de anuncio, contra lo
  // máximo que podías gastar sin comerte la utilidad
  const tope = c.bruto - c.generales;
  const roasReal = c.publicidad > 0 ? c.facturado/c.publicidad : null;
  const roasMin  = tope > 0 ? c.facturado/tope : null;
  const vaBien = roasReal != null && roasMin != null && roasReal >= roasMin;
  const kpis = [
    kpi('Publicidad del mes', fmtCosto(c.publicidad),
        c.publicidad ? '' : 'Marca un gasto como «Publicidad»'),
    kpi('ROAS real', fmtRoas(roasReal),
        roasReal != null ? 'Facturaste ' + fmtCosto(c.facturado) : 'Sin gasto en anuncios'),
    kpi('ROAS mínimo del mes', fmtRoas(roasMin),
        tope > 0 ? 'Puedes gastar hasta ' + fmtCosto(tope) : 'El margen no cubre los gastos',
        roasReal != null && roasMin != null ? (vaBien ? 'bien' : 'mal') : ''),
  ].join('');

  if(!filas.length){
    caja.innerHTML = `<div class="roas">${kpis}</div>` +
      `<p class="pista">Carga el peso y el retorno de tus diseños y aquí sale,
        uno por uno, si están caros o baratos y cuánto puedes pagar de
        publicidad por cada venta.</p>`;
    return;
  }

  const hayVentas = c.piezas > 0;
  const medMargen = mediana(filas.map(f => f.margenPct));
  const medPiezas = mediana(filas.map(f => f.piezas));

  const cuerpo = filas.map(f => {
    const p = pistaPrecio(f, medMargen, medPiezas, hayVentas);
    // lo que no rotó se apaga, salvo que precisamente eso sea la noticia
    return `<tr class="${(!f.piezas && !p.clase) ? 'flojo' : ''}">
      <td class="nom" title="${escapaAttr(f.nombre)}">${escapa(f.nombre)}</td>
      <td>${fmtCosto(f.costo)}</td>
      <td>${fmtCosto(f.retorno)}</td>
      <td>${fmtCosto(f.margen)} · ${Math.round(f.margenPct)}%</td>
      <td>${f.piezas || '—'}</td>
      <td>${f.cpaObjetivo > 0 ? fmtCosto(f.cpaObjetivo) : '—'}</td>
      <td>${fmtRoas(f.roasEq)}</td>
      <td>${fmtRoas(f.roasObj)}</td>
      <td class="dic ${p.clase}"><b>${p.txt}</b></td>
    </tr>`;
  }).join('');

  caja.innerHTML = `<div class="roas">${kpis}</div>
    <table class="precios">
      <thead><tr>
        <th>Diseño</th><th>Me cuesta</th><th>Me retorna</th><th>Margen</th>
        <th>Vendidas</th><th>Pago máx. por venta</th>
        <th>ROAS equilibrio</th><th>ROAS objetivo</th><th>Pista de precio</th>
      </tr></thead>
      <tbody>${cuerpo}</tbody>
    </table>`;
}

/* ---------------- Pestaña Crear ---------------- */
let genSpecs = [], genRecetas = [], crValores = {}, crClave = null;
let crTimer = null, crSerie = 0, crCargado = false;
/* Vista del render. Mientras el usuario no la toque, manda la que el servidor
   considera buena para ese diseño; en cuanto mueve un deslizador, manda él. */
let crVista = {giro: 32, elevacion: 31}, crVistaManual = false;

function sincronizarVista(){
  document.getElementById('crGiro').value = crVista.giro;
  document.getElementById('crElev').value = crVista.elevacion;
}

function vistaAuto(){
  crVistaManual = false;
  pedirVista();
}

async function cargarCrear(){
  if(crCargado) return;
  let d;
  try { d = await (await fetch('/api/generadores')).json(); }
  catch(e){ toast('✗ No pude cargar los generadores'); return; }
  if(!d.disponible){
    document.getElementById('crearNo').style.display = 'block';
    document.getElementById('crearSi').style.display = 'none';
    return;
  }
  genSpecs = d.parametros; genRecetas = d.disenos; crCargado = true;
  const sel = document.getElementById('crDiseno');
  sel.innerHTML = genRecetas.map(r =>
    `<option value="${r.clave}">${r.nombre}</option>`).join('');
  sel.onchange = () => elegirReceta(sel.value);
  elegirReceta(genRecetas[0].clave);
}

function elegirReceta(clave){
  crClave = clave;
  const r = genRecetas.find(x => x.clave === clave);
  crValores = Object.assign({}, r.valores);
  document.getElementById('crDesc').textContent = r.descripcion;
  document.getElementById('crNombre').value = '';
  dibujarControles();
  pedirVista();
}

/* Un parámetro con 'depende' sólo se muestra si la opción elegida está en su
   lista. Las claves de contorno, acabado, perfil y cara no se repiten entre
   sí, así que basta con mirar esos cuatro. */
function visibleSpec(s){
  /* El trazo no es un control que se mueva: es la silueta que trajo una
     imagen. Se enseña como miniatura, nunca como deslizador. */
  if(s.tipo === 'trazo') return false;
  if(!s.depende) return true;
  return ['contorno','acabado','perfil','cuello','borde','cara'].some(k => s.depende.includes(crValores[k]));
}

function fmtVal(v, u){
  const n = typeof v === 'number' ? v : parseFloat(v);
  const t = Number.isInteger(n) ? n : parseFloat(n.toFixed(2));
  return t + (u ? ' ' + u : '');
}

/* «Trazado de imagen» sólo tiene sentido con una silueta cargada: sin ella el
   motor devuelve un redondo, y ofrecer una planta que no hace nada es peor que
   no ofrecerla. */
function opcionUsable(s, o){
  if(s.clave === 'contorno' && o.clave === 'trazado') return !!crValores.trazo;
  return true;
}

function campoHTML(s){
  if(s.tipo === 'opcion'){
    const ops = s.opciones.filter(o => opcionUsable(s, o)).map(o =>
      `<option value="${o.clave}"${o.clave===crValores[s.clave]?' selected':''}>${o.etiqueta}</option>`).join('');
    /* El muestrario se abre desde donde se toma la decisión, no desde una
       barra de herramientas: el botón vive pegado al selector de planta. */
    const extra = s.clave === 'contorno'
      ? `<button class="btn muestra" onclick="abrirMuestrario()">▦ Verlas todas</button>` : '';
    return `<div class="par"><div class="fila"><label title="${s.ayuda||''}">${s.etiqueta}</label></div>
      <select data-clave="${s.clave}">${ops}</select>${extra}</div>`;
  }
  const v = crValores[s.clave];
  return `<div class="par">
    <div class="fila"><label title="${s.ayuda||''}">${s.etiqueta}</label>
      <span class="val" id="v-${s.clave}">${fmtVal(v, s.unidad)}</span></div>
    <input type="range" data-clave="${s.clave}" data-unidad="${s.unidad}"
           min="${s.min}" max="${s.max}" step="${s.paso}" value="${v}"></div>`;
}

function dibujarControles(){
  const grupos = [];
  genSpecs.forEach(s => {
    let g = grupos.find(x => x.nombre === s.grupo);
    if(!g){ g = {nombre: s.grupo, specs: []}; grupos.push(g); }
    g.specs.push(s);
  });
  const cont = document.getElementById('crGrupos');
  cont.innerHTML = grupos.map(g => {
    const campos = g.specs.filter(visibleSpec).map(campoHTML).join('');
    return campos ? `<div class="grupo"><h3>${g.nombre}</h3>${campos}</div>` : '';
  }).join('');

  cont.querySelectorAll('[data-clave]').forEach(el => {
    el.addEventListener('input', e => {
      const c = e.target.dataset.clave;
      const esRango = e.target.type === 'range';
      crValores[c] = esRango ? parseFloat(e.target.value) : e.target.value;
      const eco = document.getElementById('v-' + c);
      if(eco) eco.textContent = fmtVal(crValores[c], e.target.dataset.unidad);
      // Cambiar de forma/acabado/perfil muestra u oculta otros controles
      if(!esRango) dibujarControles();
      pedirVista();
    });
  });
}

/* ---------------- Muestrario de plantas ----------------
   La misma pieza repetida en todas las plantas. Es la respuesta a una
   pregunta que el selector no podía contestar: «¿cómo se ve mi
   portacubiertos en riñón?». Leer «Riñón» en una lista no lo dice.

   Las miniaturas se piden de una en una y la rejilla se va llenando, en vez
   de esperar a las catorce: la primera aparece en un cuarto de segundo y
   para cuando el ojo llegó abajo ya están todas. Se guardan mientras nada
   más cambie, así que volver a abrirlo es instantáneo. */
let muestraCache = {}, muestraFirma = '', muestraTanda = 0;

/* Todo lo que no es la planta. Si esto no cambió, las miniaturas de antes
   siguen valiendo; si cambió el alto, el acabado o el redondeo, no. */
function firmaMuestra(){
  const v = Object.assign({}, crValores);
  delete v.contorno;
  return JSON.stringify(Object.keys(v).sort().map(k => [k, v[k]]));
}

function plantasDelSelector(){
  const s = genSpecs.find(x => x.clave === 'contorno');
  return s ? s.opciones.filter(o => opcionUsable(s, o)) : [];
}

async function abrirMuestrario(){
  const firma = firmaMuestra();
  if(firma !== muestraFirma){ muestraCache = {}; muestraFirma = firma; }
  document.getElementById('modalFormas').classList.add('show');
  const plantas = plantasDelSelector();
  const tanda = ++muestraTanda;
  pintarMuestrario(plantas);
  for(const o of plantas){
    if(muestraTanda !== tanda) return;      // se cerró, o se volvió a abrir
    if(muestraCache[o.clave]) continue;
    try{
      const r = await fetch('/api/muestra', {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({contorno: o.clave, valores: crValores})});
      muestraCache[o.clave] = await r.json();
    }catch(e){
      muestraCache[o.clave] = {ok: false, mensaje: 'no se pudo calcular'};
    }
    if(muestraTanda !== tanda) return;
    pintarMuestrario(plantas);
  }
}

function cerrarMuestrario(){
  muestraTanda++;                            // corta la tanda en curso
  document.getElementById('modalFormas').classList.remove('show');
}

function pintarMuestrario(plantas){
  const hechas = plantas.filter(o => muestraCache[o.clave]).length;
  document.getElementById('formasHint').textContent = hechas < plantas.length
    ? `Calculando ${hechas} de ${plantas.length}…`
    : `La misma pieza en ${plantas.length} plantas: mismas medidas, mismo ` +
      `acabado, mismo todo. El peso es aproximado — la miniatura se calcula ` +
      `en grueso. Toca una para ponérsela.`;
  document.getElementById('formasRejilla').innerHTML = plantas.map(o => {
    const d = muestraCache[o.clave];
    const puesta = o.clave === crValores.contorno ? ' puesta' : '';
    let lam, pie, ayuda = '';
    if(!d){
      lam = '<span>Calculando…</span>';
      pie = '<span class="g">·</span>';
    }else if(!d.ok || !d.cerrada){
      lam = `<span>✗ ${escapa(d.mensaje || 'la malla salió abierta')}</span>`;
      pie = '<span class="g warn">no sale</span>';
    }else{
      const avisos = d.avisos || [];
      lam = `<img src="${d.png}" alt="">`;
      pie = `<span class="g${avisos.length ? ' warn' : ''}">≈ ${d.gramos} g` +
            `${avisos.length ? ' · ⚠' : ''}</span>`;
      ayuda = avisos.join(' · ');
    }
    return `<button class="forma${puesta}" onclick="ponerPlanta('${o.clave}')"` +
           ` title="${escapaAttr(ayuda)}"><div class="lam">${lam}</div>` +
           `<b>${escapa(o.etiqueta)}</b>${pie}</button>`;
  }).join('');
}

function ponerPlanta(clave){
  const o = plantasDelSelector().find(x => x.clave === clave);
  crValores.contorno = clave;
  cerrarMuestrario();
  dibujarControles();      // cada planta trae sus propios controles
  pedirVista();
  toast('✓ ' + (o ? o.etiqueta : clave));
}

function pintarDatos(d){
  if(!d) return;
  const precio = precioKg();
  const chips = [`<span class="chip">${d.ancho} × ${d.fondo} × ${d.alto} mm</span>`,
                 `<span class="chip peso">${d.gramos} g</span>`];
  if(precio){
    const envio = totalPaquete(paqueteActivo());
    const total = d.gramos/1000*precio + envio;
    chips.push(`<span class="chip costo" title="Material ${fmtCosto(d.gramos/1000*precio)} + paquetería ${fmtCosto(envio)}">${fmtCosto(total)} me cuesta</span>`);
  }
  if(d.ranuras > 1) chips.push(`<span class="chip">${d.ranuras} ranuras de ${d.ancho_ranura} mm</span>`);
  if(d.agujeros) chips.push(`<span class="chip">${d.agujeros} agujeros</span>`);
  if(d.n_piezas > 1) chips.push(`<span class="chip folder">${d.n_piezas} piezas</span>`);
  if(d.estrias) chips.push(`<span class="chip">${d.estrias} estrías</span>`);
  if(!d.cerrada) chips.push(`<span class="chip warn">malla abierta</span>`);
  document.getElementById('crDatos').innerHTML = chips.join('');
  document.getElementById('crAvisos').innerHTML =
    (d.avisos || []).map(a => `<div class="aviso">⚠ ${a}</div>`).join('');
}

function pedirVista(){
  if(!crClave) return;
  clearTimeout(crTimer);
  document.getElementById('crLienzo').classList.add('trabajando');
  crTimer = setTimeout(async () => {
    const serie = ++crSerie;
    try{
      const r = await fetch('/api/vista', {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({clave: crClave, valores: crValores,
                              vista: crVistaManual ? crVista : null})});
      const d = await r.json();
      if(serie !== crSerie) return;      // llegó tarde: ya hay otra en curso
      if(d.vista && !crVistaManual){ crVista = d.vista; sincronizarVista(); }
      if(d.png) document.getElementById('crImg').src = d.png;
      if(d.datos) pintarDatos(d.datos);
      if(d.ok === false) toast('✗ ' + (d.mensaje || 'No se pudo calcular'));
    }catch(e){
      if(serie === crSerie) toast('✗ Error al calcular la vista previa');
    }finally{
      if(serie === crSerie)
        document.getElementById('crLienzo').classList.remove('trabajando');
    }
  }, 280);
}

async function guardarDiseno(){
  const btn = document.getElementById('crGuardar');
  btn.disabled = true;
  btn.textContent = 'Generando…';
  try{
    const r = await fetch('/api/crear', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({clave: crClave, valores: crValores,
                            vista: crVistaManual ? crVista : null,
                            nombre: document.getElementById('crNombre').value})});
    const res = await r.json();
    toast((res.ok ? '✓ ' : '✗ ') + res.mensaje);
    if(res.ok) await cargarMios();
  }catch(e){ toast('✗ Error de conexión'); }
  finally{
    btn.disabled = false;
    btn.textContent = 'Guardar en mi carpeta';
  }
}

document.getElementById('precio').addEventListener('input', () => {
  config.precio_kg = precioKg() || null;
  guardarConfig();
  if(vista === 'crear') pedirVista(); else render();
});
document.getElementById('paquete').addEventListener('change', e => {
  config.paquete_activo = parseInt(e.target.value, 10);
  guardarConfig();
  if(vista === 'crear') pedirVista(); else render();
});
document.addEventListener('keydown', e => {
  if(e.key === 'Escape'){ cerrarPaqueteria(); cerrarMuestrario(); }
});

['crGiro','crElev'].forEach(id => {
  document.getElementById(id).addEventListener('input', e => {
    crVistaManual = true;
    crVista = {giro: parseFloat(document.getElementById('crGiro').value),
               elevacion: parseFloat(document.getElementById('crElev').value)};
    pedirVista();
  });
});
cargarMios();
</script>
</body>
</html>""".replace("__MONEDA__", MONEDA).replace("__APP_NOMBRE__", nombre_app())


# ----------------------------------------------------------
#  SERVIDOR
# ----------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    carpeta = None            # se asigna al arrancar
    carpeta_descargas = None  # ídem

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            body = pagina_html(self.carpeta).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/designs":
            disenos = escanear(self.carpeta)
            precios = [d["precio_kg"] for d in disenos if d["precio_kg"]]
            sugerido = round(precios[0]) if precios else PRECIO_KG_DEFECTO
            self._json({
                "carpeta": str(self.carpeta),
                "precio_sugerido": sugerido,
                "config": cargar_config(self.carpeta),
                "disenos": disenos,
            })
        elif self.path == "/api/negocio":
            self._json({"meses": cargar_negocio(self.carpeta)})
        elif self.path == "/api/generadores":
            self._json(catalogo_generadores())
        elif self.path == "/api/downloads":
            disenos = escanear(self.carpeta_descargas) if self.carpeta_descargas.exists() else []
            self._json({
                "carpeta": str(self.carpeta_descargas),
                "disenos": disenos,
            })
        else:
            self._json({"error": "no encontrado"}, 404)

    def do_POST(self):
        if self.path not in ("/api/rename", "/api/delete", "/api/mover", "/api/abrir",
                             "/api/mover_pruebas",
                             "/api/delete_multi", "/api/mover_multi",
                             "/api/vista", "/api/crear", "/api/muestra",
                             "/api/datos_set",
                             "/api/config_set", "/api/negocio_set"):
            self._json({"ok": False, "mensaje": "ruta desconocida"}, 404)
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n))
        except Exception:
            self._json({"ok": False, "mensaje": "petición inválida"}, 400)
            return

        if self.path in ("/api/vista", "/api/crear", "/api/muestra"):
            if not HAY_GENERADORES:
                self._json({"ok": False, "mensaje": "Falta la carpeta generadores/."})
                return
            try:
                if self.path == "/api/vista":
                    self._json(vista_previa(data))
                elif self.path == "/api/muestra":
                    self._json(muestra_planta(data))
                else:
                    ok, msg, nombre = generar_diseno(self.carpeta, data)
                    self._json({"ok": ok, "mensaje": msg, "nombre": nombre})
            except Exception as e:
                self._json({"ok": False, "mensaje": "Error del generador: %s" % e})
            return

        if self.path == "/api/rename":
            viejo = data.get("viejo", "")
            ok, msg, final = renombrar(self.carpeta, viejo, data.get("nuevo", ""))
            if ok:
                migrar_ml(self.carpeta, viejo, final)
            self._json({"ok": ok, "mensaje": msg, "nombre_final": final})
        elif self.path == "/api/mover_pruebas":
            viejo = data.get("archivo", "")
            ok, msg, final = mover_a_pruebas(self.carpeta, viejo)
            if ok:
                migrar_ml(self.carpeta, viejo, final)
            self._json({"ok": ok, "mensaje": msg, "nombre_final": final})
        elif self.path == "/api/delete":
            base = (self.carpeta_descargas
                    if data.get("origen") == "descargas" else self.carpeta)
            archivo = data.get("archivo", "")
            ok, msg = eliminar(base, archivo)
            if ok and data.get("origen") != "descargas":
                migrar_ml(self.carpeta, archivo, "")
            self._json({"ok": ok, "mensaje": msg})
        elif self.path == "/api/delete_multi":
            base = (self.carpeta_descargas
                    if data.get("origen") == "descargas" else self.carpeta)
            resultados = eliminar_varios(base, _lista_archivos(data))
            if data.get("origen") != "descargas":
                for r in resultados:
                    if r["ok"]:
                        migrar_ml(self.carpeta, r["archivo"], "")
            self._json({"ok": True, "resultados": resultados})
        elif self.path == "/api/datos_set":
            archivo = data.get("archivo", "")
            if not archivo:
                self._json({"ok": False, "mensaje": "Falta el archivo"})
                return
            ok, entrada = set_datos(self.carpeta, archivo, data.get("campos") or {})
            self._json({"ok": ok, "mensaje": "Guardado" if ok else "No se pudo guardar",
                       "datos": entrada})
        elif self.path == "/api/negocio_set":
            ok, mes = guardar_mes(self.carpeta, data.get("mes", ""),
                                  data.get("datos") or {})
            self._json({"ok": ok, "mensaje": "Guardado" if ok else "No se pudo guardar",
                        "datos": mes})
        elif self.path == "/api/config_set":
            ok, cfg = guardar_config(self.carpeta, data.get("config") or {})
            self._json({"ok": ok, "mensaje": "Guardado" if ok else "No se pudo guardar",
                       "config": cfg})
        elif self.path == "/api/mover_multi":
            self._json({"ok": True,
                        "resultados": mover_varios(self.carpeta_descargas, self.carpeta,
                                                   _lista_archivos(data))})
        elif self.path == "/api/abrir":
            base = (self.carpeta_descargas
                    if data.get("origen") == "descargas" else self.carpeta)
            ok, msg = abrir_en_bambu(base, data.get("archivo", ""))
            self._json({"ok": ok, "mensaje": msg})
        else:  # /api/mover
            ok, msg, final = mover_desde_descargas(self.carpeta_descargas, self.carpeta,
                                                    data.get("archivo", ""))
            self._json({"ok": ok, "mensaje": msg, "nombre_final": final})

    def log_message(self, *a):
        pass  # silenciar el log de cada request


def abrir_servidor():
    """Levanta el servidor en PUERTO; si está ocupado, prueba los siguientes.

    Lo normal es que esté ocupado porque quedó otra galería corriendo de
    antes. En vez de reventar con un traceback, avisa y se corre de puerto.
    """
    for puerto in range(PUERTO, PUERTO + 20):
        try:
            servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Handler)
        except OSError as e:
            if e.errno != errno.EADDRINUSE:
                raise
            if puerto == PUERTO:
                print(f"⚠  El puerto {PUERTO} ya está ocupado "
                      "(¿dejaste otra galería abierta?).")
                print("   Para cerrar la anterior:  "
                      f"kill $(lsof -ti tcp:{PUERTO})")
            continue
        if puerto != PUERTO:
            print(f"   Uso el puerto {puerto} en su lugar.\n")
        return servidor, puerto
    print(f"\n⚠  No encontré un puerto libre entre {PUERTO} y {PUERTO + 19}.")
    sys.exit(1)


def main():
    carpeta = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else CARPETA_DEFECTO
    if not carpeta.exists():
        print(f"⚠  No existe la carpeta:\n   {carpeta}\n")
        print("   Pásala como argumento:")
        print('   python3 catalogo3d.py "/ruta/a/tu/carpeta"')
        sys.exit(1)

    Handler.carpeta = carpeta
    Handler.carpeta_descargas = CARPETA_DESCARGAS
    n = len(list(carpeta.glob("*.3mf")))
    servidor, puerto = abrir_servidor()
    url = f"http://127.0.0.1:{puerto}/"

    print("=" * 52)
    print("  Catálogo 3D en marcha")
    print("=" * 52)
    print(f"  Carpeta : {carpeta}")
    print(f"  Archivos: {n} .3mf")
    print(f"  Abre    : {url}")
    print("  (Ctrl+C para detener)")
    print("=" * 52)

    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Detenido. ¡Hasta luego!")
        servidor.shutdown()


if __name__ == "__main__":
    main()