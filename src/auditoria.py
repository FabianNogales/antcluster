# modulo de auditoria y explicabilidad visual
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

from src.model import calcular_distancias_a_centroides
from src.classifier import clasificar_patrones_avanzados

def _obtener_nombre_cluster(cluster_id: int, info: dict, df: pd.DataFrame) -> str:
    if info.get("cluster_hormiga") == cluster_id:
        return "gasto hormiga"
    if info.get("cluster_primario") == cluster_id:
        return "gasto primario"
    if "resumen_por_cluster" in info:
        resumen = info["resumen_por_cluster"]
        filtro = resumen[resumen["cluster"] == cluster_id]
        if not filtro.empty:
            return filtro.iloc[0]["categoria_patron"]
    return f"perfil {cluster_id}"

def _renderizar_justificacion_k(scores: pd.DataFrame, mejor_k: int):
    st.markdown("### seleccion automatica del k optimo")
    st.write("el agente evaluo particiones iterativas usando silhouette score.")
    st.latex(r"s(i) = \frac{b(i) - a(i)}{\max\{a(i), b(i)\}}")
    if scores is not None and not scores.empty:
        st.dataframe(scores, hide_index=True)
        st.markdown(f"**decision:** estructura establecida en k = {mejor_k}")
    else:
        st.markdown("**nota:** modelo ejecutado con k estatico.")

def _renderizar_radar(vector_gasto, centroide, columnas):
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vector_gasto, theta=columnas, fill='toself', name='gasto'))
    fig.add_trace(go.Scatterpolar(r=centroide, theta=columnas, fill='toself', name='centroide'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=400, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def _renderizar_grafico_interactivo(vector_gasto, centroides, cluster_asignado, info, df, show_g, show_c):
    fig = go.Figure()
    
    # grafica centroides
    if show_c:
        for i, c in enumerate(centroides):
            nombre_cluster = _obtener_nombre_cluster(i, info, df)
            fig.add_trace(go.Scatter(
                x=[c[2]], y=[c[0]], mode='markers+text',
                marker=dict(size=20, symbol='star', color='#00FFFF', line=dict(width=1, color='black')),
                name=nombre_cluster, text=[nombre_cluster], textposition="top center"
            ))
            
    # grafica gasto
    if show_g:
        fig.add_trace(go.Scatter(
            x=[vector_gasto[2]], y=[vector_gasto[0]], mode='markers',
            marker=dict(size=15, color='#FF0000', line=dict(width=2, color='white')),
            name='gasto'
        ))
        
    fig.update_layout(title="proyeccion 2d interactiva", xaxis_title="frecuencia", yaxis_title="monto", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

def _renderizar_vista_nodo(registro, centroides, columnas, info, df):
    nombre = registro.get('nombre', 'desconocido')
    cluster_id = int(registro.get('cluster', -1))
    
    # calculo de z-score
    distancias_df = calcular_distancias_a_centroides([float(registro[c]) for c in columnas], centroides)
    dist_real = float(distancias_df[distancias_df["cluster"] == cluster_id]["distancia"].iloc[0])
    z_score = (dist_real - distancias_df["distancia"].mean()) / distancias_df["distancia"].std() if distancias_df["distancia"].std() > 0 else 0

    st.markdown(f"### analisis: {nombre}")
    
    # controles con key unico
    col_ctrl1, col_ctrl2 = st.columns(2)
    show_g = col_ctrl1.checkbox("mostrar gasto", True, key=f"show_g_{nombre}")
    show_c = col_ctrl2.checkbox("mostrar centroides", True, key=f"show_c_{nombre}")
    
    _renderizar_grafico_interactivo([float(registro[c]) for c in columnas], centroides, cluster_id, info, df, show_g, show_c)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 1. trazabilidad vectorial")
        df_vec = pd.DataFrame({"dimension": columnas, "valor": [float(registro[c]) for c in columnas]})
        fig_scatter = px.scatter(df_vec, x="dimension", y="valor", size="valor", color="dimension")
        fig_scatter.update_layout(template="plotly_dark")
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.write(f"**z-score:** {z_score:.2f}")

    with col2:
        st.markdown("#### 2. comparativa multidimensional")
        _renderizar_radar([float(registro[c]) for c in columnas], centroides[cluster_id], columnas)
        
    st.markdown(f"**asignacion:** {_obtener_nombre_cluster(cluster_id, info, df)}")

def _renderizar_glosario():
    with st.expander("conceptos clave del modelo"):
        st.markdown("""
        - **silhouette score:** mide qué tan bien se ajusta cada dato a su grupo asignado. el valor va de -1 a 1, donde 1 representa una separación clara entre grupos.
        - **z-score:** mide la desviación de un dato respecto al promedio del clúster. un valor cercano a 0 significa que el gasto es muy representativo del grupo; valores altos indican que es un caso inusual.
        - **centroide:** es el punto central o promedio aritmético de todos los puntos en un clúster. define el perfil característico del grupo.
        """)

def renderizar_simulador_completo(datos_modelo: dict):
    # estado de presupuesto
    if "presupuesto_auditoria" not in st.session_state:
        st.session_state["presupuesto_auditoria"] = 200.0
    
    st.markdown("### analisis de sensibilidad")
    nuevo_presupuesto = st.slider("ajuste de presupuesto total", 50.0, 1000.0, st.session_state["presupuesto_auditoria"])
    st.session_state["presupuesto_auditoria"] = nuevo_presupuesto
    
    df_raw = datos_modelo.get("df")
    centroides = datos_modelo.get("centroides")
    mejor_k = datos_modelo.get("mejor_k", 2)
    scores = datos_modelo.get("scores")
    columnas = datos_modelo.get("columnas_features") or ["monto", "horaDecimal", "frecuencia"]

    info_avanzada = clasificar_patrones_avanzados(df_raw, nuevo_presupuesto)
    df = info_avanzada["df_clasificado"]
    
    pestana_k, pestana_reciente, pestana_general = st.tabs(["justificacion de k", "analisis reciente", "trazabilidad"])

    with pestana_k:
        _renderizar_glosario()
        _renderizar_justificacion_k(scores, mejor_k)

    with pestana_reciente:
        _renderizar_vista_nodo(df.iloc[-1], centroides, columnas, info_avanzada, df)

    with pestana_general:
        df_unicos = df.drop_duplicates(subset=["nombre"])
        nombre = st.selectbox("directorio de gastos", options=df_unicos["nombre"].tolist())
        registro = df_unicos[df_unicos["nombre"] == nombre].iloc[0]
        _renderizar_vista_nodo(registro, centroides, columnas, info_avanzada, df)