# Catálogo 3D — Savia Raíz

Galería local de diseños `.3mf` (Bambu Studio) y el taller alrededor: diseño de
piezas, optimización de impresión, mercado y envíos a MercadoLibre Full.
Negocio: **Savia Raíz**, MercadoLibre México, impresora Bambu P2S.

## Lo primero en cada sesión

Antes de hacer cualquier otra cosa, pregunta con `AskUserQuestion` qué quiere
hacer el usuario: **ejecutar uno de los skills de abajo o hacer algo
distinto**. Sáltate la pregunta solo si el primer mensaje ya invoca un skill
(`/nombre`) o pide sin ambigüedad lo que hace uno de ellos — en ese caso dilo
en una línea («Esto es `colecta-full`, lo corro») y sigue.

Forma sugerida (máximo 4 opciones por pregunta; «Otra» la agrega la
herramienta sola):

1. **¿Qué hacemos hoy?** — Producto nuevo o mercado · Producción e impresión ·
   Construir algo en el código (SDD) · Otra cosa.
2. Según la respuesta, una segunda pregunta con los skills de ese grupo.

Si elige «Otra cosa», pregunta qué y decide: si es código nuevo para la
galería, el motor o un skill, propón `sdd`; si es una tarea puntual, hazla.

## Con qué se cuenta

### Skills (`.claude/skills/`)

| Grupo | Skill | Para qué |
|---|---|---|
| Producto nuevo y mercado | `producto-nuevo` | Del dato de mercado (ML/Amazon, «+100 vendidos») a 10 propuestas, diseño, prototipo, publicación y seguimiento semanas 2/4/6. Corre con Opus 5.5. |
| | `estudio-mercado` | Rutina del domingo: ventas de la semana, competencia y el estudio vivo. |
| Producción e impresión | `colecta-full` | Cuándo programar la colecta a Full, cuánto mandar y en qué orden imprimir. |
| | `optimizar-pieza` | Arreglar una pieza puntual: acabado, peso, paredes, bordes. |
| | `transform` | Paquete completo de mejoras a una pieza: capa, soporte, tamaño, placa llena. |
| Código | `sdd` | Requisitos → diseño → tareas → implementación, con aprobación en cada paso. |

### Código

- `catalog3d.py` — la galería (servidor local, solo biblioteca estándar).
- `generadores/` — motor paramétrico de recipientes (`crear.py`, recetas en
  `disenos.py`, núcleo en `nucleo/`) y scripts de piezas propias
  (`huevo_lowpoly.py`, `portacepillos_rapido.py`…). Si todavía no está en tu
  checkout, vive en la copia de trabajo principal sin versionar.

### Conocimiento versionado (`.claude/`)

| Carpeta | Qué hay |
|---|---|
| `specs/` | Especificaciones SDD por función (`requirements.md`, `design.md`, `tasks.md`). |
| `optimizaciones/` | Registro por pieza de lo que ya se diagnosticó y cambió; `INDICE.md` primero. |
| `productos/investigacion/` | Investigaciones de mercado de `producto-nuevo`. |

### Lo que NO está en el repo (y no debe estar)

El repo es **público**.

- **Credenciales y tokens de MercadoLibre**: `~/.catalogo3d/` (permisos 600).
  Nunca se copian al repo, al chat ni a un commit.
- **Ventas y datos del negocio**: `~/.catalogo3d/ml_datos.json`,
  `.claude/mercado/` (estudio vivo y cifras semanales) y
  `.claude/productos/` salvo `investigacion/` — locales, ignorados por git.
- Diseños `.3mf`: `~/Desktop/own design 3d/`.

## Reglas de trabajo

- Español en documentos, skills y mensajes de commit.
- Solo biblioteca estándar de Python en `catalog3d.py` y `generadores/`.
- Antes de proponer una forma nueva, compárala contra lo que de verdad se
  vende: portacontroles y portacubiertos.
- Precio, costo y ventas: cítalos del estudio de mercado con su nivel de
  evidencia (medido / correlación / suposición).
