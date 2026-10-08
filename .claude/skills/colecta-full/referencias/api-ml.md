# API de MercadoLibre: lo que usa este skill

Host: `https://api.mercadolibre.com`. Todo va con `Authorization: Bearer <token>`.

## Endpoints

| Para qué | Ruta |
|---|---|
| Quién soy (seller_id, site_id) | `GET /users/me` |
| Mis publicaciones | `GET /users/{seller_id}/items/search?search_type=scan` |
| Detalle de publicaciones (20 max) | `GET /items?ids=MLM1,MLM2,...` |
| Stock en Full | `GET /marketplace/inventories/{inventory_id}/stock/fulfillment?seller_id={id}` |
| Ventas | `GET /orders/search?seller={id}&order.status=paid&order.date_created.from=...&order.date_created.to=...` |
| Token | `POST /oauth/token` |

El `inventory_id` sale del detalle de la publicación: al nivel del ítem, o uno
por variante en `variations[].inventory_id`.

## Verificado y sin verificar

**Verificado en la documentación**: la ruta de stock fulfillment y sus campos
(`total`, `available_quantity`, `not_available_quantity`, `not_available_detail`);
que `/orders/search` pagina con `offset` + `limit`, que guarda 12 meses y que
como vendedor filtra las canceladas.

**Por confirmar contra la API real** (la documentación pública rechaza las
lecturas automáticas, así que esto viene de uso conocido, no de la doc):

- El nombre exacto de los filtros de fecha `order.date_created.from` / `.to`.
- Que `search_type=scan` devuelva `scroll_id` para vendedores chicos (con pocas
  publicaciones puede bastar `offset`).
- Si `/marketplace/inventories/...` exige que la app tenga algún alcance extra.

Si algo de esto falla en la primera corrida, el error trae el cuerpo de la
respuesta de ML: ahí dice el nombre correcto del parámetro. Es un arreglo de una
línea, no un rediseño.

## Token

Access token ~6 h; refresh token ~6 meses y de **un solo uso** — cada refresco
devuelve uno nuevo y hay que guardarlo (lo hace `ml_api.refrescar()`).

La app en developers.mercadolibre.com necesita `offline_access` para que venga
refresh token. Sin eso hay que re-autorizar cada 6 horas.
