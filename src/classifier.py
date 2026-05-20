"""Clasificacion semantica de clusters para AntCluster."""

import pandas as pd


def clasificar_y_resumir(df_gastos: pd.DataFrame, presupuesto_total: float) -> dict:
    """
    Clasifica gastos en "Gasto Hormiga" y "Gasto Primario" basándose en el cluster.
    
    El cluster con promedio de monto más bajo es clasificado como "Gasto Hormiga",
    y el otro como "Gasto Primario".
    
    Parámetros:
    -----------
    df_gastos : pd.DataFrame
        DataFrame con columnas requeridas:
        - 'monto': Monto del gasto (float)
        - 'cluster': Cluster asignado (int, 0 o 1)
    presupuesto_total : float
        Presupuesto total disponible para calcular porcentajes.
    
    Retorna:
    --------
    dict
        Diccionario con los resultados del análisis:
        - 'total_gastado': Total de todos los gastos
        - 'gastos_hormiga': Total de gastos hormiga
        - 'gastos_primarios': Total de gastos primarios
        - 'cantidad_hormiga': Cantidad de registros en hormiga
        - 'porcentaje_hormiga': Porcentaje del presupuesto en gastos hormiga
        - 'cluster_hormiga': Número del cluster identificado como hormiga
        - 'cluster_primario': Número del cluster identificado como primario
    
    Raises:
    -------
    ValueError
        Si el DataFrame está vacío o falta alguna columna requerida.
    """
    if df_gastos.empty:
        raise ValueError("El DataFrame no puede estar vacío")
    
    if "cluster" not in df_gastos.columns:
        raise ValueError("El DataFrame debe contener una columna 'cluster'")
    
    if "monto" not in df_gastos.columns:
        raise ValueError("El DataFrame debe contener una columna 'monto'")
    
    # Calcular promedio de monto por cluster
    promedios = df_gastos.groupby("cluster")["monto"].mean()
    
    # Identificar dinámicamente: cluster con menor promedio = Hormiga
    cluster_hormiga = promedios.idxmin()
    cluster_primario = promedios.idxmax()
    
    # Filtrar gastos por tipo
    gastos_hormiga = df_gastos[df_gastos["cluster"] == cluster_hormiga]
    gastos_primarios = df_gastos[df_gastos["cluster"] == cluster_primario]
    
    # Calcular totales
    total_hormiga = gastos_hormiga["monto"].sum()
    total_primario = gastos_primarios["monto"].sum()
    total_gastado = total_hormiga + total_primario
    
    # Calcular cantidad de gastos hormiga
    cantidad_hormiga = len(gastos_hormiga)
    
    # Calcular porcentaje respecto al presupuesto total
    porcentaje_hormiga = (total_hormiga / presupuesto_total * 100) if presupuesto_total > 0 else 0
    
    # Imprimir resultados en formato especificado
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
