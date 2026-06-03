"""Interfaz principal para la gestion de datos de AntCluster."""

from __future__ import annotations

import streamlit as st

from src.analisis import ejecutar_analisis_agente, render_recomendacion
from src.classifier import calcular_recomendacion_mensual
from src.historico import cargar_modelo_historico, inicializar_archivos_historicos
from src.sidebar import render_sidebar_presupuesto
from src.utils import (
    get_expenses_summary,
    get_user_csv_bytes,
    guardar_ingreso_extra,
    initialize_data_files,
    load_demo_data,
    read_expenses,
    reset_user_data,
    save_expense,
)


st.set_page_config(page_title="AntCluster - Gestion de datos", layout="wide")
initialize_data_files()
inicializar_archivos_historicos()

flash = st.session_state.pop("flash_message", None)
if flash:
    getattr(st, flash.get("level", "info"))(flash.get("message", ""))


def _set_flash(level: str, message: str) -> None:
    st.session_state["flash_message"] = {"level": level, "message": message}


presupuesto_base, presupuesto_total, ingresos_extra, resumen_ingresos = render_sidebar_presupuesto()
expenses = read_expenses()
summary = get_expenses_summary()
analisis_actual = ejecutar_analisis_agente(expenses, presupuesto_total)
modelo_historico = cargar_modelo_historico()

st.title("AntCluster - Gestion de datos")
st.write("Gestiona gastos, registra ingresos extra y revisa el analisis financiero mensual.")

col_top1, col_top2, col_top3, col_top4 = st.columns(4)
col_top1.metric("Presupuesto base", f"Bs. {presupuesto_base:.2f}")
col_top2.metric("Ingresos extra", f"Bs. {float(resumen_ingresos['total_ingresos_extra']):.2f}")
col_top3.metric("Presupuesto total", f"Bs. {presupuesto_total:.2f}")
col_top4.metric("Saldo disponible", f"Bs. {presupuesto_total - float(summary['total_gastado']):.2f}")

st.subheader("Resumen operativo")
col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
col_sum1.metric("Cantidad de gastos", int(summary["cantidad_gastos"]))
col_sum2.metric("Total gastado", f"Bs. {float(summary['total_gastado']):.2f}")
col_sum3.metric("Promedio por gasto", f"Bs. {float(summary['promedio_gasto']):.2f}")
col_sum4.metric("Cantidad ingresos extra", int(resumen_ingresos["cantidad_ingresos"]))

col_budget, col_income = st.columns(2)

with col_budget:
    st.subheader("Presupuesto y gastos")
    st.caption(
        f"Presupuesto base: Bs. {presupuesto_base:.2f} | "
        f"Ingresos extra: Bs. {float(resumen_ingresos['total_ingresos_extra']):.2f} | "
        f"Presupuesto total: Bs. {presupuesto_total:.2f}"
    )
    with st.form("formulario_gasto"):
        nombre = st.text_input("Nombre del gasto")
        monto = st.number_input("Monto del gasto", min_value=0.0, step=0.5, format="%.2f")
        enviado = st.form_submit_button("Guardar gasto", use_container_width=True)

    if enviado:
        try:
            save_expense(nombre, monto)
            _set_flash("success", "El gasto fue guardado correctamente.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

with col_income:
    st.subheader("Ingreso extra del mes")
    st.caption("No se registra como gasto. Solo aumenta el presupuesto total disponible.")
    with st.form("formulario_ingreso_extra"):
        descripcion_ingreso = st.text_input("Descripcion del ingreso extra")
        monto_ingreso = st.number_input("Monto del ingreso extra", min_value=0.0, step=0.5, format="%.2f")
        ingreso_enviado = st.form_submit_button("Agregar ingreso extra", use_container_width=True)

    if ingreso_enviado:
        try:
            guardar_ingreso_extra(descripcion_ingreso, monto_ingreso)
            _set_flash("success", "El ingreso extra fue guardado y el presupuesto total se actualizo.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

st.subheader("Gastos registrados")
st.dataframe(expenses, use_container_width=True, hide_index=True)

if not ingresos_extra.empty:
    st.subheader("Ingresos extra registrados")
    st.dataframe(ingresos_extra, use_container_width=True, hide_index=True)

if analisis_actual and analisis_actual.get("mensaje") is None:
    resumen_avanzado = analisis_actual["resumen"]

    st.subheader("Resumen financiero")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total gastado", f"Bs. {resumen_avanzado['total_gastado']:.2f}")
    col2.metric("Gastos hormiga", f"Bs. {resumen_avanzado['gastos_hormiga']:.2f}")
    col3.metric("Gastos primarios", f"Bs. {resumen_avanzado['gastos_primarios']:.2f}")
    col4.metric("Extraordinarios", f"Bs. {resumen_avanzado['gastos_extraordinarios']:.2f}")
    col5.metric("Porcentaje hormiga", f"{resumen_avanzado['porcentaje_hormiga']:.1f}%")

    st.subheader("Recomendacion mensual del agente")
    render_recomendacion(analisis_actual["recomendacion"])
elif analisis_actual and analisis_actual.get("mensaje"):
    st.info(analisis_actual["mensaje"])
elif modelo_historico.get("entrenado"):
    st.subheader("Recomendacion mensual del agente")
    recomendacion_historica = calcular_recomendacion_mensual(
        presupuesto_total=presupuesto_total,
        resumen_base=modelo_historico.get("resumen_entrenamiento", {}),
    )
    render_recomendacion(recomendacion_historica)
else:
    st.info("Registra al menos dos gastos validos para activar el analisis y la recomendacion mensual.")

st.subheader("Controles de datos")
st.download_button(
    "Descargar CSV de gastos",
    data=get_user_csv_bytes(),
    file_name="gastos_usuario.csv",
    mime="text/csv",
    use_container_width=True,
)
col_demo, col_reset = st.columns(2)
with col_demo:
    if st.button("Cargar dataset demo", use_container_width=True):
        load_demo_data()
        _set_flash("success", "Se cargo el dataset demo y se limpiaron ingresos extra previos.")
        st.rerun()
with col_reset:
    if st.button("Reiniciar datos", use_container_width=True):
        reset_user_data()
        _set_flash("success", "Se reiniciaron gastos e ingresos extra.")
        st.rerun()
