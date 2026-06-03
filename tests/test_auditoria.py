"""Pruebas de formato para la auditoria visual."""

from __future__ import annotations

import unittest

import pandas as pd

from src.auditoria import formatear_etiqueta_cluster


class TestAuditoria(unittest.TestCase):
    def test_formatear_etiqueta_cluster_evita_duplicado_confuso(self) -> None:
        info = {
            "resumen_por_cluster": pd.DataFrame(
                [
                    {"cluster": 0, "categoria_patron": "Gasto Hormiga Recurrente", "cantidad": 3},
                    {"cluster": 1, "categoria_patron": "Gasto Hormiga Recurrente", "cantidad": 2},
                ]
            )
        }
        df = pd.DataFrame({"cluster": [0, 1]})

        etiqueta_0 = formatear_etiqueta_cluster(0, info, df)
        etiqueta_1 = formatear_etiqueta_cluster(1, info, df)

        self.assertEqual(etiqueta_0, "Cluster 0 - Gasto Hormiga Recurrente")
        self.assertEqual(etiqueta_1, "Cluster 1 - Gasto Hormiga Recurrente")
        self.assertNotEqual(etiqueta_0, etiqueta_1)


if __name__ == "__main__":
    unittest.main()
