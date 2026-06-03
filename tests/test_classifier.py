"""Pruebas del clasificador avanzado."""

import unittest

import pandas as pd

from src.classifier import (
    calcular_recomendacion_mensual,
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

    def test_resumen_financiero_avanzado_cambia_con_presupuesto(self) -> None:
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

        resumen_500 = resumir_finanzas_avanzadas(clasificado, presupuesto_total=500.0)
        resumen_1000 = resumir_finanzas_avanzadas(clasificado, presupuesto_total=1000.0)

        self.assertAlmostEqual(resumen_500["gastos_hormiga"], 93.0, places=1)
        self.assertAlmostEqual(resumen_500["porcentaje_hormiga"], 18.6, places=1)
        self.assertAlmostEqual(resumen_1000["gastos_hormiga"], 93.0, places=1)
        self.assertAlmostEqual(resumen_1000["porcentaje_hormiga"], 9.3, places=1)

    def test_resumen_financiero_avanzado_cambia_con_ingreso_extra(self) -> None:
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
        clasificado = clasificar_patrones_avanzados(df, presupuesto_total=600.0)["df_clasificado"]
        resumen = resumir_finanzas_avanzadas(clasificado, presupuesto_total=600.0)

        self.assertAlmostEqual(resumen["gastos_hormiga"], 93.0, places=1)
        self.assertAlmostEqual(resumen["porcentaje_hormiga"], 15.5, places=1)

    def test_calcular_recomendacion_mensual_devuelve_ahorro(self) -> None:
        recomendacion = calcular_recomendacion_mensual(
            presupuesto_total=500.0,
            resumen_base={
                "gastos_primarios": 170.0,
                "gastos_hormiga": 93.0,
                "gastos_extraordinarios": 65.0,
            },
        )
        self.assertAlmostEqual(recomendacion["ahorro_estimado"], 172.0, places=1)
        self.assertTrue(recomendacion["presupuesto_cubre_patron"])

    def test_calcular_recomendacion_mensual_advierte_si_presupuesto_no_cubre(self) -> None:
        recomendacion = calcular_recomendacion_mensual(
            presupuesto_total=200.0,
            resumen_base={
                "gastos_primarios": 170.0,
                "gastos_hormiga": 93.0,
                "gastos_extraordinarios": 65.0,
            },
        )
        self.assertLess(recomendacion["ahorro_estimado"], 0.0)
        self.assertFalse(recomendacion["presupuesto_cubre_patron"])
        self.assertIn("no cubre", recomendacion["mensaje"])

    def test_calcular_recomendacion_mensual_usa_ultimo_mes_historico(self) -> None:
        rows = []
        for month in range(1, 12):
            rows.extend(
                [
                    {
                        "nombre": f"Primario {month}",
                        "monto": 1000.0,
                        "fecha": f"2025-{month:02d}-01",
                        "categoria_patron": "Gasto Primario",
                    },
                    {
                        "nombre": f"Hormiga {month}",
                        "monto": 500.0,
                        "fecha": f"2025-{month:02d}-02",
                        "categoria_patron": "Gasto Hormiga Recurrente",
                    },
                    {
                        "nombre": f"Extra {month}",
                        "monto": 250.0,
                        "fecha": f"2025-{month:02d}-03",
                        "categoria_patron": "Gasto Extraordinario",
                    },
                ]
            )
        rows.extend(
            [
                {"nombre": "Alquiler", "monto": 100.0, "fecha": "2026-05-01", "categoria_patron": "Gasto Primario"},
                {
                    "nombre": "Transporte",
                    "monto": 20.0,
                    "fecha": "2026-05-02",
                    "categoria_patron": "Gasto Hormiga Recurrente",
                },
                {
                    "nombre": "Cafe",
                    "monto": 5.0,
                    "fecha": "2026-05-03",
                    "categoria_patron": "Gasto Hormiga Ocasional",
                },
                {
                    "nombre": "Reparacion",
                    "monto": 40.0,
                    "fecha": "2026-05-04",
                    "categoria_patron": "Gasto Extraordinario",
                },
            ]
        )

        recomendacion = calcular_recomendacion_mensual(
            presupuesto_total=500.0,
            df_clasificado=pd.DataFrame(rows),
            modo="ultimo_mes",
        )

        self.assertEqual(recomendacion["periodo_usado"], "2026-05")
        self.assertEqual(recomendacion["periodo_texto"], "mayo 2026")
        self.assertAlmostEqual(recomendacion["apartar_primarios"], 100.0, places=1)
        self.assertAlmostEqual(recomendacion["controlar_hormiga"], 25.0, places=1)
        self.assertAlmostEqual(recomendacion["reservar_extraordinarios"], 40.0, places=1)
        self.assertAlmostEqual(recomendacion["total_recomendado_mes"], 165.0, places=1)
        self.assertAlmostEqual(recomendacion["ahorro_estimado"], 335.0, places=1)
        self.assertAlmostEqual(recomendacion["compromiso_presupuesto"], 33.0, places=1)

    def test_calcular_recomendacion_mensual_cambia_con_presupuesto_total(self) -> None:
        df = pd.DataFrame(
            [
                {"monto": 100.0, "fecha": "2026-05-01", "categoria_patron": "Gasto Primario"},
                {"monto": 25.0, "fecha": "2026-05-02", "categoria_patron": "Gasto Hormiga Recurrente"},
                {"monto": 40.0, "fecha": "2026-05-03", "categoria_patron": "Gasto Extraordinario"},
            ]
        )

        recomendacion_500 = calcular_recomendacion_mensual(presupuesto_total=500.0, df_clasificado=df)
        recomendacion_300 = calcular_recomendacion_mensual(presupuesto_total=300.0, df_clasificado=df)

        self.assertAlmostEqual(recomendacion_500["total_recomendado_mes"], 165.0, places=1)
        self.assertAlmostEqual(recomendacion_500["ahorro_estimado"], 335.0, places=1)
        self.assertAlmostEqual(recomendacion_300["total_recomendado_mes"], 165.0, places=1)
        self.assertAlmostEqual(recomendacion_300["ahorro_estimado"], 135.0, places=1)
        self.assertAlmostEqual(recomendacion_300["compromiso_presupuesto"], 55.0, places=1)

    def test_calcular_recomendacion_mensual_sin_fecha_usa_fallback(self) -> None:
        df = pd.DataFrame(
            [
                {"monto": 100.0, "categoria_patron": "Gasto Primario"},
                {"monto": 25.0, "categoria_patron": "Gasto Hormiga Ocasional"},
            ]
        )

        recomendacion = calcular_recomendacion_mensual(presupuesto_total=500.0, df_clasificado=df)

        self.assertEqual(recomendacion["modo_recomendacion"], "fallback")
        self.assertIn("No se pudo detectar", recomendacion["advertencia_periodo"])
        self.assertAlmostEqual(recomendacion["total_recomendado_mes"], 125.0, places=1)

    def test_clasificar_patrones_avanzados_requiere_cluster(self) -> None:
        df = pd.DataFrame({"nombre": ["Cafe"], "monto": [5.0], "frecuencia": [3]})
        with self.assertRaises(ValueError):
            clasificar_patrones_avanzados(df, presupuesto_total=200.0)


if __name__ == "__main__":
    unittest.main()
