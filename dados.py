import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import openai
import os

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Conexão com o banco de dados no Render
DATABASE_URL = "postgresql://banco_litmeapp_user:A48TgTYgIwbKtQ1nRSsLA53ipPPphiTj@dpg-d04mhrodl3ps73dh0k7g-a.oregon-postgres.render.com/banco_litmeapp"
engine = create_engine(DATABASE_URL)

# API Key da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("📊 Visualização das Respostas do Formulário")

# Função para verificar se o usuário já preencheu o questionário
def verificar_questionario(username):
    if not username:
        st.error("❌ Nome de usuário inválido")
        return False

    try:
        with engine.connect() as conn:
            result = conn.execute(text("""SELECT questionario_preenchido FROM usuarios WHERE username = :username"""), {"username": username}).fetchone()
            if result:
                return result[0]  # 'questionario_preenchido' estará no índice 0 da tupla
            else:
                st.error(f"❌ Usuário '{username}' não encontrado.")
                return False
    except Exception as e:
        st.error(f"❌ Erro ao verificar o questionário: {e}")
        return False

# Função para salvar as respostas no banco de dados
def salvar_respostas(username, respostas):
    try:
        with engine.connect() as conn:
            conn.execute(text("""INSERT INTO respostas_formulario 
                                 (username, frequencia_leitura, tempo_leitura, local_leitura, tipo_livro, generos, 
                                  autor_favorito, tamanho_livro, narrativa, sentimento_livro, questoes_sociais, 
                                  releitura, formato_livro, influencia, avaliacoes, audiolivros, interesse_artigos, 
                                  area_academica, objetivo_leitura, tipo_conteudo, nivel_leitura, velocidade, 
                                  curiosidade, contexto_cultural, memoria, leitura_em_ingles) 
                                 VALUES (:username, :frequencia_leitura, :tempo_leitura, :local_leitura, :tipo_livro, 
                                         :generos, :autor_favorito, :tamanho_livro, :narrativa, :sentimento_livro, 
                                         :questoes_sociais, :releitura, :formato_livro, :influencia, :avaliacoes, 
                                         :audiolivros, :interesse_artigos, :area_academica, :objetivo_leitura, 
                                         :tipo_conteudo, :nivel_leitura, :velocidade, :curiosidade, :contexto_cultural, 
                                         :memoria, :leitura_em_ingles)"""),
                                {"username": username, **respostas})
        st.success("Respostas salvas com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar respostas: {e}")

# Função para marcar que o questionário foi preenchido
def marcar_questionario_preenchido(username):
    try:
        with engine.connect() as conn:
            conn.execute(text("""UPDATE usuarios SET questionario_preenchido = TRUE WHERE username = :username"""), {"username": username})
        st.success("Questionário marcado como preenchido!")
    except Exception as e:
        st.error(f"Erro ao marcar questionário: {e}")

# Função para gerar o perfil de leitura com a OpenAI
def gerar_perfil_leitura(respostas):
    prompt = f"""
    O usuário respondeu ao seguinte questionário sobre seus hábitos de leitura:
    
    Frequência de leitura: {respostas['frequencia_leitura']}
    Tempo de leitura diário: {respostas['tempo_leitura']}
    Local de leitura: {respostas['local_leitura']}
    Tipo de livro preferido: {respostas['tipo_livro']}
    Gêneros literários preferidos: {respostas['generos']}
    Autor favorito: {respostas['autor_favorito']}
    Tamanho de livro preferido: {respostas['tamanho_livro']}
    Narrativa preferida: {respostas['narrativa']}
    Sentimento preferido em livros: {respostas['sentimento_livro']}
    Questões sociais de interesse: {respostas['questoes_sociais']}
    Costuma reler livros? {respostas['releitura']}
    Formato de livro preferido: {respostas['formato_livro']}
    Tipo de influência desejada: {respostas['influencia']}
    Costuma ler avaliações de livros? {respostas['avaliacoes']}
    Gosta de ouvir audiolivros? {respostas['audiolivros']}
    Interesse em artigos sobre livros? {respostas['interesse_artigos']}
    Área acadêmica de interesse: {respostas['area_academica']}
    Objetivo principal com a leitura: {respostas['objetivo_leitura']}
    Tipo de conteúdo de interesse: {respostas['tipo_conteudo']}
    Nível de leitura: {respostas['nivel_leitura']}
    Velocidade de leitura: {respostas['velocidade']}
    Temas de curiosidade: {respostas['curiosidade']}
    Interesse por contextos culturais: {respostas['contexto_cultural']}
    Memória sobre o que leu: {respostas['memoria']}
    Costuma ler em inglês? {respostas['leitura_em_ingles']}
        
    
    Escreva um perfil de leitura dinâmico e personalizado para este usuário, utilizando uma linguagem natural.
    """
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].text.strip()

# Campos de entrada para o nome de usuário
username = st.text_input("Digite seu nome de usuário:")

# Verificar se o usuário já preencheu o questionário
if username:
    if verificar_questionario(username):
        st.title("Perfil de Leitura")
        # Aqui, recuperamos as respostas do banco de dados
        with engine.connect() as conn:
            respostas_usuario = conn.execute(text("""SELECT * FROM respostas_formulario WHERE username = :username"""), {"username": username}).fetchone()

        # Gerar o perfil de leitura com a OpenAI
        perfil = gerar_perfil_leitura(respostas_usuario)
        st.write(perfil)

    else:
        st.title("Preencha o Formulário")
        frequencia_leitura = st.selectbox("Qual a frequência de leitura?", ["Diariamente", "Semanalmente", "Mensalmente"])
        tempo_leitura = st.text_input("Quanto tempo você dedica à leitura por dia?")
        local_leitura = st.text_input("Onde você costuma ler?")
        tipo_livro = st.text_input("Que tipo de livros você mais gosta?")
        generos = st.text_input("Quais gêneros literários você prefere?")
        autor_favorito = st.text_input("Quem é seu autor favorito?")
        tamanho_livro = st.text_input("Qual o tamanho de livro que você prefere?")
        narrativa = st.text_input("Você prefere livros com narrativa em primeira ou terceira pessoa?")
        sentimento_livro = st.text_input("Qual o sentimento que você mais gosta de explorar nos livros?")
        questoes_sociais = st.text_input("Quais questões sociais você mais se interessa em livros?")
        releitura = st.text_input("Você costuma reler livros?")
        formato_livro = st.selectbox("Qual formato de livro você prefere?", ["Físico", "Digital", "Audiobook"])
        influencia = st.text_input("Que tipo de influência você gostaria de ver nos livros?")
        avaliacoes = st.text_input("Você costuma ler avaliações de livros antes de escolher?")
        audiolivros = st.selectbox("Você gosta de ouvir audiolivros?", ["Sim", "Não"])
        interesse_artigos = st.selectbox("Você tem interesse em artigos sobre livros?", ["Sim", "Não"])
        area_academica = st.text_input("Você tem alguma área acadêmica de interesse em livros?")
        objetivo_leitura = st.text_input("Qual o seu principal objetivo com a leitura?")
        tipo_conteudo = st.text_input("Qual tipo de conteúdo você mais se interessa?")
        nivel_leitura = st.text_input("Qual o seu nível de leitura? (iniciante, intermediário, avançado)")
        velocidade = st.text_input("Qual a sua velocidade de leitura? (rápida, moderada, lenta)")
        curiosidade = st.text_input("Quais temas você tem mais curiosidade em explorar nos livros?")
        contexto_cultural = st.text_input("Você se interessa por livros que exploram diferentes contextos culturais?")
        memoria = st.text_input("Você se lembra facilmente do que leu nos livros?")
        leitura_em_ingles = st.selectbox("Você costuma ler livros em inglês?", ["Sim", "Não"])
        
        # Quando o formulário for preenchido
        if st.button("Salvar Respostas"):
            respostas = {
                "frequencia_leitura": frequencia_leitura,
                "tempo_leitura": tempo_leitura,
                "local_leitura": local_leitura,
                "tipo_livro": tipo_livro,
                "generos": generos,
                "autor_favorito": autor_favorito,
                "tamanho_livro": tamanho_livro,
                "narrativa": narrativa,
                "sentimento_livro": sentimento_livro,
                "questoes_sociais": questoes_sociais,
                "releitura": releitura,
                "formato_livro": formato_livro,
                "influencia": influencia,
                "avaliacoes": avaliacoes,
                "audiolivros": audiolivros,
                "interesse_artigos": interesse_artigos,
                "area_academica": area_academica,
                "objetivo_leitura": objetivo_leitura,
                "tipo_conteudo": tipo_conteudo,
                "nivel_leitura": nivel_leitura,
                "velocidade": velocidade,
                "curiosidade": curiosidade,
                "contexto_cultural": contexto_cultural,
                "memoria": memoria,
                "leitura_em_ingles": leitura_em_ingles,
            }

            # Salvar as respostas no banco de dados
            salvar_respostas(username, respostas)

            # Marcar o formulário como preenchido
            marcar_questionario_preenchido(username)

            st.success("Respostas salvas com sucesso!")
else:
    st.warning("Por favor, insira um nome de usuário válido.")
