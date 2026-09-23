"""Controle da interface do Domínio Escrita Fiscal.

`DriverDominio` usa pywinauto (somente Windows) e se conecta a uma sessão do
Domínio já aberta e logada. `DriverSimulado` apenas registra as ações e serve
para testar o roteiro (--simular) em qualquer sistema operacional.
"""

import glob
import logging
import time
from pathlib import Path

log = logging.getLogger(__name__)


class ErroAutomacao(RuntimeError):
    pass


def aguardar_arquivo(padrao: str, desde: float, timeout: float, intervalo: float = 1.0) -> Path:
    """Espera surgir um arquivo não vazio que case com `padrao` e foi gravado após `desde`."""
    limite = time.monotonic() + timeout
    while True:
        candidatos = [
            Path(c) for c in glob.glob(padrao)
            if Path(c).is_file() and Path(c).stat().st_mtime >= desde and Path(c).stat().st_size > 0
        ]
        if candidatos:
            return max(candidatos, key=lambda c: c.stat().st_mtime)
        if time.monotonic() >= limite:
            raise ErroAutomacao(f"Arquivo não gerado em {timeout:.0f}s: {padrao}")
        time.sleep(intervalo)


class DriverSimulado:
    def __init__(self):
        self.acoes = []

    def _registrar(self, *acao):
        self.acoes.append(acao)
        log.info("[simulado] %s", " ".join(str(a) for a in acao))

    def conectar(self):
        self._registrar("conectar")

    def tecla(self, teclas):
        self._registrar("tecla", teclas)

    def digitar(self, texto):
        self._registrar("digitar", texto)

    def menu(self, caminho):
        self._registrar("menu", caminho)

    def clicar_botao(self, titulo):
        self._registrar("clicar_botao", titulo)

    def esperar_janela(self, titulo, timeout):
        self._registrar("esperar_janela", titulo)

    def esperar_fechar(self, titulo, timeout):
        self._registrar("esperar_fechar", titulo)

    def aguardar(self, segundos):
        self._registrar("aguardar", segundos)

    def capturar_tela(self, arquivo: Path):
        self._registrar("capturar_tela", arquivo.name)

    def criar_pasta(self, pasta):
        self._registrar("criar_pasta", pasta)

    def verificar_arquivo(self, padrao, desde, timeout):
        self._registrar("verificar_arquivo", padrao)
        return Path(padrao)


class DriverDominio:
    def __init__(self, titulo_janela: str, backend: str = "win32"):
        self.titulo_janela = titulo_janela
        self.backend = backend
        self.app = None
        self.janela = None

    def conectar(self):
        try:
            from pywinauto import Application
        except ImportError as exc:
            raise ErroAutomacao(
                "pywinauto não instalado. Rode: pip install -r requirements.txt (no Windows)"
            ) from exc
        try:
            self.app = Application(backend=self.backend).connect(
                title_re=self.titulo_janela, timeout=10
            )
        except Exception as exc:
            raise ErroAutomacao(
                f"Janela do Domínio não encontrada ({self.titulo_janela!r}). "
                "Abra o Domínio Escrita Fiscal e faça login antes de rodar."
            ) from exc
        self.janela = self.app.window(title_re=self.titulo_janela)
        self.janela.set_focus()

    def _ativa(self):
        return self.app.top_window()

    def tecla(self, teclas):
        from pywinauto.keyboard import send_keys

        send_keys(teclas, pause=0.05)

    def digitar(self, texto):
        from pywinauto.keyboard import send_keys

        # with_spaces preserva espaços; caracteres especiais do send_keys são escapados
        escapado = "".join("{%s}" % c if c in "{}+^%~()" else c for c in texto)
        send_keys(escapado, with_spaces=True, pause=0.03)

    def menu(self, caminho):
        self.janela.set_focus()
        self.janela.menu_select(caminho)

    def clicar_botao(self, titulo):
        self._ativa().child_window(title_re=titulo, class_name_re=".*Button.*").click_input()

    def esperar_janela(self, titulo, timeout):
        self.app.window(title_re=titulo).wait("visible", timeout=timeout)

    def esperar_fechar(self, titulo, timeout):
        self.app.window(title_re=titulo).wait_not("visible", timeout=timeout)

    def aguardar(self, segundos):
        time.sleep(segundos)

    def capturar_tela(self, arquivo: Path):
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        self._ativa().capture_as_image().save(arquivo)

    def criar_pasta(self, pasta):
        Path(pasta).mkdir(parents=True, exist_ok=True)

    def verificar_arquivo(self, padrao, desde, timeout):
        return aguardar_arquivo(padrao, desde, timeout)
