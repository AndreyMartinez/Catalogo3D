#!/usr/bin/env python3
"""Sesión con MercadoLibre. Se corre una sola vez (o cuando caduque el
refresh token, a los 6 meses).

Uso:
  python3 scripts/login.py            -> te da la URL para autorizar
  python3 scripts/login.py TG-xxxx    -> canjea el código y guarda el token
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ml_api  # noqa: E402


def main():
    try:
        cred = ml_api.cargar_credenciales()
    except ml_api.ErrorML as e:
        print(e)
        return 1

    if len(sys.argv) < 2:
        print("1) Abre esta URL en tu navegador y autoriza la app:\n")
        print("   " + ml_api.url_autorizacion(cred.get("site", "MLM")))
        print("\n2) Te va a redirigir a tu redirect_uri con ?code=TG-... al final")
        print("   (la página puede verse rota: no importa, lo que vale es la URL).")
        print("\n3) Copia ese code y corre:")
        print("   python3 scripts/login.py TG-elcodigoquecopiaste")
        return 0

    code = sys.argv[1].strip()
    try:
        ml_api.canjear_codigo(code)
        yo = ml_api.pedir("/users/me")
    except ml_api.ErrorML as e:
        print(f"No se pudo: {e}")
        print("\nEl code dura minutos y se usa una sola vez. Si ya venció, "
              "vuelve a correr login.py sin argumentos y saca uno nuevo.")
        return 1

    print(f"Listo. Sesión de {yo.get('nickname')} "
          f"(id {yo.get('id')}, sitio {yo.get('site_id')}).")
    print(f"Token guardado en {ml_api.RUTA_TOKEN} (solo lo lee tu usuario).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
