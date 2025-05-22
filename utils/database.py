
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def salvar_resposta(usuario, texto, perfil_gerado):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO respostas_formulario (usuario, dados, perfil)
            VALUES (:usuario, :dados, :perfil)
        """), {"usuario": usuario, "dados": texto, "perfil": perfil_gerado})

def usuario_ja_respondeu(usuario):
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT 1 FROM respostas_formulario WHERE usuario = :usuario
        """), {"usuario": usuario})
        return result.first() is not None

def buscar_recomendacoes(usuario):
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT recomendacoes FROM respostas_formulario WHERE usuario = :usuario
        """), {"usuario": usuario})
        row = result.fetchone()
        return row['recomendacoes'] if row else None

def carregar_respostas():
    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM respostas_formulario"))
        return [dict(r._mapping) for r in result]
