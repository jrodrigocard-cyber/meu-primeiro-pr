from decimal import Decimal

import pytest

from apuracao_simples.calculo import ErroCalculo, anexo_efetivo, calcular_das


def test_anexo_i_terceira_faixa():
    r = calcular_das("50000,00", "600000,00", "I")
    assert r.faixa == 3
    assert r.aliquota_efetiva == Decimal("0.071900")
    assert r.valor_das == Decimal("3595.00")


def test_fator_r_leva_anexo_v_para_iii():
    r = calcular_das("20000", "240000", "V", folha12="72000")
    assert r.anexo == "III"
    assert r.valor_das == Decimal("1460.00")


def test_anexo_v_sem_fator_r():
    r = calcular_das("20000", "240000", "V", folha12="60000")
    assert r.anexo == "V"
    assert r.valor_das == Decimal("3225.00")


def test_primeira_faixa_sem_deducao():
    r = calcular_das("10000", "180000", "III")
    assert r.faixa == 1
    assert r.valor_das == Decimal("600.00")


def test_inicio_de_atividade_usa_aliquota_nominal():
    assert calcular_das("10000", "0", "I").valor_das == Decimal("400.00")


def test_limite_excedido():
    with pytest.raises(ErroCalculo):
        calcular_das("1000", "4800000.01", "I")


def test_anexo_invalido():
    with pytest.raises(ErroCalculo):
        anexo_efetivo("VI", "1000")
