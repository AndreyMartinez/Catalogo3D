#!/usr/bin/env python3
"""Publicador MercadoLibre → Amazon México.

Trabaja por borradores: uno por publicación activa de ML (o por variación)
en ~/.catalogo3d/amazon/borradores/. El flujo:

  lista                       activas de ML y en qué va cada una en Amazon
  armar MLM… | --todas        crea los borradores que falten
  ver MLM…                    el borrador legible, con lo que falta revisar
  aprobar MLM campo…          quita campos de «por revisar»
  validar MLM…                vista previa en Amazon (no crea nada)
  comparar MLM…               lado a lado contra lo ya publicado
  estado MLM…                 ASIN, estado e issues de lo publicado
  publicar MLM [--confirmo SKU] [--campos a,b]
                              publica de verdad; sin --confirmo solo muestra

MLM… acepta MLM123 o MLM123-<variación>.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent.parent / "colecta-full" / "scripts"))
import borrador  # noqa: E402
import esquema  # noqa: E402
import sp_api  # noqa: E402

CARPETA = sp_api.CARPETA / "amazon"
BORRADORES = CARPETA / "borradores"
PUBLICADAS = CARPETA / "publicadas.json"
CATEGORIAS = AQUI.parent / "categorias.json"
DISENOS = Path.home() / "Desktop" / "own design 3d"
CATALOGO = DISENOS / ".catalogo3d_mercadolibre.json"
COSTOS = DISENOS / ".catalogo3d_costos.json"

# El Olas se publicó a mano el 2026-10-25 y Amazon le puso su propio SKU.
PUBLICADAS_INICIALES = {
    "5Z-W3LH-N087": {"mlm": "MLM3674350731", "variacion": None, "asin": "B0HP8CH8LT",
                     "fecha": "2026-10-25", "precio": 209, "origen": "a mano en Seller Central"},
}


class ErrorPublicador(Exception):
    pass


# --------------------------------------------------------------- archivos

def leer_json(ruta, defecto=None):
    """JSON de un archivo; si está roto (editado a mano), dice archivo y
    línea y no sigue: nadie sobrescribe un borrador que no se pudo leer."""
    ruta = Path(ruta)
    if not ruta.exists():
        return defecto
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErrorPublicador(f"{ruta} tiene un error de JSON en la línea {e.lineno}, "
                              f"columna {e.colno}: {e.msg}. Corrígelo y vuelve a correr.") from None


def guardar_privado(ruta, datos):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    for carpeta in (ruta.parent, CARPETA):
        if carpeta.exists():
            os.chmod(carpeta, 0o700)
    temporal = ruta.with_suffix(".tmp")
    viejo = os.umask(0o077)
    try:
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    finally:
        os.umask(viejo)
    os.chmod(temporal, 0o600)
    temporal.replace(ruta)


def ruta_borrador(clave):
    return BORRADORES / f"{clave}.json"


def leer_borrador(clave):
    br = leer_json(ruta_borrador(clave))
    if br is None:
        raise ErrorPublicador(f"No hay borrador de {clave}. Córrelo antes con: armar {clave}")
    return br


def publicadas():
    datos = leer_json(PUBLICADAS)
    if datos is None:
        datos = dict(PUBLICADAS_INICIALES)
        guardar_privado(PUBLICADAS, datos)
    return datos


def clave_de(mlm, variacion=None):
    return f"{mlm}-{variacion}" if variacion else mlm


def separar(clave):
    mlm, _, var = clave.partition("-")
    return mlm.upper(), (var or None)


# ---------------------------------------------------------------- ML

_ml = {}


def _modulos_ml():
    if not _ml:
        import ml_api
        import traer_datos
        _ml.update(api=ml_api, datos=traer_datos)
    return _ml["api"], _ml["datos"]


def activas_ml():
    """{MLM: ítem} de las publicaciones activas, en el orden de ML."""
    ml_api, traer_datos = _modulos_ml()
    try:
        yo = ml_api.pedir("/users/me")
        ids = traer_datos.listar_publicaciones(yo["id"])
        items = traer_datos.detalle_publicaciones(ids)
    except ml_api.ErrorML as e:
        raise ErrorPublicador(f"MercadoLibre no respondió; no se escribió nada.\n{e}") from None
    return {i: items[i] for i in ids if i in items and items[i].get("status") == "active"}


def descripcion_ml(mlm):
    ml_api, _ = _modulos_ml()
    try:
        return ml_api.pedir(f"/items/{mlm}/description").get("plain_text") or ""
    except ml_api.ErrorML as e:
        raise ErrorPublicador(f"No se pudo leer la descripción de {mlm}; no se escribió nada.\n{e}") from None


_rutas = {}


def ruta_categoria(cat_id):
    if cat_id not in _rutas:
        ml_api, _ = _modulos_ml()
        try:
            c = ml_api.pedir(f"/categories/{cat_id}")
            _rutas[cat_id] = [p["name"] for p in c.get("path_from_root") or []]
        except ml_api.ErrorML:
            _rutas[cat_id] = []
    return _rutas[cat_id]


def claves_de_item(item):
    vs = item.get("variations") or []
    return [clave_de(item["id"], str(v["id"])) for v in vs] or [item["id"]]


def variacion_de(item, var_id):
    if not var_id:
        return None
    for v in item.get("variations") or []:
        if str(v["id"]) == str(var_id):
            return v
    raise ErrorPublicador(f"{item['id']} no tiene la variación {var_id}.")


# --------------------------------------------------------------- comandos

def _esquema_de(tipo, avisar=print):
    if not tipo:
        return None
    try:
        return esquema.esquema(tipo)
    except sp_api.ErrorSP as e:
        avisar(f"  (sin esquema de {tipo}: {e})")
        return None


def cmd_lista(args):
    activas = activas_ml()
    pub = publicadas()
    con_var = 0
    print(f"{len(activas)} publicaciones activas en ML\n")
    for mlm, item in activas.items():
        claves = claves_de_item(item)
        if item.get("variations"):
            con_var += 1
        for clave in claves:
            br = leer_json(ruta_borrador(clave))
            if br:
                edo, sku_ = borrador.estado(br), br.get("sku")
            else:
                sku_ = next((s for s, r in pub.items() if clave_de(r.get("mlm"), r.get("variacion")) == clave), None)
                edo = "publicado" if sku_ else "sin borrador"
            marca = " (variación)" if "-" in clave else ""
            print(f"  {clave:28} {edo:13} {sku_ or '':22} {item['title'][:55]}{marca}")
    print(f"\n{con_var} con variaciones (un borrador por variación).")
    return 0


def cmd_armar(args):
    activas = activas_ml()
    if args.todas:
        pedidas = [c for item in activas.values() for c in claves_de_item(item)]
    else:
        pedidas = []
        for c in args.claves:
            mlm, var = separar(c)
            if mlm not in activas:
                raise ErrorPublicador(f"{mlm} no está entre las activas de ML.")
            pedidas += [clave_de(mlm, var)] if var else claves_de_item(activas[mlm])
    if not pedidas:
        raise ErrorPublicador("Di qué publicaciones (MLM…) o usa --todas.")

    conf = leer_json(CATEGORIAS)
    pub = publicadas()
    usados = set(pub)
    for ruta in BORRADORES.glob("*.json") if BORRADORES.exists() else []:
        usados.add((leer_json(ruta) or {}).get("sku"))
    pesos = borrador.pesos_del_catalogo(leer_json(CATALOGO, {}))
    costos = leer_json(COSTOS)

    # Primero se lee todo de ML; si algo falla, no se escribe ningún borrador.
    nuevos, existentes = [], []
    for clave in pedidas:
        mlm, var = separar(clave)
        item = activas[mlm]
        actual = leer_json(ruta_borrador(clave))
        if actual:
            existentes.append((clave, actual, item, variacion_de(item, var)))
        else:
            nuevos.append((clave, item, variacion_de(item, var), descripcion_ml(mlm)))

    for clave, actual, item, var in existentes:
        cambios = borrador.cambios_en_ml(actual, item, var)
        if cambios:
            print(f"{clave}: ya tiene borrador; en ML cambió desde que se armó:")
            for campo, antes, ahora in cambios:
                print(f"    {campo}: {antes!r} → {ahora!r}")
            print("  El borrador no se tocó: decide tú si copias el cambio.")
        else:
            print(f"{clave}: ya tiene borrador; sin cambios en ML.")

    for clave, item, var, texto in nuevos:
        cat = (conf.get("categorias") or {}).get(item.get("category_id")) or {}
        ctx = {"categorias": conf, "pesos": pesos, "costos": costos, "publicadas": pub,
               "skus": usados, "ruta_categoria": ruta_categoria(item.get("category_id")),
               "esquema": _esquema_de(cat.get("tipo_producto"))}
        br = borrador.armar(item, texto, ctx, var)
        br["origen_ml"]["leido"] = datetime.now(timezone.utc).date().isoformat()
        usados.add(br["sku"])
        guardar_privado(ruta_borrador(clave), br)
        print(f"{clave}: borrador nuevo → {br['sku']}  «{br['titulo']}»"
              f"  ({len(br['por_revisar'])} por revisar, {len(br['avisos'])} avisos)")
    return 0


def _linea(etiqueta, valor):
    print(f"  {etiqueta:16} {valor}")


def _txt(x):
    return "—" if x in (None, "", []) else x


def cmd_ver(args):
    for clave in args.claves:
        br = leer_borrador(clave.upper())
        cache = _esquema_de(br.get("tipo_producto"))
        print(f"\n=== {clave.upper()} · {br['sku']} · {borrador.estado(br)} ===")
        _linea("tipo", f"{_txt(br.get('tipo_producto'))}" + (f" ({cache['nombre']})" if cache else ""))
        _linea("título", f"{br['titulo']}  [{len(br['titulo'])} car.]")
        for i, v in enumerate(br.get("vinetas") or [], 1):
            _linea(f"viñeta {i}", v)
        desc = br.get("descripcion") or ""
        _linea("descripción", (desc[:300] + "…") if len(desc) > 300 else _txt(desc))
        _linea("palabras clave", _txt(br.get("palabras_clave")))
        for k, v in (br.get("atributos") or {}).items():
            _linea(k, _txt(v))
        a, p = br["medidas"]["articulo"], br["medidas"]["paquete"]
        _linea("artículo", f"{_txt(a['frente_cm'])} frente × {_txt(a['fondo_cm'])} fondo × "
                           f"{_txt(a['alto_cm'])} alto cm · {_txt(a['peso_g'])} g")
        _linea("paquete", f"{_txt(p['largo_cm'])} × {_txt(p['ancho_cm'])} × {_txt(p['alto_cm'])} cm"
                          f" · {_txt(p['peso_g'])} g")
        f = br["fotos"]
        _linea("foto principal", f"{_txt(f.get('principal'))}  (Amazon pide fondo blanco, sin texto)")
        _linea("otras fotos", f"{len(f.get('otras') or [])}"
                              + (f", {len(f['excluidas'])} excluidas" if f.get("excluidas") else ""))
        _linea("precio", f"${_txt(br.get('precio'))}"
                         + (f"  (costo como en ML ${br['costo_ref']})" if br.get("costo_ref") else ""))
        e = br.get("envio") or {}
        _linea("envío", f"{_txt(e.get('modo'))}" + (f", {e['cantidad']} piezas" if e.get("cantidad") else ""))
        _linea("por revisar", ", ".join(br.get("por_revisar") or []) or "nada")
        for av in br.get("avisos") or []:
            print(f"  ⚠ {av}")
        if cache:
            try:
                hallazgos = esquema.revisar(borrador.payload(br, cache)["attributes"], cache)
            except borrador.ErrorBorrador as ex:
                hallazgos = [{"campo": "borrador", "tipo": "error", "detalle": str(ex)}]
            for h in hallazgos:
                print(f"  {'✖' if h['tipo'] == 'error' else '·'} {h['campo']}: {h['detalle']}")
        val = br.get("validacion")
        if val:
            vigente = "vigente" if val.get("huella") == borrador.huella(br) else "vieja: cambió el borrador"
            _linea("validación", f"{val.get('status')} el {val.get('fecha')} ({vigente})")
    return 0


def cmd_aprobar(args):
    clave = args.clave.upper()
    br = leer_borrador(clave)
    pendientes = br.get("por_revisar") or []
    desconocidos = [c for c in args.campos if c not in pendientes]
    if desconocidos:
        print(f"No están por revisar en {clave}: {', '.join(desconocidos)}. "
              f"Pendientes: {', '.join(pendientes) or 'ninguno'}. No cambié nada.")
        return 1
    br["por_revisar"] = [c for c in pendientes if c not in args.campos]
    guardar_privado(ruta_borrador(clave), br)
    print(f"{clave}: aprobado {', '.join(args.campos)}. "
          f"Falta: {', '.join(br['por_revisar']) or 'nada'}.")
    return 0


# ------------------------------------------------------------ Amazon

RUTA_LISTINGS = "/listings/2021-08-01/items"
_GTIN = ("externally_assigned_product_identifier", "product_identifier_exemption")


def _ruta_sku(sku_):
    import urllib.parse
    return f"{RUTA_LISTINGS}/{sp_api.seller_id()}/{urllib.parse.quote(sku_, safe='')}"


def leer_listing(sku_, incluir=("summaries", "attributes", "issues", "offers",
                                "fulfillmentAvailability", "productTypes")):
    """El SKU tal como está en Amazon, o None si no existe."""
    try:
        return sp_api.pedir("GET", _ruta_sku(sku_), {
            "marketplaceIds": [sp_api.MARKETPLACE], "includedData": list(incluir),
            "issueLocale": sp_api.LOCALE})
    except sp_api.ErrorSP as e:
        if "-> 404" in str(e):
            return None
        raise


def es_issue_gtin(issue):
    nombres = " ".join(issue.get("attributeNames") or [])
    texto = (issue.get("message") or "").lower()
    return any(g in nombres for g in _GTIN) or "gtin" in texto or "exenci" in texto


def es_issue_imagen(issue):
    nombres = " ".join(issue.get("attributeNames") or [])
    texto = (issue.get("message") or "").lower()
    return "image_locator" in nombres or "imagen" in texto or "image" in texto


def imprimir_issues(issues, marca="Generic"):
    if not issues:
        print("  Sin observaciones de Amazon.")
        return
    for i in issues:
        donde = ", ".join(i.get("attributeNames") or []) or "general"
        signo = {"ERROR": "✖", "WARNING": "⚠"}.get(i.get("severity"), "·")
        print(f"  {signo} [{i.get('code')}] {donde}: {i.get('message')}")
        if es_issue_gtin(i):
            print(f"      → Es la exención de GTIN: la marca {marca} no la tiene para este tipo. "
                  "Se tramita en Seller Central → Catálogo → Exención de GTIN; no reintento.")
        if es_issue_imagen(i):
            print("      → Es de la foto principal: esta sí hay que cambiarla "
                  "(fondo blanco puro, sin texto ni accesorios).")


def cmd_validar(args):
    errores = 0
    for c in args.claves:
        clave = c.upper()
        br = leer_borrador(clave)
        print(f"\n=== {clave} · {br['sku']} ===")
        if not br.get("tipo_producto"):
            print("  Falta el tipo de producto en el borrador (y en categorias.json).")
            errores += 1
            continue
        cache = esquema.esquema(br["tipo_producto"])
        try:
            cuerpo = borrador.payload(br, cache)
        except borrador.ErrorBorrador as e:
            print(f"  ✖ {e}")
            errores += 1
            continue
        locales = [h for h in esquema.revisar(cuerpo["attributes"], cache) if h["tipo"] == "error"]
        if locales:
            print("  Antes de mandarlo a Amazon hay que corregir:")
            for h in locales:
                print(f"  ✖ {h['campo']}: {h['detalle']}")
            errores += 1
            continue
        r = sp_api.pedir("PUT", _ruta_sku(br["sku"]), {
            "marketplaceIds": [sp_api.MARKETPLACE], "mode": "VALIDATION_PREVIEW",
            "includedData": ["issues", "identifiers"], "issueLocale": sp_api.LOCALE},
            cuerpo)
        estado_ = r.get("status")
        issues = r.get("issues") or []
        br["validacion"] = {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "huella": borrador.huella(br), "status": estado_, "issues": issues}
        guardar_privado(ruta_borrador(clave), br)
        print(f"  Vista previa de Amazon: {estado_} (no se creó ni cambió nada)")
        imprimir_issues(issues, (br.get("atributos") or {}).get("brand", "Generic"))
        if estado_ != "VALID":
            errores += 1
        elif br.get("por_revisar"):
            print(f"  Válido para Amazon. Para publicar falta aprobar: {', '.join(br['por_revisar'])}.")
    return 1 if errores else 0


def _simple(entradas):
    """Valor de un atributo sin marketplace_id ni language_tag, para comparar."""
    salida = []
    for e in entradas or []:
        if isinstance(e, dict):
            d = {k: v for k, v in e.items() if k not in ("marketplace_id", "language_tag")}
            salida.append(d["value"] if list(d) == ["value"] else d)
        else:
            salida.append(e)
    return salida[0] if len(salida) == 1 else salida


def _corto(valor, ancho=60):
    texto = valor if isinstance(valor, str) else json.dumps(valor, ensure_ascii=False)
    return texto if len(texto) <= ancho else texto[:ancho - 1] + "…"


def diferencias(publicado, propuesto):
    """[(atributo, en Amazon, en el borrador)] de lo que no coincide."""
    filas = []
    for nombre in sorted(set(publicado) | set(propuesto)):
        a, b = _simple(publicado.get(nombre)), _simple(propuesto.get(nombre))
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            filas.append((nombre, a if nombre in publicado else None,
                          b if nombre in propuesto else None))
    return filas


def cmd_comparar(args):
    for c in args.claves:
        clave = c.upper()
        br = leer_borrador(clave)
        actual = leer_listing(br["sku"])
        print(f"\n=== {clave} · {br['sku']} ===")
        if actual is None:
            print("  Ese SKU no existe en Amazon: nada que comparar.")
            continue
        resumen = (actual.get("summaries") or [{}])[0]
        print(f"  ASIN {resumen.get('asin')} · {', '.join(resumen.get('status') or [])} · "
              f"tipo {(actual.get('productTypes') or [{}])[0].get('productType')}")
        cache = _esquema_de(br.get("tipo_producto"))
        propuesto = borrador.payload(br, cache)["attributes"]
        filas = diferencias(actual.get("attributes") or {}, propuesto)
        print(f"  {len(filas)} diferencias (izquierda: Amazon hoy · derecha: borrador)\n")
        for nombre, en_amz, en_br in filas:
            print(f"  {nombre}")
            print(f"      Amazon:   {_corto(_txt(en_amz), 100)}")
            print(f"      borrador: {_corto(_txt(en_br), 100)}")
        imprimir_issues(actual.get("issues") or [])
    return 0


def cmd_estado(args):
    pub = publicadas()
    for c in args.claves:
        clave = c.upper()
        br = leer_json(ruta_borrador(clave))
        sku_ = (br or {}).get("sku") or next(
            (s for s, r in pub.items() if clave_de(r.get("mlm"), r.get("variacion")) == clave), None)
        if not sku_:
            print(f"{clave}: no tiene SKU todavía (ni borrador ni publicación).")
            continue
        actual = leer_listing(sku_, ("summaries", "issues", "offers", "fulfillmentAvailability"))
        if actual is None:
            print(f"{clave} · {sku_}: no está en Amazon.")
            continue
        r = (actual.get("summaries") or [{}])[0]
        print(f"\n{clave} · {sku_} · ASIN {r.get('asin')} · {', '.join(r.get('status') or [])}")
        print(f"  {r.get('itemName')}")
        for o in actual.get("offers") or []:
            print(f"  oferta {o.get('offerType')}: ${(o.get('price') or {}).get('amount')}")
        for f in actual.get("fulfillmentAvailability") or []:
            print(f"  envío {f.get('fulfillmentChannelCode')}: {f.get('quantity', '—')} piezas")
        imprimir_issues(actual.get("issues") or [])
        if r.get("asin") and sku_ in pub and pub[sku_].get("asin") != r["asin"]:
            pub[sku_]["asin"] = r["asin"]
            guardar_privado(PUBLICADAS, pub)
    return 0


# -------------------------------------------------------------- publicar

def _confirmado(args, sku_):
    """True si el SKU se confirmó con --confirmo (o tecleado en una terminal
    interactiva). Un --confirmo con otro SKU es error, no un «no»."""
    if args.confirmo is not None:
        if args.confirmo != sku_:
            raise ErrorPublicador(f"--confirmo {args.confirmo} no es el SKU de esta publicación "
                                  f"({sku_}). No se mandó nada.")
        return True
    if sys.stdin.isatty():
        return input(f"Escribe el SKU para publicar ({sku_}): ").strip() == sku_
    return False


def _registrar(clave, br, respuesta, precio_):
    registro = {"mlm": br["mlm"], "variacion": br.get("variacion"), "asin": None,
                "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "precio": precio_, "submission_id": respuesta.get("submissionId")}
    for ident in respuesta.get("identifiers") or []:
        for i in ident.get("identifiers") or []:
            if i.get("identifierType") == "ASIN":
                registro["asin"] = i.get("identifier")
    pub = publicadas()
    pub[br["sku"]] = {**pub.get(br["sku"], {}), **registro}
    guardar_privado(PUBLICADAS, pub)
    br["publicado"] = registro
    guardar_privado(ruta_borrador(clave), br)


def cmd_publicar(args):
    clave = args.clave.upper()
    br = leer_borrador(clave)
    sku_ = br["sku"]
    if args.confirmo is not None and args.confirmo != sku_:
        raise ErrorPublicador(f"--confirmo {args.confirmo} no es el SKU de {clave} ({sku_}). "
                              "No se mandó nada.")
    campos = [c.strip() for c in (args.campos or "").split(",") if c.strip()]

    if not campos:
        # Publicación completa: los candados del Req. 9.1, antes de tocar la red.
        if borrador.estado(br) == "publicado":
            raise ErrorPublicador(f"{clave} ya está publicado como {sku_}. Para cambiar campos "
                                  "usa --campos.")
        if borrador.estado(br) != "validado":
            raise ErrorPublicador(f"{clave} no está validado con su contenido actual. "
                                  f"Corre antes: validar {clave}")
        if br.get("por_revisar"):
            raise ErrorPublicador(f"{clave} tiene campos por revisar: {', '.join(br['por_revisar'])}. "
                                  f"Revísalos y apruébalos con: aprobar {clave} <campo>…")

    cache = esquema.esquema(br["tipo_producto"])
    cuerpo = borrador.payload(br, cache)
    actual = leer_listing(sku_)

    if actual is None:
        if campos:
            raise ErrorPublicador(f"{sku_} no existe en Amazon: --campos es para cambiar una "
                                  "publicación que ya existe.")
        e = br.get("envio") or {}
        print(f"\nPublicar en Amazon México:\n  SKU      {sku_}\n  título   {br['titulo']}\n"
              f"  precio   ${br['precio']}\n  envío    {e.get('modo')}"
              + (f", {e['cantidad']} piezas" if e.get("cantidad") else "")
              + f"\n  foto     {br['fotos']['principal']}\n  tipo     {br['tipo_producto']}")
        if not _confirmado(args, sku_):
            print(f"\nNo se publicó. Para publicar: publicar {clave} --confirmo {sku_}")
            return 0
        # Fuera de la vista previa Amazon no admite includedData=identifiers
        # (400 «Cannot return identifiers outside of validation mode»): el
        # ASIN se lee después con «estado».
        r = sp_api.pedir("PUT", _ruta_sku(sku_), {
            "marketplaceIds": [sp_api.MARKETPLACE], "includedData": ["issues"],
            "issueLocale": sp_api.LOCALE}, cuerpo)
        print(f"\nAmazon respondió: {r.get('status')}")
        imprimir_issues(r.get("issues") or [])
        if r.get("status") == "ACCEPTED":
            _registrar(clave, br, r, br.get("precio"))
            print(f"Registrado en {PUBLICADAS.name}. El ASIN llega en unos minutos: estado {clave}")
            return 0
        return 1

    # El SKU ya existe: no se reemplaza; solo los campos que se pidan.
    filas = diferencias(actual.get("attributes") or {}, cuerpo["attributes"])
    print(f"\n{sku_} ya existe en Amazon. {len(filas)} diferencias con el borrador:")
    for nombre, en_amz, en_br in filas:
        print(f"  {nombre:40} Amazon: {_corto(_txt(en_amz), 45):45}  borrador: {_corto(_txt(en_br), 45)}")
    if not campos:
        print(f"\nNo se cambió nada. Para actualizar campos: publicar {clave} "
              f"--campos color,item_package_weight --confirmo {sku_}")
        return 0
    faltan = [c for c in campos if c not in cuerpo["attributes"]]
    if faltan:
        raise ErrorPublicador(f"El borrador no tiene: {', '.join(faltan)}. No se mandó nada.")
    parche = {"productType": cuerpo["productType"], "patches": [
        {"op": "replace", "path": f"/attributes/{c}", "value": cuerpo["attributes"][c]}
        for c in campos]}
    params = {"marketplaceIds": [sp_api.MARKETPLACE], "includedData": ["issues"],
              "issueLocale": sp_api.LOCALE}
    previa = sp_api.pedir("PATCH", _ruta_sku(sku_), dict(params, mode="VALIDATION_PREVIEW"), parche)
    print(f"\nVista previa del cambio ({', '.join(campos)}): {previa.get('status')}")
    imprimir_issues(previa.get("issues") or [])
    if previa.get("status") != "VALID":
        return 1
    if not _confirmado(args, sku_):
        print(f"\nNo se cambió nada. Para aplicarlo: publicar {clave} --campos {','.join(campos)} "
              f"--confirmo {sku_}")
        return 0
    r = sp_api.pedir("PATCH", _ruta_sku(sku_), params, parche)
    print(f"Amazon respondió: {r.get('status')}")
    imprimir_issues(r.get("issues") or [])
    return 0 if r.get("status") == "ACCEPTED" else 1


# ------------------------------------------------------------------ main

def parser():
    ap = argparse.ArgumentParser(description="Publicador MercadoLibre → Amazon México")
    sub = ap.add_subparsers(dest="comando", required=True)
    sub.add_parser("lista", help="activas de ML y su estado en Amazon").set_defaults(fn=cmd_lista)
    p = sub.add_parser("armar", help="crea los borradores que falten")
    p.add_argument("claves", nargs="*")
    p.add_argument("--todas", action="store_true")
    p.set_defaults(fn=cmd_armar)
    p = sub.add_parser("ver", help="muestra borradores")
    p.add_argument("claves", nargs="+")
    p.set_defaults(fn=cmd_ver)
    p = sub.add_parser("aprobar", help="quita campos de «por revisar»")
    p.add_argument("clave")
    p.add_argument("campos", nargs="+")
    p.set_defaults(fn=cmd_aprobar)
    for nombre, fn, ayuda in (("validar", cmd_validar, "vista previa en Amazon (no crea nada)"),
                              ("comparar", cmd_comparar, "lado a lado contra lo publicado"),
                              ("estado", cmd_estado, "ASIN, estado e issues en Amazon")):
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("claves", nargs="+")
        p.set_defaults(fn=fn)
    p = sub.add_parser("publicar", help="publica de verdad (pide --confirmo SKU)")
    p.add_argument("clave")
    p.add_argument("--confirmo", metavar="SKU",
                   help="el SKU exacto; solo después del «sí» del usuario a esta publicación")
    p.add_argument("--campos", help="si el SKU ya existe: atributos a actualizar, separados por coma")
    p.set_defaults(fn=cmd_publicar)
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return args.fn(args)
    except (ErrorPublicador, sp_api.ErrorSP, borrador.ErrorBorrador) as e:
        print(sp_api._tapar(str(e)), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
