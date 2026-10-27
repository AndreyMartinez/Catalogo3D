#!/usr/bin/env python3
"""De una publicación de MercadoLibre a un borrador de Amazon.

Aquí vive lo mecánico: las reglas de Amazon que ML no tiene (título sin
promociones, sin el obsequio de siembra, sin el cierre de ML) y el armado de
viñetas y palabras clave que ML no tiene. La redacción fina la hacen Claude y
el usuario sobre el borrador; estas funciones solo dejan algo correcto de
donde partir.

Las descripciones de ML de Savia Raíz siguen un formato: una línea en
MAYÚSCULAS con el nombre del producto, uno o dos párrafos de entrada y
secciones con encabezado en MAYÚSCULAS (CARACTERÍSTICAS, CUIDADOS,
IMPORTANTE, INCLUYE REGALO SORPRESA…), y cierran con «¿Tienes dudas?» y
«¿Necesitas factura?».
"""
import re
import unicodedata

MARCA_GENERICA = "Generic"
MAX_VINETAS = 5
MAX_BYTES_CLAVES = 249

# «Más Regalos Sorpresa», «Más Obsequio De Siembra», «Mas Obsequio De
# Cultivo», «Con Regalo Cultivo Botanico», «. Más Regalo»… (los 40 títulos
# activos al 2026-10-26).
_OBSEQUIO_TITULO = re.compile(
    r"[,.]?\s*\b(?:m[aá]s|con|incluye)\s+(?:regalos?|obsequios?)"
    r"(?:\s+sorpresa)?"
    r"(?:\s+(?:de\s+)?(?:siembra|cultivo)(?:\s+bot[aá]nico)?)?\b",
    re.IGNORECASE)
_PROMOCION = re.compile(
    r"\b(?:env[ií]o\s+gratis|gratis|ofertas?|promoci[oó]n|descuentos?|"
    r"m[aá]s\s+vendido|ll[eé]vatelo|regalos?|obsequios?)\b",
    re.IGNORECASE)
_MARCA_PROPIA = re.compile(r"\bsavia\s+ra[ií]z\b", re.IGNORECASE)
# Caracteres que Amazon no admite en títulos.
_PROHIBIDOS = re.compile(r"[!$?_{}^¬¦]")

# Palabras del kit de siembra: si aparecen en lo que se quita, se avisa que
# el kit es posiblemente restringido. «maceta» sola no cuenta: en macetas y
# floreros es el producto mismo.
_KIT = re.compile(r"\b(?:humus|semillas?|siembra|sembrar|cultivo)\b", re.IGNORECASE)
# Frases que prometen algo que no es el producto.
_FRASE_OBSEQUIO = re.compile(
    r"\b(?:obsequios?|regalos?\s+sorpresa|recibes\s+una\s+maceta|"
    r"humus|semillas?)\b", re.IGNORECASE)
# Encabezado de una sección que solo existe para el obsequio.
_SECCION_OBSEQUIO = re.compile(r"\bINCLUYE\b.*\b(?:REGAL|OBSEQU)|\bOBSEQU|\bSIEMBRA\b|\bCULTIVO\b")
# Cierre de ML: preguntas y factura.
_CIERRE_ML = re.compile(r"^¿?\s*(?:tienes\s+dudas|necesitas\s+factura)", re.IGNORECASE)

# Palabras que no aportan como palabra clave.
_VACIAS = set("""a al con de del el en la las los mas más para por que y o
u un una sin su sus tu tus se es""".split())


def _limpiar_espacios(texto):
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"\s+([,.;:])", r"\1", texto)
    return texto.strip(" ,.;:-")


def es_kit(titulo):
    """El producto mismo es un kit de siembra (Kit Maceta con humus y
    semillas): el kit no se quita, pero puede estar restringido."""
    return bool(re.search(r"\b(?:humus|semillas?)\b", titulo or "", re.IGNORECASE))


def limpiar_titulo(titulo, marca=MARCA_GENERICA):
    """Título de ML → título para Amazon. Devuelve (título, avisos)."""
    avisos = []
    nuevo = titulo or ""

    quitado = [m.group(0).strip(" ,.") for m in _OBSEQUIO_TITULO.finditer(nuevo)]
    nuevo = _OBSEQUIO_TITULO.sub(" ", nuevo)
    quitado += [m.group(0) for m in _PROMOCION.finditer(nuevo)]
    nuevo = _PROMOCION.sub(" ", nuevo)
    if quitado:
        avisos.append("Quité del título: " + ", ".join(f"«{q}»" for q in quitado)
                      + " (Amazon no admite promociones en el título).")

    if _PROHIBIDOS.search(nuevo):
        avisos.append("Quité del título caracteres que Amazon no admite (! $ ? _ { } ^ ¬ ¦).")
        nuevo = _PROHIBIDOS.sub(" ", nuevo)

    if marca == MARCA_GENERICA:
        if _MARCA_PROPIA.search(nuevo):
            nuevo = _MARCA_PROPIA.sub(" ", nuevo)
            avisos.append("Quité «Savia Raíz» del título: la marca en Amazon es "
                          "Generic y un título con otra marca se ve como marca falsa.")
    elif marca:
        # La marca va una sola vez y al principio.
        nuevo = f"{marca} {_MARCA_PROPIA.sub(' ', nuevo)}"

    nuevo = _limpiar_espacios(nuevo)
    repetidas = sorted({p for p in re.findall(r"\w+", nuevo.lower())
                        if len(p) > 2 and nuevo.lower().split().count(p) > 2})
    if repetidas:
        avisos.append("Palabras repetidas más de dos veces en el título: "
                      + ", ".join(repetidas) + ".")
    if es_kit(titulo):
        avisos.append("Este producto es un kit con semillas y humus: en Amazon las "
                      "semillas y la tierra pueden ser producto restringido. "
                      "Revísalo antes de publicar.")
    return nuevo, avisos


def _es_encabezado(linea):
    return (linea == linea.upper() and re.search(r"[A-ZÁÉÍÓÚÑ]{3}", linea)
            and not linea.startswith("-"))


def secciones(texto):
    """Parte la descripción de ML en [{encabezado, parrafos}]. La primera
    sección es la del nombre del producto (o None si el texto no empieza con
    un encabezado). Los renglones «- …» quedan como párrafos propios."""
    salida = [{"encabezado": None, "parrafos": []}]
    for bloque in (texto or "").replace("\r\n", "\n").split("\n"):
        linea = bloque.strip()
        if not linea:
            continue
        if _es_encabezado(linea):
            if salida[-1]["encabezado"] is None and not salida[-1]["parrafos"]:
                salida[-1]["encabezado"] = linea
            else:
                salida.append({"encabezado": linea, "parrafos": []})
        else:
            salida[-1]["parrafos"].append(linea)
    return [s for s in salida if s["encabezado"] or s["parrafos"]]


def _frases(parrafo):
    return re.split(r"(?<=[.!?])\s+", parrafo)


def limpiar_descripcion(texto, kit=False):
    """Quita de la descripción de ML lo que Amazon no debe ver: las
    secciones del obsequio, las frases que lo prometen y el cierre de ML.
    Si el producto es un kit, las semillas y el humus se quedan. Devuelve
    (secciones limpias, avisos)."""
    limpias, quitado_kit, quitado_regalo, quitado_cierre = [], False, False, False
    for sec in secciones(texto):
        encabezado = sec["encabezado"] or ""
        if not kit and _SECCION_OBSEQUIO.search(encabezado):
            cuerpo = " ".join(sec["parrafos"]) + " " + encabezado
            quitado_kit |= bool(_KIT.search(cuerpo))
            quitado_regalo |= not _KIT.search(cuerpo)
            continue
        parrafos = []
        for p in sec["parrafos"]:
            if _CIERRE_ML.search(p):
                quitado_cierre = True
                continue
            if not kit:
                frases = []
                for f in _frases(p):
                    if _FRASE_OBSEQUIO.search(f):
                        quitado_kit |= bool(_KIT.search(f))
                        quitado_regalo |= not _KIT.search(f)
                    else:
                        frases.append(f)
                p = " ".join(frases).strip()
            if p:
                parrafos.append(p)
        if parrafos:
            limpias.append({"encabezado": sec["encabezado"], "parrafos": parrafos})
    avisos = []
    if quitado_kit:
        avisos.append("Quité el obsequio de siembra (maceta, humus y semillas): en "
                      "Amazon las semillas y la tierra pueden ser producto restringido. "
                      "Si lo quieres incluir, lo decides tú.")
    if quitado_regalo:
        avisos.append("Quité el «regalo sorpresa» de la descripción: Amazon no admite "
                      "promociones, y lo que no se describe no se puede reclamar.")
    if quitado_cierre:
        avisos.append("Quité el cierre de ML («¿Tienes dudas?», «¿Necesitas factura?»).")
    return limpias, avisos


def _renglones(sec):
    return [p.lstrip("-• ").strip() for p in sec["parrafos"]]


def _titulo_seccion(encabezado):
    return encabezado.split(" - ")[0].strip().rstrip(":")


def vinetas(limpias, medidas=None):
    """Hasta 5 viñetas «ENCABEZADO: texto» a partir de las secciones limpias:
    la entrada, CARACTERÍSTICAS, las medidas (si se dan), CUIDADOS e
    IMPORTANTE; si sobra lugar, el segundo párrafo de entrada y las demás
    secciones."""
    if not limpias:
        return [medidas] if medidas else []
    conocidas = ("CARACTERÍSTICAS", "CUIDADOS", "IMPORTANTE")
    # La entrada es la primera sección si no es una de las conocidas (su
    # encabezado, si tiene, es el nombre del producto).
    primera = limpias[0]
    entrada = None if _titulo_seccion(primera["encabezado"] or "") in conocidas else primera
    resto = limpias[1:] if entrada else limpias
    por_nombre = {}
    otras = []
    for s in resto:
        nombre = _titulo_seccion(s["encabezado"] or "")
        if nombre in conocidas and nombre not in por_nombre:
            por_nombre[nombre] = s
        elif s["parrafos"]:
            otras.append(s)

    def juntar(nombre, sec):
        partes = _renglones(sec)
        texto = "; ".join(p.rstrip(".") for p in partes) + "." if any(
            p.startswith(("-", "•")) for p in sec["parrafos"]) else " ".join(partes)
        return f"{nombre}: {texto}" if nombre else texto

    principales, extra = [], []
    if entrada and entrada["parrafos"]:
        principales.append(entrada["parrafos"][0])
        extra += entrada["parrafos"][1:]
    if "CARACTERÍSTICAS" in por_nombre:
        principales.append(juntar("CARACTERÍSTICAS", por_nombre["CARACTERÍSTICAS"]))
    if medidas:
        principales.append(medidas)
    for nombre in ("CUIDADOS", "IMPORTANTE"):
        if nombre in por_nombre:
            principales.append(juntar(nombre, por_nombre[nombre]))
    extra += [juntar(_titulo_seccion(s["encabezado"]) if s["encabezado"] else "", s) for s in otras]

    salida = principales[:MAX_VINETAS]
    # Lo extra entra después de la entrada, mientras haya lugar.
    for texto in extra:
        if len(salida) >= MAX_VINETAS:
            break
        salida.insert(1 if salida else 0, texto)
    return salida


def descripcion(limpias):
    """Texto de la descripción para Amazon: las secciones limpias con sus
    encabezados, separadas por renglón en blanco."""
    bloques = []
    for s in limpias:
        lineas = ([s["encabezado"]] if s["encabezado"] else []) + s["parrafos"]
        if lineas:
            bloques.append("\n".join(lineas))
    return "\n\n".join(bloques)


def _sin_acentos(texto):
    descompuesto = unicodedata.normalize("NFD", str(texto).lower())
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def palabras_clave(titulo_ml, titulo_final, categorias=()):
    """Términos de búsqueda: palabras del título de ML y de la ruta de la
    categoría que no están ya en el título final, sin promociones, sin
    repetir y en menos de 250 bytes."""
    ya = {_sin_acentos(p) for p in re.findall(r"\w+", titulo_final or "")}
    fuente = " ".join([_PROMOCION.sub(" ", _OBSEQUIO_TITULO.sub(" ", titulo_ml or ""))]
                      + list(categorias))
    salida, vistos = [], set()
    for palabra in re.findall(r"[^\W\d_]+", fuente):
        clave = _sin_acentos(palabra)
        if (len(clave) < 3 or clave in _VACIAS or clave in ya or clave in vistos
                or _MARCA_PROPIA.search(palabra)):
            continue
        candidato = " ".join(salida + [palabra.lower()])
        if len(candidato.encode("utf-8")) > MAX_BYTES_CLAVES:
            break
        salida.append(palabra.lower())
        vistos.add(clave)
    return " ".join(salida)
