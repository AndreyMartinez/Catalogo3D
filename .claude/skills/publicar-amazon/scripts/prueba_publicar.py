#!/usr/bin/env python3
"""Pruebas del publicador ML → Amazon, sin red ni credenciales reales.

Las credenciales de prueba son inventadas y viven en una carpeta temporal;
nunca se toca ~/.catalogo3d/.

Uso:  python3 prueba_publicar.py
"""
import base64
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import borrador  # noqa: E402
import esquema  # noqa: E402
import sp_api  # noqa: E402

# Inventadas, con la forma de las reales.
CRED_FALSAS = {
    "client_id": "amzn1.application-oa2-client.0123456789abcdef0123456789abcdef",
    "client_secret": "amzn1.oa2-cs.v1.prueba0000000000000000000000000000000000000000000000000000",
    "refresh_token": "Atzr|IwEBIPrueba-de-refresco-inventado-para-las-pruebas-0000000000",
    "seller_id": "A1PRUEBA0000XX",
}


class Credenciales(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._tmp.name) / "amazon_credenciales.json"

    def tearDown(self):
        self._tmp.cleanup()

    def escribir(self, datos, modo=0o600):
        self.ruta.write_text(json.dumps(datos), encoding="utf-8")
        os.chmod(self.ruta, modo)

    def test_lee_con_600(self):
        self.escribir(CRED_FALSAS)
        self.assertEqual(sp_api.cargar_credenciales(self.ruta), CRED_FALSAS)

    def test_rechaza_644(self):
        self.escribir(CRED_FALSAS, 0o644)
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.cargar_credenciales(self.ruta)
        self.assertIn("chmod 600", str(e.exception))
        self.assertIn("644", str(e.exception))

    def test_falta_el_archivo(self):
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.cargar_credenciales(self.ruta)
        texto = str(e.exception)
        for campo in sp_api.CAMPOS:
            self.assertIn(campo, texto)
        self.assertIn("Autorizar aplicación", texto)
        self.assertIn("No los pegues en el chat", texto)
        # Los ejemplos de la ayuda no se confunden con secretos.
        self.assertIn("Atzr|…", texto)
        self.assertIn("amzn1.oa2-cs.v1.…", texto)

    def test_falta_un_campo_sin_ensenar_los_demas(self):
        datos = dict(CRED_FALSAS, seller_id="")
        self.escribir(datos)
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.cargar_credenciales(self.ruta)
        texto = str(e.exception)
        self.assertIn("le falta: seller_id", texto)
        for valor in datos.values():
            if valor:
                self.assertNotIn(valor, texto)

    def test_json_roto(self):
        self.ruta.write_text('{"client_id": "' + CRED_FALSAS["client_id"],
                             encoding="utf-8")
        os.chmod(self.ruta, 0o600)
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.cargar_credenciales(self.ruta)
        self.assertIn("no es JSON válido", str(e.exception))
        self.assertNotIn(CRED_FALSAS["client_id"], str(e.exception))


class Tapar(unittest.TestCase):

    def test_tapa_valores_cargados(self):
        sp_api._registrar_secreto("valor-cualquiera-registrado")
        texto = sp_api._tapar("falló con valor-cualquiera-registrado en el cuerpo")
        self.assertNotIn("valor-cualquiera-registrado", texto)
        self.assertIn("***", texto)

    def test_tapa_formas_de_lwa_sin_cargarlas(self):
        token = "Atza|IwEBIAccesoNuevoQueNadieRegistro-0000000000000000"
        secreto = "amzn1.oa2-cs.v1.otroSecretoNoRegistrado000000000000000"
        texto = sp_api._tapar(f'{{"access_token": "{token}", "s": "{secreto}"}}')
        self.assertNotIn(token, texto)
        self.assertNotIn(secreto, texto)

    def test_error_sale_tapado(self):
        e = sp_api.ErrorSP("LWA respondió: " + CRED_FALSAS["refresh_token"])
        self.assertNotIn(CRED_FALSAS["refresh_token"], str(e))


# ------------------------------------------------------------ peticiones

class _Respuesta:
    def __init__(self, cuerpo):
        self._cuerpo = cuerpo.encode() if isinstance(cuerpo, str) else cuerpo

    def read(self):
        return self._cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http(codigo, cuerpo=""):
    return urllib.error.HTTPError("https://x", codigo, "x", {}, io.BytesIO(cuerpo.encode()))


TOKEN_LWA = json.dumps({"access_token": "Atza|AccesoDePrueba-0000000000000000000000",
                        "expires_in": 3600})


class Peticiones(unittest.TestCase):
    """sp_api.pedir con urlopen sustituido: cada llamada saca la siguiente
    respuesta de un guion. Nadie duerme de verdad."""

    def setUp(self):
        self.guardado = (sp_api._abrir, sp_api._dormir, sp_api._cred,
                         sp_api._token, sp_api._vence, sp_api._ultima)
        sp_api._cred = dict(CRED_FALSAS)
        for v in CRED_FALSAS.values():
            sp_api._registrar_secreto(v)
        sp_api._token, sp_api._vence, sp_api._ultima = None, 0.0, 0.0
        self.esperas = []
        sp_api._dormir = self.esperas.append
        self.pedidos = []

    def tearDown(self):
        (sp_api._abrir, sp_api._dormir, sp_api._cred,
         sp_api._token, sp_api._vence, sp_api._ultima) = self.guardado

    def guion(self, *pasos):
        pasos = list(pasos)

        def abrir(pedido, timeout=None):
            self.pedidos.append(pedido)
            paso = pasos.pop(0)
            if isinstance(paso, Exception):
                raise paso
            return _Respuesta(paso)
        sp_api._abrir = abrir

    def a_sp(self):
        return [p for p in self.pedidos if p.full_url.startswith(sp_api.HOST)]

    def test_429_y_luego_200(self):
        self.guion(TOKEN_LWA, _http(429), '{"items": []}')
        r = sp_api.pedir("GET", "/listings/2021-08-01/items/A1",
                         {"marketplaceIds": [sp_api.MARKETPLACE], "x": None})
        self.assertEqual(r, {"items": []})
        self.assertEqual(len(self.a_sp()), 2)
        self.assertIn(1, self.esperas)
        url = self.a_sp()[0].full_url
        self.assertIn("marketplaceIds=A1AM78C64UM0Y8", url)
        self.assertNotIn("x=", url)
        self.assertTrue(self.a_sp()[0].get_header("X-amz-access-token").startswith("Atza|"))

    def test_seis_429_dan_error(self):
        self.guion(TOKEN_LWA, *[_http(429, "TooManyRequests") for _ in range(6)])
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.pedir("GET", "/x")
        self.assertIn("falló 6 veces", str(e.exception))
        self.assertEqual([x for x in self.esperas if x >= 1], list(sp_api.ESPERAS))

    def test_caida_de_red_reintenta(self):
        self.guion(TOKEN_LWA, urllib.error.URLError("timeout"), "{}")
        self.assertEqual(sp_api.pedir("GET", "/x"), {})

    def test_401_renueva_una_vez(self):
        otro = json.dumps({"access_token": "Atza|OtroAccesoRenovado-00000000000000000",
                           "expires_in": 3600})
        self.guion(TOKEN_LWA, _http(401), otro, '{"ok": 1}')
        self.assertEqual(sp_api.pedir("GET", "/x"), {"ok": 1})
        self.assertEqual(self.a_sp()[-1].get_header("X-amz-access-token"),
                         "Atza|OtroAccesoRenovado-00000000000000000")

    def test_403_persistente_explica_roles(self):
        self.guion(TOKEN_LWA, _http(403), TOKEN_LWA, _http(403, "Unauthorized"))
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.pedir("GET", "/x")
        self.assertIn("Product Listing", str(e.exception))

    def test_400_no_reintenta(self):
        self.guion(TOKEN_LWA, _http(400, '{"errors": [{"code": "InvalidInput"}]}'))
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.pedir("PUT", "/x", cuerpo={"a": 1})
        self.assertIn("400", str(e.exception))
        self.assertEqual(len(self.a_sp()), 1)
        self.assertEqual(self.a_sp()[0].get_header("Content-type"), "application/json")

    def test_ningun_secreto_en_los_errores(self):
        eco = " ".join(CRED_FALSAS.values()) + " Atza|AccesoDePrueba-0000000000000000000000"
        self.guion(TOKEN_LWA, _http(400, eco))
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.pedir("GET", "/x")
        for valor in list(CRED_FALSAS.values()) + ["Atza|AccesoDePrueba"]:
            self.assertNotIn(valor, str(e.exception))

    def test_lwa_rechaza(self):
        self.guion(_http(400, '{"error": "invalid_grant", "error_description": "' +
                         CRED_FALSAS["refresh_token"] + '"}'))
        with self.assertRaises(sp_api.ErrorSP) as e:
            sp_api.pedir("GET", "/x")
        self.assertIn("invalid_grant", str(e.exception))
        self.assertIn("Autorizar aplicación", str(e.exception))
        self.assertNotIn(CRED_FALSAS["refresh_token"], str(e.exception))

    def test_token_se_reusa(self):
        self.guion(TOKEN_LWA, "{}", "{}")
        sp_api.pedir("GET", "/x")
        sp_api.pedir("GET", "/y")
        lwa = [p for p in self.pedidos if p.full_url == sp_api.LWA]
        self.assertEqual(len(lwa), 1)


# ---------------------------------------------------------------- esquema

ESQUEMA_MINIMO = {"required": ["brand", "item_name"],
                  "properties": {"item_name": {"items": {"properties": {
                      "value": {"type": "string", "maxLength": 200}}}}}}


class CacheDeEsquema(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.guardado = (esquema.CARPETA, sp_api.pedir, sp_api._abrir)
        esquema.CARPETA = Path(self._tmp.name) / "amazon" / "esquemas"
        esquema._vistos.clear()
        self.version = "v1"
        self.bajadas = 0
        self.crudo = json.dumps(ESQUEMA_MINIMO).encode()

        def pedir(metodo, ruta, params=None, cuerpo=None):
            return {"productType": "CADDY", "displayName": "Caddy",
                    "productTypeVersion": {"version": self.version},
                    "propertyGroups": {"offer": {"propertyNames": ["list_price"]}},
                    "schema": {"link": {"resource": "https://firmado/x"},
                               "checksum": base64.b64encode(
                                   hashlib.md5(self.crudo).digest()).decode()}}

        def abrir(url, timeout=None):
            self.bajadas += 1
            return _Respuesta(self.crudo)
        sp_api.pedir, sp_api._abrir = pedir, abrir

    def tearDown(self):
        esquema.CARPETA, sp_api.pedir, sp_api._abrir = self.guardado
        esquema._vistos.clear()
        self._tmp.cleanup()

    def test_baja_una_vez_y_reusa(self):
        c = esquema.esquema("CADDY")
        self.assertEqual(esquema.obligatorios(c), ["brand", "item_name"])
        self.assertEqual(c["grupos"], {"offer": ["list_price"]})
        esquema._vistos.clear()              # otra corrida, misma versión
        esquema.esquema("CADDY")
        self.assertEqual(self.bajadas, 1)
        ruta = esquema.CARPETA / "CADDY.json"
        self.assertEqual(os.stat(ruta).st_mode & 0o777, 0o600)
        self.assertEqual(os.stat(esquema.CARPETA).st_mode & 0o777, 0o700)

    def test_version_nueva_baja_otra_vez(self):
        esquema.esquema("CADDY")
        esquema._vistos.clear()
        self.version = "v2"
        self.assertEqual(esquema.esquema("CADDY")["version"], "v2")
        self.assertEqual(self.bajadas, 2)

    def test_checksum_malo(self):
        crudo = self.crudo
        self.crudo = b'{"required": []}'
        # El checksum se calcula del bueno; lo que baja es otro.
        sp_api.pedir = (lambda viejo: lambda *a, **k: dict(
            viejo(*a, **k), schema={"link": {"resource": "x"},
                                    "checksum": base64.b64encode(
                                        hashlib.md5(crudo).digest()).decode()}))(sp_api.pedir)
        with self.assertRaises(sp_api.ErrorSP):
            esquema.esquema("CADDY")
        self.assertFalse((esquema.CARPETA / "CADDY.json").exists())


def _texto(valor):
    return [{"value": valor, "language_tag": "es_MX", "marketplace_id": "A1AM78C64UM0Y8"}]


ESQUEMA_REVISION = {"tipo": "CADDY", "esquema": {
    "required": ["brand", "item_name", "country_of_origin"],
    "additionalProperties": False,
    "properties": {
        "brand": {"items": {"required": ["language_tag", "value"], "properties": {
            "value": {"type": "string", "minLength": 1, "maxLength": 100}}}},
        "item_name": {"items": {"required": ["language_tag", "value"], "properties": {
            "value": {"type": "string", "maxLength": 200}}}},
        "generic_keyword": {"items": {"properties": {
            "value": {"type": "string", "maxUtf8ByteLength": 10}}}},
        "country_of_origin": {"items": {"required": ["value"], "properties": {
            "value": {"type": "string", "enum": ["MX", "US"],
                      "enumNames": ["México", "Estados Unidos"]}}}},
        "material": {"items": {"properties": {"value": {"type": "string", "anyOf": [
            {"type": "string"},
            {"type": "string", "enum": ["PLA", "Plástico", "Acero al carbono", "Acero inoxidable"],
             "enumNames": ["PLA", "Plástico", "Acero al carbono", "Acero inoxidable"]}]}}}},
        "supplier_declared_has_product_identifier_exemption": {"items": {"properties": {
            "value": {"type": "boolean", "enum": [False, True]}}}},
    }}}


class Revision(unittest.TestCase):

    def base(self):
        return {"brand": _texto("Generic"), "item_name": _texto("Organizador"),
                "country_of_origin": [{"value": "MX"}]}

    def errores(self, atributos):
        return [(h["campo"], h["detalle"]) for h in esquema.revisar(atributos, ESQUEMA_REVISION)
                if h["tipo"] == "error"]

    def test_limpio(self):
        self.assertEqual(esquema.revisar(self.base(), ESQUEMA_REVISION), [])

    def test_obligatorio_faltante(self):
        a = self.base()
        del a["brand"]
        a["item_name"] = []
        campos = [c for c, _ in self.errores(a)]
        self.assertEqual(sorted(campos), ["brand", "item_name"])

    def test_titulo_de_201(self):
        a = dict(self.base(), item_name=_texto("x" * 201))
        self.assertEqual(self.errores(a), [("item_name", "201 caracteres; el máximo es 200")])

    def test_bytes_cuentan_acentos(self):
        a = dict(self.base(), generic_keyword=_texto("ñañaña"))   # 6 letras, 9 bytes
        self.assertEqual(self.errores(a), [])
        a = dict(self.base(), generic_keyword=_texto("ñañañaña"))  # 12 bytes
        self.assertIn("12 bytes", self.errores(a)[0][1])

    def test_fuera_de_lista_cerrada_es_error(self):
        a = dict(self.base(), country_of_origin=[{"value": "México"}])
        self.assertIn("no está en la lista", self.errores(a)[0][1])

    def test_fuera_de_lista_sugerida_es_aviso(self):
        a = dict(self.base(), material=_texto("Madera"))
        h = esquema.revisar(a, ESQUEMA_REVISION)
        self.assertEqual([x["tipo"] for x in h], ["aviso"])

    def test_atributo_que_el_tipo_no_tiene(self):
        a = dict(self.base(), capacity=[{"value": 2.5, "unit": "liters"}])
        self.assertEqual(self.errores(a), [("capacity", "el tipo CADDY no tiene este atributo")])

    def test_subcampo_requerido(self):
        a = dict(self.base(), brand=[{"value": "Generic"}])
        self.assertEqual(self.errores(a), [("brand", "le falta language_tag")])

    def test_mas_cercano(self):
        valores, nombres, cerrada = esquema.opciones(ESQUEMA_REVISION, "material")
        self.assertFalse(cerrada)
        self.assertEqual(esquema.valor_mas_cercano("PLA", valores, nombres), "PLA")
        self.assertEqual(esquema.valor_mas_cercano("plastico", valores, nombres), "Plástico")
        self.assertIsNone(esquema.valor_mas_cercano("acero", valores, nombres))   # ambiguo
        self.assertIsNone(esquema.valor_mas_cercano("Madera", valores, nombres))
        v, n, cerrada = esquema.opciones(ESQUEMA_REVISION, "country_of_origin")
        self.assertTrue(cerrada)
        self.assertEqual(esquema.valor_mas_cercano("México", v, n), "MX")

    def test_palabra_completa(self):
        # «pla» no debe caer en «Plástico» por empezar igual.
        self.assertIsNone(esquema.valor_mas_cercano("pla", ["Plástico", "Vidrio"]))
        self.assertEqual(esquema.valor_mas_cercano("carbono", ["Acero al carbono", "Vidrio"]),
                         "Acero al carbono")

    def test_exencion(self):
        self.assertEqual(esquema.atributo_exencion(ESQUEMA_REVISION),
                         "supplier_declared_has_product_identifier_exemption")


# ------------------------------------------------------ reglas de texto

# Publicación real del Olas en ML (MLM3674350731), recortada. Es texto
# público de la propia publicación.
OLAS_TITULO = "Organizador De Cubiertos Olas Más Obsequios Negro"
OLAS_DESCRIPCION = """ORGANIZADOR DE CUBIERTOS OLAS - 3 COMPARTIMENTOS

Ten tus cubiertos ordenados y siempre a la mano con este portacubiertos de sobremesa.

Sepáralos en sus 3 compartimentos: tenedores, cucharas y cuchillos.

INCLUYE OBSEQUIO DE SIEMBRA
Además recibes una maceta pequeña, humus y semillas para que siembres tu propia planta. Un detalle que hace de tu compra un regalo especial.

CARACTERÍSTICAS
- Portacubiertos de sobremesa con 3 compartimentos
- Color: negro
- Material: PLA, bioplástico biodegradable de origen vegetal, acabado mate

CUIDADOS
- Lávalo a mano con agua tibia y jabón neutro
- Evita el sol directo y las fuentes de calor

IMPORTANTE
Pieza hecha con impresión 3D: puede presentar finas líneas de capa propias del proceso.

¿Tienes dudas? Escríbenos en preguntas, con gusto te respondemos.

¿Necesitas factura? Te la generamos. Solo envíanos tus datos fiscales por mensaje después de tu compra."""


class Texto(unittest.TestCase):

    def test_titulo_del_olas(self):
        t, avisos = borrador.limpiar_titulo(OLAS_TITULO)
        self.assertEqual(t, "Organizador De Cubiertos Olas Negro")
        self.assertIn("«Más Obsequios»", avisos[0])

    def test_titulos_reales(self):
        casos = {
            "Organizador De Control Remoto Más Regalos Sorpresa": "Organizador De Control Remoto",
            "Portalapices Moderno Diseño Mas Obsequio De Cultivo": "Portalapices Moderno Diseño",
            "Florero Decorativo Ondas, Con Regalo Cultivo Botanico Gris": "Florero Decorativo Ondas Gris",
            "Organizador De Tocador Baño Cepillos. Más Regalo Sorpresa Negro":
                "Organizador De Tocador Baño Cepillos Negro",
            "Organizador De Cubiertos Más Obsequio De Siembra Gris": "Organizador De Cubiertos Gris",
            "Portacepillos De Baño Más Regalos Savia Raiz Negro": "Portacepillos De Baño Negro",
        }
        for ml, esperado in casos.items():
            self.assertEqual(borrador.limpiar_titulo(ml)[0], esperado, ml)

    def test_promociones_y_caracteres(self):
        t, avisos = borrador.limpiar_titulo("Florero ¡Envío Gratis! Oferta Negro $")
        self.assertNotRegex(t.lower(), r"gratis|oferta|!|\$")
        self.assertEqual(len(avisos), 2)

    def test_marca_propia_al_frente(self):
        t, _ = borrador.limpiar_titulo("Portacepillos De Baño Más Regalos Savia Raiz Negro",
                                       marca="Savia Raíz")
        self.assertEqual(t, "Savia Raíz Portacepillos De Baño Negro")
        t, _ = borrador.limpiar_titulo("Florero Ondas Negro", marca="Savia Raíz")
        self.assertEqual(t, "Savia Raíz Florero Ondas Negro")

    def test_kit_de_siembra_se_queda_con_aviso(self):
        titulo = "Kit Maceta De Escritorio Con Humus, Semillas Y Tarro Blanco Carita"
        t, avisos = borrador.limpiar_titulo(titulo)
        self.assertEqual(t, titulo)
        self.assertTrue(any("restringido" in a for a in avisos))
        texto = "KIT MACETA\n\nEste kit trae una maceta, humus y semillas.\n\n¿Tienes dudas? Escríbenos."
        lim, _ = borrador.limpiar_descripcion(texto, kit=borrador.es_kit(titulo))
        self.assertIn("humus y semillas", borrador.descripcion(lim))

    def test_maceta_no_es_kit(self):
        t, avisos = borrador.limpiar_titulo("Maceta Geométrica Minimalista Negra")
        self.assertEqual(avisos, [])
        lim, avisos = borrador.limpiar_descripcion(
            "MACETA GEOMÉTRICA\n\nUna maceta para tu suculenta favorita.")
        self.assertEqual(avisos, [])
        self.assertIn("maceta para tu suculenta", borrador.descripcion(lim))

    def test_descripcion_sin_obsequio_ni_cierre(self):
        lim, avisos = borrador.limpiar_descripcion(OLAS_DESCRIPCION)
        todo = borrador.descripcion(lim) + " ".join(borrador.vinetas(lim))
        for fuera in ("OBSEQUIO", "humus", "semillas", "regalo", "¿Tienes dudas?", "factura"):
            self.assertNotIn(fuera, todo)
        self.assertIn("CARACTERÍSTICAS", borrador.descripcion(lim))
        self.assertTrue(any("restringido" in a for a in avisos))
        self.assertTrue(any("cierre de ML" in a for a in avisos))

    def test_vinetas(self):
        lim, _ = borrador.limpiar_descripcion(OLAS_DESCRIPCION)
        v = borrador.vinetas(lim, "MEDIDAS: 19.6 x 7.8 x 10.2 cm.")
        self.assertEqual(len(v), 5)
        self.assertTrue(v[0].startswith("Ten tus cubiertos"))
        self.assertEqual(v[1], "CARACTERÍSTICAS: Portacubiertos de sobremesa con 3 compartimentos; "
                               "Color: negro; Material: PLA, bioplástico biodegradable de origen "
                               "vegetal, acabado mate.")
        self.assertEqual(v[2], "MEDIDAS: 19.6 x 7.8 x 10.2 cm.")
        self.assertTrue(v[3].startswith("CUIDADOS: Lávalo a mano"))
        self.assertTrue(v[4].startswith("IMPORTANTE: Pieza hecha"))
        # Sin medidas, el segundo párrafo de entrada ocupa el lugar.
        v = borrador.vinetas(lim)
        self.assertTrue(v[1].startswith("Sepáralos"))

    def test_sin_descripcion(self):
        lim, _ = borrador.limpiar_descripcion("¿Necesitas factura? Te la generamos.")
        self.assertEqual(lim, [])
        self.assertEqual(borrador.vinetas(lim, "MEDIDAS: 1 cm."), ["MEDIDAS: 1 cm."])

    def test_palabras_clave(self):
        claves = borrador.palabras_clave(
            OLAS_TITULO, "Organizador De Cubiertos Olas Negro",
            ["Hogar, Muebles y Jardín", "Cocina", "Organizadores de Cubiertos"])
        palabras = claves.split()
        self.assertIn("cocina", palabras)
        for fuera in ("organizador", "cubiertos", "obsequios", "de", "y"):
            self.assertNotIn(fuera, palabras)
        self.assertEqual(len(palabras), len(set(palabras)))
        largo = borrador.palabras_clave("", "", ["palabra" + "x" * 20 + str(i) for i in range(40)])
        self.assertLess(len(largo.encode("utf-8")), 250)


if __name__ == "__main__":
    unittest.main()
