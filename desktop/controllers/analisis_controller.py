"""Controlador para la vista desktop de analisis del agente."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.classifier import clasificar_patrones_avanzados, resumir_finanzas_avanzadas
from src.historico import cargar_gastos_historicos, inicializar_archivos_historicos
from src.model import aplicar_kmeans_avanzado
from src.preprocessing import DEFAULT_PRESUPUESTO_TOTAL
from src.utils import calcular_presupuesto_actualizado, initialize_data_files, leer_ingresos_extra, read_expenses


SUMMARY_ZERO = {
    "total_gastado": 0.0,
    "gastos_primarios": 0.0,
    "gastos_hormiga": 0.0,
    "gastos_extraordinarios": 0.0,
    "porcentaje_hormiga": 0.0,
}

FEATURE_COLUMNS = [
    "nombre",
    "monto",
    "horaDecimal",
    "frecuencia",
    "impactoMensual",
    "porcentajePresupuesto",
]

CLASSIFIED_COLUMNS = [
    "nombre",
    "monto",
    "fecha",
    "hora",
    "frecuencia",
    "cluster",
    "categoria_patron",
    "impactoMensual",
    "porcentajePresupuesto",
]

CENTROID_COLUMNS = [
    "cluster",
    "monto",
    "horaDecimal",
    "frecuencia",
    "impactoMensual",
    "porcentajePresupuesto",
]


class AnalisisController:
    """Integra la UI desktop con el flujo K-Means existente."""

    def __init__(self, presupuesto_base: float = DEFAULT_PRESUPUESTO_TOTAL) -> None:
        initialize_data_files()
        inicializar_archivos_historicos()
        self._presupuesto_base = float(presupuesto_base)

    def run_analysis(self) -> dict:
        expenses = read_expenses()
        presupuesto_total = self._get_presupuesto_total()

        if expenses.empty:
            return self._empty_snapshot(
                presupuesto_total=presupuesto_total,
                message="No hay datos suficientes para analizar.",
            )

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
                **self._empty_snapshot(
                    presupuesto_total=presupuesto_total,
                    message=self._normalize_model_message(mensaje_error),
                ),
                "matrix_df": self._select_columns(df_con_clusters, FEATURE_COLUMNS),
                "scores_df": self._scores_df(resultados_modelo.get("scores")),
                "mejor_k": resultados_modelo.get("mejor_k"),
            }

        resultado_avanzado = clasificar_patrones_avanzados(df_con_clusters, presupuesto_total)
        df_clasificado = resultado_avanzado["df_clasificado"]
        df_usuario_clasificado = df_clasificado.tail(len(expenses)).copy()
        resumen = resumir_finanzas_avanzadas(df_usuario_clasificado, presupuesto_total)

        return {
            "message": "Analisis ejecutado correctamente.",
            "presupuesto_total": float(presupuesto_total),
            "resumen": resumen,
            "mejor_k": resultados_modelo.get("mejor_k"),
            "clusters_activos": int(df_usuario_clasificado["cluster"].nunique(dropna=True))
            if "cluster" in df_usuario_clasificado.columns
            else 0,
            "matrix_df": self._select_columns(df_clasificado, FEATURE_COLUMNS),
            "classified_df": self._select_columns(df_usuario_clasificado, CLASSIFIED_COLUMNS),
            "centroids_df": self._centroids_df(centroides, resultados_modelo.get("columnas_features")),
            "scores_df": self._scores_df(resultados_modelo.get("scores")),
        }

    def _get_presupuesto_total(self) -> float:
        ingresos_extra = leer_ingresos_extra()
        return calcular_presupuesto_actualizado(self._presupuesto_base, ingresos_extra)

    def _empty_snapshot(self, presupuesto_total: float, message: str) -> dict:
        return {
            "message": message,
            "presupuesto_total": float(presupuesto_total),
            "resumen": SUMMARY_ZERO.copy(),
            "mejor_k": None,
            "clusters_activos": 0,
            "matrix_df": pd.DataFrame(columns=FEATURE_COLUMNS),
            "classified_df": pd.DataFrame(columns=CLASSIFIED_COLUMNS),
            "centroids_df": pd.DataFrame(columns=CENTROID_COLUMNS),
            "scores_df": pd.DataFrame(columns=["k", "silhouette_score"]),
        }

    def _normalize_model_message(self, message: str | None) -> str:
        if not message:
            return "No hay datos suficientes para analizar."
        if "Silhouette" in message or "Rango de K" in message:
            return "Se necesitan mas registros para calcular K automatico."
        return str(message)

    def _select_columns(self, df: pd.DataFrame | None, columns: list[str]) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=columns)

        out = df.copy()
        for column in columns:
            if column not in out.columns:
                out[column] = pd.NA
        return out.loc[:, columns].reset_index(drop=True)

    def _centroids_df(self, centroides: object, columnas_features: object) -> pd.DataFrame:
        if centroides is None:
            return pd.DataFrame(columns=CENTROID_COLUMNS)

        columnas = list(columnas_features or [])
        centroides_np = np.asarray(centroides, dtype=float)
        if centroides_np.ndim != 2 or not columnas:
            return pd.DataFrame(columns=CENTROID_COLUMNS)

        records = []
        for cluster_index, row in enumerate(centroides_np):
            record = {"cluster": cluster_index}
            for idx, column in enumerate(columnas):
                try:
                    record[column] = float(row[idx])
                except (IndexError, TypeError, ValueError):
                    record[column] = pd.NA
            records.append(record)

        df = pd.DataFrame(records)
        for column in CENTROID_COLUMNS:
            if column not in df.columns:
                df[column] = pd.NA
        return df.loc[:, CENTROID_COLUMNS].reset_index(drop=True)

    def _scores_df(self, scores: object) -> pd.DataFrame:
        if isinstance(scores, pd.DataFrame):
            if scores.empty:
                return pd.DataFrame(columns=["k", "silhouette_score"])
            out = scores.copy()
            for column in ["k", "silhouette_score"]:
                if column not in out.columns:
                    out[column] = pd.NA
            return out.loc[:, ["k", "silhouette_score"]].copy()
        return pd.DataFrame(columns=["k", "silhouette_score"])
