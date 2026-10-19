#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera piezas de la línea desde la terminal.

    python3 crear.py --listar
    python3 crear.py portacontroles
    python3 crear.py portalapices --contorno origami --pliegues 10
    python3 crear.py portacubiertos --salida /ruta/carpeta --nombre MiVersion

Cualquier parámetro de disenos.PARAMETROS se puede pasar como --clave valor.
Lo mismo que hace la pestaña «Crear» del catálogo, sin navegador.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import disenos                                    # noqa: E402
from nucleo import cuerpo, exportar, render       # noqa: E402

CARPETA_DEFECTO = Path.home() / "Desktop" / "own design 3d"
CENTRO_PLATO = 128.0        # centra la pieza en la placa al abrir el .3mf


def generar(clave, valores, carpeta, nombre=None, con_miniatura=True, vista=None):
    """Construye, renderiza y guarda. Devuelve (datos, rutas).

    `vista` es (giro, elevación) en grados: así la miniatura queda desde el
    mismo ángulo que el usuario dejó en la pantalla."""
    p = disenos.normalizar(valores)
    malla, datos = cuerpo.construir(p)
    nombre = nombre or disenos.nombre_sugerido(clave, p)
    nombre = "".join(c for c in nombre if c not in '/\\:*?"<>|').strip() or "Diseno"

    carpeta = Path(carpeta).expanduser()
    carpeta.mkdir(parents=True, exist_ok=True)
    rutas = {"3mf": carpeta / (nombre + ".3mf"), "stl": carpeta / (nombre + ".stl")}

    png = None
    if con_miniatura:
        png = render.render(malla.v, malla.t, tam=512, suavizado=2,
                            direccion=render.vector_vista(*(vista or render.camara(p))),
                            ruta=carpeta / (nombre + ".png"))
        rutas["png"] = carpeta / (nombre + ".png")

    notas = "%s · %s mm · %s g" % (nombre, "×".join(
        str(datos[k]) for k in ("ancho", "fondo", "alto")), datos["gramos"])
    piezas = exportar.acomodar(datos["piezas"], CENTRO_PLATO)
    exportar.guardar_3mf(piezas, rutas["3mf"], nombre, miniatura=png, notas=notas,
                         parametros=dict(p, diseno=clave))
    exportar.guardar_stl(piezas, rutas["stl"], nombre)
    return datos, rutas


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("diseno", nargs="?")
    ap.add_argument("--listar", action="store_true")
    ap.add_argument("--nombre")
    ap.add_argument("--salida")
    ap.add_argument("--sin-miniatura", action="store_true")
    ap.add_argument("-h", "--help", action="store_true")
    for spec in disenos.PARAMETROS:
        ap.add_argument("--" + spec["clave"].replace("_", "-"),
                        dest=spec["clave"], default=None)
    args = ap.parse_args()

    if args.help or (not args.diseno and not args.listar):
        print(__doc__)
        print("Diseños:", ", ".join(d["clave"] for d in disenos.DISENOS))
        print("\nParámetros:")
        for spec in disenos.PARAMETROS:
            rango = ("%s a %s" % (spec["min"], spec["max"]) if spec["tipo"] == "num"
                     else "/".join(o["clave"] for o in spec["opciones"]))
            print("  --%-22s %-14s %s" % (spec["clave"].replace("_", "-"),
                                          spec["valor"], rango))
        return

    if args.listar:
        for d in disenos.DISENOS:
            print("%-16s %s" % (d["clave"], d["descripcion"]))
        return

    if args.diseno not in disenos.POR_CLAVE:
        print("No conozco «%s». Hay: %s"
              % (args.diseno, ", ".join(disenos.POR_CLAVE)))
        sys.exit(1)

    valores = disenos.parametros_de(args.diseno)
    for spec in disenos.PARAMETROS:
        v = getattr(args, spec["clave"], None)
        if v is not None:
            valores[spec["clave"]] = v

    carpeta = (Path(args.salida) if args.salida
               else CARPETA_DEFECTO / disenos.POR_CLAVE[args.diseno]["carpeta"])
    datos, rutas = generar(args.diseno, valores, carpeta, args.nombre,
                           not args.sin_miniatura)

    print("%s — %s" % (disenos.POR_CLAVE[args.diseno]["nombre"], rutas["3mf"].stem))
    print("  Exterior     %s × %s × %s mm"
          % (datos["ancho"], datos["fondo"], datos["alto"]))
    if datos["ranuras"] > 1:
        print("  Ranuras      %d de %s mm" % (datos["ranuras"], datos["ancho_ranura"]))
    if datos["agujeros"]:
        print("  Drenaje      %d agujeros" % datos["agujeros"])
    if len(datos["piezas"]) > 1:
        print("  Piezas       %s" % ", ".join(n for n, _ in datos["piezas"]))
    if datos.get("bandeja"):
        b = datos["bandeja"]
        print("  Bandeja      %s × %s × %s mm, %d costillas"
              % (b["ancho"], b["fondo"], b["alto"], b["costillas"]))
    if datos["estrias"]:
        print("  Estrías      %d" % datos["estrias"])
    print("  Material     %.1f cm³  ≈  %s g" % (datos["volumen_cm3"], datos["gramos"]))
    print("  Malla        %d triángulos, %s"
          % (datos["triangulos"], "cerrada" if datos["cerrada"] else "ABIERTA"))
    print("  Resolución   %d puntos por anillo × %d capas"
          % (datos["segmentos"], datos["capas"]))
    for a in datos["avisos"]:
        print("  ⚠  " + a)
    for k in ("3mf", "stl", "png"):
        if k in rutas:
            print("  → %s" % rutas[k])


if __name__ == "__main__":
    main()
