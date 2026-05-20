# Pruebas de ejecucion

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
