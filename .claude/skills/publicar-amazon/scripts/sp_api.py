#!/usr/bin/env python3
"""Cliente mínimo de la Selling Partner API de Amazon (SP-API). Solo
biblioteca estándar, igual que el resto del catálogo.

Las credenciales viven fuera del repo, en ~/.catalogo3d/amazon_credenciales.json
con permisos 600. Ningún secreto sale de este módulo: todo texto de error
pasa por _tapar() antes de llegar a la pantalla.
"""
import json
import os
import re
import stat
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HOST = "https://sellingpartnerapi-na.amazon.com"
LWA = "https://api.amazon.com/auth/o2/token"
MARKETPLACE = "A1AM78C64UM0Y8"   # Amazon México
LOCALE = "es_MX"

CARPETA = Path.home() / ".catalogo3d"
RUTA_CRED = CARPETA / "amazon_credenciales.json"
CAMPOS = ("client_id", "client_secret", "refresh_token", "seller_id")
# Se tapan los cuatro: client_id y seller_id son identificadores, no
# secretos, pero no hay razón para que aparezcan en un error.

# Valores que _tapar() quita de cualquier texto: las credenciales cargadas
# y, más adelante, los access tokens vigentes.
_secretos = set()
# Por si un valor llega antes de cargar las credenciales (o es uno nuevo
# que Amazon devolvió): las formas conocidas de tokens y secretos de LWA.
# El mínimo de 20 deja pasar los ejemplos de AYUDA_CRED («Atzr|…»).
_FORMAS = re.compile(r"(Atz[ra]\|[\w\-|=+/.]{20,}|amzn1\.oa2-cs\.[\w\-.]{20,})")

AYUDA_CRED = f"""Faltan las credenciales de Amazon. Crea {RUTA_CRED}
con permisos 600 y estos campos:

  {{"client_id": "amzn1.application-oa2-client.…",
   "client_secret": "amzn1.oa2-cs.v1.…",
   "refresh_token": "Atzr|…",
   "seller_id": "A…"}}

De dónde sale cada uno (Seller Central, como usuario principal):
  - Aplicaciones y servicios → Desarrollar aplicaciones → tu app privada
    (tipo SP API, roles «Product Listing» y «Amazon Fulfillment»).
  - client_id y client_secret: «Ver» en Credenciales de LWA.
  - refresh_token: botón «Autorizar aplicación».
  - seller_id: Identificador de comerciante (Merchant Token); también sale
    en la dirección de tu página de vendedor, después de «seller=».

No los pegues en el chat. Para escribirlos sin que se vean en pantalla:

  python3 -c "import getpass,json,os;p=os.path.expanduser('~/.catalogo3d/amazon_credenciales.json');d={{k:getpass.getpass(k+': ').strip() for k in {list(CAMPOS)!r}}};os.umask(0o077);open(p,'w').write(json.dumps(d,indent=2));os.chmod(p,0o600);print('Guardado en',p)"
"""


class ErrorSP(Exception):
    """Error de credenciales o de la API. El texto ya va tapado."""

    def __init__(self, mensaje):
        super().__init__(_tapar(str(mensaje)))


def _registrar_secreto(valor):
    if isinstance(valor, str) and len(valor) >= 6:
        _secretos.add(valor)


def _tapar(texto):
    """Quita de un texto todo valor secreto conocido y toda forma de token
    o secreto de LWA. Se usa en cada mensaje que puede llegar a la pantalla."""
    texto = str(texto)
    # Los más largos primero: un secreto podría contener a otro.
    for valor in sorted(_secretos, key=len, reverse=True):
        texto = texto.replace(valor, "***")
    return _FORMAS.sub("***", texto)


def cargar_credenciales(ruta=None):
    """Lee las credenciales. Se niega si el archivo falta, si lo pueden leer
    otros usuarios o si le falta un campo; nunca enseña un valor."""
    ruta = Path(ruta or RUTA_CRED)
    if not ruta.exists():
        raise ErrorSP(AYUDA_CRED)
    modo = stat.S_IMODE(os.stat(ruta).st_mode)
    if modo & 0o077:
        raise ErrorSP(
            f"{ruta} tiene permisos {oct(modo)[2:]}: otros usuarios de la "
            f"Mac pueden leerlo. Corre:\n  chmod 600 {ruta}\ny vuelve a intentar.")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except ValueError as e:
        # El mensaje de json trae la posición, no el contenido.
        raise ErrorSP(f"{ruta} no es JSON válido (línea {getattr(e, 'lineno', '?')}).") from None
    for campo in CAMPOS:
        _registrar_secreto(datos.get(campo))
    faltan = [c for c in CAMPOS if not str(datos.get(c) or "").strip()]
    if faltan:
        raise ErrorSP(f"A {ruta} le falta: {', '.join(faltan)}.\n\n{AYUDA_CRED}")
    return {c: str(datos[c]).strip() for c in CAMPOS}


# ---------------------------------------------------------------- peticiones

# Esperas entre reintentos ante 429, 5xx o falla de red: cinco reintentos,
# 31 s en total. Los límites de Listings son de 5 peticiones por segundo.
ESPERAS = (1, 2, 4, 8, 16)
PAUSA = 0.25
REINTENTABLES = (429, 500, 502, 503, 504)

# Se sustituyen en las pruebas.
_abrir = urllib.request.urlopen
_dormir = time.sleep
_reloj = time.monotonic

_cred = None
_token = None        # access token de LWA: solo en memoria
_vence = 0.0
_ultima = 0.0


def credenciales():
    global _cred
    if _cred is None:
        _cred = cargar_credenciales()
    return _cred


def seller_id():
    return credenciales()["seller_id"]


def _access_token(forzar=False):
    """Access token de LWA. Dura una hora; se pide otro 2 minutos antes. No
    se guarda en disco: el refresh token de LWA no rota."""
    global _token, _vence
    if _token and not forzar and _reloj() < _vence:
        return _token
    cred = credenciales()
    cuerpo = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": cred["refresh_token"],
        "client_id": cred["client_id"],
        "client_secret": cred["client_secret"],
    }).encode()
    pedido = urllib.request.Request(
        LWA, data=cuerpo,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with _abrir(pedido, timeout=30) as r:
            datos = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            codigo = json.loads(e.read()).get("error", "")
        except ValueError:
            codigo = ""
        raise ErrorSP(
            f"Amazon no renovó el acceso ({e.code} {codigo}). Si el error es "
            "invalid_grant o invalid_client, autoriza la app otra vez en Seller "
            "Central (Desarrollar aplicaciones → Autorizar aplicación) o revisa "
            "que el client secret no haya rotado.") from None
    except urllib.error.URLError as e:
        raise ErrorSP(f"No hay conexión con Amazon: {e.reason}") from None
    _token = datos["access_token"]
    _registrar_secreto(_token)
    _vence = _reloj() + float(datos.get("expires_in", 3600)) - 120
    return _token


def _url(ruta, params):
    url = HOST + ruta
    if params:
        limpios = {k: (",".join(v) if isinstance(v, (list, tuple)) else v)
                   for k, v in params.items() if v is not None}
        url += "?" + urllib.parse.urlencode(limpios)
    return url


def pedir(metodo, ruta, params=None, cuerpo=None):
    """Petición a SP-API. 'ruta' va sin el host: '/listings/2021-08-01/…'.
    Reintenta 429, 5xx y caídas de red; con 401/403 renueva el token una vez.
    Devuelve el JSON de la respuesta ({} si viene vacía)."""
    global _ultima
    url = _url(ruta, params)
    datos = None if cuerpo is None else json.dumps(cuerpo).encode()
    renovado = False
    intento = 0
    while True:
        espera = PAUSA - (_reloj() - _ultima)
        if espera > 0:
            _dormir(espera)
        encabezados = {
            "x-amz-access-token": _access_token(forzar=renovado and intento == 0),
            "Accept": "application/json",
            "User-Agent": "PublicadorSaviaRaiz/1.0 (Language=Python)",
        }
        if datos is not None:
            encabezados["Content-Type"] = "application/json"
        pedido = urllib.request.Request(url, data=datos, method=metodo,
                                        headers=encabezados)
        motivo = None
        try:
            with _abrir(pedido, timeout=60) as r:
                _ultima = _reloj()
                texto = r.read()
                return json.loads(texto) if texto.strip() else {}
        except urllib.error.HTTPError as e:
            _ultima = _reloj()
            detalle = e.read().decode("utf-8", "replace")[:1500]
            if e.code in (401, 403) and not renovado:
                renovado, intento = True, 0
                continue
            if e.code not in REINTENTABLES:
                pista = ""
                if e.code == 403:
                    pista = ("\n  (403 después de renovar: revisa que la app tenga "
                             "los roles «Product Listing» y «Amazon Fulfillment».)")
                raise ErrorSP(f"{metodo} {ruta} -> {e.code}: {detalle}{pista}") from None
            motivo = f"{e.code}: {detalle}"
        except urllib.error.URLError as e:
            _ultima = _reloj()
            motivo = f"sin conexión ({e.reason})"
        if intento >= len(ESPERAS):
            raise ErrorSP(f"{metodo} {ruta} falló {intento + 1} veces; la última: {motivo}")
        _dormir(ESPERAS[intento])
        intento += 1
