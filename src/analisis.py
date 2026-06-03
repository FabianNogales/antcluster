"""Funciones compartidas para ejecutar y mostrar el analisis financiero."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.classifier import (
    calcular_recomendacion_mensual,
    clasificar_patrones_avanzados,
    resumir_finanzas_avanzadas,
)
from src.historico import cargar_gastos_historicos
from src.model import aplicar_kmeans_avanzado


def ejecutar_analisis_agente(expenses: pd.DataFrame, presupuesto_total: float) -> dict | None:
    """Ejecuta el analisis actual y deja los datos listos para el simulador."""
    if expenses.empty:
        return None

    df_historico = cargar_gastos_historicos()
    df_combinado = pd.concat([df_historico, expenses], ignore_index=True)
    resultados_modelo = aplicar_kmeans_avanzado(
        df_combinado,
        presupuesto_total=presupuesto_total,
        random_state=42,
    )

    df_con_clusters = resultados_modelo.get("df")
    centroides = resultados_modelo.get("centroides")
    mensaje_error = resultados_modelo.get("mensaje")

    if mensaje_error is not None or centroides is None or df_con_clusters is None or df_con_clusters.empty:
        return {
            "mensaje": mensaje_error or "Se necesitan mas datos validos para ejecutar el analisis.",
            "centroides": centroides,
            "df": df_con_clusters,
        }

    resultado_avanzado = clasificar_patrones_avanzados(df_con_clusters, presupuesto_total)
    df_visualizacion = resultado_avanzado["df_clasificado"]
    df_historico_clasificado = df_visualizacion.head(len(df_historico)).copy()
    df_solo_usuario = df_visualizacion.tail(len(expenses)).copy()
    resumen_avanzado = resumir_finanzas_avanzadas(df_solo_usuario, presupuesto_total)
    df_recomendacion = df_historico_clasificado if not df_historico_clasificado.empty else df_solo_usuario
    recomendacion = calcular_recomendacion_mensual(
        presupuesto_total=presupuesto_total,
        df_clasificado=df_recomendacion,
    )

    info_combinada = {**resumen_avanzado, **resultado_avanzado}
    st.session_state["datos_simulador"] = {
        "df": df_con_clusters,
        "centroides": centroides,
        "info": info_combinada,
        "mejor_k": resultados_modelo.get("mejor_k"),
        "scores": resultados_modelo.get("scores"),
        "columnas_features": resultados_modelo.get("columnas_features"),
        "presupuesto_total": float(presupuesto_total),
    }

    return {
        "df_usuario": df_solo_usuario,
        "resumen": resumen_avanzado,
        "recomendacion": recomendacion,
        "resultados_modelo": resultados_modelo,
        "mensaje": None,
    }


def ejecutar_recomendacion_historica(presupuesto_total: float) -> dict | None:
    """Calcula una recomendacion mensual desde el CSV historico sin reentrenar el agente."""
    df_historico = cargar_gastos_historicos()
    if df_historico.empty:
        return None

    resultados_modelo = aplicar_kmeans_avanzado(
        df_historico,
        presupuesto_total=presupuesto_total,
        random_state=42,
    )
    df_con_clusters = resultados_modelo.get("df")
    centroides = resultados_modelo.get("centroides")
    mensaje_error = resultados_modelo.get("mensaje")
    if mensaje_error is not None or centroides is None or df_con_clusters is None or df_con_clusters.empty:
        return None

    resultado_avanzado = clasificar_patrones_avanzados(df_con_clusters, presupuesto_total)
    return calcular_recomendacion_mensual(
        presupuesto_total=presupuesto_total,
        df_clasificado=resultado_avanzado["df_clasificado"],
        modo="ultimo_mes",
    )


def render_recomendacion(recomendacion: dict) -> None:
    """Muestra la recomendacion mensual en columnas."""
    if recomendacion.get("advertencia_periodo"):
        st.warning(recomendacion["advertencia_periodo"])
    elif recomendacion.get("periodo_texto"):
        st.caption(f"Recomendacion basada en el ultimo mes historico: {recomendacion['periodo_texto']}.")
    else:
        st.caption("Basado en el ultimo mes historico disponible.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Apartar para primarios", f"Bs. {recomendacion['apartar_primarios']:.2f}")
    col2.metric("Controlar hormiga", f"Bs. {recomendacion['controlar_hormiga']:.2f}")
    col3.metric("Reservar extraordinarios", f"Bs. {recomendacion['reservar_extraordinarios']:.2f}")
    col4.metric("Posible ahorro", f"Bs. {recomendacion['ahorro_estimado']:.2f}")

    st.caption(f"Compromiso del presupuesto: {recomendacion['compromiso_presupuesto']:.1f}%")
    if recomendacion["presupuesto_cubre_patron"]:
        st.success(recomendacion["mensaje"])
    else:
        st.warning("El presupuesto no cubre el patron actual de consumo.")
