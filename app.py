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

st.title("🩺 Auditoría Clínica Inteligente")
st.markdown("Sistema de evaluación automática de evolución y concurrencia")
st.divider()

# ----------------------
# COLUMNAS PRINCIPALES
# ----------------------
col1, col2 = st.columns([1, 1])

# ----------------------
# 📝 INPUTS
# ----------------------
with col1:
    st.markdown("### 📄 Evolución clínica")
    texto_evolucion = st.text_area("Ingrese evolución clínica", height=180)
    evaluar_evo = st.button("Evaluar Evolución 🟦", use_container_width=True)

    st.markdown("### 🟥 Nota de concurrencia")
    texto_concurrencia = st.text_area("Ingrese nota de concurrencia", height=180)
    evaluar_conc = st.button("Evaluar Concurrencia 🟥", use_container_width=True)

# ----------------------
# 📊 PROCESAMIENTO
# ----------------------
if evaluar_evo:
    if texto_evolucion.strip():
        score_evo, df_evo = evaluar_grupo(texto_evolucion, criterios_evolucion)
        st.session_state["score_evo"] = score_evo
        st.session_state["df_evo"] = df_evo
    else:
        st.warning("⚠️ No ingresaste evolución")

if evaluar_conc:
    if texto_concurrencia.strip():
        score_conc, df_conc = evaluar_grupo(texto_concurrencia, criterios_concurrencia)
        st.session_state["score_conc"] = score_conc
        st.session_state["df_conc"] = df_conc
    else:
        st.warning("⚠️ No ingresaste concurrencia")

# ----------------------
# 📊 RESULTADOS VISUALES
# ----------------------
with col2:
    st.markdown("### 📊 Resultados")

    # 🟦 Evolución
    if "df_evo" in st.session_state:
        with st.container():
            st.markdown("#### 🟦 Evolución")
            colA, colB = st.columns([1, 2])

            with colA:
                st.metric("Score", round(st.session_state["score_evo"], 2))

            with colB:
                st.dataframe(st.session_state["df_evo"], use_container_width=True)

    # 🟥 Concurrencia
    if "df_conc" in st.session_state:
        with st.container():
            st.markdown("#### 🟥 Nota de Concurrencia")
            colA, colB = st.columns([1, 2])

            with colA:
                st.metric("Score", round(st.session_state["score_conc"], 2))

            with colB:
                st.dataframe(st.session_state["df_conc"], use_container_width=True)

# ----------------------
# 🟩 USO DEL MÓDULO
# ----------------------
st.divider()
st.markdown("### 🟩 Uso del Módulo")

colM1, colM2 = st.columns(2)

with colM1:
    asesoria = st.checkbox("📞 Solicitó asesoría en plataforma")

with colM2:
    modulos = st.checkbox("🧩 Usó módulos (demoras, fugas, fallas, hallazgos)")

score_modulo = 0
if asesoria:
    score_modulo += 1.0
if modulos:
    score_modulo += 1.8

st.metric("Score Uso del Módulo", score_modulo)

# ----------------------
# 🧮 TOTAL
# ----------------------
st.divider()
st.markdown("## 🧮 Resultado Final")

total = 0

if "score_evo" in st.session_state:
    total += st.session_state["score_evo"]

if "score_conc" in st.session_state:
    total += st.session_state["score_conc"]

total += score_modulo

st.metric("TOTAL GENERAL", round(total, 2))
