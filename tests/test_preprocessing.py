"""Pruebas de robustez para preprocessing."""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.preprocessing import (
    calcularHoraDecimal,
    calcular_frecuencia_mensual_csv,
    preparar_features_avanzadas,
    preparar_datos_para_modelo,
    vectorizarTransacciones,
)


class TestPreprocessing(unittest.TestCase):
    def test_calcular_hora_decimal_hhmm(self) -> None:
        self.assertEqual(calcularHoraDecimal("14:30"), 14.5)

    def test_calcular_hora_decimal_invalida(self) -> None:
        self.assertTrue(pd.isna(calcularHoraDecimal("99:99")))

    def test_preparar_datos_con_hora_decimal_existente(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["Cafe", "Snack"],
                "monto": [5, 8],
                "fecha": ["2026-05-01", "2026-05-02"],
                "hora": ["bad", "also_bad"],
                "horaDecimal": [10.5, 16.0],
                "frecuencia": [1, 1],
            }
        )

        out = preparar_datos_para_modelo(df)
        self.assertEqual(out.loc[0, "horaDecimal"], 10.5)
        self.assertEqual(out.loc[1, "horaDecimal"], 16.0)

    def test_preparar_datos_calcula_frecuencia_si_falta(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["Cafe", "Cafe", "Snack"],
                "monto": [5, 6, 4],
                "fecha": ["2026-05-01", "2026-05-03", "2026-05-04"],
                "hora": ["10:00", "11:00", "17:00"],
            }
        )

        out = preparar_datos_para_modelo(df)
        self.assertIn("frecuencia", out.columns)
        self.assertEqual(float(out.loc[0, "frecuencia"]), 2.0)
        self.assertEqual(float(out.loc[1, "frecuencia"]), 2.0)
        self.assertEqual(float(out.loc[2, "frecuencia"]), 1.0)

    def test_preparar_datos_monto_invalido_no_rompe(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["Cafe", "Snack"],
                "monto": ["abc", 5],
                "fecha": ["2026-05-01", "2026-05-02"],
                "hora": ["10:00", "17:00"],
                "frecuencia": [1, 1],
            }
        )

        out = preparar_datos_para_modelo(df)
        self.assertTrue(pd.isna(out.loc[0, "monto"]))
        self.assertEqual(float(out.loc[1, "monto"]), 5.0)

    def test_vectorizar_devuelve_columnas_esperadas(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["Cafe", "Snack"],
                "monto": [5, 8],
                "fecha": ["2026-05-01", "2026-05-02"],
                "hora": ["10:00", "16:30"],
                "frecuencia": [1, 2],
            }
        )

        mat = vectorizarTransacciones(df)
        self.assertEqual(list(mat.columns), ["monto", "horaDecimal", "frecuencia"])

    def test_calcular_frecuencia_mensual_csv_archivo_inexistente(self) -> None:
        out = calcular_frecuencia_mensual_csv("ruta/que/no/existe.csv")
        self.assertTrue(out.empty)
        self.assertIn("monto", out.columns)

    def test_calcular_frecuencia_mensual_csv_contenido_valido(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "gastos.csv"
            df = pd.DataFrame(
                {
                    "nombre": ["Cafe", "Cafe", "Almuerzo"],
                    "monto": [5, 6, 15],
                    "fecha": ["2026-05-01", "2026-05-02", "2026-05-02"],
                    "hora": ["10:00", "11:00", "13:00"],
                }
            )
            df.to_csv(path, index=False)

            out = calcular_frecuencia_mensual_csv(str(path))

            self.assertEqual(len(out), 3)
            self.assertIn("horaDecimal", out.columns)
            self.assertIn("frecuencia", out.columns)
            self.assertEqual(float(out.loc[0, "frecuencia"]), 2.0)

    def test_preparar_features_avanzadas_calcula_impacto_y_porcentaje(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["Cafe", "Snack"],
                "monto": [5, 8],
                "fecha": ["2026-05-01", "2026-05-02"],
                "hora": ["10:00", "16:30"],
                "frecuencia": [2, 3],
            }
        )

        out = preparar_features_avanzadas(df, presupuesto_total=200.0)
        self.assertIn("impactoMensual", out.columns)
        self.assertIn("porcentajePresupuesto", out.columns)
        # La fuente oficial usa frecuencia mensual por (nombre, mes).
        # En este caso hay 1 registro por nombre dentro del mismo mes.
        self.assertEqual(float(out.loc[0, "impactoMensual"]), 5.0)
        self.assertEqual(float(out.loc[1, "impactoMensual"]), 8.0)
        self.assertAlmostEqual(float(out.loc[0, "porcentajePresupuesto"]), 2.5, places=6)
        self.assertAlmostEqual(float(out.loc[1, "porcentajePresupuesto"]), 4.0, places=6)

    def test_preparar_features_avanzadas_presupuesto_cero_no_rompe(self) -> None:
        df = pd.DataFrame(
            {
                "nombre": ["Cafe"],
                "monto": [5],
                "fecha": ["2026-05-01"],
                "hora": ["10:00"],
                "frecuencia": [2],
            }
        )

        out = preparar_features_avanzadas(df, presupuesto_total=0)
        self.assertEqual(float(out.loc[0, "porcentajePresupuesto"]), 0.0)

    def test_preparar_features_avanzadas_dataframe_vacio(self) -> None:
        df = pd.DataFrame(columns=["nombre", "monto", "fecha", "hora", "frecuencia"])
        out = preparar_features_avanzadas(df)
        self.assertTrue(out.empty)
        self.assertIn("impactoMensual", out.columns)
        self.assertIn("porcentajePresupuesto", out.columns)


if __name__ == "__main__":
    unittest.main()
