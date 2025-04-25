import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from sqlalchemy import create_engine
import hashlib

# ========== CONFIGURAÇÕES DE CONEXÃO COM BANCO ==========
DATABASE_URL = "postgresql://banco_litmeapp_user:A48TgTYgIwbKtQ1nRSsLA53ipPPphiTj@dpg-d04mhrodl3ps73dh0k7g-a.oregon-postgres.render.com/banco_litmeapp"
engine = create_engine(DATABASE_URL)

# ========== FUNÇÕES AUXILIARES ==========
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_user():
    st.subheader("Login")
    username = st.text_input("Nome de usuário", key="login_user")
    senha = st.text_input("Senha", type="password", key="login_pass")
    
    if st.button("Entrar"):
        if username in st.session_state.users:
            senha_hash = hash_password(senha)
            if st.session_state.users[username]["password"] == senha_hash:
                st.session_state.logged_in = True
                st.session_state.logged_user = username
                st.success("Login realizado com sucesso!")
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não encontrado.")

def create_user():
    st.subheader("Cadastro de Usuário")

    if "users" not in st.session_state:
        st.session_state.users = {}

    nome = st.text_input("Nome completo")
    username = st.text_input("Nome de usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Criar conta"):
        if nome and username and senha:
            if username in st.session_state.users:
                st.warning("Nome de usuário já existe. Escolha outro.")
            else:
                hashed_password = hash_password(senha)
                st.session_state.users[username] = {"name": nome, "password": hashed_password}
                st.success("Conta criada com sucesso!")
        else:
            st.warning("Preencha todos os campos!")

# ========== INICIALIZAÇÃO DO ESTADO ==========
if "users" not in st.session_state:
    st.session_state.users = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "logged_user" not in st.session_state:
    st.session_state.logged_user = None

# ========== LOGIN OU CADASTRO ==========
if not st.session_state.logged_in:
    opcao = st.radio("Escolha uma opção", ("Login", "Criar conta"))

    if opcao == "Login":
        login_user()
    elif opcao == "Criar conta":
        create_user()
else:
    st.write(f"Olá, {st.session_state.users[st.session_state.logged_user]['name']}!")

    # ========== FORMULÁRIO ==========
    st.title("Formulário de Preferências de Leitura")

    st.header("1. Sobre seus hábitos de leitura")
    frequencia_leitura = st.radio("Com que frequência você costuma ler?", ["Todos os dias", "Algumas vezes por semana", "Algumas vezes por mês", "Raramente"])
    tempo_leitura = st.radio("Quanto tempo você geralmente dedica à leitura por sessão?", ["Menos de 30 minutos", "30 minutos a 1 hora", "1 a 2 horas", "Mais de 2 horas"])
    local_leitura = st.radio("Onde você costuma ler com mais frequência?", ["Em casa", "No transporte público", "Em bibliotecas/cafés", "Outros lugares"])

    st.header("2. Sobre suas preferências de leitura")
    tipo_livro = st.radio("Você prefere livros de ficção ou não ficção?", ["Ficção", "Não ficção", "Gosto dos dois"])
    generos = st.multiselect("Quais gêneros literários você mais gosta? (Escolha até 3)", [
        "Ficção científica", "Fantasia", "Romance", "Mistério/Thriller", "Terror",
        "História", "Biografia", "Desenvolvimento pessoal", "Negócios", "Filosofia", "Outro"
    ])
    genero_outro = st.text_input("Qual outro gênero?") if "Outro" in generos else ""
    autor_favorito = st.text_input("Você tem algum autor favorito?")
    tamanho_livro = st.radio("Você prefere livros curtos ou longos?", ["Curtos (-200 páginas)", "Médios (200-400 páginas)", "Longos (+400 páginas)", "Não tenho preferência"])
    narrativa = st.radio("Como você gosta da narrativa dos livros?", ["Ação rápida", "Narrativa introspectiva", "Equilibrado"])

    st.header("3. Personalidade do Leitor")
    sentimento_livro = st.radio("Como você gostaria que um livro te fizesse sentir?", [
        "Inspirado", "Reflexivo", "Empolgado", "Confortável", "Assustado"
    ])
    questoes_sociais = st.radio("Você gosta de livros que abordam questões sociais ou filosóficas?", [
        "Sim", "Depende do tema", "Prefiro histórias leves"
    ])
    releitura = st.radio("Você gosta de reler livros?", ["Sempre procuro novas leituras", "Gosto de reler", "Um pouco dos dois"])

    st.header("4. Ajustes Finais")
    formato_livro = st.radio("Você prefere livros físicos ou digitais?", ["Físicos", "Digitais", "Tanto faz"])
    influencia = st.radio("O que mais influencia você na escolha de um livro?", [
        "Críticas", "Recomendações", "Premiações", "Sinopse e capa"
    ])
    avaliacoes = st.radio("Quer recomendações baseadas em avaliações?", [
        "Sim", "Prefiro personalizadas", "Tanto faz"
    ])
    audiolivros = st.radio("Você tem interesse em audiolivros?", ["Sim", "Não", "Depende do livro"])

    st.header("5. Interesse em Artigos Acadêmicos")
    interesse_artigos = st.radio("Você tem interesse em artigos acadêmicos?", ["Sim", "Leio quando necessário", "Não"])
    area_academica = st.text_input("Quais áreas te interessam?") if interesse_artigos != "Não" else ""

    st.header("6. Perfil Cognitivo e de Leitura")
    objetivo_leitura = st.radio("Qual seu principal objetivo ao ler?", [
        "Aprender", "Se entreter", "Desenvolvimento pessoal", "Conexão emocional", "Outros"
    ])
    tipo_conteudo = st.radio("Que tipo de conteúdo consome no dia a dia?", [
        "Livros longos", "Artigos", "Vídeos", "Podcasts", "Notícias"
    ])
    nivel_leitura = st.radio("Seu nível de leitura:", ["Iniciante", "Intermediário", "Avançado"])
    velocidade = st.radio("Seu ritmo de leitura:", ["Rápido", "Moderado", "Lento"])
    curiosidade = st.radio("Você é curioso sobre temas variados?", ["Sim", "Depende", "Não muito"])
    contexto_cultural = st.radio("Gosta de livros com outras culturas/épocas?", ["Sim", "Depende", "Prefiro histórias próximas"])
    memoria = st.radio("Você prefere livros com...", [
        "Tramas simples", "Histórias complexas", "Equilíbrio"
    ])
    leitura_em_ingles = st.radio("Você lê em inglês?", ["Sim", "Às vezes", "Não"])

    if st.button("Enviar Respostas"):
        dados = {
            "usuario": st.session_state.logged_user,
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
            "leitura_em_ingles": leitura_em_ingles
        }

        df = pd.DataFrame([dados])
        df.to_sql("respostas_formulario", engine, if_exists="append", index=False)
        st.success("Formulário enviado com sucesso! ✅")