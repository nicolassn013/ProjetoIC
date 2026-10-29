"""
config.py - Lê a configuração do FTP sem nunca colocar segredo no código.

Ordem de prioridade: variáveis de ambiente > arquivo config.env na raiz do
projeto (ignorado pelo git). O modelo sem segredos é config.exemplo.env.
A senha nunca aparece em print, repr ou mensagem de erro.
"""

import os
from dataclasses import dataclass, field

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARQUIVO_ENV_PADRAO = os.path.join(PASTA_PROJETO, "config.env")


class ConfigError(Exception):
    """Configuração ausente ou inválida (a mensagem cita só o NOME da variável)."""


@dataclass(frozen=True)
class ConfigFTP:
    host: str
    usuario: str
    senha: str = field(repr=False)
    pasta: str = "/"
    porta: int = 21
    tls: bool = False


def ler_arquivo_env(caminho):
    """Lê linhas CHAVE=VALOR (ignora vazias e comentários). Arquivo ausente = {}."""
    valores = {}
    if not caminho or not os.path.exists(caminho):
        return valores
    with open(caminho, encoding="utf-8-sig") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            valores[chave.strip()] = valor.strip().strip("'").strip('"')
    return valores


def carregar_config_ftp(caminho_env=None, ambiente=None):
    """Monta o ConfigFTP. Falta de variável obrigatória levanta ConfigError."""
    ambiente = os.environ if ambiente is None else ambiente
    valores = ler_arquivo_env(caminho_env or ARQUIVO_ENV_PADRAO)
    for chave, valor in ambiente.items():
        if chave.startswith("FTP_") and str(valor).strip():
            valores[chave] = str(valor).strip()

    faltando = [
        chave for chave in ("FTP_HOST", "FTP_USER", "FTP_PASS")
        if not valores.get(chave) or valores[chave].upper().startswith("COLOQUE_")
    ]
    if faltando:
        raise ConfigError(
            f"Faltam no config.env (ou nas variáveis de ambiente): {', '.join(faltando)}. "
            "Copie config.exemplo.env para config.env e preencha."
        )
    try:
        porta = int(valores.get("FTP_PORT", "21") or "21")
    except ValueError:
        raise ConfigError("FTP_PORT precisa ser um número.")
    return ConfigFTP(
        host=valores["FTP_HOST"],
        usuario=valores["FTP_USER"],
        senha=valores["FTP_PASS"],
        pasta=valores.get("FTP_DIR", "/") or "/",
        porta=porta,
        tls=valores.get("FTP_TLS", "0").lower() in ("1", "true", "sim"),
    )
