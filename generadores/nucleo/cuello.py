#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cuellos: cómo se cierra la pieza hacia la boca.

Un cuello es lo mismo que un perfil —una función z -> factor de escala— y por
eso vive junto a él en `escala(z)`, multiplicando. Que vaya de escala y no de
desplazamiento es lo que hace que la pared conserve su espesor sola.

Se separa del perfil porque son dos decisiones distintas y conviene no
mezclarlas. El perfil pone la panza: dónde está lo más ancho y cómo se llega.
El cuello pone la boca: cuánto se cierra arriba y desde qué altura. Un vaso es
un perfil sin cuello; un jarrón es el mismo perfil con cuello. Metidos en el
mismo control, para conseguir un jarrón habría que elegir entre panza y boca, y
un jarrón es justamente las dos cosas.

La curva del cierre es un smoothstep, t²(3−2t), y no una recta. La razón es la
esquina: multiplicar por una función con derivada nula en los dos extremos deja
intacta la pendiente de la panza donde empieza el hombro, y llega al cuello
igual de suave. Con una recta aparecen dos quiebres, y una esquina en el hombro
es de las cosas que hacen que una pieza se lea barata.

Los tres cuellos son el mismo cierre en distinto tramo. `suave` se toma toda la
altura que le queda; `abrupto` cierra en el primer 45% y sigue recto; `botella`
en el primer 25%. De ahí sale que el primero se lea como jarrón, el segundo
tenga hombro marcado y el tercero, gollete.
"""


class Cuello:
    """`fn` va de la fracción de altura (0 a 1) al factor de escala.

    `neutro` dice que no hace nada, y sirve para que el motor se salte el
    trabajo extra en vez de multiplicar por uno. `minimo` es lo más que llega a
    cerrarse, que es lo que necesita el chequeo de la pared interior.
    """

    def __init__(self, fn, varia_z=True, neutro=False, minimo=1.0):
        self.fn = fn
        self.varia_z = varia_z
        self.neutro = neutro
        self.minimo = minimo

    def __call__(self, zn):
        return self.fn(zn)


def _cierre(boca, hombro, tramo):
    """El cierre, común a los tres cuellos. `tramo` es qué parte de lo que
    queda por encima del hombro se usa para cerrar; el resto sigue recto."""
    largo = max(1e-6, (1.0 - hombro) * tramo)

    def fn(zn):
        if zn <= hombro:
            return 1.0
        t = (zn - hombro) / largo
        if t >= 1.0:
            return boca
        return 1.0 - (1.0 - boca) * t * t * (3.0 - 2.0 * t)
    return fn


def _hecho(p, tramo):
    boca = max(0.0, min(1.0, float(p["boca"])))
    hombro = max(0.0, min(0.99, float(p["cuello_hombro"])))
    if boca >= 0.999:
        return ninguno(p)          # una boca entera no es un cuello
    return Cuello(_cierre(boca, hombro, tramo), True, False, boca)


def ninguno(p):
    return Cuello(lambda zn: 1.0, False, True, 1.0)


def suave(p):
    """Jarrón: el hombro se toma toda la altura que le queda."""
    return _hecho(p, 1.0)


def abrupto(p):
    """Hombro marcado y cuello corto: cierra en el primer 45%."""
    return _hecho(p, 0.45)


def botella(p):
    """Gollete: cierra pronto y sube recto un buen tramo."""
    return _hecho(p, 0.25)


CUELLOS = {
    "ninguno": ("Sin cuello", ninguno),
    "suave": ("Suave", suave),
    "abrupto": ("Hombro marcado", abrupto),
    "botella": ("Botella", botella),
}
