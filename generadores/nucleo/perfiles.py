#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Perfiles: cómo cambia el ancho de la pieza conforme sube.

Un perfil es una función z -> factor de escala (1.0 = sin cambio), con z
normalizado de 0 a 1. Se aplica a toda la sección, así que la pared conserva
su espesor.

Ojo con pasarse de intensidad: más de ~0.25 empieza a dar voladizos que
piden soporte.
"""

import math


class Perfil:
    """`angular`, si viene, es una función (z, θ) -> factor que se multiplica
    encima de `fn` columna por columna. Es lo que deja que una panza salga
    más de un lado que del otro; los perfiles de siempre no la llevan y la
    sección sigue escalando pareja."""

    def __init__(self, fn, varia_z=True, angular=None):
        self.fn = fn
        self.varia_z = varia_z
        self.angular = angular

    def __call__(self, z):
        return self.fn(z)


def recto(p):
    return Perfil(lambda z: 1.0, False)


def conico(p):
    """Base más angosta que la boca. Es lineal, así que no pide subdividir."""
    k = p["perfil_intensidad"]
    return Perfil(lambda z: 1.0 - k * (1.0 - z), False)


def invertido(p):
    """Boca más angosta que la base: se cierra arriba. También lineal."""
    k = p["perfil_intensidad"]
    return Perfil(lambda z: 1.0 - k * z, False)


def barril(p):
    """Panza a media altura."""
    k = p["perfil_intensidad"]
    return Perfil(lambda z: 1.0 + k * math.sin(math.pi * z))


def campana(p):
    """Se abre hacia arriba, con la curva acelerando."""
    k = p["perfil_intensidad"]
    return Perfil(lambda z: 1.0 - k + k * z * z)


def organico(p):
    """Panza abajo y boca recogida: la forma de huevo de las macetas bonitas.

    El máximo cae como al 40 % de la altura, no a la mitad, que es lo que
    hace que se vea asentada en vez de un barril.
    """
    k = p["perfil_intensidad"]
    # z·(1−z)^1.63 tiene el máximo en 0.38 y arranca con pendiente finita.
    # Un seno de z^0.8 también daba la forma, pero su derivada en z=0 es
    # infinita: la pared salía de la cama abriéndose de golpe y la pieza
    # pedía soportes desde la primera capa.
    pico = 0.38 * (1.0 - 0.38) ** 1.63
    return Perfil(lambda z: 1.0 + k * (z * (1.0 - z) ** 1.63) / pico
                  - 0.55 * k * z ** 1.6)


def cintura(p):
    """Estrechada a media altura: buen agarre."""
    k = p["perfil_intensidad"]
    return Perfil(lambda z: 1.0 - k * math.sin(math.pi * z))


def oleaje(p):
    """Panzas apiladas e inclinadas, como tela que se retuerce al subir.

    Cada panza es un anillo ladeado: su altura se corre `inclinación` (en
    fracción de la altura) hacia un lado y baja otro tanto del contrario, y
    el lado hacia el que se ladea gira `giro` vueltas de abajo a arriba. Por
    eso no se lee como un barril de varios pisos sino como la maceta que se
    tuerce.

    Con `reparto` la panza deja de dar la vuelta entera: los pliegues nacen
    en los dos extremos (en x) a la vez, bajan en curva hacia el centro y se
    apagan antes de juntarse. Ahí el ladeo ya no gira: es cuánto baja el
    pliegue del extremo al centro, y el giro no se usa.

    La onda arranca en cero sobre la cama y crece en el primer 18 % de la
    altura: así la base es el contorno tal cual, asienta plana y el filete
    del fondo no tiene que pelearse con una panza.
    """
    k = p["perfil_intensidad"]
    ondas = float(p.get("oleaje_ondas", 2.0))
    ladeo = float(p.get("oleaje_inclinacion", 0.10))
    giro = float(p.get("oleaje_giro", 0.5))
    dos_pi = 2.0 * math.pi

    def envolvente(z):
        t = min(1.0, max(0.0, z / 0.18))
        return t * t * (3.0 - 2.0 * t)

    reparto = float(p.get("oleaje_reparto", 0.0))
    desfase = float(p.get("oleaje_desfase", 0.0))

    def suave(a, b, x):
        t = min(1.0, max(0.0, (x - a) / (b - a)))
        return t * t * (3.0 - 2.0 * t)

    pliegues = _pliegues(p) if reparto > 0.0 else []
    # Cómo cae cada pliegue a lo largo. En 0 cae fuerte al salir del borde y
    # se va tendiendo; en 1 sale casi plano y se clava hacia abajo al final,
    # como gancho. La caída total es la misma: sólo cambia dónde se gasta.
    gancho = min(1.0, max(0.0, float(p.get("oleaje_gancho", 0.0))))

    def angular(z, theta):
        fase = z + ladeo * math.cos(theta - dos_pi * giro * z)
        ola = math.sin(dos_pi * (ondas * fase + desfase))
        if reparto > 0.0:
            # `u` es dónde cae la columna a lo largo: −1 en el extremo
            # izquierdo, 0 al centro del frente (y de la espalda), +1 en el
            # derecho. Cada pliegue se recorre desde su extremo: t = 0 en el
            # borde, 1 al centro, 2 en el extremo de enfrente.
            u = math.cos(theta)
            suma = 0.0
            for lado, z0, caida, alcance, fuerza, ancho in pliegues:
                t = 1.0 - lado * u
                tau = min(t / alcance, 1.0)
                curva = ((1.0 - gancho) * (1.0 - (1.0 - tau) ** 2)
                         + gancho * tau ** 3)
                cresta = z0 - caida * curva
                # Con gancho la caída se gasta al final, así que el pliegue
                # tiene que seguir vivo hasta ahí o se apaga antes de bajar.
                vida = 1.0 - suave(0.55 + 0.30 * gancho, 1.0, tau)
                if vida <= 0.0:
                    continue
                d = (z - cresta) / ancho
                if abs(d) < 3.5:
                    suma += fuerza * vida * math.exp(-d * d)
            ola = (1.0 - reparto) * ola + reparto * suma
        return 1.0 + k * envolvente(z) * ola

    return Perfil(lambda z: 1.0, True, angular)


def _pliegues(p):
    """Los pliegues sueltos del oleaje «desde los extremos».

    Cada uno es una cresta que nace en un extremo a la altura `z0`, baja
    `caida` conforme entra al frente —rápido al salir del borde y cada vez más
    tendida— y se apaga al llegar a su `alcance` (1 = el centro; más de 1 lo
    cruza). La sección es una campana de `ancho`: sólo empuja hacia afuera,
    como la tela, en vez del sube y baja de la onda.

    Con `oleaje_variacion` en 0 salen todos iguales y en espejo; subiéndolo,
    cada pliegue se corre de altura, cae distinto y llega más lejos o se
    corta antes. La semilla fija el sorteo, para que la misma pieza salga
    igual cada vez y se pueda probar otra con sólo cambiarla.
    """
    import random
    n = max(1, int(round(float(p.get("oleaje_ondas", 2.0)))))
    caida = float(p.get("oleaje_inclinacion", 0.10))
    variacion = float(p.get("oleaje_variacion", 0.0))
    corre = float(p.get("oleaje_desfase", 0.0))
    azar = random.Random(int(p.get("oleaje_semilla", 0)))
    paso = 0.92 / n
    salida = []
    for lado in (-1.0, 1.0):
        for j in range(n):
            def tirada(rango):
                return azar.uniform(-rango, rango) * variacion
            z0 = 0.97 - corre * paso - j * paso + tirada(0.12 * paso)
            salida.append((lado, z0,
                           max(0.0, caida * (1.0 + tirada(0.35))),
                           max(0.5, 1.1 + tirada(0.35)),
                           1.0 + tirada(0.25),
                           0.09 * (1.0 + tirada(0.25))))
    return salida


PERFILES = {
    "recto": ("Recto", recto),
    "organico": ("Orgánico", organico),
    "conico": ("Cónico", conico),
    "invertido": ("Cónico invertido", invertido),
    "barril": ("Barril", barril),
    "campana": ("Campana", campana),
    "cintura": ("Cintura", cintura),
    "oleaje": ("Oleaje", oleaje),
}
