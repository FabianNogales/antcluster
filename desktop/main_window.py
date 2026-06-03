"""Ventana principal de la aplicacion desktop AntCluster."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from desktop.views.analisis_agente_view import AnalisisAgenteView
from desktop.views.aprendizaje_historico_view import AprendizajeHistoricoView
from desktop.views.caja_blanca_view import CajaBlancaView
from desktop.views.gestion_gastos_view import GestionGastosView


class MainWindow(QMainWindow):
    """Contenedor principal con navegacion lateral y vistas intercambiables."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AntCluster")
        self.resize(1200, 800)
        self.setMinimumSize(960, 640)

        self._stack = QStackedWidget()
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        content = self._build_content()

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, stretch=1)

        self.setCentralWidget(central)
        self._select_view(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 24, 18, 24)
        layout.setSpacing(10)

        title = QLabel("AntCluster")
        title.setObjectName("SidebarTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        subtitle = QLabel("Desktop")
        subtitle.setObjectName("SidebarSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(22)

        nav_items = [
            ("Gestion de gastos", GestionGastosView()),
            ("Aprendizaje historico", AprendizajeHistoricoView()),
            ("Analisis del agente", AnalisisAgenteView()),
            ("Caja blanca", CajaBlancaView()),
        ]

        for index, (label, view) in enumerate(nav_items):
            self._stack.addWidget(view)
            button = QPushButton(label)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setObjectName("NavButton")
            button.clicked.connect(lambda checked=False, view_index=index: self._select_view(view_index))
            self._nav_group.addButton(button, index)
            layout.addWidget(button)

        layout.addStretch(1)

        status = QLabel("Fase desktop base")
        status.setObjectName("SidebarStatus")
        status.setWordWrap(True)
        layout.addWidget(status)

        return sidebar

    def _build_content(self) -> QWidget:
        content = QFrame()
        content.setObjectName("Content")
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 30, 32, 32)
        layout.setSpacing(0)
        layout.addWidget(self._stack)

        return content

    def _select_view(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        button = self._nav_group.button(index)
        if button is not None:
            button.setChecked(True)
