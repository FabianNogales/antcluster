# Pruebas de ejecución

## Persona 1 - Interfaz de registro

| Codigo | Descripcion | Entrada | Resultado esperado | Estado |
|---|---|---|---|---|
| PR-001 | Inicio de la app | `streamlit run app.py` | Se muestra el titulo `AntCluster` | Pendiente |
| PR-002 | Validacion de nombre vacio | Nombre vacio y monto valido | Se muestra un error claro indicando que el nombre no puede estar vacio | Pendiente |
| PR-003 | Validacion de monto invalido | Nombre valido y monto `0` | Se muestra un error claro indicando que el monto debe ser mayor a 0 | Pendiente |
| PR-004 | Registro exitoso | `Cafe`, `8`, `19/05/2026`, `10:30` | Se muestra el mensaje de registro correcto y el ultimo gasto en pantalla | Pendiente |

## Persona 2 - Gestion de datos CSV

| Codigo | Descripcion | Entrada | Resultado esperado | Estado |
|---|---|---|---|---|
| P2-001 | Guardar gasto en CSV | Registrar `Cafe` con monto `5` | El gasto se agrega en `data/gastos_usuario.csv` con id, fecha, hora y frecuencia | Pendiente |
| P2-002 | Persistencia al recargar | Recargar la app despues de registrar un gasto | El gasto sigue apareciendo en la tabla | Pendiente |
| P2-003 | Cargar dataset demo | Pulsar `Cargar dataset demo` | La tabla muestra los registros de `data/gastos_demo.csv` | Pendiente |
| P2-004 | Descargar CSV | Pulsar `Descargar CSV` | Se descarga `gastos_usuario.csv` con los gastos actuales | Pendiente |
| P2-005 | Reiniciar datos | Pulsar `Reiniciar datos` | La tabla queda vacia | Pendiente |
| P2-006 | Verificar encabezados despues del reinicio | Abrir `data/gastos_usuario.csv` despues de reiniciar | El archivo queda vacio pero conserva `id,nombre,monto,fecha,hora,frecuencia` | Pendiente |

## Persona 3 - Procesamiento y clustering

| Codigo | Descripcion | Entrada | Resultado esperado | Estado |
|---|---|---|---|---|
| P3-001 | Cargar dataset demo y procesar | Pulsar `Analizar gastos` con `data/gastos_demo.csv` | El sistema calcula frecuencias mensuales sin errores | Pendiente |
| P3-002 | Aplicar K-Means | Gastos con 2 clusters identificados | Se muestran dos grupos diferenciados (pequeños y grandes) | Pendiente |
| P3-003 | Clasificar gastos correctamente | Ejecutar algoritmo completo | Cluster bajo = "Gasto Hormiga", Cluster alto = "Gasto Primario" | Pendiente |
| P3-004 | Mostrar resumen de presupuesto | Presupuesto: `200 Bs`, Gastos totales: `120 Bs` | Se visualiza: Total gastado, Gastos hormiga, Gastos primarios, Porcentaje | Pendiente |
| P3-005 | Visualizar grafico de clusters | Ejecutar analisis completo | Se genera grafico scatter con los 2 clusters claramente separados | Pendiente |

## Evidencias Fotográficas

A continuacion se presentan las capturas que demuestran el funcionamiento del sistema:

### 1. Registro de Gastos
![Registro de gasto](capturas/registro_gasto.png)

*Descripcion*: Interfaz de registro de un nuevo gasto con validaciones correctas.

### 2. Grafico de Clusters
![Grafico de clusters](capturas/grafico_clusters.png)

*Descripcion*: Visualizacion de los dos clusters identificados por K-Means en el espacio 3D [Monto, Hora, Frecuencia].

### 3. Resumen Final
![Resumen final](capturas/resumen_final.png)

*Descripcion*: Salida del analisis final mostrando clasificacion de gastos hormiga y primarios con porcentajes respecto al presupuesto.
