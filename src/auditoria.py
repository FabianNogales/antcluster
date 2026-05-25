# modulo de explicabilidad visual para el algoritmo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from src.model import calcular_distancias_a_centroides

def _obtener_nombre_cluster(cluster_id: int, info: dict, df: pd.DataFrame) -> str:
    # verifica etiquetas del modelo basico
    if info.get("cluster_hormiga") == cluster_id:
        return "gasto hormiga"
    if info.get("cluster_primario") == cluster_id:
        return "gasto primario"
    
    # verifica etiquetas del modelo avanzado
    if "resumen_por_cluster" in info:
        resumen = info["resumen_por_cluster"]
        filtro = resumen[resumen["cluster"] == cluster_id]
        if not filtro.empty:
            return filtro.iloc[0]["categoria_patron"]
            
    # busca etiqueta predominante en el dataframe
    if "categoria_patron" in df.columns:
        filtro = df[df["cluster"] == cluster_id]
        if not filtro.empty:
            return filtro["categoria_patron"].mode()[0]
            
    return f"perfil {cluster_id}"

def renderizar_simulador_completo(datos_modelo: dict):
    # extrae variables de sesion
    df = datos_modelo.get("df")
    centroides = datos_modelo.get("centroides")
    mejor_k = datos_modelo.get("mejor_k", 2)
    info = datos_modelo.get("info", {})
    
    scores = datos_modelo.get("scores")
    if scores is None:
        scores = pd.DataFrame()
        
    columnas = datos_modelo.get("columnas_features")
    if not columnas:
        columnas = ["monto", "horaDecimal", "frecuencia"]
        
    if df is None or df.empty or centroides is None:
        st.markdown("**aviso:** faltan datos para mostrar la simulacion.")
        return

    # renderiza pestanas limpias
    pestana_k, pestana_reciente, pestana_general = st.tabs([
        "justificacion de k",
        "analisis del ultimo gasto", 
        "trazabilidad general"
    ])

    with pestana_k:
        _renderizar_justificacion_k(scores, mejor_k)

    with pestana_reciente:
        _renderizar_vista_reciente(df, centroides, columnas, info)

    with pestana_general:
        _renderizar_vista_general(df, centroides, columnas, info)


def _renderizar_justificacion_k(scores: pd.DataFrame, mejor_k: int):
    # explica seleccion automatica de clusters
    st.markdown("### seleccion automatica del k optimo")
    st.write("el agente evaluo particiones iterativas usando silhouette score.")
    st.latex(r"s(i) = \frac{b(i) - a(i)}{\max\{a(i), b(i)\}}")
    
    if scores is not None and not scores.empty:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(scores.style.highlight_max(subset=['silhouette_score'], color='#2ECC71'), hide_index=True)
        with col2:
            st.markdown(f"**decision:** se establecio la estructura en k = {mejor_k} grupos.")
    else:
        st.markdown("**nota:** modelo ejecutado con un k estatico.")


def _graficar_vectores_multik(vector_gasto: np.ndarray, centroides: np.ndarray, nombre_gasto: str, cluster_asignado: int, info: dict, df: pd.DataFrame):
    # renderiza plano cartesiano
    fig, ax = plt.subplots(figsize=(7, 5))
    colores = ['gold', 'green', 'purple', 'cyan', 'magenta']
    
    for i, c in enumerate(centroides):
        color = colores[i % len(colores)]
        edge = 'red' if i == cluster_asignado else 'black'
        linewidth = 2.5 if i == cluster_asignado else 1.0
        
        # asigna nombre semantico real en lugar de indices numericos
        nombre_cluster = _obtener_nombre_cluster(i, info, df)
        
        ax.scatter(c[2], c[0], c=color, s=250, marker='*', edgecolors=edge, linewidths=linewidth, label=nombre_cluster)
        
        if i == cluster_asignado:
            ax.plot([vector_gasto[2], c[2]], [vector_gasto[0], c[0]], color, linestyle='--', alpha=0.8)

    ax.scatter(vector_gasto[2], vector_gasto[0], c='blue', s=120, marker='o', label=f'gasto: {nombre_gasto}')

    ax.set_title("proyeccion 2d (frecuencia vs monto)")
    ax.set_xlabel("frecuencia")
    ax.set_ylabel("monto (bs)")
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    st.pyplot(fig)


def _renderizar_vista_reciente(df: pd.DataFrame, centroides: np.ndarray, columnas: list, info: dict):
    # envia ultimo dato insertado
    ultimo_registro = df.iloc[-1]
    _mostrar_proceso_nodo(ultimo_registro, centroides, columnas, info, df)


def _renderizar_vista_general(df: pd.DataFrame, centroides: np.ndarray, columnas: list, info: dict):
    # genera lista deduplicada
    st.markdown("### selecciona un gasto historico para auditar")
    
    df_unicos = df.drop_duplicates(subset=["nombre"]).copy()
    nombres_gastos = df_unicos["nombre"].tolist()
    gasto_seleccionado = st.selectbox("directorio de gastos", options=nombres_gastos)
    
    if gasto_seleccionado:
        registro = df_unicos[df_unicos["nombre"] == gasto_seleccionado].iloc[0]
        _mostrar_proceso_nodo(registro, centroides, columnas, info, df)


def _mostrar_proceso_nodo(registro: pd.Series, centroides: np.ndarray, columnas: list, info: dict, df: pd.DataFrame):
    # despliega calculos vectoriales
    nombre = registro.get('nombre', 'desconocido')
    cluster_asignado = int(registro.get('cluster', -1))
    
    st.markdown("### 1. extraccion vectorial")
    vector_gasto = [float(registro[col]) for col in columnas]
    st.code(f"{columnas} \n= [ {', '.join([f'{v:.2f}' for v in vector_gasto])} ]", language="json")
    
    st.markdown("### 2. calculo de distancia")
    distancias_df = calcular_distancias_a_centroides(vector_gasto, centroides)
    
    col_dist, col_grafico = st.columns([1, 2])
    
    with col_dist:
        st.write("**distancias por perfil:**")
        st.dataframe(distancias_df.style.format({"distancia": "{:.2f}"}), hide_index=True)
        
        # obtiene etiqueta correcta
        nombre_cluster = _obtener_nombre_cluster(cluster_asignado, info, df)
        st.markdown(f"**asignacion espacial:** {nombre_cluster}")
        
        if 'categoria_patron' in registro.index:
            st.markdown(f"**capa heuristica:** {registro['categoria_patron']}")
            
    with col_grafico:
        # dibuja proyeccion
        _graficar_vectores_multik(np.array(vector_gasto), centroides, nombre, cluster_asignado, info, df)