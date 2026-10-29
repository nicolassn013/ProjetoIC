"""
consultas.py - Todas as queries usadas pelo dashboard, num lugar só.

Cada função recebe uma conexão já aberta (ver banco.conectar) e devolve um
DataFrame pronto pra uso. Nenhuma função aqui inventa dado: se a tabela
estiver vazia ou a data não existir, o retorno é um DataFrame vazio, e quem
decide o que mostrar na tela é o dashboard.py.
"""

import pandas as pd

import catalogo_meteorologia as catalogo
import migracoes

ANOS = [str(a) for a in range(2020, 2027)]


# ============================================================
# ESCRITA (antes vivia espalhada dentro de pipeline/carrega_banco.py;
# consolidado aqui pra existir um único lugar que conhece o schema
# inteiro do banco, tanto pra ler quanto pra gravar).
# ============================================================

def inicializar_schema(conn):
    """Atualiza a estrutura do banco aplicando as migrações pendentes
    (app/migracoes/*.sql). Idempotente: num banco já atualizado não faz nada.
    Devolve a lista de migrações aplicadas agora."""
    return migracoes.aplicar(conn)


def salvar_dia(conn, data_iso, df_15min, df_resumo_pivot):
    """Grava (de forma idempotente) um dia inteiro: apaga o que já existia
    daquela data em leitura_15min/resumo_diario e insere de novo.

    df_15min: já vem pronto (mesmas colunas da tabela leitura_15min).
    df_resumo_pivot: 1 linha, colunas = indicadores do resumo do Passo 4.

    Devolve {"linhas_antes", "linhas_depois"} para quem chamou poder avisar
    quando um dia completo for trocado por um dia com menos linhas.
    """
    colunas_15min = [
        "timestamp_15min", "potencia_fv_kw", "potencia_inversores_soma_kw",
        "INV01", "INV02", "INV03", "INV04", "ghi_lppyra02_w_m2",
        "ghi_lpnet14_w_m2", "temperatura_c", "vento_m_s", "precipitacao",
        "meteorologia_disponivel", "ghi_disponivel",
    ]
    df_15min = df_15min[[c for c in colunas_15min if c in df_15min.columns]]

    cursor = conn.cursor()
    linhas_antes = cursor.execute(
        "SELECT COUNT(*) FROM leitura_15min WHERE DATE(timestamp_15min) = ?", (data_iso,)
    ).fetchone()[0]
    cursor.execute("DELETE FROM leitura_15min WHERE DATE(timestamp_15min) = ?", (data_iso,))
    cursor.execute("DELETE FROM resumo_diario WHERE data = ?", (data_iso,))
    conn.commit()

    df_15min.to_sql("leitura_15min", conn, if_exists="append", index=False)
    df_resumo_pivot.to_sql("resumo_diario", conn, if_exists="append", index=False)
    return {"linhas_antes": int(linhas_antes), "linhas_depois": len(df_15min)}


def salvar_meteorologia(conn, df, modo="substituir_dia"):
    """Grava (de forma idempotente) a meteorologia de um ou mais dias em
    meteorologia_15min: apaga o que já existia dos dias presentes no DataFrame
    e insere de novo, tudo numa transação só (se algo falhar, nada muda).

    df: coluna 'timestamp_15min' obrigatória; as demais devem ser colunas do
    catálogo (app/catalogo_meteorologia.py). Coluna desconhecida ou timestamp
    repetido é erro, para não perder dado em silêncio. Coluna ausente fica
    NULL. Flags aceitam True/False/NaN e vão para o banco como 1/0/NULL.

    modo="substituir_dia" (padrão): apaga os dias inteiros presentes no DataFrame
    e insere de novo. Serve para carga em lote (dia completo).
    modo="mesclar": apaga só os horários presentes no DataFrame e insere de novo;
    os outros horários do mesmo dia são preservados. Serve para a aquisição
    incremental, em que chega 1 arquivo de 15 min por vez. Usar "substituir_dia"
    com 1 linha apagaria o resto do dia.

    Devolve {"modo", "linhas_gravadas", "linhas_substituidas", "dias": {data:
    {"linhas_antes", "linhas_depois"}}, "dias_com_menos_linhas": [datas]}. Em
    "mesclar" a lista de dias com menos linhas é sempre vazia.
    """
    if modo not in ("substituir_dia", "mesclar"):
        raise ValueError(f"modo inválido: {modo!r} (use 'substituir_dia' ou 'mesclar')")
    permitidas = catalogo.colunas_meteorologia_15min()
    if "timestamp_15min" not in df.columns:
        raise ValueError("DataFrame sem a coluna 'timestamp_15min'.")
    desconhecidas = [c for c in df.columns if c not in permitidas]
    if desconhecidas:
        raise ValueError(
            f"Colunas que não existem em meteorologia_15min: {desconhecidas}. "
            "Se forem variáveis novas, crie uma migração (app/migracoes/) e atualize o catálogo."
        )

    df = df.copy()
    df["timestamp_15min"] = pd.to_datetime(df["timestamp_15min"])
    repetidos = df.loc[df["timestamp_15min"].duplicated(keep=False), "timestamp_15min"]
    if not repetidos.empty:
        raise ValueError(
            f"{repetidos.nunique()} timestamp(s) repetido(s) em timestamp_15min, "
            f"por exemplo {repetidos.iloc[0]}. Resolva a duplicata antes de gravar."
        )
    if "timestamp_original" in df.columns:
        df["timestamp_original"] = pd.to_datetime(df["timestamp_original"])
    for coluna in ["lacuna_temporal"] + catalogo.colunas_flags():
        if coluna in df.columns:
            df[coluna] = df[coluna].map(lambda x: None if pd.isna(x) else int(bool(x))).astype(object)

    datas = sorted(df["timestamp_15min"].dt.strftime("%Y-%m-%d").unique())
    contagem = {}
    substituidas = 0
    try:
        if modo == "substituir_dia":
            for data_iso in datas:
                antes = conn.execute(
                    "SELECT COUNT(*) FROM meteorologia_15min WHERE DATE(timestamp_15min) = ?", (data_iso,)
                ).fetchone()[0]
                conn.execute("DELETE FROM meteorologia_15min WHERE DATE(timestamp_15min) = ?", (data_iso,))
                depois = int((df["timestamp_15min"].dt.strftime("%Y-%m-%d") == data_iso).sum())
                contagem[data_iso] = {"linhas_antes": int(antes), "linhas_depois": depois}
                substituidas += int(antes)
        else:
            horarios = df["timestamp_15min"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
            for horario in horarios:
                substituidas += conn.execute(
                    "DELETE FROM meteorologia_15min WHERE timestamp_15min = ?", (horario,)
                ).rowcount
        df.to_sql("meteorologia_15min", conn, if_exists="append", index=False)
    except Exception:
        conn.rollback()
        raise

    return {
        "modo": modo,
        "linhas_gravadas": len(df),
        "linhas_substituidas": substituidas,
        "dias": contagem,
        "dias_com_menos_linhas": [d for d, c in contagem.items() if c["linhas_depois"] < c["linhas_antes"]],
    }


def ingestao_ja_feita(conn, nome_arquivo, sha256):
    """True se este arquivo (mesmo nome e mesmo conteúdo) já foi processado com sucesso."""
    return conn.execute(
        "SELECT 1 FROM ingestao_arquivos WHERE nome_arquivo = ? AND sha256 = ? AND status = 'ok'",
        (nome_arquivo, sha256),
    ).fetchone() is not None


def registrar_ingestao(conn, origem, nome_arquivo, sha256, status, linhas_lidas=None,
                       linhas_gravadas=None, primeiro_registro=None, ultimo_registro=None,
                       mensagem=None):
    """Anota no diário (ingestao_arquivos) o resultado do processamento de um arquivo.
    Um mesmo arquivo com o mesmo status só fica uma vez (a linha anterior é substituída)."""
    conn.execute(
        """
        INSERT OR REPLACE INTO ingestao_arquivos
            (origem, nome_arquivo, sha256, processado_em, status, linhas_lidas, linhas_gravadas,
             primeiro_registro, ultimo_registro, mensagem)
        VALUES (?, ?, ?, datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?)
        """,
        (origem, nome_arquivo, sha256, status, linhas_lidas, linhas_gravadas,
         None if primeiro_registro is None else str(primeiro_registro),
         None if ultimo_registro is None else str(ultimo_registro), mensagem),
    )
    conn.commit()


def ultimas_ingestoes(conn, limite=20):
    """Últimos registros do diário de aquisição, do mais recente para o mais antigo."""
    return pd.read_sql(
        "SELECT * FROM ingestao_arquivos ORDER BY id DESC LIMIT ?", conn, params=[int(limite)]
    )


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
    """data_iso no formato 'YYYY-MM-DD'. Devolve as 14 colunas de sempre (usina
    + 5 variáveis meteorológicas), ordenadas por timestamp. Lê pela view, então
    a meteorologia mais nova (meteorologia_15min) vale sobre a cópia legada."""
    df = pd.read_sql(
        """
        SELECT timestamp_15min, potencia_fv_kw, potencia_inversores_soma_kw,
               INV01, INV02, INV03, INV04,
               ghi_lppyra02_w_m2, ghi_lpnet14_w_m2, temperatura_c, vento_m_s, precipitacao,
               meteorologia_disponivel, ghi_disponivel
        FROM vw_leitura_completa
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


def meteorologia_15min_do_dia(conn, data_iso):
    """Todas as variáveis de meteorologia_15min de um dia (YYYY-MM-DD)."""
    return pd.read_sql(
        "SELECT * FROM meteorologia_15min WHERE DATE(timestamp_15min) = ? ORDER BY timestamp_15min",
        conn,
        params=[data_iso],
        parse_dates=["timestamp_15min", "timestamp_original"],
    )


def leitura_completa_do_dia(conn, data_iso):
    """Usina + meteorologia completa de um dia, pela view vw_leitura_completa
    (as linhas da usina sempre aparecem; meteorologia ausente vem como NULL)."""
    return pd.read_sql(
        "SELECT * FROM vw_leitura_completa WHERE DATE(timestamp_15min) = ? ORDER BY timestamp_15min",
        conn,
        params=[data_iso],
        parse_dates=["timestamp_15min", "timestamp_original"],
    )


def cobertura_meteorologia(conn):
    """Quantas linhas têm valor em cada uma das 56 variáveis do catálogo.
    Os nomes de coluna e tabela vêm do catálogo (nunca de entrada externa)."""
    totais = {
        tabela: conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
        for tabela in (catalogo.TABELA_LEITURA, catalogo.TABELA_METEOROLOGIA)
    }
    linhas = []
    for v in catalogo.VARIAVEIS:
        preenchidos = conn.execute(f"SELECT COUNT({v.coluna}) FROM {v.tabela}").fetchone()[0]
        total = totais[v.tabela]
        linhas.append({
            "coluna": v.coluna, "tabela": v.tabela, "grupo": v.grupo, "tratada": v.tratada,
            "preenchidos": preenchidos, "total_linhas": total,
            "pct": round(100 * preenchidos / total, 1) if total else 0.0,
        })
    return pd.DataFrame(linhas)


def verificar_schema_meteorologia(conn):
    """Compara as colunas reais de meteorologia_15min com o catálogo.
    Devolve {"faltando_no_banco": [...], "sobrando_no_banco": [...]}; ambas
    vazias = banco e catálogo concordam."""
    reais = [r[1] for r in conn.execute("PRAGMA table_info(meteorologia_15min)")]
    esperadas = catalogo.colunas_meteorologia_15min()
    return {
        "faltando_no_banco": [c for c in esperadas if c not in reais],
        "sobrando_no_banco": [c for c in reais if c not in esperadas],
    }


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
        "SELECT COUNT(*) AS n FROM vw_leitura_completa WHERE meteorologia_disponivel = 1", conn
    )["n"][0]
    com_ghi = pd.read_sql(
        "SELECT COUNT(*) AS n FROM vw_leitura_completa WHERE ghi_disponivel = 1", conn
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
