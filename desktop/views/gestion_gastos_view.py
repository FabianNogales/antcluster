"""Vista PySide6 para gestion de gastos."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
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
    QTableView,
    QVBoxLayout,
    QWidget,
)

from desktop.controllers.gastos_controller import GastosController
from desktop.widgets import MetricCard, PandasTableModel


class GestionGastosView(QWidget):
    """Pantalla desktop para registrar gastos, ingresos y revisar el analisis."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = GastosController()
        self._table_model = PandasTableModel()
        self._metric_cards: dict[str, MetricCard] = {}
        self._recommendation_labels: dict[str, QLabel] = {}

        self._setup_ui()
        self._refresh()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        title = QLabel("Gestion de gastos")
        title.setObjectName("ViewTitle")

        subtitle = QLabel("Registra gastos, administra ingresos extra y revisa el resumen mensual del agente.")
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

        content_layout.addLayout(self._build_budget_metrics())
        content_layout.addLayout(self._build_forms())
        content_layout.addLayout(self._build_financial_summary())
        content_layout.addWidget(self._build_recommendation_panel())
        content_layout.addWidget(self._build_table_section())
        content_layout.addLayout(self._build_data_controls())
        content_layout.addWidget(self._build_status_label())

        scroll.setWidget(content)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addWidget(accent_line)
        root_layout.addWidget(scroll, stretch=1)

    def _build_budget_metrics(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        budget_panel = QFrame()
        budget_panel.setObjectName("FormPanel")
        budget_layout = QVBoxLayout(budget_panel)
        budget_layout.setContentsMargins(14, 12, 14, 12)
        budget_layout.setSpacing(8)

        label = QLabel("Presupuesto base del mes (Bs)")
        label.setObjectName("SectionCaption")

        self.budget_input = QDoubleSpinBox()
        self.budget_input.setDecimals(2)
        self.budget_input.setRange(0.0, 1_000_000_000.0)
        self.budget_input.setSingleStep(10.0)
        self.budget_input.setValue(self._controller.presupuesto_base)
        self.budget_input.valueChanged.connect(self._on_budget_changed)

        budget_layout.addWidget(label)
        budget_layout.addWidget(self.budget_input)

        layout.addWidget(budget_panel, stretch=2)

        for key, title in [
            ("ingresos_extra", "Ingresos extra"),
            ("presupuesto_total", "Presupuesto total activo"),
            ("saldo_disponible", "Saldo disponible"),
        ]:
            card = MetricCard(title)
            self._metric_cards[key] = card
            layout.addWidget(card, stretch=1)

        return layout

    def _build_forms(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self._build_expense_form(), stretch=1)
        layout.addWidget(self._build_extra_income_form(), stretch=1)
        return layout

    def _build_expense_form(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("FormPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        title = QLabel("Registrar gasto")
        title.setObjectName("SectionTitle")

        self.expense_name_input = QLineEdit()
        self.expense_name_input.setPlaceholderText("Nombre del gasto")

        self.expense_amount_input = QDoubleSpinBox()
        self.expense_amount_input.setDecimals(2)
        self.expense_amount_input.setRange(0.0, 1_000_000_000.0)
        self.expense_amount_input.setSingleStep(0.5)

        save_button = QPushButton("Guardar gasto")
        save_button.clicked.connect(self._on_save_expense)

        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(QLabel("Nombre"), 1, 0)
        layout.addWidget(self.expense_name_input, 1, 1)
        layout.addWidget(QLabel("Monto (Bs)"), 2, 0)
        layout.addWidget(self.expense_amount_input, 2, 1)
        layout.addWidget(save_button, 3, 0, 1, 2)
        return panel

    def _build_extra_income_form(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("FormPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        title = QLabel("Agregar ingreso extra")
        title.setObjectName("SectionTitle")

        caption = QLabel("No se registra como gasto; solo aumenta el presupuesto total.")
        caption.setObjectName("SectionCaption")
        caption.setWordWrap(True)

        self.extra_description_input = QLineEdit()
        self.extra_description_input.setPlaceholderText("Descripcion")

        self.extra_amount_input = QDoubleSpinBox()
        self.extra_amount_input.setDecimals(2)
        self.extra_amount_input.setRange(0.0, 1_000_000_000.0)
        self.extra_amount_input.setSingleStep(0.5)

        save_button = QPushButton("Guardar ingreso extra")
        save_button.clicked.connect(self._on_save_extra_income)

        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(caption, 1, 0, 1, 2)
        layout.addWidget(QLabel("Descripcion"), 2, 0)
        layout.addWidget(self.extra_description_input, 2, 1)
        layout.addWidget(QLabel("Monto (Bs)"), 3, 0)
        layout.addWidget(self.extra_amount_input, 3, 1)
        layout.addWidget(save_button, 4, 0, 1, 2)
        return panel

    def _build_financial_summary(self) -> QGridLayout:
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
            ]
        ):
            card = MetricCard(title)
            self._metric_cards[key] = card
            layout.addWidget(card, index // 5, index % 5)

        return layout

    def _build_recommendation_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("RecommendationPanel")
        layout = QGridLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(8)

        title = QLabel("Recomendacion mensual del agente")
        title.setObjectName("SectionTitle")
        layout.addWidget(title, 0, 0, 1, 4)

        self.recommendation_period_label = QLabel("Sin recomendacion disponible.")
        self.recommendation_period_label.setObjectName("SectionCaption")
        self.recommendation_period_label.setWordWrap(True)
        layout.addWidget(self.recommendation_period_label, 1, 0, 1, 4)

        fields = [
            ("apartar_primarios", "Apartar para primarios"),
            ("controlar_hormiga", "Controlar hormiga"),
            ("reservar_extraordinarios", "Reservar extraordinarios"),
            ("ahorro_estimado", "Posible ahorro"),
            ("compromiso_presupuesto", "Compromiso del presupuesto"),
            ("mensaje", "Estado"),
        ]

        for row, (key, label_text) in enumerate(fields, start=2):
            label = QLabel(label_text)
            label.setObjectName("SectionCaption")
            value = QLabel("-")
            value.setWordWrap(True)
            self._recommendation_labels[key] = value
            layout.addWidget(label, row, 0)
            layout.addWidget(value, row, 1, 1, 3)

        return panel

    def _build_table_section(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        title = QLabel("Gastos registrados")
        title.setObjectName("SectionTitle")

        self.table = QTableView()
        self.table.setModel(self._table_model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(260)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(title)
        layout.addWidget(self.table)
        return panel

    def _build_data_controls(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)

        reload_button = QPushButton("Actualizar / Recargar")
        reload_button.clicked.connect(self._refresh)

        demo_button = QPushButton("Cargar dataset demo")
        demo_button.clicked.connect(self._on_load_demo)

        reset_button = QPushButton("Reiniciar datos")
        reset_button.clicked.connect(self._on_reset_data)

        open_data_button = QPushButton("Abrir carpeta data")
        open_data_button.clicked.connect(self._on_open_data_folder)

        layout.addWidget(reload_button)
        layout.addWidget(demo_button)
        layout.addWidget(reset_button)
        layout.addWidget(open_data_button)
        layout.addStretch(1)
        return layout

    def _build_status_label(self) -> QLabel:
        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        return self.status_label

    def _on_budget_changed(self, value: float) -> None:
        self._controller.set_presupuesto_base(value)
        self._refresh()

    def _on_save_expense(self) -> None:
        try:
            self._controller.add_expense(self.expense_name_input.text(), self.expense_amount_input.value())
        except ValueError as error:
            self._show_error(str(error))
            return

        self.expense_name_input.clear()
        self.expense_amount_input.setValue(0.0)
        self._refresh("El gasto fue guardado correctamente.")

    def _on_save_extra_income(self) -> None:
        try:
            self._controller.add_extra_income(self.extra_description_input.text(), self.extra_amount_input.value())
        except ValueError as error:
            self._show_error(str(error))
            return

        self.extra_description_input.clear()
        self.extra_amount_input.setValue(0.0)
        self._refresh("El ingreso extra fue guardado y el presupuesto total se actualizo.")

    def _on_load_demo(self) -> None:
        self._controller.load_demo()
        self._refresh("Se cargo el dataset demo y se limpiaron ingresos extra previos.")

    def _on_reset_data(self) -> None:
        answer = QMessageBox.question(
            self,
            "Reiniciar datos",
            "Esto limpiara gastos e ingresos extra registrados. Deseas continuar?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._controller.reset_data()
        self._refresh("Se reiniciaron gastos e ingresos extra.")

    def _on_open_data_folder(self) -> None:
        path = self._controller.get_data_folder()
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _refresh(self, message: str | None = None) -> None:
        try:
            snapshot = self._controller.build_snapshot()
        except Exception as error:
            self._show_error(f"No se pudo actualizar la vista: {error}")
            return

        self._render_snapshot(snapshot)
        if message:
            self._set_status(message)
        else:
            self._set_status(str(snapshot.get("mensaje_analisis") or "Vista actualizada."))

    def _render_snapshot(self, snapshot: dict) -> None:
        self.budget_input.blockSignals(True)
        self.budget_input.setValue(float(snapshot["presupuesto_base"]))
        self.budget_input.blockSignals(False)

        resumen_ingresos = snapshot["resumen_ingresos"]
        resumen_financiero = snapshot["resumen_financiero"]

        self._metric_cards["ingresos_extra"].set_value(
            self._money(float(resumen_ingresos["total_ingresos_extra"]))
        )
        self._metric_cards["presupuesto_total"].set_value(self._money(float(snapshot["presupuesto_total"])))
        self._metric_cards["saldo_disponible"].set_value(self._money(float(snapshot["saldo_disponible"])))
        self._metric_cards["total_gastado"].set_value(self._money(float(resumen_financiero["total_gastado"])))
        self._metric_cards["gastos_primarios"].set_value(self._money(float(resumen_financiero["gastos_primarios"])))
        self._metric_cards["gastos_hormiga"].set_value(self._money(float(resumen_financiero["gastos_hormiga"])))
        self._metric_cards["gastos_extraordinarios"].set_value(
            self._money(float(resumen_financiero["gastos_extraordinarios"]))
        )
        self._metric_cards["porcentaje_hormiga"].set_value(
            f"{float(resumen_financiero['porcentaje_hormiga']):.1f}%"
        )

        self._render_recommendation(snapshot.get("recomendacion"))
        self._table_model.set_dataframe(snapshot["gastos_table"])
        self.table.resizeColumnsToContents()

    def _render_recommendation(self, recomendacion: dict | None) -> None:
        if not recomendacion:
            self.recommendation_period_label.setText("Sin recomendacion disponible.")
            for label in self._recommendation_labels.values():
                label.setText("-")
            return

        if recomendacion.get("advertencia_periodo"):
            self.recommendation_period_label.setText(str(recomendacion["advertencia_periodo"]))
        elif recomendacion.get("periodo_texto"):
            self.recommendation_period_label.setText(
                f"Recomendacion basada en el ultimo mes historico: {recomendacion['periodo_texto']}."
            )
        else:
            self.recommendation_period_label.setText("Basado en el ultimo mes historico disponible.")

        self._recommendation_labels["apartar_primarios"].setText(
            self._money(float(recomendacion["apartar_primarios"]))
        )
        self._recommendation_labels["controlar_hormiga"].setText(
            self._money(float(recomendacion["controlar_hormiga"]))
        )
        self._recommendation_labels["reservar_extraordinarios"].setText(
            self._money(float(recomendacion["reservar_extraordinarios"]))
        )
        self._recommendation_labels["ahorro_estimado"].setText(
            self._money(float(recomendacion["ahorro_estimado"]))
        )
        self._recommendation_labels["compromiso_presupuesto"].setText(
            f"{float(recomendacion['compromiso_presupuesto']):.1f}%"
        )
        self._recommendation_labels["mensaje"].setText(str(recomendacion["mensaje"]))

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "AntCluster", message)
        self._set_status(message)

    @staticmethod
    def _money(value: float) -> str:
        return f"Bs. {value:.2f}"
