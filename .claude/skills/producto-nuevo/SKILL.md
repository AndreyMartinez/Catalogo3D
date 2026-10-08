---
name: producto-nuevo
description: Descubre, diseña y lanza un producto nuevo de impresión 3D a partir de datos reales de mercado (MercadoLibre México y Amazon México) — competencia, precios, comentarios y publicaciones con «+100 vendidos» — y le da seguimiento desde que se diseña hasta semanas después de publicado para decidir si escalar, potenciar o retirar. Úsalo cuando el usuario pida buscar productos nuevos, analizar el mercado de una categoría, proponer ideas/diseños para vender, iterar un producto nuevo, o revisar si un lanzamiento funcionó. Trabaja por fases con pausas para decidir juntos.
model: claude-opus-5-5
argument-hint: "[categoría o slug] — vacío para ver el tablero"
---

# /producto-nuevo — del dato de mercado a la pieza que se vende

Este skill está pensado para **Opus 5.5** (el `model:` de arriba lo fija). Si al
cargarlo notas que corres con otro modelo, dilo en una línea y pregunta si
seguir; no lo hagas en silencio.

Es un proceso **conjunto y por fases**. Cada fase termina en una pausa donde el
usuario decide; no encadenes dos fases sin su visto bueno. Todo lo que se
produce se guarda en `.claude/productos/` del **repo principal** (el script lo
resuelve solo aunque corras en un worktree) para retomarlo entre sesiones.

```
0 Arranque → 1 Mercado → 2 Diez propuestas → 3 Diseño e iteración
          → 4 Prototipo impreso → 5 Publicación → 6 Seguimiento (sem 2/4/6) → veredicto
```

## 0. Arranque (siempre)

```bash
python3 .claude/skills/producto-nuevo/scripts/tablero.py ver
```

- Si hay productos en curso, muéstralos primero: lo que toca hoy suele ser
  seguir uno (una revisión vencida, una iteración pendiente) antes que abrir
  otro. Pregunta con `AskUserQuestion` si no es obvio.
- Lee **`.claude/mercado/estudio-de-mercado.md`** (lo mantiene el skill
  `estudio-mercado` cada domingo): hallazgos, hipótesis abiertas, costos
  reales (§3) y competencia vigente. No repitas lo que ya está medido ahí; si
  una propuesta toca una hipótesis de su §4, dilo. Lee también
  `.claude/mercado/competencia/` si hay una semana reciente: es tu punto de
  partida en la fase 1.
- Lee las memorias del proyecto que aplican: las dos piezas que se fabrican,
  ventas por categoría, estilo origami, low-poly, soportes. El **costo** sale
  de `config.json` (`precio_kg`, `paqueteria`), que debe coincidir con el §3
  del estudio; si no coincide, gana el estudio y corrige el config.
- **Tus ventas son el primer dato de mercado.** Están en
  `~/.catalogo3d/ml_datos.json` (las baja `colecta-full`). `tablero.py ver`
  imprime la línea base por categoría; si los datos tienen más de 7 días,
  ofrece refrescar con
  `python3 .claude/skills/colecta-full/scripts/traer_datos.py --dias 90`.

Contexto de negocio (verifícalo si pasó tiempo): marca **Savia Raíz**,
MercadoLibre México, precio típico **$198–219 MXN** con «regalos sorpresa /
obsequio de siembra», impresora Bambu **P2S** (placa 256×256×256). Categorías
con venta: **portacontroles** (la mitad de todo), **portacubiertos**,
**portalápices**, **figuras de animales** origami; portacepillos y floreros
como satélites.

## 1. Mercado — con el navegador

Lee primero `referencias/mercado.md` (dónde buscar, qué significa cada señal,
qué capturar). En corto:

- Usa **Claude in Chrome** (el navegador del usuario); si no está conectado,
  el navegador integrado. Lee con `get_page_text` / `find`; capturas solo para
  juzgar fotos y estética de la competencia.
- Por categoría: 2–4 búsquedas con las palabras del comprador, más «Más
  vendidos» de ML y Best Sellers de Amazon.
- Captura 15–25 publicaciones por categoría. Las de **«+100 vendidos»** o más
  (ML) y **«más de 100 comprados el mes pasado»** (Amazon) son las que mandan.
- De las 3–5 más fuertes abre la publicación y lee **opiniones de 1–3
  estrellas y preguntas**: ahí está el hueco que vamos a llenar.
- Explora también **adyacentes** que se resuelvan con lo que ya sabemos
  fabricar (`referencias/limites-de-diseno.md`): baño, escritorio, cocina,
  entrada de la casa, mascotas, plantas.
- Solo lectura: no inicies sesión, no compres, no agregues al carrito, no
  hagas preguntas en publicaciones, no aceptes banners más allá de lo esencial.

Guarda en `.claude/productos/investigacion/AAAA-MM-DD-<categoria>.md`: la tabla,
los dolores **resumidos en tus palabras** (no copies reseñas) y una conclusión
de 5 líneas — qué vende, a qué precio, de qué se queja la gente, dónde está el
hueco.

**Pausa 1.** Por categoría: cuántas publicaciones con +100, banda de precio, 3
dolores repetidos, dónde ves oportunidad. Pregunta en qué categorías enfocar.

## 2. Diez propuestas

Lee `referencias/limites-de-diseno.md` **antes** de proponer. Cada propuesta
usa la ficha y la rúbrica de `referencias/ficha-propuesta.md`. Reglas:

- **Diez**, repartidas entre las categorías elegidas; al menos 2 que mejoren
  algo que ya vendes (salen rápido, arriesgan poco) y al menos 2 adyacentes.
- Cada una nace de un dato: una publicación con +100 vendidos **y** un dolor de
  sus comentarios. Sin dato no es propuesta, es ocurrencia — márcala así.
- Estética de la línea: **elegante, moderna, minimalista**. Una idea de forma
  fuerte por pieza (una silueta, un acabado), no cinco adornos.
- Semáforo de factibilidad honesto (verde / amarillo / rojo) según el
  documento de límites. Un rojo puede entrar si el dato es muy bueno; dilo.
- Costo = `gramos / 1000 × precio_kg + paqueteria` (de `config.json`). La
  paquetería fija castiga lo chico.

Preséntalas como **artifact** (las 10 fichas, la tabla de puntajes ordenada y,
para las verdes que el motor resuelve, un render rápido con
`generadores/crear.py`).

**Pausa 2.** El usuario elige 1–3. Regístralas:

```bash
python3 .claude/skills/producto-nuevo/scripts/tablero.py nuevo <slug> \
    --nombre "Nombre" --categoria portacontroles \
    --origen investigacion/AAAA-MM-DD-portacontroles.md
```

## 3. Diseño e iteración

Cada producto tiene `.claude/productos/<slug>.md` (lo crea `tablero.py nuevo`):
la ficha elegida, cada ronda y cada decisión con su porqué.

- **Primero la vía barata.** Recipiente → motor (`generadores/crear.py`,
  recetas en `disenos.py`). Referencia con caras planas → poliedro dedicado
  como `huevo_lowpoly.py`. Figura → **no la modeles a mano**: modelo base con
  licencia comercial y adáptalo (memoria `estilo-origami-facetado`).
- Pide **medidas reales** de lo que va dentro (controles, cubiertos, cepillos,
  celular) antes de fijar ranuras. No las supongas.
- Cada ronda: render lado a lado contra la referencia del mercado (cámara
  ~30° de elevación, color de la foto), peso, costo, voladizos, copias por
  placa. **Un cambio de concepto por ronda.**
- Antes de cerrar, pásalo por `/transform` (perfil, placa llena, soporte); no
  repitas aquí esa receta.

```bash
python3 .claude/skills/producto-nuevo/scripts/tablero.py fase <slug> diseno --nota "ronda 3: ..."
```

**Pausa 3.** El usuario aprueba la versión a imprimir.

## 4. Prototipo impreso

El usuario imprime. Registra lo real, no lo estimado:

```bash
python3 .claude/skills/producto-nuevo/scripts/tablero.py fase <slug> impreso \
    --gramos 168 --horas 5.9 --nota "pelusa en filete inferior; cabe control Samsung"
```

Pide foto. Defecto → vuelve a 3 (o a `optimizar-pieza`). Confirma que los
objetos reales entran y que se ve como el render.

## 5. Publicación

- Título con las palabras que usan los +100 vendidos de la investigación. Propón
  3 y que elija.
- Precio dentro de la banda medida, con costo y margen a la vista.
- Fotos: la pieza **en uso** y una que muestre el diferenciador que salió de
  los comentarios.
- **La publicación la crea el usuario** en ML; tú no publicas. Cuando exista:

```bash
python3 .claude/skills/producto-nuevo/scripts/tablero.py publicar <slug> MLM1234567890 --precio 198
```

## 6. Seguimiento y veredicto

`tablero.py ver` marca las revisiones vencidas (semanas 2, 4 y 6 desde
publicar). Para revisar uno:

1. Refresca ventas (`colecta-full/scripts/traer_datos.py`).
2. `tablero.py ver <slug>` cruza las ventas de esa publicación contra la
   **mediana de tus publicaciones de la misma categoría** (unidades/semana).
3. Si el usuario quiere, mira la publicación en el navegador: visitas,
   preguntas, posición en la búsqueda principal.

| A la semana 4 | Veredicto | Qué hacer |
|---|---|---|
| ≥ mediana de su categoría | **escalar** | Full, colores, variante de tamaño |
| 30 % – mediana | **potenciar** | título/fotos/precio primero; luego una variante |
| < 30 % de la mediana | **iterar** o **retirar** | visitas sin ventas → precio o foto; sin visitas → demanda o título |

Umbrales en `config.json`. Distingue visitas sin venta (problema de oferta) de
cero visitas (demanda o búsqueda). Con menos de 8 ventas el número es ruido:
dilo.

```bash
python3 .claude/skills/producto-nuevo/scripts/tablero.py veredicto <slug> potenciar --nota "..."
```

Al cerrar un producto, escribe en su archivo **qué aprendimos**: de eso se
alimenta la siguiente ronda de propuestas. Y llévalo al estudio vivo: el
producto entra en §5 («Productos en desarrollo») al publicarse, y su veredicto
pasa a §2 (hallazgo, con su nivel de evidencia) al cerrarse. Así la rutina del
domingo lo vigila sin que nadie se acuerde.

## Dónde vive cada cosa

| Qué | Dónde |
|---|---|
| Tablero (estado de todos) | `.claude/productos/tablero.json` |
| Un producto: ficha, rondas, decisiones | `.claude/productos/<slug>.md` |
| Investigaciones de mercado | `.claude/productos/investigacion/` |
| Umbrales y palabras por categoría | `.claude/skills/producto-nuevo/config.json` |
| Ventas reales | `~/.catalogo3d/ml_datos.json` (de `colecta-full`) |
