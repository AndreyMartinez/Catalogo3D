#!/usr/bin/env python3
"""Red de seguridad de traer_datos.py: lo que semana.py y plan.py leen de
cada publicación tiene que seguir saliendo igual aunque la descarga crezca.

Sin red ni credenciales: órdenes sintéticas pasadas por resumir_ordenes.
Las horas son de mediodía para que el día no dependa del huso horario.

Uso:  python3 prueba_traer_datos.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ml_api  # noqa: E402
import traer_datos  # noqa: E402


def _sin_red(*a, **k):
    raise AssertionError("la prueba intentó pegarle a la API de ML")


ml_api.pedir = _sin_red


def orden(oid, fecha, *items):
    """items: (mlm, titulo, sku, cantidad, precio, variation_id)."""
    return {
        "id": oid,
        "date_created": fecha,
        "order_items": [
            {"item": {"id": mlm, "title": titulo, "seller_sku": sku,
                      "variation_id": var},
             "quantity": cant, "unit_price": precio}
            for mlm, titulo, sku, cant, precio, var in items
        ],
    }


ORDENES = [
    # Una orden con dos publicaciones.
    orden(1, "2026-10-01T12:00:00.000-04:00",
          ("MLM1", "Organizador control remoto", "PC-1", 1, 209.0, 111),
          ("MLM2", "Organizador de cubiertos", "CU-1", 2, 198.0, None)),
    # Misma publicación, mismo día, otra variante.
    orden(2, "2026-10-01T15:30:00.000-04:00",
          ("MLM1", "Organizador control remoto", "PC-1", 1, 209.0, 112)),
    # Otro día.
    orden(3, "2026-10-02T11:00:00.000-04:00",
          ("MLM1", "Organizador control remoto", "PC-1", 3, 209.0, 111)),
    # Una línea sin id de publicación se ignora.
    orden(4, "2026-10-02T13:00:00.000-04:00",
          (None, "Sin id", None, 5, 10.0, None)),
]


def ventas(resultado):
    """resumir_ordenes devuelve hoy un dict; si llega a devolver más cosas,
    las ventas por publicación van primero."""
    return resultado[0] if isinstance(resultado, tuple) else resultado


class LoQueYaSeLee(unittest.TestCase):
    def setUp(self):
        self.v = ventas(traer_datos.resumir_ordenes(ORDENES))

    def test_publicaciones(self):
        self.assertEqual(set(self.v), {"MLM1", "MLM2"})

    def test_claves_que_leen_semana_y_plan(self):
        for reg in self.v.values():
            for clave in ("titulo", "seller_sku", "variantes", "por_dia", "unidades"):
                self.assertIn(clave, reg)

    def test_mlm1(self):
        r = self.v["MLM1"]
        self.assertEqual(r["titulo"], "Organizador control remoto")
        self.assertEqual(r["seller_sku"], "PC-1")
        self.assertEqual(r["unidades"], 5)
        self.assertEqual(r["por_dia"], {"2026-10-01": 2, "2026-10-02": 3})
        self.assertEqual(r["variantes"], {"111": 4, "112": 1})

    def test_mlm2(self):
        r = self.v["MLM2"]
        self.assertEqual(r["unidades"], 2)
        self.assertEqual(r["por_dia"], {"2026-10-01": 2})
        self.assertEqual(r["variantes"], {})

    def test_sin_ordenes(self):
        self.assertEqual(ventas(traer_datos.resumir_ordenes([])), {})


class FechaEnCDMX(unittest.TestCase):
    def test_madrugada_ml_es_dia_anterior(self):
        self.assertEqual(traer_datos.dia_mx("2026-10-03T00:30:00.000-04:00"), "2026-10-02")

    def test_mediodia_mismo_dia(self):
        self.assertEqual(traer_datos.dia_mx("2026-10-03T12:00:00.000-04:00"), "2026-10-03")

    def test_utc_con_z(self):
        self.assertEqual(traer_datos.dia_mx("2026-10-03T05:59:00Z"), "2026-10-02")
        self.assertEqual(traer_datos.dia_mx("2026-10-03T06:00:00Z"), "2026-10-03")

    def test_vacio_o_raro_no_truena(self):
        self.assertEqual(traer_datos.dia_mx(None), "")
        self.assertEqual(traer_datos.dia_mx(""), "")
        self.assertEqual(traer_datos.dia_mx("2026-10-03 algo"), "2026-10-03")

    def test_resumen_usa_hora_cdmx(self):
        v = ventas(traer_datos.resumir_ordenes([orden(
            9, "2026-10-03T01:15:00.000-04:00",
            ("MLM1", "Organizador control remoto", "PC-1", 1, 209.0, None))]))
        self.assertEqual(v["MLM1"]["por_dia"], {"2026-10-02": 1})


class TotalesPorDia(unittest.TestCase):
    def setUp(self):
        self.v, self.d = traer_datos.resumir_ordenes(ORDENES)

    def test_orden_con_dos_publicaciones_es_una_orden(self):
        dia = self.d["2026-10-01"]
        self.assertEqual(dia["ordenes"], 2)
        self.assertEqual(dia["unidades"], 4)               # 1 + 2 + 1
        self.assertAlmostEqual(dia["ingreso"], 209 + 2 * 198 + 209)
        self.assertEqual(dia["canceladas"], 0)

    def test_linea_sin_id_no_cuenta_orden(self):
        dia = self.d["2026-10-02"]
        self.assertEqual(dia["ordenes"], 1)                # la 4 no tiene id
        self.assertEqual(dia["unidades"], 3)

    def test_ingreso_por_publicacion(self):
        self.assertEqual(self.v["MLM1"]["ingreso_por_dia"],
                         {"2026-10-01": 418.0, "2026-10-02": 627.0})
        self.assertEqual(self.v["MLM2"]["ingreso_por_dia"], {"2026-10-01": 396.0})

    def test_cuadra_con_publicaciones(self):
        self.assertEqual(sum(d["unidades"] for d in self.d.values()),
                         sum(r["unidades"] for r in self.v.values()))


class Canceladas(unittest.TestCase):
    def test_solo_suman_canceladas(self):
        v, d = traer_datos.resumir_ordenes(ORDENES)
        antes = {k: dict(r, por_dia=dict(r["por_dia"])) for k, r in v.items()}
        traer_datos.contar_canceladas([
            orden(20, "2026-10-01T18:00:00.000-04:00",
                  ("MLM1", "Organizador control remoto", "PC-1", 4, 209.0, None)),
            orden(21, "2026-10-05T18:00:00.000-04:00"),
        ], d)
        self.assertEqual(d["2026-10-01"]["canceladas"], 1)
        self.assertEqual(d["2026-10-01"]["unidades"], 4)    # no cambia
        self.assertEqual(d["2026-10-05"],
                         {"ordenes": 0, "unidades": 0, "ingreso": 0.0, "canceladas": 1})
        self.assertEqual(v["MLM1"]["unidades"], antes["MLM1"]["unidades"])
        self.assertEqual(v["MLM1"]["por_dia"], antes["MLM1"]["por_dia"])


if __name__ == "__main__":
    unittest.main()
