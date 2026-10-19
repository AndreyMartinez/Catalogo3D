#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bandeja de goteo: el plato donde se para el vaso.

Un vaso con drenaje sin bandeja no resuelve nada — nada más manda el
agua a la repisa. La bandeja la recoge, y se levanta el vaso para vaciarla.

Es la misma silueta del vaso, corrida hacia afuera lo que mida la pared más
la holgura, y de unos centímetros de alto. Lo único que no es obvio son las
costillas del fondo: sin ellas el vaso se queda parado dentro de su propia
agua y no sirve de nada haber drenado.

Sale como pieza aparte en el mismo .3mf, así que se lamina de una y se
imprime de un color o de dos.
"""

import math

from . import malla as M

ALTO_COSTILLA = 2.5      # lo que el vaso queda por encima del charco
ANCHO_COSTILLA = 1.6     # media anchura de cada barra
PUNTOS = 200             # el contorno de la bandeja no necesita el del vaso


def _perfil(anillo, escala, alto, amp, salida):
    """El contorno del vaso corrido `salida` mm hacia afuera.

    Se toma el radio más ancho que el vaso alcanza dentro de la altura de la
    bandeja, no el de su base: con un perfil cónico o de barril, la base es
    lo más angosto y una bandeja hecha a esa medida le pega al vaso más
    arriba."""
    e = max(escala(alto * j / 8.0) for j in range(9))
    paso = max(1, len(anillo) // PUNTOS)
    return [(x * e + nx * (amp + salida), y * e + ny * (amp + salida))
            for x, y, nx, ny, _ in anillo[::paso]]


def _barra(largo, ancho, angulo):
    c, s = math.cos(angulo), math.sin(angulo)
    return [(x * c - y * s, x * s + y * c)
            for x, y in ((-largo, -ancho), (largo, -ancho),
                         (largo, ancho), (-largo, ancho))]


def _aro(m, poly, z):
    return [m.punto(x, y, z) for x, y in poly]


def _abanico(m, aro, poly, z, hacia_arriba):
    """Cierra un aro ya construido con un abanico desde su centro.

    El aro entra hecho a propósito: si el abanico creara sus propios puntos,
    las caras coincidirían en el espacio pero no en los índices y la malla
    quedaría abierta por todo el contorno.

    Todos los contornos del motor son estrellados respecto al centro —están
    escritos como radio en función del ángulo—, así que el abanico siempre
    vale. Y vale donde el recorte de orejas se atora: un rectángulo muestreado
    tiene tramos rectos llenos de puntos casi colineales, y ahí el
    triangulador general se queda sin orejas que cortar."""
    cx = sum(x for x, _ in poly) / len(poly)
    cy = sum(y for _, y in poly) / len(poly)
    centro = m.punto(cx, cy, z)
    for i in range(len(aro)):
        j = (i + 1) % len(aro)
        if hacia_arriba:
            m.cara(centro, aro[i], aro[j])
        else:
            m.cara(centro, aro[j], aro[i])


def construir(anillo, amp, escala, p):
    """Devuelve (malla, datos) o (None, motivo)."""
    alto = float(p["bandeja_alto"])
    holgura = float(p["bandeja_holgura"])
    pared = max(1.6, float(p["pared"]))
    piso = max(1.6, float(p["piso"]))
    barras = max(0, int(p["bandeja_costillas"]))

    if alto <= piso + ALTO_COSTILLA + 1.0:
        return None, "La bandeja es más baja que su propio piso; súbele el alto."

    interior = _perfil(anillo, escala, alto, amp, holgura)
    exterior = _perfil(anillo, escala, alto, amp, holgura + pared)

    m = M.Malla()
    ext0, ext1 = _aro(m, exterior, 0.0), _aro(m, exterior, alto)
    int0, int1 = _aro(m, interior, piso), _aro(m, interior, alto)
    n = len(exterior)
    for i in range(n):
        j = (i + 1) % n
        m.quad(ext0[i], ext0[j], ext1[j], ext1[i])    # pared de afuera
        m.quad(int1[i], int1[j], int0[j], int0[i])    # pared de adentro
        m.quad(ext1[i], ext1[j], int1[j], int1[i])    # canto de arriba
    _abanico(m, ext0, exterior, 0.0, False)           # asiento
    _abanico(m, int0, interior, piso, True)           # fondo del plato

    # Las costillas son barras de lado a lado que pasan por el centro: dos
    # barras hacen una cruz, tres una estrella de seis. Van de diámetro
    # completo para que el agua corra por debajo del vaso en vez de quedarse
    # encharcada en un anillo.
    radio = min(math.hypot(x, y) for x, y in interior) - 1.2
    puestas = 0
    if radio > 4.0:
        for k in range(barras):
            barra = M.placa(_barra(radio, ANCHO_COSTILLA, math.pi * k / barras),
                            [], piso, piso + ALTO_COSTILLA)
            if barra is not None:
                m.unir(barra)
                puestas += 1

    m.normalizar()
    (x0, y0, _), (x1, y1, _) = m.caja()
    return m, {
        "ancho": round(x1 - x0, 1),
        "fondo": round(y1 - y0, 1),
        "alto": round(alto, 1),
        "costillas": puestas,
        "apoyo": piso + ALTO_COSTILLA,   # cuánto sube el vaso al meterlo
    }
