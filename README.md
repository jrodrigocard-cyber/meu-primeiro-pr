# Automação da apuração do Simples Nacional — Domínio Escrita Fiscal

Robô (RPA) em Python que, para cada empresa de uma lista:

1. troca de empresa no Domínio (F8);
2. abre a apuração e processa a competência informada;
3. salva capturas de tela como evidência;
4. recalcula o DAS pelas tabelas da LC 123/2006 (LC 155/2016) para **conferir** o valor do Domínio;
5. gera um relatório CSV com o status de cada empresa (erros não param o lote).

> O Domínio não tem API pública; o robô controla a tela via teclado/menus
> (pywinauto). **Os passos precisam ser ajustados à sua versão do Domínio** no
> `config.yaml` — não é preciso mexer no código.

## Instalação (Windows)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.exemplo.yaml config.yaml
copy empresas.exemplo.csv empresas.csv
```

## Uso

1. Abra o Domínio Escrita Fiscal e faça login (o robô **não** guarda senhas).
2. Teste o roteiro sem mexer no Domínio:
   ```bat
   python -m apuracao_simples --competencia 08/2026 --simular
   ```
3. Rode de verdade (comece com uma empresa só):
   ```bat
   python -m apuracao_simples --competencia 08/2026 --somente 1
   python -m apuracao_simples --competencia 08/2026
   ```
   Não use mouse/teclado enquanto o robô roda.

Saída em `saida/`: `relatorio_<competência>_<data>.csv`, `log_<data>.txt` e
`evidencias/<competência>/<código>_*.png` (inclusive telas de erro).
Código de retorno: `0` tudo OK, `1` falha de configuração, `2` alguma empresa com erro.

## empresas.csv

Separador `;` (padrão do Excel). Colunas: `codigo` (código da empresa no Domínio,
obrigatório), `nome`, `ativo` (`N` pula a empresa) e, para a conferência do DAS,
`anexo` (I a V), `receita_mes`, `rbt12`, `folha12` (folha dos últimos 12 meses,
usada no Fator R do Anexo V). Qualquer coluna vira variável no roteiro (`$cnpj` etc.).

## Ajustando o roteiro (`config.yaml`)

Cada passo tem uma ação: `tecla`, `digitar`, `menu`, `clicar_botao`,
`esperar_janela`, `esperar_fechar`, `aguardar`, `capturar_tela`. Veja os
comentários em `config.exemplo.yaml`. Dicas:

- Faça a apuração manualmente anotando cada tecla/TAB e reproduza no roteiro.
- Para descobrir títulos de janelas e botões:
  ```python
  from pywinauto import Application
  app = Application(backend="win32").connect(title_re=".*Dom[ií]nio.*")
  app.top_window().print_control_identifiers()
  ```
- Se menus/botões não forem encontrados, troque `backend: win32` por `uia`, ou
  use atalhos de teclado (`%m` = Alt+M) em vez de `menu`.
- Prefira `esperar_janela` a `aguardar` fixo: o robô fica mais rápido e confiável.

## Limitações da conferência

O cálculo cobre uma atividade/anexo por empresa. Não trata sublimite de
ICMS/ISS, receitas de exportação, retenções/ST, múltiplas atividades nem
segregação por tributo — nesses casos, use o valor do Domínio/PGDAS-D como
referência e a coluna de conferência apenas como indicativo.

## Testes

```bash
pip install pytest pyyaml
python -m pytest
```
