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
from pathlib import Path

HOST = "https://sellingpartnerapi-na.amazon.com"
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
