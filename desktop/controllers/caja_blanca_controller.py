"""Controlador para la vista desktop de caja blanca."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.classifier import clasificar_patrones_avanzados
from src.historico import cargar_gastos_historicos, inicializar_archivos_historicos
from src.model import aplicar_kmeans_avanzado, calcular_distancias_a_centroides
from src.preprocessing import DEFAULT_PRESUPUESTO_TOTAL
from src.utils import calcular_presupuesto_actualizado, initialize_data_files, leer_ingresos_extra, read_expenses


FEATURE_COLUMNS = ["monto", "horaDecimal", "frecuencia", "impactoMensual", "porcentajePresupuesto"]
SCORES_COLUMNS = ["k", "silhouette_score"]
TRACE_VECTOR_COLUMNS = ["dimension", "valor"]
REPEATED_CLUSTER_COLUMNS = [
    "cluster",
    "categoria_patron",
    "monto",
    "horaDecimal",
    "frecuencia",
    "impactoMensual",
    "porcentajePresupuesto",
    "subpatron",
]


class CajaBlancaController:
    """Prepara datos explicables del flujo K-Means para PySide6."""

    def __init__(self, presupuesto_base: float = DEFAULT_PRESUPUESTO_TOTAL) -> None:
        initialize_data_files()
        inicializar_archivos_historicos()
        self._presupuesto_base = float(presupuesto_base)
        self._snapshot: dict | None = None

    def refresh(self) -> dict:
        expenses = read_expenses()
        presupuesto_total = self._get_presupuesto_total()
        if expenses.empty:
            self._snapshot = self._empty_snapshot("No hay datos suficientes para analizar.", presupuesto_total)
            return self._snapshot

        df_historico = cargar_gastos_historicos()
        df_combinado = pd.concat([df_historico, expenses], ignore_index=True)
        resultados_modelo = aplicar_kmeans_avanzado(
            df_combinado,
            presupuesto_total=presupuesto_total,
            random_state=42,
        )

        df_cluster = resultados_modelo.get("df")
        centroides = resultados_modelo.get("centroides")
        mensaje_error = resultados_modelo.get("mensaje")
        columnas_features = list(resultados_modelo.get("columnas_features") or FEATURE_COLUMNS)

        if mensaje_error is not None or centroides is None or df_cluster is None or df_cluster.empty:
            self._snapshot = {
                **self._empty_snapshot(self._normalize_message(mensaje_error), presupuesto_total),
                "scores_df": self._scores_df(resultados_modelo.get("scores")),
                "mejor_k": resultados_modelo.get("mejor_k"),
            }
            return self._snapshot

        info_avanzada = clasificar_patrones_avanzados(df_cluster, presupuesto_total)
        df_clasificado = info_avanzada["df_clasificado"].reset_index(drop=True)
        user_start = max(len(df_clasificado) - len(expenses), 0)
        df_usuario = df_clasificado.iloc[user_start:].copy().reset_index(drop=True)

        centroides_df = self._centroids_df(centroides, columnas_features, df_clasificado)
        repeated_df = self._repeated_clusters_df(centroides_df)
        expense_options = self._expense_options(df_usuario)

        self._snapshot = {
            "message": "Simulador actualizado correctamente.",
            "presupuesto_total": float(presupuesto_total),
            "mejor_k": resultados_modelo.get("mejor_k"),
            "scores_df": self._scores_df(resultados_modelo.get("scores")),
            "k_message": self._k_message(resultados_modelo.get("scores"), resultados_modelo.get("mejor_k")),
            "df_plot": df_clasificado,
            "df_usuario": df_usuario,
            "centroides": np.asarray(centroides, dtype=float),
            "columnas_features": columnas_features,
            "centroides_df": centroides_df,
            "expense_options": expense_options,
            "repeated_note": self._repeated_note(repeated_df),
            "repeated_clusters_df": repeated_df,
        }
        return self._snapshot

    def trace_expense(self, option_index: int) -> dict:
        if self._snapshot is None:
            raise ValueError("Actualiza el simulador antes de seleccionar un gasto.")

        df_usuario = self._snapshot.get("df_usuario")
        centroides = self._snapshot.get("centroides")
        columnas = list(self._snapshot.get("columnas_features") or [])
        if df_usuario is None or df_usuario.empty or centroides is None or not columnas:
            raise ValueError("No hay datos suficientes para trazar un gasto.")

        index = int(option_index)
        if index < 0 or index >= len(df_usuario):
            raise ValueError("Selecciona un gasto valido.")

        registro = df_usuario.iloc[index]
        vector = [float(registro[column]) for column in columnas]
        distancias_df = calcular_distancias_a_centroides(vector, centroides)
        cluster = int(registro.get("cluster"))
        categoria = str(registro.get("categoria_patron", "Categoria no definida"))

        return {
            "nombre": str(registro.get("nombre", "Gasto")),
            "cluster": cluster,
            "categoria": categoria,
            "vector_df": pd.DataFrame(
                [{"dimension": column, "valor": value} for column, value in zip(columnas, vector)],
                columns=TRACE_VECTOR_COLUMNS,
            ),
            "distancias_df": distancias_df,
            "explanation": (
                f"El gasto se asigna al cluster {cluster} porque su vector queda mas cerca "
                "de ese centroide que de los demas."
            ),
        }

    def _get_presupuesto_total(self) -> float:
        ingresos_extra = leer_ingresos_extra()
        return calcular_presupuesto_actualizado(self._presupuesto_base, ingresos_extra)

    def _empty_snapshot(self, message: str, presupuesto_total: float) -> dict:
        return {
            "message": message,
            "presupuesto_total": float(presupuesto_total),
            "mejor_k": None,
            "scores_df": pd.DataFrame(columns=SCORES_COLUMNS),
            "k_message": "No hay scores disponibles para justificar K.",
            "df_plot": pd.DataFrame(),
            "df_usuario": pd.DataFrame(),
            "centroides": None,
            "columnas_features": FEATURE_COLUMNS,
            "centroides_df": pd.DataFrame(columns=["cluster", *FEATURE_COLUMNS, "categoria_patron"]),
            "expense_options": [],
            "repeated_note": "No hay clusters repetidos para comparar.",
            "repeated_clusters_df": pd.DataFrame(columns=REPEATED_CLUSTER_COLUMNS),
        }

    def _normalize_message(self, message: str | None) -> str:
        if not message:
            return "No hay datos suficientes para analizar."
        if "Silhouette" in message or "Rango de K" in message:
            return "Se necesitan mas registros para calcular K automatico."
        return str(message)

    def _scores_df(self, scores: object) -> pd.DataFrame:
        if isinstance(scores, pd.DataFrame) and not scores.empty:
            out = scores.copy()
            for column in SCORES_COLUMNS:
                if column not in out.columns:
                    out[column] = pd.NA
            return out.loc[:, SCORES_COLUMNS].reset_index(drop=True)
        return pd.DataFrame(columns=SCORES_COLUMNS)

    def _k_message(self, scores: object, mejor_k: object) -> str:
        scores_df = self._scores_df(scores)
        if scores_df.empty:
            return "No hay scores disponibles; el modelo no pudo justificar K automatico con estos datos."
        return f"El mejor K seleccionado fue {mejor_k}, correspondiente al mayor Silhouette Score evaluado."

    def _centroids_df(self, centroides: object, columnas: list[str], df_clasificado: pd.DataFrame) -> pd.DataFrame:
        centroides_np = np.asarray(centroides, dtype=float)
        if centroides_np.ndim != 2:
            return pd.DataFrame(columns=["cluster", *FEATURE_COLUMNS, "categoria_patron"])

        categories = self._categories_by_cluster(df_clasificado)
        records = []
        for cluster_index, row in enumerate(centroides_np):
            record = {"cluster": cluster_index, "categoria_patron": categories.get(cluster_index, "Sin categoria")}
            for idx, column in enumerate(columnas):
                if column in FEATURE_COLUMNS:
                    record[column] = float(row[idx])
            records.append(record)

        out = pd.DataFrame(records)
        for column in ["cluster", *FEATURE_COLUMNS, "categoria_patron"]:
            if column not in out.columns:
                out[column] = pd.NA
        return out.loc[:, ["cluster", *FEATURE_COLUMNS, "categoria_patron"]].reset_index(drop=True)

    def _categories_by_cluster(self, df: pd.DataFrame) -> dict[int, str]:
        if df.empty or "cluster" not in df.columns or "categoria_patron" not in df.columns:
            return {}
        grouped = (
            df.groupby(["cluster", "categoria_patron"], dropna=False)
            .size()
            .rename("cantidad")
            .reset_index()
            .sort_values(by=["cluster", "cantidad"], ascending=[True, False])
        )
        categories = {}
        for cluster in grouped["cluster"].dropna().unique():
            row = grouped[grouped["cluster"] == cluster].iloc[0]
            categories[int(cluster)] = str(row["categoria_patron"])
        return categories

    def _expense_options(self, df_usuario: pd.DataFrame) -> list[str]:
        options = []
        for index, row in df_usuario.reset_index(drop=True).iterrows():
            nombre = str(row.get("nombre", "Gasto"))
            monto = float(row.get("monto", 0.0) or 0.0)
            fecha = str(row.get("fecha", ""))
            options.append(f"{index + 1}. {nombre} | Bs. {monto:.2f} | {fecha}")
        return options

    def _repeated_clusters_df(self, centroides_df: pd.DataFrame) -> pd.DataFrame:
        if centroides_df.empty or "categoria_patron" not in centroides_df.columns:
            return pd.DataFrame(columns=REPEATED_CLUSTER_COLUMNS)

        duplicated = centroides_df["categoria_patron"].duplicated(keep=False)
        repeated = centroides_df.loc[duplicated].copy()
        if repeated.empty:
            return pd.DataFrame(columns=REPEATED_CLUSTER_COLUMNS)

        repeated["subpatron"] = repeated.apply(self._subpattern, axis=1)
        for column in REPEATED_CLUSTER_COLUMNS:
            if column not in repeated.columns:
                repeated[column] = pd.NA
        return repeated.loc[:, REPEATED_CLUSTER_COLUMNS].reset_index(drop=True)

    def _repeated_note(self, repeated_df: pd.DataFrame) -> str:
        if repeated_df.empty:
            return "No se detectaron clusters distintos con la misma categoria."
        categories = ", ".join(sorted(repeated_df["categoria_patron"].dropna().astype(str).unique()))
        return (
            "Existen clusters con una misma categoria interpretada. Esto es esperado cuando el agente separa "
            f"subpatrones numericos diferentes dentro de: {categories}."
        )

    def _subpattern(self, row: pd.Series) -> str:
        frecuencia = float(row.get("frecuencia", 0.0) or 0.0)
        hora = float(row.get("horaDecimal", 0.0) or 0.0)
        impacto = float(row.get("impactoMensual", 0.0) or 0.0)

        freq_text = "alta frecuencia" if frecuencia >= 4 else "frecuencia media" if frecuencia >= 2 else "baja frecuencia"
        if hora < 12:
            time_text = "manana"
        elif hora < 18:
            time_text = "tarde"
        else:
            time_text = "noche"
        impact_text = "alto impacto" if impacto >= 60 else "impacto medio" if impacto >= 20 else "bajo impacto"
        return f"{freq_text}, {time_text}, {impact_text}"
