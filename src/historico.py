"""Persistencia y uso de aprendizaje historico para AntCluster."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.classifier import clasificar_patrones_avanzados, resumir_finanzas_avanzadas
from src.model import aplicar_kmeans_avanzado, calcular_distancias_a_centroides
from src.preprocessing import (
    DEFAULT_PRESUPUESTO_TOTAL,
    calcularHoraDecimal,
    normalizar_presupuesto_total,
)
from src.utils import DATA_DIR, OFFICIAL_COLUMNS, recalculate_frequencies

HISTORICO_CSV = DATA_DIR / "gastos_historicos.csv"
MODELO_HISTORICO_JSON = DATA_DIR / "modelo_historico.json"


def _empty_historico_df() -> pd.DataFrame:
    return pd.DataFrame(columns=OFFICIAL_COLUMNS)


def _modelo_no_entrenado() -> dict[str, Any]:
    return {
        "entrenado": False,
        "fecha_entrenamiento": None,
        "cantidad_registros": 0,
        "presupuesto_total": None,
        "columnas_features": [],
        "mejor_k": None,
        "scores_silhouette": [],
        "centroides": [],
        "categorias_por_cluster": {},
        "resumen_entrenamiento": {"mensaje": "Modelo historico no entrenado."},
    }


def _coerce_historico_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return _empty_historico_df()

    normalized = df.copy()
    for col in OFFICIAL_COLUMNS:
        if col not in normalized.columns:
            normalized[col] = pd.NA

    normalized = normalized[OFFICIAL_COLUMNS]
    normalized["id"] = pd.to_numeric(normalized["id"], errors="coerce")
    normalized["nombre"] = normalized["nombre"].fillna("").astype(str).str.strip()
    normalized["monto"] = pd.to_numeric(normalized["monto"], errors="coerce")
    normalized["fecha"] = normalized["fecha"].fillna("").astype(str)
    normalized["hora"] = normalized["hora"].fillna("").astype(str)
    normalized["frecuencia"] = pd.to_numeric(normalized["frecuencia"], errors="coerce")
    normalized = recalculate_frequencies(normalized)
    return normalized


def _crear_dataset_historico_demo() -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    idx = 1

    for month in (3, 4, 5):
        prefix = f"2026-{month:02d}"

        def add_rows(nombre: str, monto: float, day_hours: list[tuple[int, str]]) -> None:
            nonlocal idx
            for day, hora in day_hours:
                records.append(
                    {
                        "id": idx,
                        "nombre": nombre,
                        "monto": monto,
                        "fecha": f"{prefix}-{day:02d}",
                        "hora": hora,
                        "frecuencia": 1,
                    }
                )
                idx += 1

        add_rows("Almuerzo", 18.0, [(2, "12:30"), (5, "12:45"), (9, "12:55"), (13, "13:00")])
        add_rows("Cena", 20.0, [(2, "20:15"), (6, "20:35"), (10, "20:45"), (14, "21:00")])
        add_rows(
            "Transporte",
            3.0,
            [(2, "07:20"), (2, "18:10"), (5, "07:25"), (5, "18:15"), (9, "07:30"), (9, "18:20"), (13, "07:35"), (13, "18:25")],
        )
        add_rows("Cafe", 5.0, [(3, "10:10"), (5, "10:25"), (7, "16:20"), (9, "10:30"), (11, "16:25"), (13, "10:40")])
        add_rows("Snack", 5.0, [(4, "16:45"), (8, "16:55"), (12, "17:05")])
        add_rows("Dulces", 4.0, [(6, "15:30"), (10, "15:45")])
        add_rows("Refresco", 7.0, [(7, "16:10"), (12, "16:20")])
        add_rows("Agua", 1.0, [(3, "09:30"), (11, "09:40")])
        add_rows("Taxi", 35.0, [(15, "22:00")])
        add_rows("Cine", 30.0, [(16, "19:30")])

    return recalculate_frequencies(pd.DataFrame(records, columns=OFFICIAL_COLUMNS))


def inicializar_archivos_historicos() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not HISTORICO_CSV.exists() or HISTORICO_CSV.stat().st_size == 0:
        demo = _crear_dataset_historico_demo()
        demo.to_csv(HISTORICO_CSV, index=False)

    if not MODELO_HISTORICO_JSON.exists() or MODELO_HISTORICO_JSON.stat().st_size == 0:
        guardar_modelo_historico(_modelo_no_entrenado())


def cargar_gastos_historicos() -> pd.DataFrame:
    inicializar_archivos_historicos()
    try:
        df = pd.read_csv(HISTORICO_CSV)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError):
        return _empty_historico_df()
    return _coerce_historico_df(df)


def guardar_gastos_historicos(df: pd.DataFrame) -> None:
    inicializar_archivos_historicos()
    coerced = _coerce_historico_df(df)
    coerced.to_csv(HISTORICO_CSV, index=False)


def entrenar_agente_historico(
    df_historico: pd.DataFrame,
    presupuesto_total: float = DEFAULT_PRESUPUESTO_TOTAL,
) -> dict[str, Any]:
    if df_historico is None or df_historico.empty:
        modelo = _modelo_no_entrenado()
        modelo["resumen_entrenamiento"] = {"mensaje": "No hay datos historicos para entrenar."}
        return modelo

    presupuesto = normalizar_presupuesto_total(
        presupuesto_total,
        fallback=DEFAULT_PRESUPUESTO_TOTAL,
        allow_non_positive=True,
    )
    df_base = _coerce_historico_df(df_historico)
    out = aplicar_kmeans_avanzado(df_base, presupuesto_total=presupuesto, random_state=42)

    df_cluster = out.get("df", pd.DataFrame())
    centroides = out.get("centroides")
    mejor_k = out.get("mejor_k")
    scores_df = out.get("scores", pd.DataFrame(columns=["k", "silhouette_score"]))
    columnas_features = out.get("columnas_features", [])
    mensaje = out.get("mensaje")

    modelo: dict[str, Any] = {
        "entrenado": False,
        "fecha_entrenamiento": datetime.now().isoformat(timespec="seconds"),
        "cantidad_registros": int(len(df_base)),
        "presupuesto_total": float(presupuesto),
        "columnas_features": list(columnas_features),
        "mejor_k": int(mejor_k) if mejor_k is not None else None,
        "scores_silhouette": [],
        "centroides": [],
        "categorias_por_cluster": {},
        "resumen_entrenamiento": {"mensaje": mensaje or "Entrenamiento incompleto."},
    }

    if not scores_df.empty:
        modelo["scores_silhouette"] = [
            {"k": int(row["k"]), "silhouette_score": float(row["silhouette_score"])}
            for _, row in scores_df.iterrows()
        ]

    if centroides is None or df_cluster.empty:
        return modelo

    centroides_np = np.asarray(centroides, dtype=float)
    modelo["centroides"] = centroides_np.tolist()

    clasificado = clasificar_patrones_avanzados(df_cluster, presupuesto_total=presupuesto)
    df_clasificado = clasificado["df_clasificado"]
    resumen = resumir_finanzas_avanzadas(df_clasificado, presupuesto_total=presupuesto)

    categorias_por_cluster: dict[str, str] = {}
    grouped = (
        df_clasificado.groupby(["cluster", "categoria_patron"], dropna=False)
        .size()
        .rename("cantidad")
        .reset_index()
        .sort_values(by=["cluster", "cantidad"], ascending=[True, False])
    )
    for cluster in grouped["cluster"].dropna().unique():
        top_row = grouped[grouped["cluster"] == cluster].iloc[0]
        categorias_por_cluster[str(int(cluster))] = str(top_row["categoria_patron"])

    modelo["categorias_por_cluster"] = categorias_por_cluster
    modelo["resumen_entrenamiento"] = {
        **resumen,
        "resumen_categorias": clasificado["resumen_categorias"].to_dict(orient="records"),
        "mensaje": "Entrenamiento historico exitoso.",
    }
    modelo["entrenado"] = True
    return modelo


def guardar_modelo_historico(modelo_dict: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with MODELO_HISTORICO_JSON.open("w", encoding="utf-8") as fp:
        json.dump(modelo_dict, fp, ensure_ascii=False, indent=2)


def cargar_modelo_historico() -> dict[str, Any]:
    inicializar_archivos_historicos()
    if not MODELO_HISTORICO_JSON.exists() or MODELO_HISTORICO_JSON.stat().st_size == 0:
        return _modelo_no_entrenado()

    try:
        with MODELO_HISTORICO_JSON.open("r", encoding="utf-8") as fp:
            loaded = json.load(fp)
    except (json.JSONDecodeError, OSError):
        return _modelo_no_entrenado()

    if not isinstance(loaded, dict):
        return _modelo_no_entrenado()

    base = _modelo_no_entrenado()
    base.update(loaded)
    return base


def clasificar_gasto_con_modelo_historico(
    gasto: dict[str, Any],
    modelo_historico: dict[str, Any],
    presupuesto_total: float = DEFAULT_PRESUPUESTO_TOTAL,
) -> dict[str, Any]:
    if not modelo_historico or not modelo_historico.get("centroides"):
        raise ValueError("No hay centroides historicos disponibles. Entrena el modelo primero.")

    centroides = np.asarray(modelo_historico["centroides"], dtype=float)
    columnas = list(modelo_historico.get("columnas_features") or [])
    if not columnas:
        raise ValueError("El modelo historico no tiene columnas de features.")

    now = datetime.now()
    nombre = str(gasto.get("nombre", "Gasto nuevo")).strip() or "Gasto nuevo"
    monto = float(gasto.get("monto", 0.0))
    if monto <= 0:
        raise ValueError("El monto del nuevo gasto debe ser mayor a 0.")

    fecha = str(gasto.get("fecha", now.strftime("%Y-%m-%d")))
    hora = str(gasto.get("hora", now.strftime("%H:%M")))
    _ = fecha  # mantiene compatibilidad de firma sin recalcular frecuencia mensual en fila unica.

    frecuencia_raw = gasto.get("frecuencia", None)
    try:
        frecuencia = float(frecuencia_raw) if frecuencia_raw is not None else 1.0
    except (TypeError, ValueError):
        frecuencia = 1.0
    if not np.isfinite(frecuencia) or frecuencia <= 0:
        frecuencia = 1.0

    hora_decimal = calcularHoraDecimal(hora)
    if pd.isna(hora_decimal):
        raise ValueError("La hora del nuevo gasto no es valida. Usa formato HH:MM.")

    impacto_mensual = float(monto * frecuencia)
    presupuesto = normalizar_presupuesto_total(
        presupuesto_total,
        fallback=DEFAULT_PRESUPUESTO_TOTAL,
        allow_non_positive=True,
    )
    presupuesto_modelo_raw = modelo_historico.get("presupuesto_total", None)
    try:
        presupuesto_modelo = float(presupuesto_modelo_raw) if presupuesto_modelo_raw is not None else None
    except (TypeError, ValueError):
        presupuesto_modelo = None
    if not np.isfinite(presupuesto) or presupuesto <= 0:
        porcentaje_presupuesto = 0.0
    else:
        porcentaje_presupuesto = float((impacto_mensual / presupuesto) * 100.0)

    feature_map = {
        "monto": float(monto),
        "horaDecimal": float(hora_decimal),
        "frecuencia": float(frecuencia),
        "impactoMensual": float(impacto_mensual),
        "porcentajePresupuesto": float(porcentaje_presupuesto),
    }

    missing = [col for col in columnas if col not in feature_map]
    if missing:
        raise ValueError(f"El modelo historico requiere columnas no soportadas: {', '.join(missing)}")

    vector = [float(feature_map[col]) for col in columnas]
    distancias_df = calcular_distancias_a_centroides(vector, centroides)
    cluster_asignado = int(distancias_df.iloc[0]["cluster"])

    categorias = modelo_historico.get("categorias_por_cluster", {})
    categoria = categorias.get(str(cluster_asignado), "Categoria historica no definida")
    dist_min = float(distancias_df.iloc[0]["distancia"])

    explicacion = (
        f"El gasto '{nombre}' fue proyectado al vector avanzado y comparado contra centroides "
        f"historicos. Se asigno al cluster {cluster_asignado} por menor distancia euclidiana "
        f"({dist_min:.4f}). Categoria estimada: {categoria}. "
        f"Presupuesto usado para clasificar: {presupuesto:.2f} Bs."
    )
    if presupuesto_modelo is not None:
        explicacion = (
            f"{explicacion} Presupuesto registrado en entrenamiento historico: "
            f"{presupuesto_modelo:.2f} Bs."
        )

    return {
        "vector_generado": {col: float(feature_map[col]) for col in columnas},
        "cluster_asignado": cluster_asignado,
        "distancias_centroides": distancias_df.to_dict(orient="records"),
        "categoria_interpretada": categoria,
        "presupuesto_clasificacion": float(presupuesto),
        "presupuesto_modelo_entrenado": presupuesto_modelo,
        "explicacion": explicacion,
    }
