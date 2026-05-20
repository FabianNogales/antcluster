# Descripcion de la beta

## Estado actual
La beta ya integra registro de gastos, persistencia en CSV, preprocesamiento robusto, clustering con K-Means (`K=2`) y clasificacion semantica de clusters.

## Flujo actual
1. Registro de gasto en `app.py`.
2. Guardado en `data/gastos_usuario.csv` mediante `src/utils.py`.
3. Preprocesamiento en `src/preprocessing.py`:
   - Limpieza de columnas.
   - Calculo de frecuencia mensual por nombre y mes.
   - Conversion de hora a `horaDecimal`.
4. Aplicacion de K-Means en `src/model.py` sobre `[monto, horaDecimal, frecuencia]`.
5. Clasificacion semantica en `src/classifier.py`:
   - Cluster de menor monto promedio -> Gasto Hormiga.
   - Cluster de mayor monto promedio -> Gasto Primario.
6. Visualizacion de resumen y tabla clasificada en Streamlit.

## Alcance de esta etapa
- Robustecer validaciones de datos sin cambiar el objetivo del proyecto.
- Mantener el contrato del modelo `aplicar_kmeans(df, n_clusters=2, random_state=42)`.
- Mejorar pruebas y documentacion para mantenimiento academico.