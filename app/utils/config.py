# config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não encontrado.")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrado.")

engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 10})
