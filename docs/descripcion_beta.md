# Descripcion de la beta

## Estado actual
La beta integra registro de gastos, persistencia en CSV, preprocesamiento robusto, vector avanzado, clustering con K automatico (Silhouette Score), clasificacion avanzada y aprendizaje historico persistente.

## Flujo actual
1. Registro de gasto en `app.py`.
2. Guardado en `data/gastos_usuario.csv` mediante `src/utils.py`.
3. Preprocesamiento en `src/preprocessing.py`:
   - Limpieza de columnas.
   - Frecuencia mensual oficial por nombre y mes.
   - Conversion de hora a `horaDecimal`.
   - Features avanzadas: `[monto, horaDecimal, frecuencia, impactoMensual, porcentajePresupuesto]`.
4. Aplicacion de K-Means en `src/model.py` con `aplicar_kmeans_avanzado`:
   - Busqueda automatica de K con Silhouette Score.
   - Centroides y distancias para explicabilidad.
5. Clasificacion avanzada en `src/classifier.py`:
   - Gasto Primario
   - Gasto Hormiga Recurrente
   - Gasto Hormiga Ocasional
   - Gasto Extraordinario
6. Simulador visual (`pages/simulador.py` + `src/auditoria.py`) con trazabilidad y explicacion del agente.
7. Aprendizaje historico persistente (`src/historico.py`) con `data/gastos_historicos.csv` y `data/modelo_historico.json`.

## Alcance de esta etapa
- Mantener el contrato del modelo `aplicar_kmeans_avanzado()` y su integracion en app.
- Consolidar un solo flujo funcional: avanzado + historico.
- Mejorar pruebas y documentacion para mantenimiento academico.
