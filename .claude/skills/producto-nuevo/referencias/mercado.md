# Cómo leer el mercado (MercadoLibre México y Amazon México)

## Dónde buscar

| Qué | URL |
|---|---|
| Búsqueda ML | `https://listado.mercadolibre.com.mx/<palabras-con-guiones>` |
| Búsqueda ML, más relevantes primero | (es el orden por defecto; no lo cambies a «menor precio») |
| Más vendidos ML | `https://www.mercadolibre.com.mx/mas-vendidos` → navegar a la categoría (Hogar, Muebles y Jardín → Organización, Decoración…) |
| Búsqueda Amazon | `https://www.amazon.com.mx/s?k=<palabras+con+mas>` |
| Best Sellers Amazon | `https://www.amazon.com.mx/gp/bestsellers/` → Hogar y Cocina → subcategoría |

Palabras de arranque por categoría (amplíalas con las que veas en los títulos
que más venden — esa es la forma en que busca el comprador):

- **Portacontroles**: organizador control remoto, porta controles, soporte
  controles tv, organizador sala control.
- **Portacubiertos**: escurridor cubiertos, organizador cubiertos fregadero,
  porta cubiertos cocina, cubiertero.
- **Portalápices**: portalapices escritorio, organizador escritorio, lapicero
  minimalista, porta plumas.
- **Figuras**: figura decorativa minimalista, escultura geométrica, adorno
  origami, figura animal decoración.
- **Adyacentes** (probar 1–2 por sesión): portacepillos, jabonera, porta
  audífonos, base celular escritorio, porta llaves entrada, organizador
  maquillaje/brochas, maceta minimalista, bandeja catchall, porta incienso,
  sujetalibros, organizador cargadores.

## Qué significa cada señal

| Señal | Dónde | Qué mide | Ojo |
|---|---|---|---|
| «+5 vendidos», «+25», «+50», «+100», «+500», «+1000», «+5mil» | ML, debajo del título o en la ficha | Ventas **acumuladas** de esa publicación, desde que existe | No dice en cuánto tiempo. Una +100 de hace 3 años pesa menos que una +100 nueva. Si se puede, mira la fecha de la opinión más vieja. |
| «MÁS VENDIDO» / «N.º 1 en …» | ML | Lidera su subcategoría ahora | Es la señal más fresca de ML |
| «FULL» (rayo verde) | ML | Stock en bodega de ML | Quien vende mucho suele estar en Full; sin Full y +100 = demanda fuerte a pesar de envío lento |
| «Tienda oficial» | ML | Marca registrada | Compite por confianza, no por precio |
| «Más de 100 comprados el mes pasado» | Amazon | Ventas del **último mes** | Es la mejor señal de velocidad que hay; no existe en ML |
| Estrellas y número de calificaciones | ambos | Satisfacción y volumen | Muchas opiniones = muchas ventas, aun sin etiqueta |
| Ranking «N.º X en Hogar y cocina» | Amazon, ficha | Posición en la categoría | Menor = más vende |

**Umbral para estudiar a fondo**: ML +100 o MÁS VENDIDO; Amazon +100/mes o
≥ 200 calificaciones.

## Qué capturar (una fila por publicación)

```
| # | Sitio | Título (corto) | Precio | Señal de venta | ★ (n) | Full | Material | Qué la hace distinta | Link |
```

- **Material**: plástico inyectado, madera, bambú, metal, acrílico, **impresión
  3D** (se nota: capas visibles, «hecho en 3D», colores PLA). Las 3D con +100
  son la prueba directa de que el formato vende.
- **Qué la hace distinta**: una frase — «giratorio», «4 espacios + celular»,
  «bambú con cajón», «forma de nube».
- Precio sin envío. Si hay variantes de precio, el más bajo.

## Leer opiniones y preguntas (de las 3–5 más fuertes)

Abre la publicación → «Opiniones» → filtra 1–3 estrellas si hay filtro;
si no, baja hasta encontrarlas. Busca **repeticiones**, no anécdotas:

- **Tamaño**: «no cabe el control de Roku / Samsung», «muy chico», «muy alto».
- **Estabilidad**: «se vuelca», «se resbala», «se mueve».
- **Calidad**: «se ve barato», «llegó roto», «huele», «olor a plástico».
- **Función**: «junta agua», «hongos», «no escurre», «difícil de limpiar».
- **Estética**: «no es como en la foto», «el color es distinto».

Las **preguntas** dicen lo que el comprador quiere y la publicación no
contesta: «¿caben 5 controles?», «¿viene en blanco?», «¿cuánto mide?».

Escribe cada dolor como: `dolor (n veces visto) — qué podemos hacer con la
pieza`. Nunca pegues reseñas completas; resume.

## Cómo navegar sin perder tiempo

Aprendido en la primera corrida (2026-10-07), con Claude in Chrome:

- **El navegador integrado no sirve para ML**: lo manda a «account-verification».
  Usa el Chrome del usuario (ya trae su sesión; solo lectura igual).
- **ML no pinta los resultados si la pestaña no está al frente.** Patrón que
  funciona: `navigate` → `wait 3` → `screenshot` (escala 0.2, solo para
  forzar el pintado) → `wait 3` → `javascript_tool`.
- `get_page_text` **no** sirve en los listados de ML (devuelve vacío o solo
  una reseña). Extrae con JS sobre `li.ui-search-layout__item`: título
  `a.poly-component__title`, vendidos con la regex `\+(\d+(mil)?)\s*vendidos`,
  precio = último `.andes-money-amount__fraction` (el de oferta).
- **La salida de `javascript_tool` se corta a ~1000 caracteres.** Devuelve
  primero el resumen (n resultados, cuántos con +100, precio p25/mediana/p75)
  y solo las filas con +100 en formato corto; guarda el arreglo en `window.__B`
  y pide el resto en una segunda llamada con `slice`.
- Opiniones en ML: `article` que contenga «Calificación N de 5». La página solo
  muestra las primeras; casi siempre son de 5 estrellas — no concluyas «no hay
  quejas» con eso.
- **Amazon es más rápido para dolores**: la ficha trae «Los clientes dicen»,
  un resumen de reseñas con los temas y su conteo (Tamaño(12), Calidad(41)…).
  Busca ese texto con JS y lee 700 caracteres desde ahí.
- En Amazon, `[data-component-type=s-search-result]`; «100+ comprados el mes
  pasado» aparece en pocos resultados — su ausencia no significa que no vende,
  mira el número de calificaciones.
- No hagas clic en anuncios (`click1.mercadolibre`, `publicidad.`): le cobra al
  anunciante. Navega a la versión orgánica (`/up/MLMU…`).
- Captura de pantalla solo para juzgar **fotos**: qué estilo de foto usan los
  que más venden (fondo blanco, en uso, ambiente).
- Si sale un muro de inicio de sesión o un CAPTCHA, para y avisa al usuario;
  no lo resuelvas.
- Si una página no carga o bloquea lecturas, anota «sin dato» en vez de
  inventar.

## Tus propias ventas como referencia

`tablero.py ver` imprime, por categoría, tus unidades/semana por publicación
(mediana). Úsalo para calibrar: si tu portacontroles vende 2/semana por
publicación con +100 en la vitrina, una categoría adyacente donde los líderes
apenas llegan a +25 no te va a dar más que eso.
