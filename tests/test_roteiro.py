from pathlib import Path

import pytest
import yaml

from apuracao_simples.__main__ import ler_empresas, main
from apuracao_simples.driver import DriverSimulado
from apuracao_simples.roteiro import ExecutorRoteiro, validar_roteiro

RAIZ = Path(__file__).resolve().parent.parent


def config_exemplo():
    return yaml.safe_load((RAIZ / "config.exemplo.yaml").read_text(encoding="utf-8"))


def test_roteiro_substitui_variaveis(tmp_path):
    driver = DriverSimulado()
    executor = ExecutorRoteiro(driver, config_exemplo(), tmp_path)
    r = executor.processar({"codigo": "12", "nome": "X", "anexo": "I",
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
    r = ExecutorRoteiro(driver, config_exemplo(), tmp_path).processar({"codigo": "1"}, "08/2026")
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
