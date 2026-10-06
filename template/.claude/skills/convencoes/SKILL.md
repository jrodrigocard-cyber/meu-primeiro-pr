---
name: convencoes
description: Agente de Convenções Coletivas. Consulta instrumentos coletivos (CCT/ACT) no Mediador do Ministério do Trabalho, guarda em SQLite local (data/convencoes.db), extrai cláusulas de PDFs (reajuste, piso, benefícios) e compara convenções. Use quando o usuário falar de convenção coletiva, acordo coletivo, sindicato, piso salarial, reajuste de categoria ou Mediador.
---

# Agente de Convenções

Fonte: https://mediador.trabalho.gov.br/sistemas/mediador/ConsultarInstColetivo
Dados em `data/convencoes.db` e PDFs em `data/pdfs/` (fora do git).

> **Testado em 06/10/2026:** o site abre e os campos do formulário são lidos
> (`txtNRCNPJ`, `txtNORazaoSocial`, `txtDSCategoria`, `cboUFRegistro`, datas de
> registro/vigência etc.), mas o botão Pesquisar é protegido por **reCAPTCHA v3**
> e envia a consulta por AJAX (`/ConsultarInstColetivo/getConsultaAvancada`).
> Por isso `buscar.py consultar` provavelmente será barrado, e não se deve
> contornar o captcha. Caminho recomendado: faça a consulta no navegador
> (você, ou a extensão Claude no Chrome), baixe os PDFs e use `analisar.py`.

## 1. Consultar o Mediador (script automático)

```bash
S=.claude/skills/convencoes/scripts
python3 $S/buscar.py campos                       # lista os campos do formulário
python3 $S/buscar.py consultar CAMPO=valor ...    # envia a consulta, salva resultados
python3 $S/buscar.py baixar [--id N]              # baixa os PDFs dos instrumentos salvos
```

## 2. Analisar PDFs baixados (fluxo principal)

O usuário baixa o PDF da convenção no navegador (vai para `~/Downloads`).
Sem argumento, `extrair` pega o PDF mais recente de `~/Downloads`. Depois de
extrair, leia o texto completo (`data/convencoes.db`, coluna `texto`, ou rode
`pdftotext -layout arquivo.pdf -`) e responda com resumo: partes, vigência,
data-base, piso, reajuste, benefícios, jornada e contribuições, citando cláusulas.

```bash
python3 $S/analisar.py extrair arquivo.pdf        # texto + cláusulas-chave, salva no banco
python3 $S/analisar.py listar
python3 $S/analisar.py comparar ID1 ID2           # compara cláusulas lado a lado
```

## Resumo para o cliente
Seguir o "Resumo padrão de convenção para o cliente" do `CLAUDE.md` (9 temas fixos, tabela Tema | O que diz | Cláusula).

## Relatório PDF para o cliente (padrão Anályse)
Monte um JSON como `relatorios/MR024201-2025-resumo.json` (título, meta, seções com `tabela` ou `itens`) e rode:
`python3 $S/relatorio.py resumo.json` (salva em `~/Downloads`; requer `reportlab`). O logo fica em `assets/logo-analyse.png`.

## Regras

- Cite sempre a cláusula/trecho de origem ao resumir valores (piso, reajuste, vigência).
- Valores extraídos por regex são sugestões: confirme no texto do PDF antes de afirmar.
- Se o site não responder (403/timeout), diga isso; não invente dados.
- Use o banco apenas pelos scripts.
