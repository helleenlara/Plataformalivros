# pages/formulario.py
import streamlit as st
from app.services.auth import autenticar_usuario, cadastrar_usuario
from app.services.database import salvar_resposta, buscar_resposta_existente
from app.services.recomendador import gerar_perfil

def render():
    if "logged_user" not in st.session_state:
        st.sidebar.title("🔐 Autenticação")
        aba_login, aba_cadastro = st.sidebar.tabs(["Login", "Cadastrar"])

        with aba_login:
            st.subheader("Login")
            login_user = st.text_input("Usuário", key="login_user")
            login_pass = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Entrar", key="btn_login"):
                user = autenticar_usuario(login_user, login_pass)
                if user:
                    st.session_state.logged_user = user.username
                    st.session_state.logged_name = user.nome
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

        with aba_cadastro:
            st.subheader("Cadastrar")
            new_user = st.text_input("Usuário", key="new_user")
            new_name = st.text_input("Nome", key="new_name")
            new_pass = st.text_input("Senha", type="password", key="signup_pass")
            if st.button("Cadastrar", key="btn_signup"):
                try:
                    cadastrar_usuario(new_user, new_name, new_pass)
                    st.success("Conta criada! Faça login.")
                except:
                    st.error("Erro ao cadastrar. Verifique os dados e tente novamente.")
    else:
        st.sidebar.write(f"👤 {st.session_state.logged_name}")
        if st.sidebar.button("Logout", key="btn_logout"):
            for key in ["logged_user", "logged_name", "form_submitted", "perfil"]:
                st.session_state.pop(key, None)
            st.rerun()

        resposta_existente = buscar_resposta_existente(st.session_state.logged_user)
        if resposta_existente and "form_submitted" not in st.session_state:
            st.session_state.form_submitted = True
            st.session_state.perfil = resposta_existente.perfil_gerado

        if "form_submitted" not in st.session_state:
            st.title("📋 Formulário de Preferências de Leitura")
            # Aqui você adicionaria os campos do formulário como no seu código original
        else:
            st.title("📖 Seu Perfil Literário")
            st.write(st.session_state.perfil)