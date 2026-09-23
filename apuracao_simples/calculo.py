"""Cálculo de conferência do DAS do Simples Nacional.

Recalcula o valor devido pelas tabelas dos Anexos I a V da LC 123/2006
(redação da LC 155/2016) para conferir o valor apurado pelo Domínio.

Alíquota efetiva = (RBT12 x Alíquota nominal - Parcela a deduzir) / RBT12
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

LIMITE_SIMPLES = Decimal("4800000")
FATOR_R_MINIMO = Decimal("0.28")

# (limite superior da faixa, alíquota nominal, parcela a deduzir)
TABELAS = {
    "I": [  # Comércio
        (Decimal("180000"), Decimal("0.04"), Decimal("0")),
        (Decimal("360000"), Decimal("0.073"), Decimal("5940")),
        (Decimal("720000"), Decimal("0.095"), Decimal("13860")),
        (Decimal("1800000"), Decimal("0.107"), Decimal("22500")),
        (Decimal("3600000"), Decimal("0.143"), Decimal("87300")),
        (Decimal("4800000"), Decimal("0.19"), Decimal("378000")),
    ],
    "II": [  # Indústria
        (Decimal("180000"), Decimal("0.045"), Decimal("0")),
        (Decimal("360000"), Decimal("0.078"), Decimal("5940")),
        (Decimal("720000"), Decimal("0.10"), Decimal("13860")),
        (Decimal("1800000"), Decimal("0.112"), Decimal("22500")),
        (Decimal("3600000"), Decimal("0.147"), Decimal("85500")),
        (Decimal("4800000"), Decimal("0.30"), Decimal("720000")),
    ],
    "III": [  # Serviços (inclui Anexo V com Fator R >= 28%)
        (Decimal("180000"), Decimal("0.06"), Decimal("0")),
        (Decimal("360000"), Decimal("0.112"), Decimal("9360")),
        (Decimal("720000"), Decimal("0.135"), Decimal("17640")),
        (Decimal("1800000"), Decimal("0.16"), Decimal("35640")),
        (Decimal("3600000"), Decimal("0.21"), Decimal("125640")),
        (Decimal("4800000"), Decimal("0.33"), Decimal("648000")),
    ],
    "IV": [  # Serviços (construção, vigilância, limpeza, advocacia...)
        (Decimal("180000"), Decimal("0.045"), Decimal("0")),
        (Decimal("360000"), Decimal("0.09"), Decimal("8100")),
        (Decimal("720000"), Decimal("0.102"), Decimal("12420")),
        (Decimal("1800000"), Decimal("0.14"), Decimal("39780")),
        (Decimal("3600000"), Decimal("0.22"), Decimal("183780")),
        (Decimal("4800000"), Decimal("0.33"), Decimal("828000")),
    ],
    "V": [  # Serviços sujeitos ao Fator R
        (Decimal("180000"), Decimal("0.155"), Decimal("0")),
        (Decimal("360000"), Decimal("0.18"), Decimal("4500")),
        (Decimal("720000"), Decimal("0.195"), Decimal("9900")),
        (Decimal("1800000"), Decimal("0.205"), Decimal("17100")),
        (Decimal("3600000"), Decimal("0.23"), Decimal("62100")),
        (Decimal("4800000"), Decimal("0.305"), Decimal("540000")),
    ],
}


class ErroCalculo(ValueError):
    pass


@dataclass(frozen=True)
class ResultadoCalculo:
    anexo: str
    faixa: int
    aliquota_nominal: Decimal
    parcela_deduzir: Decimal
    aliquota_efetiva: Decimal
    valor_das: Decimal


def _dec(valor) -> Decimal:
    if isinstance(valor, Decimal):
        return valor
    texto = str(valor).strip()
    # Aceita formato brasileiro "1.234,56"
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return Decimal(texto or "0")


def anexo_efetivo(anexo: str, rbt12, folha12=None) -> str:
    """Aplica o Fator R: Anexo V vai para o III quando folha12/RBT12 >= 28%."""
    anexo = anexo.strip().upper()
    if anexo not in TABELAS:
        raise ErroCalculo(f"Anexo inválido: {anexo!r} (use I, II, III, IV ou V)")
    if anexo == "V" and folha12 is not None:
        rbt12, folha12 = _dec(rbt12), _dec(folha12)
        if rbt12 > 0 and folha12 / rbt12 >= FATOR_R_MINIMO:
            return "III"
    return anexo


def calcular_das(receita_mes, rbt12, anexo: str, folha12=None) -> ResultadoCalculo:
    """Calcula o DAS do mês para uma única atividade/anexo.

    Para início de atividade (RBT12 zerado) usa a alíquota nominal da 1ª faixa.
    Não trata sublimite de ICMS/ISS, retenções nem segregação por tributo.
    """
    receita_mes, rbt12 = _dec(receita_mes), _dec(rbt12)
    if receita_mes < 0 or rbt12 < 0:
        raise ErroCalculo("Receita e RBT12 não podem ser negativos")
    if rbt12 > LIMITE_SIMPLES:
        raise ErroCalculo(f"RBT12 {rbt12} acima do limite do Simples ({LIMITE_SIMPLES})")

    anexo = anexo_efetivo(anexo, rbt12, folha12)
    for faixa, (limite, nominal, deduzir) in enumerate(TABELAS[anexo], start=1):
        if rbt12 <= limite:
            break

    if rbt12 == 0:
        efetiva = nominal
    else:
        efetiva = (rbt12 * nominal - deduzir) / rbt12

    valor = (receita_mes * efetiva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return ResultadoCalculo(
        anexo=anexo,
        faixa=faixa,
        aliquota_nominal=nominal,
        parcela_deduzir=deduzir,
        aliquota_efetiva=efetiva.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
        valor_das=valor,
    )
