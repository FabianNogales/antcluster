"""Funciones de preprocesamiento y vectorización para AntCluster."""

import os
import pandas as pd

def calcular_frecuencia_mensual_csv(ruta_entrada: str, ruta_salida: str = None) -> pd.DataFrame:
    if not os.path.exists(ruta_entrada):
        print(f"Error: El archivo en {ruta_entrada} no existe.")
        return None
        
    df_gastos = pd.read_csv(ruta_entrada)
    
    if df_gastos.empty:
        return df_gastos
    df_gastos['timestamp_temporal'] = pd.to_datetime(df_gastos['fecha'] + ' ' + df_gastos['hora'])
    
    fecha_maxima = df_gastos['timestamp_temporal'].max()
    
    agrupaciones = df_gastos.groupby('nombre').agg(
        total_compras=('timestamp_temporal', 'count'),
        primera_compra=('timestamp_temporal', 'min')
    ).reset_index()
    
    agrupaciones['dias_activos'] = (fecha_maxima - agrupaciones['primera_compra']).dt.days + 1
    
    agrupaciones['frecuencia_calculada'] = (agrupaciones['total_compras'] / agrupaciones['dias_activos']) * 30
    agrupaciones['frecuencia_calculada'] = agrupaciones['frecuencia_calculada'].round(2)
    
    diccionario_frecuencias = dict(zip(agrupaciones['nombre'], agrupaciones['frecuencia_calculada']))
    df_gastos['frecuencia'] = df_gastos['nombre'].map(diccionario_frecuencias)
    
    df_gastos = df_gastos.drop(columns=['timestamp_temporal'])
    if ruta_salida:
        df_gastos.to_csv(ruta_salida, index=False)
    return df_gastos

def calcularHoraDecimal(horaString):
    """
    Convierte una hora en formato 'HH:MM' a un valor numérico decimal.
    Ejemplo: '14:30' se convierte a 14.5.
    Si el formato es inválido, retorna 0.0 por seguridad.
    """
    if pd.isna(horaString) or not isinstance(horaString, str) or ':' not in horaString:
        return 0.0
    
    try:
        partesHora = horaString.split(':')
        horaReal = int(partesHora[0])
        minutosDecimales = int(partesHora[1]) / 60.0
        horaDecimal = horaReal + minutosDecimales
        return round(horaDecimal, 2)
    except (ValueError, IndexError):
        return 0.0

def vectorizarTransacciones(dfGastos):
    """
    Recibe un DataFrame de Pandas con los gastos crudos y devuelve la matriz
    tridimensional [Monto, Hora, Frecuencia] lista para el algoritmo K-Means.
    """
    if dfGastos.empty:
        return pd.DataFrame(columns=['monto', 'horaDecimal', 'frecuencia'])

    dfProcesado = dfGastos.copy()

    dfProcesado['monto'] = pd.to_numeric(dfProcesado['monto'], errors='coerce').fillna(0.0)
    dfProcesado['horaDecimal'] = dfProcesado['hora'].apply(calcularHoraDecimal)
    dfProcesado['frecuencia'] = pd.to_numeric(dfProcesado['frecuencia'], errors='coerce').fillna(0).astype(int)
    
    matrizVectores = dfProcesado[['monto', 'horaDecimal', 'frecuencia']]
    
    return matrizVectores

if __name__ == "__main__":
    ruta_demo = os.path.join("data", "gastos_demo.csv")
    ruta_usuario = os.path.join("data", "gastos_usuario.csv")

    df_demo_resultado = calcular_frecuencia_mensual_csv(ruta_demo, ruta_salida=ruta_demo)
    if df_demo_resultado is not None:
        print(df_demo_resultado[['id', 'nombre', 'monto', 'fecha', 'frecuencia']].to_string(index=False))
        print("\n--- MATRIZ VECTORIZADA ---")
        matriz_final = vectorizarTransacciones(df_demo_resultado)
        print(matriz_final.head())
        
    df_usuario_resultado = calcular_frecuencia_mensual_csv(ruta_usuario, ruta_salida=ruta_usuario)