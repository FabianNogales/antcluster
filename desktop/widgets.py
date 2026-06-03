"""Widgets reutilizables para la base desktop de AntCluster."""

from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class PlaceholderView(QWidget):
    """Vista inicial para secciones que se migraran desde Streamlit."""

    def __init__(self, title: str, description: str) -> None:
        super().__init__()
        self._setup_ui(title, description)

    def _setup_ui(self, title: str, description: str) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(18)

        title_label = QLabel(title)
        title_label.setObjectName("ViewTitle")

        subtitle_label = QLabel(description)
        subtitle_label.setObjectName("ViewSubtitle")
        subtitle_label.setWordWrap(True)

        accent_line = QLabel()
        accent_line.setObjectName("AccentLine")

        panel = QFrame()
        panel.setObjectName("ViewPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 22, 24, 22)
        panel_layout.setSpacing(12)

        placeholder = QLabel("Pantalla preparada para migrar funcionalidades en una fase posterior.")
        placeholder.setObjectName("PlaceholderText")
        placeholder.setWordWrap(True)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        panel_layout.addWidget(placeholder)
        panel_layout.addStretch(1)

        root_layout.addWidget(title_label)
        root_layout.addWidget(subtitle_label)
        root_layout.addWidget(accent_line)
        root_layout.addSpacing(8)
        root_layout.addWidget(panel, stretch=1)


class PandasTableModel(QAbstractTableModel):
    """Modelo Qt simple para mostrar DataFrames en QTableView."""

    def __init__(self, dataframe: pd.DataFrame | None = None) -> None:
        super().__init__()
        self._df = pd.DataFrame() if dataframe is None else dataframe.copy()

    def set_dataframe(self, dataframe: pd.DataFrame | None) -> None:
        self.beginResetModel()
        self._df = pd.DataFrame() if dataframe is None else dataframe.copy()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return int(len(self._df.index))

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return int(len(self._df.columns))

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole}:
            return None

        value = self._df.iat[index.row(), index.column()]
        if pd.isna(value):
            return ""
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None

        if orientation == Qt.Orientation.Horizontal:
            try:
                return str(self._df.columns[section])
            except IndexError:
                return ""
        return str(section + 1)


class MetricCard(QFrame):
    """Tarjeta compacta para metricas financieras."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("MetricCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")

        self.value_label = QLabel("Bs. 0.00")
        self.value_label.setObjectName("MetricValue")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)
