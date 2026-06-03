"""Controlador para la vista desktop de aprendizaje historico."""

from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from src.historico import (
    MODELO_HISTORICO_JSON,
    cargar_gastos_historicos,
    cargar_modelo_historico,
    clasificar_gasto_con_modelo_historico,
    entrenar_agente_historico,
    guardar_modelo_historico,
    inicializar_archivos_historicos,
)
from src.preprocessing import DEFAULT_PRESUPUESTO_TOTAL, calcularHoraDecimal
from src.utils import calcular_presupuesto_actualizado, initialize_data_files, leer_ingresos_extra


CENTROID_COLUMNS = [
    "cluster",
    "monto",
    "horaDecimal",
    "frecuencia",
    "impactoMensual",
    "porcentajePresupuesto",
]


class HistoricoController:
    """Integra la UI desktop con las funciones historicas existentes."""

    def __init__(self, presupuesto_base: float = DEFAULT_PRESUPUESTO_TOTAL) -> None:
        initialize_data_files()
        inicializar_archivos_historicos()
        self._presupuesto_base = float(presupuesto_base)

    def build_snapshot(self) -> dict:
        modelo = cargar_modelo_historico()
        df_historico = cargar_gastos_historicos()
        presupuesto_total = self._get_presupuesto_total()

        return {
            "modelo": modelo,
            "estado_modelo": "entrenado" if modelo.get("entrenado") else "no entrenado",
            "modelo_existe": MODELO_HISTORICO_JSON.exists() and MODELO_HISTORICO_JSON.stat().st_size > 0,
            "registros_historicos": int(len(df_historico)),
            "presupuesto_activo": float(presupuesto_total),
            "presupuesto_entrenamiento": modelo.get("presupuesto_total"),
            "resumen_entrenamiento": self._build_training_summary(modelo),
            "centroides_df": self._build_centroids_df(modelo),
            "scores_df": self._build_scores_df(modelo),
        }

    def train(self) -> dict:
        df_historico = cargar_gastos_historicos()
        nuevo_modelo = entrenar_agente_historico(
            df_historico,
            presupuesto_total=self._get_presupuesto_total(),
        )
        guardar_modelo_historico(nuevo_modelo)
        return nuevo_modelo

    def classify_expense(
        self,
        nombre: str,
        monto: float,
        fecha: str,
        hora: str,
        frecuencia: int,
    ) -> dict:
        modelo = cargar_modelo_historico()
        self._validate_classification_input(modelo, nombre, monto, hora, frecuencia)

        resultado = clasificar_gasto_con_modelo_historico(
            {
                "nombre": nombre.strip(),
                "monto": float(monto),
                "fecha": fecha,
                "hora": hora.strip(),
                "frecuencia": int(frecuencia),
            },
            modelo_historico=modelo,
            presupuesto_total=self._get_presupuesto_total(),
        )

        return {
            **resultado,
            "vector_df": self._build_vector_df(resultado),
            "distancias_df": pd.DataFrame(resultado.get("distancias_centroides", [])),
        }

    def _get_presupuesto_total(self) -> float:
        ingresos_extra = leer_ingresos_extra()
        return calcular_presupuesto_actualizado(self._presupuesto_base, ingresos_extra)

    def _build_training_summary(self, modelo: dict) -> dict:
        columnas = modelo.get("columnas_features") or []
        return {
            "fecha_entrenamiento": modelo.get("fecha_entrenamiento") or "-",
            "cantidad_registros": int(modelo.get("cantidad_registros") or 0),
            "mejor_k": modelo.get("mejor_k"),
            "presupuesto_total": modelo.get("presupuesto_total"),
            "columnas_features": ", ".join(str(col) for col in columnas) if columnas else "-",
        }

    def _build_centroids_df(self, modelo: dict) -> pd.DataFrame:
        centroides = modelo.get("centroides") or []
        columnas = list(modelo.get("columnas_features") or [])
        if not centroides or not columnas:
            return pd.DataFrame(columns=CENTROID_COLUMNS)

        records = []
        for cluster_index, row in enumerate(centroides):
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
        return df.loc[:, CENTROID_COLUMNS]

    def _build_scores_df(self, modelo: dict) -> pd.DataFrame:
        scores = modelo.get("scores_silhouette") or []
        if not scores:
            return pd.DataFrame(columns=["k", "silhouette_score"])
        return pd.DataFrame(scores, columns=["k", "silhouette_score"])

    def _build_vector_df(self, resultado: dict) -> pd.DataFrame:
        vector = resultado.get("vector_generado") or {}
        if not vector:
            return pd.DataFrame(columns=["feature", "valor"])
        return pd.DataFrame(
            [{"feature": key, "valor": value} for key, value in vector.items()],
            columns=["feature", "valor"],
        )

    def _validate_classification_input(
        self,
        modelo: dict,
        nombre: str,
        monto: float,
        hora: str,
        frecuencia: int,
    ) -> None:
        if not modelo.get("entrenado") or not modelo.get("centroides"):
            raise ValueError("Primero entrene el agente historico.")

        if not nombre.strip():
            raise ValueError("El nombre del gasto no puede estar vacio.")

        if float(monto) <= 0:
            raise ValueError("El monto debe ser mayor a 0.")

        hora_texto = hora.strip()
        if not re.fullmatch(r"\d{2}:\d{2}", hora_texto):
            raise ValueError("La hora debe tener formato HH:MM.")

        try:
            datetime.strptime(hora_texto, "%H:%M")
        except ValueError as error:
            raise ValueError("La hora debe tener formato HH:MM valido.") from error

        if pd.isna(calcularHoraDecimal(hora_texto)):
            raise ValueError("La hora debe tener formato HH:MM valido.")

        if int(frecuencia) <= 0:
            raise ValueError("La frecuencia debe ser mayor a 0.")
