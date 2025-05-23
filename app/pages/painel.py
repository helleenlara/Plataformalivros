# pages/painel.py
import streamlit as st
import pandas as pd
from app.services.database import carregar_dados
from app.config import GEMINI_API_KEY
import google.generativeai as genai
import json

def render():
    st.title("📖 Painel do Escritor")

    st.markdown("""
    Este painel utiliza conceitos de **Big Data em Python** para fornecer insights úteis a escritores,
    baseando-se nas preferências reais dos leitores coletadas pela plataforma.
    """)

    df = carregar_dados()

    if df.empty:
        st.warning("Ainda não há dados suficientes para análise.")
        return

    st.header("📊 Análise Estatística dos Leitores")

    col1, col2 = st.columns(2)
    with col1:
        if "formato_livro" in df.columns:
            st.subheader("📘 Formato de Leitura Preferido")
            st.bar_chart(df["formato_livro"].value_counts())

    with col2:
        if "generos" in df.columns:
            generos_series = df["generos"].str.split(", ").explode()
            st.subheader("📚 Gêneros Literários Mais Citados")
            st.bar_chart(generos_series.value_counts())

    col3, col4 = st.columns(2)
    with col3:
        if "objetivo_leitura" in df.columns:
            st.subheader("🎯 Objetivo de Leitura")
            st.bar_chart(df["objetivo_leitura"].value_counts())

    with col4:
        if "sentimento_livro" in df.columns:
            st.subheader("💫 Sentimentos Desejados")
            st.bar_chart(df["sentimento_livro"].value_counts())

    if "perfil_gerado" in df.columns:
        st.header("🧠 Análise Inteligente com IA")
        try:
            textos = " ".join(df["perfil_gerado"]).lower()
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
            chat = model.start_chat()
            prompt = f"""
Analise os seguintes perfis literários de leitores.
Identifique os principais temas, estilos narrativos e interesses recorrentes.
Resuma em tópicos úteis para escritores que desejam alinhar sua escrita ao público.

Perfis:
{textos}
"""
            response = chat.send_message(prompt.strip())
            st.markdown(response.text)
        except Exception as iae:
            st.warning(f"❌ Erro na análise com IA: {iae}")