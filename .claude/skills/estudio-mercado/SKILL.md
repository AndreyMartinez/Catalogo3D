---
name: estudio-mercado
description: Rutina semanal de análisis de mercado del negocio en MercadoLibre — baja ventas reales, calcula las cifras de la semana, revisa la competencia en el navegador y escribe el reporte del domingo, actualizando el estudio de mercado vivo (.claude/mercado/estudio-de-mercado.md) que leen los demás skills. Úsalo cuando el usuario pida el resumen o análisis de la semana, el estudio de mercado, cómo van las ventas, qué producto conviene lanzar o mandar a Full, o cuando lo dispare la tarea programada del domingo.
---

# Estudio de mercado semanal

Produce cada semana, de lunes a domingo:

1. `.claude/mercado/datos/AAAA-Www.json` y `.md`: las cifras (las hace el script).
2. `.claude/mercado/competencia/AAAA-Www.json`: lo visto en la competencia.
3. `.claude/mercado/semanas/AAAA-Www.md`: el reporte para el usuario.
4. `.claude/mercado/estudio-de-mercado.md` actualizado: hallazgos, hipótesis y bitácora.

Lee primero el estudio vigente. Ahí están los hallazgos anteriores y lo que
quedó pendiente de validar; el reporte nuevo los confirma o los corrige.

## Paso 1 — Datos de ventas

```bash
python3 .claude/skills/colecta-full/scripts/traer_datos.py --dias 90
python3 .claude/skills/estudio-mercado/scripts/semana.py
```

`semana.py` toma la última semana cerrada (lunes a domingo). Si corre el
domingo, esa semana es la que termina hoy. Si los datos se bajaron antes de
que cerrara la semana, lo marca con ⚠️; dilo en el reporte.

**Si `traer_datos.py` falla por sesión** (token vencido, sin refresh_token):
NO intentes iniciar sesión ni autorizar la app en el navegador. Autorizar
OAuth es una decisión del usuario cada vez, y en una corrida programada no hay
quien la confirme. Sigue con los últimos datos guardados, márcalos como
viejos en el reporte, y pon arriba del todo qué tiene que hacer el usuario:
correr `colecta-full/scripts/login.py` (ver la sección «Sesión» de ese
skill). Con `offline_access` activado en la app de ML, el token se renueva
solo durante ~6 meses y esto no debería pasar.

## Paso 2 — Competencia (navegador, solo lectura)

Usa el navegador para buscar en mercadolibre.com.mx, sin iniciar sesión, las
búsquedas de las categorías que más venden y de las que se están evaluando.
Mínimo:

- `portacepillos`, `portacepillos familiar`
- `organizador control remoto`
- `organizador de cubiertos`
- `portalapices`

De cada búsqueda anota los primeros 10–15 resultados: título, precio, si dice
«Full», cuántos vendidos muestra, formato (doble, triple, compartimentos…) y si
la publicación es nuestra (vendedor Savia Raíz; el `seller_id` está en `~/.catalogo3d/ml_datos.json`). Guarda
`competencia/AAAA-Www.json` y compara contra la semana anterior: precios que
se movieron, competidores nuevos arriba, formatos que dominan.

Reglas: solo leer páginas públicas. No iniciar sesión, no comprar, no
preguntar a vendedores, no hacer clic en anuncios ni aceptar nada más que
rechazar cookies no esenciales. Si ML muestra captcha o bloquea, no lo
resuelvas: anótalo y sigue sin competencia esa semana.

## Paso 3 — Reporte de la semana

`.claude/mercado/semanas/AAAA-Www.md`, en este orden:

1. **Resumen en 5 líneas**: unidades contra semana anterior y contra el
   promedio de 4 semanas, la categoría que más se movió, y la única cosa que
   haría el usuario esta semana.
2. **Cifras**: pega las tablas de `datos/AAAA-Www.md`.
3. **Lo que cambió**: publicaciones con alerta `sube`, `baja`, `dormida`,
   `nueva`, con una explicación probable y su nivel de evidencia.
4. **Competencia**: lo relevante, no la lista entera.
5. **Hipótesis**: avance de cada una de la tabla del estudio (§4).
6. **Recomendaciones**: máximo 3, cada una con el dato en que se apoya y su
   nivel (medido / correlación / suposición). Si una recomendación depende de
   una suposición, dilo.

Con pocas unidades (menos de ~5 por publicación a la semana), una semana sola
no es tendencia: compárala con el promedio de 4 y no saques conclusiones de
un salto aislado.

## Paso 4 — Actualiza el estudio vivo

En `.claude/mercado/estudio-de-mercado.md`:

- Agrega la fila de la semana a la **Bitácora** (§8).
- Corrige los **Hallazgos** (§2) que los datos nuevos confirmen o contradigan.
  No borres la historia: si un hallazgo dejó de valer, márcalo y di desde qué
  semana.
- Mueve **Hipótesis** (§4) a hallazgos cuando queden medidas.
- Actualiza **Competencia** (§7) con el resumen vigente.
- Cambia la fecha de «Última actualización».

## Paso 5 — Avisa

Si corre como tarea programada, termina con un resumen corto para el usuario:
las 5 líneas del resumen y la ruta del reporte. Si faltó la sesión de ML,
eso va primero.

## Qué NO hacer

- No cambies precios, publicaciones, stock ni nada en la cuenta de ML. Este
  skill solo lee.
- No programes colectas ni envíos.
- No inventes cifras de competencia que no viste en pantalla.
