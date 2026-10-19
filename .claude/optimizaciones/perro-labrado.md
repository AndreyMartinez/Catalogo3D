# Perro labrado — labrador sentado low-poly

Archivo: `own design 3d/Perro labrado.3mf`
Origen: MakerLab «Image to 3D v2» (`quant.obj`), 145k caras, arista mediana 0.32 mm
(malla densa con facetas planas). Traía escala anisotrópica propia 2.319/1.835/1.936.
Respaldo original: `Perro labrado.3mf.bak` (v0).

## Feedback
- 2026-10-18 — Mejorar la panza con el soporte árbol, la cola se daña un poquito,
  forma más tierna, más grande para la caja (20×16×11), todo proporcional.
- 2026-10-18 — Rechazó la versión con cabeza +30 %, cuello −8 mm y hocico chato
  («se ve terrible, quedó cabezón»). Quiere la forma original, **un poco gordita y
  pareja**, proporcional y elegante («es para vender»). Siempre mostrar el render
  antes de escribir el archivo.

## Diagnóstico (v0, 70×184×145 mm)
- Cola: ~52 mm, punta de 1.4 mm de ancho; la raíz (y local 39–50) quedaba 2–6 mm en
  el aire → volado colgando del árbol: es lo que se dañaba.
- Panza/pecho: la parte de abajo sube en rampa ~55° de la vertical desde los muslos
  hasta el pecho (z 5 → 49 mm); todo eso cuelga del árbol entre las patas.
- 13 % del área con volado >30° bloqueada por la propia malla (pecho, orejas,
  muslos): `support_on_build_plate_only=0` ya venía bien.
- Laminado CLI del original (0.20 mm, 2 piezas): 5 h 50 m, 216 g (108 g c/u).

## v1 (2026-10-18)
Malla reescrita en mm de mundo (transform de escala 1), script en el scratchpad
(`deform2.py` + `escribir.py`):
- **Cola**: fondo bajado a la cama desde la raíz (apoyo completo y=44–72), 20 % más
  corta, punta 50 % más gruesa (ancho mínimo ~13 mm).
- **Gordito parejo**: inflado por normal suavizada (300 pasadas de Laplace), 1.5 mm en
  todo + 1.5 mm extra en tronco (sin cabeza ni patas bajas), campo de empuje suavizado,
  base pegada a la cama sin mover; 0 caras invertidas, cerrada.
- **Escala uniforme ×1.07** → **77×189×157 mm**: entra acostado en la caja 20×16×11.
- **Perfil**: capa 0.12, techo/piso 8/5, soporte `tree_organic`, umbral 30→40°,
  interfaz superior 2→3 capas, espaciado de interfaz 0.5→0.3 (panza más lisa),
  separación XY 0.35→0.5, brim `outer_only` 3 mm (el auto de 5 mm chocaba entre perros).
  Sin planchado (las facetas no tienen techos planos que valga la pena).
- **Plato: 2 → 3 perros.** En fila no caben: el árbol bajo los muslos sale ~10 mm por
  los costados (llegó a X=262). El del medio va girado 180° y corrido 55 mm en Y (su
  cadera junto a las colas de los otros): 226 mm de ancho, 9 mm entre hulls.
- Miniatura del plato regenerada (matplotlib) y `slice_info.config` del laminado CLI.

| Versión | Piezas/plato | Tiempo plato | Peso plato | Por pieza | Material/pieza |
|---|---|---|---|---|---|
| v0 (0.20 mm) | 2 | 5 h 50 m | 216 g | 2.9 h · 108 g | $18.0 |
| v1 (0.12 mm, gordito +7 %) | 3 | 20 h 35 m | 501 g | 6.9 h · 167 g | $27.9 |

| v2 (0.16 mm, relleno rayo 10 %) | 3 | 11 h 02 m | 227 g | 3.7 h · 76 g | $12.6 |

(Material a 167 $/kg, sin paquetería. Medido por CLI de Bambu.)

## v2 (2026-10-18) — optimización
Respaldo de v1: `Perro labrado.3mf.v1.bak`. Misma malla y plato; solo perfil:
capa 0.12→**0.16**, techo/piso 8/5→6/4, relleno grid 15 %→**lightning 10 %**.
Variantes laminadas por CLI (plato de 3): 0.20+rayo 8 h 56 m/215 g; 0.12+rayo
14 h 14 m/232 g; 0.16+adaptive cubic 8 % 13 h 04 m/337 g. El rayo es lo que baja el
peso (en una figura solo sostiene el lomo); eligió 0.16+rayo.
- Pidió «un poco más alto»: no entra en la caja 20×16×11 (va justo, 157 de 160) y
  girado de lado tampoco gana — la diagonal cabeza–punta de cola es más larga.
  Se quedó en 157 mm.

## Pendiente
- Imprimir y ver si la panza sale limpia con organic + interfaz densa y si la cola ya
  no se daña.
- Confirmar en la impresión que el relleno rayo no deja hundido el lomo/cabeza.
