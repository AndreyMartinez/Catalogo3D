#!/usr/bin/env python3
"""Lo que Amazon pide para cada tipo de producto, leído del Product Type
Definitions API.

El esquema (un JSON Schema de ~300 KB por tipo) se guarda en
~/.catalogo3d/amazon/esquemas/<TIPO>.json y solo se vuelve a bajar cuando
Amazon publica otra versión del tipo. La consulta de versión se hace una vez
por tipo y por corrida.
"""
import base64
import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sp_api  # noqa: E402

RUTA_DEF = "/definitions/2020-09-01/productTypes"
CARPETA = sp_api.CARPETA / "amazon" / "esquemas"

# Tipo → definición ya consultada en esta corrida.
_vistos = {}


def _guardar_privado(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # esquemas/ y amazon/: solo el usuario.
    for carpeta in (ruta.parent, ruta.parent.parent):
        os.chmod(carpeta, 0o700)
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    os.chmod(temporal, 0o600)
    temporal.replace(ruta)


def buscar_tipos(palabras):
    """Tipos de producto de Amazon México que corresponden a unas palabras.
    Devuelve [(nombre, nombre_visible)]."""
    r = sp_api.pedir("GET", RUTA_DEF, {
        "keywords": palabras if isinstance(palabras, str) else ",".join(palabras),
        "marketplaceIds": [sp_api.MARKETPLACE],
        "locale": sp_api.LOCALE,
        "searchLocale": sp_api.LOCALE,
    })
    return [(t["name"], t.get("displayName") or t["name"])
            for t in r.get("productTypes") or []]


def _definicion(tipo):
    if tipo not in _vistos:
        _vistos[tipo] = sp_api.pedir("GET", f"{RUTA_DEF}/{tipo}", {
            "marketplaceIds": [sp_api.MARKETPLACE],
            "sellerId": sp_api.seller_id(),
            "requirements": "LISTING",
            "locale": sp_api.LOCALE,
        })
    return _vistos[tipo]


def _bajar(enlace, checksum):
    """Baja el esquema del enlace firmado (sin token: ya viene autorizado)
    y comprueba el MD5 que manda Amazon."""
    try:
        with sp_api._abrir(enlace, timeout=120) as r:
            crudo = r.read()
    except urllib.error.URLError as e:
        raise sp_api.ErrorSP(f"No se pudo bajar el esquema: {getattr(e, 'reason', e)}") from None
    if checksum:
        md5 = base64.b64encode(hashlib.md5(crudo).digest()).decode()
        if md5 != checksum:
            raise sp_api.ErrorSP("El esquema bajado no coincide con su checksum; "
                                 "vuelve a intentar.")
    return json.loads(crudo)


def esquema(tipo):
    """Esquema del tipo para Amazon México, en español. Devuelve el dict de
    caché: {tipo, nombre, version, bajado, grupos, esquema}."""
    ruta = CARPETA / f"{tipo}.json"
    definicion = _definicion(tipo)
    version = (definicion.get("productTypeVersion") or {}).get("version")
    if ruta.exists():
        try:
            cache = json.loads(ruta.read_text(encoding="utf-8"))
        except ValueError:
            cache = {}
        if version and cache.get("version") == version:
            return cache
    liga = definicion["schema"]
    cache = {
        "tipo": tipo,
        "nombre": definicion.get("displayName") or tipo,
        "version": version,
        "bajado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "grupos": {g: v.get("propertyNames", [])
                   for g, v in (definicion.get("propertyGroups") or {}).items()},
        "esquema": _bajar(liga["link"]["resource"], liga.get("checksum")),
    }
    _guardar_privado(ruta, cache)
    return cache


def obligatorios(cache):
    """Los atributos que el esquema exige siempre (los condicionales los
    revisa Amazon al validar)."""
    return list(cache["esquema"].get("required") or [])


# ------------------------------------------------------- revisión local

def _sin_acentos(texto):
    descompuesto = unicodedata.normalize("NFD", str(texto).lower())
    return " ".join("".join(c for c in descompuesto
                            if unicodedata.category(c) != "Mn").split())


def opciones(cache, atributo):
    """Lista de valores del atributo: (valores, nombres, cerrada). 'cerrada'
    es un enum (solo vale lo de la lista); si no, es una lista sugerida
    (anyOf con texto libre). Sin lista: ([], [], False)."""
    valor = _valor(_propiedad(cache, atributo))
    if "enum" in valor:
        return valor["enum"], valor.get("enumNames") or valor["enum"], True
    for opcion in valor.get("anyOf") or []:
        if "enum" in opcion:
            return opcion["enum"], opcion.get("enumNames") or opcion["enum"], False
    return [], [], False


def valor_mas_cercano(texto, valores, nombres=None):
    """El valor de la lista que corresponde a un dato de ML. Primero igualdad
    (con el valor o con su nombre visible), luego el texto como palabra
    completa dentro del nombre. Si no hay uno solo, None: el campo queda
    «por revisar»."""
    if texto is None or not valores:
        return None
    nombres = nombres or valores
    buscado = _sin_acentos(texto)
    if not buscado:
        return None
    pares = list(zip(valores, nombres))
    iguales = [v for v, n in pares
               if buscado in (_sin_acentos(v), _sin_acentos(n))]
    if len(set(map(str, iguales))) == 1:
        return iguales[0]
    if iguales:
        return None
    patron = re.compile(r"\b" + re.escape(buscado) + r"\b")
    contienen = [v for v, n in pares if patron.search(_sin_acentos(n))]
    return contienen[0] if len(contienen) == 1 else None


def atributo_exencion(cache):
    """Nombre del atributo con el que se declara que el producto no tiene
    GTIN (supplier_declared_has_product_identifier_exemption en CADDY)."""
    for nombre in cache["esquema"].get("properties") or {}:
        if "product_identifier_exemption" in nombre:
            return nombre
    return None


def _propiedad(cache, atributo):
    return (cache["esquema"].get("properties") or {}).get(atributo) or {}


def _valor(propiedad):
    return ((propiedad.get("items") or {}).get("properties") or {}).get("value") or {}


def _hallazgo(campo, tipo, detalle):
    return {"campo": campo, "tipo": tipo, "detalle": detalle}


def revisar(atributos, cache):
    """Revisa los atributos ya en forma de Amazon (los del payload) contra el
    esquema, sin red. Devuelve [{campo, tipo: 'error'|'aviso', detalle}].
    Las reglas condicionales (allOf/if/then) no se reimplementan: esas las
    reporta Amazon en la vista previa."""
    esq = cache["esquema"]
    props = esq.get("properties") or {}
    hallazgos = []

    for campo in esq.get("required") or []:
        if not atributos.get(campo):
            hallazgos.append(_hallazgo(campo, "error", "obligatorio y sin valor"))

    for campo, lista in atributos.items():
        prop = props.get(campo)
        if prop is None:
            tipo = "error" if esq.get("additionalProperties") is False else "aviso"
            hallazgos.append(_hallazgo(campo, tipo,
                                       f"el tipo {cache.get('tipo', '')} no tiene este atributo"))
            continue
        if not isinstance(lista, list):
            hallazgos.append(_hallazgo(campo, "error", "debe ser una lista de valores"))
            continue
        if prop.get("maxItems") and len(lista) > prop["maxItems"]:
            hallazgos.append(_hallazgo(campo, "error",
                                       f"{len(lista)} valores; el máximo es {prop['maxItems']}"))
        requeridos = (prop.get("items") or {}).get("required") or []
        regla = _valor(prop)
        valores, nombres, cerrada = opciones(cache, campo)
        for i, entrada in enumerate(lista, 1):
            donde = f"{campo}[{i}]" if len(lista) > 1 else campo
            if not isinstance(entrada, dict):
                hallazgos.append(_hallazgo(donde, "error", "cada valor debe ser un objeto"))
                continue
            faltan = [r for r in requeridos if r not in entrada]
            if faltan:
                hallazgos.append(_hallazgo(donde, "error", f"le falta {', '.join(faltan)}"))
            if "value" not in entrada:
                continue
            valor = entrada["value"]
            if isinstance(valor, str):
                largo = len(valor)
                if regla.get("maxLength") is not None and largo > regla["maxLength"]:
                    hallazgos.append(_hallazgo(donde, "error",
                                               f"{largo} caracteres; el máximo es {regla['maxLength']}"))
                if regla.get("minLength") and largo < regla["minLength"]:
                    hallazgos.append(_hallazgo(donde, "error", "vacío"))
                bytes_ = len(valor.encode("utf-8"))
                tope = regla.get("maxUtf8ByteLength")
                if tope is not None and bytes_ > tope:
                    hallazgos.append(_hallazgo(donde, "error",
                                               f"{bytes_} bytes; el máximo es {tope}"))
            if valores and valor not in valores:
                if cerrada:
                    hallazgos.append(_hallazgo(donde, "error",
                                               f"«{valor}» no está en la lista de Amazon"))
                else:
                    hallazgos.append(_hallazgo(donde, "aviso",
                                               f"«{valor}» no está en la lista sugerida; "
                                               "Amazon lo acepta, pero filtra mejor con uno de la lista"))
    return hallazgos
