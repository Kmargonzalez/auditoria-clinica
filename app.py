import streamlit as st
import re
import pandas as pd

from sentence_transformers import SentenceTransformer, util

@st.cache_resource
def cargar_modelo():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = cargar_modelo()

@st.cache_data
def embedding(texto):
    return model.encode(texto)

def similitud(texto, referencia):
    emb1 = embedding(texto)
    emb2 = embedding(referencia)
    return util.cos_sim(emb1, emb2).item()

st.set_page_config(page_title="Auditoría Clínica", layout="wide")

def limpiar_texto(texto):
    return texto.lower()

def evaluar_identificacion(texto):
    edad = bool(re.search(r'\b\d{1,3}\s*años\b', texto))
    sexo = any(x in texto for x in ["masculino", "femenino"])
    return 1 if (edad and sexo) else 0

def evaluar_signos(texto):
    patrones = [
        "frecuencia cardiaca",
        "presion arterial",
        "frecuencia respiratoria",
        "temperatura"
    ]
    return 1 if sum(p in texto for p in patrones) >= 2 else 0

def evaluar_diagnostico(texto):
    referencia = "el paciente tiene un diagnostico medico claro de una enfermedad"
    score = similitud(texto, referencia)
    return 1 if score > 0.4 else 0

def evaluar_plan(texto):
    referencia = "el paciente requiere tratamiento o manejo medico o quirurgico"
    score = similitud(texto, referencia)
    return 1 if score > 0.4 else 0
    # ----------------------
# NOTA CONCURRENCIA
# ----------------------

def evaluar_procesos_pendientes(texto):
    keywords = [
        "pendiente",
        "interconsulta",
        "valoracion",
        "procedimiento",
        "cirugia",
        "remision"
    ]
    return 1 if any(k in texto for k in keywords) else 0


def evaluar_justificacion_estancia(texto):
    referencia = "el paciente necesita hospitalizacion por condicion medica"
    score = similitud(texto, referencia)
    return 1 if score > 0.4 else 0


def evaluar_analisis_concurrencia(texto):
    referencia = "el texto contiene analisis clinico con razonamiento medico"
    score = similitud(texto, referencia)
    return 1 if score > 0.45 else 0
    
criterios_evolucion = [
    {"nombre": "Identificación paciente", "peso": 0.3, "func": evaluar_identificacion},
    {"nombre": "Signos vitales", "peso": 0.5, "func": evaluar_signos},
    {"nombre": "Diagnóstico", "peso": 0.5, "func": evaluar_diagnostico},
    {"nombre": "Plan de manejo", "peso": 0.5, "func": evaluar_plan},
]

# ----------------------
# NOTA CONCURRENCIA
# ----------------------
criterios_concurrencia = [
    {"nombre": "Procesos pendientes", "peso": 1.5, "func": evaluar_procesos_pendientes},
    {"nombre": "Justificación de estancia", "peso": 2.0, "func": evaluar_justificacion_estancia},
    {"nombre": "Análisis técnico-administrativo", "peso": 0.9, "func": evaluar_analisis_concurrencia},
]

def evaluar_grupo(texto, criterios):
    resultados = []
    total = 0

    for c in criterios:
        val = c["func"](texto)
        score = val * c["peso"]
        total += score

        resultados.append({
            "Criterio": c["nombre"],
            "Cumple": "✅" if val else "❌",
            "Peso": c["peso"],
            "Puntaje": score
        })

    return total, pd.DataFrame(resultados)

def evaluar_nota(texto):
    texto = limpiar_texto(texto)
    resultados = []
    total = 0

    for c in criterios:
        val = c["func"](texto)
        score = val * c["peso"]
        total += score

        resultados.append({
            "Criterio": c["nombre"],
            "Cumple": "✅" if val else "❌",
            "Peso": c["peso"],
            "Puntaje": score
        })

    return total, pd.DataFrame(resultados)

st.title("🩺 Auditoría Clínica Automática")

# Crear columnas
col1, col2 = st.columns([1, 1])

# ----------------------
# COLUMNA 1 (INPUT)
# ----------------------
with col1:
    st.subheader("📄 Evolución clínica")
    texto_evolucion = st.text_area("Pega la evolución clínica", height=200)

    st.subheader("🟥 Nota de concurrencia")
    texto_concurrencia = st.text_area("Pega la nota de concurrencia", height=200)

    evaluar = st.button("Evaluar")

# ----------------------
# COLUMNA 2 (RESULTADOS)
# ----------------------
with col2:
    st.subheader("📊 Resultados")

    if evaluar:

        # 🔹 Evolución
        st.markdown("## 🟦 Evolución")
        score_evo, df_evo = evaluar_grupo(texto_evolucion, criterios_evolucion)
        st.metric("Score Evolución", round(score_evo, 2))
        st.dataframe(df_evo)

        # 🔹 Concurrencia
        st.markdown("## 🟥 Nota de Concurrencia")
        score_conc, df_conc = evaluar_grupo(texto_concurrencia, criterios_concurrencia)
        st.metric("Score Concurrencia", round(score_conc, 2))
        st.dataframe(df_conc)

        # 🔹 Uso del módulo
        st.markdown("## 🟩 Uso del Módulo")

        asesoria = st.checkbox("¿Solicitó asesoría en plataforma?")
        modulos = st.checkbox("¿Usó módulos (demoras, fugas, fallas, hallazgos)?")

        score_modulo = 0
        if asesoria:
            score_modulo += 1.0
        if modulos:
            score_modulo += 1.8

        st.metric("Score Uso del Módulo", score_modulo)

        # 🔹 TOTAL
        total = score_evo + score_conc + score_modulo
        st.markdown("## 🧮 Score Total")
        st.metric("TOTAL", round(total, 2))
