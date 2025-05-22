
import streamlit as st
from utils.database import buscar_recomendacoes
from utils.autenticacao import get_usuario_logado

st.title("📖 Recomendação de Livros")

usuario = get_usuario_logado()

if usuario:
    recomendacoes = buscar_recomendacoes(usuario)
    if recomendacoes:
        for livro in recomendacoes:
            st.subheader(livro['titulo'])
            st.write(f"Autor: {livro['autor']}")
            st.write(f"Motivo: {livro['justificativa']}")
    else:
        st.warning("Nenhuma recomendação encontrada para você.")
else:
    st.warning("Faça login para ver suas recomendações.")
