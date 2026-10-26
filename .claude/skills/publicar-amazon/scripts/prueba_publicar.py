#!/usr/bin/env python3
"""Pruebas del publicador ML → Amazon, sin red ni credenciales reales.

Las credenciales de prueba son inventadas y viven en una carpeta temporal;
nunca se toca ~/.catalogo3d/.

Uso:  python3 prueba_publicar.py
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
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


if __name__ == "__main__":
    unittest.main()
