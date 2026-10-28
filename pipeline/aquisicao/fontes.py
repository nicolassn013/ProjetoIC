"""
fontes.py - De onde vêm os arquivos .txt da estação.

Duas fontes com a mesma interface (listar / ler):
  FonteFTP         lê direto do servidor FTP da estação;
  FontePastaLocal  lê de uma pasta do computador (arquivos baixados à mão com
                   o FileZilla, ou arquivos de teste).
O resto do código só conhece a interface, então trocar de fonte não muda
o tratamento nem a gravação no banco.
"""

import ftplib
import io
import os
import re
import time

from .config import ConfigFTP

PADRAO_ARQUIVO = re.compile(r"_15m_(\d{8})_(\d{4})\.txt$", re.IGNORECASE)


def filtrar_e_ordenar(nomes, periodo=None, ultimos=None):
    """Mantém só nomes no padrão *_15m_AAAAMMDD_HHMM.txt, em ordem cronológica.

    periodo: None, 'tudo' ou prefixo de data (AAAA, AAAAMM, AAAAMMDD).
    ultimos: se não houver período, fica só com os N mais recentes.
    """
    validos = []
    for nome in nomes:
        base = os.path.basename(str(nome).strip().replace("\\", "/"))
        achado = PADRAO_ARQUIVO.search(base)
        if achado:
            validos.append((achado.groups(), base))
    validos.sort()
    nomes_validos = [base for _, base in validos]

    if periodo and periodo.lower() != "tudo":
        if not re.fullmatch(r"\d{4}(\d{2}(\d{2})?)?", periodo):
            raise ValueError("periodo deve ser 'tudo', AAAA, AAAAMM ou AAAAMMDD")
        return [b for (g, b) in validos if g[0].startswith(periodo)]
    if periodo and periodo.lower() == "tudo":
        return nomes_validos
    if ultimos is not None:
        return nomes_validos[-int(ultimos):] if int(ultimos) > 0 else []
    return nomes_validos


class FontePastaLocal:
    origem = "pasta"

    def __init__(self, pasta):
        self.pasta = pasta

    def __enter__(self):
        if not os.path.isdir(self.pasta):
            raise FileNotFoundError(f"Pasta não encontrada: {self.pasta}")
        return self

    def __exit__(self, *erro):
        return False

    def listar(self):
        return os.listdir(self.pasta)

    def ler(self, nome):
        with open(os.path.join(self.pasta, os.path.basename(nome)), "rb") as f:
            return f.read()


class FonteFTP:
    origem = "ftp"

    def __init__(self, config: ConfigFTP, fabrica_ftp=None, tentativas=3, espera_s=3.0):
        self.config = config
        self._fabrica = fabrica_ftp or (ftplib.FTP_TLS if config.tls else ftplib.FTP)
        self._tentativas = tentativas
        self._espera_s = espera_s
        self._ftp = None

    def _conectar(self):
        ftp = self._fabrica(timeout=45)
        ftp.connect(self.config.host, self.config.porta)
        ftp.login(self.config.usuario, self.config.senha)
        if self.config.tls:
            ftp.prot_p()
        ftp.set_pasv(True)
        if self.config.pasta and self.config.pasta != "/":
            ftp.cwd(self.config.pasta)
        self._ftp = ftp

    def __enter__(self):
        try:
            self._conectar()
        except Exception as erro:
            raise ConnectionError(
                f"Falha ao conectar no FTP {self.config.host}:{self.config.porta} "
                f"({type(erro).__name__}). Confira a rede do campus e as credenciais."
            ) from None
        return self

    def __exit__(self, *erro):
        self._fechar()
        return False

    def _fechar(self):
        if self._ftp is not None:
            try:
                self._ftp.quit()
            except Exception:
                pass
            self._ftp = None

    def listar(self):
        return self._ftp.nlst()

    def ler(self, nome):
        """Baixa um arquivo. Em falha, reconecta e tenta de novo (até 'tentativas')."""
        ultimo = None
        for tentativa in range(1, self._tentativas + 1):
            try:
                buf = io.BytesIO()
                self._ftp.retrbinary(f"RETR {os.path.basename(nome)}", buf.write)
                return buf.getvalue()
            except Exception as erro:
                ultimo = erro
                if tentativa < self._tentativas:
                    time.sleep(self._espera_s)
                    self._fechar()
                    try:
                        self._conectar()
                    except Exception as erro_conexao:
                        ultimo = erro_conexao
        raise ConnectionError(f"Não consegui baixar '{nome}' ({type(ultimo).__name__}).") from None


def criar_fonte(tipo, config=None, pasta=None):
    if tipo == "pasta":
        if not pasta:
            raise ValueError("Informe --pasta com a pasta dos arquivos .txt.")
        return FontePastaLocal(pasta)
    if tipo == "ftp":
        if config is None:
            raise ValueError("Fonte FTP precisa de configuração.")
        return FonteFTP(config)
    raise ValueError(f"fonte desconhecida: {tipo!r} (use 'ftp' ou 'pasta')")
