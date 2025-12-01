import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard de Manutenção", layout="wide")

# --- CSS PARA FUNDO PRETO/DEGRADÊ ---
st.markdown(
    """
    <style>
    /* Fundo da aplicação principal */
    .stApp {
        background: linear-gradient(to bottom, #0e1117, #262730);
        color: white;
    }
    /* Ajuste para cartões métricos (opcional, para destacar) */
    [data-testid="stMetricValue"] {
        color: #00f2c3 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Dashboard de Manutenção") 

# --- 1. FUNÇÕES DE LIMPEZA E EXTRAÇÃO ---

def extrair_id_maquina(texto):
    if not isinstance(texto, str):
        return "N/I"
    texto_limpo = texto.strip().replace('#', '')
    if ' - ' in texto_limpo:
        return texto_limpo.split(' - ')[0].strip()
    return texto_limpo.split(' ')[0].strip()

def extrair_nome_maquina(texto):
    if not isinstance(texto, str):
        return "Desconhecido"
    if ' - ' in texto:
        partes = texto.split(' - ')
        if len(partes) > 1:
            return partes[1].strip()
    return texto

def converter_duracao(valor):
    try:
        if pd.isna(valor) or valor == 0 or valor == '0':
            return 0.0
        if isinstance(valor, str):
            valor = valor.strip()
            if ':' in valor:
                partes = valor.split(':')
                if len(partes) == 3:
                    return int(partes[0]) + (int(partes[1])/60
