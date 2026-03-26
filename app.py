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

import re

def evaluar_identificacion(texto):
    texto = texto.lower()

    # 🔹 Detectar edad (más flexible)
    edad = bool(re.search(r'\b\d{1,3}\s*(años|anos)', texto))

    # 🔹 Detectar sexo (más variantes)
    sexo = any(x in texto for x in [
        "masculino",
        "femenino",
        "hombre",
        "mujer",
        "paciente masculino",
        "paciente femenina"
    ])

    return 1 if (edad and sexo) else 0

def evaluar_signos(texto):
    texto = texto.lower()

    patrones = [
        r"frecuencia\s*card",        # frecuencia cardiaca
        r"frecuencia\s*resp",        # frecuencia respiratoria
        r"temperatura",
        r"saturacion",
        r"\bta\b",                  # TA
        r"sist",                    # sistólica
        r"diast",                   # diastólica
        r"\d+\s*/\s*\d+"            # presión tipo 120/80
    ]

    encontrados = sum(bool(re.search(p, texto)) for p in patrones)

    return 1 if encontrados >= 2 else 0

def evaluar_diagnostico(texto):
    referencia = "el paciente tiene un diagnostico medico claro de una enfermedad"
    score = similitud(texto, referencia)
    return 1 if score > 0.4 else 0

def evaluar_plan(texto):
    texto = texto.lower()

    # 🔹 Regla obligatoria (evita falsos positivos)
    palabras_clave = [
        "plan",
        "tratamiento",
        "manejo",
        "se indica",
        "se inicia",
        "requiere",
        "se realiza"
    ]

    tiene_keyword = any(p in texto for p in palabras_clave)

    if not tiene_keyword:
        return 0  # ❌ sin palabras clave → no hay plan

    # 🔹 Validación con IA
    referencia = "el paciente tiene un plan de tratamiento definido"
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
        score = int(val) * c["peso"]
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
    evaluar_evo = st.button("Evaluar Evolución 🟦")

    st.subheader("🟥 Nota de concurrencia")
    texto_concurrencia = st.text_area("Pega la nota de concurrencia", height=200)
    evaluar_conc = st.button("Evaluar Concurrencia 🟥")

# ----------------------
# COLUMNA 2 (RESULTADOS)
# ----------------------
with col2:
    st.subheader("📊 Resultados")

    # ----------------------
    # 🟦 EVOLUCIÓN
    # ----------------------
    if evaluar_evo:
        if texto_evolucion.strip():
        score_evo, df_evo = evaluar_grupo(texto_evolucion, criterios_evolucion)
        st.session_state["score_evo"] = score_evo
        st.dataframe(df_evo)
        else:
            st.warning("⚠️ No ingresaste evolución")

    # ----------------------
    # 🟥 CONCURRENCIA
    # ----------------------
    if evaluar_conc:
        if texto_concurrencia.strip():
        score_conc, df_conc = evaluar_grupo(texto_concurrencia, criterios_concurrencia)
        st.session_state["score_conc"] = score_conc
        st.dataframe(df_conc)
        else:
            st.warning("⚠️ No ingresaste nota de concurrencia")

        # ----------------------
        # 🟩 USO DEL MÓDULO
        # ----------------------
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
st.markdown("## 🧮 Score Total")

total = 0

if "score_evo" in st.session_state:
    total += st.session_state["score_evo"]

if "score_conc" in st.session_state:
    total += st.session_state["score_conc"]

total += score_modulo

st.metric("TOTAL", round(total, 2))
