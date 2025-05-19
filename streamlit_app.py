import streamlit as st
import pandas as pd
import hashlib
import os
import json
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, text
import google.generativeai as genai
from pathlib import Path

# Carrega variáveis de ambiente
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)

# Conexão com banco e API
DATABASE_URL = os.getenv("DATABASE_URL")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL não definida no .env")

if gemini_api_key is None:
    raise ValueError("GEMINI_API_KEY não definida no .env")

engine = create_engine(os.getenv("DATABASE_URL"))

# Funções auxiliares
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_ou_criar_tabela_usuarios():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                username TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                senha_hash TEXT NOT NULL
            );
        """))

def verificar_ou_criar_tabela_respostas():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS respostas_formulario (
                usuario TEXT PRIMARY KEY REFERENCES usuarios(username),
                dados JSONB NOT NULL,
                perfil_gerado TEXT
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
        return conn.execute(text("""
            SELECT username, nome FROM usuarios
            WHERE username = :username AND senha_hash = :senha_hash
        """), {"username": username, "senha_hash": senha_hash}).fetchone()

def buscar_resposta_existente(usuario):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT dados, perfil_gerado FROM respostas_formulario
            WHERE usuario = :usuario
        """), {"usuario": usuario}).fetchone()
        return result

def salvar_resposta(usuario, dados_dict, perfil_gerado):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO respostas_formulario (usuario, dados, perfil_gerado)
            VALUES (:usuario, :dados, :perfil)
            ON CONFLICT (usuario)
            DO UPDATE SET dados = :dados, perfil_gerado = :perfil
        """), {"usuario": usuario, "dados": json.dumps(dados_dict), "perfil": perfil_gerado})

# Setup
st.set_page_config(page_title="Plataforma de Livros", layout="wide")
verificar_ou_criar_tabela_usuarios()
verificar_ou_criar_tabela_respostas()

# Login/Cadastro
if "logged_user" not in st.session_state:
    st.sidebar.title("🔐 Autenticação")
    tab_login, tab_signup = st.sidebar.tabs(["Login", "Cadastrar"])

    with tab_login:
        st.subheader("Login")
        login_user = st.text_input("Usuário", key="login_user")
        login_pass = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar", key="btn_login"):
            user = autenticar_usuario(login_user, login_pass)
            if user:
                st.session_state.logged_user = user.username
                st.session_state.logged_name = user.nome
                st.success(f"Bem-vindo(a), {user.nome}!")
            else:
                st.error("Usuário ou senha incorretos.")

    with tab_signup:
        st.subheader("Cadastrar")
        new_user = st.text_input("Usuário", key="new_user")
        new_name = st.text_input("Nome", key="new_name")
        new_pass = st.text_input("Senha", type="password", key="new_pass")
        if st.button("Cadastrar", key="btn_signup"):
            try:
                cadastrar_usuario(new_user, new_name, new_pass)
                st.success("Conta criada! Faça login.")
            except IntegrityError:
                st.error("Este usuário já existe.")
else:
    st.sidebar.write(f"👤 {st.session_state.logged_name}")
    if st.sidebar.button("Logout"):
        del st.session_state.logged_user
        del st.session_state.logged_name
        st.experimental_rerun()

    resposta_existente = buscar_resposta_existente(st.session_state.logged_user)

    if resposta_existente:
        st.success("Você já preencheu o formulário. Aqui está seu perfil literário:")
        st.header("📖 Seu Perfil de Leitura")
        st.write(resposta_existente.perfil_gerado)
    else:
        st.title("Formulário de Preferências de Leitura")
        genero = st.selectbox("Qual seu gênero favorito?", ["Fantasia", "Ficção Científica", "Romance", "Suspense", "Outro"])
        autor = st.text_input("Autor favorito:")
        ritmo = st.radio("Você lê em ritmo...", ["Rápido", "Moderado", "Lento"])

        if st.button("Enviar Respostas"):
            dados = {
                "genero": genero,
                "autor": autor,
                "ritmo": ritmo
            }

            try:
                salvar_resposta(st.session_state.logged_user, dados, "")
                st.success("Respostas salvas! Gerando perfil...")
            except IntegrityError:
                st.error("Você já respondeu o formulário.")
                st.stop()

            prompt = f"Crie um breve perfil literário para um leitor que gosta de {genero}, autor favorito {autor}, e lê em ritmo {ritmo}."

            try:
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel("gemini-1.5-pro")
                response = model.generate_content(prompt)
                perfil = response.text
            except Exception as e:
                st.error(f"Erro ao gerar perfil: {e}")
                perfil = None

            if perfil:
                salvar_resposta(st.session_state.logged_user, dados, perfil)
                st.header("📖 Seu Perfil de Leitura")
                st.write(perfil)