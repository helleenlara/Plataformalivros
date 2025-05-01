import streamlit as st
import pandas as pd
import hashlib
import os
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, text

# Carrega variáveis de ambiente
dotenv_path = os.path.join(os.getcwd(), '.env')
load_dotenv(dotenv_path)

# Verifica se a variável DATABASE_URL foi carregada corretamente
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("A variável de ambiente 'DATABASE_URL' não foi encontrada no arquivo .env")

# Criação do motor de conexão com o banco de dados
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})

# -------------------------------
# Funções auxiliares
# -------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_ou_criar_tabela_usuarios():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                username TEXT PRIMARY KEY,
                nome TEXT,
                senha_hash TEXT
            );
        """))

def cadastrar_usuario(username, nome, senha):
    senha_hash = hash_password(senha)
    with engine.begin() as conn:  # garante commit automático
        conn.execute(text("""
            INSERT INTO usuarios (username, nome, senha_hash)
            VALUES (:username, :nome, :senha_hash)
        """), {
            "username": username,
            "nome": nome,
            "senha_hash": senha_hash
        })

def autenticar_usuario(username, senha):
    senha_hash = hash_password(senha)
    with engine.connect() as conn:
        return conn.execute(text("""
            SELECT username, nome FROM usuarios
            WHERE username = :username AND senha_hash = :senha_hash
        """), {"username": username, "senha_hash": senha_hash}).fetchone()

def usuario_ja_respondeu_formulario(username):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 1 FROM respostas_formulario WHERE usuario = :username LIMIT 1
        """), {"username": username}).fetchone()
        return result is not None

# -------------------------------
# Setup inicial
# -------------------------------
st.set_page_config(page_title="Plataforma de Livros", layout="wide")
verificar_ou_criar_tabela_usuarios()

# -------------------------------
# Seção de autenticação
# -------------------------------
if "logged_user" not in st.session_state:
    st.sidebar.title("🔐 Autenticação")
    tab_login, tab_signup = st.sidebar.tabs(["Login", "Cadastrar"])

    with tab_login:
        st.subheader("Login")
        login_user = st.text_input("Usuário", key="login_user")
        login_pass = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar", key="btn_login"):
            user = autenticar_usuario(login_user, login_pass)
            if user:
                st.session_state.logged_user = user.username
                st.session_state.logged_name = user.nome
                st.success(f"Bem-vindo(a), {user.nome}!")
            else:
                st.error("Usuário ou senha incorretos.")

    with tab_signup:
        st.subheader("Cadastrar")
        new_user = st.text_input("Usuário", key="new_user")
        new_name = st.text_input("Nome", key="new_name")
        new_pass = st.text_input("Senha", type="password", key="new_pass")
        if st.button("Cadastrar", key="btn_signup"):
            try:
                cadastrar_usuario(new_user, new_name, new_pass)
                st.success("Conta criada! Faça login.")
            except IntegrityError:
                st.error("Este usuário já existe. Escolha outro.")
else:
    st.sidebar.write(f"👤 {st.session_state.logged_name}")
    if st.sidebar.button("Logout", key="btn_logout"):
        del st.session_state.logged_user
        del st.session_state.logged_name
        st.experimental_rerun()

    # ==== Formulário de Preferências de Leitura ====
    st.title("Formulário de Preferências de Leitura")

    st.header("1. Sobre seus hábitos de leitura")
    frequencia_leitura = st.radio("Com que frequência você costuma ler?", ["Todos os dias", "Algumas vezes por semana", "Algumas vezes por mês", "Raramente"])
    tempo_leitura = st.radio("Quanto tempo você geralmente dedica à leitura por sessão?", ["Menos de 30 minutos", "30 minutos a 1 hora", "1 a 2 horas", "Mais de 2 horas"])
    local_leitura = st.radio("Onde você costuma ler com mais frequência?", ["Em casa", "No transporte público", "Em bibliotecas/cafés", "Outros lugares"])

    st.header("2. Sobre suas preferências de leitura")
    tipo_livro = st.radio("Você prefere livros de ficção ou não ficção?", ["Ficção", "Não ficção", "Gosto dos dois"])
    generos = st.multiselect("Quais gêneros literários você mais gosta? (Escolha até 3)", ["Ficção científica", "Fantasia", "Romance", "Mistério/Thriller", "Terror", "História", "Biografia", "Desenvolvimento pessoal", "Negócios", "Filosofia", "Outro"])
    genero_outro = ""
    if "Outro" in generos:
        genero_outro = st.text_input("Qual outro gênero?")
    autor_favorito = st.text_input("Você tem algum autor favorito?")
    tamanho_livro = st.radio("Você prefere livros curtos ou longos?", ["Curtos (-200 páginas)", "Médios (200-400 páginas)", "Longos (+400 páginas)", "Não tenho preferência"])
    narrativa = st.radio("Como você gosta da narrativa dos livros?", ["Ação rápida, cheia de acontecimentos", "Narrativa introspectiva, com profundidade emocional", "Equilibrado entre ação e introspecção"])

    st.header("3. Personalidade do Leitor")
    sentimento_livro = st.radio("Como você gostaria que um livro te fizesse sentir?", ["Inspirado e motivado", "Reflexivo e pensativo", "Empolgado e cheio de adrenalina", "Confortável e relaxado", "Assustado e intrigado"])
    questoes_sociais = st.radio("Você gosta de livros que abordam questões sociais ou filosóficas?", ["Sim, adoro reflexões profundas", "Depende do tema", "Prefiro histórias mais leves"])
    releitura = st.radio("Você gosta de reler livros ou prefere sempre algo novo?", ["Sempre procuro novas leituras", "Gosto de reler meus favoritos", "Um pouco dos dois"])

    st.header("4. Ajustes Finais para Recomendação")
    formato_livro = st.radio("Você prefere livros físicos ou digitais?", ["Físicos", "Digitais (Kindle, PDF, etc.)", "Tanto faz"])
    influencia = st.radio("O que mais influencia você na escolha de um livro?", ["Críticas e resenhas", "Recomendações de amigos", "Premiações e best-sellers", "Sinopse e capa"])
    avaliacoes = st.radio("Gostaria de receber recomendações baseadas em avaliações de outros leitores?", ["Sim, me mostre os mais bem avaliados", "Prefiro descobertas personalizadas", "Tanto faz"])
    audiolivros = st.radio("Você tem interesse em audiolivros?", ["Sim, gosto de ouvir livros", "Não, prefiro ler", "Depende do livro"])

    st.header("5. Interesse em Artigos Acadêmicos")
    interesse_artigos = st.radio("Você tem interesse em artigos acadêmicos ou técnicos?", ["Sim, leio frequentemente", "Leio quando necessário", "Não tenho interesse"])
    area_academica = ""
    if interesse_artigos != "Não tenho interesse":
        area_academica = st.text_input("Se sim, quais áreas ou temas você mais se interessa?")

    st.header("6. Perfil Cognitivo e de Leitura")
    objetivo_leitura = st.radio("Qual é o seu principal objetivo ao ler?", ["Aprender algo novo", "Se entreter e relaxar", "Desenvolvimento pessoal ou profissional", "Conectar-se emocionalmente com histórias", "Outros"])
    tipo_conteudo = st.radio("Que tipo de conteúdo você mais consome no dia a dia?", ["Livros e textos longos", "Artigos e blogs curtos", "Vídeos no YouTube/TikTok", "Podcasts e audiobooks", "Notícias e matérias jornalísticas"])
    nivel_leitura = st.radio("Como você classificaria seu nível de leitura?", ["Iniciante – leio pouco ou estou começando", "Intermediário – leio com frequência moderada", "Avançado – leio com frequência e gosto de desafios"])
    velocidade = st.radio("Você costuma ler em um ritmo...", ["Rápido – gosto de terminar logo", "Moderado – acompanho no meu tempo", "Lento – gosto de refletir e analisar"])
    curiosidade = st.radio("Você se considera uma pessoa curiosa sobre temas variados?", ["Sim, adoro explorar assuntos novos", "Depende do assunto", "Não muito, gosto de coisas familiares"])
    contexto_cultural = st.radio("Você gosta de livros ambientados em outras culturas, países ou épocas?", ["Sim, isso me interessa muito", "Depende do contexto", "Prefiro histórias que se pareçam com minha realidade"])
    memoria = st.radio("Você prefere livros com...", ["Tramas simples e fáceis de acompanhar", "Histórias complexas, com múltiplos personagens e tempos", "Um equilíbrio entre os dois"])
    leitura_em_ingles = st.radio("Você lê livros ou artigos em inglês?", ["Sim, frequentemente", "Às vezes, quando necessário", "Não, prefiro conteúdos em português"])

    if st.button("Enviar Respostas", key="btn_submit"):
        if usuario_ja_respondeu_formulario(st.session_state.logged_user):
            st.warning("Você já enviou suas preferências anteriormente. Caso deseje atualizar, isso será implementado em breve.")
        else:
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

    st.info("🛠️ A geração do perfil de leitura está temporariamente desativada.")
