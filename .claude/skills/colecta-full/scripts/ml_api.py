#!/usr/bin/env python3
"""Cliente mínimo de la API de MercadoLibre. Solo biblioteca estándar,
igual que el resto del catálogo.

Guarda credenciales y token fuera del repo, en ~/.catalogo3d/, con
permisos 600. El token de acceso dura unas 6 horas; el de refresco se
usa una sola vez, así que cada refresco guarda el nuevo.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.mercadolibre.com"
CARPETA = Path.home() / ".catalogo3d"
RUTA_CRED = CARPETA / "ml_credenciales.json"
RUTA_TOKEN = CARPETA / "ml_token.json"


class ErrorML(Exception):
    pass


def _guardar_privado(ruta: Path, datos: dict):
    CARPETA.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(ruta, 0o600)


def cargar_credenciales():
    if not RUTA_CRED.exists():
        raise ErrorML(
            f"Faltan las credenciales. Crea {RUTA_CRED} con:\n"
            '  {"client_id": "...", "client_secret": "...", '
            '"redirect_uri": "https://localhost/ml"}'
        )
    return json.loads(RUTA_CRED.read_text(encoding="utf-8"))


def cargar_token():
    if not RUTA_TOKEN.exists():
        raise ErrorML("No hay sesión. Corre primero: python3 scripts/login.py")
    return json.loads(RUTA_TOKEN.read_text(encoding="utf-8"))


def _post_oauth(campos: dict):
    cuerpo = urllib.parse.urlencode(campos).encode()
    pedido = urllib.request.Request(
        f"{API}/oauth/token", data=cuerpo,
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Accept": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")
        raise ErrorML(f"OAuth falló ({e.code}): {detalle}") from None


def _escribir_token(datos: dict):
    datos["expira_en"] = time.time() + float(datos.get("expires_in", 0)) - 120
    _guardar_privado(RUTA_TOKEN, datos)
    return datos


def canjear_codigo(code: str):
    """Primer intercambio: el código de la URL de autorización por el token."""
    cred = cargar_credenciales()
    datos = _post_oauth({
        "grant_type": "authorization_code",
        "client_id": cred["client_id"],
        "client_secret": cred["client_secret"],
        "code": code,
        "redirect_uri": cred["redirect_uri"],
    })
    return _escribir_token(datos)


def refrescar():
    cred = cargar_credenciales()
    token = cargar_token()
    if not token.get("refresh_token"):
        raise ErrorML("El token no trae refresh_token. Vuelve a correr login.py "
                      "y revisa que la app tenga activado 'offline_access'.")
    datos = _post_oauth({
        "grant_type": "refresh_token",
        "client_id": cred["client_id"],
        "client_secret": cred["client_secret"],
        "refresh_token": token["refresh_token"],
    })
    return _escribir_token(datos)


def _token_vigente():
    token = cargar_token()
    if time.time() >= token.get("expira_en", 0):
        token = refrescar()
    return token["access_token"]


def pedir(ruta: str, params: dict = None, reintento=True):
    """GET autenticado. 'ruta' va sin el host: '/users/me'."""
    url = API + ruta
    if params:
        url += "?" + urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None})
    pedido = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {_token_vigente()}",
                      "Accept": "application/json"})
    try:
        with urllib.request.urlopen(pedido, timeout=45) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403) and reintento:
            refrescar()
            return pedir(ruta, params, reintento=False)
        detalle = e.read().decode("utf-8", "replace")[:600]
        raise ErrorML(f"GET {url}\n  -> {e.code}: {detalle}") from None


def url_autorizacion(site="MLM"):
    cred = cargar_credenciales()
    dominio = {"MLM": "com.mx", "MLA": "com.ar", "MLB": "com.br",
               "MLC": "cl", "MCO": "com.co", "MPE": "com.pe"}.get(site, "com.mx")
    q = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": cred["client_id"],
        "redirect_uri": cred["redirect_uri"],
    })
    return f"https://auth.mercadolibre.{dominio}/authorization?{q}"
