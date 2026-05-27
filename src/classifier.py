"""Clasificacion semantica de clusters para AntCluster."""

from __future__ import annotations

import logging

import pandas as pd

from src.preprocessing import (
    DEFAULT_PRESUPUESTO_TOTAL,
    normalizar_presupuesto_total,
    preparar_features_avanzadas,
)

logger = logging.getLogger(__name__)


def clasificar_y_resumir(df_gastos: pd.DataFrame, presupuesto_total: float) -> dict:
    """
    Clasifica gastos en "Gasto Hormiga" y "Gasto Primario" basandose en el cluster.

    El cluster con promedio de monto mas bajo es clasificado como "Gasto Hormiga",
    y el otro como "Gasto Primario".
    """
    if df_gastos.empty:
        raise ValueError("El DataFrame no puede estar vacio")

    if "cluster" not in df_gastos.columns:
        raise ValueError("El DataFrame debe contener una columna 'cluster'")

    if "monto" not in df_gastos.columns:
        raise ValueError("El DataFrame debe contener una columna 'monto'")

    promedios = df_gastos.groupby("cluster")["monto"].mean()

    cluster_hormiga = promedios.idxmin()
    cluster_primario = promedios.idxmax()

    gastos_hormiga = df_gastos[df_gastos["cluster"] == cluster_hormiga]
    gastos_primarios = df_gastos[df_gastos["cluster"] == cluster_primario]

    total_hormiga = gastos_hormiga["monto"].sum()
    total_primario = gastos_primarios["monto"].sum()
    total_gastado = total_hormiga + total_primario
    cantidad_hormiga = len(gastos_hormiga)

    porcentaje_hormiga = (total_hormiga / presupuesto_total * 100) if presupuesto_total > 0 else 0

    logger.debug(
        "Resumen clasificar_y_resumir total=%.2f hormiga=%.2f primario=%.2f porcentaje_hormiga=%.2f",
        total_gastado,
        total_hormiga,
        total_primario,
        porcentaje_hormiga,
    )

    return {
        "total_gastado": total_gastado,
        "gastos_hormiga": total_hormiga,
        "gastos_primarios": total_primario,
        "cantidad_hormiga": cantidad_hormiga,
        "porcentaje_hormiga": porcentaje_hormiga,
        "cluster_hormiga": cluster_hormiga,
        "cluster_primario": cluster_primario,
    }


def _safe_budget(presupuesto_total: float) -> float:
    return normalizar_presupuesto_total(
        presupuesto_total,
        fallback=DEFAULT_PRESUPUESTO_TOTAL,
        allow_non_positive=True,
    )


def _threshold(series: pd.Series, q: float) -> float:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return 0.0
    return float(clean.quantile(q))


def _clasificar_fila_patron(
    row: pd.Series,
    umbrales: dict[str, float],
) -> str:
    monto = float(row.get("monto", 0.0))
    frecuencia = float(row.get("frecuencia", 0.0))
    impacto = float(row.get("impactoMensual", 0.0))
    porcentaje = float(row.get("porcentajePresupuesto", 0.0))

    monto_bajo = umbrales["monto_bajo"]
    monto_primario = umbrales["monto_primario"]
    monto_extraordinario = umbrales["monto_extraordinario"]
    freq_baja = umbrales["freq_baja"]
    freq_repetida = umbrales["freq_repetida"]
    freq_alta = umbrales["freq_alta"]
    impacto_recurrente = umbrales["impacto_recurrente"]
    impacto_primario = umbrales["impacto_primario"]
    porcentaje_primario = umbrales["porcentaje_primario"]

    # Evento de monto alto y baja frecuencia: gasto no recurrente.
    if monto >= monto_extraordinario and frecuencia <= freq_baja:
        return "Gasto Extraordinario"

    # Gasto base de vida/recurrente con impacto mensual alto.
    if monto >= monto_primario and frecuencia >= freq_repetida and (
        impacto >= impacto_primario or porcentaje >= porcentaje_primario
    ):
        return "Gasto Primario"

    # Monto bajo/medio frecuente que se acumula en el mes.
    if monto < monto_primario and frecuencia >= freq_alta and impacto >= impacto_recurrente:
        return "Gasto Hormiga Recurrente"

    if monto <= monto_bajo and frecuencia <= freq_baja and impacto <= impacto_recurrente:
        return "Gasto Hormiga Ocasional"

    if frecuencia >= freq_alta:
        return "Gasto Hormiga Recurrente"

    if impacto >= impacto_primario and monto >= monto_primario:
        return "Gasto Primario"

    return "Gasto Hormiga Ocasional"


def clasificar_patrones_avanzados(
    df: pd.DataFrame,
    presupuesto_total: float = DEFAULT_PRESUPUESTO_TOTAL,
) -> dict:
    """
    Clasifica patrones avanzados de consumo.

    Categorias:
    - Gasto Primario
    - Gasto Hormiga Ocasional
    - Gasto Hormiga Recurrente
    - Gasto Extraordinario
    """
    if df is None or df.empty:
        raise ValueError("El DataFrame no puede estar vacio")

    if "cluster" not in df.columns:
        raise ValueError("El DataFrame debe contener una columna 'cluster'")

    presupuesto = _safe_budget(presupuesto_total)
    base = preparar_features_avanzadas(df, presupuesto_total=presupuesto).copy()

    base["monto"] = pd.to_numeric(base["monto"], errors="coerce").fillna(0.0)
    base["frecuencia"] = pd.to_numeric(base["frecuencia"], errors="coerce").fillna(0.0)
    base["impactoMensual"] = pd.to_numeric(base["impactoMensual"], errors="coerce").fillna(0.0)
    base["porcentajePresupuesto"] = pd.to_numeric(base["porcentajePresupuesto"], errors="coerce").fillna(0.0)

    umbrales = {
        "monto_bajo": max(_threshold(base["monto"], 0.35), 8.0),
        "monto_primario": max(_threshold(base["monto"], 0.55), 12.0),
        "monto_extraordinario": max(_threshold(base["monto"], 0.80), 25.0),
        "freq_baja": min(max(_threshold(base["frecuencia"], 0.30), 1.0), 2.0),
        "freq_repetida": max(_threshold(base["frecuencia"], 0.50), 3.0),
        "freq_alta": max(_threshold(base["frecuencia"], 0.70), 4.0),
        "impacto_recurrente": max(_threshold(base["impactoMensual"], 0.45), 20.0),
        "impacto_primario": max(_threshold(base["impactoMensual"], 0.75), 60.0),
        "porcentaje_primario": max(_threshold(base["porcentajePresupuesto"], 0.75), 12.0),
    }

    base["categoria_patron"] = base.apply(_clasificar_fila_patron, axis=1, umbrales=umbrales)

    resumen_categorias = (
        base["categoria_patron"].value_counts(dropna=False).rename_axis("categoria").reset_index(name="cantidad")
    )

    resumen_cluster = (
        base.groupby(["cluster", "categoria_patron"], dropna=False)
        .size()
        .rename("cantidad")
        .reset_index()
        .sort_values(by=["cluster", "cantidad"], ascending=[True, False])
    )

    return {
        "df_clasificado": base,
        "resumen_categorias": resumen_categorias,
        "resumen_por_cluster": resumen_cluster,
        "umbrales": umbrales,
    }


def resumir_finanzas_avanzadas(
    df_clasificado: pd.DataFrame,
    presupuesto_total: float = DEFAULT_PRESUPUESTO_TOTAL,
) -> dict:
    """
    Resume el resultado financiero usando la categoria avanzada.
    """
    if df_clasificado is None or df_clasificado.empty:
        raise ValueError("El DataFrame clasificado no puede estar vacio")

    if "monto" not in df_clasificado.columns:
        raise ValueError("El DataFrame debe contener una columna 'monto'")

    if "categoria_patron" not in df_clasificado.columns:
        raise ValueError("El DataFrame debe contener una columna 'categoria_patron'")

    presupuesto = _safe_budget(presupuesto_total)

    monto = pd.to_numeric(df_clasificado["monto"], errors="coerce").fillna(0.0)
    categoria = df_clasificado["categoria_patron"].fillna("").astype(str)

    mask_hormiga = categoria.str.contains("Hormiga", case=False, na=False)
    mask_primario = categoria == "Gasto Primario"
    mask_extraordinario = categoria == "Gasto Extraordinario"

    total_gastado = float(monto.sum())
    gastos_hormiga = float(monto[mask_hormiga].sum())
    gastos_primarios = float(monto[mask_primario].sum())
    gastos_extraordinarios = float(monto[mask_extraordinario].sum())
    porcentaje_hormiga = float((gastos_hormiga / presupuesto) * 100.0) if presupuesto > 0 else 0.0

    return {
        "total_gastado": total_gastado,
        "gastos_hormiga": gastos_hormiga,
        "gastos_primarios": gastos_primarios,
        "gastos_extraordinarios": gastos_extraordinarios,
        "porcentaje_hormiga": porcentaje_hormiga,
    }
