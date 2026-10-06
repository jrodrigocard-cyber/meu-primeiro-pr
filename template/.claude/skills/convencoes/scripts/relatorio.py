#!/usr/bin/env python3
"""Gera relatório PDF (padrão Anályse) a partir de um JSON de resumo.
Uso: relatorio.py resumo.json [saida.pdf]  (padrão: ~/Downloads/<nome>.pdf)"""
import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle, KeepTogether)

AZUL = colors.Color(0, 139 / 255, 208 / 255)
LOGO = Path(__file__).resolve().parents[4] / "assets" / "logo-analyse.png"
F = "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf"
for n, s in (("Sans", "Regular"), ("Sans-B", "Bold")):
    pdfmetrics.registerFont(TTFont(n, F % s))

est = lambda **k: ParagraphStyle("x", fontName=k.pop("f", "Sans"), **k)
TIT = est(f="Sans-B", fontSize=18, leading=22)
H = est(f="Sans-B", fontSize=12, leading=15, spaceBefore=14, spaceAfter=2)
LAB = est(f="Sans-B", fontSize=8, leading=11, textColor=AZUL)
TXT = est(fontSize=9.5, leading=13.5)
CEL = est(fontSize=8.8, leading=11.5)
CELB = est(f="Sans-B", fontSize=8.8, leading=11.5)
CAB = est(f="Sans-B", fontSize=8.8, leading=11.5, textColor=colors.white)


def tabela(linhas):
    dados = [[Paragraph(x, CAB) for x in ("Tema", "O que diz", "Cláusula")]]
    for t, d, c in linhas:
        dados.append([Paragraph(t, CELB), Paragraph(d, CEL), Paragraph(c, CEL)])
    t = Table(dados, colWidths=[36 * mm, 115 * mm, 21 * mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.Color(.85, .85, .85)),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(.96, .98, 1)]),
    ]))
    return t


def main(js, saida):
    d = json.load(open(js, encoding="utf-8"))
    rodape = f"Anályse Assessoria Contábil S/S - {d['titulo']} - {d['data']}"

    def pagina(c, doc):
        c.saveState()
        c.setFont("Sans", 7.5)
        c.setFillColor(colors.Color(.55, .55, .55))
        c.drawString(20 * mm, 12 * mm, rodape)
        c.drawRightString(190 * mm, 12 * mm, f"Página {doc.page}")
        c.restoreState()

    doc = BaseDocTemplate(saida, pagesize=A4, title=d["titulo"], author="Anályse Assessoria Contábil S/S")
    doc.addPageTemplates([PageTemplate(frames=[Frame(20 * mm, 18 * mm, 170 * mm, 259 * mm, 0, 0, 0, 0)], onPage=pagina)])
    h = 17 * mm
    s = [Image(str(LOGO), width=h * 1280 / 370, height=h, hAlign="LEFT"), Spacer(1, 8 * mm),
         Paragraph(d["titulo"], TIT), Spacer(1, 2 * mm)]
    meta = [[Paragraph(k.upper(), LAB), Paragraph(v, TXT)] for k, v in d["meta"]]
    mt = Table(meta, colWidths=[34 * mm, 136 * mm])
    mt.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
                            ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.Color(.8, .8, .8)),
                            ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    s += [mt]
    for i, sec in enumerate(d["secoes"], 1):
        bloco = [Paragraph(f"{i}. {sec['titulo']}", H), Paragraph(sec.get("rotulo", "OBSERVAÇÕES"), LAB), Spacer(1, 3)]
        if "tabela" in sec:
            s += bloco + [tabela(sec["tabela"])]
        else:
            s += [KeepTogether(bloco)] + [Paragraph("• " + b, TXT) for b in sec["itens"]]
    doc.build(s)


if __name__ == "__main__":
    js = sys.argv[1]
    if len(sys.argv) > 2:
        out = sys.argv[2]
    else:
        pasta = Path.home() / "Downloads"
        pasta.mkdir(exist_ok=True)
        out = str(pasta / (Path(js).stem + ".pdf"))
    main(js, out)
    print("PDF salvo em", out)
