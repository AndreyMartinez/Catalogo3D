# Catálogo 3D

Galería local para tus diseños `.3mf` (Bambu Studio). Corre un servidor
en tu máquina y se abre en el navegador — sin dependencias, solo Python 3
estándar.

## Qué hace

- Muestra la miniatura de cada `.3mf` (la que ya trae el propio archivo).
- Lee el peso en gramos si el archivo ya fue laminado en Bambu Studio.
- Calcula un costo estimado (peso × precio por kg, ajustable en vivo).
- Renombra el archivo real en disco desde la galería.
- Elimina el archivo real en disco desde la galería.
- Recorre subcarpetas: muestra también los `.3mf` que tengas organizados
  en carpetas dentro de tu carpeta de diseños.
- Pestaña **Descargas**: lista los `.3mf` que tengas en `~/Downloads` y
  te deja moverlos con un botón a tu carpeta de diseños (evita
  sobrescribir si ya existe un archivo con el mismo nombre).

## Uso

```bash
python3 catalog3d.py
```

Por defecto busca en `~/Desktop/own design 3d`. Para usar otra carpeta:

```bash
python3 catalog3d.py "/ruta/a/tu/carpeta"
```

Se abre solo en `http://127.0.0.1:8770/`. Para cerrar: `Ctrl+C` en la terminal.

## Requisitos

Solo Python 3 (librería estándar). No hay que instalar nada más.
