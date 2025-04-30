import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
import hashlib

# Carrega variáveis de ambiente
load_dotenv()

# Configura chave da API Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

# Conecta ao banco de dados PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável de ambiente 'DATABASE_URL' não foi encontrada no arquivo .env")
engine = create_engine(DATABASE_URL)

# Funções auxiliares
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_ou_criar_tabela_usuarios():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                username TEXT PRIMARY KEY,
                nome TEXT,
                senha_hash TEXT
            );
        """))

def cadastrar_usuario(username, nome, senha):
    senha_hash = hash_password(senha)
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO usuarios (username, nome, senha_hash)
            VALUES (:username, :nome, :senha_hash)
        """), {"username": username, "nome": nome, "senha_hash": senha_hash})

def autenticar_usuario(username, senha):
    senha_hash = hash_password(senha)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT * FROM usuarios
            WHERE username = :username AND senha_hash = :senha_hash
        """), {"username": username, "senha_hash": senha_hash}).fetchone()
    return result

# Inicializa aplicação
verificar_ou_criar_tabela_usuarios()

st.title("Recomendações de Livros Personalizadas")

menu = st.sidebar.selectbox("Menu", ["Login", "Cadastro"])

if menu == "Cadastro":
    with st.sidebar.form("cadastro_form"):
        st.subheader("Criar nova conta")
        new_username = st.text_input("Usuário")
        new_nome = st.text_input("Nome completo")
        new_password = st.text_input("Senha", type="password")
        if st.form_submit_button("Cadastrar"):
            try:
                cadastrar_usuario(new_username, new_nome, new_password)
                st.success("Usuário cadastrado com sucesso!")
            except IntegrityError:
                st.error("Este nome de usuário já existe.")
            except Exception as e:
                st.error(f"Erro ao cadastrar: {e}")

elif menu == "Login":
    if "logged_user" not in st.session_state:
        with st.sidebar.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                usuario = autenticar_usuario(username, password)
                if usuario:
                    st.session_state.logged_user = usuario.username
                    st.session_state.nome_user = usuario.nome
                    st.success(f"Bem-vindo, {usuario.nome}!")
                else:
                    st.error("Usuário ou senha incorretos.")

if "logged_user" in st.session_state:
    st.header("Formulário de Preferências de Leitura")
    with st.form("formulario_respostas"):
        preferencia = st.radio("Você prefere ficção ou não ficção?", ["Ficção", "Não ficção", "Ambos"])
        genero = st.text_input("Qual seu gênero favorito?")
        autor = st.text_input("Autor favorito")
        estilo = st.radio("Prefere ação, introspecção ou equilíbrio?", ["Ação", "Introspecção", "Equilíbrio"])

        if st.form_submit_button("Enviar Respostas"):
            prompt = f"""
            Usuário gosta de {preferencia}, especialmente do gênero {genero}.
            Autor favorito: {autor}.
            Prefere estilo de leitura com foco em {estilo.lower()}.
            Gere um perfil de leitura e recomende 3 livros baseados nisso.
            """
            try:
                model = genai.GenerativeModel("gemini-pro")
                response = model.generate_content(prompt)
                perfil = response.text
                st.subheader("🔍 Seu Perfil de Leitura e Recomendações")
                st.markdown(perfil)
            except Exception as e:
                st.error(f"Erro ao gerar recomendação: {e}")
