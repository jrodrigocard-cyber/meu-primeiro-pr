---
name: anotar
description: Registra, lista e busca anotações do projeto em um banco SQLite local (data/notas.db). Use quando o usuário pedir para anotar, lembrar, registrar uma decisão, listar anotações ou buscar algo anotado antes.
---

# Anotar

Memória de longo prazo do projeto, guardada localmente em `data/notas.db` (SQLite, fora do git).

## Como usar

Rode o script a partir da raiz do projeto:

```bash
python3 .claude/skills/anotar/scripts/notas.py add "texto da anotação" [--tag decisao]
python3 .claude/skills/anotar/scripts/notas.py list [--tag decisao] [--limit 20]
python3 .claude/skills/anotar/scripts/notas.py search "termo"
```

## Regras

- Ao pedir para anotar, grave o texto fielmente, com uma `--tag` curta quando houver categoria clara (ex.: `decisao`, `ideia`, `pendencia`).
- Antes de responder perguntas sobre decisões ou contexto passado, rode `search` com os termos relevantes.
- Decisões que valem para todo o projeto também devem ir para a seção "Memória / Decisões" do `CLAUDE.md`.
- Nunca apague o banco nem edite o arquivo diretamente; use apenas o script.
