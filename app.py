"""Interfaz principal de AntCluster para registrar gastos."""

from datetime import datetime

import streamlit as st


st.set_page_config(page_title="AntCluster", layout="centered")


def inicializar_estado() -> None:
    """Inicializa las claves usadas por la interfaz."""
    if "ultimo_gasto" not in st.session_state:
        st.session_state.ultimo_gasto = None


def validar_gasto(nombre: str, monto: float) -> list[str]:
    """Valida los datos minimos del formulario."""
    errores: list[str] = []

    if not nombre.strip():
        errores.append("El nombre del gasto no puede estar vacio.")

    if monto <= 0:
        errores.append("El monto debe ser mayor a 0.")

    return errores


def registrar_gasto(nombre: str, monto: float) -> None:
    """Guarda temporalmente el ultimo gasto valido en session_state."""
    ahora = datetime.now()

    st.session_state.ultimo_gasto = {
        "nombre": nombre.strip(),
        "monto": float(monto),
        "fecha": ahora.strftime("%Y-%m-%d"),
        "hora": ahora.strftime("%H:%M"),
    }


inicializar_estado()

st.title("AntCluster")
st.write("Registro base de gastos para la primera etapa del proyecto.")

with st.form("formulario_gasto"):
    nombre = st.text_input("Nombre del gasto")
    monto = st.number_input("Monto", min_value=0.0, step=0.5, format="%.2f")
    enviado = st.form_submit_button("Guardar gasto")

if enviado:
    errores = validar_gasto(nombre, monto)

    if errores:
        for error in errores:
            st.error(error)
    else:
        registrar_gasto(nombre, monto)
        st.success("El gasto fue registrado correctamente.")

if st.session_state.ultimo_gasto:
    ultimo_gasto = st.session_state.ultimo_gasto
    st.subheader("Ultimo gasto registrado")
    st.write(f"Nombre: {ultimo_gasto['nombre']}")
    st.write(f"Monto: Bs. {ultimo_gasto['monto']:.2f}")
    st.write(f"Fecha: {ultimo_gasto['fecha']}")
    st.write(f"Hora: {ultimo_gasto['hora']}")
