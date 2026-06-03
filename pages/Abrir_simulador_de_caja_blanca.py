"""Pantalla de analisis detallado para la caja blanca del agente."""

from __future__ import annotations

import streamlit as st

from src.auditoria import renderizar_simulador_completo
from src.historico import inicializar_archivos_historicos
from src.sidebar import render_sidebar_presupuesto
from src.theme import apply_app_theme
from src.utils import initialize_data_files


st.set_page_config(page_title="Abrir simulador de caja blanca", layout="wide")
apply_app_theme()
initialize_data_files()
inicializar_archivos_historicos()
render_sidebar_presupuesto()

st.title("Simulador analitico avanzado")

if st.button("Volver a gestion principal", use_container_width=True):
    st.switch_page("app.py")

if "datos_simulador" in st.session_state:
    datos_modelo = st.session_state["datos_simulador"]
    renderizar_simulador_completo(datos_modelo)
else:
    st.info("No hay datos en memoria. Ejecuta primero el analisis del agente desde la pantalla principal.")
