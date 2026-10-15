"""
banco.py - Camada de conexão com o SQLite (Passo 6).

Toda a lógica de "onde está o banco" e "como abrir/fechar conexão" fica
isolada aqui, pra não espalhar caminho de arquivo pelo resto do código.
"""

import os
import sqlite3
from contextlib import contextmanager

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PASTA_PROJETO, "dados", "leituras.db")


class BancoNaoEncontrado(Exception):
    """Levantada quando o leituras.db não existe no caminho esperado."""


@contextmanager
def conectar():
    """Abre a conexão para LEITURA (dashboard, consultas ad-hoc). Exige que
    o banco já exista -- é um erro real se não existir, porque quem só lê
    não tem por que criar o banco na hora.

    Uso:
        with conectar() as conn:
            df = pd.read_sql("SELECT ...", conn)
    """
    if not os.path.exists(DB_PATH):
        raise BancoNaoEncontrado(
            f"Não encontrei o banco em {DB_PATH}. "
            "Rode 'python pipeline/carrega_banco.py' antes de abrir o dashboard."
        )
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def conectar_ou_criar():
    """Abre a conexão para ESCRITA (pipeline/carrega_banco.py). Cria o
    arquivo/pasta se ainda não existir -- é o comportamento certo pra quem
    está justamente povoando o banco pela primeira vez."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
