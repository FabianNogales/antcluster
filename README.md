# AntCluster

## Descripcion
AntCluster es una aplicacion en Python para la materia de Inteligencia Artificial. El proyecto se enfoca en aprendizaje no supervisado para segmentar gastos hormiga mediante K-Means con `K=2`.

Cada gasto sera transformado en un vector con la forma `[Monto, Hora, Frecuencia]`. En esta primera etapa solo se implementa la interfaz de registro de gastos.

## Tecnologias previstas
- Python
- Streamlit
- Pandas
- NumPy
- scikit-learn
- Matplotlib

## Alcance actual
- Interfaz base en Streamlit
- Formulario para registrar gastos
- Validaciones del nombre y del monto
- Almacenamiento temporal del ultimo gasto en `st.session_state`

## Estructura del proyecto
```text
antcluster/
├── README.md
├── requirements.txt
├── .gitignore
├── app.py
├── data/
│   ├── gastos_demo.csv
│   └── gastos_usuario.csv
├── src/
│   ├── __init__.py
│   ├── preprocessing.py
│   ├── model.py
│   ├── classifier.py
│   └── utils.py
└── docs/
    ├── descripcion_beta.md
    ├── manual_instalacion.md
    ├── pruebas_ejecucion.md
    └── capturas/
        └── persona1_registro_gastos/
```

## Instalacion y ejecucion
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Estado
La logica de K-Means y la clasificacion semantica aun no estan implementadas.
