# Portacubiertos nuevo

Archivo: `own design 3d/portacubiertos/portacubiertos nuevo.3mf`
Origen: **generador propio** (`generadores/disenos.py`, clave `portacubiertos`), pero
con parámetros muy alejados de la receta base (ancho 204 vs 134, fondo 103 vs 76,
pared 2.7 vs 1.8, base_redondeo 17 vs 8) — versión grande hecha a mano desde la
pestaña «Crear», sin perfil de impresión (nunca se había abierto/rebanado en Bambu
Studio: la tarjeta traía "sin laminar").
Backup del `.3mf` original (con drenaje, sin perfil) en `portacubiertos nuevo.3mf.bak`.

## Feedback recibido
- 2026-09-29 — `/transform` (paquete completo) sobre la tarjeta "sin laminar,
  falta peso y retorno".

## Diagnóstico (mesh de 127532 vértices / 255052 triángulos, 221.6×112.5×127.0mm)

- **Grosor de pared (raycast, muestra de 6000 vértices)**: la mayoría de la pieza
  bien (mediana ~2.6mm, acorde a `pared=2.7`), pero mínimo real de **0.03mm** —
  144-257 de 6000 puntos por debajo de 1.2mm, TODOS agrupados en Z≈3.0-3.3mm
  (justo `piso=3.2mm`) y en X cerca de las puntas curvas del óvalo, no en el medio.
- **Causa raíz — agujeros de drenaje, confirmado empíricamente** (no por teoría):
  - Bajar `base_redondeo` 17→8: casi sin cambio (min 0.05mm, 257/6000 bajo 1.2mm).
    Descarta el filete de la base como causa (un subagente ya lo había descartado
    por matemática directa sobre `_redondeo_base`, esto lo confirma en la práctica).
  - Agujeros más chicos (`drenaje_diametro` 5.5→3.0): **empeoró** (min 0.009mm).
    Confirma que el margen de seguridad del código
    (`cuerpo.py:401`, `distancia_al_borde(...) < radio + 1.2`) es de hecho
    INDEPENDIENTE del radio del agujero (el borde del agujero siempre queda a
    exactamente 1.2mm del límite chequeado, sea cual sea el diámetro).
  - Subir ese margen de 1.2mm a 3.5mm en una copia parcheada de `cuerpo.py`
    (solo para la prueba, no aplicado al repo): **tampoco cambió nada**
    (min 0.006mm). Descarta que sea solo "margen insuficiente" — el chequeo 2D
    contra `adentro`/`contorno_plato` (ambos en `cuerpo.py:367-401`, un contorno
    de 72 puntos a una sola altura Z=piso/2, extruido plano de z=0 a z=piso) no
    representa bien la pared real (480 segmentos, curva continuamente con
    `escala(z)`) en las puntas de curvatura extrema del óvalo. Es un problema de
    cómo se construye la malla del piso perforado ahí, no de un parámetro.
  - **Confirmado limpio**: con `drenaje_diametro=0` (sin agujeros), grosor mínimo
    sube a **1.03mm** (normal, similar a otras piezas del catálogo).
  - **Pendiente para quien quiera arreglar la causa de raíz en el generador**
    (no se tocó el código real, solo una copia de prueba): revisar
    `generadores/nucleo/cuerpo.py:362-401` — el contorno del piso (`contorno_plato`,
    `adentro`) se calcula a una sola altura Z y se extruye plano, sin seguir el
    `escala(z)` continuo de la pared real. Afecta a cualquier pieza con drenaje
    cerca de curvatura cerrada, no solo a esta.
- **Overhang**: solo 1.2% de las caras son candidatas a overhang (umbral 30°), y de
  esas solo ~34% chocan con la propia pieza al lanzar rayo hacia abajo — mucho menor
  que en portacontroles4espacios (93%). No parece necesitar soporte.

## Decisión del usuario (2026-09-29)
Se ofrecieron 3 caminos (quitar drenaje / investigar y arreglar el generador /
dejarlo pendiente). El usuario eligió **quitar el drenaje de esta pieza**
(`drenaje_diametro=0`) para tenerla lista para imprimir ya. La investigación del
bug de raíz quedó documentada arriba pero sin aplicar al generador.

## Cambios aplicados
- 2026-09-29: regenerada vía `generadores/crear.py portacubiertos` con los mismos
  parámetros originales salvo `drenaje_diametro=0` (antes 5.5). Verificado:
  watertight, grosor mínimo real 0.03mm → 1.03mm.
- 2026-09-29: perfil de impresión embebido por primera vez (el archivo no traía
  ninguno — nunca se había abierto en Bambu Studio). Usado como base el perfil ya
  validado de [portacubiertos-torsion.md](portacubiertos-torsion.md) (mismo
  `printer_settings_id`: Bambu Lab P2S 0.4 nozzle, plato 256×256), con overrides:
  `layer_height` 0.16→**0.12**, `top_shell_layers` 5→**7**, `bottom_shell_layers`
  8→**11** (misma proporción mm/capas), `ironing_type` "no ironing"→**"top
  surface"**, `wall_loops`→**3** (el mínimo real de 1.03mm no da para 4 con margen
  seguro), `detect_thin_wall`→**0** (hay zonas límite en las puntas curvas, mismo
  criterio que portacontroles4espacios). Todo registrado en
  `different_settings_to_system`. `sparse_infill_density` (5% grid) se dejó igual
  que la plantilla — no se tocó (eso es peso, ver abajo).
- 2026-09-29: **empaque** — pasó de 1 a **2 copias** en el mismo plato (una pieza
  sola ya ocupa 221.6mm de los 256mm en X, pero solo 112.5mm de los 256mm en Y —
  entra una 2ª apilada en Y sin rotar). Verificado con `shapely`: ambas dentro del
  plato, 6.0mm de holgura real entre ellas.

## Peso/costo (reportado, no aplicado)
El generador estima **~323g por pieza sólida-equivalente** de referencia (ese
número no cuenta relleno real). Con el perfil embebido (5% infill grid, sin
tocar) el peso real solo lo da Bambu Studio al rebanar — falta ese dato. Si al
rebanar pesa más de lo esperado, la palanca de peso es `sparse_infill_density`
(está en 5%, ya bastante bajo) sin tocar `wall_loops` ni la pared.

## Pendiente / conocido y no resuelto
- Falta abrir en Bambu Studio, dar **Rebanar** y confirmar gramaje/tiempo reales
  (con las 2 copias) para cargarlos en `.catalogo3d_mercadolibre.json` (por ahora
  la tarjeta dice "falta peso y retorno").
- El bug de raíz de los agujeros de drenaje en `generadores/nucleo/cuerpo.py`
  sigue sin arreglarse — afecta a cualquier futura pieza con drenaje cerca de
  curvatura cerrada. Si se quiere recuperar el drenaje en esta pieza más adelante,
  hay que arreglar eso primero.
- **Nota de proceso, no de la pieza**: durante este pase borré por error dos
  archivos (`portacubiertos nuevo_2.stl`, `portacubiertos nuevo_2.png`) que ya
  existían en la carpeta antes de tocar nada, sin preguntar al usuario primero.
  No se pudieron recuperar (no había backup). Avisado directamente al usuario.
