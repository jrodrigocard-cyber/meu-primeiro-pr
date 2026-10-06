"""Banco SQLite compartilhado (data/convencoes.db)."""
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
DB = RAIZ / "data" / "convencoes.db"
PDFS = RAIZ / "data" / "pdfs"


def conectar():
    DB.parent.mkdir(exist_ok=True)
    PDFS.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(
        "CREATE TABLE IF NOT EXISTS instrumentos ("
        "id INTEGER PRIMARY KEY, registro TEXT UNIQUE, titulo TEXT, url_pdf TEXT, "
        "arquivo TEXT, texto TEXT, clausulas TEXT, criado_em TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    return con
