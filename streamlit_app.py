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

dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("A variável de ambiente 'DATABASE_URL' não foi encontrada no arquivo .env")

gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key is None:
    raise ValueError("A variável de ambiente 'GEMINI_API_KEY' não foi encontrada no arquivo .env")

engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})

def salvar_resposta(usuario, dados_dict, perfil_gerado):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO respostas_formulario (usuario, dados, perfil_gerado)
            VALUES (:usuario, :dados, :perfil)
            ON CONFLICT (usuario)
            DO UPDATE SET dados = :dados, perfil_gerado = :perfil
        """), {
            "usuario": usuario,
            "dados": json.dumps(dados_dict),
            "perfil": perfil_gerado
        })

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

def verificar_ou_criar_tabela_respostas():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS respostas_formulario (
                usuario TEXT PRIMARY KEY,
                dados JSONB,
                perfil_gerado TEXT,
                FOREIGN KEY (usuario) REFERENCES usuarios(username)
            );
        """))

def cadastrar_usuario(username, nome, senha):
    senha_hash = hash_password(senha)
    with engine.begin() as conn:
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

# Setup inicial
st.set_page_config(page_title="Plataforma de Livros", layout="wide")
verificar_ou_criar_tabela_usuarios()
verificar_ou_criar_tabela_respostas()

# Autenticação
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
                st.rerun()
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
                st.error("Este usuário já existe. Escolha outro.")

else:
    st.sidebar.write(f"👤 {st.session_state.logged_name}")
    if st.sidebar.button("Logout", key="btn_logout"):
        del st.session_state.logged_user
        del st.session_state.logged_name
        st.rerun()

    # Lógica principal para mostrar formulário ou perfil
    resposta_existente = buscar_resposta_existente(st.session_state.logged_user)
    
    if resposta_existente and resposta_existente.perfil_gerado:
        st.session_state["perfil_gerado"] = resposta_existente.perfil_gerado
    else:
        st.session_state.pop("perfil_gerado", None)
    
    if "perfil_gerado" in st.session_state:
        st.header("📖 Seu Perfil de Leitura")
        st.write(st.session_state["perfil_gerado"])

        if st.button("Refazer formulário"):
            st.session_state.pop("perfil_gerado", None)
            st.rerun()

    else:
        # Formulário de preferências (exemplo simplificado, complete com seus campos)
        st.title("Formulário de Preferências de Leitura")
        frequencia_leitura = st.radio("Com que frequência você costuma ler?", ["Todos os dias", "Algumas vezes por semana", "Algumas vezes por mês", "Raramente"])
        # ... complete com os outros campos do seu formulário ...

        if st.button("Enviar Respostas", key="btn_submit"):
            dados = {
                "frequencia_leitura": frequencia_leitura,
                # adicione o resto dos dados aqui...
            }
            
            prompt = f"""
            Você é um especialista em perfis de leitura. Com base nas informações abaixo, determine qual tipo de leitor eu sou:

            Dados:
            ```json
            {json.dumps(dados, ensure_ascii=False, indent=2)}
            ```
            """

            try:
                with st.spinner("Gerando seu perfil literário... Isso pode levar alguns segundos."):
                    genai.configure(api_key=gemini_api_key)
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    response = model.generate_content(prompt)
                    perfil = response.text
            except Exception as e:
                st.error(f"Erro ao gerar perfil de leitura: {e}")
                perfil = None

            if perfil:
                salvar_resposta(st.session_state.logged_user, dados, perfil)
                st.session_state["perfil_gerado"] = perfil
                st.rerun()
            else:
                st.error("Não foi possível gerar seu perfil de leitura.")
