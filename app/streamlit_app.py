# main.py
import streamlit as st
from app.pages import formulario, painel

st.set_page_config(page_title="Plataforma de Livros", layout="wide")
st.sidebar.title("📚 Navegação")

pagina = st.sidebar.radio("Escolha uma seção:", [
    "📋 Formulário do Leitor",
    "📖 Painel do Escritor"
])

if pagina == "📋 Formulário do Leitor":
    formulario.render()
elif pagina == "📖 Painel do Escritor":
    painel.render()
