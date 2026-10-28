"""
leitor.py - Transforma o texto de um arquivo .txt da estação MAWS55 numa tabela.

FORMATO REAL (confirmado com 2 arquivos do FTP, EMA_SER_01_15m_20220715_1900.txt
e ..._2330.txt): UMA linha por arquivo, separada por vírgula, SEM cabeçalho:

    EMA_SER_01,15m,2022-07-15,23:30:07, 22.5, 1016.4, ..., 0.0
    local, freq, data, hora (UTC), 52 ou 56 valores

Como não há cabeçalho, o significado de cada posição vem da ordem abaixo (a
mesma dos nomes do arquivo bruto do Estudante 1). O horário do arquivo é UTC
(conferido contra a coluna 'UTC' do arquivo tratado dele); o horário local
('UTC -3') é UTC menos 3 horas.

DOIS LAYOUTS (pela quantidade de valores, nunca por suposição):
  - 56 valores: layout completo (inclui o grupo 'Temperatura ... LPNET14 (NTC)').
  - 52 valores: layout antigo, sem o grupo NTC (arquivos de 15/07/2022 a
    22/08/2022). Os valores do grupo NTC ficam vazios (NULL).
Qualquer outra quantidade é erro (arquivo cortado ou formato novo): o arquivo
vai para o diário como erro e nada é gravado.
"""

import pandas as pd

ESTATISTICAS = ("inst", "med", "max", "min")
ESTATISTICAS_3 = ("med", "max", "min")
QUANTIDADE_CABECALHO = 4          # local, freq, data, hora


def _grupo(modelo, estatisticas=ESTATISTICAS):
    return [modelo.format(e=e) for e in estatisticas]


# Ordem dos 56 valores no arquivo (o grupo NTC fica entre a radiação líquida e o vento)
GRUPO_NTC = _grupo("Temperatura {e} LPNET14 (NTC)")
ORDEM_56 = (
    ["Temp int"]
    + _grupo("Pressao {e}")
    + _grupo("Temperatura {e}")
    + _grupo("Umidade Relativa {e}")
    + _grupo("Radiação solar global {e} LPPYRA02")
    + _grupo("Radiação solar global {e} LPNET14")
    + _grupo("Radiação solar refletida {e}")
    + _grupo("Radiação IV {e}")
    + _grupo("Radiação spf {e}")
    + _grupo("Radiação solar líquida {e}")
    + GRUPO_NTC
    + _grupo("Direção vento {e}", ESTATISTICAS_3)
    + _grupo("Velocidade vento {e}", ESTATISTICAS_3)
    + _grupo("Temp solo {e}")
    + _grupo("Umid solo {e}")
    + ["Precipitação"]
)
ORDEM_52 = [n for n in ORDEM_56 if n not in GRUPO_NTC]
LAYOUTS = {len(ORDEM_56): ORDEM_56, len(ORDEM_52): ORDEM_52}


class FormatoInvalido(Exception):
    """O conteúdo do arquivo não tem a forma esperada."""


def _decodificar(conteudo):
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            return conteudo.decode(codificacao)
        except UnicodeDecodeError:
            continue
    raise FormatoInvalido("Não consegui decodificar o arquivo como texto.")


def _numero(texto):
    """Texto -> float; vazio ou texto não numérico -> (None, era_lixo)."""
    texto = texto.strip()
    if texto == "":
        return None, False
    try:
        return float(texto), False
    except ValueError:
        return None, True


def ler_maws55(conteudo):
    """Devolve DataFrame com 'UTC', 'UTC -3' (datetime) e as colunas de medição com
    os nomes canônicos (float, vazio = NaN; grupo NTC ausente no layout de 52).
    Metadados em df.attrs: valores_nao_numericos, linhas_invalidas, linhas_layout_52."""
    linhas = [l for l in _decodificar(conteudo).splitlines() if l.strip()]
    if not linhas:
        raise FormatoInvalido("Arquivo vazio.")

    registros, invalidas, nao_numericos, layout_52, motivos = [], 0, 0, 0, []
    for linha in linhas:
        campos = linha.split(",")
        valores = campos[QUANTIDADE_CABECALHO:]
        ordem = LAYOUTS.get(len(valores))
        horario = pd.to_datetime(f"{campos[2].strip()} {campos[3].strip()}", errors="coerce") \
            if len(campos) >= QUANTIDADE_CABECALHO else pd.NaT
        if ordem is None or pd.isna(horario):
            invalidas += 1
            if len(motivos) < 3:
                motivos.append(f"{len(valores)} valores, horário {'ok' if not pd.isna(horario) else 'inválido'}"
                               if len(campos) >= QUANTIDADE_CABECALHO else f"só {len(campos)} campos")
            continue
        registro = {"Local": campos[0].strip(), "Freq": campos[1].strip(), "UTC": horario}
        for nome, texto in zip(ordem, valores):
            numero, lixo = _numero(texto)
            nao_numericos += lixo
            registro[nome] = numero
        layout_52 += len(valores) == len(ORDEM_52)
        registros.append(registro)

    if not registros:
        raise FormatoInvalido(
            f"Nenhuma linha no formato esperado ({len(ORDEM_56)} ou {len(ORDEM_52)} valores depois de "
            f"local, freq, data e hora). Problemas: {motivos}. Início: {linhas[0][:80]!r}")

    df = pd.DataFrame(registros, columns=["Local", "Freq", "UTC"] + ORDEM_56)
    df["UTC -3"] = df["UTC"] - pd.Timedelta(hours=3)      # fuso fixo UTC-3 (sem horário de verão desde 2019)
    df[ORDEM_56] = df[ORDEM_56].astype("float64")
    df.attrs.update(valores_nao_numericos=nao_numericos, linhas_invalidas=invalidas,
                    linhas_layout_52=layout_52)
    return df
