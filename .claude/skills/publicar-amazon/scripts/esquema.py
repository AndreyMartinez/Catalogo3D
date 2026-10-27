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
import sys
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
