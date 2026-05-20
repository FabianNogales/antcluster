"""Pruebas basicas del modulo de clustering."""

import unittest

import pandas as pd

from src.model import aplicar_kmeans


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


if __name__ == "__main__":
    unittest.main()
