"""Modelo de clustering para AntCluster."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


REQUIRED_ALIASES = {
    "monto": ("monto", "Monto"),
    "hora": ("horaDecimal", "hora_decimal", "hora", "Hora"),
    "frecuencia": ("frecuencia", "Frecuencia"),
}
DEFAULT_ADVANCED_COLUMNS = [
    "monto",
    "horaDecimal",
    "frecuencia",
    "impactoMensual",
    "porcentajePresupuesto",
]


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
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                return np.nan
            return round(hour + (minute / 60.0), 2)
        except (ValueError, TypeError):
            return np.nan

    try:
        return float(text)
    except ValueError:
        return np.nan


def _is_hour_column_name(column_name: str) -> bool:
    normalized = column_name.lower().replace("_", "")
    return normalized in {"hora", "horadecimal"}


def _coerce_feature_series(df: pd.DataFrame, column_name: str) -> pd.Series:
    if _is_hour_column_name(column_name):
        return df[column_name].apply(_hora_a_decimal)
    return pd.to_numeric(df[column_name], errors="coerce")


def _resolve_default_columns(df: pd.DataFrame) -> dict[str, str]:
    col_monto = _find_column(df, REQUIRED_ALIASES["monto"])
    col_hora = _find_column(df, REQUIRED_ALIASES["hora"])
    col_frecuencia = _find_column(df, REQUIRED_ALIASES["frecuencia"])

    if not all([col_monto, col_hora, col_frecuencia]):
        faltantes = []
        if col_monto is None:
            faltantes.append("monto")
        if col_hora is None:
            faltantes.append("hora")
        if col_frecuencia is None:
            faltantes.append("frecuencia")
        raise ValueError(f"Faltan columnas requeridas para K-Means: {', '.join(faltantes)}")

    return {"monto": col_monto, "hora": col_hora, "frecuencia": col_frecuencia}


def _prepare_feature_frame(
    df: pd.DataFrame,
    columnas_features: list[str] | tuple[str, ...] | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Construye el DataFrame de features numericas en orden estable.

    Si columnas_features es None, usa el contrato basico:
    [monto, hora, frecuencia] con aliases compatibles.
    """
    if columnas_features is None:
        resolved = _resolve_default_columns(df)
        features = pd.DataFrame(
            {
                "monto": _coerce_feature_series(df, resolved["monto"]),
                "hora": _coerce_feature_series(df, resolved["hora"]),
                "frecuencia": _coerce_feature_series(df, resolved["frecuencia"]),
            },
            index=df.index,
        )
        return features, ["monto", "hora", "frecuencia"]

    requested = list(columnas_features)
    if not requested:
        raise ValueError("columnas_features no puede ser una lista vacia.")

    missing = [col for col in requested if col not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas para K-Means: {', '.join(missing)}")

    data = {col: _coerce_feature_series(df, col) for col in requested}
    return pd.DataFrame(data, index=df.index), requested


def _fit_kmeans(
    x: np.ndarray,
    n_clusters: int,
    random_state: int = 42,
    usar_normalizacion: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    scaler = None
    x_model = x
    if usar_normalizacion:
        scaler = StandardScaler()
        x_model = scaler.fit_transform(x_model)

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = model.fit_predict(x_model)

    if scaler is not None:
        centroides = scaler.inverse_transform(model.cluster_centers_)
    else:
        centroides = model.cluster_centers_

    return labels, centroides


def evaluar_k_optimo(
    df: pd.DataFrame,
    k_min: int = 2,
    k_max: int = 5,
    random_state: int = 42,
    columnas_features: list[str] | tuple[str, ...] | None = None,
) -> tuple[int | None, pd.DataFrame, str | None]:
    """
    Evalua K optimo con Silhouette Score.

    Retorna:
    - mejor_k
    - tabla de scores (k, silhouette_score)
    - mensaje de control (None si todo salio bien)
    """
    if df is None:
        raise ValueError("El DataFrame no puede ser None.")

    columnas = list(columnas_features) if columnas_features is not None else None
    if columnas is None and all(col in df.columns for col in DEFAULT_ADVANCED_COLUMNS):
        columnas = DEFAULT_ADVANCED_COLUMNS

    features, columnas_usadas = _prepare_feature_frame(df, columnas_features=columnas)
    valid_features = features.dropna()
    n_samples = len(valid_features)

    if n_samples < 3:
        mensaje = "No hay suficientes datos validos para calcular Silhouette Score."
        return None, pd.DataFrame(columns=["k", "silhouette_score"]), mensaje

    k_min_sanitized = max(2, int(k_min))
    k_max_sanitized = int(k_max)
    k_upper = min(k_max_sanitized, n_samples - 1)

    if k_min_sanitized > k_upper:
        mensaje = "Rango de K invalido para la cantidad de muestras disponibles."
        return None, pd.DataFrame(columns=["k", "silhouette_score"]), mensaje

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(valid_features.to_numpy(dtype=float))

    records: list[dict[str, float]] = []
    for k in range(k_min_sanitized, k_upper + 1):
        model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = model.fit_predict(x_scaled)
        if len(np.unique(labels)) < 2:
            continue
        score = float(silhouette_score(x_scaled, labels))
        records.append({"k": float(k), "silhouette_score": score})

    if not records:
        mensaje = "No se pudo calcular Silhouette Score para ningun valor de K valido."
        return None, pd.DataFrame(columns=["k", "silhouette_score"]), mensaje

    score_df = pd.DataFrame(records)
    score_df["k"] = score_df["k"].astype(int)
    best_row = score_df.loc[score_df["silhouette_score"].idxmax()]
    mejor_k = int(best_row["k"])

    _ = columnas_usadas  # conserva el valor para depuracion sin alterar el contrato
    return mejor_k, score_df, None


def aplicar_kmeans(
    df: pd.DataFrame,
    n_clusters: int = 2,
    random_state: int = 42,
    auto_k: bool = False,
    k_min: int = 2,
    k_max: int = 5,
    usar_normalizacion: bool = False,
    columnas_features: list[str] | tuple[str, ...] | None = None,
) -> tuple[pd.DataFrame, np.ndarray | None, str | None]:
    """
    Aplica K-Means sobre un conjunto de features numericas.

    Compatibilidad garantizada:
    - Si se usa con los parametros historicos, mantiene el flujo original:
      aplicar_kmeans(df, n_clusters=2, random_state=42)

    Retorna:
    - DataFrame original con columna `cluster` asignada en filas validas.
    - Centroide(s) del modelo como matriz NumPy o None si no se entreno.
    - Mensaje de control (None si todo salio bien).
    """
    if df is None:
        raise ValueError("El DataFrame no puede ser None.")

    resultado = df.copy()
    resultado["cluster"] = pd.NA

    features, _ = _prepare_feature_frame(resultado, columnas_features=columnas_features)
    valid_mask = features.notna().all(axis=1)
    valid_features = features.loc[valid_mask]

    if auto_k:
        mejor_k, _, mensaje_k = evaluar_k_optimo(
            resultado,
            k_min=k_min,
            k_max=k_max,
            random_state=random_state,
            columnas_features=columnas_features,
        )
        if mejor_k is None:
            return resultado, None, mensaje_k
        n_clusters = mejor_k

    if len(valid_features) < n_clusters:
        mensaje = f"Se necesitan al menos {n_clusters} registros validos para aplicar K-Means."
        return resultado, None, mensaje

    x = valid_features.to_numpy(dtype=float)
    clusters, centroides = _fit_kmeans(
        x=x,
        n_clusters=n_clusters,
        random_state=random_state,
        usar_normalizacion=usar_normalizacion,
    )

    resultado.loc[valid_features.index, "cluster"] = clusters
    resultado["cluster"] = pd.to_numeric(resultado["cluster"], errors="coerce").astype("Int64")

    return resultado, centroides, None


def aplicar_kmeans_avanzado(
    df: pd.DataFrame,
    presupuesto_total: float = 200.0,
    k_min: int = 2,
    k_max: int = 5,
    random_state: int = 42,
) -> dict:
    """
    Ejecuta el flujo avanzado:
    - prepara features historicas
    - busca K optimo con silhouette
    - aplica K-Means con normalizacion
    """
    if df is None:
        raise ValueError("El DataFrame no puede ser None.")

    from src.preprocessing import preparar_features_avanzadas

    df_features = preparar_features_avanzadas(df, presupuesto_total=presupuesto_total)
    columnas = [col for col in DEFAULT_ADVANCED_COLUMNS if col in df_features.columns]

    if len(columnas) < 3:
        mensaje = "No hay suficientes columnas numericas para el modo avanzado."
        return {
            "df": df_features.assign(cluster=pd.Series(dtype="Int64")),
            "centroides": None,
            "mejor_k": None,
            "scores": pd.DataFrame(columns=["k", "silhouette_score"]),
            "columnas_features": columnas,
            "mensaje": mensaje,
        }

    mejor_k, scores, mensaje_k = evaluar_k_optimo(
        df_features,
        k_min=k_min,
        k_max=k_max,
        random_state=random_state,
        columnas_features=columnas,
    )

    if mejor_k is None:
        salida = df_features.copy()
        salida["cluster"] = pd.Series(pd.NA, index=salida.index, dtype="Int64")
        return {
            "df": salida,
            "centroides": None,
            "mejor_k": None,
            "scores": scores,
            "columnas_features": columnas,
            "mensaje": mensaje_k,
        }

    df_cluster, centroides, mensaje_modelo = aplicar_kmeans(
        df_features,
        n_clusters=mejor_k,
        random_state=random_state,
        usar_normalizacion=True,
        columnas_features=columnas,
    )

    return {
        "df": df_cluster,
        "centroides": centroides,
        "mejor_k": mejor_k,
        "scores": scores,
        "columnas_features": columnas,
        "mensaje": mensaje_modelo,
    }


def calcular_distancias_a_centroides(
    vector: list[float] | np.ndarray,
    centroides: np.ndarray,
) -> pd.DataFrame:
    """
    Calcula distancia euclidiana de un vector contra cada centroide.
    """
    if centroides is None:
        raise ValueError("centroides no puede ser None.")

    vector_np = np.asarray(vector, dtype=float).reshape(-1)
    centroides_np = np.asarray(centroides, dtype=float)

    if centroides_np.ndim != 2:
        raise ValueError("centroides debe ser una matriz de 2 dimensiones.")

    if centroides_np.shape[1] != vector_np.shape[0]:
        raise ValueError("Dimensiones incompatibles entre vector y centroides.")

    distances = np.linalg.norm(centroides_np - vector_np, axis=1)
    out = pd.DataFrame({"cluster": np.arange(len(distances)), "distancia": distances})
    return out.sort_values(by="distancia", ascending=True).reset_index(drop=True)
