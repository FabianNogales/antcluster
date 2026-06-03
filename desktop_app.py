"""Punto de entrada para la aplicacion desktop de AntCluster."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from desktop.main_window import MainWindow
from desktop.theme import apply_theme


def main() -> int:
    """Inicia la aplicacion PySide6."""
    app = QApplication(sys.argv)
    app.setApplicationName("AntCluster")
    apply_theme(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
