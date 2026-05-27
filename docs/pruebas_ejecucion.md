# Reporte de pruebas de ejecucion

Este documento resume las pruebas funcionales del prototipo `antcluster`, incluyendo registro de gastos, persistencia en CSV, preprocesamiento y analisis con K-Means.

## 1. Resumen de pruebas

| Fase | Descripcion | Resultado esperado | Estado | Evidencia |
|---|---|---|---|---|
| F1 | Registro e interfaz | Ingreso de transacciones con validacion de datos | Exitoso | Figura 1 |
| F2 | Persistencia CSV | Almacenamiento en `data/gastos_usuario.csv` | Exitoso | Figura 1 |
| F3 | Analisis K-Means | Clasificacion automatica y calculo de metricas | Exitoso | Figura 2 |
| F4 | Formateo visual | Tabla con color por tipo de gasto | Exitoso | Figura 2 |

## 2. Pruebas funcionales de interfaz y datos

| Codigo | Descripcion | Entrada | Resultado esperado |
|---|---|---|---|
| UI-001 | Inicio de app | `streamlit run app.py` | Carga titulo, formulario y tabla de gastos |
| UI-002 | Validacion nombre | Nombre vacio + monto valido | Mensaje de validacion de nombre |
| UI-003 | Validacion monto | Nombre valido + monto `0` | Mensaje de validacion de monto |
| UI-004 | Registro exitoso | `Cafe`, `8` | Registro guardado y visible en tabla |
| UI-005 | Cargar demo | Boton `Cargar dataset demo` | Se cargan registros demo en tabla |
| UI-006 | Reiniciar datos | Boton `Reiniciar datos` | CSV usuario queda solo con encabezados |

## 3. Pruebas de preprocesamiento

| Codigo | Descripcion | Entrada | Resultado esperado |
|---|---|---|---|
| PRE-001 | CSV inexistente | Ruta no valida | Retorna DataFrame vacio sin romper |
| PRE-002 | Frecuencia faltante | CSV sin columna `frecuencia` | Se calcula por nombre y mes |
| PRE-003 | Hora HH:MM | `hora=14:30` | `horaDecimal=14.5` |
| PRE-004 | Hora invalida | `hora=99:99` | `horaDecimal=NaN` (fila controlada) |
| PRE-005 | Monto invalido | `monto='abc'` | `monto=NaN` (modelo filtra fila) |

## 4. Pruebas de modelo y clasificacion

| Codigo | Descripcion | Entrada | Resultado esperado |
|---|---|---|---|
| MOD-001 | K-Means base | DataFrame valido con 4 filas | Devuelve `cluster`, centroides y `mensaje=None` |
| MOD-002 | Pocos registros validos | Menos de 2 filas validas | Mensaje: se necesitan al menos 2 registros validos |
| MOD-003 | Clasificacion semantica | Cluster bajo y cluster alto | Hormiga = cluster de menor monto promedio |

## 5. Comandos de validacion automatica

```bash
python -m py_compile app.py src/preprocessing.py src/model.py src/classifier.py src/utils.py
python -m unittest discover -s tests -v
```

## 6. Evidencias

### Figura 1. Flujo de registro y almacenamiento
![Registro y gestion de datos](capturas/persona1_registro_gastos/registro_gasto.png)

Descripcion: interfaz principal con formulario, confirmacion de guardado y actualizacion de indicadores.

### Figura 2. Resumen analitico y segmentacion por color
![Resultados del analisis K-Means](capturas/persona1_registro_gastos/resumen_final.png)

Descripcion: panel con metricas de gastos hormiga/primarios y tabla clasificada por tipo.

Nota: la visualizacion de clusters y trazabilidad se genera dinamicamente con Plotly en el simulador de caja blanca.
