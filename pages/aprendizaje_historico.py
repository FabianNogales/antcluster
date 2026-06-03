"""Pagina independiente para aprendizaje historico."""

from __future__ import annotations

import streamlit as st

from src.historico import (
    MODELO_HISTORICO_JSON,
    cargar_gastos_historicos,
    cargar_modelo_historico,
    clasificar_gasto_con_modelo_historico,
    entrenar_agente_historico,
    guardar_modelo_historico,
    inicializar_archivos_historicos,
)
from src.sidebar import render_sidebar_presupuesto
from src.utils import initialize_data_files


st.set_page_config(page_title="Aprendizaje historico", layout="wide")
initialize_data_files()
inicializar_archivos_historicos()

flash = st.session_state.pop("flash_message", None)
if flash:
    getattr(st, flash.get("level", "info"))(flash.get("message", ""))


def _set_flash(level: str, message: str) -> None:
    st.session_state["flash_message"] = {"level": level, "message": message}


_, presupuesto_total, _, _ = render_sidebar_presupuesto()
modelo_historico = cargar_modelo_historico()
df_historico = cargar_gastos_historicos()

st.title("Aprendizaje historico")
st.subheader("Estado del modelo historico")

estado_modelo = "entrenado" if modelo_historico.get("entrenado") else "no entrenado"
existe_modelo = MODELO_HISTORICO_JSON.exists() and MODELO_HISTORICO_JSON.stat().st_size > 0
col_h1, col_h2, col_h3 = st.columns(3)
col_h1.metric("Estado", estado_modelo)
col_h2.metric("Archivo modelo", "Disponible" if existe_modelo else "No disponible")
col_h3.metric("Registros historicos", len(df_historico))

if st.button("Entrenar agente historico", use_container_width=True):
    try:
        nuevo_modelo = entrenar_agente_historico(df_historico, presupuesto_total=presupuesto_total)
        guardar_modelo_historico(nuevo_modelo)
        _set_flash("success", "Entrenamiento historico completado y guardado.")
        st.rerun()
    except Exception:
        st.error("No se pudo entrenar el modelo historico con los datos actuales.")

if modelo_historico.get("entrenado"):
    st.subheader("Resumen del entrenamiento")
    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    col_e1.metric("Fecha entrenamiento", str(modelo_historico.get("fecha_entrenamiento") or "-"))
    col_e2.metric("Registros usados", int(modelo_historico.get("cantidad_registros") or 0))
    col_e3.metric("Mejor K", int(modelo_historico.get("mejor_k") or 0))
    presupuesto_entrenamiento = modelo_historico.get("presupuesto_total", None)
    if presupuesto_entrenamiento is None:
        col_e4.metric("Presupuesto entrenamiento", "-")
    else:
        col_e4.metric("Presupuesto entrenamiento", f"Bs. {float(presupuesto_entrenamiento):.2f}")

    centroides_hist = modelo_historico.get("centroides", [])
    columnas_hist = modelo_historico.get("columnas_features", [])
    if centroides_hist and columnas_hist:
        st.write("Centroides historicos")
        st.dataframe(
            data={
                "cluster": list(range(len(centroides_hist))),
                **{col: [float(row[idx]) for row in centroides_hist] for idx, col in enumerate(columnas_hist)},
            },
            use_container_width=True,
            hide_index=True,
        )

    scores_hist = modelo_historico.get("scores_silhouette", [])
    if scores_hist:
        st.write("Scores de Silhouette historicos")
        st.dataframe(scores_hist, use_container_width=True, hide_index=True)

    with st.form("formulario_clasificacion_historica"):
        st.write("Clasificar nuevo gasto con centroides historicos")
        if presupuesto_entrenamiento is None:
            st.caption(f"Presupuesto usado para clasificar ahora: Bs. {float(presupuesto_total):.2f}")
        else:
            st.caption(
                f"Presupuesto actual (clasificacion): Bs. {float(presupuesto_total):.2f} | "
                f"Presupuesto del entrenamiento historico: Bs. {float(presupuesto_entrenamiento):.2f}"
            )
        nombre_h = st.text_input("Nombre nuevo gasto", value="Gasto nuevo")
        monto_h = st.number_input("Monto nuevo gasto", min_value=0.0, step=0.5, format="%.2f")
        fecha_h = st.date_input("Fecha nuevo gasto")
        hora_h = st.text_input("Hora nuevo gasto (HH:MM)", value="12:00")
        frecuencia_h = st.number_input("Frecuencia (opcional)", min_value=0, value=1, step=1)
        enviar_h = st.form_submit_button("Clasificar con historico", use_container_width=True)

    if enviar_h:
        try:
            resultado_hist = clasificar_gasto_con_modelo_historico(
                {
                    "nombre": nombre_h,
                    "monto": monto_h,
                    "fecha": fecha_h.strftime("%Y-%m-%d"),
                    "hora": hora_h,
                    "frecuencia": frecuencia_h,
                },
                modelo_historico=modelo_historico,
                presupuesto_total=presupuesto_total,
            )
            st.success("Clasificacion historica ejecutada.")
            st.write(f"Cluster asignado: **{resultado_hist['cluster_asignado']}**")
            st.write(f"Categoria interpretada: **{resultado_hist['categoria_interpretada']}**")
            st.write(resultado_hist["explicacion"])
            presupuesto_entrenado = resultado_hist["presupuesto_modelo_entrenado"]
            presupuesto_entrenado_texto = "-" if presupuesto_entrenado is None else f"Bs. {float(presupuesto_entrenado):.2f}"
            st.caption(
                f"Presupuesto clasificacion: Bs. {float(resultado_hist['presupuesto_clasificacion']):.2f} | "
                f"Presupuesto entrenamiento: {presupuesto_entrenado_texto}"
            )
            st.write("Vector generado")
            st.json(resultado_hist["vector_generado"])
            st.write("Distancias a centroides")
            st.dataframe(resultado_hist["distancias_centroides"], use_container_width=True, hide_index=True)
        except ValueError as error:
            st.error(str(error))
        except Exception:
            st.error("No se pudo clasificar el nuevo gasto con el modelo historico.")
else:
    st.info("Todavia no hay un modelo historico entrenado.")
