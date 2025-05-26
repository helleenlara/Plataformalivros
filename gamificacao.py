# gamificacao.py
import streamlit as st
from sqlalchemy import text
from datetime import date

def registrar_leitura(engine, username):
    st.subheader("📈 Registro de Leitura")
    paginas = st.number_input("Quantas páginas leu hoje?", min_value=1, step=1)
    finalizado = st.checkbox("Finalizou um livro hoje?")
    if st.button("Registrar leitura"):
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO progresso_leitura (username, data, paginas_lidas, livro_finalizado)
                VALUES (:u, CURRENT_DATE, :p, :f)
                ON CONFLICT (username, data) DO UPDATE
                SET paginas_lidas = :p, livro_finalizado = :f
            """), {"u": username, "p": paginas, "f": finalizado})
        st.success("Leitura registrada com sucesso!")

def calcular_pontos_e_nivel(engine, username):
    with engine.connect() as conn:
        paginas, livros = conn.execute(text("""
            SELECT COALESCE(SUM(paginas_lidas), 0), COUNT(*) FILTER (WHERE livro_finalizado)
            FROM progresso_leitura WHERE username = :u
        """), {"u": username}).fetchone()
        pontos = paginas + livros * 50

        if pontos < 100:
            nivel = "Iniciante"
        elif pontos < 500:
            nivel = "Aprendiz"
        elif pontos < 1000:
            nivel = "Explorador Literário"
        else:
            nivel = "Mestre das Letras"

        return pontos, nivel

def mostrar_status(engine, username):
    pontos, nivel = calcular_pontos_e_nivel(engine, username)
    st.metric("Pontos", pontos)
    st.metric("Nível", nivel)

def verificar_conquistas(engine, username):
    with engine.begin() as conn:
        conquistas = []
        total_paginas = conn.execute(text("""
            SELECT SUM(paginas_lidas) FROM progresso_leitura WHERE username = :u
        """), {"u": username}).scalar() or 0
        if total_paginas >= 100:
            conquistas.append("Leu 100 páginas!")

        finalizados = conn.execute(text("""
            SELECT COUNT(*) FROM progresso_leitura WHERE username = :u AND livro_finalizado = TRUE
        """), {"u": username}).scalar()
        if finalizados >= 1:
            conquistas.append("Primeiro livro finalizado")

        dias = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT data FROM progresso_leitura WHERE username = :u
                AND data >= CURRENT_DATE - INTERVAL '6 days'
            ) dias
        """), {"u": username}).scalar()
        if dias == 7:
            conquistas.append("Leu 7 dias seguidos")

        for c in conquistas:
            conn.execute(text("""
                INSERT INTO conquistas (username, nome_conquista)
                VALUES (:u, :c)
                ON CONFLICT DO NOTHING
            """), {"u": username, "c": c})

def mostrar_conquistas(engine, username):
    with engine.connect() as conn:
        conquistas = conn.execute(text("""
            SELECT nome_conquista, data_conquista FROM conquistas
            WHERE username = :u
            ORDER BY data_conquista DESC
        """), {"u": username}).fetchall()
        st.subheader("🏅 Suas Conquistas")
        if not conquistas:
            st.info("Nenhuma conquista ainda. Registre sua leitura!")
        for c in conquistas:
            st.write(f"✅ {c.nome_conquista} - {c.data_conquista}")

def ranking_top(engine):
    with engine.connect() as conn:
        dados = conn.execute(text("""
            SELECT u.username, COALESCE(SUM(p.paginas_lidas) + COUNT(*) FILTER (WHERE p.livro_finalizado) * 50, 0) as pontos
            FROM usuarios u
            LEFT JOIN progresso_leitura p ON u.username = p.username
            GROUP BY u.username
            ORDER BY pontos DESC
            LIMIT 5
        """)).fetchall()
        st.subheader("🏆 Ranking dos Leitores")
        for i, r in enumerate(dados, 1):
            st.write(f"{i}º {r.username} - {r.pontos} pontos")

def desafio_ativo():
    return "Leia 50 páginas esta semana para ganhar +50 pontos bônus"

def validar_desafio(engine, username):
    with engine.connect() as conn:
        semana = conn.execute(text("""
            SELECT SUM(paginas_lidas) FROM progresso_leitura
            WHERE username = :u AND data >= CURRENT_DATE - INTERVAL '6 days'
        """), {"u": username}).scalar() or 0
        return semana >= 50

