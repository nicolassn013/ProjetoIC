import os
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment


# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Localização do próprio arquivo .py
PASTA_PROJETO = os.path.dirname(
    os.path.abspath(__file__)
)

PASTA_DADOS = os.path.join(
    PASTA_PROJETO,
    "dados"
)

# Arquivo que já passou pelo tratamento
ARQUIVO_ENTRADA = os.path.join(
    PASTA_DADOS,
    "dados_meteorologicos_tratados.xlsx"
)

# Arquivo que será gerado nesta fase
ARQUIVO_SAIDA = os.path.join(
    PASTA_DADOS,
    "analise_meteorologicos.xlsx"
)

# Frequência esperada da estação
INTERVALO_ESPERADO = pd.Timedelta(
    minutes=15
)


# ============================================================
# LIMPAR TERMINAL
# ============================================================

def limpar_terminal():

    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


# ============================================================
# CARREGAR DADOS TRATADOS
# ============================================================

def carregar_dados():

    print(
        "\n" + "=" * 70
    )
    print(
        "ANÁLISE DOS DADOS METEOROLÓGICOS"
    )
    print(
        "=" * 70
    )

    print(
        "\nCarregando arquivo tratado..."
    )

    if not os.path.exists(
        ARQUIVO_ENTRADA
    ):

        raise FileNotFoundError(
            "\nArquivo não encontrado:\n"
            + ARQUIVO_ENTRADA
        )

    df = pd.read_excel(
        ARQUIVO_ENTRADA,
        sheet_name="dados_tratados"
    )

    if "UTC -3" not in df.columns:

        raise ValueError(
            "A coluna 'UTC -3' não foi encontrada."
        )

    df["UTC -3"] = pd.to_datetime(
        df["UTC -3"],
        errors="coerce"
    )

    # Remove somente registros que não possuem
    # timestamp utilizável.
    df = df.dropna(
        subset=["UTC -3"]
    ).copy()

    # Garante ordem cronológica.
    df = df.sort_values(
        "UTC -3"
    ).reset_index(
        drop=True
    )

    print(
        "Arquivo carregado com sucesso."
    )

    print(
        f"Registros: {len(df)}"
    )

    print(
        f"Colunas: {len(df.columns)}"
    )

    print(
        f"Primeiro registro: "
        f"{df['UTC -3'].min()}"
    )

    print(
        f"Último registro: "
        f"{df['UTC -3'].max()}"
    )

    return df


# ============================================================
# IDENTIFICAR COLUNAS DE MEDIÇÃO
# ============================================================

def obter_colunas_medicao(df):

    colunas = []

    # Essas colunas não são variáveis meteorológicas.
    colunas_auxiliares = {
        "UTC",
        "UTC -3",
        "Local",
        "Freq",
        "intervalo_anterior",
        "intervalo_negativo",
        "lacuna_temporal"
    }

    for coluna in df.columns:

        nome = str(coluna)

        # Flags não são medições.
        if nome.startswith(
            "flag_"
        ):
            continue

        # Colunas auxiliares não são medições.
        if nome in colunas_auxiliares:
            continue

        # Caso a versão tratada possua uma coluna
        # específica "variavel_tratado", ela não será
        # considerada como uma nova variável.
        if nome.endswith(
            "_tratado"
        ):
            continue

        # Só queremos variáveis numéricas.
        if pd.api.types.is_numeric_dtype(
            df[coluna]
        ):

            colunas.append(
                coluna
            )

    return colunas


# ============================================================
# OBTER SÉRIE USADA NA ANÁLISE
# ============================================================

def obter_serie_analise(
    df,
    coluna
):

    coluna_tratada = (
        f"{coluna}_tratado"
    )

    # Se houver uma versão tratada específica,
    # ela será utilizada.
    if coluna_tratada in df.columns:

        serie = pd.to_numeric(
            df[
                coluna_tratada
            ],
            errors="coerce"
        )

        origem = "tratado"

    else:

        serie = pd.to_numeric(
            df[coluna],
            errors="coerce"
        )

        origem = "original"

    return serie, origem


# ============================================================
# ESTATÍSTICA DESCRITIVA
# ============================================================

def calcular_estatisticas(df):

    print(
        "\nCalculando estatísticas descritivas..."
    )

    colunas = obter_colunas_medicao(
        df
    )

    resultados = []

    for coluna in colunas:

        serie, origem = (
            obter_serie_analise(
                df,
                coluna
            )
        )

        total = len(
            serie
        )

        validos = int(
            serie.notna().sum()
        )

        ausentes = int(
            serie.isna().sum()
        )

        if validos > 0:

            minimo = float(
                serie.min()
            )

            maximo = float(
                serie.max()
            )

            media = float(
                serie.mean()
            )

            mediana = float(
                serie.median()
            )

            desvio_padrao = float(
                serie.std()
            )

            mascara_valida = (
                serie.notna()
            )

            primeiro_valido = (
                df.loc[
                    mascara_valida,
                    "UTC -3"
                ].min()
            )

            ultimo_valido = (
                df.loc[
                    mascara_valida,
                    "UTC -3"
                ].max()
            )

        else:

            minimo = None
            maximo = None
            media = None
            mediana = None
            desvio_padrao = None
            primeiro_valido = None
            ultimo_valido = None

        disponibilidade = (
            validos / total * 100
            if total > 0
            else 0
        )

        resultados.append(
            {
                "variavel": coluna,
                "origem_utilizada": origem,
                "registros_totais": total,
                "registros_validos": validos,
                "registros_ausentes": ausentes,
                "disponibilidade_%": disponibilidade,
                "media": media,
                "mediana": mediana,
                "desvio_padrao": desvio_padrao,
                "minimo": minimo,
                "maximo": maximo,
                "primeiro_valido": primeiro_valido,
                "ultimo_valido": ultimo_valido
            }
        )

    resultado = pd.DataFrame(
        resultados
    )

    resultado = resultado.sort_values(
        "variavel"
    ).reset_index(
        drop=True
    )

    print(
        f"Variáveis analisadas: "
        f"{len(resultado)}"
    )

    return resultado


# ============================================================
# CALCULAR REGISTROS ESPERADOS
# ============================================================

def calcular_registros_esperados(
    inicio,
    fim
):

    if (
        pd.isna(inicio)
        or pd.isna(fim)
        or fim < inicio
    ):

        return 0

    segundos = (
        fim - inicio
    ).total_seconds()

    intervalos = (
        segundos
        / INTERVALO_ESPERADO.total_seconds()
    )

    return int(
        round(intervalos)
    ) + 1


# ============================================================
# GERAR PERÍODOS ANUAIS
# ============================================================

def gerar_periodos_anuais(
    primeiro,
    ultimo
):

    primeiro_ano = (
        primeiro.year
    )

    ultimo_ano = (
        ultimo.year
    )

    periodos = []

    for ano in range(
        primeiro_ano,
        ultimo_ano + 1
    ):

        inicio_ano = pd.Timestamp(
            year=ano,
            month=1,
            day=1,
            hour=0,
            minute=0
        )

        fim_ano = pd.Timestamp(
            year=ano,
            month=12,
            day=31,
            hour=23,
            minute=45
        )

        inicio = max(
            inicio_ano,
            primeiro
        )

        fim = min(
            fim_ano,
            ultimo
        )

        periodos.append(
            (
                str(ano),
                inicio,
                fim
            )
        )

    return periodos


# ============================================================
# GERAR PERÍODOS MENSAIS
# ============================================================

def gerar_periodos_mensais(
    primeiro,
    ultimo
):

    primeiro_periodo = pd.Period(
        primeiro,
        freq="M"
    )

    ultimo_periodo = pd.Period(
        ultimo,
        freq="M"
    )

    periodos = []

    periodo_atual = primeiro_periodo

    while periodo_atual <= ultimo_periodo:

        inicio_mes = (
            periodo_atual
            .start_time
        )

        fim_mes = (
            periodo_atual
            .end_time
        )

        inicio = max(
            inicio_mes,
            primeiro
        )

        fim = min(
            fim_mes,
            ultimo
        )

        periodos.append(
            (
                str(periodo_atual),
                inicio,
                fim
            )
        )

        periodo_atual += 1

    return periodos


# ============================================================
# DISPONIBILIDADE ANUAL
# ============================================================

def calcular_disponibilidade_anual(
    df
):

    print(
        "\nCalculando disponibilidade anual..."
    )

    primeiro = df[
        "UTC -3"
    ].min()

    ultimo = df[
        "UTC -3"
    ].max()

    periodos = gerar_periodos_anuais(
        primeiro,
        ultimo
    )

    colunas = obter_colunas_medicao(
        df
    )

    resultados = []

    # Cria coluna auxiliar com o ano.
    anos = df[
        "UTC -3"
    ].dt.year

    for periodo, inicio, fim in periodos:

        mascara_periodo = (
            (df["UTC -3"] >= inicio)
            &
            (df["UTC -3"] <= fim)
        )

        esperado = (
            calcular_registros_esperados(
                inicio,
                fim
            )
        )

        for coluna in colunas:

            serie, origem = (
                obter_serie_analise(
                    df,
                    coluna
                )
            )

            serie_periodo = (
                serie.loc[
                    mascara_periodo
                ]
            )

            validos = int(
                serie_periodo.notna().sum()
            )

            ausentes = max(
                esperado - validos,
                0
            )

            disponibilidade = (
                validos
                / esperado
                * 100
                if esperado > 0
                else 0
            )

            resultados.append(
                {
                    "ano": periodo,
                    "variavel": coluna,
                    "registros_esperados":
                        esperado,
                    "registros_validos":
                        validos,
                    "registros_ausentes":
                        ausentes,
                    "disponibilidade_%":
                        disponibilidade
                }
            )

    return pd.DataFrame(
        resultados
    )


# ============================================================
# DISPONIBILIDADE MENSAL
# ============================================================

def calcular_disponibilidade_mensal(
    df
):

    print(
        "\nCalculando disponibilidade mensal..."
    )

    primeiro = df[
        "UTC -3"
    ].min()

    ultimo = df[
        "UTC -3"
    ].max()

    periodos = gerar_periodos_mensais(
        primeiro,
        ultimo
    )

    colunas = obter_colunas_medicao(
        df
    )

    resultados = []

    for periodo, inicio, fim in periodos:

        mascara_periodo = (
            (df["UTC -3"] >= inicio)
            &
            (df["UTC -3"] <= fim)
        )

        esperado = (
            calcular_registros_esperados(
                inicio,
                fim
            )
        )

        for coluna in colunas:

            serie, origem = (
                obter_serie_analise(
                    df,
                    coluna
                )
            )

            serie_periodo = (
                serie.loc[
                    mascara_periodo
                ]
            )

            validos = int(
                serie_periodo.notna().sum()
            )

            ausentes = max(
                esperado - validos,
                0
            )

            disponibilidade = (
                validos
                / esperado
                * 100
                if esperado > 0
                else 0
            )

            resultados.append(
                {
                    "mes": periodo,
                    "variavel": coluna,
                    "registros_esperados":
                        esperado,
                    "registros_validos":
                        validos,
                    "registros_ausentes":
                        ausentes,
                    "disponibilidade_%":
                        disponibilidade
                }
            )

    return pd.DataFrame(
        resultados
    )

# ============================================================
# VARIÁVEIS PRINCIPAIS PARA ANÁLISE
# ============================================================

def obter_variaveis_principais(df):

    variaveis = [
        "Temperatura inst",
        "Radiação solar global inst LPPYRA02",
        "Radiação solar global inst LPNET14",
        "Velocidade vento med",
        "Umidade Relativa inst",
        "Precipitação"
    ]

    encontradas = []

    for nome in variaveis:

        if nome in df.columns:
            encontradas.append(nome)

    return encontradas


# ============================================================
# MÉDIAS MENSAIS
# ============================================================

def calcular_medias_mensais(df):

    print(
        "\nCalculando médias mensais das variáveis principais..."
    )

    variaveis = obter_variaveis_principais(
        df
    )

    resultados = []

    # Cria o período mensal com base no timestamp.
    df = df.copy()

    df["mes"] = (
        df["UTC -3"]
        .dt.to_period("M")
    )

    for mes, grupo in df.groupby(
        "mes"
    ):

        for coluna in variaveis:

            serie, origem = (
                obter_serie_analise(
                    df.loc[
                        grupo.index
                    ],
                    coluna
                )
            )

            validos = (
                serie.dropna()
            )

            if len(validos) == 0:

                continue

            resultados.append(
                {
                    "mes": str(mes),
                    "variavel": coluna,
                    "origem_utilizada": origem,
                    "registros_validos": len(
                        validos
                    ),
                    "media": validos.mean(),
                    "mediana": validos.median(),
                    "desvio_padrao": validos.std(),
                    "minimo": validos.min(),
                    "maximo": validos.max()
                }
            )

    resultado = pd.DataFrame(
        resultados
    )

    if not resultado.empty:

        resultado = resultado.sort_values(
            [
                "mes",
                "variavel"
            ]
        ).reset_index(
            drop=True
        )

    print(
        f"Variáveis principais analisadas: "
        f"{len(variaveis)}"
    )

    print(
        f"Linhas de médias mensais geradas: "
        f"{len(resultado)}"
    )

    return resultado


# ============================================================
# RESUMO GERAL
# ============================================================

def gerar_resumo(
    df,
    estatisticas,
    disponibilidade_anual
):

    print(
        "\nGerando resumo..."
    )

    primeiro = df[
        "UTC -3"
    ].min()

    ultimo = df[
        "UTC -3"
    ].max()

    esperado_total = (
        calcular_registros_esperados(
            primeiro,
            ultimo
        )
    )

    registros = len(df)

    disponibilidade_temporal = (
        registros
        / esperado_total
        * 100
        if esperado_total > 0
        else 0
    )

    if (
        "lacuna_temporal"
        in df.columns
    ):

        quantidade_lacunas = int(
            df[
                "lacuna_temporal"
            ].sum()
        )

    else:

        quantidade_lacunas = None

    if (
        "intervalo_negativo"
        in df.columns
    ):

        intervalos_negativos = int(
            df[
                "intervalo_negativo"
            ].sum()
        )

    else:

        intervalos_negativos = None

    resumo = pd.DataFrame(
        {
            "indicador": [
                "Primeiro registro",
                "Último registro",
                "Registros na base",
                "Registros esperados no período",
                "Disponibilidade temporal geral (%)",
                "Variáveis numéricas analisadas",
                "Lacunas temporais",
                "Intervalos negativos"
            ],
            "valor": [
                primeiro,
                ultimo,
                registros,
                esperado_total,
                disponibilidade_temporal,
                len(estatisticas),
                quantidade_lacunas,
                intervalos_negativos
            ]
        }
    )

    return resumo


# ============================================================
# FORMATAR EXCEL
# ============================================================

def formatar_excel(
    caminho
):

    print(
        "\nFormatando arquivo Excel..."
    )

    wb = load_workbook(
        caminho
    )

    for ws in wb.worksheets:

        # Congelar primeira linha.
        ws.freeze_panes = "A2"

        # Filtro.
        if ws.max_row > 1:

            ws.auto_filter.ref = (
                ws.dimensions
            )

        # Cabeçalho.
        for cell in ws[1]:

            cell.font = Font(
                bold=True
            )

            cell.alignment = Alignment(
                horizontal="center",
                vertical="center"
            )

        # Ajuste automático das colunas.
        for coluna in ws.columns:

            letra = (
                coluna[0]
                .column_letter
            )

            maior = 0

            for cell in coluna:

                if cell.value is None:
                    continue

                tamanho = len(
                    str(cell.value)
                )

                if tamanho > maior:

                    maior = tamanho

            largura = min(
                max(
                    maior + 2,
                    10
                ),
                45
            )

            ws.column_dimensions[
                letra
            ].width = largura

        # Formatação de timestamps.
        for row in ws.iter_rows():

            for cell in row:

                if isinstance(
                    cell.value,
                    pd.Timestamp
                ):

                    cell.number_format = (
                        "yyyy-mm-dd hh:mm:ss"
                    )

    wb.save(
        caminho
    )


# ============================================================
# SALVAR RESULTADOS
# ============================================================

def salvar_resultados(
    estatisticas,
    disponibilidade_anual,
    disponibilidade_mensal,
    medias_mensais,
    resumo
):

    print(
        "\nSalvando resultados..."
    )

    with pd.ExcelWriter(
        ARQUIVO_SAIDA,
        engine="openpyxl"
    ) as writer:

        estatisticas.to_excel(
            writer,
            sheet_name="estatisticas",
            index=False
        )

        disponibilidade_anual.to_excel(
            writer,
            sheet_name="disponibilidade_anual",
            index=False
        )

        disponibilidade_mensal.to_excel(
            writer,
            sheet_name="disponibilidade_mensal",
            index=False
        )

        medias_mensais.to_excel(
            writer,
            sheet_name="medias_mensais",
            index=False
        )

        resumo.to_excel(
            writer,
            sheet_name="resumo",
            index=False
        )

    formatar_excel(
        ARQUIVO_SAIDA
    )

    print(
        "\nArquivo de análise salvo em:"
    )

    print(
        os.path.abspath(
            ARQUIVO_SAIDA
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    limpar_terminal()

    # --------------------------------------------------------
    # 1. CARREGAR BASE TRATADA
    # --------------------------------------------------------

    df = carregar_dados()

    # --------------------------------------------------------
    # 2. ESTATÍSTICA DESCRITIVA
    # --------------------------------------------------------

    estatisticas = (
        calcular_estatisticas(
            df
        )
    )

    # --------------------------------------------------------
    # 3. DISPONIBILIDADE ANUAL
    # --------------------------------------------------------

    disponibilidade_anual = (
        calcular_disponibilidade_anual(
            df
        )
    )

    # --------------------------------------------------------
    # 4. DISPONIBILIDADE MENSAL
    # --------------------------------------------------------

    disponibilidade_mensal = (
        calcular_disponibilidade_mensal(
            df
        )
    )

    # --------------------------------------------------------
    # 5. MÉDIAS MENSAIS
    # --------------------------------------------------------

    medias_mensais = (
        calcular_medias_mensais(
        df
        )
    )

    # --------------------------------------------------------
    # 5. RESUMO
    # --------------------------------------------------------

    resumo = gerar_resumo(
        df,
        estatisticas,
        disponibilidade_anual
    )

    # --------------------------------------------------------
    # 6. SALVAR
    # --------------------------------------------------------

    salvar_resultados(
        estatisticas,
        disponibilidade_anual,
        disponibilidade_mensal,
        medias_mensais,
        resumo
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

print(
    "1. estatisticas"
)

print(
    "2. disponibilidade_anual"
)

print(
    "3. disponibilidade_mensal"
)

print(
    "4. medias_mensais"
)

print(
    "5. resumo"
)


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    main()