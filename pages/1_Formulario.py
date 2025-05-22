
import streamlit as st
from utils.database import salvar_resposta, usuario_ja_respondeu
from utils.autenticacao import get_usuario_logado

st.title("📝 Formulário de Preferências de Leitura")

usuario = get_usuario_logado()

if usuario:
    if not usuario_ja_respondeu(usuario):
        resposta = st.text_area("O que você gosta de ler?")
        if st.button("Enviar"):
            salvar_resposta(usuario, resposta, perfil_gerado=None)
            st.success("Resposta salva com sucesso!")
    else:
        st.info("Você já respondeu o formulário.")
else:
    st.warning("Faça login para responder.")
