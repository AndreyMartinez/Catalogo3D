# Marca Savia Raíz

Identidad rediseñada el 2026-11-24. Del logo anterior solo se quedó Arepo, el
perro de la casa.

## Logo oficial

`logo_oficial.jpg` (1024×1024): sello con la cabeza de Arepo en una sola línea
carbón y la lengua rosa; el cuello se vuelve raíces libres con dos brotes y
puntos rosas. «SEMBRAR CON AMOR» en arco arriba, «CRECER CON PACIENCIA» en arco
abajo y «SAVIA RAÍZ» al centro (el cuello cruza el nombre, así se aprobó).

Eslogan: **Sembrar con amor · crecer con paciencia.** Detrás: caer y
levantarse, creer en uno mismo, sembrar, amabilidad, respeto, sociedad y
paciencia.

| Color | Hex | Uso |
|---|---|---|
| Crema | `#F1EDE2` | fondo |
| Carbón | `#1D1913` | línea y letras |
| Rosa | `#C97380` | lengua y puntos |

Pendiente: pasarlo a vector (SVG) para etiquetas y empaque.

## MercadoLibre — Mi página

Publicado en https://www.mercadolibre.com.mx/pagina/7s7d6pkj

| Archivo | Dónde va | Medida que pide ML |
|---|---|---|
| `mercadolibre/perfil_1000.png` | logotipo del encabezado | mín. 500×500, se ve redondo de ~40 px |
| `mercadolibre/encabezado_claro_3840x200.jpg` | portada de escritorio (la que está puesta) | mín. 1920×100; lo importante en los 1180×100 del centro |
| `mercadolibre/encabezado_oscuro_3840x200.jpg` | alternativa oscura | igual |
| `mercadolibre/nuestra_raiz_escritorio_3840x960.jpg` | banner principal de «Nuestra raíz» | 1920×480 |
| `mercadolibre/nuestra_raiz_movil_1200x676.jpg` | el mismo, en celular | 600×338 |
| `mercadolibre/tarjeta{1,2,3}_*.jpg` | tarjetas de la Lista de contenido en Inicio | 383×216 escritorio y 355×199 celular (se sube cada una aparte) |

`nuestra-raiz.md` tiene los 5 bloques de texto de la subpágina, las tarjetas y
las fuentes de los estudios citados.

## Cómo se hizo

`generadores/logo_gemini.py` con `gemini-3-pro-image`, la foto de Arepo y las
referencias que fue mandando el usuario. Las rondas descartadas viven fuera del
repo, en `~/Desktop/Logo Savia Raiz/rondas/`.
