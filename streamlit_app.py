import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from sqlalchemy import create_engine
import hashlib

# Função para hash da senha
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Cadastro de usuários
def create_user():
    st.subheader("Cadastro de usuário")
    nome = st.text_input("Nome completo")
    username = st.text_input("Nome de usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Criar conta"):
        if nome and username and senha:
            hashed_password = hash_password(senha)
            # Armazenar dados do usuário, como nome, nome de usuário e senha hashada
            st.session_state.users[username] = {"name": nome, "password": hashed_password}
            st.success("Conta criada com sucesso!")
        else:
            st.warning("Preencha todos os campos!")

# Login de usuários
def login_user():
    st.subheader("Login")
    username = st.text_input("Nome de usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Login"):
        if username in st.session_state.users:
            stored_password = st.session_state.users[username]["password"]
            if stored_password == hash_password(senha):
                st.session_state.logged_in = True
                st.session_state.logged_user = username
                st.success(f"Bem-vindo, {st.session_state.users[username]['name']}!")
            else:
                st.error("Senha incorreta")
        else:
            st.error("Usuário não encontrado")

# Inicializando o estado da sessão para armazenar os usuários
if "users" not in st.session_state:
    st.session_state.users = {}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "logged_user" not in st.session_state:
    st.session_state.logged_user = None

# Se o usuário estiver logado, exibe uma mensagem de boas-vindas
if st.session_state.logged_in:
    st.write(f"Olá, {st.session_state.users[st.session_state.logged_user]['name']}!")
else:
    # Caso contrário, oferece a opção de login ou cadastro
    option = st.radio("Escolha uma opção", ("Login", "Criar conta"))

    if option == "Login":
        login_user()
    elif option == "Criar conta":
        create_user()

# Banco de dados PostgreSQL no Render
DATABASE_URL = "postgresql://banco_litmeapp_user:A48TgTYgIwbKtQ1nRSsLA53ipPPphiTj@dpg-d04mhrodl3ps73dh0k7g-a.oregon-postgres.render.com/banco_litmeapp"
engine = create_engine(DATABASE_URL)

# ====== Sistema de Login ======
usernames = ['usuario1', 'usuario2']
passwords = ['senha1', 'senha2']

# Senhas hash para "123" e "456"
hashed_passwords = [stauth.Hasher([senha]).generate()[0] for senha in passwords]

authenticator = stauth.Authenticate(
    usernames=usernames,
    passwords=hashed_passwords,
    cookie_name="cookie_name",
    key="secret_key",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login", "main")
if authentication_status:
    st.write(f"Bem-vindo, {name}!")
else:
    st.error("Login falhou ou usuário não encontrado.")

    st.title("Formulário de Preferências de Leitura")

    # Seção 1 - Hábitos de leitura
    st.header("1. Sobre seus hábitos de leitura")
    frequencia_leitura = st.radio("Com que frequência você costuma ler?", [
        "Todos os dias", "Algumas vezes por semana", "Algumas vezes por mês", "Raramente"])

    tempo_leitura = st.radio("Quanto tempo você geralmente dedica à leitura por sessão?", [
        "Menos de 30 minutos", "30 minutos a 1 hora", "1 a 2 horas", "Mais de 2 horas"])

    local_leitura = st.radio("Onde você costuma ler com mais frequência?", [
        "Em casa", "No transporte público", "Em bibliotecas/cafés", "Outros lugares"])

    # Seção 2 - Preferências de leitura
    st.header("2. Sobre suas preferências de leitura")
    tipo_livro = st.radio("Você prefere livros de ficção ou não ficção?", ["Ficção", "Não ficção", "Gosto dos dois"])

    generos = st.multiselect("Quais gêneros literários você mais gosta? (Escolha até 3)", [
        "Ficção científica", "Fantasia", "Romance", "Mistério/Thriller", "Terror",
        "História", "Biografia", "Desenvolvimento pessoal", "Negócios", "Filosofia", "Outro"])

    genero_outro = ""
    if "Outro" in generos:
        genero_outro = st.text_input("Qual outro gênero?")

    autor_favorito = st.text_input("Você tem algum autor favorito?")

    tamanho_livro = st.radio("Você prefere livros curtos ou longos?", [
        "Curtos (-200 páginas)", "Médios (200-400 páginas)", "Longos (+400 páginas)", "Não tenho preferência"])

    narrativa = st.radio("Como você gosta da narrativa dos livros?", [
        "Ação rápida, cheia de acontecimentos",
        "Narrativa introspectiva, com profundidade emocional",
        "Equilibrado entre ação e introspecção"])

    # Seção 3 - Personalidade do Leitor
    st.header("3. Personalidade do Leitor")
    sentimento_livro = st.radio("Como você gostaria que um livro te fizesse sentir?", [
        "Inspirado e motivado", "Reflexivo e pensativo", "Empolgado e cheio de adrenalina",
        "Confortável e relaxado", "Assustado e intrigado"])

    questoes_sociais = st.radio("Você gosta de livros que abordam questões sociais ou filosóficas?", [
        "Sim, adoro reflexões profundas", "Depende do tema", "Prefiro histórias mais leves"])

    releitura = st.radio("Você gosta de reler livros ou prefere sempre algo novo?", [
        "Sempre procuro novas leituras", "Gosto de reler meus favoritos", "Um pouco dos dois"])

    # Seção 4 - Ajustes finais
    st.header("4. Ajustes Finais para Recomendação")
    formato_livro = st.radio("Você prefere livros físicos ou digitais?", ["Físicos", "Digitais (Kindle, PDF, etc.)", "Tanto faz"])

    influencia = st.radio("O que mais influencia você na escolha de um livro?", [
        "Críticas e resenhas", "Recomendações de amigos", "Premiações e best-sellers", "Sinopse e capa"])

    avaliacoes = st.radio("Gostaria de receber recomendações baseadas em avaliações de outros leitores?", [
        "Sim, me mostre os mais bem avaliados", "Prefiro descobertas personalizadas", "Tanto faz"])

    audiolivros = st.radio("Você tem interesse em audiolivros?", [
        "Sim, gosto de ouvir livros", "Não, prefiro ler", "Depende do livro"])

    # Seção 5 - Interesse em Artigos Acadêmicos
    st.header("5. Interesse em Artigos Acadêmicos")
    interesse_artigos = st.radio("Você tem interesse em artigos acadêmicos ou técnicos?", [
        "Sim, leio frequentemente", "Leio quando necessário", "Não tenho interesse"])

    area_academica = ""
    if interesse_artigos != "Não tenho interesse":
        area_academica = st.text_input("Se sim, quais áreas ou temas você mais se interessa?")

    # Seção 6 - Perfil Cognitivo e de Leitura
    st.header("6. Perfil Cognitivo e de Leitura")
    objetivo_leitura = st.radio("Qual é o seu principal objetivo ao ler?", [
        "Aprender algo novo", "Se entreter e relaxar", "Desenvolvimento pessoal ou profissional",
        "Conectar-se emocionalmente com histórias", "Outros"])

    tipo_conteudo = st.radio("Que tipo de conteúdo você mais consome no dia a dia?", [
        "Livros e textos longos", "Artigos e blogs curtos", "Vídeos no YouTube/TikTok",
        "Podcasts e audiobooks", "Notícias e matérias jornalísticas"])

    nivel_leitura = st.radio("Como você classificaria seu nível de leitura?", [
        "Iniciante – leio pouco ou estou começando", "Intermediário – leio com frequência moderada",
        "Avançado – leio com frequência e gosto de desafios"])

    velocidade = st.radio("Você costuma ler em um ritmo...", [
        "Rápido – gosto de terminar logo", "Moderado – acompanho no meu tempo",
        "Lento – gosto de refletir e analisar"])

    curiosidade = st.radio("Você se considera uma pessoa curiosa sobre temas variados?", [
        "Sim, adoro explorar assuntos novos", "Depende do assunto", "Não muito, gosto de coisas familiares"])

    contexto_cultural = st.radio("Você gosta de livros ambientados em outras culturas, países ou épocas?", [
        "Sim, isso me interessa muito", "Depende do contexto", "Prefiro histórias que se pareçam com minha realidade"])

    memoria = st.radio("Você prefere livros com...", [
        "Tramas simples e fáceis de acompanhar",
        "Histórias complexas, com múltiplos personagens e tempos",
        "Um equilíbrio entre os dois"])

    leitura_em_ingles = st.radio("Você lê livros ou artigos em inglês?", [
        "Sim, frequentemente", "Às vezes, quando necessário", "Não, prefiro conteúdos em português"])

    if st.button("Enviar Respostas"):
        dados = {
            "usuario": username,
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

elif authentication_status == False:
    st.error("Usuário ou senha incorretos")
elif authentication_status is None:
    st.warning("Por favor, insira seu usuário e senha")

