"""
migracoes.py - Aplica as mudanças de estrutura do banco, uma de cada vez.

Cada arquivo de app/migracoes/NNN_nome.sql é uma mudança. O número da última
aplicada fica gravado dentro do próprio banco (PRAGMA user_version). Assim
qualquer pessoa refaz o banco do zero, e um banco antigo é atualizado só com
o que faltava. Nunca edite um .sql já aplicado: crie o próximo número.
"""

import os
import re
import sqlite3
from datetime import datetime

import banco

PASTA_MIGRACOES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migracoes")
_PADRAO = re.compile(r"^(\d{3})_.+\.sql$")


def listar_migracoes():
    """[(numero, caminho)] em ordem. Falha se houver número repetido ou faltando."""
    achadas = []
    for nome in sorted(os.listdir(PASTA_MIGRACOES)):
        m = _PADRAO.match(nome)
        if m:
            achadas.append((int(m.group(1)), os.path.join(PASTA_MIGRACOES, nome)))
    numeros = [n for n, _ in achadas]
    if numeros != list(range(1, len(numeros) + 1)):
        raise RuntimeError(f"Migrações com numeração quebrada: {numeros} (esperado 1, 2, 3...)")
    return achadas


def versao_atual(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _banco_tem_dados(conn):
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
    ).fetchone()[0] > 0


def _fazer_backup(conn, versao_de, versao_para):
    pasta = os.path.join(os.path.dirname(banco.DB_PATH), "backups")
    os.makedirs(pasta, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(pasta, f"leituras_v{versao_de}_para_v{versao_para}_{carimbo}.db")
    copia = sqlite3.connect(destino)
    try:
        conn.backup(copia)
    finally:
        copia.close()
    return destino


def aplicar(conn):
    """Aplica as migrações pendentes. Devolve a lista de números aplicados
    (vazia se o banco já estava atualizado). Se o banco já tinha tabelas,
    guarda uma cópia em dados/backups/ antes de mudar qualquer coisa."""
    migracoes = listar_migracoes()
    atual = versao_atual(conn)
    pendentes = [(n, c) for n, c in migracoes if n > atual]
    if not pendentes:
        return []

    if _banco_tem_dados(conn):
        _fazer_backup(conn, atual, pendentes[-1][0])

    aplicadas = []
    for numero, caminho in pendentes:
        with open(caminho, encoding="utf-8") as f:
            sql = f.read()
        try:
            conn.executescript(f"BEGIN;\n{sql}\nPRAGMA user_version = {numero};\nCOMMIT;")
        except sqlite3.Error:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        aplicadas.append(numero)
    return aplicadas
