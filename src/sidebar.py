"""Componentes compartidos para el sidebar de AntCluster."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.preprocessing import DEFAULT_PRESUPUESTO_TOTAL, normalizar_presupuesto_total
from src.utils import calcular_presupuesto_actualizado, get_extra_income_summary, leer_ingresos_extra


def render_sidebar_presupuesto() -> tuple[float, float, pd.DataFrame, dict[str, float | int]]:
    """Renderiza solo el presupuesto base y actualiza el presupuesto total oficial."""
    ingresos_extra = leer_ingresos_extra()
    resumen_ingresos = get_extra_income_summary()
    total_ingresos_extra = float(resumen_ingresos["total_ingresos_extra"])

    if "presupuesto_base" not in st.session_state:
        presupuesto_state = normalizar_presupuesto_total(
            st.session_state.get("presupuesto_total"),
            fallback=DEFAULT_PRESUPUESTO_TOTAL,
            allow_non_positive=True,
        )
        st.session_state["presupuesto_base"] = float(max(presupuesto_state - total_ingresos_extra, 0.0))
    else:
        st.session_state["presupuesto_base"] = normalizar_presupuesto_total(
            st.session_state["presupuesto_base"],
            fallback=DEFAULT_PRESUPUESTO_TOTAL,
            allow_non_positive=True,
        )

    presupuesto_base = st.sidebar.number_input(
        "Presupuesto base del mes (Bs)",
        min_value=0.0,
        step=10.0,
        format="%.2f",
        key="presupuesto_base",
    )

    presupuesto_total = calcular_presupuesto_actualizado(float(presupuesto_base), ingresos_extra)
    st.session_state["presupuesto_total"] = float(presupuesto_total)

    return float(presupuesto_base), float(presupuesto_total), ingresos_extra, resumen_ingresos
