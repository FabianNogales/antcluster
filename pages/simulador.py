"""Pestaña paralela para el análisis de caja blanca."""

import streamlit as st
from src.auditoria import renderizar_simulador_completo

st.set_page_config(page_title="Simulador Analítico Avanzado", layout="wide")
st.title("Simulador Analítico Avanzado")

if "datos_simulador" in st.session_state:
    datos_modelo = st.session_state["datos_simulador"]
    renderizar_simulador_completo(datos_modelo)
else:
    st.info("No hay datos en memoria. Ejecuta el modelo avanzado en la pestaña principal primero.")