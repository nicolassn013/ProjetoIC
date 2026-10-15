"""
consultas.py - Todas as queries usadas pelo dashboard, num lugar só.

Cada função recebe uma conexão já aberta (ver banco.conectar) e devolve um
DataFrame pronto pra uso. Nenhuma função aqui inventa dado: se a tabela
estiver vazia ou a data não existir, o retorno é um DataFrame vazio, e quem
decide o que mostrar na tela é o dashboard.py.
"""

import pandas as pd

ANOS = [str(a) for a in range(2020, 2027)]


# ============================================================
# ESCRITA (antes vivia espalhada dentro de pipeline/carrega_banco.py;
# consolidado aqui pra existir um único lugar que conhece o schema
# inteiro do banco, tanto pra ler quanto pra gravar).
# ============================================================

def inicializar_schema(conn):
    """Cria as tabelas se ainda não existirem. Idempotente por natureza
    (CREATE TABLE IF NOT EXISTS)."""
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leitura_15min (
            timestamp_15min DATETIME PRIMARY KEY,
            potencia_fv_kw REAL,
            potencia_inversores_soma_kw REAL,
            INV01 REAL, INV02 REAL, INV03 REAL, INV04 REAL,
            ghi_lppyra02_w_m2 REAL, ghi_lpnet14_w_m2 REAL,
            temperatura_c REAL, vento_m_s REAL, precipitacao REAL,
            meteorologia_disponivel BOOLEAN, ghi_disponivel BOOLEAN
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumo_diario (
            data DATE PRIMARY KEY,
            registros_eletricos_5min INTEGER,
            registros_com_potencia_usina INTEGER,
            registros_com_4_inversores INTEGER,
            registros_15min INTEGER,
            registros_com_meteorologia INTEGER,
            correlacao_usina_vs_soma_inversores REAL,
            geracao_max_inv01_kw REAL, geracao_max_inv02_kw REAL,
            geracao_max_inv03_kw REAL, geracao_max_inv04_kw REAL
        )
    ''')
    conn.commit()


def salvar_dia(conn, data_iso, df_15min, df_resumo_pivot):
    """Grava (de forma idempotente) um dia inteiro: apaga o que já existia
    daquela data em leitura_15min/resumo_diario e insere de novo.

    df_15min: já vem pronto (mesmas colunas da tabela leitura_15min).
    df_resumo_pivot: 1 linha, colunas = indicadores do resumo do Passo 4.
    """
    colunas_15min = [
        "timestamp_15min", "potencia_fv_kw", "potencia_inversores_soma_kw",
        "INV01", "INV02", "INV03", "INV04", "ghi_lppyra02_w_m2",
        "ghi_lpnet14_w_m2", "temperatura_c", "vento_m_s", "precipitacao",
        "meteorologia_disponivel", "ghi_disponivel",
    ]
    df_15min = df_15min[[c for c in colunas_15min if c in df_15min.columns]]

    cursor = conn.cursor()
    cursor.execute("DELETE FROM leitura_15min WHERE DATE(timestamp_15min) = ?", (data_iso,))
    cursor.execute("DELETE FROM resumo_diario WHERE data = ?", (data_iso,))
    conn.commit()

    df_15min.to_sql("leitura_15min", conn, if_exists="append", index=False)
    df_resumo_pivot.to_sql("resumo_diario", conn, if_exists="append", index=False)


def salvar_historico_anual(conn, df_inversores, df_usina):
    """Histórico anual é sempre regenerado por completo (replace), porque
    vem inteiro de novo a cada vez que o relatório 'estatístico ALL' é
    reprocessado -- não faz sentido tentar mesclar incrementalmente."""
    df_inversores.to_sql("historico_anual_inversores", conn, if_exists="replace", index=False)
    df_usina.to_sql("historico_anual_usina", conn, if_exists="replace", index=False)


def datas_disponiveis(conn):
    """Lista (como texto YYYY-MM-DD) os dias que existem em leitura_15min."""
    df = pd.read_sql(
        "SELECT DISTINCT DATE(timestamp_15min) AS data FROM leitura_15min ORDER BY data",
        conn,
    )
    return df["data"].tolist()


def leitura_15min_do_dia(conn, data_iso):
    """data_iso no formato 'YYYY-MM-DD'. Devolve todas as colunas de 15min
    daquele dia, ordenadas por timestamp."""
    df = pd.read_sql(
        """
        SELECT *
        FROM leitura_15min
        WHERE DATE(timestamp_15min) = ?
        ORDER BY timestamp_15min
        """,
        conn,
        params=[data_iso],
        parse_dates=["timestamp_15min"],
    )
    return df


def resumo_diario(conn):
    df = pd.read_sql("SELECT * FROM resumo_diario ORDER BY data", conn)
    return df


def resumo_do_dia(conn, data_iso):
    df = pd.read_sql("SELECT * FROM resumo_diario WHERE data = ?", conn, params=[data_iso])
    return df.iloc[0] if not df.empty else None


def historico_anual_inversores(conn):
    return pd.read_sql("SELECT * FROM historico_anual_inversores", conn)


def historico_anual_usina(conn):
    return pd.read_sql("SELECT * FROM historico_anual_usina", conn)


def historico_anual_inversores_long(conn):
    """Formato 'longo' (inversor, ano, kwh) — mais fácil de plotar."""
    df = historico_anual_inversores(conn)
    if df.empty:
        return df
    df = df.drop(columns=["Valor total"], errors="ignore")
    df_long = df.melt(id_vars=["inversor"], var_name="ano", value_name="geracao_kwh")
    df_long = df_long[df_long["ano"].isin(ANOS)]
    df_long["ano"] = df_long["ano"].astype(int)
    return df_long.sort_values(["inversor", "ano"])


def cobertura_geral(conn):
    """Contagens gerais usadas na Visão geral / Qualidade dos dados."""
    total_15min = pd.read_sql("SELECT COUNT(*) AS n FROM leitura_15min", conn)["n"][0]
    com_meteo = pd.read_sql(
        "SELECT COUNT(*) AS n FROM leitura_15min WHERE meteorologia_disponivel = 1", conn
    )["n"][0]
    com_ghi = pd.read_sql(
        "SELECT COUNT(*) AS n FROM leitura_15min WHERE ghi_disponivel = 1", conn
    )["n"][0]
    com_4_inv = pd.read_sql(
        "SELECT COUNT(*) AS n FROM leitura_15min WHERE potencia_inversores_soma_kw IS NOT NULL", conn
    )["n"][0]
    duplicados = pd.read_sql(
        """
        SELECT COUNT(*) AS n FROM (
            SELECT timestamp_15min FROM leitura_15min
            GROUP BY timestamp_15min HAVING COUNT(*) > 1
        )
        """,
        conn,
    )["n"][0]

    return {
        "total_registros_15min": int(total_15min),
        "com_meteorologia": int(com_meteo),
        "pct_meteorologia": round(100 * com_meteo / total_15min, 1) if total_15min else 0.0,
        "com_ghi": int(com_ghi),
        "pct_ghi": round(100 * com_ghi / total_15min, 1) if total_15min else 0.0,
        "com_4_inversores": int(com_4_inv),
        "pct_4_inversores": round(100 * com_4_inv / total_15min, 1) if total_15min else 0.0,
        "timestamps_duplicados": int(duplicados),
    }
