---
name: colecta-full
description: Planea el próximo envío a MercadoLibre Full leyendo las ventas y el stock reales del vendedor por la API oficial. Úsalo cuando el usuario pregunte cuándo programar la colecta, cuántas unidades mandar de cada diseño, qué le va a faltar en Full, o en qué orden imprimir para llegar a tiempo. También para revisar si le alcanza la capacidad de impresión antes de comprometerse con un envío.
---

# Planear la colecta a Full

Responde tres preguntas encadenadas: **cuándo** programar la colecta, **cuánto**
mandar de cada diseño, y **en qué orden imprimirlo** para que salga a tiempo.

Todo sale de datos reales: ventas y stock vienen de la API de MercadoLibre; el
peso y el retorno de cada pieza, del propio catálogo
(`.catalogo3d_mercadolibre.json`, junto a los diseños).

## Contexto de mercado

Antes de presentar el plan, lee `.claude/mercado/estudio-de-mercado.md`: ahí está qué categorías crecen, qué publicaciones están dormidas y qué productos están por entrar a Full (por ejemplo, el portacepillos 02RAPIDO). Úsalo para comentar el plan, no para cambiar los números: las cantidades salen de las ventas que baja este skill.

## Flujo

```bash
python3 .claude/skills/colecta-full/scripts/traer_datos.py --dias 90
python3 .claude/skills/colecta-full/scripts/plan.py
```

El primero baja y guarda; el segundo solo calcula. Si ya bajaste datos hoy, corre
solo `plan.py` — no le pegues a la API de más.

Si `traer_datos.py` se queja de sesión, mira «Sesión» abajo.

## Cómo interpretar la salida

El reporte trae cuatro bloques. Al usuario le importan en este orden:

1. **La fecha de colecta**. Sale del diseño que se queda sin stock primero, menos
   el lead time de Full, menos el colchón. Si dice «vas tarde», ya no hay fecha
   cómoda: la que da es «lo antes posible».
2. **Llegas / no llegas**. Compara las horas de impresión necesarias contra tu
   capacidad diaria. Si no llegas, da la `fecha_colecta_realista`: la primera
   fecha en la que sí tendrías todo impreso. **Esta es la parte que más le
   importa al usuario** — el problema que quiere resolver es comprometerse a un
   envío que luego no alcanza a imprimir.
3. **Qué mandar**, por diseño.
4. **Orden de impresión**, con la fecha en que queda lista cada tanda. Un
   ⚠️ marca que ese diseño se queda sin stock *antes* de que termines de
   imprimirlo: ahí ya hay venta perdida y conviene decírselo explícitamente.

## Lo que el cálculo no sabe

Dilo cuando presentes el plan, no lo escondas:

- **Las horas son estimadas**, no medidas. Salen de `peso_g ÷ gramos_por_hora`.
  Es una regla de dedo: una pieza con mucha superficie o soportes tarda bastante
  más de lo que su peso sugiere. Para horas reales hay que leer el tiempo del
  `.3mf` laminado (está en `slice_info.config`, junto al `used_g` que ya lee
  `catalog3d.py`) o ponerlas a mano en `horas_por_pieza` del `config.json`.
- **El plan imprime en fila**, una tanda tras otra. No modela varias piezas por
  placa, que es como se imprime de verdad; el plan va a salir conservador.
- **Con poco historial el promedio miente.** El reporte marca cada diseño con
  confianza `baja` (menos de 8 ventas en 60 días). No presentes esos números
  como si fueran predicciones.
- **Los diseños sin link de ML no se cruzan con sus ventas.** El reporte los
  cuenta al final; hay que vincularlos desde la galería con «🔗 Vincular ML».

## Ajustes

Todo lo tuyo vive en `config.json` del skill: impresoras, horas al día, ritmo de
extrusión, lead time de Full, colchón, días de cobertura que quieres. Si el
usuario dice «tengo dos impresoras» o «Full tarda una semana», eso se cambia ahí,
no en el código.

## Sesión

Se autoriza una sola vez (el refresh token dura ~6 meses):

```bash
python3 .claude/skills/colecta-full/scripts/login.py          # da la URL
python3 .claude/skills/colecta-full/scripts/login.py TG-xxx   # canjea el código
```

Credenciales y token viven en `~/.catalogo3d/`, con permisos 600, fuera del
repo. **Nunca los escribas en el chat, en el repo ni en un commit.** Si falta el
archivo de credenciales, el error dice qué crear; que lo llene el usuario.

## Programar la colecta

El plan dice cuándo y cuánto. **La colecta se programa a mano en el panel de
MercadoLibre** — no la agendes tú. Si el usuario quiere, se le puede abrir el
panel en el navegador, pero la confirmación del envío es suya.

Ver `referencias/api-ml.md` para los endpoints y lo que está sin verificar.
