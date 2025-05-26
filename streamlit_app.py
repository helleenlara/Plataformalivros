
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
    validar_desafio
)

# Configuração da página
st.set_page_config(page_title="Plataforma LitMe", layout="wide")

# Estilo personalizado
st.markdown("""
    <style>
        .main {
            background-color: #f9f9f9;
        }
        h1, h2, h3 {
            color: #1f4172;
        }
        .stButton>button {
            color: white;
            background-color: #1f4172;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
        }
        .stSidebar {
            background-color: #e9f0fa;
        }
    </style>
""", unsafe_allow_html=True)

# Logo e navegação
st.sidebar.image("static/logo_litme.jpg", use_container_width=True)
st.sidebar.title("📚 Navegação")
pagina = st.sidebar.radio("Escolha uma seção:", ["📋 Formulário do Leitor", "📖 Painel do Escritor", "🎮 Gamificação"])

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

verificar_ou_criar_tabela_usuarios()


if pagina == "📋 Formulário do Leitor":
    if "logged_user" not in st.session_state:
        st.sidebar.title("🔐 Autenticação")
        aba_login, aba_cadastro = st.sidebar.tabs(["Login", "Cadastrar"])

        with aba_login:
            st.subheader("Login")
            login_user = st.text_input("Usuário", key="login_user")
            login_pass = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Entrar", key="btn_login"):
                user = autenticar_usuario(login_user, login_pass)
                if user:
                    st.session_state.logged_user = user.username
                    st.session_state.logged_name = user.nome
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

        with aba_cadastro:
            st.subheader("Cadastrar")
            new_user = st.text_input("Usuário", key="new_user")
            new_name = st.text_input("Nome", key="new_name")
            new_pass = st.text_input("Senha", type="password", key="signup_pass")
            if st.button("Cadastrar", key="btn_signup"):
                try:
                    cadastrar_usuario(new_user, new_name, new_pass)
                    st.success("Conta criada! Faça login.")
                except IntegrityError:
                    st.error("Este usuário já existe. Escolha outro.")
    else:
        st.sidebar.write(f"👤 {st.session_state.logged_name}")
        if st.sidebar.button("Logout", key="btn_logout"):
            for key in ["logged_user", "logged_name", "form_submitted", "perfil"]:
                st.session_state.pop(key, None)
            st.rerun()

        resposta_existente = buscar_resposta_existente(st.session_state.logged_user)
        if resposta_existente and "form_submitted" not in st.session_state:
            st.session_state.form_submitted = True
            st.session_state.perfil = resposta_existente.perfil_gerado

        if "form_submitted" not in st.session_state:
            st.title("📋 Formulário de Preferências de Leitura")

            idade = st.selectbox("Faixa etária:", [
                "Menor de 18", "18 a 24", "25 a 34", "35 a 44", "45 a 60", "Acima de 60"])
            frequencia_leitura = st.radio("Frequência de leitura", ["Todos os dias", "Algumas vezes por semana", "Algumas vezes por mês", "Raramente"])
            tempo_leitura = st.radio("Tempo por sessão", ["Menos de 30 minutos", "30 minutos a 1 hora", "1 a 2 horas", "Mais de 2 horas"])
            local_leitura = st.radio("Onde você lê?", ["Em casa", "No transporte público", "Em bibliotecas/cafés", "Outros lugares"])
            tipo_livro = st.radio("Prefere ficção ou não ficção?", ["Ficção", "Não ficção", "Gosto dos dois"])
            generos = st.multiselect("Gêneros favoritos", ["Ficção científica", "Fantasia", "Romance", "Mistério/Thriller", "Terror", "História", "Biografia", "Desenvolvimento pessoal", "Negócios", "Filosofia", "Outro"])
            genero_outro = st.text_input("Qual outro gênero?") if "Outro" in generos else ""
            autor_favorito = st.text_input("Autor favorito")
            tamanho_livro = st.radio("Tamanho preferido", ["Curtos (-200 páginas)", "Médios (200-400 páginas)", "Longos (+400 páginas)", "Não tenho preferência"])
            narrativa = st.radio("Estilo de narrativa", ["Ação rápida", "Narrativa introspectiva", "Equilibrado entre os dois"])
            sentimento_livro = st.radio("Sentimento desejado", ["Inspirado", "Reflexivo", "Empolgado", "Confortável", "Assustado"])
            questoes_sociais = st.radio("Gosta de temas sociais?", ["Sim", "Depende do tema", "Prefiro histórias leves"])
            releitura = st.radio("Reler livros?", ["Sempre procuro novas leituras", "Gosto de reler", "Um pouco dos dois"])
            formato_livro = st.radio("Formato preferido", ["Físicos", "Digitais", "Tanto faz"])
            influencia = st.radio("Influência na escolha", ["Críticas", "Amigos", "Premiações", "Sinopse e capa"])
            avaliacoes = st.radio("Importância das avaliações", ["Sim", "Prefiro personalizadas", "Tanto faz"])
            audiolivros = st.radio("Audiolivros?", ["Sim", "Não", "Depende"])
            interesse_artigos = st.radio("Lê artigos acadêmicos?", ["Sim", "Às vezes", "Não"])
            area_academica = st.text_input("Áreas de interesse acadêmico") if interesse_artigos != "Não" else ""
            objetivo_leitura = st.radio("Objetivo ao ler", ["Aprender", "Relaxar", "Desenvolvimento pessoal", "Conexão emocional", "Outros"])
            tipo_conteudo = st.radio("Tipo de conteúdo consumido", ["Textos longos", "Blogs", "Vídeos", "Podcasts", "Notícias"])
            nivel_leitura = st.radio("Nível de leitura", ["Iniciante", "Intermediário", "Avançado"])
            velocidade = st.radio("Ritmo de leitura", ["Rápido", "Moderado", "Lento"])
            curiosidade = st.radio("Curiosidade por temas novos", ["Sim", "Depende", "Não muito"])
            contexto_cultural = st.radio("Livros de outras culturas?", ["Sim", "Depende", "Prefiro minha realidade"])
            memoria = st.radio("Tipo de trama", ["Simples", "Complexa", "Equilibrada"])
            leitura_em_ingles = st.radio("Lê em inglês?", ["Sim", "Às vezes", "Não"])

            if st.button("Enviar Respostas", key="btn_submit"):
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
                prompt = f"Gere um perfil literário com base nas respostas e recomende livros e artigos academicos com base nesse perfil:\n{json.dumps(dados, indent=2, ensure_ascii=False)}"
                model = genai.GenerativeModel("gemini-2.0-flash")
                chat = model.start_chat()
                response = chat.send_message(prompt)
                perfil = response.text

                salvar_resposta(st.session_state.logged_user, dados, perfil)
                st.session_state.form_submitted = True
                st.session_state.perfil = perfil
                st.rerun()
        else:
            st.title("📖 Seu Perfil Literário")
            st.write(st.session_state.perfil)
            if st.button("🔄 Gerar nova recomendação", key="btn_nova_recomendacao"):
                resposta_existente = buscar_resposta_existente(st.session_state.logged_user)
                if resposta_existente:
                    dados = resposta_existente.dados if isinstance(resposta_existente.dados, dict) else json.loads(resposta_existente.dados)
                    genai.configure(api_key=gemini_api_key)
                    prompt = (
                        "Com base nas respostas abaixo, crie um perfil literário atualizado.\n"
                        "Depois, recomende:\n"
                        "1. Livros relevantes com base nos gostos literários.\n"
                        "2. Artigos acadêmicos conforme os interesses acadêmicos (se aplicável).\n\n"
                        f"{json.dumps(dados, indent=2, ensure_ascii=False)}"
                    )
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    chat = model.start_chat()
                    response = chat.send_message(prompt)
                    perfil = response.text

                    salvar_resposta(st.session_state.logged_user, dados, perfil)
                    st.session_state.perfil = perfil
                    st.success("✅ Nova recomendação gerada!")
                    st.rerun()

elif pagina == "📖 Painel do Escritor":
    st.title("📖 Painel do Escritor")
    st.markdown("""
Este painel utiliza conceitos de **Big Data em Python** para fornecer insights úteis a escritores,
baseando-se nas preferências reais dos leitores coletadas pela plataforma.
""")

    try:
        df = carregar_dados()       
        if df.empty:
            st.warning("Ainda não há dados suficientes para análise")
            st.stop()
    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {e}")
        st.stop()

    faixa_etaria_opcao = st.selectbox("Filtrar por faixa etária:", ["Todas"] + sorted(df["idade"].dropna().unique().tolist()))
    if faixa_etaria_opcao != "Todas":
        df = df[df["idade"] == faixa_etaria_opcao]

    st.header( "📊 Análise Estatística dos Leitores")
    col1, col2 = st.columns(2)
    with col1:
        if "formato_livro" in df.columns:
            st.subheader("Formato de Leitura Preferido")
            st.bar_chart(df["formato_livro"].value_counts())

    with col2:
        if "generos" in df.columns:
            generos_series = df["generos"].str.split(", ").explode()
            st.subheader("Gêneros Literários Mais Citados")
            st.bar_chart(generos_series.value_counts())

    col3, col4 = st.columns(2)
    with col3:
        if "objetivo_leitura" in df.columns:
            st.subheader("Objetivo de Leitura")
            st.bar_chart(df["objetivo_leitura"].value_counts())

    with col4:
        if "sentimento_livro" in df.columns:
            st.subheader("Sentimentos Desejados")
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
            st.warning("⚠️ Não há perfis suficientes para análise.")
            st.stop()

        from datetime import datetime
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
        st.markdown(response.text)
        st.download_button("⬇️ Baixar Análise", data=response.text, file_name="analise_ia.txt")

    except Exception as e:
        st.warning(f"❌ Erro na análise com IA: {e}")
elif pagina == "🎮 Gamificação":
    from gamificacao import (
    registrar_leitura,
    mostrar_status,
    verificar_conquistas,
    mostrar_conquistas,
    ranking_top,
    desafio_ativo,
    validar_desafio
)

    if "logged_user" in st.session_state:
        usuario = st.session_state.logged_user
        st.title("🎮 Gamificação da Leitura")

        registrar_leitura(engine, usuario)
        mostrar_status(engine, usuario)
        verificar_conquistas(engine, usuario)
        mostrar_conquistas(engine, usuario)
        ranking_top(engine)

        st.subheader("🔥 Desafio da Semana")
        st.info(desafio_ativo())
        if validar_desafio(engine, usuario):
            st.success("✅ Desafio concluído! Você ganhou 50 pontos bônus.")
        else:
            st.warning("📚 Continue lendo para concluir o desafio!")
    else:
        st.warning("Faça login para acessar a gamificação.")
