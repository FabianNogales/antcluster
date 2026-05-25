"""Interfaz principal para la gestion de datos de AntCluster."""

import pandas as pd
import streamlit as st

from src.classifier import clasificar_patrones_avanzados, clasificar_y_resumir
from src.model import aplicar_kmeans_avanzado
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

            resultados_modelo = aplicar_kmeans_avanzado(
                df_modelo,
                presupuesto_total=presupuesto_total,
                random_state=42,
            )
            
            df_con_clusters = resultados_modelo.get("df")
            centroides = resultados_modelo.get("centroides")
            mensaje_error = resultados_modelo.get("mensaje")

            if mensaje_error is None and centroides is not None:
                st.write("**Resumen Financiero:**")
                
                # obtiene metricas basicas del resumen
                resultado_basico = clasificar_y_resumir(df_con_clusters, presupuesto_total)
                
                # obtiene metricas avanzadas con las 5 variables y heuristica
                resultado_avanzado = clasificar_patrones_avanzados(df_con_clusters, presupuesto_total)
                df_visualizacion = resultado_avanzado["df_clasificado"]

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Total gastado", f"Bs. {resultado_basico['total_gastado']:.2f}")
                col2.metric("Gastos Hormiga", f"Bs. {resultado_basico['gastos_hormiga']:.2f}")
                col3.metric("Gastos Primarios", f"Bs. {resultado_basico['gastos_primarios']:.2f}")
                col4.metric(
                    "Porcentaje Hormiga",
                    f"{resultado_basico['porcentaje_hormiga']:.1f}%",
                )

                # configura las 5 columnas base mas el patron
                columnas_mostrar = ["nombre", "monto", "fecha", "hora", "frecuencia", "impactoMensual", "porcentajePresupuesto", "categoria_patron"]
                df_para_mostrar = df_visualizacion[columnas_mostrar]

                # colorea basado en la nueva columna de categoria
                def colorear_columna_tipo(columna):
                    estilos = []
                    for valor in columna:
                        if "Hormiga" in str(valor):
                            estilos.append("color: #f1c40f; font-weight: bold;")
                        elif "Primario" in str(valor):
                            estilos.append("color: #2ecc71; font-weight: bold;")
                        elif "Extraordinario" in str(valor):
                            estilos.append("color: #e74c3c; font-weight: bold;")
                        else:
                            estilos.append("")
                    return estilos

                st.write("**Tabla Clasificada Avanzada:**")
                st.dataframe(
                    df_para_mostrar.style.apply(colorear_columna_tipo, subset=["categoria_patron"], axis=0),
                    use_container_width=True,
                    hide_index=True,
                )
                st.divider()
                
                # combina diccionarios para no perder contexto en el simulador
                info_combinada = {**resultado_basico, **resultado_avanzado}
                
                # envia variables a la memoria compartida
                st.session_state["datos_simulador"] = {
                    "df": df_con_clusters,
                    "centroides": centroides,
                    "info": info_combinada,
                    "mejor_k": resultados_modelo.get("mejor_k"),
                    "scores": resultados_modelo.get("scores"),
                    "columnas_features": resultados_modelo.get("columnas_features")
                }
                
                # boton nativo sin emojis
                if st.button("abrir simulador de caja blanca", use_container_width=True):
                    st.switch_page("pages/simulador.py")
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