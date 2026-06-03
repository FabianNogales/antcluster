"""Controlador para la vista desktop de gestion de gastos."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analisis import ejecutar_recomendacion_historica
from src.classifier import (
    calcular_recomendacion_mensual,
    clasificar_patrones_avanzados,
    resumir_finanzas_avanzadas,
)
from src.historico import cargar_gastos_historicos, cargar_modelo_historico, inicializar_archivos_historicos
from src.model import aplicar_kmeans_avanzado
from src.preprocessing import DEFAULT_PRESUPUESTO_TOTAL, normalizar_presupuesto_total
from src.utils import (
    DATA_DIR,
    calcular_presupuesto_actualizado,
    get_expenses_summary,
    get_extra_income_summary,
    guardar_ingreso_extra,
    initialize_data_files,
    leer_ingresos_extra,
    load_demo_data,
    read_expenses,
    reset_user_data,
    save_expense,
)


SUMMARY_ZERO = {
    "total_gastado": 0.0,
    "gastos_hormiga": 0.0,
    "gastos_primarios": 0.0,
    "gastos_extraordinarios": 0.0,
    "porcentaje_hormiga": 0.0,
}


class GastosController:
    """Integra la UI desktop con las funciones existentes de src."""

    TABLE_COLUMNS = [
        "id",
        "nombre",
        "monto",
        "fecha",
        "hora",
        "frecuencia",
        "categoria_patron",
        "impactoMensual",
        "porcentajePresupuesto",
    ]

    def __init__(self, presupuesto_base: float = DEFAULT_PRESUPUESTO_TOTAL) -> None:
        initialize_data_files()
        inicializar_archivos_historicos()
        self._presupuesto_base = normalizar_presupuesto_total(
            presupuesto_base,
            fallback=DEFAULT_PRESUPUESTO_TOTAL,
            allow_non_positive=True,
        )

    @property
    def presupuesto_base(self) -> float:
        return float(self._presupuesto_base)

    def set_presupuesto_base(self, value: float) -> None:
        self._presupuesto_base = normalizar_presupuesto_total(
            value,
            fallback=DEFAULT_PRESUPUESTO_TOTAL,
            allow_non_positive=True,
        )

    def get_data_folder(self) -> Path:
        return DATA_DIR

    def add_expense(self, nombre: str, monto: float) -> None:
        save_expense(nombre, monto)

    def add_extra_income(self, descripcion: str, monto: float) -> None:
        guardar_ingreso_extra(descripcion, monto)

    def load_demo(self) -> None:
        load_demo_data()

    def reset_data(self) -> None:
        reset_user_data()

    def build_snapshot(self) -> dict:
        ingresos_extra = leer_ingresos_extra()
        resumen_ingresos = get_extra_income_summary()
        presupuesto_total = calcular_presupuesto_actualizado(self._presupuesto_base, ingresos_extra)

        expenses = read_expenses()
        resumen_operativo = get_expenses_summary()
        analisis = self._build_analysis(expenses, presupuesto_total)
        table_df = self._build_table_df(expenses, analisis.get("df_usuario"))

        return {
            "presupuesto_base": float(self._presupuesto_base),
            "presupuesto_total": float(presupuesto_total),
            "ingresos_extra": ingresos_extra,
            "resumen_ingresos": resumen_ingresos,
            "resumen_operativo": resumen_operativo,
            "resumen_financiero": analisis["resumen"],
            "recomendacion": analisis["recomendacion"],
            "mensaje_analisis": analisis["mensaje"],
            "gastos_table": table_df,
            "saldo_disponible": float(presupuesto_total) - float(resumen_operativo["total_gastado"]),
        }

    def _build_analysis(self, expenses: pd.DataFrame, presupuesto_total: float) -> dict:
        if expenses.empty:
            return self._build_empty_expense_analysis(presupuesto_total)

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
                "df_usuario": pd.DataFrame(),
                "resumen": SUMMARY_ZERO.copy(),
                "recomendacion": None,
                "mensaje": mensaje_error or "Se necesitan mas datos validos para ejecutar el analisis.",
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

        return {
            "df_usuario": df_solo_usuario,
            "resumen": resumen_avanzado,
            "recomendacion": recomendacion,
            "mensaje": None,
        }

    def _build_empty_expense_analysis(self, presupuesto_total: float) -> dict:
        modelo_historico = cargar_modelo_historico()
        if modelo_historico.get("entrenado"):
            recomendacion = ejecutar_recomendacion_historica(presupuesto_total)
            if recomendacion is not None:
                return {
                    "df_usuario": pd.DataFrame(),
                    "resumen": SUMMARY_ZERO.copy(),
                    "recomendacion": recomendacion,
                    "mensaje": None,
                }

        return {
            "df_usuario": pd.DataFrame(),
            "resumen": SUMMARY_ZERO.copy(),
            "recomendacion": None,
            "mensaje": "Registra al menos dos gastos validos para activar el analisis y la recomendacion mensual.",
        }

    def _build_table_df(self, expenses: pd.DataFrame, df_usuario_clasificado: pd.DataFrame | None) -> pd.DataFrame:
        source = df_usuario_clasificado if df_usuario_clasificado is not None and not df_usuario_clasificado.empty else expenses
        if source is None or source.empty:
            return pd.DataFrame(columns=self.TABLE_COLUMNS[:6])

        table = source.copy()
        visible_columns = [column for column in self.TABLE_COLUMNS if column in table.columns]
        return table.loc[:, visible_columns].reset_index(drop=True)

    pass
