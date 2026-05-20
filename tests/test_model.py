"""Pruebas basicas del modulo de clustering."""

import unittest

import pandas as pd

from src.model import aplicar_kmeans
from src.classifier import clasificar_y_resumir


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


class TestClasificarYResumirResumidos(unittest.TestCase):
    """Verifica la clasificacion semantica de clusters como Hormiga y Primario."""

    def test_clasifica_correctamente_hormiga_vs_primario(self) -> None:
        """
        Verifica que el cluster con promedio menor sea identificado como 'Hormiga'
        y el cluster con promedio mayor como 'Primario'.
        """
        # Crear datos mock: cluster 0 con montos pequeños, cluster 1 con montos grandes
        df = pd.DataFrame(
            {
                "monto": [5.0, 6.0, 7.0, 50.0, 55.0, 60.0],
                "cluster": [0, 0, 0, 1, 1, 1],
            }
        )

        presupuesto = 200.0
        resultado = clasificar_y_resumir(df, presupuesto)

        # Verificar que los totales son correctos
        self.assertEqual(resultado["total_gastado"], 183.0)
        self.assertEqual(resultado["gastos_hormiga"], 18.0)  # 5 + 6 + 7
        self.assertEqual(resultado["gastos_primarios"], 165.0)  # 50 + 55 + 60
        self.assertEqual(resultado["cantidad_hormiga"], 3)

    def test_calcula_porcentaje_correcto(self) -> None:
        """Verifica que el porcentaje del presupuesto se calcula correctamente."""
        df = pd.DataFrame(
            {
                "monto": [10.0, 15.0, 100.0, 120.0],
                "cluster": [0, 0, 1, 1],
            }
        )

        presupuesto = 500.0
        resultado = clasificar_y_resumir(df, presupuesto)

        # Gastos hormiga: 10 + 15 = 25
        # Porcentaje: 25 / 500 * 100 = 5.0%
        self.assertEqual(resultado["porcentaje_hormiga"], 5.0)

    def test_maneja_presupuesto_cero(self) -> None:
        """Verifica que la función maneja presupuesto cero sin errores."""
        df = pd.DataFrame(
            {
                "monto": [5.0, 50.0],
                "cluster": [0, 1],
            }
        )

        presupuesto = 0.0
        resultado = clasificar_y_resumir(df, presupuesto)

        # Porcentaje debe ser 0 cuando presupuesto es 0
        self.assertEqual(resultado["porcentaje_hormiga"], 0.0)

    def test_lanza_error_con_dataframe_vacio(self) -> None:
        """Verifica que lanza ValueError con DataFrame vacío."""
        df = pd.DataFrame()
        presupuesto = 200.0

        with self.assertRaises(ValueError):
            clasificar_y_resumir(df, presupuesto)

    def test_lanza_error_sin_columna_cluster(self) -> None:
        """Verifica que lanza ValueError si falta la columna 'cluster'."""
        df = pd.DataFrame(
            {
                "monto": [5.0, 50.0],
            }
        )
        presupuesto = 200.0

        with self.assertRaises(ValueError):
            clasificar_y_resumir(df, presupuesto)

    def test_lanza_error_sin_columna_monto(self) -> None:
        """Verifica que lanza ValueError si falta la columna 'monto'."""
        df = pd.DataFrame(
            {
                "cluster": [0, 1],
            }
        )
        presupuesto = 200.0

        with self.assertRaises(ValueError):
            clasificar_y_resumir(df, presupuesto)


if __name__ == "__main__":
    unittest.main()
