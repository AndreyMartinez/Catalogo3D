#!/usr/bin/env python3
"""Pruebas de mes.py con datos sintéticos: sin red, sin credenciales y sin
tocar ~/.catalogo3d ni .claude/mercado.

Uso:  python3 prueba_mes.py
"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mes  # noqa: E402

MX = mes.HUSO_MX


def dt(texto):
    """Fecha y hora en la CDMX."""
    return datetime.fromisoformat(texto).replace(tzinfo=MX)


def serie(desde, hasta, valor=1):
    d, out = date.fromisoformat(desde), {}
    while d <= date.fromisoformat(hasta):
        out[d.isoformat()] = valor
        d += timedelta(days=1)
    return out


# ── 3.1 Calendario y comparación ──────────────────────────────────────────

class Calendario(unittest.TestCase):
    def test_mes_en_curso_corta_el_dia_anterior_a_la_descarga(self):
        c = mes.corte(dt("2026-10-16T08:00"), date(2026, 10, 16))
        self.assertEqual((c["inicio"], c["hasta"], c["dias"]),
                         (date(2026, 10, 1), date(2026, 10, 15), 15))
        self.assertFalse(c["cerrado"])
        self.assertEqual(c["parcial"], date(2026, 10, 16))
        self.assertEqual(c["dias_mes"], 31)

    def test_mes_cerrado(self):
        c = mes.corte(dt("2026-10-16T08:00"), date(2026, 10, 16), (2026, 9))
        self.assertTrue(c["cerrado"])
        self.assertEqual((c["hasta"], c["dias"]), (date(2026, 9, 30), 30))
        self.assertIsNone(c["parcial"])

    def test_dia_uno_sin_dias_completos(self):
        c = mes.corte(dt("2026-10-01T09:00"), date(2026, 10, 1))
        self.assertEqual(c["dias"], 0)
        self.assertIsNone(c["hasta"])
        # El mes anterior ya quedó cerrado con esa descarga.
        self.assertTrue(mes.corte(dt("2026-10-01T09:00"), date(2026, 10, 1), (2026, 9))["cerrado"])

    def test_mes_futuro(self):
        with self.assertRaises(ValueError):
            mes.corte(dt("2026-10-16T08:00"), date(2026, 10, 16), (2026, 11))

    def test_recorte_dia_31_contra_mes_de_30(self):
        s = serie("2026-09-01", "2026-09-30", 2)
        self.assertEqual(mes.al_dia(s, 2026, 9, 31), (60, True))
        self.assertEqual(mes.al_dia(s, 2026, 9, 15), (30, False))

    def test_febrero(self):
        self.assertEqual(mes.al_dia(serie("2027-02-01", "2027-02-28"), 2027, 2, 30), (28, True))

    def test_cobertura(self):
        primer = date(2026, 6, 14)
        self.assertFalse(mes.cobertura(primer, 2026, 6, 16))   # junio empieza antes
        self.assertTrue(mes.cobertura(primer, 2026, 7, 16))
        self.assertFalse(mes.cobertura(primer, 2026, 7, 0))

    def test_diferencia_base_chica_sin_porcentaje(self):
        d = mes.diferencia(12, 6, 6)
        self.assertEqual((d["valor"], d["pct"], d["base_chica"]), (6, None, True))
        d = mes.diferencia(12, 10, 10)
        self.assertEqual(d["pct"], 20.0)
        self.assertFalse(d["base_chica"])

    def test_mes_anterior(self):
        self.assertEqual(mes.mes_anterior(2026, 1), (2025, 12))
        self.assertEqual(mes.mes_anterior(2026, 2, 3), (2025, 11))


# ── 3.2 Proyección y meta ─────────────────────────────────────────────────

class Proyeccion(unittest.TestCase):
    def test_ritmo_parejo(self):
        p = mes.proyectar(serie("2026-10-01", "2026-10-10", 3), date(2026, 10, 1),
                          date(2026, 10, 10), 31)
        self.assertEqual((p["ritmo_mes"], p["ritmo_7"]), (3, 3))
        self.assertEqual(p["cierre_ritmo_mes"], 93)
        self.assertFalse(p["cambio_ritmo"])
        self.assertTrue(p["confiable"])
        self.assertEqual(p["nivel"], "suposición")

    def test_menos_de_7_dias_no_confiable(self):
        p = mes.proyectar(serie("2026-10-01", "2026-10-04", 2), date(2026, 10, 1),
                          date(2026, 10, 4), 31)
        self.assertFalse(p["confiable"])
        self.assertEqual(p["ritmo_7"], 2)              # con 4 días, ritmo de 4

    def test_cambio_de_ritmo(self):
        s = serie("2026-10-01", "2026-10-07", 1)
        s.update(serie("2026-10-08", "2026-10-14", 4))
        p = mes.proyectar(s, date(2026, 10, 1), date(2026, 10, 14), 31)
        self.assertTrue(p["cambio_ritmo"])
        self.assertEqual(p["ritmo_7"], 4)
        self.assertEqual(p["cierre_ritmo_7"], 35 + 4 * 17)

    def test_cero_ventas_sin_dividir_entre_cero(self):
        p = mes.proyectar({}, date(2026, 10, 1), date(2026, 10, 10), 31)
        self.assertEqual((p["llevado"], p["cierre_ritmo_mes"]), (0, 0))
        self.assertFalse(p["cambio_ritmo"])

    def test_sin_dias(self):
        self.assertIsNone(mes.proyectar({}, date(2026, 10, 1), None, 31))

    def test_meta(self):
        m = mes.meta(180, 90, 15, 5)
        self.assertEqual((m["falta"], m["ritmo_necesario"]), (90, 6))
        self.assertFalse(m["alcanza_a_este_ritmo"])
        m = mes.meta(100, 120, 15, 5)
        self.assertTrue(m["alcanzada"])
        self.assertIsNone(m["ritmo_necesario"])
        self.assertFalse(mes.meta(100, 50, 0, 5)["alcanza_a_este_ritmo"])


# ── 3.3 Alertas y retorno ─────────────────────────────────────────────────

class AlertasYRetorno(unittest.TestCase):
    INICIO = date(2026, 10, 1)
    VIEJA = date(2026, 6, 14)                       # ventana de 125 días

    def test_dormida_con_una_unidad(self):
        self.assertEqual(mes.alerta(0, 1, True, date(2026, 7, 1), self.INICIO, self.VIEJA),
                         ["dormida"])

    def test_dormida_manda_sobre_baja(self):
        self.assertEqual(mes.alerta(0, 8, True, date(2026, 7, 1), self.INICIO, self.VIEJA),
                         ["dormida"])

    def test_sube_y_baja(self):
        self.assertEqual(mes.alerta(10, 4, True, date(2026, 7, 1), self.INICIO, self.VIEJA), ["sube"])
        self.assertEqual(mes.alerta(2, 6, True, date(2026, 7, 1), self.INICIO, self.VIEJA), ["baja"])
        self.assertEqual(mes.alerta(2, 1, True, date(2026, 7, 1), self.INICIO, self.VIEJA), [])

    def test_nueva_solo_con_historia(self):
        self.assertEqual(mes.alerta(3, 0, False, date(2026, 10, 5), self.INICIO, self.VIEJA), ["nueva"])
        corta = date(2026, 9, 1)                    # 30 días antes del mes
        self.assertEqual(mes.alerta(3, 0, False, date(2026, 10, 5), self.INICIO, corta), [])

    def test_retorno_parcial_y_extrapolado(self):
        filas = [{"unidades": 4, "ganancia_u": 30.0}, {"unidades": 6, "ganancia_u": None},
                 {"unidades": 0, "ganancia_u": 50.0}]
        r = mes.retorno(filas)
        self.assertEqual((r["parcial"], r["extrapolado"]), (120, 300))
        self.assertEqual((r["unidades_vinculadas"], r["unidades"]), (4, 10))
        self.assertEqual((r["nivel_parcial"], r["nivel_extrapolado"]), ("correlación", "suposición"))

    def test_sin_vinculadas(self):
        r = mes.retorno([{"unidades": 5, "ganancia_u": None}])
        self.assertIsNone(r["parcial"])
        self.assertIn("falta el dato", r["nota"])


# ── 4. Entrada y salida ───────────────────────────────────────────────────

def crudo(formato_viejo=False, generado="2026-10-16T12:00:00+00:00",
          desde="2026-06-13T12:00:00+00:00", octubre=True):
    """Dos publicaciones: MLM1 vende parejo, MLM2 vendió en septiembre y se durmió."""
    v1 = serie("2026-06-14", "2026-09-30", 2)
    if octubre:
        v1.update(serie("2026-10-01", "2026-10-16", 3))
    v2 = serie("2026-09-01", "2026-09-10", 1)
    ventas = {
        "MLM1": {"titulo": "Organizador control remoto", "por_dia": v1,
                 "ingreso_por_dia": {f: n * 200.0 for f, n in v1.items()}, "unidades": sum(v1.values())},
        "MLM2": {"titulo": "Organizador de cubiertos", "por_dia": v2,
                 "ingreso_por_dia": {f: n * 198.0 for f, n in v2.items()}, "unidades": sum(v2.values())},
    }
    d = {"generado": generado, "dias_historial": 125,
         "publicaciones": {"MLM1": {"logistic_type": "fulfillment"},
                           "MLM2": {"logistic_type": "xd_drop_off"}},
         "ventas": ventas}
    if not formato_viejo:
        d["desde"] = desde
        pd = {}
        for v in ventas.values():
            for f, n in v["por_dia"].items():
                x = pd.setdefault(f, {"ordenes": 0, "unidades": 0, "ingreso": 0.0, "canceladas": 0})
                x["ordenes"] += 1
                x["unidades"] += n
                x["ingreso"] += v["ingreso_por_dia"][f]
        pd.setdefault("2026-10-03", {"ordenes": 0, "unidades": 0, "ingreso": 0.0,
                                     "canceladas": 0})["canceladas"] = 2
        d["por_dia"] = pd
    return d


class EntradaYSalida(unittest.TestCase):
    AHORA = datetime.fromisoformat("2026-10-16T14:00:00+00:00")

    def correr(self, datos, *argv, ahora=None):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        ruta = base / "ml_datos.json"
        if datos is not None:
            ruta.write_text(json.dumps(datos), encoding="utf-8")
        mapa = {"MLM1": {"archivo": "pc.3mf", "retorno": 75.0, "costo": 25.0}}
        buf = io.StringIO()
        with redirect_stdout(buf):
            cod = mes.main(list(argv), datos=ruta, salida=base / "meses",
                           ahora=ahora or self.AHORA, mapa=mapa)
        return cod, buf.getvalue(), base / "meses"

    def tearDown(self):
        if hasattr(self, "tmp"):
            self.tmp.cleanup()

    def leer(self, carpeta, mes_):
        return json.loads((carpeta / (mes_ + ".json")).read_text(encoding="utf-8"))

    def test_mes_en_curso(self):
        cod, out, carpeta = self.correr(crudo(), "--meta", "120")
        self.assertEqual(cod, 0)
        r = self.leer(carpeta, "2026-10")
        self.assertEqual(r["dias_transcurridos"], 15)              # el 16 va a medias
        self.assertEqual(r["totales"]["unidades"], 45)
        self.assertEqual(r["totales"]["ordenes"], 15)
        self.assertEqual(r["totales"]["canceladas"], 2)
        self.assertEqual(r["totales"]["ticket"], 600)
        self.assertEqual(r["hoy_parcial"]["unidades"], 3)
        ant = r["mes_anterior"]
        self.assertEqual(ant["al_dia"]["unidades"], 40)            # 30 de MLM1 + 10 de MLM2
        self.assertEqual(ant["completo"]["unidades"], 70)
        self.assertEqual(ant["diferencia"]["unidades"]["pct"], 12.5)
        self.assertEqual(r["promedio_3"]["meses"], ["2026-09", "2026-08", "2026-07"])
        self.assertAlmostEqual(r["promedio_3"]["al_dia"]["unidades"], (40 + 30 + 30) / 3, 2)
        self.assertEqual(r["proyeccion"]["unidades"]["cierre_ritmo_mes"], 93)
        self.assertEqual(r["meta"]["unidades"]["falta"], 75)
        self.assertEqual(r["full"], {"full": 45, "no_full": 0})
        pubs = {p["id"]: p for p in r["publicaciones"]}
        self.assertEqual(pubs["MLM2"]["alertas"], ["dormida"])
        self.assertEqual(pubs["MLM1"]["participacion"], 100.0)
        self.assertEqual(r["retorno"]["parcial"], 45 * 50)
        self.assertFalse(r["datos_viejos"])
        self.assertIn("5. _Recomendación", out)
        self.assertTrue((carpeta / "2026-10.md").exists())

    def test_mes_cerrado_sin_proyeccion(self):
        cod, out, carpeta = self.correr(crudo(), "--mes", "2026-09")
        self.assertEqual(cod, 0)
        r = self.leer(carpeta, "2026-09")
        self.assertTrue(r["cerrado"])
        self.assertIsNone(r["proyeccion"])
        self.assertEqual(r["totales"]["unidades"], 70)
        self.assertEqual(r["mes_anterior"]["al_dia"]["unidades"], 62)  # agosto completo
        self.assertIn("Mes cerrado", out)

    def test_cero_ventas(self):
        cod, out, carpeta = self.correr(crudo(octubre=False))
        self.assertEqual(cod, 0)
        r = self.leer(carpeta, "2026-10")
        self.assertEqual(r["totales"]["unidades"], 0)
        self.assertIsNone(r["totales"]["ticket"])
        self.assertIsNone(r["retorno"]["parcial"])
        self.assertIn("**0 unidades**", out)

    def test_datos_viejos(self):
        cod, out, _ = self.correr(crudo(), ahora=datetime.fromisoformat("2026-10-18T14:00:00+00:00"))
        self.assertEqual(cod, 0)
        self.assertIn("⚠️ Los datos se bajaron", out)

    def test_formato_viejo(self):
        cod, out, carpeta = self.correr(crudo(formato_viejo=True))
        self.assertEqual(cod, 0)
        r = self.leer(carpeta, "2026-10")
        self.assertEqual(r["totales"]["unidades"], 45)
        self.assertNotIn("ordenes", r["totales"])
        self.assertIn("formato_viejo", r["avisos"])
        self.assertIn("solo en unidades", out)

    def test_historial_corto_omite_comparacion(self):
        cod, out, carpeta = self.correr(crudo(desde="2026-09-20T12:00:00+00:00"))
        self.assertEqual(cod, 0)
        r = self.leer(carpeta, "2026-10")
        self.assertIn("omitido", r["mes_anterior"])
        self.assertIn("omitido", r["promedio_3"])
        self.assertIn("Sin comparación", out)

    def test_sin_archivo(self):
        cod, out, _ = self.correr(None)
        self.assertEqual(cod, 1)
        self.assertIn("traer_datos.py", out)

    def test_mes_invalido_y_futuro(self):
        self.assertEqual(self.correr(crudo(), "--mes", "2026-13")[0], 2)
        self.tearDown()
        self.assertEqual(self.correr(crudo(), "--mes", "septiembre")[0], 2)
        self.tearDown()
        cod, out, _ = self.correr(crudo(), "--mes", "2026-12")
        self.assertEqual(cod, 2)
        self.assertIn("todavía no empieza", out)


if __name__ == "__main__":
    unittest.main()
