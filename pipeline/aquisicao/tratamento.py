"""
tratamento.py - Regras de qualidade do Estudante 1, aplicadas a dados novos.

As regras são as do script dele (tratamento_de_dados_meteorologicos.py,
criar_flags_fisicas), uma por grupo de variável. Valor que viola a regra vira
vazio no valor tratado e a flag fica True; o valor bruto não é gravado no
banco. Variáveis sem regra (as 32 brutas) seguem como vieram, sem flag.
O teste test_tratamento valida estas regras contra o arquivo tratado dele.
"""

import numpy as np
import pandas as pd

import catalogo_meteorologia as catalogo

# grupo do catálogo -> (descrição, função que recebe a série e devolve a máscara "inválido")
REGRAS = {
    "Temperatura do ar": ("igual a -40 (código inválido)", lambda s: s == -40),
    "Umidade relativa do ar": ("fora de 0 a 100 %", lambda s: (s < 0) | (s > 100)),
    "Direção do vento": ("fora de 0 a 360 graus", lambda s: (s < 0) | (s > 360)),
    "Velocidade do vento": ("negativa", lambda s: s < 0),
    "Precipitação": ("negativa", lambda s: s < 0),
    "Radiação global": ("negativa", lambda s: s < 0),
    "Umidade do solo": ("igual a -400 (código de erro)", lambda s: s == -400),
}


def _nome_bruto(variavel):
    nome = variavel.coluna_arquivo
    return nome[: -len("_tratado")] if nome.endswith("_tratado") else nome


def tratar(df_bruto):
    """Recebe o DataFrame de leitor.ler_maws55 e devolve as colunas de meteorologia_15min
    (timestamp_15min, timestamp_original, lacuna_temporal, 56 valores, 24 flags).
    df.attrs['duplicados_descartados']: horários repetidos dentro do mesmo balde de 15 min
    (fica o registro mais recente)."""
    df_bruto = df_bruto.reset_index(drop=True)      # índices alinhados nas colunas montadas abaixo
    horario = pd.to_datetime(df_bruto["UTC -3"])
    saida = pd.DataFrame({
        "timestamp_15min": horario.dt.floor("15min"),
        "timestamp_original": horario,
        "lacuna_temporal": pd.Series([None] * len(df_bruto), dtype=object),
    })

    colunas = {}
    for v in catalogo.VARIAVEIS:
        bruto = _nome_bruto(v)
        if bruto in df_bruto.columns:
            serie = pd.to_numeric(df_bruto[bruto], errors="coerce").astype("float64")
            presente = True
        else:
            serie = pd.Series(np.nan, index=df_bruto.index, dtype="float64")
            presente = False
        if v.flag_arquivo:
            invalido = (REGRAS[v.grupo][1](serie).fillna(False).astype(bool)) if presente else None
            if presente:
                serie = serie.mask(invalido)
                colunas[catalogo.nome_flag(v)] = invalido
            else:
                colunas[catalogo.nome_flag(v)] = pd.Series([None] * len(serie), dtype=object)
        colunas[v.coluna] = serie
    saida = pd.concat([saida, pd.DataFrame(colunas)], axis=1)
    saida = saida[catalogo.colunas_meteorologia_15min()]

    antes = len(saida)
    saida = (saida.sort_values("timestamp_original")
                  .drop_duplicates("timestamp_15min", keep="last")
                  .reset_index(drop=True))
    saida.attrs["duplicados_descartados"] = antes - len(saida)
    return saida
