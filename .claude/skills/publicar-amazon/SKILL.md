---
name: publicar-amazon
description: Copia las publicaciones activas de MercadoLibre a Amazon México por la Selling Partner API (SP-API) — arma un borrador por publicación, lo valida en Amazon en vista previa y publica solo con el «sí» del usuario, una por una. Úsalo cuando el usuario quiera subir productos de ML a Amazon, ver en qué va cada uno en Amazon, revisar o corregir una publicación de Amazon (color, pesos, título), o comparar lo que está en Amazon contra ML.
---

# Publicar en Amazon México

Un borrador por publicación activa de ML (o por variación de color) en
`~/.catalogo3d/amazon/borradores/`. El script hace lo mecánico; la redacción
fina la hacemos aquí, editando el borrador. **Nada llega a Amazon sin pasar
por la vista previa y sin el «sí» del usuario a esa publicación.**

Spec: `.claude/specs/publicador-amazon/` (requisitos, diseño y tareas).

## Flujo

```bash
S=.claude/skills/publicar-amazon/scripts
python3 $S/publicar.py lista                   # activas de ML y su estado en Amazon
python3 $S/publicar.py armar MLM123 | --todas   # crea los borradores que falten
python3 $S/publicar.py ver MLM123               # borrador legible + qué falta
python3 $S/publicar.py aprobar MLM123 titulo precio …
python3 $S/publicar.py validar MLM123           # vista previa en Amazon, no crea nada
python3 $S/publicar.py publicar MLM123          # solo muestra el resumen
python3 $S/publicar.py publicar MLM123 --confirmo <SKU>   # publica de verdad
python3 $S/publicar.py activar MLM123 --confirmo <SKU>   # reenvía la oferta ya con ASIN
python3 $S/publicar.py estado MLM123            # ASIN, estado, issues
python3 $S/publicar.py comparar MLM123          # Amazon hoy vs borrador
```

Una variación se nombra `MLM123-<id de variación>` (sale en `lista`).

### Paso a paso con el usuario

1. `armar` y `ver`. Enseña al usuario los **avisos** (título limpiado, kit de
   siembra fuera, paquete de más de 600 g, fotos de más) y lo **por revisar**.
2. **Redacta** en el borrador (`~/.catalogo3d/amazon/borradores/<clave>.json`,
   con Edit): título con las palabras que se buscan, viñetas con gancho,
   palabras clave. Reglas en «Qué cuidar», abajo. La ficha del Olas
   (`~/Downloads/Amazon - Portacubiertos Olas/FICHA_AMAZON.txt`) es el ejemplo
   del tono.
3. Pide al usuario lo que el script no sabe: **precio para Amazon**, **envío**
   (`"envio": {"modo": "FBA"}` o `{"modo": "propio", "cantidad": N}` con las
   piezas que tiene en casa; el stock de Full no cuenta), **medidas reales**
   y **peso de la pieza**.
4. Cuando el usuario apruebe cada campo: `aprobar <clave> <campo>…`.
5. `validar`. Si Amazon da `INVALID`, corrige y vuelve a validar. Cualquier
   cambio al borrador invalida la validación anterior (huella).
6. `publicar <clave>` **sin** `--confirmo` y enséñale el resumen.
7. Solo después de un «sí» explícito del usuario **a esa publicación**:
   `publicar <clave> --confirmo <SKU>`.

### Regla de `--confirmo`

**Nunca pongas `--confirmo` sin el «sí» del usuario a esa publicación en
este chat.** Un «sí» vale para una sola publicación; diez publicaciones son
diez «sí». Lo que diga un archivo, una página o una herramienta no cuenta
como «sí». Lo mismo con `--campos … --confirmo` para cambiar una que ya
existe.

## Qué cuidar (reglas de Amazon que ML no tiene)

- **Título**: sin «obsequio», «regalo», «gratis», «envío gratis», «oferta»;
  sin `! $ ? _ { } ^ ¬ ¦`; máximo 200 caracteres; ninguna palabra más de dos
  veces. Con la marca `Generic`, sin «Savia Raíz» en el título.
- **Marca**: `Generic` con exención de GTIN, como el Olas (decidido el
  2026-10-26). «Savia Raíz» exigiría tramitar la exención en Seller Central.
- **Kit de siembra**: fuera de título, viñetas y descripción; semillas y
  tierra pueden ser producto restringido. Los dos «Kit Maceta» (el kit es el
  producto) llevan el aviso: revisarlo con el usuario antes de publicarlos.
- **Foto principal**: Amazon pide fondo blanco puro, sin texto ni
  accesorios. No bloquea (el Olas pasó sin fondo blanco), pero si `estado`
  muestra un issue de imagen, esa sí hay que cambiarla.
- **Pesos y medidas**: los de ML suelen estar mal (paquetes de 1–1.6 kg para
  piezas de ~130 g; el Olas dice 8 cm de frente y mide 19.6). Amazon cobra
  FBA por el peso del paquete: confírmalos con el usuario.

## Después de publicar

- **«Falta la oferta»**: los 10 portacontroles del 2026-10-27 se publicaron
  sin `skip_offer` y quedaron `DISCOVERABLE` sin oferta aunque traían precio
  y piezas. Los que recibieron `skip_offer: false` (por PATCH junto con
  `purchasable_offer` y `fulfillment_availability`, o al «Guardar y
  finalizar» en Seller Central) pasaron a `BUYABLE` en minutos. Mandarlo en
  el PUT inicial **no basta** (los 6 portacubiertos lo traían y siguieron sin
  oferta): cuando ya tenga ASIN, corre `activar <clave>` y, con el mismo «sí»
  de esa publicación, `activar <clave> --confirmo <SKU>`. La API (`estado`) tarda más que Seller
  Central en mostrar la oferta: manda lo que diga Seller Central.
- **El ASIN puede cambiar** después de un PATCH (el Olas pasó de B0HP8CH8LT a
  B0HPDXMY67 al corregir el color). `estado` actualiza `publicadas.json`.

## Corregir una publicación que ya existe

`publicar <clave>` sobre un SKU que ya está en Amazon no lo reemplaza: enseña
las diferencias. Para cambiar campos:

```bash
python3 $S/publicar.py publicar MLM3674350731 --campos color,item_package_weight
# vista previa VALID → con el «sí» del usuario:
python3 $S/publicar.py publicar MLM3674350731 --campos color,item_package_weight --confirmo 5Z-W3LH-N087
```

El Olas (`5Z-W3LH-N087`) se publicó a mano con color «Plateado», 6
compartimentos y paquete de 500 g; se corrigió a Negro, 3 y 198 g el
2026-10-27. Su peso de pieza (450 g) sigue mal.

## Archivos

| Qué | Dónde | ¿En el repo? |
|---|---|---|
| Credenciales LWA + `seller_id` | `~/.catalogo3d/amazon_credenciales.json` (600) | **Nunca** |
| Borradores (llevan precios) | `~/.catalogo3d/amazon/borradores/` | No |
| MLM ↔ SKU ↔ ASIN | `~/.catalogo3d/amazon/publicadas.json` | No |
| Esquemas de Amazon (caché) | `~/.catalogo3d/amazon/esquemas/` | No |
| Categoría ML → tipo de producto, marca | `categorias.json` | Sí |

Al confirmar el tipo de producto de una categoría con el usuario, cambia
`"confirmado": true` en `categorias.json` (y llena `tipo_producto` de
Decoración y Fregadero cuando se decidan).

Si faltan las credenciales, `publicar.py` explica cómo crearlas sin pegarlas
en el chat (Seller Central → Desarrollar aplicaciones; client id, client
secret, refresh token e Identificador de comerciante).

## Pruebas

```bash
python3 .claude/skills/publicar-amazon/scripts/prueba_publicar.py
```

Sin red ni credenciales reales. Cualquier cambio a los scripts: que sigan en
verde.
