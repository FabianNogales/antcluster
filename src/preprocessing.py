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


if __name__ == "__main__":
    ruta_demo = os.path.join("data", "gastos_demo.csv")
    ruta_usuario = os.path.join("data", "gastos_usuario.csv")

    df_demo_resultado = calcular_frecuencia_mensual_csv(ruta_demo, ruta_salida=ruta_demo)
    if df_demo_resultado is not None:
        print(df_demo_resultado[['id', 'nombre', 'monto', 'fecha', 'frecuencia']].to_string(index=False))
    df_usuario_resultado = calcular_frecuencia_mensual_csv(ruta_usuario, ruta_salida=ruta_usuario)