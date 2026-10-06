#!/usr/bin/env python3
"""Anotações locais em SQLite (data/notas.db), sem dependências externas."""
import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).resolve().parents[4] / "data" / "notas.db"


def conectar():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(
        "CREATE TABLE IF NOT EXISTS notas ("
        "id INTEGER PRIMARY KEY, criada_em TEXT NOT NULL, tag TEXT, texto TEXT NOT NULL)"
    )
    return con


def mostrar(linhas):
    if not linhas:
        print("Nenhuma anotação encontrada.")
    for id_, data, tag, texto in linhas:
        print(f"#{id_} [{data}]{f' ({tag})' if tag else ''} {texto}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("texto")
    a.add_argument("--tag")
    l = sub.add_parser("list")
    l.add_argument("--tag")
    l.add_argument("--limit", type=int, default=20)
    s = sub.add_parser("search")
    s.add_argument("termo")
    args = p.parse_args()

    con = conectar()
    cols = "id, criada_em, tag, texto"
    if args.cmd == "add":
        agora = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur = con.execute(
            "INSERT INTO notas (criada_em, tag, texto) VALUES (?, ?, ?)",
            (agora, args.tag, args.texto),
        )
        con.commit()
        print(f"Anotação #{cur.lastrowid} salva.")
    elif args.cmd == "list":
        q, params = f"SELECT {cols} FROM notas", []
        if args.tag:
            q += " WHERE tag = ?"
            params.append(args.tag)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(args.limit)
        mostrar(con.execute(q, params).fetchall())
    else:
        like = f"%{args.termo}%"
        mostrar(
            con.execute(
                f"SELECT {cols} FROM notas WHERE texto LIKE ? OR tag LIKE ? ORDER BY id DESC",
                (like, like),
            ).fetchall()
        )


if __name__ == "__main__":
    main()
