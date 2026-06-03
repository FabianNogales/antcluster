"""Estilos visuales compartidos para AntCluster."""

from __future__ import annotations

import streamlit as st


BG_MAIN = "#00140f"
BG_PANEL = "#001f18"
BG_PANEL_SOFT = "#06261f"
BG_SIDEBAR = "#000f0c"
TEXT_MAIN = "#eefcf6"
TEXT_MUTED = "#9db3ad"
ACCENT = "#45f58a"
ACCENT_SOFT = "#1dbf67"
DANGER = "#ff5c78"
WARNING = "#ffb84d"
BORDER = "rgba(69, 245, 138, 0.16)"
GRID = "rgba(157, 179, 173, 0.18)"


def apply_app_theme() -> None:
    """Aplica una capa visual global sin cambiar la estructura de Streamlit."""
    st.markdown(
        f"""
        <style>
        :root {{
            --ant-bg-main: {BG_MAIN};
            --ant-bg-panel: {BG_PANEL};
            --ant-bg-panel-soft: {BG_PANEL_SOFT};
            --ant-sidebar: {BG_SIDEBAR};
            --ant-text: {TEXT_MAIN};
            --ant-muted: {TEXT_MUTED};
            --ant-accent: {ACCENT};
            --ant-accent-soft: {ACCENT_SOFT};
            --ant-danger: {DANGER};
            --ant-warning: {WARNING};
            --ant-border: {BORDER};
        }}

        .stApp {{
            color: var(--ant-text);
            background:
                radial-gradient(circle at 70% 6%, rgba(69, 245, 138, 0.12), transparent 30rem),
                linear-gradient(180deg, #001a13 0%, var(--ant-bg-main) 55%, #000b09 100%);
        }}

        [data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, rgba(0, 31, 24, 0.98), rgba(0, 15, 12, 0.98));
            border-right: 1px solid var(--ant-border);
        }}

        [data-testid="stSidebar"] * {{
            color: var(--ant-text);
        }}

        [data-testid="stSidebarNav"] a {{
            border-radius: 12px;
            color: var(--ant-muted);
            transition: background 140ms ease, color 140ms ease, box-shadow 140ms ease;
        }}

        [data-testid="stSidebarNav"] a:hover,
        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            color: var(--ant-text);
            background: rgba(69, 245, 138, 0.14);
            box-shadow: inset 0 0 0 1px var(--ant-border);
        }}

        h1, h2, h3 {{
            color: var(--ant-text);
            letter-spacing: 0;
        }}

        h1 {{
            text-shadow: 0 0 20px rgba(69, 245, 138, 0.20);
        }}

        p, label, [data-testid="stCaptionContainer"] {{
            color: var(--ant-muted);
        }}

        [data-testid="stMetric"],
        [data-testid="stForm"],
        [data-testid="stExpander"],
        div[data-testid="stDataFrame"],
        div[data-testid="stJson"],
        div[data-testid="stPlotlyChart"] {{
            background: linear-gradient(145deg, rgba(0, 38, 30, 0.90), rgba(0, 22, 17, 0.94));
            border: 1px solid var(--ant-border);
            border-radius: 14px;
            box-shadow: 0 0 28px rgba(69, 245, 138, 0.06);
        }}

        [data-testid="stMetric"] {{
            padding: 1rem 1.1rem;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--ant-accent);
            text-shadow: 0 0 18px rgba(69, 245, 138, 0.28);
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--ant-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
        }}

        [data-testid="stForm"] {{
            padding: 1rem;
        }}

        input,
        textarea,
        [data-baseweb="select"] > div,
        [data-baseweb="input"] > div {{
            color: var(--ant-text);
            background-color: rgba(0, 20, 15, 0.96);
            border-color: var(--ant-border);
            border-radius: 12px;
        }}

        input:focus,
        textarea:focus {{
            border-color: var(--ant-accent);
            box-shadow: 0 0 0 1px rgba(69, 245, 138, 0.55);
        }}

        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] button {{
            color: var(--ant-text);
            background: linear-gradient(180deg, var(--ant-accent), var(--ant-accent-soft));
            border: 1px solid rgba(69, 245, 138, 0.75);
            border-radius: 12px;
            font-weight: 700;
            box-shadow: 0 0 22px rgba(69, 245, 138, 0.18);
        }}

        .stButton > button *,
        .stDownloadButton > button *,
        [data-testid="stFormSubmitButton"] button * {{
            color: var(--ant-text) !important;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stFormSubmitButton"] button:hover {{
            color: var(--ant-text);
            border-color: var(--ant-accent);
            box-shadow: 0 0 30px rgba(69, 245, 138, 0.34);
        }}

        [data-testid="stAlert"] {{
            border-radius: 12px;
            border: 1px solid var(--ant-border);
            background: rgba(0, 38, 30, 0.92);
        }}

        div[data-testid="stDataFrame"] {{
            overflow: hidden;
        }}

        [data-testid="stTabs"] button {{
            color: var(--ant-muted);
            border-radius: 12px;
        }}

        [data-testid="stTabs"] button[aria-selected="true"] {{
            color: #00140f;
            background: var(--ant-accent);
        }}

        .stSlider [role="slider"] {{
            background-color: var(--ant-accent);
            box-shadow: 0 0 18px rgba(69, 245, 138, 0.35);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def style_plotly_figure(fig):
    """Alinea los graficos Plotly con la paleta visual de la app."""
    fig.update_layout(
        paper_bgcolor=BG_PANEL,
        plot_bgcolor=BG_PANEL,
        font=dict(color=TEXT_MAIN),
        title_font=dict(color=TEXT_MAIN),
        legend=dict(
            bgcolor="rgba(0, 20, 15, 0.70)",
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(color=TEXT_MAIN),
        ),
        margin=dict(l=24, r=24, t=56, b=32),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT_MUTED))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT_MUTED))
    if "polar" in fig.layout:
        fig.update_layout(
            polar=dict(
                bgcolor=BG_PANEL,
                radialaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT_MUTED)),
                angularaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT_MUTED)),
            )
        )
    return fig
