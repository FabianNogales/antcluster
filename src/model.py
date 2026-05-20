"""Modelo de clustering para AntCluster."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


REQUIRED_ALIASES = {
    "monto": ("monto", "Monto"),
    "hora": ("hora", "horaDecimal", "hora_decimal", "Hora"),
    "frecuencia": ("frecuencia", "Frecuencia"),
}


def _find_column(df: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    """Busca la primera columna existente dentro de una lista de alias."""
    for alias in aliases:
        if alias in df.columns:
            return alias
    return None


def _hora_a_decimal(value: object) -> float:
    """
    Convierte hora a decimal.

    Acepta:
    - Numeros (ej. 14.5)
    - Texto HH:MM (ej. 14:30 -> 14.5)
    - Texto numerico (ej. "14.5")
    """
    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()
    if not text:
        return np.nan

    if ":" in text:
        try:
            hour_text, minute_text = text.split(":", maxsplit=1)
            hour = int(hour_text)
            minute = int(minute_text)
            return round(hour + (minute / 60.0), 2)
        except (ValueError, TypeError):
            return np.nan

    try:
        return float(text)
    except ValueError:
        return np.nan


def aplicar_kmeans(
    df: pd.DataFrame,
    n_clusters: int = 2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, np.ndarray | None, str | None]:
    """
    Aplica K-Means sobre la matriz [monto, hora, frecuencia].

    Parametros:
    - df: DataFrame con columnas de monto, hora y frecuencia (o alias compatibles).
    - n_clusters: cantidad de clusters (por defecto 2 para la beta).
    - random_state: semilla fija para resultados reproducibles.

    Devuelve:
    - DataFrame original con columna `cluster` asignada en filas validas.
    - Centroide(s) del modelo como matriz NumPy o None si no se entreno.
    - Mensaje de control (None si todo salio bien).
    """
    if df is None:
        raise ValueError("El DataFrame no puede ser None.")

    resultado = df.copy()
    resultado["cluster"] = pd.NA

    col_monto = _find_column(resultado, REQUIRED_ALIASES["monto"])
    col_hora = _find_column(resultado, REQUIRED_ALIASES["hora"])
    col_frecuencia = _find_column(resultado, REQUIRED_ALIASES["frecuencia"])

    if not all([col_monto, col_hora, col_frecuencia]):
        faltantes = []
        if col_monto is None:
            faltantes.append("monto")
        if col_hora is None:
            faltantes.append("hora")
        if col_frecuencia is None:
            faltantes.append("frecuencia")
        raise ValueError(f"Faltan columnas requeridas para K-Means: {', '.join(faltantes)}")

    # Se construye la matriz X en el orden [monto, hora, frecuencia].
    features = pd.DataFrame(
        {
            "monto": pd.to_numeric(resultado[col_monto], errors="coerce"),
            "hora": resultado[col_hora].apply(_hora_a_decimal),
            "frecuencia": pd.to_numeric(resultado[col_frecuencia], errors="coerce"),
        },
        index=resultado.index,
    )

    valid_mask = features.notna().all(axis=1)
    valid_features = features.loc[valid_mask, ["monto", "hora", "frecuencia"]]

    if len(valid_features) < n_clusters:
        mensaje = (
            "Se necesitan al menos 2 registros validos para aplicar K-Means con K=2."
        )
        return resultado, None, mensaje

    x = valid_features.to_numpy(dtype=float)

    # Se entrena K-Means con K=2 y semilla fija para reproducibilidad.
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    clusters = kmeans.fit_predict(x)

    # Se asigna el cluster solo a filas que participaron en el entrenamiento.
    resultado.loc[valid_features.index, "cluster"] = clusters
    resultado["cluster"] = pd.to_numeric(resultado["cluster"], errors="coerce").astype("Int64")

    return resultado, kmeans.cluster_centers_, None
