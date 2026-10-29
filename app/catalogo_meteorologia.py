"""
catalogo_meteorologia.py - Lista única das variáveis da estação MAWS55.

Este arquivo é a fonte de verdade de "quais variáveis meteorológicas existem,
como se chamam no arquivo tratado, como se chamam no banco, qual a unidade e
se já foram tratadas". O pipeline, o dicionário e os testes leem daqui.

Atenção: o DDL do banco NÃO é gerado em tempo de execução a partir deste
catálogo. A estrutura mora nos scripts versionados de app/migracoes/. Se o
catálogo mudar, é preciso criar uma migração nova, e o teste
test_catalogo_bate_com_schema avisa quando os dois divergem.

Unidades: o sufixo no nome (_w_m2, _hpa, _c, _pct, _graus, _m_s) só aparece
quando a unidade é certa pela própria grandeza. Todas as unidades abaixo são
INFERIDAS pelo nome e pela faixa de valores; nenhuma foi confirmada ainda pelo
Estudante 1 (campo UNIDADE_CONFIRMADA).
"""

from collections import namedtuple

TABELA_METEOROLOGIA = "meteorologia_15min"
TABELA_LEITURA = "leitura_15min"
UNIDADE_CONFIRMADA = False

# coluna_arquivo: nome no xlsx tratado (versão _tratado quando existe)
# flag_arquivo:   nome da coluna de flag no xlsx (None = ainda sem tratamento)
# tabela:         onde o VALOR vive. Desde a migração 003 todas as 56 vivem em
#                 meteorologia_15min; as 5 legadas ainda têm cópia em leitura_15min
Variavel = namedtuple(
    "Variavel",
    "coluna coluna_arquivo flag_arquivo grupo unidade descricao tratada tabela",
)


def _quatro(prefixo_banco, sufixo_banco, prefixo_arquivo, prefixo_flag, grupo,
            unidade, descricao, tratada, estatisticas=("inst", "med", "max", "min")):
    nomes = {"inst": "instantâneo", "med": "média", "max": "máximo", "min": "mínimo"}
    saida = []
    for est in estatisticas:
        coluna_arquivo = f"{prefixo_arquivo.format(est=est)}" + ("_tratado" if tratada else "")
        saida.append(Variavel(
            coluna=f"{prefixo_banco.format(est=est)}{sufixo_banco}",
            coluna_arquivo=coluna_arquivo,
            flag_arquivo=prefixo_flag.format(est=est) if (tratada and prefixo_flag) else None,
            grupo=grupo,
            unidade=unidade,
            descricao=f"{descricao} ({nomes[est]})",
            tratada=tratada,
            tabela=TABELA_METEOROLOGIA,
        ))
    return saida


VARIAVEIS = []

# ---- As 5 que já estavam em leitura_15min (a cópia de lá fica como legado)
VARIAVEIS += [
    Variavel("ghi_lppyra02_w_m2", "Radiação solar global inst LPPYRA02_tratado",
             "flag_radiacao_solar_global_inst_lppyra02", "Radiação global", "W/m²",
             "Radiação global, sensor LPPYRA02 (instantâneo)", True, TABELA_METEOROLOGIA),
    Variavel("ghi_lpnet14_w_m2", "Radiação solar global inst LPNET14_tratado",
             "flag_radiacao_solar_global_inst_lpnet14", "Radiação global", "W/m²",
             "Radiação global, sensor LPNET14 (instantâneo)", True, TABELA_METEOROLOGIA),
    Variavel("temperatura_c", "Temperatura inst_tratado", "flag_temperatura_inst",
             "Temperatura do ar", "°C", "Temperatura do ar (instantâneo)", True, TABELA_METEOROLOGIA),
    Variavel("vento_m_s", "Velocidade vento med_tratado", "flag_velocidade_vento_med",
             "Velocidade do vento", "m/s", "Velocidade do vento (média)", True, TABELA_METEOROLOGIA),
    Variavel("precipitacao", "Precipitação_tratado", "flag_precipitacao",
             "Precipitação", "mm", "Precipitação no intervalo", True, TABELA_METEOROLOGIA),
]

# ---- Já tratadas pelo Estudante 1 (têm _tratado e flag): 19 campos
VARIAVEIS += _quatro("umidade_relativa_{est}", "_pct", "Umidade Relativa {est}",
                     "flag_umidade_relativa_{est}", "Umidade relativa do ar", "%",
                     "Umidade relativa do ar", True)
VARIAVEIS += _quatro("vento_dir_{est}", "_graus", "Direção vento {est}",
                     "flag_direcao_vento_{est}", "Direção do vento", "graus",
                     "Direção do vento", True, ("med", "max", "min"))
VARIAVEIS += _quatro("vento_vel_{est}", "_m_s", "Velocidade vento {est}",
                     "flag_velocidade_vento_{est}", "Velocidade do vento", "m/s",
                     "Velocidade do vento", True, ("max", "min"))
for _sensor, _nome in (("lppyra02", "LPPYRA02"), ("lpnet14", "LPNET14")):
    VARIAVEIS += _quatro(f"ghi_{_sensor}_{{est}}", "_w_m2",
                         f"Radiação solar global {{est}} {_nome}",
                         f"flag_radiacao_solar_global_{{est}}_{_sensor}",
                         "Radiação global", "W/m²",
                         f"Radiação global, sensor {_nome}", True, ("med", "max", "min"))
VARIAVEIS += _quatro("umid_solo_{est}", "", "Umid solo {est}", "flag_umid_solo_{est}",
                     "Umidade do solo", "a confirmar", "Umidade do solo", True)

# ---- Só dado bruto (sem _tratado, sem flag): 32 campos
VARIAVEIS += _quatro("pressao_{est}", "_hpa", "Pressao {est}", None, "Pressão atmosférica",
                     "hPa", "Pressão atmosférica", False)
VARIAVEIS += [Variavel("temp_int_c", "Temp int", None, "Temperatura adicional", "°C",
                       "Temp int (definição a confirmar)", False, TABELA_METEOROLOGIA)]
VARIAVEIS += _quatro("temperatura_{est}", "_c", "Temperatura {est}", None,
                     "Temperatura adicional", "°C", "Temperatura do ar", False,
                     ("med", "max", "min"))
VARIAVEIS += _quatro("rad_refletida_{est}", "_w_m2", "Radiação solar refletida {est}", None,
                     "Radiação refletida", "W/m²", "Radiação solar refletida", False)
VARIAVEIS += _quatro("rad_iv_{est}", "_w_m2", "Radiação IV {est}", None,
                     "Radiação infravermelha", "W/m²", "Radiação infravermelha (IV)", False)
VARIAVEIS += _quatro("rad_spf_{est}", "_w_m2", "Radiação spf {est}", None,
                     "Radiação SPF", "W/m²", "Radiação SPF (significado a confirmar)", False)
VARIAVEIS += _quatro("rad_liquida_{est}", "_w_m2", "Radiação solar líquida {est}", None,
                     "Radiação líquida", "W/m²", "Radiação solar líquida", False)
VARIAVEIS += _quatro("temp_ntc_lpnet14_{est}", "_c", "Temperatura {est} LPNET14 (NTC)", None,
                     "Temperatura do sensor LPNET14 (NTC)", "°C",
                     "Temperatura do sensor LPNET14 (NTC)", False)
VARIAVEIS += _quatro("temp_solo_{est}", "", "Temp solo {est}", None, "Temperatura do solo",
                     "a confirmar", "Temperatura do solo", False)

# Colunas de apoio da tabela meteorologia_15min (não são medições)
COLUNAS_APOIO = ["timestamp_15min", "timestamp_original", "lacuna_temporal"]

# Colunas das 5 variáveis antigas que ainda existem em leitura_15min (legado).
COLUNAS_LEGADAS_EM_LEITURA = [
    "ghi_lppyra02_w_m2", "ghi_lpnet14_w_m2", "temperatura_c", "vento_m_s", "precipitacao",
]


def nome_flag(variavel):
    return f"flag_{variavel.coluna}"


def variaveis_da_tabela_meteorologia():
    return [v for v in VARIAVEIS if v.tabela == TABELA_METEOROLOGIA]


def colunas_valores():
    return [v.coluna for v in variaveis_da_tabela_meteorologia()]


def colunas_flags():
    """Flags guardadas em meteorologia_15min: as das variáveis tratadas
    (19 novas + as 5 que já existiam)."""
    return [nome_flag(v) for v in VARIAVEIS if v.flag_arquivo]


def colunas_meteorologia_15min():
    """Todas as colunas de meteorologia_15min na ordem do catálogo (a ordem física
    no banco pode diferir, porque migrações novas acrescentam colunas no fim)."""
    return COLUNAS_APOIO + colunas_valores() + colunas_flags()


def mapa_valores_arquivo():
    """{coluna do banco: coluna do xlsx tratado} das 56 variáveis."""
    return {v.coluna: v.coluna_arquivo for v in variaveis_da_tabela_meteorologia()}


def mapa_flags_arquivo():
    """{coluna de flag do banco: coluna de flag do xlsx tratado}."""
    return {nome_flag(v): v.flag_arquivo for v in VARIAVEIS if v.flag_arquivo}


def gerar_dicionario_markdown():
    """Texto do dicionário das 56 variáveis, gerado do próprio catálogo."""
    linhas = [
        "| Coluna no banco | Onde fica | Unidade (inferida) | Descrição | Tratada pelo Estudante 1 | Flag |",
        "|---|---|---|---|---|---|",
    ]
    for v in VARIAVEIS:
        flag = f"`{nome_flag(v)}`" if v.flag_arquivo else "—"
        tratada = "sim" if v.tratada else "não (dado bruto)"
        linhas.append(
            f"| `{v.coluna}` | `{v.tabela}` | {v.unidade} | {v.descricao} | {tratada} | {flag} |"
        )
    return "\n".join(linhas)


if __name__ == "__main__":
    print(gerar_dicionario_markdown())
