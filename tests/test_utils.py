"""Pruebas de persistencia de gastos e ingresos extra."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.utils as utils
from src.utils import (
    calcular_presupuesto_actualizado,
    guardar_ingreso_extra,
    initialize_data_files,
    leer_ingresos_extra,
    read_expenses,
)


class TestIngresosExtra(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp_dir.name)

        self._patchers = [
            patch.object(utils, "DATA_DIR", self.data_dir),
            patch.object(utils, "USER_CSV", self.data_dir / "gastos_usuario.csv"),
            patch.object(utils, "DEMO_CSV", self.data_dir / "gastos_demo.csv"),
            patch.object(utils, "EXTRA_INCOME_CSV", self.data_dir / "ingresos_extra.csv"),
        ]
        for patcher in self._patchers:
            patcher.start()
        initialize_data_files()

    def tearDown(self) -> None:
        for patcher in reversed(self._patchers):
            patcher.stop()
        self.tmp_dir.cleanup()

    def test_guardar_ingreso_extra_aumenta_presupuesto_total(self) -> None:
        guardar_ingreso_extra("Ingreso freelance", 100.0, fecha="2026-06-02", hora="09:00")
        presupuesto = calcular_presupuesto_actualizado(500.0)
        self.assertAlmostEqual(presupuesto, 600.0, places=6)

    def test_ingreso_extra_no_se_guarda_como_gasto(self) -> None:
        guardar_ingreso_extra("Reembolso", 80.0, fecha="2026-06-02", hora="10:00")

        gastos = read_expenses()
        ingresos = leer_ingresos_extra()

        self.assertTrue(gastos.empty)
        self.assertEqual(len(ingresos), 1)
        self.assertEqual(str(ingresos.iloc[0]["descripcion"]), "Reembolso")


if __name__ == "__main__":
    unittest.main()
