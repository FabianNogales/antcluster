"""Vista PySide6 para aprendizaje historico."""

from __future__ import annotations

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from desktop.controllers.historico_controller import HistoricoController
from desktop.widgets import MetricCard, PandasTableModel


class AprendizajeHistoricoView(QWidget):
    """Pantalla desktop para entrenar y consultar el modelo historico."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = HistoricoController()
        self._metric_cards: dict[str, MetricCard] = {}
        self._centroids_model = PandasTableModel()
        self._scores_model = PandasTableModel()
        self._vector_model = PandasTableModel()
        self._distances_model = PandasTableModel()

        self._setup_ui()
        self._refresh()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        title = QLabel("Aprendizaje historico")
        title.setObjectName("ViewTitle")

        subtitle = QLabel("Entrena el agente con datos historicos y clasifica nuevos gastos contra sus centroides.")
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

        content_layout.addLayout(self._build_status_section())
        content_layout.addLayout(self._build_training_controls())
        content_layout.addLayout(self._build_training_summary())
        content_layout.addLayout(self._build_model_tables())
        content_layout.addWidget(self._build_classification_panel())
        content_layout.addWidget(self._build_classification_result())
        content_layout.addWidget(self._build_status_label())

        scroll.setWidget(content)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(accent_line)
        root_layout.addWidget(scroll, stretch=1)

    def _build_status_section(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        for index, (key, title) in enumerate(
            [
                ("estado_modelo", "Estado"),
                ("archivo_modelo", "Archivo modelo"),
                ("registros_historicos", "Registros historicos"),
                ("presupuesto_activo", "Presupuesto activo"),
                ("presupuesto_entrenamiento", "Presupuesto entrenamiento"),
            ]
        ):
            card = MetricCard(title)
            self._metric_cards[key] = card
            layout.addWidget(card, 0, index)

        return layout

    def _build_training_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        train_button = QPushButton("Entrenar agente historico")
        train_button.clicked.connect(self._on_train)

        reload_button = QPushButton("Actualizar / Recargar")
        reload_button.clicked.connect(self._refresh)

        layout.addWidget(train_button)
        layout.addWidget(reload_button)
        layout.addStretch(1)
        return layout

    def _build_training_summary(self) -> QGridLayout:
        layout = QGridLayout()
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        for index, (key, title) in enumerate(
            [
                ("fecha_entrenamiento", "Fecha entrenamiento"),
                ("cantidad_registros", "Registros usados"),
                ("mejor_k", "Mejor K"),
                ("presupuesto_total", "Presupuesto del modelo"),
                ("columnas_features", "Columnas features"),
            ]
        ):
            card = MetricCard(title)
            self._metric_cards[key] = card
            layout.addWidget(card, index // 5, index % 5)

        return layout

    def _build_model_tables(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(
            self._build_table_panel("Centroides historicos", self._centroids_model, minimum_height=220),
            stretch=2,
        )
        layout.addWidget(
            self._build_table_panel("Scores de Silhouette", self._scores_model, minimum_height=220),
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

    def _build_classification_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("FormPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        title = QLabel("Clasificar nuevo gasto con centroides historicos")
        title.setObjectName("SectionTitle")

        self.classification_budget_label = QLabel("")
        self.classification_budget_label.setObjectName("SectionCaption")
        self.classification_budget_label.setWordWrap(True)

        self.name_input = QLineEdit("Gasto nuevo")
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setDecimals(2)
        self.amount_input.setRange(0.0, 1_000_000_000.0)
        self.amount_input.setSingleStep(0.5)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())

        self.hour_input = QLineEdit("12:00")
        self.hour_input.setPlaceholderText("HH:MM")

        self.frequency_input = QSpinBox()
        self.frequency_input.setRange(1, 1_000_000)
        self.frequency_input.setValue(1)

        classify_button = QPushButton("Clasificar con historico")
        classify_button.clicked.connect(self._on_classify)

        layout.addWidget(title, 0, 0, 1, 4)
        layout.addWidget(self.classification_budget_label, 1, 0, 1, 4)
        layout.addWidget(QLabel("Nombre"), 2, 0)
        layout.addWidget(self.name_input, 2, 1)
        layout.addWidget(QLabel("Monto (Bs)"), 2, 2)
        layout.addWidget(self.amount_input, 2, 3)
        layout.addWidget(QLabel("Fecha"), 3, 0)
        layout.addWidget(self.date_input, 3, 1)
        layout.addWidget(QLabel("Hora (HH:MM)"), 3, 2)
        layout.addWidget(self.hour_input, 3, 3)
        layout.addWidget(QLabel("Frecuencia"), 4, 0)
        layout.addWidget(self.frequency_input, 4, 1)
        layout.addWidget(classify_button, 4, 2, 1, 2)
        return panel

    def _build_classification_result(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RecommendationPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)

        title = QLabel("Resultado de clasificacion historica")
        title.setObjectName("SectionTitle")
        layout.addWidget(title, 0, 0, 1, 2)

        self.cluster_result_label = QLabel("-")
        self.category_result_label = QLabel("-")
        self.explanation_label = QLabel("Sin clasificacion ejecutada.")
        self.explanation_label.setObjectName("SectionCaption")
        self.explanation_label.setWordWrap(True)

        layout.addWidget(QLabel("Cluster asignado"), 1, 0)
        layout.addWidget(self.cluster_result_label, 1, 1)
        layout.addWidget(QLabel("Categoria interpretada"), 2, 0)
        layout.addWidget(self.category_result_label, 2, 1)
        layout.addWidget(self.explanation_label, 3, 0, 1, 2)

        vector_panel = self._build_table_panel("Vector generado", self._vector_model, minimum_height=150)
        distances_panel = self._build_table_panel("Distancias a centroides", self._distances_model, minimum_height=150)
        layout.addWidget(vector_panel, 4, 0)
        layout.addWidget(distances_panel, 4, 1)
        return panel

    def _build_status_label(self) -> QLabel:
        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        return self.status_label

    def _on_train(self) -> None:
        try:
            modelo = self._controller.train()
        except Exception as error:
            self._show_error(f"No se pudo entrenar el modelo historico: {error}")
            return

        message = "Entrenamiento historico completado y guardado."
        if not modelo.get("entrenado"):
            resumen = modelo.get("resumen_entrenamiento") or {}
            message = str(resumen.get("mensaje") or "Entrenamiento historico incompleto.")
        self._refresh(message)

    def _on_classify(self) -> None:
        try:
            resultado = self._controller.classify_expense(
                nombre=self.name_input.text(),
                monto=self.amount_input.value(),
                fecha=self.date_input.date().toString("yyyy-MM-dd"),
                hora=self.hour_input.text(),
                frecuencia=self.frequency_input.value(),
            )
        except ValueError as error:
            self._show_error(str(error))
            return
        except Exception as error:
            self._show_error(f"No se pudo clasificar el nuevo gasto con el modelo historico: {error}")
            return

        self._render_classification_result(resultado)
        self._set_status("Clasificacion historica ejecutada.")

    def _refresh(self, message: str | None = None) -> None:
        try:
            snapshot = self._controller.build_snapshot()
        except Exception as error:
            self._show_error(f"No se pudo actualizar la vista historica: {error}")
            return

        self._render_snapshot(snapshot)
        self._set_status(message or "Vista historica actualizada.")

    def _render_snapshot(self, snapshot: dict) -> None:
        self._metric_cards["estado_modelo"].set_value(str(snapshot["estado_modelo"]))
        self._metric_cards["archivo_modelo"].set_value("Disponible" if snapshot["modelo_existe"] else "No disponible")
        self._metric_cards["registros_historicos"].set_value(str(snapshot["registros_historicos"]))
        self._metric_cards["presupuesto_activo"].set_value(self._money(float(snapshot["presupuesto_activo"])))

        presupuesto_entrenamiento = snapshot.get("presupuesto_entrenamiento")
        self._metric_cards["presupuesto_entrenamiento"].set_value(
            "-" if presupuesto_entrenamiento is None else self._money(float(presupuesto_entrenamiento))
        )

        resumen = snapshot["resumen_entrenamiento"]
        self._metric_cards["fecha_entrenamiento"].set_value(str(resumen["fecha_entrenamiento"]))
        self._metric_cards["cantidad_registros"].set_value(str(resumen["cantidad_registros"]))
        self._metric_cards["mejor_k"].set_value("-" if resumen["mejor_k"] is None else str(resumen["mejor_k"]))
        self._metric_cards["presupuesto_total"].set_value(
            "-" if resumen["presupuesto_total"] is None else self._money(float(resumen["presupuesto_total"]))
        )
        self._metric_cards["columnas_features"].set_value(str(resumen["columnas_features"]))

        self._centroids_model.set_dataframe(snapshot["centroides_df"])
        self._scores_model.set_dataframe(snapshot["scores_df"])
        self._update_classification_budget_text(snapshot)

    def _update_classification_budget_text(self, snapshot: dict) -> None:
        current_budget = self._money(float(snapshot["presupuesto_activo"]))
        training_budget = snapshot.get("presupuesto_entrenamiento")
        if training_budget is None:
            self.classification_budget_label.setText(f"Presupuesto usado para clasificar ahora: {current_budget}.")
            return

        self.classification_budget_label.setText(
            "Presupuesto actual de clasificacion: "
            f"{current_budget} | Presupuesto del entrenamiento historico: {self._money(float(training_budget))}."
        )

    def _render_classification_result(self, resultado: dict) -> None:
        self.cluster_result_label.setText(str(resultado["cluster_asignado"]))
        self.category_result_label.setText(str(resultado["categoria_interpretada"]))
        self.explanation_label.setText(str(resultado["explicacion"]))
        self._vector_model.set_dataframe(resultado["vector_df"])
        self._distances_model.set_dataframe(resultado["distancias_df"])

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "AntCluster", message)
        self._set_status(message)

    @staticmethod
    def _money(value: float) -> str:
        return f"Bs. {value:.2f}"
