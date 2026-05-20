"""Interfaz principal para la gestión de datos de AntCluster."""

import pandas as pd
import streamlit as st

from src.classifier import clasificar_y_resumir
from src.model import aplicar_kmeans
from src.preprocessing import calcular_frecuencia_mensual_csv, vectorizarTransacciones
from src.utils import (
    get_expenses_summary,
    get_user_csv_bytes,
    initialize_data_files,
    load_demo_data,
    read_expenses,
    reset_user_data,
    save_expense,
    USER_CSV,
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

# ==================== ANÁLISIS DE CLUSTERING ====================
st.divider()
st.subheader("Analisis de Gastos con K-Means")

# Configurar presupuesto total en la barra lateral
presupuesto_total = st.sidebar.number_input(
    "Presupuesto total (Bs)",
    min_value=0.0,
    value=200.0,
    step=10.0,
    format="%.2f"
)

# Ejecutar análisis solo si hay gastos suficientes
if not expenses.empty and len(expenses) >= 2:
    try:
        # Procesar datos: calcular frecuencia mensual
        df_procesado = calcular_frecuencia_mensual_csv(str(USER_CSV))
        
        if df_procesado is not None and not df_procesado.empty:
            # Vectorizar transacciones
            matriz_vectores = vectorizarTransacciones(df_procesado)
            
            # Aplicar K-Means
            df_con_clusters, centroides, mensaje_error = aplicar_kmeans(
                df_procesado, 
                n_clusters=2,
                random_state=42
            )
            
            if mensaje_error is None and centroides is not None:
                # Clasificar y obtener el resumen financiero estructurado
                st.write("**Resumen Financiero:**")
                resultado_clasificacion = clasificar_y_resumir(df_con_clusters, presupuesto_total)
                
                # Mostrar métricas cuantitativas del resumen
                col1, col2, col3, col4 = st.columns(4)
                col1.metric(
                    "Total gastado",
                    f"Bs. {resultado_clasificacion['total_gastado']:.2f}"
                )
                col2.metric(
                    "Gastos Hormiga",
                    f"Bs. {resultado_clasificacion['gastos_hormiga']:.2f}"
                )
                col3.metric(
                    "Gastos Primarios",
                    f"Bs. {resultado_clasificacion['gastos_primarios']:.2f}"
                )
                col4.metric(
                    "Porcentaje Hormiga",
                    f"{resultado_clasificacion['porcentaje_hormiga']:.1f}%"
                )
                
                # Clonar DataFrame para evitar alterar los datos de origen en la visualización
                df_visualizacion = df_con_clusters.copy()
                
                # Identificar índices de los clústeres calculados por la lógica del clasificador
                cluster_hormiga = resultado_clasificacion['cluster_hormiga']
                cluster_primario = resultado_clasificacion['cluster_primario']
                
                # Mapear los identificadores numéricos a etiquetas de texto formales
                def mapear_tipo_gasto(cluster_val):
                    if pd.isna(cluster_val):
                        return "Sin clasificar"
                    elif int(cluster_val) == cluster_hormiga:
                        return "Gasto Hormiga"
                    else:
                        return "Gasto Primario"
                
                df_visualizacion['Tipo'] = df_visualizacion['cluster'].apply(mapear_tipo_gasto)
                
                # Filtrar y ordenar las columnas requeridas para la tabla final
                columnas_mostrar = ['nombre', 'monto', 'fecha', 'hora', 'frecuencia', 'Tipo']
                df_para_mostrar = df_visualizacion[columnas_mostrar]
                
                # Función de estilo que aplica color elegante SOLO a las celdas de la columna 'Tipo'
                def colorear_columna_tipo(columna):
                    estilos = []
                    for valor in columna:
                        if valor == "Gasto Hormiga":
                            estilos.append('color: #F1C40F; font-weight: bold;')  # Texto amarillo dorado elegante
                        elif valor == "Gasto Primario":
                            estilos.append('color: #2ECC71; font-weight: bold;')  # Texto verde esmeralda elegante
                        else:
                            estilos.append('')
                    return estilos
                
                # Renderizar tabla final aplicando los estilos estilizados en la columna seleccionada
                st.write("**Tabla Clasificada:**")
                st.dataframe(
                    df_para_mostrar.style.apply(colorear_columna_tipo, subset=['Tipo'], axis=0),
                    use_container_width=True,
                    hide_index=True
                )
                
            else:
                st.warning(mensaje_error or "No se pudo aplicar K-Means. Intenta con mas datos.")
        else:
            st.info("No hay suficientes datos para procesar.")
    except Exception as e:
        st.error(f"Error en el analisis: {str(e)}")
else:
    st.info("Registra al menos 2 gastos para ver el analisis de clustering.")

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