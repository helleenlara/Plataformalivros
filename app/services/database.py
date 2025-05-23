# services/database.py
import json
import pandas as pd
from sqlalchemy import text
from app.config import engine

def salvar_resposta(usuario, dados_dict, perfil_gerado):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO respostas_formulario (usuario, dados, perfil_gerado)
            VALUES (:usuario, :dados, :perfil)
            ON CONFLICT (usuario) DO UPDATE
            SET dados = :dados, perfil_gerado = :perfil
        """), {
            "usuario": usuario,
            "dados": json.dumps(dados_dict),
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
                dados_dicts = df["dados"].apply(json.loads).apply(pd.Series)
                df = pd.concat([df.drop(columns=["dados"]), dados_dicts], axis=1)
            return df
    except:
        return pd.DataFrame()
