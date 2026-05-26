"""Interfaz principal para la gestion de datos de AntCluster."""

import streamlit as st

from src.classifier import clasificar_patrones_avanzados, resumir_finanzas_avanzadas
from src.historico import (
    MODELO_HISTORICO_JSON,
    cargar_gastos_historicos,
    cargar_modelo_historico,
    clasificar_gasto_con_modelo_historico,
    entrenar_agente_historico,
    guardar_modelo_historico,
    inicializar_archivos_historicos,
)
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

st.set_page_config(page_title="AntCluster - Gestion de datos", layout="wide")
initialize_data_files()
inicializar_archivos_historicos()

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
    value=500.0,
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
                
                resultado_avanzado = clasificar_patrones_avanzados(df_con_clusters, presupuesto_total)
                df_visualizacion = resultado_avanzado["df_clasificado"]
                resumen_avanzado = resumir_finanzas_avanzadas(df_visualizacion, presupuesto_total)

                col1, col2, col3 = st.columns(3)
                col1.metric("Total gastado", f"Bs. {resumen_avanzado['total_gastado']:.2f}")
                col2.metric("Gastos Hormiga", f"Bs. {resumen_avanzado['gastos_hormiga']:.2f}")
                col3.metric("Gastos Primarios", f"Bs. {resumen_avanzado['gastos_primarios']:.2f}")

                col4, col5 = st.columns(2)
                col4.metric("Gastos Extraord.", f"Bs. {resumen_avanzado['gastos_extraordinarios']:.2f}")
                col5.metric(
                    "Porcentaje Hormiga",
                    f"{resumen_avanzado['porcentaje_hormiga']:.1f}%",
                )

                # configura las 5 columnas base mas el patron
                columnas_mostrar = [
                    "nombre",
                    "categoria_patron",
                    "monto",
                    "fecha",
                    "hora",
                    "frecuencia",
                    "impactoMensual",
                    "porcentajePresupuesto",
                ]
                df_para_mostrar = df_visualizacion[columnas_mostrar].copy()
                for col_num in ["monto", "frecuencia", "impactoMensual", "porcentajePresupuesto"]:
                    df_para_mostrar[col_num] = df_para_mostrar[col_num].round(2)

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
                    column_config={
                        "nombre": st.column_config.TextColumn("nombre", width="medium"),
                        "categoria_patron": st.column_config.TextColumn("categoria_patron", width="medium"),
                        "monto": st.column_config.NumberColumn("monto", format="%.2f"),
                        "frecuencia": st.column_config.NumberColumn("frecuencia", format="%.2f"),
                        "impactoMensual": st.column_config.NumberColumn("impactoMensual", format="%.2f"),
                        "porcentajePresupuesto": st.column_config.NumberColumn("porcentajePresupuesto", format="%.2f"),
                    },
                    use_container_width=True,
                    hide_index=True,
                )
                st.divider()
                
                # combina diccionarios para no perder contexto en el simulador
                info_combinada = {**resumen_avanzado, **resultado_avanzado}
                
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

# ==================== APRENDIZAJE HISTORICO ====================
st.subheader("Aprendizaje histórico")
modelo_historico = cargar_modelo_historico()
df_historico = cargar_gastos_historicos()
estado_modelo = "entrenado" if modelo_historico.get("entrenado") else "no entrenado"
existe_modelo = MODELO_HISTORICO_JSON.exists() and MODELO_HISTORICO_JSON.stat().st_size > 0
st.write(f"Estado del modelo histórico: **{estado_modelo}**")
st.caption(f"Archivo modelo_historico.json: {'Disponible' if existe_modelo else 'No disponible'}")
st.caption(f"Registros históricos disponibles: {len(df_historico)}")

if st.button("Entrenar agente histórico", use_container_width=True):
    try:
        nuevo_modelo = entrenar_agente_historico(df_historico, presupuesto_total=presupuesto_total)
        guardar_modelo_historico(nuevo_modelo)
        st.success("Entrenamiento histórico completado y guardado.")
        st.rerun()
    except Exception:
        st.error("No se pudo entrenar el modelo histórico con los datos actuales.")

if modelo_historico.get("entrenado"):
    st.write("**Resumen del entrenamiento histórico:**")
    col_h1, col_h2, col_h3 = st.columns(3)
    col_h1.metric("Fecha entrenamiento", str(modelo_historico.get("fecha_entrenamiento") or "-"))
    col_h2.metric("Registros usados", int(modelo_historico.get("cantidad_registros") or 0))
    col_h3.metric("Mejor K histórico", int(modelo_historico.get("mejor_k") or 0))

    centroides_hist = modelo_historico.get("centroides", [])
    columnas_hist = modelo_historico.get("columnas_features", [])
    if centroides_hist and columnas_hist:
        st.write("Centroides históricos")
        st.dataframe(
            data={
                "cluster": list(range(len(centroides_hist))),
                **{
                    col: [float(row[idx]) for row in centroides_hist]
                    for idx, col in enumerate(columnas_hist)
                },
            },
            use_container_width=True,
            hide_index=True,
        )

    scores_hist = modelo_historico.get("scores_silhouette", [])
    if scores_hist:
        st.write("Scores de Silhouette históricos")
        st.dataframe(scores_hist, use_container_width=True, hide_index=True)

    with st.form("formulario_clasificacion_historica"):
        st.write("Clasificar nuevo gasto con centroides históricos")
        nombre_h = st.text_input("Nombre nuevo gasto", value="Gasto nuevo")
        monto_h = st.number_input("Monto nuevo gasto", min_value=0.0, step=0.5, format="%.2f")
        fecha_h = st.date_input("Fecha nuevo gasto")
        hora_h = st.text_input("Hora nuevo gasto (HH:MM)", value="12:00")
        frecuencia_h = st.number_input("Frecuencia (opcional)", min_value=0, value=1, step=1)
        enviar_h = st.form_submit_button("Clasificar con histórico")

    if enviar_h:
        try:
            resultado_hist = clasificar_gasto_con_modelo_historico(
                {
                    "nombre": nombre_h,
                    "monto": monto_h,
                    "fecha": fecha_h.strftime("%Y-%m-%d"),
                    "hora": hora_h,
                    "frecuencia": frecuencia_h,
                },
                modelo_historico=modelo_historico,
                presupuesto_total=presupuesto_total,
            )
            st.success("Clasificación histórica ejecutada.")
            st.write(f"Cluster asignado: **{resultado_hist['cluster_asignado']}**")
            st.write(f"Categoría interpretada: **{resultado_hist['categoria_interpretada']}**")
            st.write(resultado_hist["explicacion"])
            st.write("Vector generado")
            st.json(resultado_hist["vector_generado"])
            st.write("Distancias a centroides")
            st.dataframe(resultado_hist["distancias_centroides"], use_container_width=True, hide_index=True)
        except ValueError as error:
            st.error(str(error))
        except Exception:
            st.error("No se pudo clasificar el nuevo gasto con el modelo histórico.")
else:
    st.info("Todavía no hay un modelo histórico entrenado.")

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
