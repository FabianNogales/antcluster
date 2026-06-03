"""Vista PySide6 para caja blanca del agente."""

from __future__ import annotations

import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QComboBox,
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

from desktop.controllers.caja_blanca_controller import CajaBlancaController
from desktop.widgets import MetricCard, PandasTableModel


class CajaBlancaView(QWidget):
    """Pantalla desktop para explicar visualmente las decisiones del agente."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = CajaBlancaController()
        self._snapshot: dict | None = None
        self._metric_cards: dict[str, MetricCard] = {}
        self._scores_model = PandasTableModel()
        self._vector_model = PandasTableModel()
        self._distances_model = PandasTableModel()
        self._repeated_model = PandasTableModel()

        self._figure = Figure(figsize=(7, 4), tight_layout=True)
        self._canvas = FigureCanvas(self._figure)

        self._setup_ui()
        self._refresh_simulator()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        title = QLabel("Caja blanca")
        title.setObjectName("ViewTitle")

        subtitle = QLabel("Explicacion visual de clusters, centroides y trazabilidad de gasto.")
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
        content_layout.addWidget(self._build_explanation_panel())
        content_layout.addLayout(self._build_k_section())
        content_layout.addWidget(self._build_plot_panel())
        content_layout.addWidget(self._build_trace_panel())
        content_layout.addWidget(self._build_repeated_panel())
        content_layout.addWidget(self._build_status_label())

        scroll.setWidget(content)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(accent_line)
        root_layout.addWidget(scroll, stretch=1)

    def _build_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        refresh_button = QPushButton("Actualizar simulador")
        refresh_button.clicked.connect(self._refresh_simulator)

        layout.addWidget(refresh_button)
        layout.addStretch(1)
        return layout

    def _build_explanation_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RecommendationPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Como decide el agente")
        title.setObjectName("SectionTitle")

        text = QLabel(
            "K-Means genera clusters numericos a partir de monto, hora, frecuencia, impacto mensual "
            "y porcentaje del presupuesto. Luego el clasificador interpreta esos clusters como categorias "
            "financieras. Puede haber mas de un cluster con la misma categoria si representan subpatrones "
            "distintos."
        )
        text.setObjectName("SectionCaption")
        text.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(text)
        return panel

    def _build_k_section(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        metrics_panel = QWidget()
        metrics_layout = QGridLayout(metrics_panel)
        metrics_layout.setContentsMargins(0, 0, 0, 0)
        metrics_layout.setHorizontalSpacing(12)
        metrics_layout.setVerticalSpacing(12)

        for index, (key, title) in enumerate(
            [
                ("mejor_k", "Mejor K"),
                ("presupuesto_total", "Presupuesto analizado"),
            ]
        ):
            card = MetricCard(title)
            self._metric_cards[key] = card
            metrics_layout.addWidget(card, index, 0)

        self.k_message_label = QLabel("")
        self.k_message_label.setObjectName("SectionCaption")
        self.k_message_label.setWordWrap(True)
        metrics_layout.addWidget(self.k_message_label, 2, 0)

        scores_panel = self._build_table_panel("Scores de Silhouette", self._scores_model, minimum_height=170)
        layout.addWidget(metrics_panel, stretch=1)
        layout.addWidget(scores_panel, stretch=2)
        return layout

    def _build_plot_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RecommendationPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Agrupamiento de gastos segun frecuencia e impacto mensual")
        title.setObjectName("SectionTitle")
        self.plot_message_label = QLabel("")
        self.plot_message_label.setObjectName("SectionCaption")
        self.plot_message_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self._canvas)
        layout.addWidget(self.plot_message_label)
        return panel

    def _build_trace_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RecommendationPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(10)

        title = QLabel("Trazabilidad de gasto")
        title.setObjectName("SectionTitle")

        self.expense_selector = QComboBox()
        self.expense_selector.currentIndexChanged.connect(self._on_expense_selected)

        self.trace_cluster_label = QLabel("-")
        self.trace_category_label = QLabel("-")
        self.trace_explanation_label = QLabel("Selecciona un gasto para ver su trazabilidad.")
        self.trace_explanation_label.setObjectName("SectionCaption")
        self.trace_explanation_label.setWordWrap(True)

        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(QLabel("Gasto"), 1, 0)
        layout.addWidget(self.expense_selector, 1, 1)
        layout.addWidget(QLabel("Cluster asignado"), 2, 0)
        layout.addWidget(self.trace_cluster_label, 2, 1)
        layout.addWidget(QLabel("Categoria"), 3, 0)
        layout.addWidget(self.trace_category_label, 3, 1)
        layout.addWidget(self.trace_explanation_label, 4, 0, 1, 2)
        layout.addWidget(self._build_table_panel("Vector generado", self._vector_model, 150), 5, 0)
        layout.addWidget(self._build_table_panel("Distancias a centroides", self._distances_model, 150), 5, 1)
        return panel

    def _build_repeated_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RecommendationPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(8)

        title = QLabel("Clusters con categoria repetida")
        title.setObjectName("SectionTitle")
        self.repeated_note_label = QLabel("")
        self.repeated_note_label.setObjectName("SectionCaption")
        self.repeated_note_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self.repeated_note_label)
        layout.addWidget(self._build_table_panel("Comparacion de centroides", self._repeated_model, 180))
        return panel

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

    def _refresh_simulator(self) -> None:
        try:
            self._snapshot = self._controller.refresh()
        except Exception as error:
            self._set_status(f"No se pudo actualizar el simulador: {error}")
            self._clear_plot("El grafico no pudo renderizarse.")
            return

        self._render_snapshot(self._snapshot)
        self._set_status(str(self._snapshot["message"]))

    def _render_snapshot(self, snapshot: dict) -> None:
        self._metric_cards["mejor_k"].set_value("-" if snapshot["mejor_k"] is None else str(snapshot["mejor_k"]))
        self._metric_cards["presupuesto_total"].set_value(self._money(float(snapshot["presupuesto_total"])))
        self.k_message_label.setText(str(snapshot["k_message"]))
        self._scores_model.set_dataframe(snapshot["scores_df"])
        self.repeated_note_label.setText(str(snapshot["repeated_note"]))
        self._repeated_model.set_dataframe(snapshot["repeated_clusters_df"])
        self._populate_expense_selector(snapshot["expense_options"])
        self._render_plot(snapshot)

    def _populate_expense_selector(self, options: list[str]) -> None:
        self.expense_selector.blockSignals(True)
        self.expense_selector.clear()
        self.expense_selector.addItems(options)
        self.expense_selector.blockSignals(False)
        if options:
            self.expense_selector.setCurrentIndex(0)
            self._render_trace(0)
        else:
            self._clear_trace()

    def _render_plot(self, snapshot: dict) -> None:
        try:
            df = snapshot["df_plot"]
            centroides_df = snapshot["centroides_df"]
            if df is None or df.empty:
                self._clear_plot("No hay datos suficientes para graficar.")
                return
            if centroides_df is None or centroides_df.empty:
                self._clear_plot("No hay centroides disponibles para graficar.")
                return

            self._figure.clear()
            ax = self._figure.add_subplot(111)
            for label, group in df.groupby("categoria_patron", dropna=False):
                ax.scatter(
                    pd.to_numeric(group["frecuencia"], errors="coerce"),
                    pd.to_numeric(group["impactoMensual"], errors="coerce"),
                    label=str(label),
                    alpha=0.78,
                    s=46,
                )

            ax.scatter(
                pd.to_numeric(centroides_df["frecuencia"], errors="coerce"),
                pd.to_numeric(centroides_df["impactoMensual"], errors="coerce"),
                marker="X",
                s=150,
                c="black",
                edgecolors="white",
                linewidths=1.0,
                label="Centroides",
            )
            ax.set_title("Agrupamiento de gastos segun frecuencia e impacto mensual")
            ax.set_xlabel("Frecuencia")
            ax.set_ylabel("Impacto mensual")
            ax.grid(True, alpha=0.25)
            ax.legend(loc="best", fontsize=8)
            self._canvas.draw()
            self.plot_message_label.setText("")
        except Exception as error:
            self._clear_plot(f"El grafico no pudo renderizarse: {error}")

    def _clear_plot(self, message: str) -> None:
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center", wrap=True)
        ax.set_axis_off()
        self._canvas.draw()
        self.plot_message_label.setText(message)

    def _on_expense_selected(self, index: int) -> None:
        if index >= 0:
            self._render_trace(index)

    def _render_trace(self, index: int) -> None:
        try:
            trace = self._controller.trace_expense(index)
        except Exception as error:
            self._set_status(str(error))
            self._clear_trace()
            return

        self.trace_cluster_label.setText(str(trace["cluster"]))
        self.trace_category_label.setText(str(trace["categoria"]))
        self.trace_explanation_label.setText(str(trace["explanation"]))
        self._vector_model.set_dataframe(trace["vector_df"])
        self._distances_model.set_dataframe(trace["distancias_df"])

    def _clear_trace(self) -> None:
        self.trace_cluster_label.setText("-")
        self.trace_category_label.setText("-")
        self.trace_explanation_label.setText("No hay gastos disponibles para trazar.")
        self._vector_model.set_dataframe(pd.DataFrame(columns=["dimension", "valor"]))
        self._distances_model.set_dataframe(pd.DataFrame(columns=["cluster", "distancia"]))

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    @staticmethod
    def _money(value: float) -> str:
        return f"Bs. {value:.2f}"
