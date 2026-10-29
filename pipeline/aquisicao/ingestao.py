"""
ingestao.py - Orquestra: fonte -> leitura -> tratamento -> banco -> diário.

Cada arquivo é processado de forma independente: se um falhar, os outros
seguem e o erro fica anotado no diário (tabela ingestao_arquivos). Arquivo
com o mesmo nome e o mesmo conteúdo já processado com sucesso é pulado.
A gravação usa modo="mesclar": cada arquivo só troca os horários que traz,
sem apagar o resto do dia.
"""

import hashlib
import os
from dataclasses import dataclass

import banco
import consultas

from .leitor import ler_maws55
from .tratamento import tratar

PASTA_BRUTOS = os.path.join(banco.PASTA_PROJETO, "dados", "brutos", "maws55")


@dataclass
class ResultadoArquivo:
    nome: str
    status: str            # 'ok', 'erro', 'ignorado' (já processado) ou 'simulado'
    linhas_lidas: int = 0
    linhas_gravadas: int = 0
    mensagem: str = ""


def sha256(conteudo):
    return hashlib.sha256(conteudo).hexdigest()


def guardar_copia_bruta(nome, conteudo, pasta=None):
    """Guarda o arquivo exatamente como veio. Mesmo nome com conteúdo diferente
    não sobrescreve: ganha o sufixo do hash."""
    pasta = pasta or PASTA_BRUTOS
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, os.path.basename(nome))
    if os.path.exists(destino):
        with open(destino, "rb") as f:
            if f.read() == conteudo:
                return destino
        destino = f"{destino}.{sha256(conteudo)[:8]}"
    with open(destino, "wb") as f:
        f.write(conteudo)
    return destino


def _mensagem_aviso(bruto, tratado):
    avisos = []
    if bruto.attrs.get("linhas_layout_52"):
        avisos.append(f"layout antigo de 52 valores (grupo NTC vazio): {bruto.attrs['linhas_layout_52']} linha(s)")
    if bruto.attrs.get("valores_nao_numericos"):
        avisos.append(f"valores não numéricos virados vazio: {bruto.attrs['valores_nao_numericos']}")
    if bruto.attrs.get("linhas_invalidas"):
        avisos.append(f"linhas fora do formato descartadas: {bruto.attrs['linhas_invalidas']}")
    if tratado.attrs.get("duplicados_descartados"):
        avisos.append(f"horários repetidos no mesmo bloco de 15 min: {tratado.attrs['duplicados_descartados']}")
    return "; ".join(avisos)


def processar_arquivo(conn, fonte, nome, simular=False, guardar_bruto=True, pasta_brutos=None):
    try:
        conteudo = fonte.ler(nome)
    except Exception as erro:
        mensagem = f"{type(erro).__name__}: {erro}"
        if not simular:
            consultas.registrar_ingestao(conn, fonte.origem, nome, "sem-conteudo", "erro", mensagem=mensagem)
        return ResultadoArquivo(nome, "erro", mensagem=mensagem)

    hash_arquivo = sha256(conteudo)
    if consultas.ingestao_ja_feita(conn, nome, hash_arquivo):
        return ResultadoArquivo(nome, "ignorado", mensagem="já processado")

    if guardar_bruto and not simular and fonte.origem == "ftp":
        guardar_copia_bruta(nome, conteudo, pasta_brutos)

    try:
        bruto = ler_maws55(conteudo)
        tratado = tratar(bruto)
        if tratado.empty:
            raise ValueError("arquivo sem nenhuma linha com horário válido")
        aviso = _mensagem_aviso(bruto, tratado)
        if simular:
            return ResultadoArquivo(nome, "simulado", len(bruto), len(tratado), aviso)
        consultas.salvar_meteorologia(conn, tratado, modo="mesclar")
        consultas.registrar_ingestao(
            conn, fonte.origem, nome, hash_arquivo, "ok", linhas_lidas=len(bruto),
            linhas_gravadas=len(tratado), primeiro_registro=tratado["timestamp_original"].min(),
            ultimo_registro=tratado["timestamp_original"].max(), mensagem=aviso or None)
        return ResultadoArquivo(nome, "ok", len(bruto), len(tratado), aviso)
    except Exception as erro:
        conn.rollback()
        mensagem = f"{type(erro).__name__}: {erro}"
        if not simular:
            consultas.registrar_ingestao(conn, fonte.origem, nome, hash_arquivo, "erro", mensagem=mensagem)
        return ResultadoArquivo(nome, "erro", mensagem=mensagem)


def executar(conn, fonte, nomes, simular=False, guardar_bruto=True, pasta_brutos=None):
    """Processa os arquivos na ordem dada e devolve a lista de ResultadoArquivo."""
    return [processar_arquivo(conn, fonte, n, simular, guardar_bruto, pasta_brutos) for n in nomes]
