import os
import time
from pathlib import Path

import pytest
import yaml

from apuracao_simples.__main__ import ler_empresas, main
from apuracao_simples.driver import DriverSimulado, ErroAutomacao, aguardar_arquivo
from apuracao_simples.roteiro import ExecutorRoteiro, montar_variaveis, validar_roteiro

RAIZ = Path(__file__).resolve().parent.parent
CNPJ = "00.000.000/0001-00"


def config_exemplo():
    return yaml.safe_load((RAIZ / "config.exemplo.yaml").read_text(encoding="utf-8"))


def test_roteiro_substitui_variaveis(tmp_path):
    driver = DriverSimulado()
    executor = ExecutorRoteiro(driver, config_exemplo(), tmp_path)
    r = executor.processar({"codigo": "12", "nome": "X", "anexo": "I", "cnpj": CNPJ,
                            "receita_mes": "50000,00", "rbt12": "600000,00"}, "08/2026")
    assert r.status == "OK"
    assert ("digitar", "12") in driver.acoes
    assert ("digitar", "08/2026") in driver.acoes
    assert r.das_conferencia == "3595.00"
    assert r.evidencias[0].endswith("08-2026/12_apuracao.png")


def test_erro_em_uma_empresa_nao_para_o_lote(tmp_path):
    class DriverQuebrado(DriverSimulado):
        def menu(self, caminho):
            raise TimeoutError("menu não encontrado")

    driver = DriverQuebrado()
    r = ExecutorRoteiro(driver, config_exemplo(), tmp_path).processar(
        {"codigo": "1", "cnpj": CNPJ}, "08/2026")
    assert r.status == "ERRO"
    assert "menu não encontrado" in r.mensagem
    assert driver.acoes[-1] == ("tecla", "{ESC}")


def test_acao_desconhecida():
    with pytest.raises(ValueError):
        validar_roteiro([{"clicar_mouse": "x"}])


def test_ler_empresas_ignora_inativas():
    empresas = ler_empresas(RAIZ / "empresas.exemplo.csv")
    assert [e["codigo"] for e in empresas] == ["1", "2"]


def test_main_simulado(tmp_path):
    codigo = main(["--competencia", "08/2026", "--simular",
                   "--config", str(RAIZ / "config.exemplo.yaml"),
                   "--empresas", str(RAIZ / "empresas.exemplo.csv"),
                   "--saida", str(tmp_path)])
    assert codigo == 0
    relatorio = next(tmp_path.glob("relatorio_08-2026_*.csv")).read_text(encoding="utf-8-sig")
    assert "3595.00" in relatorio and "1460.00" in relatorio


def test_variaveis_derivadas_e_globais():
    v = montar_variaveis({"codigo": "1", "cnpj": CNPJ}, "08/2026",
                         {"pasta_pgdas": "C:/PGDAS/$competencia_aaaamm"})
    assert v["competencia_mmaaaa"] == "082026"
    assert v["cnpj_numeros"] == "00000000000100"
    assert v["pasta_pgdas"] == "C:/PGDAS/202608"


def test_coluna_da_empresa_tem_prioridade_sobre_variavel_global():
    v = montar_variaveis({"codigo": "1", "pasta_pgdas": "D:/cliente1"}, "08/2026",
                         {"pasta_pgdas": "C:/PGDAS"})
    assert v["pasta_pgdas"] == "D:/cliente1"


def test_pgdas_no_roteiro_simulado(tmp_path):
    driver = DriverSimulado()
    r = ExecutorRoteiro(driver, config_exemplo(), tmp_path).processar(
        {"codigo": "1", "cnpj": CNPJ}, "08/2026")
    assert r.status == "OK"
    assert ("menu", "Arquivos->Simples Nacional->PGDAS-D") in driver.acoes
    assert r.arquivos_gerados == ["C:\\PGDAS-D\\202608\\PGDASD_00000000000100_202608*"]


def test_empresa_sem_cnpj_nao_executa(tmp_path):
    driver = DriverSimulado()
    r = ExecutorRoteiro(driver, config_exemplo(), tmp_path).processar({"codigo": "1"}, "08/2026")
    assert r.status == "ERRO" and "CNPJ" in r.mensagem
    assert driver.acoes == []


def test_pgdas_nao_gerado_marca_erro(tmp_path):
    class DriverSemArquivo(DriverSimulado):
        def verificar_arquivo(self, padrao, desde, timeout):
            return aguardar_arquivo(str(tmp_path / "nada*"), desde, 0, intervalo=0)

    r = ExecutorRoteiro(DriverSemArquivo(), config_exemplo(), tmp_path).processar(
        {"codigo": "1", "cnpj": CNPJ}, "08/2026")
    assert r.status == "ERRO" and "Arquivo não gerado" in r.mensagem


def test_aguardar_arquivo_ignora_antigos_e_vazios(tmp_path):
    antigo = tmp_path / "PGDASD_antigo.txt"
    antigo.write_text("x")
    os.utime(antigo, (1000, 1000))
    (tmp_path / "PGDASD_vazio.txt").touch()
    with pytest.raises(ErroAutomacao):
        aguardar_arquivo(str(tmp_path / "PGDASD_*"), time.time() - 60, 0, intervalo=0)
    novo = tmp_path / "PGDASD_novo.txt"
    novo.write_text("conteudo")
    assert aguardar_arquivo(str(tmp_path / "PGDASD_*"), time.time() - 60, 0) == novo
