"""Pruebas para aprendizaje historico persistente."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import src.historico as historico
from src.historico import (
    cargar_gastos_historicos,
    cargar_modelo_historico,
    clasificar_gasto_con_modelo_historico,
    entrenar_agente_historico,
    guardar_modelo_historico,
    inicializar_archivos_historicos,
)


class TestHistorico(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp_dir.name)
        self.historico_csv = self.data_dir / "gastos_historicos.csv"
        self.modelo_json = self.data_dir / "modelo_historico.json"

        self._patchers = [
            patch.object(historico, "DATA_DIR", self.data_dir),
            patch.object(historico, "HISTORICO_CSV", self.historico_csv),
            patch.object(historico, "MODELO_HISTORICO_JSON", self.modelo_json),
        ]
        for patcher in self._patchers:
            patcher.start()

    def tearDown(self) -> None:
        for patcher in reversed(self._patchers):
            patcher.stop()
        self.tmp_dir.cleanup()

    def test_inicializar_archivos_historicos_crea_demo_y_json(self) -> None:
        inicializar_archivos_historicos()
        self.assertTrue(self.historico_csv.exists())
        self.assertTrue(self.modelo_json.exists())

        df = pd.read_csv(self.historico_csv)
        self.assertFalse(df.empty)
        self.assertEqual(list(df.columns), ["id", "nombre", "monto", "fecha", "hora", "frecuencia"])

        modelo = cargar_modelo_historico()
        self.assertFalse(modelo["entrenado"])
        self.assertIn("resumen_entrenamiento", modelo)

    def test_cargar_gastos_historicos_inexistente_crea_archivo(self) -> None:
        self.assertFalse(self.historico_csv.exists())
        df = cargar_gastos_historicos()
        self.assertTrue(self.historico_csv.exists())
        self.assertFalse(df.empty)
        self.assertIn("frecuencia", df.columns)

    def test_cargar_modelo_historico_inexistente_devuelve_base(self) -> None:
        self.assertFalse(self.modelo_json.exists())
        modelo = cargar_modelo_historico()
        self.assertTrue(self.modelo_json.exists())
        self.assertFalse(modelo["entrenado"])
        self.assertEqual(modelo["centroides"], [])

    def test_guardar_y_cargar_modelo_historico(self) -> None:
        modelo = {
            "entrenado": True,
            "fecha_entrenamiento": "2026-05-26T18:00:00",
            "cantidad_registros": 10,
            "presupuesto_total": 500.0,
            "columnas_features": ["monto", "horaDecimal", "frecuencia", "impactoMensual", "porcentajePresupuesto"],
            "mejor_k": 3,
            "scores_silhouette": [{"k": 2, "silhouette_score": 0.4}],
            "centroides": [[1, 2, 3, 4, 5]],
            "categorias_por_cluster": {"0": "Gasto Hormiga Recurrente"},
            "resumen_entrenamiento": {"mensaje": "ok"},
        }
        guardar_modelo_historico(modelo)
        loaded = cargar_modelo_historico()
        self.assertTrue(loaded["entrenado"])
        self.assertEqual(loaded["mejor_k"], 3)
        self.assertEqual(loaded["columnas_features"], modelo["columnas_features"])
        self.assertEqual(loaded["centroides"], modelo["centroides"])

    def test_entrenar_agente_historico_devuelve_mejor_k_y_centroides(self) -> None:
        df_hist = cargar_gastos_historicos()
        modelo = entrenar_agente_historico(df_hist, presupuesto_total=500.0)
        self.assertTrue(modelo["entrenado"])
        self.assertIsInstance(modelo["mejor_k"], int)
        self.assertTrue(len(modelo["columnas_features"]) >= 3)
        self.assertTrue(len(modelo["centroides"]) > 0)
        self.assertTrue(len(modelo["scores_silhouette"]) > 0)

    def test_modelo_historico_json_guarda_columnas_y_centroides(self) -> None:
        df_hist = cargar_gastos_historicos()
        modelo = entrenar_agente_historico(df_hist, presupuesto_total=500.0)
        guardar_modelo_historico(modelo)
        loaded = cargar_modelo_historico()
        self.assertEqual(loaded["columnas_features"], modelo["columnas_features"])
        self.assertEqual(loaded["centroides"], modelo["centroides"])

    def test_clasificar_con_modelo_historico_no_reentrena(self) -> None:
        df_hist = cargar_gastos_historicos()
        modelo = entrenar_agente_historico(df_hist, presupuesto_total=500.0)

        with patch("src.historico.aplicar_kmeans_avanzado", side_effect=AssertionError("no debe reentrenar")):
            out = clasificar_gasto_con_modelo_historico(
                {
                    "nombre": "Cafe",
                    "monto": 5.0,
                    "fecha": "2026-05-26",
                    "hora": "10:30",
                    "frecuencia": 1,
                },
                modelo_historico=modelo,
                presupuesto_total=500.0,
            )
        self.assertIn("cluster_asignado", out)

    def test_clasificar_con_modelo_historico_devuelve_resultado_completo(self) -> None:
        df_hist = cargar_gastos_historicos()
        modelo = entrenar_agente_historico(df_hist, presupuesto_total=500.0)
        out = clasificar_gasto_con_modelo_historico(
            {
                "nombre": "Taxi",
                "monto": 34.0,
                "fecha": "2026-05-26",
                "hora": "22:10",
                "frecuencia": 1,
            },
            modelo_historico=modelo,
            presupuesto_total=500.0,
        )
        self.assertIn("vector_generado", out)
        self.assertIn("cluster_asignado", out)
        self.assertIn("distancias_centroides", out)
        self.assertIn("categoria_interpretada", out)
        self.assertIn("explicacion", out)
        self.assertTrue(len(out["distancias_centroides"]) > 0)

    def test_entrenar_historico_con_pocos_datos(self) -> None:
        df_min = pd.DataFrame(
            [{"id": 1, "nombre": "Cafe", "monto": 5.0, "fecha": "2026-05-01", "hora": "10:00", "frecuencia": 1}]
        )
        modelo = entrenar_agente_historico(df_min, presupuesto_total=500.0)
        self.assertFalse(modelo["entrenado"])
        self.assertEqual(modelo["centroides"], [])
        self.assertIn("resumen_entrenamiento", modelo)

    def test_clasificar_respeta_frecuencia_enviada_formulario(self) -> None:
        modelo = {
            "centroides": [
                [18.0, 12.67, 5.0, 90.0, 18.0],
                [20.0, 20.5, 4.0, 80.0, 16.0],
                [3.0, 7.5, 8.0, 24.0, 4.8],
            ],
            "columnas_features": ["monto", "horaDecimal", "frecuencia", "impactoMensual", "porcentajePresupuesto"],
            "categorias_por_cluster": {
                "0": "Gasto Primario",
                "1": "Gasto Primario",
                "2": "Gasto Hormiga Recurrente",
            },
        }

        almuerzo = clasificar_gasto_con_modelo_historico(
            {"nombre": "Almuerzo", "monto": 18.0, "hora": "12:40", "frecuencia": 5},
            modelo_historico=modelo,
            presupuesto_total=500.0,
        )
        cena = clasificar_gasto_con_modelo_historico(
            {"nombre": "Cena", "monto": 20.0, "hora": "20:30", "frecuencia": 4},
            modelo_historico=modelo,
            presupuesto_total=500.0,
        )
        transporte = clasificar_gasto_con_modelo_historico(
            {"nombre": "Transporte", "monto": 3.0, "hora": "07:30", "frecuencia": 8},
            modelo_historico=modelo,
            presupuesto_total=500.0,
        )

        self.assertAlmostEqual(almuerzo["vector_generado"]["monto"], 18.0, places=2)
        self.assertAlmostEqual(almuerzo["vector_generado"]["horaDecimal"], 12.67, places=2)
        self.assertAlmostEqual(almuerzo["vector_generado"]["frecuencia"], 5.0, places=2)
        self.assertAlmostEqual(almuerzo["vector_generado"]["impactoMensual"], 90.0, places=2)
        self.assertAlmostEqual(almuerzo["vector_generado"]["porcentajePresupuesto"], 18.0, places=2)
        self.assertEqual(almuerzo["categoria_interpretada"], "Gasto Primario")

        self.assertAlmostEqual(cena["vector_generado"]["monto"], 20.0, places=2)
        self.assertAlmostEqual(cena["vector_generado"]["horaDecimal"], 20.5, places=2)
        self.assertAlmostEqual(cena["vector_generado"]["frecuencia"], 4.0, places=2)
        self.assertAlmostEqual(cena["vector_generado"]["impactoMensual"], 80.0, places=2)
        self.assertAlmostEqual(cena["vector_generado"]["porcentajePresupuesto"], 16.0, places=2)
        self.assertEqual(cena["categoria_interpretada"], "Gasto Primario")

        self.assertAlmostEqual(transporte["vector_generado"]["monto"], 3.0, places=2)
        self.assertAlmostEqual(transporte["vector_generado"]["horaDecimal"], 7.5, places=2)
        self.assertAlmostEqual(transporte["vector_generado"]["frecuencia"], 8.0, places=2)
        self.assertAlmostEqual(transporte["vector_generado"]["impactoMensual"], 24.0, places=2)
        self.assertAlmostEqual(transporte["vector_generado"]["porcentajePresupuesto"], 4.8, places=2)
        self.assertEqual(transporte["categoria_interpretada"], "Gasto Hormiga Recurrente")

    def test_clasificar_sin_frecuencia_usa_fallback_uno(self) -> None:
        modelo = {
            "centroides": [[18.0, 12.67, 1.0, 18.0, 3.6]],
            "columnas_features": ["monto", "horaDecimal", "frecuencia", "impactoMensual", "porcentajePresupuesto"],
            "categorias_por_cluster": {"0": "Gasto Hormiga Ocasional"},
        }
        out = clasificar_gasto_con_modelo_historico(
            {"nombre": "Almuerzo", "monto": 18.0, "hora": "12:40"},
            modelo_historico=modelo,
            presupuesto_total=500.0,
        )
        self.assertAlmostEqual(out["vector_generado"]["frecuencia"], 1.0, places=6)
        self.assertAlmostEqual(out["vector_generado"]["impactoMensual"], 18.0, places=6)
        self.assertAlmostEqual(out["vector_generado"]["porcentajePresupuesto"], 3.6, places=6)

    def test_clasificar_historico_respeta_presupuesto_recibido(self) -> None:
        modelo = {
            "presupuesto_total": 500.0,
            "centroides": [[18.0, 12.67, 1.0, 18.0, 3.6]],
            "columnas_features": ["monto", "horaDecimal", "frecuencia", "impactoMensual", "porcentajePresupuesto"],
            "categorias_por_cluster": {"0": "Gasto Hormiga Ocasional"},
        }

        out_500 = clasificar_gasto_con_modelo_historico(
            {"nombre": "Almuerzo", "monto": 18.0, "hora": "12:40", "frecuencia": 1},
            modelo_historico=modelo,
            presupuesto_total=500.0,
        )
        out_1000 = clasificar_gasto_con_modelo_historico(
            {"nombre": "Almuerzo", "monto": 18.0, "hora": "12:40", "frecuencia": 1},
            modelo_historico=modelo,
            presupuesto_total=1000.0,
        )

        self.assertAlmostEqual(out_500["vector_generado"]["porcentajePresupuesto"], 3.6, places=6)
        self.assertAlmostEqual(out_1000["vector_generado"]["porcentajePresupuesto"], 1.8, places=6)
        self.assertAlmostEqual(out_500["presupuesto_clasificacion"], 500.0, places=6)
        self.assertAlmostEqual(out_1000["presupuesto_clasificacion"], 1000.0, places=6)
        self.assertAlmostEqual(out_500["presupuesto_modelo_entrenado"], 500.0, places=6)


if __name__ == "__main__":
    unittest.main()
