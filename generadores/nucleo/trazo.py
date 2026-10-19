#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""La silueta sacada de una imagen, guardada como radio en función del ángulo.

Todos los contornos del motor están escritos así —un radio por cada ángulo—, y
el piso se cierra en abanico desde el centro apoyándose en esa propiedad. La
silueta trazada se guarda igual, y no es sólo por parecerse: muestrear por
ángulo **garantiza** que la forma sea estrellada respecto del centro, que es la
condición de la que depende ese abanico. Lo que se pierde a cambio son las
concavidades hondas —la hendidura de una luna, el hueco de una C—, y eso se
mide y se avisa donde se traza, no aquí.

Guardada así, la silueta cabe en unos doscientos caracteres, y por eso puede
viajar dentro de los propios valores en vez de necesitar un registro aparte en
el servidor: sobrevive un recargado de página y no deja estado que limpiar.

Este módulo es sólo la representación —codificar, decodificar, interpolar—. La
lectura del PNG y el trazado de la silueta viven en `imagen.py` y en la parte
de arriba de este mismo archivo cuando llegue.
"""

import base64
import binascii
import math
import zlib

MUESTRAS = 180          # un radio cada dos grados
MARCA = b"T1"           # versión del formato; una que no se conozca se ignora
_TOPE_INFLADO = 16384   # lo que entra viene de fuera: zlib no se suelta libre


def radio_en(radios, t):
    """El radio en la fracción `t` del contorno, interpolando entre muestras.

    Circular a propósito: el contorno se cierra sobre sí mismo, y la última
    muestra tiene que estirarse hacia la primera. Cortar ahí dejaría un
    escalón justo en la costura.
    """
    n = len(radios)
    u = (t % 1.0) * n
    i = int(u)
    return radios[i % n] + (radios[(i + 1) % n] - radios[i % n]) * (u - i)


def remuestrear(radios, n=MUESTRAS):
    """Lleva una lista de radios a `n` muestras parejas."""
    if len(radios) == n:
        return list(radios)
    return [radio_en(radios, i / n) for i in range(n)]


def codificar(radios):
    """Radios → la cadena que viaja en los valores.

    Cada radio se guarda como fracción del mayor, en un byte. Sobre una pieza
    de 70 mm un paso vale 0.14 mm: por debajo de lo que imprime la máquina, así
    que la cuantización no se ve. La escala real se la pone el contorno, que
    estira la silueta hasta llenar el ancho y el fondo pedidos.
    """
    if not radios:
        return ""
    radios = remuestrear([max(0.0, float(r)) for r in radios])
    mayor = max(radios)
    if mayor <= 0.0:
        return ""
    crudo = bytes(min(255, max(0, round(r / mayor * 255.0))) for r in radios)
    return base64.b64encode(zlib.compress(MARCA + crudo, 9)).decode("ascii")


def decodificar(cadena):
    """La cadena → radios de 0 a 1, o None si no se pudo leer.

    Devuelve None y no lanza para todo: base64 roto, zlib roto, una marca de
    versión que no se conoce, o un largo que no cuadra. Lo que entra por aquí
    viene del navegador, y el motor tiene que poder degradar a un círculo en
    vez de caerse.
    """
    if not isinstance(cadena, str) or not cadena:
        return None
    try:
        comprimido = base64.b64decode(cadena, validate=True)
    except (binascii.Error, ValueError):
        return None
    try:
        # Con tope: 3 KB comprimidos pueden inflarse a muchísimo más, y esto
        # lo manda quien tenga el navegador abierto.
        motor = zlib.decompressobj()
        crudo = motor.decompress(comprimido, _TOPE_INFLADO)
        if motor.unconsumed_tail:
            return None
    except zlib.error:
        return None
    if not crudo.startswith(MARCA) or len(crudo) != len(MARCA) + MUESTRAS:
        return None
    return [b / 255.0 for b in crudo[len(MARCA):]]


def de_funcion(fn, n=MUESTRAS):
    """Radios muestreados de una función del ángulo. Comodidad para pruebas y
    para el trazador, que produce lo mismo desde los píxeles."""
    return [float(fn(i * 2.0 * math.pi / n)) for i in range(n)]
