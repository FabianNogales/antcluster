"""Pruebas del clasificador avanzado."""

import unittest

import pandas as pd

from src.classifier import clasificar_patrones_avanzados, clasificar_y_resumir


class TestClassifierAdvanced(unittest.TestCase):
    def test_clasificar_y_resumir_sigue_funcionando(self) -> None:
        df = pd.DataFrame(
            {
                "monto": [5.0, 6.0, 50.0, 60.0],
                "cluster": [0, 0, 1, 1],
            }
        )
        out = clasificar_y_resumir(df, 200.0)
        self.assertIn("total_gastado", out)
        self.assertIn("cluster_hormiga", out)

    def test_clasificar_patrones_avanzados_detecta_categorias(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["Almuerzo", "Transporte", "Cafe", "Dulces", "Laptop", "Cena"],
                "monto": [18.0, 3.0, 5.0, 2.0, 120.0, 20.0],
                "hora": ["12:30", "07:30", "10:30", "16:00", "18:45", "20:30"],
                "frecuencia": [5, 12, 10, 1, 1, 4],
                "cluster": [0, 1, 1, 1, 0, 0],
            }
        )

        out = clasificar_patrones_avanzados(df, presupuesto_total=300.0)
        clasificado = out["df_clasificado"]

        self.assertIn("categoria_patron", clasificado.columns)

        categoria_por_nombre = dict(zip(clasificado["nombre"], clasificado["categoria_patron"]))
        self.assertEqual(categoria_por_nombre["Laptop"], "Gasto Extraordinario")
        self.assertEqual(categoria_por_nombre["Dulces"], "Gasto Hormiga Ocasional")
        self.assertEqual(categoria_por_nombre["Transporte"], "Gasto Hormiga Recurrente")
        self.assertEqual(categoria_por_nombre["Cafe"], "Gasto Hormiga Recurrente")
        self.assertIn(categoria_por_nombre["Almuerzo"], {"Gasto Primario", "Gasto Hormiga Recurrente"})

    def test_clasificar_patrones_avanzados_requiere_cluster(self) -> None:
        df = pd.DataFrame({"nombre": ["Cafe"], "monto": [5.0], "frecuencia": [3]})
        with self.assertRaises(ValueError):
            clasificar_patrones_avanzados(df, presupuesto_total=200.0)


if __name__ == "__main__":
    unittest.main()
