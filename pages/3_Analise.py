
import streamlit as st
from utils.database import carregar_respostas
import pandas as pd

st.title("📊 Análise de Dados")

respostas = carregar_respostas()

if respostas:
    df = pd.DataFrame(respostas)
    st.dataframe(df)
    if 'genero_preferido' in df.columns:
        st.bar_chart(df['genero_preferido'].value_counts())
else:
    st.info("Nenhuma resposta encontrada no banco de dados.")
