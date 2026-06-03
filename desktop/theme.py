"""Tema visual Qt para la aplicacion desktop de AntCluster."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication


BG_MAIN = "#00140f"
BG_PANEL = "#001f18"
BG_PANEL_SOFT = "#06261f"
BG_SIDEBAR = "#000f0c"
TEXT_MAIN = "#eefcf6"
TEXT_MUTED = "#9db3ad"
ACCENT = "#45f58a"
ACCENT_SOFT = "#1dbf67"
BORDER = "rgba(69, 245, 138, 0.18)"


def apply_theme(app: QApplication) -> None:
    """Aplica un estilo oscuro sobrio a la aplicacion Qt."""
    app.setStyleSheet(
        f"""
        QMainWindow {{
            background: {BG_MAIN};
            color: {TEXT_MAIN};
        }}

        QWidget {{
            background: {BG_MAIN};
            color: {TEXT_MAIN};
            font-family: Segoe UI, Arial, sans-serif;
            font-size: 14px;
        }}

        QFrame#Sidebar {{
            background: {BG_SIDEBAR};
            border-right: 1px solid {BORDER};
        }}

        QLabel#SidebarTitle {{
            color: {TEXT_MAIN};
            font-size: 24px;
            font-weight: 700;
        }}

        QLabel#SidebarSubtitle,
        QLabel#SidebarStatus,
        QLabel#PlaceholderText {{
            color: {TEXT_MUTED};
        }}

        QLabel#SidebarSubtitle {{
            font-size: 12px;
            text-transform: uppercase;
        }}

        QLabel#SidebarStatus {{
            padding-top: 16px;
            font-size: 12px;
        }}

        QPushButton#NavButton {{
            color: {TEXT_MUTED};
            background: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 12px 14px;
            text-align: left;
            font-weight: 600;
        }}

        QPushButton#NavButton:hover {{
            color: {TEXT_MAIN};
            background: rgba(69, 245, 138, 0.10);
            border-color: {BORDER};
        }}

        QPushButton#NavButton:checked {{
            color: {TEXT_MAIN};
            background: rgba(69, 245, 138, 0.16);
            border-color: rgba(69, 245, 138, 0.35);
        }}

        QFrame#Content {{
            background: {BG_MAIN};
        }}

        QFrame#ViewPanel {{
            background: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}

        QLabel#ViewTitle {{
            color: {TEXT_MAIN};
            font-size: 30px;
            font-weight: 700;
        }}

        QLabel#ViewSubtitle {{
            color: {TEXT_MUTED};
            font-size: 15px;
        }}

        QLabel#AccentLine {{
            background: {ACCENT_SOFT};
            min-height: 2px;
            max-height: 2px;
        }}

        QFrame#MetricCard,
        QFrame#FormPanel,
        QFrame#RecommendationPanel {{
            background: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 8px;
        }}

        QLabel#MetricTitle,
        QLabel#SectionCaption,
        QLabel#StatusLabel {{
            color: {TEXT_MUTED};
        }}

        QLabel#MetricTitle {{
            font-size: 12px;
            font-weight: 600;
        }}

        QLabel#MetricValue {{
            color: {TEXT_MAIN};
            font-size: 20px;
            font-weight: 700;
        }}

        QLabel#SectionTitle {{
            color: {TEXT_MAIN};
            font-size: 17px;
            font-weight: 700;
        }}

        QLineEdit,
        QDoubleSpinBox,
        QSpinBox,
        QDateEdit,
        QComboBox {{
            color: {TEXT_MAIN};
            background: #000f0c;
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 7px 9px;
            min-height: 22px;
        }}

        QLineEdit:focus,
        QDoubleSpinBox:focus,
        QSpinBox:focus,
        QDateEdit:focus,
        QComboBox:focus {{
            border-color: rgba(69, 245, 138, 0.60);
        }}

        QPushButton {{
            color: {TEXT_MAIN};
            background: rgba(69, 245, 138, 0.12);
            border: 1px solid rgba(69, 245, 138, 0.28);
            border-radius: 7px;
            padding: 9px 12px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background: rgba(69, 245, 138, 0.18);
            border-color: rgba(69, 245, 138, 0.42);
        }}

        QPushButton:pressed {{
            background: rgba(29, 191, 103, 0.30);
        }}

        QTableView {{
            color: {TEXT_MAIN};
            background: {BG_PANEL};
            alternate-background-color: {BG_PANEL_SOFT};
            border: 1px solid {BORDER};
            border-radius: 8px;
            gridline-color: rgba(157, 179, 173, 0.16);
            selection-background-color: rgba(69, 245, 138, 0.24);
            selection-color: {TEXT_MAIN};
        }}

        QHeaderView::section {{
            color: {TEXT_MAIN};
            background: {BG_PANEL_SOFT};
            border: 0;
            border-right: 1px solid rgba(157, 179, 173, 0.16);
            border-bottom: 1px solid {BORDER};
            padding: 8px;
            font-weight: 700;
        }}

        QScrollBar:vertical,
        QScrollBar:horizontal {{
            background: {BG_MAIN};
            border: 0;
            width: 12px;
            height: 12px;
        }}

        QScrollBar::handle:vertical,
        QScrollBar::handle:horizontal {{
            background: rgba(157, 179, 173, 0.32);
            border-radius: 6px;
        }}

        QStatusBar {{
            background: {BG_PANEL_SOFT};
            color: {TEXT_MUTED};
        }}
        """
    )
