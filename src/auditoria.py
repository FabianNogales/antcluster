# modulo de auditoria y explicabilidad visual
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from src.classifier import clasificar_patrones_avanzados
from src.model import calcular_distancias_a_centroides
from src.preprocessing import DEFAULT_PRESUPUESTO_TOTAL, normalizar_presupuesto_total
from src.theme import ACCENT, DANGER, TEXT_MAIN, WARNING, style_plotly_figure


def _color_categoria(categoria: str) -> str:
    if categoria == "Gasto Primario":
        return ACCENT
    if categoria == "Gasto Hormiga Recurrente":
        return WARNING
    if categoria == "Gasto Hormiga Ocasional":
        return "#4aa3ff"
    if categoria == "Gasto Extraordinario":
        return DANGER
    return TEXT_MAIN


def _obtener_nombre_cluster(cluster_id: int, info: dict, df: pd.DataFrame) -> str:
    if info.get("cluster_hormiga") == cluster_id:
        return "Gasto Hormiga"
    if info.get("cluster_primario") == cluster_id:
        return "Gasto Primario"
    if "resumen_por_cluster" in info:
        resumen = info["resumen_por_cluster"]
        filtro = resumen[resumen["cluster"] == cluster_id]
        if not filtro.empty:
            return str(filtro.iloc[0]["categoria_patron"])
    return f"Perfil {cluster_id}"


def formatear_etiqueta_cluster(cluster_id: int, info: dict, df: pd.DataFrame) -> str:
    """Genera una etiqueta unica por cluster para la leyenda del simulador."""
    categoria = _obtener_nombre_cluster(cluster_id, info, df)
    return f"Cluster {cluster_id} - {categoria}"


def _renderizar_justificacion_k(scores: pd.DataFrame, mejor_k: int) -> None:
    st.markdown("### Seleccion automatica del K optimo")
    st.write("El agente evaluo particiones iterativas usando Silhouette Score.")
    st.latex(r"s(i) = \frac{b(i) - a(i)}{\max\{a(i), b(i)\}}")
    if scores is not None and not scores.empty:
        st.dataframe(scores, hide_index=True)
        st.markdown(f"**Decision:** estructura establecida en K = {mejor_k}")
    else:
        st.markdown("**Nota:** modelo ejecutado con K estatico.")


def _renderizar_radar(vector_gasto, centroide, columnas) -> None:
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=vector_gasto,
            theta=columnas,
            fill="toself",
            name="Gasto seleccionado",
            line=dict(color=DANGER),
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=centroide,
            theta=columnas,
            fill="toself",
            name="Centroide asignado",
            line=dict(color=ACCENT),
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=True,
        height=400,
    )
    style_plotly_figure(fig)
    st.plotly_chart(fig, use_container_width=True)


def _renderizar_grafico_interactivo(
    vector_gasto,
    centroides,
    cluster_asignado,
    info,
    df,
    show_g,
    show_c,
) -> None:
    fig = go.Figure()

    if show_c:
        for i, centroide in enumerate(centroides):
            categoria = _obtener_nombre_cluster(i, info, df)
            nombre_cluster = formatear_etiqueta_cluster(i, info, df)
            fig.add_trace(
                go.Scatter(
                    x=[centroide[2]],
                    y=[centroide[0]],
                    mode="markers+text",
                    marker=dict(
                        size=24 if i == cluster_asignado else 20,
                        symbol="star",
                        color=ACCENT,
                        line=dict(width=2, color=_color_categoria(categoria)),
                    ),
                    name=nombre_cluster,
                    text=[nombre_cluster],
                    textposition="top center",
                )
            )

    if show_g:
        fig.add_trace(
            go.Scatter(
                x=[vector_gasto[2]],
                y=[vector_gasto[0]],
                mode="markers",
                marker=dict(size=15, color=DANGER, line=dict(width=2, color=TEXT_MAIN)),
                name="Gasto seleccionado",
            )
        )

    fig.update_layout(
        title="Proyeccion 2D interactiva",
        xaxis_title="Frecuencia",
        yaxis_title="Monto",
        legend=dict(title="Leyenda"),
    )
    style_plotly_figure(fig)
    st.plotly_chart(fig, use_container_width=True)


def _renderizar_vista_nodo(registro, centroides, columnas, info, df) -> None:
    nombre = registro.get("nombre", "desconocido")
    cluster_id = int(registro.get("cluster", -1))

    distancias_df = calcular_distancias_a_centroides([float(registro[c]) for c in columnas], centroides)
    z_scores = stats.zscore(distancias_df["distancia"].to_numpy(dtype=float), ddof=0, nan_policy="omit")
    if np.isnan(z_scores).all():
        z_score = 0.0
    else:
        idx = int(distancias_df.index[distancias_df["cluster"] == cluster_id][0])
        z_score = float(np.nan_to_num(z_scores[idx], nan=0.0))

    st.markdown(f"### Analisis: {nombre}")

    col_ctrl1, col_ctrl2 = st.columns(2)
    show_g = col_ctrl1.checkbox("Mostrar gasto", True, key=f"show_g_{nombre}")
    show_c = col_ctrl2.checkbox("Mostrar centroides", True, key=f"show_c_{nombre}")

    _renderizar_grafico_interactivo(
        [float(registro[c]) for c in columnas],
        centroides,
        cluster_id,
        info,
        df,
        show_g,
        show_c,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 1. Trazabilidad vectorial")
        df_vec = pd.DataFrame({"dimension": columnas, "valor": [float(registro[c]) for c in columnas]})
        fig_scatter = px.scatter(
            df_vec,
            x="dimension",
            y="valor",
            size="valor",
            color="dimension",
        )
        style_plotly_figure(fig_scatter)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.write(f"**Z-score:** {z_score:.2f}")

    with col2:
        st.markdown("#### 2. Comparativa multidimensional")
        _renderizar_radar([float(registro[c]) for c in columnas], centroides[cluster_id], columnas)

    st.markdown(f"**Asignacion:** {formatear_etiqueta_cluster(cluster_id, info, df)}")


def _renderizar_glosario() -> None:
    with st.expander("Conceptos clave del modelo"):
        st.markdown(
            """
            - **Silhouette Score:** mide que tan bien se ajusta cada dato a su grupo asignado. El valor va de -1 a 1.
            - **Z-score:** mide la desviacion de un dato respecto al promedio del cluster.
            - **Centroide:** es el punto central o promedio aritmetico de todos los puntos en un cluster.
            """
        )


def renderizar_simulador_completo(datos_modelo: dict) -> None:
    presupuesto_base = normalizar_presupuesto_total(
        st.session_state.get("presupuesto_total", datos_modelo.get("presupuesto_total", DEFAULT_PRESUPUESTO_TOTAL)),
        fallback=DEFAULT_PRESUPUESTO_TOTAL,
        allow_non_positive=True,
    )

    if "presupuesto_auditoria" not in st.session_state:
        st.session_state["presupuesto_auditoria"] = float(presupuesto_base)
    rango_maximo = max(100.0, presupuesto_base * 2.0 if presupuesto_base > 0 else 100.0)
    valor_inicial_slider = float(st.session_state["presupuesto_auditoria"])
    valor_inicial_slider = min(max(valor_inicial_slider, 0.0), rango_maximo)

    st.markdown("### Analisis de sensibilidad")
    nuevo_presupuesto = st.slider(
        "Ajuste de presupuesto total",
        min_value=0.0,
        max_value=float(rango_maximo),
        value=float(valor_inicial_slider),
        step=10.0,
    )
    st.session_state["presupuesto_auditoria"] = nuevo_presupuesto

    df_raw = datos_modelo.get("df")
    centroides = datos_modelo.get("centroides")
    mejor_k = datos_modelo.get("mejor_k", 2)
    scores = datos_modelo.get("scores")
    columnas = datos_modelo.get("columnas_features") or ["monto", "horaDecimal", "frecuencia"]

    info_avanzada = clasificar_patrones_avanzados(df_raw, nuevo_presupuesto)
    df = info_avanzada["df_clasificado"]

    st.markdown("### Datos usados por el agente")
    columnas_historial = [
        col
        for col in [
            "nombre",
            "monto",
            "hora",
            "frecuencia",
            "impactoMensual",
            "porcentajePresupuesto",
            "cluster",
            "categoria_patron",
        ]
        if col in df.columns
    ]
    st.dataframe(df[columnas_historial], use_container_width=True, hide_index=True)

    st.markdown("### Vectorizacion y matriz X")
    columnas_x = [c for c in columnas if c in df.columns]
    st.dataframe(df[columnas_x], use_container_width=True, hide_index=True)

    if centroides is not None and len(columnas) > 0:
        st.markdown("### Centroides")
        centroides_df = pd.DataFrame(centroides, columns=columnas)
        centroides_df.insert(0, "cluster", range(len(centroides_df)))
        centroides_df["etiqueta"] = [
            formatear_etiqueta_cluster(int(cluster_id), info_avanzada, df)
            for cluster_id in centroides_df["cluster"]
        ]
        st.dataframe(centroides_df, use_container_width=True, hide_index=True)

    pestana_k, pestana_reciente, pestana_general = st.tabs(
        ["Justificacion de K", "Analisis reciente", "Trazabilidad"]
    )

    with pestana_k:
        _renderizar_glosario()
        _renderizar_justificacion_k(scores, mejor_k)

    with pestana_reciente:
        _renderizar_vista_nodo(df.iloc[-1], centroides, columnas, info_avanzada, df)

    with pestana_general:
        df_unicos = df.drop_duplicates(subset=["nombre"])
        nombre = st.selectbox("Directorio de gastos", options=df_unicos["nombre"].tolist())
        registro = df_unicos[df_unicos["nombre"] == nombre].iloc[0]
        _renderizar_vista_nodo(registro, centroides, columnas, info_avanzada, df)
