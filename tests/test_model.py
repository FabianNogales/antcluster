"""Pruebas del modulo de clustering."""

import unittest

import pandas as pd

from src.classifier import clasificar_y_resumir
from src.model import (
    aplicar_kmeans,
    aplicar_kmeans_avanzado,
    calcular_distancias_a_centroides,
    evaluar_k_optimo,
)


class TestAplicarKMeans(unittest.TestCase):
    """Verifica comportamiento principal de K-Means en la beta."""

    def test_devuelve_columna_cluster_y_2_clusters(self) -> None:
        df = pd.DataFrame(
            {
                "monto": [2.0, 3.0, 20.0, 22.0],
                "hora": ["08:00", "08:30", "20:00", "21:00"],
                "frecuencia": [12, 11, 2, 1],
            }
        )

        resultado, centroides, mensaje = aplicar_kmeans(df)

        self.assertIn("cluster", resultado.columns)
        self.assertIsNone(mensaje)
        self.assertIsNotNone(centroides)
        self.assertEqual(centroides.shape, (2, 3))
        self.assertEqual(int(resultado["cluster"].nunique(dropna=True)), 2)

    def test_acepta_columna_hora_decimal(self) -> None:
        df = pd.DataFrame(
            {
                "monto": [2.0, 3.0, 20.0, 22.0],
                "horaDecimal": [8.0, 8.5, 20.0, 21.0],
                "frecuencia": [12, 11, 2, 1],
            }
        )

        resultado, centroides, mensaje = aplicar_kmeans(df)

        self.assertIn("cluster", resultado.columns)
        self.assertIsNone(mensaje)
        self.assertIsNotNone(centroides)
        self.assertEqual(int(resultado["cluster"].nunique(dropna=True)), 2)

    def test_no_falla_con_pocos_registros(self) -> None:
        df = pd.DataFrame(
            {
                "monto": [5.0],
                "hora": ["10:30"],
                "frecuencia": [4],
            }
        )

        resultado, centroides, mensaje = aplicar_kmeans(df)

        self.assertIn("cluster", resultado.columns)
        self.assertTrue(resultado["cluster"].isna().all())
        self.assertIsNone(centroides)
        self.assertIsNotNone(mensaje)

    def test_monto_invalido_no_rompe_el_modelo(self) -> None:
        df = pd.DataFrame(
            {
                "monto": ["x", 8, 20],
                "hora": ["07:00", "10:30", "18:00"],
                "frecuencia": [3, 2, 1],
            }
        )

        resultado, centroides, mensaje = aplicar_kmeans(df)

        self.assertIn("cluster", resultado.columns)
        self.assertIsNone(mensaje)
        self.assertIsNotNone(centroides)
        self.assertTrue(pd.isna(resultado.loc[0, "cluster"]))

    def test_dataframe_vacio_con_columnas_no_rompe(self) -> None:
        df = pd.DataFrame(columns=["monto", "hora", "frecuencia"])

        resultado, centroides, mensaje = aplicar_kmeans(df)

        self.assertIn("cluster", resultado.columns)
        self.assertIsNone(centroides)
        self.assertIsNotNone(mensaje)


class TestClasificarYResumir(unittest.TestCase):
    """Verifica la clasificacion semantica de clusters."""

    def test_clasifica_correctamente_hormiga_vs_primario(self) -> None:
        df = pd.DataFrame(
            {
                "monto": [5.0, 6.0, 7.0, 50.0, 55.0, 60.0],
                "cluster": [0, 0, 0, 1, 1, 1],
            }
        )

        resultado = clasificar_y_resumir(df, 200.0)

        self.assertEqual(resultado["total_gastado"], 183.0)
        self.assertEqual(resultado["gastos_hormiga"], 18.0)
        self.assertEqual(resultado["gastos_primarios"], 165.0)
        self.assertEqual(resultado["cantidad_hormiga"], 3)

    def test_calcula_porcentaje_correcto(self) -> None:
        df = pd.DataFrame(
            {
                "monto": [10.0, 15.0, 100.0, 120.0],
                "cluster": [0, 0, 1, 1],
            }
        )

        resultado = clasificar_y_resumir(df, 500.0)
        self.assertEqual(resultado["porcentaje_hormiga"], 5.0)

    def test_maneja_presupuesto_cero(self) -> None:
        df = pd.DataFrame(
            {
                "monto": [5.0, 50.0],
                "cluster": [0, 1],
            }
        )

        resultado = clasificar_y_resumir(df, 0.0)
        self.assertEqual(resultado["porcentaje_hormiga"], 0.0)

    def test_lanza_error_con_dataframe_vacio(self) -> None:
        with self.assertRaises(ValueError):
            clasificar_y_resumir(pd.DataFrame(), 200.0)

    def test_lanza_error_sin_columna_cluster(self) -> None:
        df = pd.DataFrame({"monto": [5.0, 50.0]})
        with self.assertRaises(ValueError):
            clasificar_y_resumir(df, 200.0)

    def test_lanza_error_sin_columna_monto(self) -> None:
        df = pd.DataFrame({"cluster": [0, 1]})
        with self.assertRaises(ValueError):
            clasificar_y_resumir(df, 200.0)


class TestModeloAvanzado(unittest.TestCase):
    def test_evaluar_k_optimo_devuelve_scores(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["A", "B", "C", "D", "E", "F"],
                "monto": [3, 4, 5, 18, 20, 22],
                "horaDecimal": [8.0, 8.5, 9.0, 20.0, 20.5, 21.0],
                "frecuencia": [10, 11, 9, 3, 2, 2],
                "impactoMensual": [30, 44, 45, 54, 40, 44],
                "porcentajePresupuesto": [10, 14.7, 15.0, 18.0, 13.3, 14.7],
            }
        )

        mejor_k, scores, mensaje = evaluar_k_optimo(df, k_min=2, k_max=4, random_state=42)
        self.assertIsNone(mensaje)
        self.assertIsInstance(mejor_k, int)
        self.assertFalse(scores.empty)
        self.assertIn("k", scores.columns)
        self.assertIn("silhouette_score", scores.columns)

    def test_evaluar_k_optimo_pocos_datos(self) -> None:
        df = pd.DataFrame(
            {
                "monto": [5.0, 6.0],
                "horaDecimal": [10.5, 11.0],
                "frecuencia": [2, 2],
                "impactoMensual": [10.0, 12.0],
                "porcentajePresupuesto": [5.0, 6.0],
            }
        )

        mejor_k, scores, mensaje = evaluar_k_optimo(df, k_min=2, k_max=5)
        self.assertIsNone(mejor_k)
        self.assertTrue(scores.empty)
        self.assertIsNotNone(mensaje)

    def test_aplicar_kmeans_avanzado_devuelve_mejor_k(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["Almuerzo", "Cena", "Transporte", "Cafe", "Snack", "Dulces", "Taxi"],
                "monto": [18, 20, 3, 5, 5, 4, 35],
                "hora": ["12:30", "20:30", "07:30", "10:30", "17:00", "16:00", "22:00"],
                "frecuencia": [5, 4, 12, 10, 3, 1, 1],
            }
        )

        out = aplicar_kmeans_avanzado(df, presupuesto_total=300.0, k_min=2, k_max=4, random_state=42)
        self.assertIn("df", out)
        self.assertIn("centroides", out)
        self.assertIn("mejor_k", out)
        self.assertIn("scores", out)
        self.assertIn("columnas_features", out)
        self.assertIn("mensaje", out)
        self.assertIn("cluster", out["df"].columns)
        if out["mensaje"] is None:
            self.assertIsInstance(out["mejor_k"], int)
            self.assertIsNotNone(out["centroides"])

    def test_calcular_distancias_a_centroides(self) -> None:
        vector = [5.0, 10.0, 3.0]
        centroides = [[4.0, 10.0, 2.0], [20.0, 20.0, 5.0]]

        dist = calcular_distancias_a_centroides(vector, centroides)
        self.assertEqual(list(dist.columns), ["cluster", "distancia"])
        self.assertEqual(int(dist.loc[0, "cluster"]), 0)


if __name__ == "__main__":
    unittest.main()
