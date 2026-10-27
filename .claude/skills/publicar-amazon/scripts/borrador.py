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


# ------------------------------------------ fotos, medidas, precio, SKU

MAX_FOTOS = 9          # principal + other_product_image_locator_1..8
# Un paquete de pieza impresa pesa 200–400 g (el del Olas, 198 g); en ML hay
# paquetes capturados de más de 1 kg. Amazon cobra FBA por ese peso.
PAQUETE_SOSPECHOSO_G = 600
_COLORES = re.compile(r"\b(negr[oa]|blanc[oa]|gris|amarill[oa]|azul|roj[oa]|verde|rosa|"
                      r"beige|caf[eé]|dorad[oa]|plateado)\b", re.IGNORECASE)
# Material de ML → como lo dice Amazon (la lista de CADDY no tiene «PLA»;
# el Olas quedó como «Plástico»).
SINONIMOS_MATERIAL = {"pla": "Plástico", "pld": "Plástico", "plastico": "Plástico"}
# Palabras del título que no sirven de nombre en el SKU.
_GENERICAS = set("""organizador organizadores porta portacubiertos portacontroles
portalapices portacepillos soporte de del con para y en el la los las control
controles remoto remotos cubiertos diseno moderno minimalista decorativo
decorativa florero maceta kit escritorio bano tocador cocina figura set
espacios espacio redondo humus semillas tarro organizador cepillos""".split())


def url_completa(url):
    """URL de mlstatic en tamaño completo: la API da «-O.jpg» (500 px); la
    misma foto con «-F.jpg» sale a 1200 px."""
    url = (url or "").replace("http://", "https://", 1)
    return re.sub(r"-[A-Z]\.(?:jpg|jpeg|webp|png)$", "-F.jpg", url)


def fotos(item, variacion=None):
    """Fotos en tamaño completo y en el orden de ML; las de la variación si
    tiene. Devuelve (principal, otras, avisos)."""
    todas = item.get("pictures") or []
    if variacion and variacion.get("picture_ids"):
        por_id = {p.get("id"): p for p in todas}
        todas = [por_id[i] for i in variacion["picture_ids"] if i in por_id]
    urls = [url_completa(p.get("secure_url") or p.get("url")) for p in todas]
    urls = [u for u in urls if u]
    avisos = []
    if len(urls) > MAX_FOTOS:
        avisos.append(f"ML tiene {len(urls)} fotos; Amazon acepta {MAX_FOTOS}. "
                      f"Quedaron las primeras {MAX_FOTOS}.")
    urls = urls[:MAX_FOTOS]
    return (urls[0] if urls else None), urls[1:], avisos


def _atributo(item, *ids):
    for a in item.get("attributes") or []:
        if a.get("id") in ids and a.get("value_name"):
            return a
    return None


def _numero(atributo, unidades):
    """'8 cm' → 8.0 en la unidad pedida ('cm' o 'g')."""
    if not atributo:
        return None
    struct = atributo.get("value_struct") or {}
    numero, unidad = struct.get("number"), struct.get("unit")
    if numero is None:
        m = re.match(r"\s*([\d.,]+)\s*([a-zA-Z]*)", atributo.get("value_name") or "")
        if not m:
            return None
        numero, unidad = float(m.group(1).replace(",", ".")), m.group(2)
    factor = {"cm": {"cm": 1, "mm": 0.1, "m": 100, "in": 2.54, "pulgadas": 2.54},
              "g": {"g": 1, "kg": 1000, "mg": 0.001, "lb": 453.592}}[unidades]
    f = factor.get((unidad or unidades).lower())
    return round(float(numero) * f, 2) if f else None


def medidas(item, peso_g=None):
    """Medidas del artículo y del paquete en cm y g. En ML los ejes vienen
    como LENGTH/WIDTH/DEPTH sin regla fija (el Olas dice WIDTH 8 y mide
    19.6 de frente), así que quedan siempre «por revisar». El paquete se
    ordena de mayor a menor, como lo pide Amazon."""
    largo = _numero(_atributo(item, "LENGTH"), "cm")
    ancho = _numero(_atributo(item, "WIDTH"), "cm")
    fondo = _numero(_atributo(item, "DEPTH"), "cm")
    articulo = {
        "frente_cm": largo if largo is not None else ancho,
        "fondo_cm": fondo if fondo is not None else (ancho if largo is not None else None),
        "alto_cm": _numero(_atributo(item, "HEIGHT"), "cm"),
        "peso_g": peso_g if peso_g is not None else _numero(_atributo(item, "WEIGHT"), "g"),
    }
    lados = [_numero(_atributo(item, f"SELLER_PACKAGE_{e}"), "cm")
             for e in ("LENGTH", "WIDTH", "HEIGHT")]
    lados = sorted([x for x in lados if x is not None], reverse=True)
    paquete = {"largo_cm": None, "ancho_cm": None, "alto_cm": None,
               "peso_g": _numero(_atributo(item, "SELLER_PACKAGE_WEIGHT"), "g")}
    if len(lados) == 3:
        paquete.update(largo_cm=lados[0], ancho_cm=lados[1], alto_cm=lados[2])
    return {"articulo": articulo, "paquete": paquete}


def vineta_medidas(med):
    a = med["articulo"]
    if None in (a["frente_cm"], a["fondo_cm"], a["alto_cm"]):
        return None
    texto = (f"MEDIDAS: {a['frente_cm']:g} cm de frente x {a['fondo_cm']:g} cm de fondo "
             f"x {a['alto_cm']:g} cm de alto")
    if a.get("peso_g"):
        texto += f"; pesa {a['peso_g']:g} g"
    return texto + "."


def precio(item, variacion=None):
    """Precio de lista: original_price si hay (las promos de ML bajan
    'price' por un tiempo); si no, el de la variación o el del ítem."""
    if item.get("original_price"):
        return float(item["original_price"])
    if variacion and variacion.get("price"):
        return float(variacion["price"])
    return float(item.get("price") or 0) or None


def costo(peso_g, costos, paquete=None):
    """Costo de la pieza como en el catálogo: peso × precio_kg + paquetería
    (la del diseño o la activa). Incluye lo del kit de ML."""
    if not peso_g or not costos:
        return None
    paquetes = costos.get("paquetes") or []
    i = paquete if paquete is not None else costos.get("paquete_activo", 0)
    caja = paquetes[i] if 0 <= (i or 0) < len(paquetes) else {"elementos": []}
    empaque = sum(e["costo_compra"] / e["unidades"] for e in caja["elementos"] if e.get("unidades"))
    return round(peso_g / 1000 * costos["precio_kg"] + empaque, 2)


def pesos_del_catalogo(catalogo):
    """{MLM: (peso_g, paquete)} desde .catalogo3d_mercadolibre.json (el MLM
    va dentro del enlace de edición)."""
    salida = {}
    for datos in (catalogo or {}).values():
        m = re.search(r"MLM\d+", datos.get("link") or "")
        if m and datos.get("peso_g"):
            salida[m.group(0)] = (float(datos["peso_g"]), datos.get("paquete"))
    return salida


def color(item, variacion=None):
    if variacion:
        for c in variacion.get("attribute_combinations") or []:
            if c.get("value_name") and c.get("id") in ("COLOR", None, "MAIN_COLOR"):
                return c["value_name"]
    a = _atributo(item, "COLOR", "MAIN_COLOR")
    if a:
        return a["value_name"]
    # Sin atributo: el último color conocido del título.
    m = _COLORES.findall(item.get("title") or "")
    return m[-1].capitalize() if m else None


def _ascii(texto):
    return re.sub(r"[^A-Z0-9]", "", _sin_acentos(texto).upper())


def sku(clave, titulo_limpio, color_, usados, mlm=""):
    """SR-<CLAVE>-<NOMBRE>-<COL>: NOMBRE es la primera palabra del título que
    no es genérica ni color (si no hay, los últimos 4 dígitos del MLM); COL,
    las 3 primeras letras del color. Si ya existe, -2, -3…"""
    nombre = next((_ascii(p) for p in re.findall(r"[^\W\d_]+", titulo_limpio or "")
                   if _sin_acentos(p) not in _GENERICAS and len(p) > 2
                   and not _COLORES.fullmatch(p)), None)
    partes = ["SR", clave or "GEN", (nombre or mlm[-4:] or "PIEZA")[:10]]
    if color_:
        conocido = _COLORES.search(color_)
        partes.append(_ascii(conocido.group(0) if conocido else color_)[:3])
    base = "-".join(partes)
    candidato, n = base, 2
    while candidato in usados:
        candidato, n = f"{base}-{n}", n + 1
    return candidato


def _material(item):
    a = _atributo(item, "MATERIAL", "MATERIALS")
    texto = a["value_name"] if a else None
    if texto is None and re.search(r"\bPLA\b", item.get("title") or ""):
        texto = "PLA"
    if texto is None:
        return None
    return SINONIMOS_MATERIAL.get(_sin_acentos(texto).strip(), texto)


def armar(item, texto_descripcion, ctx, variacion=None):
    """Borrador nuevo para una publicación (o una variación) de ML.

    ctx: categorias (el JSON de categorias.json), pesos ({MLM: (g, paquete)}),
    costos (.catalogo3d_costos.json), publicadas ({sku: {mlm, variacion}}),
    skus (los ya usados), ruta_categoria ([nombres]) y esquema (caché del
    tipo, o None). Las listas de valores de Amazon se aplican si hay esquema.
    """
    from esquema import opciones, valor_mas_cercano   # evita el ciclo al importar

    mlm = item["id"]
    var_id = str(variacion["id"]) if variacion else None
    conf = ctx.get("categorias") or {}
    marca = conf.get("marca", MARCA_GENERICA)
    cat = (conf.get("categorias") or {}).get(item.get("category_id")) or {}

    titulo, avisos = limpiar_titulo(item.get("title"), marca)
    color_ = color(item, variacion)
    if variacion and color_ and _sin_acentos(color_) not in _sin_acentos(titulo):
        titulo = f"{titulo} {color_}"
    kit = es_kit(item.get("title"))
    limpias, avisos_desc = limpiar_descripcion(texto_descripcion, kit)
    avisos += avisos_desc

    peso, paquete_costo = (ctx.get("pesos") or {}).get(mlm, (None, None))
    med = medidas(item, peso)
    principal, otras, avisos_fotos = fotos(item, variacion)
    avisos += avisos_fotos
    if not limpias:
        avisos.append("La publicación de ML no tiene descripción: las viñetas y la "
                      "descripción hay que escribirlas.")

    existente = next((s for s, r in (ctx.get("publicadas") or {}).items()
                      if r.get("mlm") == mlm and str(r.get("variacion") or "") == str(var_id or "")),
                     None)
    sku_ = existente or sku(cat.get("clave_sku"), titulo, color_, set(ctx.get("skus") or ()), mlm)
    if (med["paquete"]["peso_g"] or 0) > PAQUETE_SOSPECHOSO_G:
        avisos.append(f"En ML el paquete pesa {med['paquete']['peso_g']:g} g; una pieza "
                      "impresa suele ir en 200–400 g. Amazon cobra FBA por ese peso: revísalo.")

    atributos = {
        "brand": marca,
        "manufacturer": conf.get("fabricante", marca),
        "country_of_origin": "MX",
        "condition_type": "new_new",
        "supplier_declared_dg_hz_regulation": "not_applicable",
    }
    if color_:
        atributos["color"] = color_
    material = _material(item)
    if material:
        atributos["material"] = material
    compartimentos = _atributo(item, "COMPARTMENTS_NUMBER")
    if compartimentos:
        try:
            atributos["number_of_compartments"] = int(float(compartimentos["value_name"]))
        except ValueError:
            pass

    # Los que Amazon exige por reglas condicionales (la vista previa del Olas
    # los pidió); el Olas publicado a mano los trae con esta forma.
    modelo = _limpiar_espacios(_COLORES.sub(" ", titulo)) if color_ else titulo
    atributos.update({
        "model_name": modelo,
        "model_number": sku_,
        "number_of_items": 1,
        "unit_count": {"value": 1.0, "type": {"value": "unidad", "language_tag": LOCALE}},
        "included_components": modelo,
        "batteries_required": False,
    })

    por_revisar = ["titulo", "vinetas", "descripcion", "palabras_clave", "precio",
                   "envio", "foto_principal", "medidas"]
    if kit:
        por_revisar.append("atributo:included_components")
    if not cat.get("confirmado") or not cat.get("tipo_producto"):
        por_revisar.insert(0, "tipo_producto")
    if not color_:
        por_revisar.append("atributo:color")
    cache = ctx.get("esquema")
    if cache:
        props = cache["esquema"].get("properties") or {}
        for nombre in list(atributos):
            if nombre not in props:
                del atributos[nombre]
                continue
            valores, nombres, cerrada = opciones(cache, nombre)
            if valores and atributos[nombre] not in valores:
                cercano = valor_mas_cercano(atributos[nombre], valores, nombres)
                if cercano is not None:
                    atributos[nombre] = cercano
                elif cerrada:
                    por_revisar.append(f"atributo:{nombre}")
        for nombre in cache["esquema"].get("required") or []:
            if nombre not in atributos and nombre not in _CAMPOS_PROPIOS:
                atributos[nombre] = None
                por_revisar.append(f"atributo:{nombre}")

    vin_medidas = vineta_medidas(med)
    return {
        "mlm": mlm,
        "variacion": var_id,
        "sku": sku_,
        "tipo_producto": cat.get("tipo_producto"),
        "titulo": titulo,
        "vinetas": vinetas(limpias, vin_medidas),
        "descripcion": descripcion(limpias),
        "palabras_clave": palabras_clave(item.get("title"), titulo, ctx.get("ruta_categoria") or ()),
        "atributos": atributos,
        "medidas": med,
        "fotos": {"principal": principal, "otras": otras, "excluidas": []},
        "precio": precio(item, variacion),
        "costo_ref": costo(peso, ctx.get("costos"), paquete_costo),
        "envio": {"modo": None, "cantidad": None},
        "por_revisar": por_revisar,
        "avisos": avisos,
        "origen_ml": {
            "titulo": item.get("title"),
            "precio": precio(item, variacion),
            "fotos": [principal] + otras if principal else [],
            "categoria": item.get("category_id"),
        },
        "validacion": None,
        "publicado": None,
    }


# Atributos que el borrador llena con sus propios campos (título, viñetas…)
# y que payload() pone; no se piden como atributo suelto.
_CAMPOS_PROPIOS = {"item_name", "bullet_point", "product_description", "generic_keyword",
                   "purchasable_offer", "fulfillment_availability", "list_price",
                   "main_product_image_locator", "supplier_declared_has_product_identifier_exemption",
                   "externally_assigned_product_identifier", "item_depth_width_height",
                   "item_dimensions", "item_length_width_height", "item_weight",
                   "item_package_dimensions", "item_package_weight"}


# ------------------------------------------------- lo que va a Amazon

MARKETPLACE = "A1AM78C64UM0Y8"
LOCALE = "es_MX"
MONEDA = "MXN"
# Campos del borrador que cambian lo que se manda; la huella sale de ellos.
CAMPOS_CONTENIDO = ("sku", "tipo_producto", "titulo", "vinetas", "descripcion",
                    "palabras_clave", "atributos", "medidas", "fotos", "precio", "envio")


class ErrorBorrador(Exception):
    pass


def _subcampos(cache, atributo):
    if not cache:
        return {"value", "marketplace_id", "language_tag"}
    prop = (cache["esquema"].get("properties") or {}).get(atributo) or {}
    return set(((prop.get("items") or {}).get("properties") or {}))


def _entrada(cache, atributo, valor):
    """Un valor del borrador en la forma de Amazon: {'value': …} más
    marketplace_id y language_tag solo si el esquema del atributo los tiene."""
    sub = _subcampos(cache, atributo)
    entrada = dict(valor) if isinstance(valor, dict) else {"value": valor}
    if "marketplace_id" in sub:
        entrada.setdefault("marketplace_id", MARKETPLACE)
    if "language_tag" in sub and "value" in entrada and isinstance(entrada["value"], str):
        entrada.setdefault("language_tag", LOCALE)
    return entrada


def _tiene(cache, atributo):
    return cache is None or atributo in (cache["esquema"].get("properties") or {})


def _cm(valor):
    return {"unit": "centimeters", "value": valor}


def payload(br, cache=None):
    """Borrador → cuerpo de putListingsItem: {productType, requirements,
    attributes}. Los atributos que el borrador deja en None (por revisar)
    no se mandan."""
    if not br.get("tipo_producto"):
        raise ErrorBorrador("El borrador no tiene tipo de producto.")
    attrs = {}

    def poner(nombre, valores):
        valores = [v for v in (valores if isinstance(valores, list) else [valores])
                   if v not in (None, "", [])]
        if valores:
            attrs[nombre] = [_entrada(cache, nombre, v) for v in valores]

    poner("item_name", br.get("titulo"))
    poner("bullet_point", list(br.get("vinetas") or []))
    poner("product_description", br.get("descripcion"))
    poner("generic_keyword", br.get("palabras_clave"))
    for nombre, valor in (br.get("atributos") or {}).items():
        poner(nombre, valor)

    fotos_ = br.get("fotos") or {}
    excluidas = set(fotos_.get("excluidas") or [])
    if fotos_.get("principal"):
        poner("main_product_image_locator", {"media_location": fotos_["principal"]})
    otras = [u for u in fotos_.get("otras") or [] if u not in excluidas]
    for i, url in enumerate(otras[:MAX_FOTOS - 1], 1):
        poner(f"other_product_image_locator_{i}", {"media_location": url})

    if br.get("precio"):
        oferta = {"currency": MONEDA,
                  "our_price": [{"schedule": [{"value_with_tax": br["precio"]}]}]}
        if "audience" in _subcampos(cache, "purchasable_offer"):
            oferta["audience"] = "ALL"
        poner("purchasable_offer", oferta)
        if _tiene(cache, "list_price"):
            poner("list_price", {"currency": MONEDA, "value_with_tax": br["precio"]})

    envio = br.get("envio") or {}
    if envio.get("modo") == "FBA":
        poner("fulfillment_availability", {"fulfillment_channel_code": "AMAZON_NA"})
    elif envio.get("modo") == "propio":
        if not envio.get("cantidad"):
            raise ErrorBorrador("Envío propio sin cantidad: pon cuántas piezas tienes "
                                "en casa (el stock de Full no cuenta).")
        poner("fulfillment_availability", {"fulfillment_channel_code": "DEFAULT",
                                           "quantity": int(envio["cantidad"])})
    elif envio.get("modo") is not None:
        raise ErrorBorrador(f"Modo de envío desconocido: {envio['modo']!r} (FBA o propio).")

    med = br.get("medidas") or {}
    a, p = med.get("articulo") or {}, med.get("paquete") or {}
    if None not in (a.get("frente_cm"), a.get("fondo_cm"), a.get("alto_cm")):
        if _tiene(cache, "item_depth_width_height"):
            poner("item_depth_width_height", {"depth": _cm(a["fondo_cm"]),
                                              "width": _cm(a["frente_cm"]),
                                              "height": _cm(a["alto_cm"])})
        elif _tiene(cache, "item_length_width_height"):
            poner("item_length_width_height", {"length": _cm(a["frente_cm"]),
                                               "width": _cm(a["fondo_cm"]),
                                               "height": _cm(a["alto_cm"])})
    if a.get("peso_g") and _tiene(cache, "item_weight"):
        poner("item_weight", {"unit": "grams", "value": a["peso_g"]})
    if None not in (p.get("largo_cm"), p.get("ancho_cm"), p.get("alto_cm")):
        poner("item_package_dimensions", {"length": _cm(p["largo_cm"]),
                                          "width": _cm(p["ancho_cm"]),
                                          "height": _cm(p["alto_cm"])})
    if p.get("peso_g"):
        poner("item_package_weight", {"unit": "grams", "value": p["peso_g"]})

    # Sin GTIN: producto exento con la marca del borrador (Generic, como el Olas).
    if "externally_assigned_product_identifier" not in attrs:
        from esquema import atributo_exencion   # evita el ciclo al importar
        exencion = (atributo_exencion(cache) if cache
                    else "supplier_declared_has_product_identifier_exemption")
        if exencion:
            poner(exencion, True)

    return {"productType": br["tipo_producto"], "requirements": "LISTING",
            "attributes": attrs}


def huella(br):
    """sha256 del contenido que se manda a Amazon, en JSON canónico. Una
    validación vale solo para la huella con la que se hizo."""
    import hashlib
    import json
    contenido = {c: br.get(c) for c in CAMPOS_CONTENIDO}
    texto = json.dumps(contenido, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def estado(br):
    """'publicado', 'validado' (la última validación es VALID y es de este
    contenido) o 'borrador'."""
    if br.get("publicado"):
        return "publicado"
    val = br.get("validacion") or {}
    if val.get("status") == "VALID" and val.get("huella") == huella(br):
        return "validado"
    return "borrador"


def cambios_en_ml(br, item, variacion=None):
    """Lo que cambió en ML desde que se armó el borrador: [(campo, antes,
    ahora)]. El borrador no se toca; el usuario decide."""
    origen = br.get("origen_ml") or {}
    principal, otras, _ = fotos(item, variacion)
    ahora = {"titulo": item.get("title"), "precio": precio(item, variacion),
             "fotos": [principal] + otras if principal else []}
    return [(c, origen.get(c), ahora[c]) for c in ("titulo", "precio", "fotos")
            if origen.get(c) != ahora[c]]


# ----------------------------------------------------------- fotos en red

LADO_MINIMO = 1000     # Amazon pide ≥ 1000 px en el lado mayor para el zoom
BYTES_CABECERA = 65535


def _abrir(pedido, timeout=None):     # se sustituye en las pruebas
    import urllib.request
    return urllib.request.urlopen(pedido, timeout=timeout)


def medidas_imagen(datos):
    """(ancho, alto) leídos del encabezado de un JPEG, PNG o WebP, o None."""
    import struct
    if datos[:8] == b"\x89PNG\r\n\x1a\n" and len(datos) >= 24:
        return struct.unpack(">II", datos[16:24])
    if datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        trozo = datos[12:16]
        if trozo == b"VP8 " and len(datos) >= 30:
            ancho, alto = struct.unpack("<HH", datos[26:30])
            return ancho & 0x3FFF, alto & 0x3FFF
        if trozo == b"VP8L" and len(datos) >= 25:
            b = datos[21:25]
            return (1 + (((b[1] & 0x3F) << 8) | b[0]),
                    1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6)))
        if trozo == b"VP8X" and len(datos) >= 30:
            return (1 + int.from_bytes(datos[24:27], "little"),
                    1 + int.from_bytes(datos[27:30], "little"))
        return None
    if datos[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(datos):
        if datos[i] != 0xFF:
            return None
        marca = datos[i + 1]
        if marca in (0xD8, 0x01) or 0xD0 <= marca <= 0xD7:
            i += 2
            continue
        largo = struct.unpack(">H", datos[i + 2:i + 4])[0]
        if marca in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            alto, ancho = struct.unpack(">HH", datos[i + 5:i + 9])
            return ancho, alto
        i += 2 + largo
    return None


def revisar_foto(url):
    """{url, ok, ancho, alto, aviso}. Pide solo los primeros 64 KB (mlstatic
    no acepta HEAD) y lee el tamaño del encabezado."""
    import urllib.error
    import urllib.request
    pedido = urllib.request.Request(url, headers={"Range": f"bytes=0-{BYTES_CABECERA}",
                                                  "User-Agent": "PublicadorSaviaRaiz/1.0"})
    try:
        with _abrir(pedido, timeout=30) as r:
            tipo = (r.headers.get("Content-Type") or "") if getattr(r, "headers", None) else ""
            datos = r.read(BYTES_CABECERA + 1)
    except (urllib.error.URLError, OSError) as e:
        return {"url": url, "ok": False, "ancho": None, "alto": None,
                "aviso": f"No responde: {getattr(e, 'reason', e)}"}
    if tipo and not tipo.startswith("image/"):
        return {"url": url, "ok": False, "ancho": None, "alto": None,
                "aviso": f"No es una imagen ({tipo})."}
    tam = medidas_imagen(datos)
    if not tam:
        return {"url": url, "ok": False, "ancho": None, "alto": None,
                "aviso": "No se pudo leer el tamaño (¿no es JPEG, PNG ni WebP?)."}
    ancho, alto = tam
    aviso = None
    if max(ancho, alto) < LADO_MINIMO:
        aviso = (f"Mide {ancho}×{alto} px; Amazon pide al menos {LADO_MINIMO} px en el lado "
                 "mayor para el zoom.")
    return {"url": url, "ok": True, "ancho": ancho, "alto": alto, "aviso": aviso}


def fotos_ok(urls):
    """Revisa varias fotos; devuelve la lista de resultados en el mismo orden."""
    return [revisar_foto(u) for u in urls if u]
