#!/usr/bin/env python3
"""Extrai texto e cláusulas-chave de PDFs de convenções e compara. Requer pdftotext."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db import conectar  # noqa: E402

CHAVES = {
    "piso": r"piso\s+salarial|sal[aá]rio\s+normativo",
    "reajuste": r"reajuste|corre[cç][aã]o\s+salarial",
    "vigencia": r"vig[eê]ncia",
    "data_base": r"data[- ]base",
    "vale_alimentacao": r"vale[- ]alimenta|ticket|cesta\s+b[aá]sica",
    "jornada": r"jornada|hora\s+extra|horas\s+extras",
    "contribuicao": r"contribui[cç][aã]o\s+(assistencial|sindical|negocial)",
}


def clausulas(texto):
    out = {}
    for nome, rx in CHAVES.items():
        ach = [m.start() for m in re.finditer(rx, texto, re.I)]
        out[nome] = [" ".join(texto[max(0, i - 80): i + 320].split()) for i in ach[:3]]
    return out


def ultimo_download():
    pdfs = sorted(Path.home().joinpath("Downloads").glob("*.pdf"), key=lambda f: f.stat().st_mtime)
    if not pdfs:
        sys.exit("Nenhum PDF em ~/Downloads")
    return str(pdfs[-1])


def extrair(a):
    a.pdf = a.pdf or ultimo_download()
    print("Arquivo:", a.pdf)
    texto = subprocess.run(["pdftotext", "-layout", a.pdf, "-"], capture_output=True, text=True, check=True).stdout
    cl = clausulas(texto)
    con = conectar()
    con.execute(
        "INSERT INTO instrumentos(registro,titulo,arquivo,texto,clausulas) VALUES(?,?,?,?,?) "
        "ON CONFLICT(registro) DO UPDATE SET texto=excluded.texto,clausulas=excluded.clausulas",
        (Path(a.pdf).name, Path(a.pdf).stem, a.pdf, texto, json.dumps(cl, ensure_ascii=False)),
    )
    con.commit()
    for k, v in cl.items():
        print(f"== {k}: {len(v)} trecho(s)")
        for t in v[:1]:
            print("  ", t)


def listar(_):
    for r in conectar().execute("SELECT id,registro,titulo,clausulas IS NOT NULL FROM instrumentos"):
        print(f"#{r[0]} {r[1]} | {r[2]} | {'analisado' if r[3] else 'sem análise'}")


def comparar(a):
    con = conectar()
    docs = []
    for i in (a.id1, a.id2):
        r = con.execute("SELECT registro,clausulas FROM instrumentos WHERE id=?", (i,)).fetchone()
        if not r or not r[1]:
            sys.exit(f"#{i} não existe ou não foi analisado")
        docs.append((r[0], json.loads(r[1])))
    for k in CHAVES:
        print(f"\n### {k}")
        for nome, cl in docs:
            print(f"- {nome}: {(cl.get(k) or ['(não encontrado)'])[0]}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="cmd", required=True)
    e = s.add_parser("extrair")
    e.add_argument("pdf", nargs="?", help="padrão: PDF mais recente em ~/Downloads")
    e.set_defaults(f=extrair)
    s.add_parser("listar").set_defaults(f=listar)
    c = s.add_parser("comparar")
    c.add_argument("id1", type=int)
    c.add_argument("id2", type=int)
    c.set_defaults(f=comparar)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
