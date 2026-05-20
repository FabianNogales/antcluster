"""Interfaz principal para la gestion de datos de AntCluster."""

import pandas as pd
import streamlit as st

from src.classifier import clasificar_y_resumir
from src.model import aplicar_kmeans
from src.preprocessing import calcular_frecuencia_mensual_csv, vectorizarTransacciones
from src.utils import (
    USER_CSV,
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

st.title("AntCluster - Gestion de datos")

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

# ==================== ANALISIS DE CLUSTERING ====================
st.divider()
st.subheader("Analisis de Gastos con K-Means")

presupuesto_total = st.sidebar.number_input(
    "Presupuesto total (Bs)",
    min_value=0.0,
    value=200.0,
    step=10.0,
    format="%.2f",
)

if not expenses.empty:
    try:
        df_procesado = calcular_frecuencia_mensual_csv(str(USER_CSV))

        if not df_procesado.empty:
            matriz_vectores = vectorizarTransacciones(df_procesado)
            df_modelo = df_procesado.copy()
            for columna in matriz_vectores.columns:
                df_modelo[columna] = matriz_vectores[columna]

            df_con_clusters, centroides, mensaje_error = aplicar_kmeans(
                df_modelo,
                n_clusters=2,
                random_state=42,
            )

            if mensaje_error is None and centroides is not None:
                st.write("**Resumen Financiero:**")
                resultado_clasificacion = clasificar_y_resumir(df_con_clusters, presupuesto_total)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total gastado", f"Bs. {resultado_clasificacion['total_gastado']:.2f}")
                col2.metric("Gastos Hormiga", f"Bs. {resultado_clasificacion['gastos_hormiga']:.2f}")
                col3.metric("Gastos Primarios", f"Bs. {resultado_clasificacion['gastos_primarios']:.2f}")
                col4.metric(
                    "Porcentaje Hormiga",
                    f"{resultado_clasificacion['porcentaje_hormiga']:.1f}%",
                )

                df_visualizacion = df_con_clusters.copy()

                cluster_hormiga = resultado_clasificacion["cluster_hormiga"]

                def mapear_tipo_gasto(cluster_val):
                    if pd.isna(cluster_val):
                        return "Sin clasificar"
                    if int(cluster_val) == cluster_hormiga:
                        return "Gasto Hormiga"
                    return "Gasto Primario"

                df_visualizacion["Tipo"] = df_visualizacion["cluster"].apply(mapear_tipo_gasto)

                columnas_mostrar = ["nombre", "monto", "fecha", "hora", "frecuencia", "Tipo"]
                df_para_mostrar = df_visualizacion[columnas_mostrar]

                def colorear_columna_tipo(columna):
                    estilos = []
                    for valor in columna:
                        if valor == "Gasto Hormiga":
                            estilos.append("color: #F1C40F; font-weight: bold;")
                        elif valor == "Gasto Primario":
                            estilos.append("color: #2ECC71; font-weight: bold;")
                        else:
                            estilos.append("")
                    return estilos

                st.write("**Tabla Clasificada:**")
                st.dataframe(
                    df_para_mostrar.style.apply(colorear_columna_tipo, subset=["Tipo"], axis=0),
                    use_container_width=True,
                    hide_index=True,
                )

            else:
                st.warning("Se necesitan al menos 2 registros v\u00e1lidos para aplicar K-Means.")
        else:
            st.info("No hay datos validos para procesar en el analisis.")
    except (ValueError, KeyError, TypeError):
        st.error("No se pudieron procesar algunos datos. Verifica el formato del CSV e intenta nuevamente.")
    except Exception:
        st.error("Ocurrio un problema inesperado al ejecutar el analisis.")
else:
    st.info("No hay gastos registrados todavia.")

st.divider()

# ==================== CONTROLES DE DATOS ====================

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
