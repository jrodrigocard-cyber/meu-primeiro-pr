"""Linha de comando: python -m apuracao_simples --competencia 08/2026 [--simular]"""

import argparse
import csv
import logging
import re
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import yaml

from .driver import DriverDominio, DriverSimulado, ErroAutomacao
from .roteiro import ExecutorRoteiro

log = logging.getLogger("apuracao_simples")


def ler_empresas(caminho: Path, filtro=None):
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        amostra = f.read(2048)
        f.seek(0)
        delimitador = ";" if amostra.count(";") >= amostra.count(",") else ","
        empresas = []
        for linha in csv.DictReader(f, delimiter=delimitador):
            linha = {k.strip().lower(): (v or "").strip() for k, v in linha.items() if k}
            if not linha.get("codigo"):
                continue
            if linha.get("ativo", "S").upper() in ("N", "NAO", "NÃO", "0"):
                continue
            if filtro and linha["codigo"] not in filtro:
                continue
            empresas.append(linha)
    return empresas


def gravar_relatorio(resultados, caminho: Path):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        campos = list(asdict(resultados[0]).keys()) if resultados else ["codigo"]
        escritor = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        escritor.writeheader()
        for r in resultados:
            linha = asdict(r)
            linha["arquivos_gerados"] = " | ".join(linha["arquivos_gerados"])
            linha["evidencias"] = " | ".join(linha["evidencias"])
            escritor.writerow(linha)


def main(argv=None):
    p = argparse.ArgumentParser(description="Apuração do Simples Nacional no Domínio Escrita Fiscal")
    p.add_argument("--competencia", required=True, help="Competência no formato MM/AAAA")
    p.add_argument("--config", default="config.yaml", type=Path)
    p.add_argument("--empresas", default="empresas.csv", type=Path)
    p.add_argument("--somente", nargs="*", help="Processar apenas estes códigos de empresa")
    p.add_argument("--simular", action="store_true", help="Não controla o Domínio; só mostra os passos")
    p.add_argument("--saida", default="saida", type=Path, help="Pasta de relatórios e evidências")
    args = p.parse_args(argv)

    if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{4}", args.competencia):
        p.error("competência deve estar no formato MM/AAAA, ex.: 08/2026")

    args.saida.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(args.saida / f"log_{carimbo}.txt", encoding="utf-8"),
        ],
    )

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    empresas = ler_empresas(args.empresas, set(args.somente or []))
    if not empresas:
        log.error("Nenhuma empresa ativa encontrada em %s", args.empresas)
        return 1

    if args.simular:
        driver = DriverSimulado()
    else:
        driver = DriverDominio(config.get("titulo_janela", ".*Dom[ií]nio.*Escrita Fiscal.*"),
                               config.get("backend", "win32"))
    try:
        driver.conectar()
    except ErroAutomacao as exc:
        log.error("%s", exc)
        return 1

    executor = ExecutorRoteiro(driver, config, args.saida / "evidencias")
    resultados = [executor.processar(e, args.competencia) for e in empresas]

    relatorio = args.saida / f"relatorio_{args.competencia.replace('/', '-')}_{carimbo}.csv"
    gravar_relatorio(resultados, relatorio)
    erros = sum(r.status != "OK" for r in resultados)
    log.info("Concluído: %d empresas, %d com erro. Relatório: %s", len(resultados), erros, relatorio)
    return 2 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
