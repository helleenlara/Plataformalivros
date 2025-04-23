import streamlit as st
from sqlalchemy import create_engine
import pandas as pd


DATABASE_URL = "postgresql://banco_litmeapp_user:A48TgTYgIwbKtQ1nRSsLA53ipPPphiTj@dpg-d04mhrodl3ps73dh0k7g-a.oregon-postgres.render.com/banco_litmeapp"

engine = create_engine(DATABASE_URL)

if st.button("Enviar Respostas"):
    # Monta os dados em um DataFrame
    dados = {
        "frequencia_leitura": frequencia_leitura,
        "tempo_leitura": tempo_leitura,
        "local_leitura": local_leitura,
        "tipo_livro": tipo_livro,
        "generos": ", ".join(generos),
        "genero_outro": genero_outro,
        "autor_favorito": autor_favorito,
        "tamanho_livro": tamanho_livro,
        "narrativa": narrativa,
        "sentimento_livro": sentimento_livro,
        "questoes_sociais": questoes_sociais,
        "releitura": releitura,
        "formato_livro": formato_livro,
        "influencia": influencia,
        "avaliacoes": avaliacoes,
        "audiolivros": audiolivros
    }

    df = pd.DataFrame([dados])
    df.to_sql("respostas_formulario", engine, if_exists="append", index=False)

    st.success("Formulário enviado com sucesso!")

st.title("Formulário de Preferências de Leitura")

# Seção 1 - Hábitos de leitura
st.header("1. Sobre seus hábitos de leitura")

frequencia_leitura = st.radio("Com que frequência você costuma ler?", [
    "Todos os dias",
    "Algumas vezes por semana",
    "Algumas vezes por mês",
    "Raramente"
])

tempo_leitura = st.radio("Quanto tempo você geralmente dedica à leitura por sessão?", [
    "Menos de 30 minutos",
    "30 minutos a 1 hora",
    "1 a 2 horas",
    "Mais de 2 horas"
])

local_leitura = st.radio("Onde você costuma ler com mais frequência?", [
    "Em casa",
    "No transporte público",
    "Em bibliotecas/cafés",
    "Outros lugares"
])

# Seção 2 - Preferências de leitura
st.header("2. Sobre suas preferências de leitura")

tipo_livro = st.radio("Você prefere livros de ficção ou não ficção?", [
    "Ficção",
    "Não ficção",
    "Gosto dos dois"
])

generos = st.multiselect("Qual gênero literário você mais gosta? (Escolha até 3)", [
    "Ficção científica", "Fantasia", "Romance", "Mistério/Thriller", "Terror",
    "História", "Biografia", "Desenvolvimento pessoal", "Negócios", "Filosofia", "Outro"
])

genero_outro = ""
if "Outro" in generos:
    genero_outro = st.text_input("Qual outro gênero?")

autor_favorito = st.text_input("Você tem algum autor favorito?")

tamanho_livro = st.radio("Você prefere livros curtos ou longos?", [
    "Curtos (-200 páginas)",
    "Médios (200-400 páginas)",
    "Longos (+400 páginas)",
    "Não tenho preferência"
])

narrativa = st.radio("Como você gosta da narrativa dos livros?", [
    "Ação rápida, cheia de acontecimentos",
    "Narrativa introspectiva, com profundidade emocional",
    "Equilibrado entre ação e introspecção"
])

# Seção 3 - Personalidade do leitor
st.header("3. Personalidade do Leitor")

sentimento_livro = st.radio("Como você gostaria que um livro te fizesse sentir?", [
    "Inspirado e motivado",
    "Reflexivo e pensativo",
    "Empolgado e cheio de adrenalina",
    "Confortável e relaxado",
    "Assustado e intrigado"
])

questoes_sociais = st.radio("Você gosta de livros que abordam questões sociais ou filosóficas?", [
    "Sim, adoro reflexões profundas",
    "Depende do tema",
    "Prefiro histórias mais leves"
])

releitura = st.radio("Você gosta de reler livros ou prefere sempre algo novo?", [
    "Sempre procuro novas leituras",
    "Gosto de reler meus favoritos",
    "Um pouco dos dois"
])

# Seção 4 - Ajustes finais
st.header("4. Ajustes Finais para Recomendação")

formato_livro = st.radio("Você prefere livros físicos ou digitais?", [
    "Físicos",
    "Digitais (Kindle, PDF, etc.)",
    "Tanto faz"
])

influencia = st.radio("O que mais influencia você na escolha de um livro?", [
    "Críticas e resenhas",
    "Recomendações de amigos",
    "Premiações e best-sellers",
    "Sinopse e capa"
])

avaliacoes = st.radio("Gostaria de receber recomendações baseadas em avaliações de outros leitores?", [
    "Sim, me mostre os mais bem avaliados",
    "Prefiro descobertas personalizadas",
    "Tanto faz"
])

audiolivros = st.radio("Você tem interesse em audiolivros?", [
    "Sim, gosto de ouvir livros",
    "Não, prefiro ler",
    "Depende do livro"
])

# Botão de envio
if st.button("Enviar Respostas"):
    st.success("Formulário enviado com sucesso!")

