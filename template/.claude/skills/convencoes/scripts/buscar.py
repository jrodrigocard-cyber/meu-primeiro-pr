#!/usr/bin/env python3
"""Consulta o Mediador (MTE) e baixa instrumentos coletivos. Só biblioteca padrão."""
import argparse
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from http.cookiejar import CookieJar

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from db import PDFS, conectar  # noqa: E402

URL = "https://mediador.trabalho.gov.br/sistemas/mediador/ConsultarInstColetivo"
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
op.addheaders = [("User-Agent", "Mozilla/5.0 (agente-convencoes)")]


def abrir(url, dados=None):
    corpo = urllib.parse.urlencode(dados).encode() if dados else None
    with op.open(url, corpo, timeout=60) as r:
        return r.read(), r.headers.get("Content-Type", "")


class Pagina(HTMLParser):
    def __init__(self):
        super().__init__()
        self.campos, self.links, self.form = [], [], {}
        self._a = None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "form":
            self.form = {"action": a.get("action") or "", "method": (a.get("method") or "get").lower()}
        elif tag in ("input", "select", "textarea") and a.get("name"):
            self.campos.append((a["name"], tag, a.get("type", ""), a.get("value", "")))
        elif tag == "a" and a.get("href"):
            self._a = [a["href"], ""]

    def handle_data(self, d):
        if self._a:
            self._a[1] += d

    def handle_endtag(self, tag):
        if tag == "a" and self._a:
            self.links.append(tuple(self._a))
            self._a = None


def ler(html):
    p = Pagina()
    p.feed(html.decode("utf-8", "replace"))
    return p


def campos(_):
    p = ler(abrir(URL)[0])
    print("form:", p.form)
    for nome, tag, tipo, val in p.campos:
        print(f"  {nome}  <{tag} {tipo}>  padrao={val!r}")


def consultar(a):
    p = ler(abrir(URL)[0])
    dados = {n: v for n, t, ty, v in p.campos if ty == "hidden"}
    dados.update(kv.split("=", 1) for kv in a.filtros)
    acao = urllib.parse.urljoin(URL, p.form.get("action", ""))
    if p.form.get("method") == "post":
        html, _ = abrir(acao, dados)
    else:
        html, _ = abrir(acao + "?" + urllib.parse.urlencode(dados))
    r = ler(html)
    con = conectar()
    n = 0
    for href, txt in r.links:
        if re.search(r"(pdf|download|visualizar|Instrumento)", href, re.I):
            reg = re.search(r"(MR\d{6}/\d{4})", txt + href)
            con.execute(
                "INSERT OR IGNORE INTO instrumentos(registro,titulo,url_pdf) VALUES(?,?,?)",
                (reg.group(1) if reg else href, txt.strip(), urllib.parse.urljoin(acao, href)),
            )
            n += 1
    con.commit()
    print(f"{n} instrumento(s) salvo(s). Se 0, confira `campos` e o HTML retornado.")


def baixar(a):
    con = conectar()
    q = "SELECT id,url_pdf FROM instrumentos WHERE arquivo IS NULL"
    linhas = con.execute(q + (" AND id=?" if a.id else ""), (a.id,) if a.id else ()).fetchall()
    for id_, url in linhas:
        dados, tipo = abrir(url)
        if b"%PDF" not in dados[:8]:
            print(f"#{id_}: não é PDF ({tipo}); pulando")
            continue
        f = PDFS / f"{id_}.pdf"
        f.write_bytes(dados)
        con.execute("UPDATE instrumentos SET arquivo=? WHERE id=?", (str(f), id_))
        print(f"#{id_}: {f}")
    con.commit()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("campos").set_defaults(f=campos)
    c = s.add_parser("consultar")
    c.add_argument("filtros", nargs="*", help="CAMPO=valor")
    c.set_defaults(f=consultar)
    b = s.add_parser("baixar")
    b.add_argument("--id", type=int)
    b.set_defaults(f=baixar)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
