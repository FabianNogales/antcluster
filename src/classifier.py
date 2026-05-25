"""Clasificacion semantica de clusters para AntCluster."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.preprocessing import preparar_features_avanzadas


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

    print(f"Total gastado: {total_gastado:.0f} Bs")
    print(f"Gastos hormiga: {total_hormiga:.0f} Bs")
    print(f"Gastos primarios: {total_primario:.0f} Bs")
    print(f"Porcentaje en gastos hormiga: {porcentaje_hormiga:.1f}%")

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
    try:
        presupuesto = float(presupuesto_total)
    except (TypeError, ValueError):
        return 200.0
    if not np.isfinite(presupuesto) or presupuesto <= 0:
        return 200.0
    return presupuesto


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
    monto_alto = umbrales["monto_alto"]
    freq_baja = umbrales["freq_baja"]
    freq_alta = umbrales["freq_alta"]
    impacto_bajo = umbrales["impacto_bajo"]
    impacto_alto = umbrales["impacto_alto"]
    porcentaje_alto = umbrales["porcentaje_alto"]

    if monto >= monto_alto and frecuencia <= freq_baja:
        return "Gasto Extraordinario"

    if frecuencia >= freq_alta and (impacto >= impacto_bajo or porcentaje >= (porcentaje_alto * 0.6)):
        return "Gasto Hormiga Recurrente"

    if impacto >= impacto_alto or porcentaje >= porcentaje_alto:
        return "Gasto Primario"

    if monto <= monto_bajo and frecuencia <= freq_baja and impacto <= impacto_bajo:
        return "Gasto Hormiga Ocasional"

    if frecuencia >= freq_alta:
        return "Gasto Hormiga Recurrente"

    if impacto >= impacto_alto:
        return "Gasto Primario"

    return "Gasto Hormiga Ocasional"


def clasificar_patrones_avanzados(
    df: pd.DataFrame,
    presupuesto_total: float = 200.0,
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
        "monto_bajo": _threshold(base["monto"], 0.40),
        "monto_alto": _threshold(base["monto"], 0.75),
        "freq_baja": _threshold(base["frecuencia"], 0.35),
        "freq_alta": _threshold(base["frecuencia"], 0.70),
        "impacto_bajo": _threshold(base["impactoMensual"], 0.35),
        "impacto_alto": _threshold(base["impactoMensual"], 0.75),
        "porcentaje_alto": max(_threshold(base["porcentajePresupuesto"], 0.75), 5.0),
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
