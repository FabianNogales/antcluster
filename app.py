"""Interfaz principal para la gestion de datos de AntCluster."""

import streamlit as st

from src.utils import (
    get_expenses_summary,
    get_user_csv_bytes,
    initialize_data_files,
    load_demo_data,
    read_expenses,
    reset_user_data,
    save_expense,
)


st.set_page_config(page_title="AntCluster - Gestion de datos", layout="centered")
initialize_data_files()

st.title("AntCluster - Gestión de datos")

with st.form("formulario_gasto"):
    nombre = st.text_input("Nombre del gasto")
    monto = st.number_input("Monto", min_value=0.0, step=0.5, format="%.2f")
    enviado = st.form_submit_button("Guardar gasto")

if enviado:
    try:
        save_expense(nombre, monto)
        st.success("El gasto fue guardado correctamente.")
    except ValueError as error:
        st.error(str(error))

summary = get_expenses_summary()
col_count, col_total, col_average = st.columns(3)
col_count.metric("Cantidad de gastos", summary["cantidad_gastos"])
col_total.metric("Total gastado", f"Bs. {summary['total_gastado']:.2f}")
col_average.metric("Promedio por gasto", f"Bs. {summary['promedio_gasto']:.2f}")

st.subheader("Gastos registrados")
expenses = read_expenses()
st.dataframe(expenses, width="stretch", hide_index=True)

st.download_button(
    "Descargar CSV",
    data=get_user_csv_bytes(),
    file_name="gastos_usuario.csv",
    mime="text/csv",
)

col_demo, col_reset = st.columns(2)

with col_demo:
    if st.button("Cargar dataset demo", width="stretch"):
        load_demo_data()
        st.rerun()

with col_reset:
    if st.button("Reiniciar datos", width="stretch"):
        reset_user_data()
        st.rerun()
