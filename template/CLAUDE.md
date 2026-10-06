# __NOME__

## Contexto
Descreva aqui o objetivo do projeto.

## Convenções
- Idioma: português
- Dados locais ficam em `data/` (não versionados)

## Memória / Decisões
Registre aqui decisões importantes e aprendizados. Atualize sempre que algo relevante for decidido.

## Skills do projeto
Ficam em `.claude/skills/<nome>/SKILL.md`. Inclusa: `anotar` (anotações em SQLite local, `data/notas.db`). `convencoes` (consulta ao Mediador, SQLite `data/convencoes.db`, análise e comparação de PDFs).

## Resumo padrão de convenção para o cliente
Ao receber o PDF de qualquer convenção/acordo coletivo, gerar resumo em tabela
(Tema | O que diz | Cláusula) com exatamente estes temas, nesta ordem:
1. Vigência e data-base
2. Piso salarial (todas as faixas/funções e a data de início)
3. Reajuste (percentual, tabela proporcional, base da próxima revisão)
4. Vale-refeição ou alimentação (valores, municípios, natureza, proporcionalidade)
5. Vale-transporte
6. Seguro de vida em grupo
7. Estabilidade da gestante
8. Jornada (horas extras, compensação; só citar banco de horas se o texto trouxer regras)
9. Contribuição negocial dos empregados (valor, parcelas, meses de desconto, oposição)
Regras: citar sempre o nº da cláusula; conferir valores por extenso x numéricos e
apontar divergências; se o tema não existir no PDF, escrever "Não consta". Se
houver cláusulas relevantes além desses temas (ex.: contribuição patronal), listar em "Outros pontos".
Relatório ao cliente: seguir o padrão visual da ata da Analyse (logo da empresa).
Relatórios em PDF: sempre salvar em `~/Downloads` (padrão do `relatorio.py`) e, em sessão na nuvem, também enviar o arquivo ao usuário.
