#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fotos de producto con Gemini: de un render (o una foto real) de la pieza a
escenas como si ya estuviera impresa, para las fotos de MercadoLibre.

    python3 fotos_gemini.py ref.png --nombre Maceta_Gajos_Trenzada
    python3 fotos_gemini.py ref.png --escenas repisa mano -n 2
    python3 fotos_gemini.py ref.png --prompt "sobre una mesa de centro de nogal"
    python3 fotos_gemini.py --modelos          # qué modelos de imagen hay
    python3 fotos_gemini.py --guardar-llave    # la pide oculta y la prueba

La llave va en ~/.catalogo3d/gemini_key (una línea, permisos 600) o en la
variable GEMINI_API_KEY. Nunca en el repo.

La imagen de referencia manda la forma: el modelo suele cambiar el número de
gajos, quitar el giro o la estría, así que cada foto se revisa contra la pieza
antes de subirla. La principal de ML va con la foto real; estas son las de
ambiente.
"""

import argparse
import base64
import getpass
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://generativelanguage.googleapis.com/v1beta"
MODELO = "gemini-3.1-flash-image"
LLAVE = Path.home() / ".catalogo3d" / "gemini_key"
SALIDA = Path.home() / "Desktop" / "own design 3d" / "Pruebas de productos" / "fotos"

# Lo que se le repite al modelo en cada escena: que copie la pieza tal cual y
# que se vea impresa en PLA mate, no cerámica ni plástico inyectado.
FIDELIDAD = (
    "The reference image shows a 3D-printed product. Reproduce this exact object: "
    "same silhouette and proportions, same number of lobes, same twist and the same "
    "fine ribbing direction. Do not add, remove or reshape any feature. Render it as "
    "a real photograph of a matte PLA 3D print in {color} (recolor it if the reference "
    "shows another color), with very fine horizontal "
    "layer lines visible up close. No text, no logos, no watermark, no packaging. "
    "Square 1:1 photo, product in sharp focus, natural colors."
)

ESCENAS = {
    "blanco": "Studio product shot on a seamless pure white background, soft even light, "
              "gentle contact shadow, object centered and filling most of the frame.",
    # Pared de una vuelta: no aguanta agua, y la boca libre de la maceta de
    # gajos es de ~36 mm, no entra maceta de vivero. Flores secas siempre.
    "detalle": "Macro close-up of the surface: the diagonal ribs and the crease between two "
               "lobes, raking side light, background softly blurred.",
    "arriba": "Seen from above at a steep angle on a light wood surface, showing the "
              "four-lobed opening and how the lobes twist down the body.",
    "repisa": "On a light oak wall shelf in a bright Scandinavian living room, a few thin "
              "dried olive branches inside, soft window light from the left.",
    "escritorio": "On a tidy home-office desk next to a laptop and a notebook, a few "
                  "slim dried lavender stems inside the narrow opening, daylight.",
    "recibidor": "On a narrow entryway console table with a round mirror behind, dried "
                 "eucalyptus and bunny-tail grass inside, warm light.",
    "mesa": "On a minimalist japandi dining table with linen runner, a few dried pampas "
            "stems inside, warm late-afternoon light, shallow depth of field.",
    "recamara": "On a white nightstand next to a ceramic lamp and a book, dried "
                "eucalyptus branches inside, calm morning light.",
    "mano": "Held by an adult hand against a neutral beige wall, to show its real size "
            "(about 9 cm wide and 19 cm tall); the lobes keep their strong quarter-turn "
            "spiral and the ribs run diagonally all the way up, soft daylight.",
}


def guardar_llave():
    """Pide la llave sin mostrarla en pantalla y la deja en LLAVE con 600."""
    k = getpass.getpass("Pega la llave de Gemini (no se ve al escribir) y Enter: ").strip()
    if not k:
        sys.exit("No se pegó nada; no guardé.")
    LLAVE.parent.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(LLAVE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(k + "\n")
    os.chmod(LLAVE, 0o600)
    print("Guardada en %s (solo tú la lees). Probando…" % LLAVE)
    modelos()


def llave():
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if k:
        return k
    if not LLAVE.exists():
        sys.exit("Falta la llave: guárdala en %s (chmod 600) o en GEMINI_API_KEY." % LLAVE)
    if LLAVE.stat().st_mode & 0o077:
        print("Aviso: %s la pueden leer otros usuarios; chmod 600." % LLAVE, file=sys.stderr)
    return LLAVE.read_text().strip()


def pedir(metodo, ruta, cuerpo=None):
    req = urllib.request.Request(
        API + ruta, method=metodo,
        data=None if cuerpo is None else json.dumps(cuerpo).encode(),
        headers={"x-goog-api-key": llave(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit("Gemini respondió %d: %s" % (e.code, e.read().decode(errors="replace")[:800]))


def modelos():
    hay = [m for m in pedir("GET", "/models?pageSize=200").get("models", [])
           if "image" in m["name"]]
    for m in hay:
        print(m["name"].split("/", 1)[1], "—", m.get("displayName", ""))
    if not hay:
        print("La llave funciona, pero no aparece ningún modelo de imagen.")


def generar(modelo, ref, texto):
    """Una imagen: referencia + instrucciones → bytes y su extensión."""
    tipo = mimetypes.guess_type(str(ref))[0] or "image/png"
    cuerpo = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": tipo,
                             "data": base64.b64encode(Path(ref).read_bytes()).decode()}},
            {"text": texto},
        ]}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": "1:1"}},
    }
    r = pedir("POST", "/models/%s:generateContent" % modelo, cuerpo)
    for c in r.get("candidates", []):
        for parte in c.get("content", {}).get("parts", []):
            datos = parte.get("inlineData") or parte.get("inline_data")
            if datos:
                ext = mimetypes.guess_extension(datos.get("mimeType", "image/png")) or ".png"
                return base64.b64decode(datos["data"]), ext
    motivo = r.get("promptFeedback") or [c.get("finishReason") for c in r.get("candidates", [])]
    raise RuntimeError("sin imagen en la respuesta: %s" % motivo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("referencia", nargs="?", help="render o foto de la pieza")
    ap.add_argument("--nombre", help="prefijo de los archivos (por omisión, el de la referencia)")
    ap.add_argument("--escenas", nargs="+", choices=sorted(ESCENAS),
                    default=["blanco", "repisa", "mesa", "mano"])
    ap.add_argument("--prompt", help="escena libre en lugar de las de la lista")
    ap.add_argument("--color", default="warm off-white cream")
    ap.add_argument("-n", type=int, default=1, help="variantes por escena")
    ap.add_argument("--modelo", default=MODELO)
    ap.add_argument("--salida", default=str(SALIDA))
    ap.add_argument("--modelos", action="store_true", help="lista los modelos de imagen y sale")
    ap.add_argument("--guardar-llave", action="store_true",
                    help="pide la llave sin mostrarla, la guarda con 600 y la prueba")
    a = ap.parse_args()

    if a.guardar_llave:
        return guardar_llave()
    if a.modelos:
        return modelos()
    if not a.referencia or not Path(a.referencia).exists():
        ap.error("falta la imagen de referencia")
    nombre = a.nombre or Path(a.referencia).stem
    carpeta = Path(a.salida).expanduser()
    carpeta.mkdir(parents=True, exist_ok=True)
    escenas = {"libre": a.prompt} if a.prompt else {k: ESCENAS[k] for k in a.escenas}
    base = FIDELIDAD.format(color=a.color)
    for clave, escena in escenas.items():
        for i in range(1, a.n + 1):
            try:
                datos, ext = generar(a.modelo, a.referencia, base + " Scene: " + escena)
            except RuntimeError as e:
                print("  %s %d: %s" % (clave, i, e), file=sys.stderr)
                continue
            ruta = carpeta / ("%s_%s_%d%s" % (nombre, clave, i, ext))
            ruta.write_bytes(datos)
            print(ruta)


if __name__ == "__main__":
    main()
