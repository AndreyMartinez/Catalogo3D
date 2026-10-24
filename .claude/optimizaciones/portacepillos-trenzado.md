# Portacepillos Trenzado Doble

Archivo: `own design 3d/Pruebas de productos/Portacepillos_Trenzado.3mf` (+ `.png`, `.stl`)
Origen: **generador propio**, el mismo del Portacubiertos Trenzado
(`generadores/portacubiertos_trenzado.py`) en chico. Registro del grande:
[portacubiertos-trenzado.md](portacubiertos-trenzado.md).

    python3 generadores/portacubiertos_trenzado.py --salida "<carpeta>" \
        --nombre Portacepillos_Trenzado --largo 144 --alto-vaso 85 \
        --alto-bandeja 54 --alto-frente 27

## v1 (10-23) — «hazlo más pequeño… que sea para guardar porta cepillos»
El usuario vio la tarjeta del Portacubiertos Trenzado v10 («me re encantó») y lo pidió
más chico para portacepillos. Misma forma; medida tomada del Portacepillos02RAPIDO
(vaso Ø61.5 × 95, bandeja 144 × 79).

- `--largo 144`: `ajustar_al_largo` angosta los vasos parejo → radios 29.7 / 33.0 / 24.0
  (piso / panza / boca), **66 × 85 mm**, boca de 48 mm; costillas 16 → **12** (mismo ancho
  cada una). Bandeja 54 mm atrás / 27 al frente (×0.83, igual que los vasos).
  Pared, labio, separación, holgura y rendijas de 2.2 mm sin cambio.
- Juego armado **143.8 × 75.3 × 88.1 mm**. Precheck aprobado (el usuario hizo renders
  y pidió publicar).

| Juego (CLI, perfil embebido) | Tiempo | Peso | Costo |
|---|---|---|---|
| Portacubiertos v10 (2 vasos 92 × 100) | 6 h 33 | 211.8 g | $51.75 |
| **Portacepillos v1 (2 vasos 66 × 85)** | **3 h 55** | **120.5 g** | **$36.50** |

Costo = g × 167 $/kg + paquetería $16.38. Un juego por plato (sobra plato para 2).

## Publicación
- 2026-10-23: **MLM3700062373** «Portacepillos De Baño Trenzado Doble Más Regalos Negro»,
  $219, 3 u, premium (gold_pro), envío gratis, despacho propio (xd_drop_off), paquete
  20×16×11 / 300 g, categoría MLM189301, 5 fotos (renders del usuario; principal la de
  fondo blanco). Publicada por API (`POST /items`; la cuenta es de modelo de producto
  de usuario: va `family_name`, el campo `title` lo rechaza).

## Pendiente
- **Flex no quedó activo** (tags `self_service_out`): activarlo a mano como en el gato.
- Imprimir el primer juego antes de que entre la primera venta; confirmar que la boca de
  48 mm aguanta 2 cepillos + pasta y que no se voltea con cepillos eléctricos.
- Platos con 2 juegos (cabe en 256 mm) para bajar tiempo por juego: sin probar.
