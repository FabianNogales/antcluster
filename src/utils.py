"""Utilidades para gestionar los datos CSV de AntCluster."""

from datetime import date, datetime, time
from pathlib import Path

import pandas as pd


OFFICIAL_COLUMNS = ["id", "nombre", "monto", "fecha", "hora", "frecuencia"]
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
USER_CSV = DATA_DIR / "gastos_usuario.csv"
DEMO_CSV = DATA_DIR / "gastos_demo.csv"

DEMO_DATA = [
    {"id": 1, "nombre": "Pasaje", "monto": 3.0, "fecha": "2026-05-01", "hora": "07:30", "frecuencia": 2},
    {"id": 2, "nombre": "Pasaje", "monto": 3.0, "fecha": "2026-05-02", "hora": "07:35", "frecuencia": 2},
    {"id": 3, "nombre": "Almuerzo", "monto": 15.0, "fecha": "2026-05-02", "hora": "12:30", "frecuencia": 2},
    {"id": 4, "nombre": "Almuerzo", "monto": 15.0, "fecha": "2026-05-03", "hora": "12:45", "frecuencia": 2},
    {"id": 5, "nombre": "Cafe", "monto": 5.0, "fecha": "2026-05-03", "hora": "16:00", "frecuencia": 2},
    {"id": 6, "nombre": "Cafe", "monto": 5.0, "fecha": "2026-05-04", "hora": "16:20", "frecuencia": 2},
    {"id": 7, "nombre": "Snack", "monto": 6.0, "fecha": "2026-05-05", "hora": "17:30", "frecuencia": 1},
    {"id": 8, "nombre": "Dulces", "monto": 2.0, "fecha": "2026-05-06", "hora": "18:00", "frecuencia": 1},
    {"id": 9, "nombre": "Fotocopias", "monto": 2.0, "fecha": "2026-05-06", "hora": "10:00", "frecuencia": 1},
    {"id": 10, "nombre": "Recarga", "monto": 10.0, "fecha": "2026-05-07", "hora": "19:00", "frecuencia": 1},
]


def ensure_data_folder() -> None:
    """Crea la carpeta data si no existe."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _empty_expenses_df() -> pd.DataFrame:
    return pd.DataFrame(columns=OFFICIAL_COLUMNS)


def _normalize_expenses_df(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza columnas oficiales, tipos basicos y orden estable."""
    if df.empty:
        return _empty_expenses_df()

    normalized = df.copy()
    for column in OFFICIAL_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = pd.NA

    normalized = normalized[OFFICIAL_COLUMNS]
    normalized["nombre"] = normalized["nombre"].fillna("").astype(str).str.strip()
    normalized["monto"] = pd.to_numeric(normalized["monto"], errors="coerce").fillna(0.0)
    normalized["id"] = pd.to_numeric(normalized["id"], errors="coerce")
    normalized["fecha"] = normalized["fecha"].fillna("").astype(str)
    normalized["hora"] = normalized["hora"].fillna("").astype(str)
    normalized["frecuencia"] = pd.to_numeric(normalized["frecuencia"], errors="coerce").fillna(0).astype(int)

    return normalized


def _read_csv(path: Path) -> pd.DataFrame:
    """Lee un CSV y devuelve un DataFrame compatible aunque este vacio."""
    ensure_data_folder()

    if not path.exists() or path.stat().st_size == 0:
        return _empty_expenses_df()

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return _empty_expenses_df()

    return _normalize_expenses_df(df)


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    ensure_data_folder()
    normalized = _normalize_expenses_df(df)
    normalized.to_csv(path, index=False)


def _get_next_id(df: pd.DataFrame) -> int:
    if df.empty:
        return 1

    ids = pd.to_numeric(df["id"], errors="coerce").dropna()
    return 1 if ids.empty else int(ids.max()) + 1


def _format_date(value: str | date | datetime | None) -> str:
    if value is None:
        return datetime.now().strftime("%Y-%m-%d")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return datetime.strptime(str(value), "%Y-%m-%d").strftime("%Y-%m-%d")


def _format_time(value: str | time | datetime | None) -> str:
    if value is None:
        return datetime.now().strftime("%H:%M")
    if isinstance(value, datetime):
        return value.strftime("%H:%M")
    if isinstance(value, time):
        return value.strftime("%H:%M")
    return datetime.strptime(str(value), "%H:%M").strftime("%H:%M")


def create_user_csv_if_not_exists() -> None:
    """Crea data/gastos_usuario.csv con encabezados si no existe."""
    ensure_data_folder()

    if not USER_CSV.exists() or USER_CSV.stat().st_size == 0:
        _empty_expenses_df().to_csv(USER_CSV, index=False)
        return

    df = _read_csv(USER_CSV)
    _write_csv(df, USER_CSV)


def create_demo_csv_if_not_exists() -> None:
    """Crea data/gastos_demo.csv con datos de ejemplo si falta o esta vacio."""
    ensure_data_folder()

    if not DEMO_CSV.exists() or DEMO_CSV.stat().st_size == 0:
        demo_df = pd.DataFrame(DEMO_DATA, columns=OFFICIAL_COLUMNS)
        _write_csv(demo_df, DEMO_CSV)
        return

    df = _read_csv(DEMO_CSV)
    if df.empty:
        df = pd.DataFrame(DEMO_DATA, columns=OFFICIAL_COLUMNS)
    _write_csv(recalculate_frequencies(df), DEMO_CSV)


def initialize_data_files() -> None:
    """Prepara la carpeta data y los CSV requeridos por la app."""
    ensure_data_folder()
    create_user_csv_if_not_exists()
    create_demo_csv_if_not_exists()


def read_expenses() -> pd.DataFrame:
    """Lee los gastos del usuario desde data/gastos_usuario.csv."""
    create_user_csv_if_not_exists()
    df = _read_csv(USER_CSV)
    return recalculate_frequencies(df)


def recalculate_frequencies(df: pd.DataFrame) -> pd.DataFrame:
    """Actualiza frecuencia contando repeticiones del mismo nombre."""
    normalized = _normalize_expenses_df(df)
    if normalized.empty:
        return normalized

    counts = normalized["nombre"].value_counts()
    normalized["frecuencia"] = normalized["nombre"].map(counts).fillna(0).astype(int)
    return normalized


def save_expense(
    nombre: str,
    monto: float,
    fecha: str | date | datetime | None = None,
    hora: str | time | datetime | None = None,
) -> pd.DataFrame:
    """Guarda un gasto inmediatamente en el CSV de usuario."""
    clean_name = nombre.strip()
    if not clean_name:
        raise ValueError("El nombre del gasto no puede estar vacio.")

    amount = float(monto)
    if amount <= 0:
        raise ValueError("El monto debe ser mayor a 0.")

    expense_date = _format_date(fecha)
    expense_hour = _format_time(hora)

    df = read_expenses()
    next_id = _get_next_id(df)
    new_expense = pd.DataFrame(
        [
            {
                "id": next_id,
                "nombre": clean_name,
                "monto": amount,
                "fecha": expense_date,
                "hora": expense_hour,
                "frecuencia": 1,
            }
        ],
        columns=OFFICIAL_COLUMNS,
    )

    updated_df = pd.concat([df, new_expense], ignore_index=True)
    updated_df = recalculate_frequencies(updated_df)
    _write_csv(updated_df, USER_CSV)
    return updated_df


def reset_user_data() -> None:
    """Reinicia el CSV de usuario, manteniendo solo los encabezados."""
    ensure_data_folder()
    _empty_expenses_df().to_csv(USER_CSV, index=False)


def load_demo_data() -> pd.DataFrame:
    """Copia los datos demo hacia el CSV de usuario."""
    create_demo_csv_if_not_exists()
    demo_df = recalculate_frequencies(_read_csv(DEMO_CSV))
    _write_csv(demo_df, USER_CSV)
    return demo_df


def get_expenses_summary() -> dict[str, float | int]:
    """Calcula metricas basicas de los gastos guardados."""
    df = read_expenses()
    total_expenses = int(len(df))
    total_amount = float(df["monto"].sum()) if not df.empty else 0.0
    average_amount = float(df["monto"].mean()) if not df.empty else 0.0

    return {
        "cantidad_gastos": total_expenses,
        "total_gastado": total_amount,
        "promedio_gasto": average_amount,
    }


def get_user_csv_bytes() -> bytes:
    """Devuelve el CSV de usuario en bytes para st.download_button."""
    create_user_csv_if_not_exists()
    return USER_CSV.read_bytes()
