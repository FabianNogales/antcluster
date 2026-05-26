"""Pruebas del clasificador avanzado."""

import unittest

import pandas as pd

from src.classifier import (
    clasificar_patrones_avanzados,
    clasificar_y_resumir,
    resumir_finanzas_avanzadas,
)


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
                "nombre": [
                    "Almuerzo",
                    "Cena",
                    "Transporte",
                    "Cafe",
                    "Snack",
                    "Dulces",
                    "Refresco",
                    "Agua",
                    "Taxi",
                    "Cine",
                ],
                "monto": [18.0, 20.0, 3.0, 5.0, 5.0, 2.0, 7.0, 1.0, 35.0, 30.0],
                "hora": ["12:30", "20:30", "07:30", "10:30", "17:00", "16:00", "15:30", "09:40", "22:00", "21:30"],
                "frecuencia": [5, 4, 12, 4, 2, 1, 1, 1, 1, 1],
                "cluster": [0, 0, 1, 1, 2, 2, 2, 2, 3, 3],
            }
        )

        out = clasificar_patrones_avanzados(df, presupuesto_total=500.0)
        clasificado = out["df_clasificado"]

        self.assertIn("categoria_patron", clasificado.columns)

        categoria_por_nombre = dict(zip(clasificado["nombre"], clasificado["categoria_patron"]))
        self.assertEqual(categoria_por_nombre["Cena"], "Gasto Primario")
        self.assertEqual(categoria_por_nombre["Taxi"], "Gasto Extraordinario")
        self.assertEqual(categoria_por_nombre["Cine"], "Gasto Extraordinario")
        self.assertEqual(categoria_por_nombre["Transporte"], "Gasto Hormiga Recurrente")
        self.assertEqual(categoria_por_nombre["Cafe"], "Gasto Hormiga Recurrente")
        self.assertEqual(categoria_por_nombre["Snack"], "Gasto Hormiga Ocasional")
        self.assertEqual(categoria_por_nombre["Dulces"], "Gasto Hormiga Ocasional")
        self.assertEqual(categoria_por_nombre["Refresco"], "Gasto Hormiga Ocasional")
        self.assertEqual(categoria_por_nombre["Agua"], "Gasto Hormiga Ocasional")
        self.assertEqual(categoria_por_nombre["Almuerzo"], "Gasto Primario")

    def test_resumen_financiero_avanzado_esperado_dataset_prueba(self) -> None:
        rows = []
        rows.append({"nombre": "Almuerzo", "monto": 90.0, "hora": "12:30", "frecuencia": 5, "cluster": 0})
        rows.append({"nombre": "Cena", "monto": 80.0, "hora": "20:30", "frecuencia": 4, "cluster": 0})

        for _ in range(6):
            rows.append({"nombre": "Transporte", "monto": 3.0, "hora": "07:30", "frecuencia": 12, "cluster": 1})
        for _ in range(5):
            rows.append({"nombre": "Cafe", "monto": 5.0, "hora": "10:30", "frecuencia": 4, "cluster": 1})
        for _ in range(5):
            rows.append({"nombre": "Snack", "monto": 5.0, "hora": "17:00", "frecuencia": 2, "cluster": 2})
        for _ in range(5):
            rows.append({"nombre": "Dulces", "monto": 2.0, "hora": "16:00", "frecuencia": 1, "cluster": 2})
        for _ in range(2):
            rows.append({"nombre": "Refresco", "monto": 7.0, "hora": "15:30", "frecuencia": 1, "cluster": 2})
        rows.append({"nombre": "Agua", "monto": 1.0, "hora": "09:40", "frecuencia": 1, "cluster": 2})

        rows.append({"nombre": "Taxi", "monto": 35.0, "hora": "22:00", "frecuencia": 1, "cluster": 3})
        rows.append({"nombre": "Cine", "monto": 30.0, "hora": "21:30", "frecuencia": 1, "cluster": 3})

        df = pd.DataFrame(rows)

        clasificado = clasificar_patrones_avanzados(df, presupuesto_total=500.0)["df_clasificado"]
        resumen = resumir_finanzas_avanzadas(clasificado, presupuesto_total=500.0)

        self.assertAlmostEqual(resumen["total_gastado"], 328.0, places=1)
        self.assertAlmostEqual(resumen["gastos_primarios"], 170.0, places=1)
        self.assertAlmostEqual(resumen["gastos_hormiga"], 93.0, places=1)
        self.assertAlmostEqual(resumen["gastos_extraordinarios"], 65.0, places=1)
        self.assertAlmostEqual(resumen["porcentaje_hormiga"], 18.6, places=1)

    def test_clasificar_patrones_avanzados_requiere_cluster(self) -> None:
        df = pd.DataFrame({"nombre": ["Cafe"], "monto": [5.0], "frecuencia": [3]})
        with self.assertRaises(ValueError):
            clasificar_patrones_avanzados(df, presupuesto_total=200.0)


if __name__ == "__main__":
    unittest.main()
