import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Conexão com o banco de dados
DATABASE_URL = "postgresql://banco_litmeapp_user:A48TgTYgIwbKtQ1nRSsLA53ipPPphiTj@dpg-d04mhrodl3ps73dh0k7g-a.oregon-postgres.render.com/banco_litmeapp"
engine = create_engine(DATABASE_URL)

st.title("📊 Visualização das Respostas do Formulário")

# Botão para carregar os dados
df = None
if st.button("🔄 Carregar Respostas do Banco de Dados"):
    try:
        df = pd.read_sql("SELECT * FROM respostas_formulario", engine)
        st.success("Dados carregados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")

# Se os dados foram carregados, exibir
if df is not None:
    st.subheader("📋 Todas as respostas")
    st.dataframe(df)

    # Análise simples: formatos de livro preferidos
    st.subheader("📚 Formatos de livro preferidos")
    st.bar_chart(df["formato_livro"].value_counts())

    # Análise simples: Gênero mais mencionado
    st.subheader("📖 Gêneros literários mais citados")
    generos_series = df["generos"].str.split(", ").explode()
    st.bar_chart(generos_series.value_counts())
