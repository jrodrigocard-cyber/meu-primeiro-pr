"""Execução do roteiro de passos (definido no YAML) para cada empresa."""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from string import Template

from .calculo import ErroCalculo, calcular_das

log = logging.getLogger(__name__)

ACOES = {
    "tecla", "digitar", "menu", "clicar_botao", "esperar_janela",
    "esperar_fechar", "aguardar", "capturar_tela", "criar_pasta", "verificar_arquivo",
}


@dataclass
class ResultadoEmpresa:
    codigo: str
    nome: str
    competencia: str
    status: str = "OK"
    mensagem: str = ""
    das_conferencia: str = ""
    aliquota_efetiva: str = ""
    arquivos_gerados: list = field(default_factory=list)
    evidencias: list = field(default_factory=list)


def validar_roteiro(passos):
    for i, passo in enumerate(passos, start=1):
        if not isinstance(passo, dict) or len(passo) != 1:
            raise ValueError(f"Passo {i} deve ter exatamente uma ação: {passo!r}")
        acao = next(iter(passo))
        if acao not in ACOES:
            raise ValueError(f"Passo {i}: ação desconhecida {acao!r}. Válidas: {sorted(ACOES)}")


def _substituir(valor, variaveis):
    if isinstance(valor, str):
        return Template(valor).safe_substitute(variaveis)
    if isinstance(valor, dict):
        return {k: _substituir(v, variaveis) for k, v in valor.items()}
    return valor


def montar_variaveis(empresa: dict, competencia: str, globais: dict) -> dict:
    """Variáveis do roteiro: colunas da empresa + derivadas da competência + `variaveis` do config."""
    mes, ano = competencia.split("/")
    variaveis = {
        **empresa,
        "competencia": competencia,
        "mes": mes,
        "ano": ano,
        "competencia_mmaaaa": f"{mes}{ano}",
        "competencia_aaaamm": f"{ano}{mes}",
        "cnpj_numeros": re.sub(r"\D", "", empresa.get("cnpj", "")),
    }
    # Variáveis globais podem usar as da empresa, ex.: "C:/PGDAS/$competencia_aaaamm"
    for nome, valor in (globais or {}).items():
        variaveis.setdefault(nome, Template(str(valor)).safe_substitute(variaveis))
    return variaveis


class ExecutorRoteiro:
    def __init__(self, driver, config, pasta_evidencias: Path):
        self.driver = driver
        self.config = config
        self.pasta_evidencias = pasta_evidencias
        self.timeout_padrao = config.get("timeout_padrao", 30)
        self.passos = config["roteiro"]
        self.variaveis_globais = config.get("variaveis", {})
        self.recuperacao = config.get("recuperacao", [{"tecla": "{ESC}"}] * 3)
        validar_roteiro(self.passos)
        validar_roteiro(self.recuperacao)
        self.usa_cnpj = "cnpj_numeros" in str(self.passos) + str(self.variaveis_globais)

    def _executar_passo(self, passo, variaveis, resultado, inicio=0.0):
        acao, valor = next(iter(passo.items()))
        valor = _substituir(valor, variaveis)
        d = self.driver
        if acao == "tecla":
            d.tecla(valor)
        elif acao == "digitar":
            d.digitar(str(valor))
        elif acao == "menu":
            d.menu(valor)
        elif acao == "clicar_botao":
            d.clicar_botao(valor)
        elif acao in ("esperar_janela", "esperar_fechar"):
            if isinstance(valor, dict):
                titulo, timeout = valor["titulo"], valor.get("timeout", self.timeout_padrao)
            else:
                titulo, timeout = valor, self.timeout_padrao
            getattr(d, acao)(titulo, timeout)
        elif acao == "aguardar":
            d.aguardar(float(valor))
        elif acao == "capturar_tela":
            arquivo = self._arquivo_evidencia(variaveis, valor)
            d.capturar_tela(arquivo)
            resultado.evidencias.append(str(arquivo))
        elif acao == "criar_pasta":
            d.criar_pasta(valor)
        elif acao == "verificar_arquivo":
            if isinstance(valor, dict):
                padrao, timeout = valor["padrao"], valor.get("timeout", self.timeout_padrao)
            else:
                padrao, timeout = valor, self.timeout_padrao
            arquivo = d.verificar_arquivo(padrao, inicio, float(timeout))
            log.info("Arquivo gerado: %s", arquivo)
            resultado.arquivos_gerados.append(str(arquivo))

    def _arquivo_evidencia(self, variaveis, sufixo):
        comp = variaveis["competencia"].replace("/", "-")
        return self.pasta_evidencias / comp / f"{variaveis['codigo']}_{sufixo}.png"

    def _conferir(self, empresa, resultado):
        if not empresa.get("receita_mes") or not empresa.get("anexo"):
            return
        try:
            calc = calcular_das(
                empresa["receita_mes"],
                empresa.get("rbt12") or "0",
                empresa["anexo"],
                empresa.get("folha12") or None,
            )
        except (ErroCalculo, ArithmeticError, ValueError) as exc:
            resultado.mensagem = f"Conferência não calculada: {exc}"
            return
        resultado.das_conferencia = f"{calc.valor_das:.2f}"
        resultado.aliquota_efetiva = f"{calc.aliquota_efetiva * 100:.4f}% (Anexo {calc.anexo}, faixa {calc.faixa})"

    def processar(self, empresa: dict, competencia: str) -> ResultadoEmpresa:
        variaveis = montar_variaveis(empresa, competencia, self.variaveis_globais)
        resultado = ResultadoEmpresa(empresa["codigo"], empresa.get("nome", ""), competencia)
        self._conferir(empresa, resultado)
        log.info("Empresa %s - %s: iniciando apuração %s", resultado.codigo, resultado.nome, competencia)
        if self.usa_cnpj and len(variaveis["cnpj_numeros"]) != 14:
            resultado.status = "ERRO"
            resultado.mensagem = "CNPJ ausente ou inválido no empresas.csv (usado no nome do arquivo)"
            log.error("Empresa %s: %s", resultado.codigo, resultado.mensagem)
            return resultado
        # Arquivos gravados antes deste instante não contam como gerados agora
        # (margem de 2s para a resolução de data/hora do sistema de arquivos)
        inicio = time.time() - 2
        try:
            for passo in self.passos:
                self._executar_passo(passo, variaveis, resultado, inicio)
        except Exception as exc:  # qualquer falha na tela não pode parar o lote
            resultado.status = "ERRO"
            resultado.mensagem = f"{type(exc).__name__}: {exc}"
            log.exception("Empresa %s: falha na apuração", resultado.codigo)
            self._recuperar(variaveis, resultado)
        return resultado

    def _recuperar(self, variaveis, resultado):
        try:
            arquivo = self._arquivo_evidencia(variaveis, f"ERRO_{datetime.now():%H%M%S}")
            self.driver.capturar_tela(arquivo)
            resultado.evidencias.append(str(arquivo))
        except Exception:
            log.warning("Não foi possível capturar a tela do erro")
        for passo in self.recuperacao:
            try:
                self._executar_passo(passo, variaveis, resultado)
            except Exception:
                log.warning("Passo de recuperação falhou: %s", passo)
