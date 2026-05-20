"""Funciones de preprocesamiento y vectorizacion para AntCluster."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = ("nombre", "monto", "fecha", "hora", "frecuencia")
VECTOR_COLUMNS = ("monto", "horaDecimal", "frecuencia")


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


def _calcular_frecuencia_mensual(df: pd.DataFrame) -> pd.Series:
    """
    Calcula frecuencia mensual por nombre y mes.

    Si no se puede calcular para una fila (nombre/fecha invalidos), se usa 0.
    """
    if df.empty:
        return pd.Series(dtype="float64")

    nombre = df["nombre"].fillna("").astype(str).str.strip()
    fechas = pd.to_datetime(df["fecha"], errors="coerce")
    periodos = fechas.dt.to_period("M")

    freq_df = pd.DataFrame({"nombre": nombre, "periodo": periodos})
    valid_mask = (freq_df["nombre"] != "") & freq_df["periodo"].notna()

    if not valid_mask.any():
        return pd.Series(0.0, index=df.index, dtype="float64")

    conteos = (
        freq_df.loc[valid_mask]
        .groupby(["nombre", "periodo"], dropna=False)
        .size()
        .rename("frecuencia_calculada")
        .reset_index()
    )

    merged = freq_df.merge(conteos, on=["nombre", "periodo"], how="left")
    return merged["frecuencia_calculada"].fillna(0).astype(float)


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

    # Si no hay frecuencia o viene invalida, se calcula por nombre y mes.
    frecuencia_existente = pd.to_numeric(df["frecuencia"], errors="coerce")
    frecuencia_calculada = _calcular_frecuencia_mensual(df)
    df["frecuencia"] = frecuencia_existente.fillna(frecuencia_calculada)
    df["frecuencia"] = df["frecuencia"].fillna(0).astype(float)

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
