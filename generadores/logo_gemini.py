#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Variantes de logo e imágenes de marca con Gemini a partir de fotos o bocetos
de referencia. Con él salió el sello oficial de Savia Raíz (marca/).

    python3 logo_gemini.py --modelos
    python3 logo_gemini.py -r arepo.jpg -r boceto.png -p "prompt" -o salida -n 3 \
        --modelo gemini-3-pro-image --aspecto 1:1

La llave se lee de ~/.catalogo3d/gemini_key (una línea) o de GEMINI_API_KEY en
el .env que se pase con --env. Nunca se imprime ni va al repo.
"""
import argparse
import base64
import json
import mimetypes
import urllib.error
import urllib.request
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta"


def llave(env):
    texto = Path(env).expanduser().read_text()
    if "=" not in texto:  # archivo de una sola línea, como ~/.catalogo3d/gemini_key
        return texto.strip()
    for linea in texto.splitlines():
        if linea.strip().startswith("GEMINI_API_KEY="):
            return linea.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("No hay GEMINI_API_KEY en " + env)


def pedir(k, metodo, ruta, cuerpo=None):
    req = urllib.request.Request(
        API + ruta, method=metodo,
        data=json.dumps(cuerpo).encode() if cuerpo else None,
        headers={"x-goog-api-key": k, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit("Gemini %s: %s" % (e.code, e.read().decode()[:600]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="~/.catalogo3d/gemini_key")
    ap.add_argument("--modelos", action="store_true")
    ap.add_argument("--modelo", default="gemini-3.1-flash-image")
    ap.add_argument("-r", "--ref", action="append", default=[])
    ap.add_argument("-p", "--prompt")
    ap.add_argument("-o", "--salida")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--aspecto", default="1:1")
    a = ap.parse_args()
    k = llave(a.env)

    if a.modelos:
        for m in pedir(k, "GET", "/models?pageSize=200").get("models", []):
            n = m["name"].split("/")[-1]
            if "image" in n or "imagen" in n:
                print(n, "-", m.get("displayName", ""))
        return

    partes = []
    for r in a.ref:
        mime = mimetypes.guess_type(r)[0] or "image/png"
        partes.append({"inlineData": {"mimeType": mime,
                                      "data": base64.b64encode(Path(r).read_bytes()).decode()}})
    partes.append({"text": a.prompt})
    cuerpo = {"contents": [{"parts": partes}],
              "generationConfig": {"responseModalities": ["IMAGE"],
                                   "imageConfig": {"aspectRatio": a.aspecto}}}
    for i in range(1, a.n + 1):
        r = pedir(k, "POST", "/models/%s:generateContent" % a.modelo, cuerpo)
        for c in r.get("candidates", []):
            for p in c.get("content", {}).get("parts", []):
                if "inlineData" in p:
                    ext = ".png" if "png" in p["inlineData"]["mimeType"] else ".jpg"
                    out = Path("%s_%d%s" % (a.salida, i, ext))
                    out.write_bytes(base64.b64decode(p["inlineData"]["data"]))
                    print(out)
                    break
            else:
                continue
            break
        else:
            print("sin imagen:", json.dumps(r)[:400])


if __name__ == "__main__":
    main()
