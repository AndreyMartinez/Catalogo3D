# Plan de implementación — Ventas del mes

El orden persigue una cosa: **no romper `semana.py` ni `plan.py`** al ampliar
la descarga. Por eso el paso 1 es la red de seguridad sobre
`resumir_ordenes`, y la descarga real (2.4) se hace con un respaldo del
archivo de hoy. A partir de ahí, `mes.py` se construye primero como
funciones puras con su prueba y después se le pone la entrada y la salida,
para que cada caso borde quede probado antes de verlo en un reporte.

- [x] 1. Red de seguridad sobre la descarga
  - Crear `colecta-full/scripts/prueba_traer_datos.py` con `unittest`, sin red:
    órdenes sintéticas (dos publicaciones en una orden, variantes, varios
    días) pasadas por `resumir_ordenes`.
  - Fijar lo que hoy leen `semana.py` y `plan.py`: por publicación,
    `titulo`, `seller_sku`, `variantes`, `por_dia` y `unidades`, con los
    valores esperados.
  - Confirmar que importar `traer_datos` no lee credenciales ni abre red
    (si `ml_api` lo hace al importarse, la prueba lo evita sin tocar
    `ml_api`).
  - Correrla en verde **antes** de cambiar nada.
  - _Requisitos: 6.4 (no romper lo que ya lee los datos)_

- [x] 2. Ampliar `traer_datos.py`
  - [x] 2.1 Fecha en la Ciudad de México
    - `dia_mx(date_created)`: parsear el timestamp con su huso y convertir a
      `timezone(timedelta(hours=-6))`; usarla en `por_dia`.
    - Prueba: `…T00:30:00.000-04:00` cae el día anterior; `…T12:00-04:00`
      cae el mismo día; un `date_created` vacío no truena.
    - _Requisitos: 1.1_
  - [x] 2.2 Pesos y totales por día
    - En `resumir_ordenes`: `ingreso_por_dia` por publicación
      (`unit_price × quantity`) y el bloque raíz
      `por_dia = {fecha: {ordenes, unidades, ingreso, canceladas}}`. Hoy
      devuelve solo `por_item`, así que pasa a devolver las dos cosas y
      `main()` se ajusta.
    - Prueba: una orden con dos publicaciones cuenta 1 orden y suma las dos
      en unidades e ingreso.
    - _Requisitos: 1.2, 5.1_
  - [x] 2.3 Canceladas, `desde` y 125 días
    - `traer_ordenes` recibe el estado; `main()` hace una segunda pasada con
      `cancelled` que solo suma `canceladas` en el `por_dia` raíz.
    - Guardar `desde` en el JSON; `--dias` por defecto 125.
    - Prueba: las canceladas no aparecen en `ventas` ni cambian `unidades`.
    - _Requisitos: 1.3, 1.5, 2.3_
  - [x] 2.4 Descarga real y compatibilidad
    - Respaldar `~/.catalogo3d/ml_datos.json` como `ml_datos.json.bak`
      (permisos 600), correr `traer_datos.py`, y después `semana.py` y
      `plan.py`: tienen que terminar sin error y con cifras coherentes con
      el respaldo en las semanas que ambos cubren (salvo el corrimiento de
      medianoche, que se reporta).
    - `python3 -m py_compile` sobre `traer_datos.py`.
    - _Requisitos: 1.1, 1.2, 1.3_

- [x] 3. Funciones puras de `mes.py`, con prueba
  - [x] 3.1 Calendario y comparación
    - Crear `estudio-mercado/scripts/mes.py` con `corte`, `cobertura`,
      `al_dia` y `diferencia`, sin E/S.
    - Crear `estudio-mercado/scripts/prueba_mes.py`: día 31 contra mes de
      30 (recorte), mes cerrado, último día completo vs. día de descarga,
      mes de comparación que empieza antes de `desde`, base < 10 sin
      porcentaje.
    - _Requisitos: 1.1, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4_
  - [x] 3.2 Proyección y meta
    - `proyectar` y `meta`.
    - Prueba: menos de 7 días → «no confiable»; ritmos que difieren > 20 %
      → `cambio_ritmo`; meta ya alcanzada; cero ventas sin dividir entre
      cero.
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 6.5_
  - [x] 3.3 Alertas y retorno
    - `alerta` (importando el umbral de `semana.tendencia`) y `retorno`
      (sobre `semana.catalogo()`).
    - Prueba: `dormida` con 1 unidad el mes anterior y 0 en este; `nueva`
      solo si la ventana cubre 60 días antes; retorno parcial y extrapolado;
      sin unidades vinculadas → solo bruto y «falta el dato».
    - _Requisitos: 4.3, 4.4, 5.1, 5.2, 5.3, 5.4_

- [x] 4. Entrada y salida de `mes.py`
  - `main()` con `--mes`, `--meta` y `--meta-pesos`; carga de
    `ml_datos.json`, filas por publicación y categoría con Full / no Full,
    orden por unidades del mes.
  - Escribir `.claude/mercado/meses/AAAA-MM.json` y `.md` (aviso, resumen de
    5 líneas con la recomendación como marcador, totales, comparación,
    proyección, tablas, retorno) e imprimir el `.md`.
  - Errores: sin archivo, datos de más de 24 h, archivo viejo sin campos
    nuevos (reporte solo en unidades), `--mes` inválido o futuro.
  - Prueba en `prueba_mes.py`: `main()` contra un `ml_datos.json` sintético
    en una carpeta temporal, incluido uno con el formato viejo.
  - Confirmar con `git status` que nada de `meses/` aparece.
  - _Requisitos: 1.2, 4.1, 4.2, 4.5, 6.1, 6.2, 6.4, 6.5, 7.1, 7.2, 7.4, 7.5_

- [x] 5. Conectarlo a `estudio-mercado`
  - En `estudio-mercado/SKILL.md`: sección «¿Cómo va el mes?» (bajar
    datos, qué hacer si la sesión venció, correr `mes.py`, escribir la
    recomendación y contestar con el resumen) y sumar «ventas del mes» a la
    `description`. Actualizar el comando del paso 1 a los 125 días.
  - _Requisitos: 6.3, 7.3_

- [x] 6. De punta a punta con datos reales
  - Correr `mes.py` para octubre y `mes.py --mes 2026-09`; cuadrar las
    unidades de septiembre contra la suma directa de `por_dia` del 1 al
    30-09.
  - Correr las dos pruebas y `python3 -m py_compile` sobre los tres
    scripts.
  - Contestar «¿cómo vienen las ventas del mes?» siguiendo el skill.
  - _Requisitos: todos_
