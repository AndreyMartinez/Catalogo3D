#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bordes: hasta dónde sube cada columna de la pared.

El borde es lo primero que mira el ojo y hasta ahora era idéntico en todas las
combinaciones del catálogo: un aro horizontal. Un labio que no es un aro es de
las cosas que más rápido separan una pieza diseñada de un bote.

No hace falta mecanismo nuevo. El motor ya lleva una altura de remate por
columna —el arreglo `tope`, que usa el escalón para dejar el frente más bajo
que el fondo— y el casco se arma en fracciones de esa altura, así que la pared
sigue el recorte sola y sin escalones. Un borde recortado es escribir ese mismo
arreglo con otra función.

Tampoco hay problema de voladizo: el borde es lo más alto de la pieza y por
debajo siempre queda material.

Las frecuencias que corren a lo largo del contorno son enteras a la fuerza, por
la misma razón que ya obliga a eso a los acabados: el contorno se cierra sobre
sí mismo, y una onda que no dé un número entero de vueltas deja un escalón en
la costura.
"""

import math

TAU = 2 * math.pi


def _neutro(p, anillo, alto):
    return [alto] * len(anillo)


def _hondura(p, alto):
    return max(0.0, min(0.45, float(p["borde_hondura"]))) * alto


def diagonal(p, anillo, alto):
    """Un plano inclinado: la pieza cortada al bies.

    El corte es plano de verdad —la altura es lineal en la posición— y no una
    onda de media vuelta, que es lo que saldría de usar un coseno. La
    diferencia se nota: un plano lee como corte, una onda lee como decoración.
    """
    caida = _hondura(p, alto)
    if caida <= 0.0:
        return _neutro(p, anillo, alto)
    r = math.radians(float(p["borde_rumbo"]))
    ux, uy = math.cos(r), math.sin(r)
    proy = [x * ux + y * uy for x, y, _, _, _ in anillo]
    lo, hi = min(proy), max(proy)
    largo = (hi - lo) or 1.0
    # En el lado al que apunta el rumbo queda lo alto; en el opuesto, lo bajo.
    return [alto - caida * (1.0 - (q - lo) / largo) for q in proy]


def ondulado(p, anillo, alto):
    """Ondas parejas alrededor de la boca. El labio sube y baja sin quiebres."""
    caida = _hondura(p, alto)
    if caida <= 0.0:
        return _neutro(p, anillo, alto)
    n = max(1, int(round(float(p["borde_ondas"]))))
    return [alto - caida * (1.0 - math.cos(TAU * n * s)) / 2.0
            for _, _, _, _, s in anillo]


def petalos(p, anillo, alto):
    """Pétalos: lóbulos redondos que se juntan en punta.

    Cada lóbulo es un arco de círculo, no media onda. La diferencia está en el
    valle: el arco llega con tangente vertical y deja una punta viva entre
    pétalo y pétalo, y esa punta es justamente lo que se lee como flor. Una
    onda deja el valle redondeado y el resultado parece festón de cortina.
    """
    caida = _hondura(p, alto)
    if caida <= 0.0:
        return _neutro(p, anillo, alto)
    n = max(1, int(round(float(p["borde_ondas"]))))
    salida = []
    for _, _, _, _, s in anillo:
        u = (s * n) % 1.0
        arco = math.sqrt(max(0.0, 1.0 - (2.0 * u - 1.0) ** 2))
        salida.append(alto - caida * (1.0 - arco))
    return salida


BORDES = {
    "recto": ("Recto", _neutro),
    "diagonal": ("Corte diagonal", diagonal),
    "ondulado": ("Ondulado", ondulado),
    "petalos": ("Pétalos", petalos),
}


def remate(p, anillo, alto):
    """La altura de remate de cada columna, según el borde elegido."""
    return BORDES[p.get("borde", "recto")][1](p, anillo, alto)


def es_neutro(p):
    """Si el borde no recorta nada, el motor se salta el trabajo extra."""
    return (p.get("borde", "recto") == "recto"
            or float(p.get("borde_hondura", 0.0)) <= 0.0)
