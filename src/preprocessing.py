"""Funciones de preprocesamiento y vectorizacion para AntCluster."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = ("nombre", "monto", "fecha", "hora", "frecuencia")
VECTOR_COLUMNS = ("monto", "horaDecimal", "frecuencia")
ADVANCED_VECTOR_COLUMNS = ("monto", "horaDecimal", "frecuencia", "impactoMensual", "porcentajePresupuesto")


def _empty_expenses_df() -> pd.DataFrame:
    """DataFrame vacio con columnas minimas esperadas por la app."""
    return pd.DataFrame(columns=list(REQUIRED_COLUMNS))


def _read_csv_safe(ruta_entrada: str) -> pd.DataFrame:
    """Lee CSV de forma segura y devuelve DataFrame compatible aunque falle."""
    path = Path(ruta_entrada)
    if not path.exists() or path.stat().st_size == 0:
        return _empty_expenses_df()

    try:
        return pd.read_csv(path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
        return _empty_expenses_df()


def _ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura las columnas minimas para preprocesamiento."""
    normalized = df.copy()
    for col in REQUIRED_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = pd.NA
    return normalized


def calcularHoraDecimal(hora_valor: object) -> float:
    """
    Convierte hora a decimal.

    Soporta:
    - HH:MM
    - numerico (int/float)
    - string numerico
    Retorna NaN si el valor es invalido.
    """
    if pd.isna(hora_valor):
        return np.nan

    if isinstance(hora_valor, (int, float, np.number)):
        return float(hora_valor)

    texto = str(hora_valor).strip()
    if not texto:
        return np.nan

    if ":" in texto:
        try:
            hora_txt, min_txt = texto.split(":", maxsplit=1)
            hora_num = int(hora_txt)
            min_num = int(min_txt)
            if hora_num < 0 or hora_num > 23 or min_num < 0 or min_num > 59:
                return np.nan
            return round(hora_num + (min_num / 60.0), 2)
        except (ValueError, TypeError):
            return np.nan

    try:
        return float(texto)
    except ValueError:
        return np.nan


def calcular_frecuencia_mensual_oficial(df: pd.DataFrame) -> pd.Series:
    """
    Fuente oficial de frecuencia:
    - Si hay fecha valida: conteo por (nombre, mes).
    - Si falta fecha: usa frecuencia existente si es valida.
    - Si tampoco hay frecuencia valida: fallback controlado por conteo de nombre.
    """
    if df.empty:
        return pd.Series(dtype="float64")

    nombre = df["nombre"].fillna("").astype(str).str.strip()

    if "fecha" in df.columns:
        fechas = pd.to_datetime(df["fecha"], errors="coerce")
    else:
        fechas = pd.Series(pd.NaT, index=df.index)
    periodos = fechas.dt.to_period("M")

    frecuencia = pd.Series(np.nan, index=df.index, dtype="float64")
    valid_month = (nombre != "") & periodos.notna()

    if valid_month.any():
        month_counts = (
            pd.DataFrame({"nombre": nombre, "periodo": periodos}, index=df.index)
            .loc[valid_month]
            .groupby(["nombre", "periodo"])["nombre"]
            .transform("size")
            .astype(float)
        )
        frecuencia.loc[valid_month] = month_counts

    fallback_mask = frecuencia.isna() & (nombre != "")
    if fallback_mask.any():
        if "frecuencia" in df.columns:
            frecuencia_existente = pd.to_numeric(df["frecuencia"], errors="coerce")
            frecuencia.loc[fallback_mask] = frecuencia_existente.loc[fallback_mask]

    unresolved_mask = frecuencia.isna() & (nombre != "")
    if unresolved_mask.any():
        fallback_counts = nombre.loc[unresolved_mask].value_counts()
        frecuencia.loc[unresolved_mask] = (
            nombre.loc[unresolved_mask].map(fallback_counts).astype(float)
        )

    return frecuencia.fillna(0.0).astype(float)


def preparar_datos_para_modelo(df_gastos: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y normaliza datos para consumo de K-Means.

    Produce columnas estables:
    - monto (float)
    - horaDecimal (float, NaN si invalida)
    - frecuencia (float)
    """
    if df_gastos is None or df_gastos.empty:
        base = _empty_expenses_df()
        base["horaDecimal"] = pd.Series(dtype="float64")
        return base

    df = _ensure_required_columns(df_gastos)

    df["nombre"] = df["nombre"].fillna("").astype(str).str.strip()
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")

    # Priorizar horaDecimal existente; si no existe, usar hora.
    if "horaDecimal" in df.columns:
        hora_decimal = pd.to_numeric(df["horaDecimal"], errors="coerce")
    else:
        hora_decimal = pd.Series(np.nan, index=df.index, dtype="float64")

    hora_desde_texto = df["hora"].apply(calcularHoraDecimal)
    df["horaDecimal"] = hora_decimal.fillna(hora_desde_texto)

    # Fuente oficial de frecuencia para todo el sistema.
    df["frecuencia"] = calcular_frecuencia_mensual_oficial(df)

    return df


def calcular_frecuencia_mensual_csv(ruta_entrada: str, ruta_salida: str | None = None) -> pd.DataFrame:
    """
    Lee CSV y devuelve un DataFrame procesado sin romper ante datos incompletos.
    """
    df_gastos = _read_csv_safe(ruta_entrada)
    df_procesado = preparar_datos_para_modelo(df_gastos)

    if ruta_salida:
        Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
        df_procesado.to_csv(ruta_salida, index=False)

    return df_procesado


def vectorizarTransacciones(df_gastos: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve matriz [monto, horaDecimal, frecuencia] lista para K-Means.
    """
    if df_gastos is None or df_gastos.empty:
        return pd.DataFrame(columns=list(VECTOR_COLUMNS))

    df_procesado = preparar_datos_para_modelo(df_gastos)
    return df_procesado.loc[:, list(VECTOR_COLUMNS)].copy()


def preparar_features_avanzadas(
    df_gastos: pd.DataFrame,
    presupuesto_total: float = 200.0,
) -> pd.DataFrame:
    """
    Prepara features avanzadas para aprendizaje historico.

    Columnas garantizadas:
    - nombre
    - monto
    - hora
    - horaDecimal
    - frecuencia
    - impactoMensual
    - porcentajePresupuesto
    """
    df_base = preparar_datos_para_modelo(df_gastos)

    if "hora" not in df_base.columns:
        df_base["hora"] = pd.Series(dtype="object")

    if df_base.empty:
        empty_df = df_base.copy()
        empty_df["impactoMensual"] = pd.Series(dtype="float64")
        empty_df["porcentajePresupuesto"] = pd.Series(dtype="float64")
        return empty_df

    monto = pd.to_numeric(df_base["monto"], errors="coerce")
    frecuencia = pd.to_numeric(df_base["frecuencia"], errors="coerce")
    impacto_mensual = monto * frecuencia

    try:
        presupuesto = float(presupuesto_total)
    except (TypeError, ValueError):
        presupuesto = 200.0

    if not np.isfinite(presupuesto) or presupuesto <= 0:
        porcentaje = pd.Series(0.0, index=df_base.index, dtype="float64")
    else:
        porcentaje = ((impacto_mensual / presupuesto) * 100.0).fillna(0.0)

    df_base["impactoMensual"] = impacto_mensual
    df_base["porcentajePresupuesto"] = porcentaje.astype(float)
    return df_base
