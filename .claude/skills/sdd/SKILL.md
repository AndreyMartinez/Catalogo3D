---
name: sdd
description: Desarrollo guiado por especificación (Spec Driven Development) para este proyecto — convierte una idea de función nueva (en la galería, el motor de generadores o un skill) en requisitos EARS, diseño técnico, plan de tareas e implementación tarea por tarea, con aprobación del usuario entre cada paso. Úsalo cuando el usuario quiera construir o cambiar algo en el código que no cubre ningún otro skill, o diga «spec», «SDD», «hagamos una función nueva», «agrega X a la galería».
argument-hint: "[requisitos|diseno|plan|implementar N] <slug o idea>"
---

# SDD — de la idea al código, con aprobación en cada paso

Cuatro pasos, siempre en orden. **No pases al siguiente sin un «sí» explícito
del usuario** al documento del paso actual.

```
1 requisitos.md  →  2 design.md  →  3 tasks.md  →  4 implementar (una tarea a la vez)
```

Todo vive en `.claude/specs/<slug>/` — un slug corto en kebab-case por función
(`pestana-idea`, `vocabulario-de-formas` son ejemplos reales de este repo;
léelos para ver el tono y el nivel de detalle esperado). Los documentos se
escriben en español.

## 0. Antes de empezar

- Si el usuario pasó un slug que ya existe, lee los tres archivos y retoma en el
  primer paso sin aprobar o en la primera tarea sin marcar.
- Si la idea en realidad es **diseñar o mejorar una pieza** (no código), no es
  SDD: ofrece `producto-nuevo`, `optimizar-pieza` o `transform`.
- Restricciones del proyecto que todo requisito y diseño respetan:
  - **Solo biblioteca estándar de Python 3** en `catalog3d.py` y
    `generadores/`. Una dependencia nueva es una decisión del usuario, no del
    diseño.
  - **Nada de credenciales en el repo** (el repo es público). Tokens y claves
    viven en `~/.catalogo3d/` con permisos 600.
  - Los datos de ventas del usuario no se versionan.

## 1. Requisitos → `requirements.md`

- Escribe una primera versión completa **sin hacer preguntas antes**, desde la
  idea del usuario. Plantilla: `plantillas/requisitos.md`.
- Criterios en **EARS en español**: `CUANDO [evento] ENTONCES el sistema
  DEBERÁ [respuesta]`, `SI [condición] ENTONCES …`, `MIENTRAS …`.
- Piensa en casos borde, experiencia de uso y cómo se sabe que quedó bien.
- No explores código todavía: este paso es qué, no cómo.
- Cierra con: «¿Los requisitos están bien? Si sí, pasamos al diseño.» Itera
  hasta el sí.

## 2. Diseño → `design.md`

- Ahora sí lee el código que toca. Resume lo que investigaste dentro del
  diseño; no crees archivos de investigación aparte.
- Plantilla: `plantillas/diseno.md`. Cada requisito debe quedar cubierto;
  di qué decisión tomaste y por qué. Diagramas en Mermaid si ayudan.
- Si el diseño descubre un hueco en los requisitos, ofrece volver al paso 1.
- Cierra con: «¿El diseño está bien? Si sí, armo el plan de tareas.»

## 3. Plan → `tasks.md`

- Lista numerada de casillas, máximo dos niveles (1., 1.1). Plantilla:
  `plantillas/tareas.md`.
- Solo tareas de escribir, cambiar o probar código. Cada una dice qué archivos
  toca y a qué requisitos responde (`_Requisitos: 1.2, 3.1_`).
- Pasos chicos, probados temprano, sin código huérfano: cada tarea se conecta
  con lo anterior.
- Cierra con: «¿Las tareas están bien?»

## 4. Implementar — una tarea por vez

- Antes de tocar código, lee `requirements.md`, `design.md` y `tasks.md`.
- Haz **solo** la tarea pedida (si tiene subtareas, empieza por ellas).
- Verifica contra los criterios de esa tarea: corre `generadores/pruebas.py` si
  tocaste el motor, `python3 -m py_compile` en lo que editaste, y abre la
  galería (`python3 catalog3d.py`) si cambió algo visible.
- Marca la casilla en `tasks.md` y **detente**: pide revisión. No sigas con la
  siguiente tarea hasta que el usuario lo pida.
- Si algo es ambiguo, pregunta; no supongas preferencias.
