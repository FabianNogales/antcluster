# antcluster

## Descripcion
`antcluster` es un prototipo academico de Inteligencia Artificial para segmentacion de gastos hormiga usando aprendizaje no supervisado con K-Means (K automatico con Silhouette Score).

## Objetivo de la beta
Construir un flujo funcional de punta a punta para:
1. Registrar gastos.
2. Persistirlos en CSV.
3. Preparar features avanzadas para clustering.
4. Entrenar clusters con K automatico y explicar decisiones.
5. Clasificar patrones de consumo y mantener aprendizaje historico persistente.

## Tecnologias usadas
- Python
- Streamlit
- Pandas
- NumPy
- scikit-learn
- Matplotlib
- Plotly
- SciPy

## Flujo de funcionamiento
Registrar gasto -> guardar CSV -> preprocesar -> vector avanzado -> K-Means (auto-K) -> clasificar -> mostrar resumen -> simulador -> aprendizaje historico.

## Estructura principal
```text
antcluster/
|-- app.py
|-- requirements.txt
|-- data/
|   |-- gastos_demo.csv
|   `-- gastos_usuario.csv
|-- src/
|   |-- __init__.py
|   |-- auditoria.py
|   |-- historico.py
|   |-- utils.py
|   |-- preprocessing.py
|   |-- model.py
|   `-- classifier.py
|-- pages/
|   `-- simulador.py
|-- tests/
|   |-- test_historico.py
|   |-- test_classifier.py
|   |-- test_model.py
|   `-- test_preprocessing.py
`-- docs/
    |-- descripcion_beta.md
    |-- manual_instalacion.md
    `-- pruebas_ejecucion.md
```

## Instalacion en Windows (Git Bash)
```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
streamlit run app.py
```

## Instalacion en Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Ejecucion de pruebas
```bash
python -m unittest discover -s tests -v
```

## Nota de entorno
Si ejecutas comandos con un Python global sin dependencias instaladas, pueden aparecer errores como `ModuleNotFoundError: No module named 'plotly'`. Usa el entorno virtual del proyecto y reinstala `requirements.txt` para garantizar una ejecucion reproducible.
