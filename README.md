# antcluster

## Descripcion
`antcluster` es una beta academica de Inteligencia Artificial para segmentacion de gastos hormiga usando aprendizaje no supervisado con K-Means (`K=2`).

## Objetivo de la beta
Construir un flujo funcional de punta a punta para:
1. Registrar gastos.
2. Persistirlos en CSV.
3. Preparar datos para clustering.
4. Separar gastos en dos grupos y clasificarlos semanticamente.

## Tecnologias usadas
- Python
- Streamlit
- Pandas
- NumPy
- scikit-learn
- Matplotlib

## Flujo de funcionamiento
Registrar gasto -> guardar CSV -> preprocesar -> vectorizar -> K-Means -> clasificar -> mostrar resumen.

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
|   |-- utils.py
|   |-- preprocessing.py
|   |-- model.py
|   `-- classifier.py
|-- tests/
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
Si ejecutas comandos con un Python global sin dependencias instaladas, pueden aparecer errores como `ModuleNotFoundError: No module named 'pandas'`. Usa el entorno virtual del proyecto para garantizar una ejecucion reproducible.