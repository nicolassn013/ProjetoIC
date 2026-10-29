"""
PASSO 5 - Persistencia em Banco de Dados Relacional (SQLite)

Este script agora e' so' um orquestrador fino: toda a logica de "como o
banco e' estruturado e como gravar nele" mora em consultas.py (que tambem
e' usado pelo dashboard para ler). Antes esse conhecimento estava duplicado
entre este arquivo e consultas.py -- e' a consolidacao de Repository que
estava pendente na revisao arquitetural.

Consome as saidas do Passo 4 (arquivos XLSX de integracao diaria e o
historico anual) e grava tudo em dados/leituras.db. Idempotente: rodar
varias vezes nao duplica nada.
"""

import os
import re
import glob
import sys

import pandas as pd

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(PASTA_PROJETO, "dados")
PASTA_PROCESSADOS = os.path.join(PASTA_DADOS, "processados")

sys.path.insert(0, os.path.join(PASTA_PROJETO, "app"))
import banco       # noqa: E402
import consultas   # noqa: E402


def processar_historico_anual(conn):
    print("-> Processando historico anual...")
    caminho = os.path.join(PASTA_PROCESSADOS, "historico_anual_inversores.xlsx")
    if not os.path.exists(caminho):
        print("   [Aviso] Arquivo de historico anual nao encontrado. Pulando.")
        return

    df_inv = pd.read_excel(caminho, sheet_name="por_inversor")
    df_usina = pd.read_excel(caminho, sheet_name="usina_total")
    consultas.salvar_historico_anual(conn, df_inv, df_usina)
    print(f"   [OK] {len(df_inv)} linhas de inversor + {len(df_usina)} linha de usina salvas.")


def processar_dados_diarios(conn):
    print("\n-> Processando integracoes diarias...")
    arquivos = glob.glob(os.path.join(PASTA_PROCESSADOS, "integracao_usina_*.xlsx"))

    total = 0
    total_meteo = 0
    for arq in sorted(arquivos):
        m = re.search(r"integracao_usina_(\d{8})\.xlsx", arq)
        if not m:
            continue

        data_str = m.group(1)
        print(f"   Processando dia: {data_str}")

        df_15min = pd.read_excel(arq, sheet_name="integracao_15min")
        df_resumo = pd.read_excel(arq, sheet_name="resumo")

        df_resumo_pivot = df_resumo.set_index("indicador").T
        data_iso = df_resumo_pivot["data"].values[0]

        df_15min["timestamp_15min"] = pd.to_datetime(df_15min["timestamp_15min"])

        troca = consultas.salvar_dia(conn, data_iso, df_15min, df_resumo_pivot)
        if troca["linhas_depois"] < troca["linhas_antes"]:
            print(f"   [Aviso] {data_iso}: o dia tinha {troca['linhas_antes']} linhas e passou a ter "
                  f"{troca['linhas_depois']} (carga incompleta substituiu dia completo?).")
        total += len(df_15min)

        if "meteorologia_15min" in pd.ExcelFile(arq).sheet_names:
            df_meteo = pd.read_excel(arq, sheet_name="meteorologia_15min")
            if df_meteo.empty:
                print(f"   [Aviso] {data_iso}: sem meteorologia completa neste dia (fora da cobertura).")
            else:
                resposta = consultas.salvar_meteorologia(conn, df_meteo)
                for dia in resposta["dias_com_menos_linhas"]:
                    c = resposta["dias"][dia]
                    print(f"   [Aviso] meteorologia {dia}: {c['linhas_antes']} -> {c['linhas_depois']} linhas.")
                total_meteo += len(df_meteo)

    print(f"   [OK] {total} registros de 15min inseridos no total.")
    print(f"   [OK] {total_meteo} registros de meteorologia completa inseridos no total.")


def validar(conn):
    print("\n-> Validacao pos-carga:")
    cobertura = consultas.cobertura_geral(conn)
    for chave, valor in cobertura.items():
        print(f"   {chave}: {valor}")
    diferencas = consultas.verificar_schema_meteorologia(conn)
    if diferencas["faltando_no_banco"] or diferencas["sobrando_no_banco"]:
        print(f"   [Aviso] meteorologia_15min diverge do catálogo: {diferencas}")


if __name__ == "__main__":
    print("=" * 60)
    print("PASSO 5 - POPULAR BANCO DE DADOS (SQLite)")
    print("=" * 60)

    with banco.conectar_ou_criar() as conexao:
        aplicadas = consultas.inicializar_schema(conexao)
        if aplicadas:
            print(f"-> Migracoes aplicadas: {aplicadas} (copia de seguranca em dados/backups/ se o banco ja existia)")
        processar_historico_anual(conexao)
        processar_dados_diarios(conexao)
        validar(conexao)

    print("\n" + "=" * 60)
    print(f"PASSO 5 CONCLUIDO! Banco criado em: {banco.DB_PATH}")
    print("=" * 60)
