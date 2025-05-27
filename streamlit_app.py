import streamlit as st
import pandas as pd
import hashlib
import os
import json
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, text
import google.generativeai as genai
from pathlib import Path
from wordcloud import WordCloud
from datetime import datetime
from gamificacao import (
    registrar_leitura,
    mostrar_status,
    verificar_conquistas,
    mostrar_conquistas,
    ranking_top,
    desafio_ativo,
    validar_desafio,
    calcular_pontos_e_nivel # Importar a função para usar diretamente
)

# Configuração da página
st.set_page_config(page_title="Plataforma LitMe", layout="wide")

# Estilo personalizado
st.markdown("""
    <style>
        .main {
            background-color: #E9E5DB !important;
        }
        .st-emotion-cache-uf99v8.e1g8pov61 {
            background-color: #E9E5DB !important;
        }
        body {
            background-color: #E9E5DB !important;
        }

        h1, h2, h3 {
            color: #1C5F5A;
        }
        .stButton>button {
            color: white;
            background-color: #1C5F5A;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            margin-top: 15px;
            cursor: pointer;
        }
        .main .block-container {
            padding-left: 2rem;
            padding-right: 2rem;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .stTabs [data-testid="stTab"] {
            font-size: 18px;
            font-weight: bold;
            color: #1C5F5A;
        }
        .stTabs [data-testid="stTab"][aria-selected="true"] {
            border-bottom-color: #1C5F5A;
            color: #1C5F5A;
        }
        section[data-testid="stSidebarV1"] {
            display: flex;
            visibility: visible;
            transform: translateX(0%);
            transition: transform 300ms ease-in-out;
             background-color: #E9E5DB;
        }
        .st-emotion-cache-1jm6g9l.e1g8pov60 {
            display: none !important;
        }
        .st-emotion-cache-zkj8ys.e1g8pov61 {
            display: none !important;
        }
        .st-emotion-cache-uf99v8.e1g8pov61 {
            padding-right: 1rem;
            padding-left: 1rem;
        }
        .stTextInput, .stSelectbox, .stRadio, .stMultiSelect {
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        div.stButton {
            display: flex;
            justify-content: center;
        }
        .element-container .stMarkdown, .element-container .stAlert {
            text-align: center;
            width: 100%;
            margin-left: auto;
            margin-right: auto;
        }
        h1.css-10trblm.e16nr0p30 {
            text-align: center;
            width: 100%;
        }

        .justified-text {
            text-align: justify;
        }

        .highlight-container {
            border: 2px solid #1C5F5A;
            border-radius: 10px;
            padding: 20px;
            margin: 20px auto;
            background-color: #F8F5EE;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            text-align: center;
        }
        .highlight-container .stButton button {
            background-color: #28a745;
            color: white;
            font-weight: bold;
            border: 2px solid #218838;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            transform: scale(1.05);
            transition: all 0.2s ease-in-out;
            width: 80%;
            max-width: 300px;
        }
        .highlight-container .stButton button:hover {
            background-color: #218838;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
            transform: scale(1.07);
        }
    </style>
""", unsafe_allow_html=True)

# Carregar variáveis de ambiente
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if DATABASE_URL is None:
    raise ValueError("A variável DATABASE_URL não foi encontrada.")
if gemini_api_key is None:
    raise ValueError("A variável GEMINI_API_KEY não foi encontrada.")

engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})

# Funções auxiliares
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verificar_ou_criar_tabela_usuarios():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                username TEXT PRIMARY KEY,
                nome TEXT,
                senha_hash TEXT
            );
        """))

def cadastrar_usuario(username, nome, senha):
    senha_hash = hash_password(senha)
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO usuarios (username, nome, senha_hash)
            VALUES (:username, :nome, :senha_hash)
        """), {"username": username, "nome": nome, "senha_hash": senha_hash})

def autenticar_usuario(username, senha):
    senha_hash = hash_password(senha)
    with engine.connect() as conn:
        return conn.execute(text("""
            SELECT username, nome FROM usuarios
            WHERE username = :username AND senha_hash = :senha_hash
        """), {"username": username, "senha_hash": senha_hash}).fetchone()

def salvar_resposta(usuario, dados_dict, perfil_gerado):
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS respostas_formulario (
                usuario TEXT PRIMARY KEY,
                dados TEXT,
                perfil_gerado TEXT
            );
        """))
        conn.execute(text("""
            INSERT INTO respostas_formulario (usuario, dados, perfil_gerado)
            VALUES (:usuario, :dados, :perfil)
            ON CONFLICT (usuario) DO UPDATE
            SET dados = :dados, perfil_gerado = :perfil
        """), {
            "usuario": usuario,
            "dados": dados_dict if isinstance(dados_dict, str) else json.dumps(dados_dict),
            "perfil": perfil_gerado
        })

def buscar_resposta_existente(usuario):
    with engine.connect() as conn:
        return conn.execute(text("""
            SELECT dados, perfil_gerado FROM respostas_formulario
            WHERE usuario = :usuario
        """), {"usuario": usuario}).fetchone()

def carregar_dados():
    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT * FROM respostas_formulario", conn)
            if "dados" in df.columns:
                df["dados"] = df["dados"].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)
                dados_dicts = df["dados"].apply(json.loads).apply(pd.Series)
                df = pd.concat([df.drop(columns=["dados"]), dados_dicts], axis=1)
            return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados do banco: {e}")
        return pd.DataFrame()

# Painel do Escritor Conteúdo
def painel_escritor_conteudo():
    st.header("✍️ Painel do Escritor")
    st.markdown("""
    <div class="justified-text">
    Este painel utiliza conceitos de **Big Data em Python** para fornecer insights úteis a escritores,
    baseando-se nas preferências reais dos leitores coletadas pela plataforma.
    </div>
    """, unsafe_allow_html=True)

    try:
        df = carregar_dados()
        if df.empty:
            st.warning("Ainda não há dados suficientes para análise.")
            st.info("Convide mais leitores para preencherem o formulário de preferências para que a análise de dados seja mais rica!")
            return
    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {e}")
        return

    faixa_etaria_opcao = st.selectbox("Filtrar por faixa etária:", ["Todas"] + sorted(df["idade"].dropna().unique().tolist()))
    if faixa_etaria_opcao != "Todas":
        df = df[df["idade"] == faixa_etaria_opcao]

    st.subheader("📊 Análise Estatística dos Leitores")
    col1, col2 = st.columns(2)
    with col1:
        if "formato_livro" in df.columns:
            st.markdown("### Formato de Leitura Preferido")
            st.bar_chart(df["formato_livro"].value_counts())

    with col2:
        if "generos" in df.columns:
            generos_series = df["generos"].str.split(", ").explode()
            st.markdown("### Gêneros Literários Mais Citados")
            st.bar_chart(generos_series.value_counts())

    col3, col4 = st.columns(2)
    with col3:
        if "objetivo_leitura" in df.columns:
            st.markdown("### Objetivo de Leitura")
            st.bar_chart(df["objetivo_leitura"].value_counts())

    with col4:
        if "sentimento_livro" in df.columns:
            st.markdown("### Sentimentos Desejados")
            st.bar_chart(df["sentimento_livro"].value_counts())

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Baixar dados filtrados (.csv)", data=csv, file_name="dados_filtrados.csv", mime="text/csv")

    st.header("💡 Sugestões para Escrita com IA")

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        chat = model.start_chat()

        textos = " ".join(df["perfil_gerado"].dropna()).lower().strip()

        if not textos:
            st.warning("⚠️ Não há perfis suficientes para análise para a IA.")
            return

        data_atual = datetime.now().strftime("%B de %Y")

        if faixa_etaria_opcao == "Todas":
            prompt = (
                f"Hoje é {data_atual}. Você é um consultor literário com acesso a perfis reais de leitores brasileiros.\n\n"
                "Seu objetivo é ajudar escritores a adaptar seus textos para alcançar o público com mais impacto.\n"
                "Analise os perfis abaixo e identifique:\n\n"
                "1. Temas e assuntos mais valorizados pelos leitores.\n"
                "2. Estilos narrativos preferidos (ex: introspectivo, emocionante, com reviravoltas, etc).\n"
                "3. Emoções ou sensações que o público busca nos livros.\n"
                "4. Padrões de interesse e preferências recorrentes.\n\n"
                "**Com base nisso, gere recomendações práticas para escritores**, como por exemplo:\n"
                "- Que tipo de enredo desenvolver\n"
                "- Que tipo de linguagem utilizar\n"
                "- Que tipos de personagens criar\n"
                "- Como conectar emocionalmente com esse público\n\n"
                "**Apenas forneça as recomendações. Não faça perguntas nem continue a conversa.**\n\n"
                f"Aqui estão os perfis dos leitores:\n{textos}"
            )
        else:
            prompt = (
                f"Hoje é {data_atual}. Você é um consultor literário com acesso a perfis reais de leitores brasileiros da faixa etária: {faixa_etaria_opcao}.\n\n"
                "Seu objetivo é ajudar escritores a adaptar seus textos para alcançar esse público com mais impacto.\n"
                "Analise os perfis abaixo e identifique:\n\n"
                "1. Temas e assuntos mais valorizados pelos leitores dessa faixa etária.\n"
                "2. Estilos narrativos preferidos.\n"
                "3. Emoções ou sensações desejadas.\n"
                "4. Padrões de interesse e preferências específicas dessa faixa.\n\n"
                "**Com base nisso, gere recomendações práticas para escritores**, como:\n"
                "- Enredos sugeridos\n"
                "- Estilo de escrita\n"
                "- Gatilhos emocionais\n"
                "- Gêneros ideais para esse público\n\n"
                "**Apenas forneça as recomendações. Não faça perguntas nem continue a conversa.**\n\n"
                f"Aqui estão os perfis dos leitores:\n{textos}"
            )

        response = chat.send_message(prompt.strip())
        st.markdown("### 💡 Análise Gerada pela IA")
        st.markdown(f'<div class="justified-text">{response.text}</div>', unsafe_allow_html=True)
        st.download_button("⬇️ Baixar Análise", data=response.text, file_name="analise_ia.txt")

    except Exception as e:
        st.warning(f"❌ Erro na análise com IA: {e}")

# Lógica Principal da Aplicação
verificar_ou_criar_tabela_usuarios()

if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

if "logged_user" not in st.session_state and st.session_state.current_page == "login":
    col_left_login, col_center_login, col_right_login = st.columns([1, 2, 1])

    with col_center_login:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("static/litme logo wo bg.png", width=250)

        st.title("Bem-vindo(a) à Plataforma LitMe!")
        st.info("Sua jornada literária começa aqui. Faça login ou cadastre-se, ou explore o Painel do Escritor como visitante.")

        aba_login, aba_cadastro, aba_visitante = st.tabs(["🔐 Login", "📝 Cadastrar", "✍️ Painel do Escritor (Visitante)"])

        with aba_login:
            st.subheader("Acesse sua Conta")
            login_user = st.text_input("Nome de Usuário", key="login_user_main")
            login_pass = st.text_input("Senha", type="password", key="login_pass_main")
            if st.button("Entrar", key="btn_login_main"):
                user = autenticar_usuario(login_user, login_pass)
                if user:
                    st.session_state.logged_user = user.username
                    st.session_state.logged_name = user.nome
                    st.session_state.current_page = "leitor"
                    st.success(f"Bem-vindo(a), {user.nome}! Redirecionando...")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

        with aba_cadastro:
            st.subheader("Crie sua Conta")
            new_user = st.text_input("Escolha um Nome de Usuário", key="new_user_main")
            new_name = st.text_input("Seu Nome Completo", key="new_name_main")
            new_pass = st.text_input("Escolha uma Senha", type="password", key="signup_pass_main")
            if st.button("Cadastrar", key="btn_signup_main"):
                try:
                    cadastrar_usuario(new_user, new_name, new_pass)
                    st.success("Conta criada com sucesso! Agora você pode fazer login.")
                except IntegrityError:
                    st.error("Este usuário já existe. Escolha outro nome de usuário.")

        with aba_visitante:
            st.subheader("Explore o Painel do Escritor")
            st.info("Acesse insights e análises de dados de leitura sem precisar criar uma conta. **Funcionalidades de gravação ou personalização não estarão disponíveis.**")

            if st.button("Acessar Painel do Escritor", key="btn_visitor_writer_panel"):
                st.session_state.current_page = "painel_escritor_visitante"
                st.rerun()

elif st.session_state.current_page == "painel_escritor_visitante" and "logged_user" not in st.session_state:
    col_left_visitor, col_center_visitor, col_right_visitor = st.columns([1, 2, 1])
    with col_center_visitor:
        col1_v, col2_v, col3_v = st.columns([1, 2, 1])
        with col2_v:
            st.image("static/litme logo wo bg.png", width=100)

        st.title("✍️ Painel do Escritor (Modo Visitante)")
        st.info("Você está visualizando o painel do escritor no modo visitante. Para ter acesso completo e outras funcionalidades, por favor, faça login ou cadastre-se.")
        if st.button("Voltar para Login", key="btn_back_to_login"):
            st.session_state.current_page = "login"
            st.rerun()
        st.markdown("---")
        painel_escritor_conteudo()
        st.markdown("---")
        st.info("Para ter acesso completo e outras funcionalidades, por favor, faça login ou cadastre-se.")
        if st.button("Ir para Login/Cadastro", key="btn_go_to_login_bottom"):
            st.session_state.current_page = "login"
            st.rerun()

else:
    with st.sidebar:
        st.image("static/logo_litme.jpg", use_container_width=True)
        st.write(f"👤 **Bem-vindo(a):** {st.session_state.logged_name}")
        if st.button("Logout", key="btn_logout_sidebar"):
            for key in ["logged_user", "logged_name", "form_submitted", "perfil", "current_page"]:
                st.session_state.pop(key, None)
            st.session_state.current_page = "login"
            st.rerun()
        st.markdown("---")
        st.subheader("Navegação")
        if "pagina_selecionada" not in st.session_state:
            st.session_state.pagina_selecionada = "📖 Perfil do Leitor"

        pagina = st.radio("Escolha uma seção:",
                            ["📖 Perfil do Leitor", "🎮 Gamificação", "✍️ Painel do Escritor"],
                            index=["📖 Perfil do Leitor", "🎮 Gamificação", "✍️ Painel do Escritor"].index(st.session_state.pagina_selecionada))
        st.session_state.pagina_selecionada = pagina

    if pagina == "📖 Perfil do Leitor":
        st.header("📖 Seu Perfil Literário Detalhado")
        resposta_existente = buscar_resposta_existente(st.session_state.logged_user)
        if resposta_existente and "form_submitted" not in st.session_state:
            st.session_state.form_submitted = True
            st.session_state.perfil = resposta_existente.perfil_gerado

        if "form_submitted" not in st.session_state:
            st.subheader("📋 Formulário de Preferências de Leitura")
            st.info("Por favor, preencha este formulário para que possamos entender suas preferências e gerar um perfil literário para você.")

            col_left, col_form, col_right = st.columns([1, 3, 1])

            with col_form:
                # Seção 1: Dados Demográficos e Hábitos de Leitura
                st.subheader("Sua Leitura")
                col_idade, col_freq = st.columns(2)
                with col_idade:
                    idade = st.selectbox("Faixa etária:", [""] + ["Menor de 18", "18 a 24", "25 a 34", "35 a 44", "45 a 60", "Acima de 60"], index=0)
                with col_freq:
                    frequencia_leitura = st.radio("Frequência de leitura", [""] + ["Todos os dias", "Algumas vezes por semana", "Algumas vezes por mês", "Raramente"], index=0)

                col_tempo, col_local = st.columns(2)
                with col_tempo:
                    tempo_leitura = st.radio("Tempo por sessão", [""] + ["Menos de 30 minutos", "30 minutos a 1 hora", "1 a 2 horas", "Mais de 2 horas"], index=0)
                with col_local:
                    local_leitura = st.radio("Onde você lê?", [""] + ["Em casa", "No transporte público", "Em bibliotecas/cafés", "Outros lugares"], index=0)
                st.markdown("---") # Divisão aqui

                # Seção 2: Preferências de Gênero e Autoria
                st.subheader("Gêneros e Autores")
                col_tipo, col_generos = st.columns(2)
                with col_tipo:
                    tipo_livro = st.radio("Prefere ficção ou não ficção?", [""] + ["Ficção", "Não ficção", "Gosto dos dois"], index=0)
                with col_generos:
                    generos = st.multiselect("Gêneros favoritos (selecione um ou mais):", ["Ficção científica", "Fantasia", "Romance", "Mistério/Thriller", "Terror", "História", "Biografia", "Desenvolvimento pessoal", "Negócios", "Filosofia", "Outro"])
                genero_outro = st.text_input("Qual outro gênero?", key="genero_outro_input") if "Outro" in generos else ""

                # Lógica para Autor Favorito
                tem_autor_favorito = st.radio("Você tem um autor favorito?", ["", "Sim", "Não"], index=0, key="tem_autor_favorito")
                autor_favorito = ""
                if tem_autor_favorito == "Sim":
                    autor_favorito = st.text_input("Qual o nome do seu autor favorito?", key="qual_autor_favorito")
                st.markdown("---") # Divisão aqui

                # Seção 3: Estilo e Formato de Leitura
                st.subheader("Estilo e Formato")
                col_tamanho, col_narrativa = st.columns(2)
                with col_tamanho:
                    tamanho_livro = st.radio("Tamanho preferido", [""] + ["Curtos (-200 páginas)", "Médios (200-400 páginas)", "Longos (+400 páginas)", "Não tenho preferência"], index=0)
                with col_narrativa:
                    narrativa = st.radio("Estilo de narrativa", [""] + ["Ação rápida", "Narrativa introspectiva", "Equilibrado entre os dois"], index=0)

                col_sentimento, col_sociais = st.columns(2)
                with col_sentimento:
                    sentimento_livro = st.radio("Sentimento desejado ao ler", [""] + ["Inspirado", "Reflexivo", "Empolgado", "Confortável", "Assustado"], index=0)
                with col_sociais:
                    questoes_sociais = st.radio("Gosta de temas sociais?", [""] + ["Sim", "Depende do tema", "Prefiro histórias leves"], index=0)

                col_releitura, col_formato = st.columns(2)
                with col_releitura:
                    releitura = st.radio("Reler livros?", [""] + ["Sempre procuro novas leituras", "Gosto de reler", "Um pouco dos dois"], index=0)
                with col_formato:
                    formato_livro = st.radio("Formato preferido", [""] + ["Físico", "Digital", "Tanto faz"], index=0)
                st.markdown("---") # Divisão aqui

                # Seção 4: Influências e Outras Mídias
                st.subheader("Influências e Mídias")
                col_influencia, col_avaliacoes = st.columns(2)
                with col_influencia:
                    influencia = st.radio("O que mais influencia sua escolha de um livro?", [""] + ["Críticas", "Amigos", "Premiações", "Sinopse e capa"], index=0)
                with col_avaliacoes:
                    avaliacoes = st.radio("Importância das avaliações e recomendações", [""] + ["Sim", "Prefiro personalizadas", "Tanto faz"], index=0)

                col_audio, col_artigos = st.columns(2)
                with col_audio:
                    audiolivros = st.radio("Você ouve audiolivros?", [""] + ["Sim", "Não", "Depende"], index=0)
                with col_artigos:
                    interesse_artigos = st.radio("Você lê artigos acadêmicos ou científicos?", [""] + ["Sim", "Às vezes", "Não"], index=0)
                area_academica = st.text_input("Em quais áreas acadêmicas você tem interesse?", key="area_academica_input") if interesse_artigos in ["Sim", "Às vezes"] else ""
                st.markdown("---") # Divisão aqui

                # Seção 5: Propósito e Nível de Leitura
                st.subheader("Propósito e Nível")
                col_objetivo, col_conteudo = st.columns(2)
                with col_objetivo:
                    objetivo_leitura = st.radio("Qual seu principal objetivo ao ler?", [""] + ["Aprender", "Relaxar", "Desenvolvimento pessoal", "Conexão emocional", "Outros"], index=0)
                with col_conteudo:
                    tipo_conteudo = st.radio("Qual tipo de conteúdo você mais consome?", [""] + ["Textos longos", "Blogs", "Vídeos", "Podcasts", "Notícias"], index=0)

                col_nivel, col_velocidade = st.columns(2)
                with col_nivel:
                    nivel_leitura = st.radio("Como você descreveria seu nível de leitura?", [""] + ["Iniciante", "Intermediário", "Avançado"], index=0)
                with col_velocidade:
                    velocidade = st.radio("Qual o seu ritmo de leitura?", [""] + ["Rápido", "Moderado", "Lento"], index=0)
                st.markdown("---") # Divisão aqui

                # Seção 6: Curiosidade e Cultural
                st.subheader("Curiosidade e Cultural")
                col_curiosidade, col_cultural = st.columns(2)
                with col_curiosidade:
                    curiosidade = st.radio("Você tem curiosidade por temas novos e desconhecidos?", [""] + ["Sim", "Depende", "Não muito"], index=0)
                with col_cultural:
                    contexto_cultural = st.radio("Você se interessa por livros de outras culturas e perspectivas?", [""] + ["Sim", "Depende", "Prefiro minha realidade"], index=0)

                col_memoria, col_ingles = st.columns(2)
                with col_memoria:
                    memoria = st.radio("Você prefere tramas mais simples ou complexas?", [""] + ["Simples", "Complexa", "Equilibrada"], index=0)
                with col_ingles:
                    leitura_em_ingles = st.radio("Você lê livros em inglês?", [""] + ["Sim", "Às vezes", "Não"], index=0)
                st.markdown("---") # Divisão aqui


                if st.button("Enviar Respostas e Gerar Perfil", key="btn_submit"):
                    # Validação de campos obrigatórios
                    required_fields = {
                        "Faixa etária": idade,
                        "Frequência de leitura": frequencia_leitura,
                        "Tempo por sessão": tempo_leitura,
                        "Onde você lê": local_leitura,
                        "Prefere ficção ou não ficção": tipo_livro,
                        "Gêneros favoritos": generos,
                        "Você tem um autor favorito": tem_autor_favorito, # Valida a resposta 'Sim' ou 'Não'
                        "Tamanho preferido": tamanho_livro,
                        "Estilo de narrativa": narrativa,
                        "Sentimento desejado ao ler": sentimento_livro,
                        "Gosta de temas sociais": questoes_sociais,
                        "Reler livros": releitura,
                        "Formato preferido": formato_livro,
                        "O que mais influencia sua escolha de um livro": influencia,
                        "Importância das avaliações e recomendações": avaliacoes,
                        "Você ouve audiolivros": audiolivros,
                        "Você lê artigos acadêmicos ou científicos": interesse_artigos,
                        "Qual seu principal objetivo ao ler": objetivo_leitura,
                        "Qual tipo de conteúdo você mais consome": tipo_conteudo,
                        "Como você descreveria seu nível de leitura": nivel_leitura,
                        "Qual o seu ritmo de leitura": velocidade,
                        "Você tem curiosidade por temas novos e desconhecidos": curiosidade,
                        "Você se interessa por livros de outras culturas e perspectivas": contexto_cultural,
                        "Você prefere tramas mais simples ou complexas": memoria,
                        "Você lê livros em inglês": leitura_em_ingles,
                    }

                    missing_fields = []
                    for label, value in required_fields.items():
                        if not value or (isinstance(value, list) and not value):
                            missing_fields.append(label)

                    if tem_autor_favorito == "Sim" and not autor_favorito.strip():
                        missing_fields.append("Nome do autor favorito")
                    if interesse_artigos in ["Sim", "Às vezes"] and not area_academica.strip():
                        missing_fields.append("Áreas de interesse acadêmica")


                    if missing_fields:
                        st.error(f"Por favor, preencha as seguintes informações obrigatórias: {', '.join(missing_fields)}")
                    else:
                        with st.spinner("Gerando seu perfil literário... Isso pode levar alguns segundos."):
                            dados = {
                                "idade": idade,
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

                            genai.configure(api_key=gemini_api_key)
                            prompt = (
                                 "**Atue como um PSICÓLOGO LITERÁRIO altamente perspicaz e intuitivo.**\n"
                                "Sua missão é ir MUITO ALÉM das respostas diretas do formulário abaixo. **Não cite, reitere, ou faça qualquer referência explícita às informações exatas que foram fornecidas.** Ou seja, não mencione a origem de nenhum dado, como 'a preferência por', 'a recusa em', 'o interesse em', que remetam diretamente a uma resposta do formulário.\n"
                                "Em vez disso, analise as entrelinhas para **TRAÇAR UM RETRATO PSICOLÓGICO REVELADOR e SURPREENDENTE do leitor, identificando suas tendências, motivações e anseios subjacentes.** Seu objetivo é apresentar insights que o próprio leitor, ao ler, dirá: 'Uau, eu não tinha percebido isso sobre mim!'.\n"
                                "Conecte os traços de forma fluida e integrada, como se estivesse descrevendo a essência de uma personalidade complexa, e não um conjunto de dados. Foque em:\n"
                                "1.  **Forças e Desafios Inerentes:** O que define intrinsecamente este leitor e onde pode haver pontos de crescimento.\n"
                                "2.  **Desejos Não Articulados:** O que o leitor busca na leitura que ele mesmo não consegue expressar claramente.\n"
                                "3.  **Paradoxos e Equilíbrios:** Onde há aparentemente uma contradição, mas na verdade revela uma característica única.\n"
                                "4.  **Implicações de Hábitos:** O que os hábitos de leitura (onde, quando, como) revelam sobre sua psicologia.\n\n"
                                "Apresente este 'diagnóstico literário' em uma narrativa única, profunda e sem clichês, focando na descoberta de traços que vão além do óbvio.\n\n"
                                "--- # Fim do Perfil\n\n" # Linha de separação clara
                                "**Com base EXCLUSIVAMENTE nas tendências e motivações REVELADAS neste retrato psicológico (e sem repetir NENHUM dado bruto do formulário, nem mesmo inferências óbvias que já estavam no formulário), RECOMENDE:**\n"
                                "1.  **Livros relevantes**, com justificativas que explorem as conexões com as **tendências e anseios mais profundos** revelados no perfil.\n"
                                "2.  **Artigos acadêmicos apropriados**, detalhando a conexão com **áreas de pesquisa que complementem ou desafiem** as motivações subjacentes identificadas no retrato.\n\n"
                                "**Além disso, identifique uma ou duas possíveis novas áreas ou gêneros que o leitor poderia explorar**, com base nas suas preferências e inferências do perfil, e **sugira um ou dois títulos** que se encaixem nessa expansão, justificando a sugestão.\n\n"
                                "**Estruture a resposta claramente com o '## Perfil Literário' primeiro, seguido por '## Recomendações de Livros', '## Recomendações de Artigos Acadêmicos' e, por último, '## Sugestões de Expansão de Interesses'.**\n"
                                f"**Dados do Formulário para Análise:**\n{json.dumps(dados, indent=2, ensure_ascii=False)}"
                            )                  
                            model = genai.GenerativeModel("gemini-2.0-flash")
                            chat = model.start_chat()
                            response = chat.send_message(prompt)
                            perfil = response.text

                            salvar_resposta(st.session_state.logged_user, dados, perfil)
                            st.session_state.form_submitted = True
                            st.session_state.perfil = perfil
                            st.success("🎉 Perfil gerado com sucesso!")
                            st.rerun()

        else:
            st.markdown(f'<div class="justified-text">{st.session_state.perfil}</div>', unsafe_allow_html=True)
            st.markdown("---")
            st.subheader("Gerar Novas Recomendações?")
            st.info("Você pode gerar novas recomendações com base no seu perfil atual.")

            col_left_actions, col_actions, col_right_actions = st.columns([1, 3, 1])
            with col_actions:
                if st.button("🔄 Gerar nova recomendação", key="btn_nova_recomendacao"):
                    with st.spinner("Gerando nova recomendação..."):
                        resposta_existente = buscar_resposta_existente(st.session_state.logged_user)
                        if resposta_existente:
                            dados = resposta_existente.dados if isinstance(resposta_existente.dados, dict) else json.loads(resposta_existente.dados)
                            genai.configure(api_key=gemini_api_key)
                            prompt = (
                               "**Atue como um PSICÓLOGO LITERÁRIO altamente perspicaz e intuitivo.**\n"
                                "Sua missão é ir MUITO ALÉM das respostas diretas do formulário abaixo. **Não cite, reitere, ou faça qualquer referência explícita às informações exatas que foram fornecidas.** Ou seja, não mencione a origem de nenhum dado, como 'a preferência por', 'a recusa em', 'o interesse em', que remetam diretamente a uma resposta do formulário.\n"
                                "Em vez disso, analise as entrelinhas para **TRAÇAR UM RETRATO PSICOLÓGICO REVELADOR e SURPREENDENTE do leitor, identificando suas tendências, motivações e anseios subjacentes.** Seu objetivo é apresentar insights que o próprio leitor, ao ler, dirá: 'Uau, eu não tinha percebido isso sobre mim!'.\n"
                                "Conecte os traços de forma fluida e integrada, como se estivesse descrevendo a essência de uma personalidade complexa, e não um conjunto de dados. Foque em:\n"
                                "1.  **Forças e Desafios Inerentes:** O que define intrinsecamente este leitor e onde pode haver pontos de crescimento.\n"
                                "2.  **Desejos Não Articulados:** O que o leitor busca na leitura que ele mesmo não consegue expressar claramente.\n"
                                "3.  **Paradoxos e Equilíbrios:** Onde há aparentemente uma contradição, mas na verdade revela uma característica única.\n"
                                "4.  **Implicações de Hábitos:** O que os hábitos de leitura (onde, quando, como) revelam sobre sua psicologia.\n\n"
                                "Apresente este 'diagnóstico literário' em uma narrativa única, profunda e sem clichês, focando na descoberta de traços que vão além do óbvio.\n\n"
                                "--- # Fim do Perfil\n\n" # Linha de separação clara
                                "**Com base EXCLUSIVAMENTE nas tendências e motivações REVELADAS neste retrato psicológico (e sem repetir NENHUM dado bruto do formulário, nem mesmo inferências óbvias que já estavam no formulário), RECOMENDE:**\n"
                                "1.  **Livros relevantes**, com justificativas que explorem as conexões com as **tendências e anseios mais profundos** revelados no perfil.\n"
                                "2.  **Artigos acadêmicos apropriados**, detalhando a conexão com **áreas de pesquisa que complementem ou desafiem** as motivações subjacentes identificadas no retrato.\n\n"
                                "**Além disso, identifique uma ou duas possíveis novas áreas ou gêneros que o leitor poderia explorar**, com base nas suas preferências e inferências do perfil, e **sugira um ou dois títulos** que se encaixem nessa expansão, justificando a sugestão.\n\n"
                                "**Estruture a resposta claramente com o '## Perfil Literário' primeiro, seguido por '## Recomendações de Livros', '## Recomendações de Artigos Acadêmicos' e, por último, '## Sugestões de Expansão de Interesses'.**\n"
                                f"**Dados do Formulário para Análise:**\n{json.dumps(dados, indent=2, ensure_ascii=False)}"
                            )
                            model = genai.GenerativeModel("gemini-2.0-flash")
                            chat = model.start_chat()
                            response = chat.send_message(prompt)
                            perfil = response.text

                            salvar_resposta(st.session_state.logged_user, dados, perfil)
                            st.session_state.perfil = perfil
                            st.success("✅ Nova recomendação gerada!")
                            st.rerun()

    elif pagina == "🎮 Gamificação":
        if "logged_user" in st.session_state:
            usuario = st.session_state.logged_user
            st.title("🎮 Gamificação da Leitura")

            registrar_leitura(engine, usuario)

            # --- Bloco de Status do Usuário em um único highlight-container ---
            st.markdown("---")
            st.subheader("📊 Seu Desempenho Atual")
            
            col1_perf, col2_perf, col3_perf = st.columns(3)
            
            with col1_perf:
                st.subheader("Pontos")
                pontos, _ = calcular_pontos_e_nivel(engine, usuario)
                st.metric(label="Total", value=pontos)
            
            with col2_perf:
                st.subheader("Nível")
                _, nivel = calcular_pontos_e_nivel(engine, usuario)
                st.metric(label="Atual", value=nivel)

            # Calcular a colocação do usuário
            with engine.connect() as conn:
                ranking_data = conn.execute(text("""
                    SELECT u.username, COALESCE(SUM(p.paginas_lidas) + COUNT(*) FILTER (WHERE p.livro_finalizado) * 50, 0) as pontos
                    FROM usuarios u
                    LEFT JOIN progresso_leitura p ON u.username = p.username
                    GROUP BY u.username
                    ORDER BY pontos DESC
                """)).fetchall()
            
            sua_colocacao = None
            for i, r in enumerate(ranking_data):
                if r.username == usuario:
                    sua_colocacao = i + 1
                    break
            
            with col3_perf:
                st.subheader("Colocação")
                if sua_colocacao is not None:
                    st.metric(label="No Ranking", value=f"{sua_colocacao}º")
                else:
                    st.metric(label="No Ranking", value="N/A") # Ou uma mensagem indicando que não está no ranking ainda

            st.markdown("</div>", unsafe_allow_html=True)
            # --- Fim do Bloco de Status do Usuário ---
            
            st.markdown("---")
            mostrar_conquistas(engine, usuario)
            
            st.markdown("---")
            ranking_top(engine) 

            st.markdown("---")
            st.subheader("🔥 Desafio da Semana")
            st.info(desafio_ativo()) # Exibe a descrição do desafio
            
            # Valida e exibe a mensagem do desafio
            if validar_desafio(engine, usuario):
                st.success("✅ Desafio concluído! Você ganhou 50 pontos bônus.")
            else:
                st.warning("📚 Continue lendo para concluir o desafio!")
        else:
            st.warning("Faça login para acessar a gamificação.")

    elif pagina == "✍️ Painel do Escritor":
        col_left_writer, col_writer, col_right_writer = st.columns([1, 3, 1])
        with col_writer:
            painel_escritor_conteudo()