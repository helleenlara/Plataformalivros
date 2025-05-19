import streamlit as st
import hashlib
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

# Carregar variáveis de ambiente
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Criar engine com SSL
engine = create_engine(DATABASE_URL)

# Funções auxiliares
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def criar_tabela_usuarios():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                username TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                senha_hash TEXT NOT NULL
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

# Interface Streamlit
st.title("Login e Cadastro")

criar_tabela_usuarios()

menu = st.sidebar.selectbox("Menu", ["Login", "Cadastro"])

if menu == "Cadastro":
    st.subheader("Criar nova conta")
    new_user = st.text_input("Usuário")
    new_name = st.text_input("Nome")
    new_pass = st.text_input("Senha", type="password")
    if st.button("Cadastrar"):
        try:
            cadastrar_usuario(new_user, new_name, new_pass)
            st.success("Conta criada! Faça login.")
        except IntegrityError:
            st.error("Esse usuário já existe.")

elif menu == "Login":
    st.subheader("Acessar conta")
    login_user = st.text_input("Usuário")
    login_pass = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = autenticar_usuario(login_user, login_pass)
        if user:
            st.success(f"Bem-vindo(a), {user.nome}!")
        else:
            st.error("Usuário ou senha incorretos.")