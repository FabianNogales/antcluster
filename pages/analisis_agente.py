"""Pagina independiente para el analisis del agente."""

from __future__ import annotations

import streamlit as st

from src.analisis import ejecutar_analisis_agente
from src.historico import inicializar_archivos_historicos
from src.sidebar import render_sidebar_presupuesto
from src.theme import apply_app_theme
from src.utils import initialize_data_files, read_expenses


st.set_page_config(page_title="Analisis del agente", layout="wide")
apply_app_theme()
initialize_data_files()
inicializar_archivos_historicos()

_, presupuesto_total, _, _ = render_sidebar_presupuesto()
expenses = read_expenses()
analisis_actual = ejecutar_analisis_agente(expenses, presupuesto_total)
if analisis_actual and analisis_actual.get("datos_simulador"):
    st.session_state["datos_simulador"] = analisis_actual["datos_simulador"]

st.title("Analisis del agente")
st.subheader("Analisis del agente / Caja blanca")
st.caption("Esta pagina resume el estado del modelo actual. La vista detallada vive en el simulador.")

if analisis_actual and analisis_actual.get("mensaje") is None:
    resultados_modelo = analisis_actual["resultados_modelo"]
    resumen_avanzado = analisis_actual["resumen"]

    col_a1, col_a2, col_a3 = st.columns(3)
    col_a1.metric("Mejor K", str(resultados_modelo.get("mejor_k")))
    col_a2.metric("Clusters activos", str(analisis_actual["df_usuario"]["cluster"].nunique()))
    col_a3.metric("Presupuesto analizado", f"Bs. {presupuesto_total:.2f}")
    st.caption(f"Porcentaje hormiga actual: {resumen_avanzado['porcentaje_hormiga']:.1f}%")

    scores = resultados_modelo.get("scores")
    if scores is not None and not scores.empty:
        st.write("Scores de Silhouette")
        st.dataframe(scores, use_container_width=True, hide_index=True)

    st.write("Dataset enviado al simulador")
    st.dataframe(
        analisis_actual["df_usuario"][
            [
                "nombre",
                "monto",
                "hora",
                "frecuencia",
                "impactoMensual",
                "porcentajePresupuesto",
                "cluster",
                "categoria_patron",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    if st.button("Abrir analisis detallado", use_container_width=True):
        st.switch_page("pages/Abrir_simulador_de_caja_blanca.py")
elif analisis_actual and analisis_actual.get("mensaje"):
    st.info(analisis_actual["mensaje"])
else:
    st.info("No hay gastos suficientes para mostrar la caja blanca del agente.")
