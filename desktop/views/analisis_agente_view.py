"""Vista PySide6 para analisis del agente."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from desktop.controllers.analisis_controller import AnalisisController
from desktop.widgets import MetricCard, PandasTableModel


class AnalisisAgenteView(QWidget):
    """Pantalla desktop para inspeccionar el analisis K-Means del agente."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = AnalisisController()
        self._metric_cards: dict[str, MetricCard] = {}
        self._matrix_model = PandasTableModel()
        self._classified_model = PandasTableModel()
        self._centroids_model = PandasTableModel()
        self._scores_model = PandasTableModel()

        self._setup_ui()
        self._run_analysis()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        title = QLabel("Analisis del agente")
        title.setObjectName("ViewTitle")

        subtitle = QLabel("Inspecciona la vectorizacion, clusters, categorias y scores del modelo actual.")
        subtitle.setObjectName("ViewSubtitle")
        subtitle.setWordWrap(True)

        accent_line = QLabel()
        accent_line.setObjectName("AccentLine")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        content_layout.addLayout(self._build_controls())
        content_layout.addLayout(self._build_summary())
        content_layout.addWidget(self._build_table_panel("Vectorizacion / Matriz X", self._matrix_model, 240))
        content_layout.addWidget(self._build_table_panel("Tabla clasificada", self._classified_model, 260))
        content_layout.addLayout(self._build_model_tables())
        content_layout.addWidget(self._build_status_label())

        scroll.setWidget(content)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(accent_line)
        root_layout.addWidget(scroll, stretch=1)

    def _build_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        run_button = QPushButton("Ejecutar analisis / Actualizar analisis")
        run_button.clicked.connect(self._run_analysis)

        layout.addWidget(run_button)
        layout.addStretch(1)
        return layout

    def _build_summary(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        for index, (key, title) in enumerate(
            [
                ("total_gastado", "Total gastado"),
                ("gastos_primarios", "Gastos primarios"),
                ("gastos_hormiga", "Gastos hormiga"),
                ("gastos_extraordinarios", "Gastos extraordinarios"),
                ("porcentaje_hormiga", "Porcentaje hormiga"),
                ("mejor_k", "Mejor K"),
                ("clusters_activos", "Clusters activos"),
                ("presupuesto_total", "Presupuesto analizado"),
            ]
        ):
            card = MetricCard(title)
            self._metric_cards[key] = card
            layout.addWidget(card, index // 4, index % 4)

        return layout

    def _build_model_tables(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(
            self._build_table_panel("Centroides", self._centroids_model, 220),
            stretch=2,
        )
        layout.addWidget(
            self._build_table_panel("Scores de Silhouette", self._scores_model, 220),
            stretch=1,
        )
        return layout

    def _build_table_panel(self, title_text: str, model: PandasTableModel, minimum_height: int) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel(title_text)
        title.setObjectName("SectionTitle")

        table = QTableView()
        table.setModel(model)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setMinimumHeight(minimum_height)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(title)
        layout.addWidget(table)
        return panel

    def _build_status_label(self) -> QLabel:
        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        return self.status_label

    def _run_analysis(self) -> None:
        try:
            snapshot = self._controller.run_analysis()
        except Exception as error:
            self._set_status(f"No se pudo ejecutar el analisis: {error}")
            return

        self._render_snapshot(snapshot)
        self._set_status(str(snapshot["message"]))

    def _render_snapshot(self, snapshot: dict) -> None:
        resumen = snapshot["resumen"]
        self._metric_cards["total_gastado"].set_value(self._money(float(resumen["total_gastado"])))
        self._metric_cards["gastos_primarios"].set_value(self._money(float(resumen["gastos_primarios"])))
        self._metric_cards["gastos_hormiga"].set_value(self._money(float(resumen["gastos_hormiga"])))
        self._metric_cards["gastos_extraordinarios"].set_value(
            self._money(float(resumen["gastos_extraordinarios"]))
        )
        self._metric_cards["porcentaje_hormiga"].set_value(f"{float(resumen['porcentaje_hormiga']):.1f}%")
        self._metric_cards["mejor_k"].set_value("-" if snapshot["mejor_k"] is None else str(snapshot["mejor_k"]))
        self._metric_cards["clusters_activos"].set_value(str(snapshot["clusters_activos"]))
        self._metric_cards["presupuesto_total"].set_value(self._money(float(snapshot["presupuesto_total"])))

        self._matrix_model.set_dataframe(snapshot["matrix_df"])
        self._classified_model.set_dataframe(snapshot["classified_df"])
        self._centroids_model.set_dataframe(snapshot["centroids_df"])
        self._scores_model.set_dataframe(snapshot["scores_df"])

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    @staticmethod
    def _money(value: float) -> str:
        return f"Bs. {value:.2f}"
