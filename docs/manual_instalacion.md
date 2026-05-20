# Manual de instalacion

## Requisitos previos
- Python 3.10 o superior
- pip

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

## Verificacion rapida de dependencias
```bash
python -c "import pandas, streamlit, sklearn, matplotlib"
```

## Ejecucion de pruebas
```bash
python -m unittest discover -s tests -v
```

## Solucion de problemas comun
- Error: `ModuleNotFoundError: No module named 'pandas'`
  - Causa: Python global sin dependencias del proyecto.
  - Solucion: activar `venv` y reinstalar con `pip install -r requirements.txt`.