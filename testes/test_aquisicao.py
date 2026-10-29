"""
Testes da aquisição (FTP/pasta -> leitura -> tratamento -> banco -> diário).

Rodar a partir da raiz do projeto:
    python -m unittest discover -s testes -v

FORMATO: o .txt real (sem cabeçalho, vírgulas) foi confirmado com 2 arquivos do
FTP, usados aqui como constantes (REAL_2330 e REAL_1900). Os demais arquivos dos
testes são SINTÉTICOS, montados nesse mesmo formato. Só o layout de 52 valores
(2022) foi visto em arquivo real; o de 56 valores segue a ordem do arquivo do
Estudante 1 (conferida por teste, quando o xlsx dele está na máquina).
O teste que compara com o arquivo tratado do Estudante 1 só roda se esse
arquivo existir (variável METEO_TRATADO ou dados/estudante1_meteorologia/brutos/).
"""

import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PASTA_PROJETO, "app"))
sys.path.insert(0, os.path.join(PASTA_PROJETO, "pipeline"))

import banco                                            # noqa: E402
import catalogo_meteorologia as catalogo                # noqa: E402
import consultas                                        # noqa: E402
import aquisicao_maws55                                 # noqa: E402
from aquisicao import ingestao, leitor, tratamento      # noqa: E402
from aquisicao.config import ConfigError, ConfigFTP, carregar_config_ftp, ler_arquivo_env  # noqa: E402
from aquisicao.fontes import FonteFTP, FontePastaLocal, criar_fonte, filtrar_e_ordenar     # noqa: E402

ARQUIVO_TRATADO = os.environ.get("METEO_TRATADO") or os.path.join(
    PASTA_PROJETO, "dados", "estudante1_meteorologia", "brutos", "dados_meteorologicos_tratados.xlsx")


def nomes_brutos():
    return sorted({v.coluna_arquivo[:-len("_tratado")] if v.coluna_arquivo.endswith("_tratado")
                   else v.coluna_arquivo for v in catalogo.VARIAVEIS})


def linha_bruta(horario, valor=1.0, **especificos):
    """Um registro bruto: todas as medições com 'valor', exceto as de 'especificos'.
    'horario' é o horário LOCAL (UTC-3); o arquivo guarda UTC."""
    registro = {"Local": "EMA_SER_01", "Freq": "15m", "UTC": str(pd.Timestamp(horario) + pd.Timedelta(hours=3)),
                "UTC -3": str(pd.Timestamp(horario))}
    registro.update({n: valor for n in nomes_brutos()})
    registro.update(especificos)
    return registro


def texto(registros, layout=56, utc_texto=None):
    """Monta o conteúdo de um .txt no formato REAL da estação: uma linha por registro,
    separada por vírgula, sem cabeçalho (local, freq, data, hora UTC, valores)."""
    ordem = leitor.ORDEM_56 if layout == 56 else leitor.ORDEM_52
    linhas = []
    for r in registros:
        utc = pd.Timestamp(r["UTC"])
        data, hora = (utc_texto.split(" ") if utc_texto else (f"{utc:%Y-%m-%d}", f"{utc:%H:%M:%S}"))
        valores = ["" if pd.isna(r[n]) else str(r[n]) for n in ordem]
        linhas.append(",".join([r["Local"], r["Freq"], data, hora] + [f"{v:>6}" for v in valores]))
    return ("\n".join(linhas) + "\n").encode("utf-8")


def nome_arquivo(horario):
    return f"EMA_SER_01_15m_{pd.Timestamp(horario) + pd.Timedelta(hours=3):%Y%m%d_%H%M}.txt"


# As duas linhas REAIS recebidas do FTP (15/07/2022): layout antigo de 52 valores
REAL_2330 = (b"EMA_SER_01,15m,2022-07-15,23:30:07, 22.5, 1016.4, 1016.3, 1016.4, 1016.3, 32.5, 32.7, 32.8, 32.5,  57,  57,  57,  57,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,    0,   -3,   -3,   -2,   -3, 322,   8, 275,  1.3,  2.8,  0.5, 24.6, 24.6, 24.6, 24.6, 0.473, 0.473, 0.474, 0.473, 0.0\n")
REAL_1900 = (b"EMA_SER_01,15m,2022-07-15,19:00:07, 25.3, 1014.3, 1014.3, 1014.3, 1014.2, 27.0, 27.0, 34.7, 25.6,  59,  59,  60,  59,  147,  137,  171,   87,  120,  128,  160,   83,    3,    2,    3,    1,    0,    0,    0,    0,    3,    2,    3,    1,   87,   98,  123,   64,  37,  69, 358,  5.2,  8.1,  1.6, 24.9, 24.8, 24.9, 24.8, 0.475, 0.475, 0.475, 0.475, 0.0\n")


class TestLeitor(unittest.TestCase):
    def test_ordem_dos_layouts(self):
        self.assertEqual((len(leitor.ORDEM_56), len(leitor.ORDEM_52)), (56, 52))
        self.assertEqual(sorted(leitor.ORDEM_56), nomes_brutos(), "a ordem tem de cobrir exatamente as variáveis do catálogo")
        self.assertEqual(len(set(leitor.ORDEM_56)), 56)

    @unittest.skipUnless(os.path.exists(ARQUIVO_TRATADO), "arquivo tratado do Estudante 1 não está nesta máquina")
    def test_ordem_bate_com_a_ordem_do_arquivo_do_estudante1(self):
        cabecalho = list(pd.read_excel(ARQUIVO_TRATADO, sheet_name="dados_tratados", nrows=1).columns)
        self.assertEqual(cabecalho[4:60], leitor.ORDEM_56)

    def test_arquivo_real_2330(self):
        df = leitor.ler_maws55(REAL_2330)
        self.assertEqual(len(df), 1)
        r = df.iloc[0]
        self.assertEqual(r["UTC"], pd.Timestamp("2022-07-15 23:30:07"))
        self.assertEqual(r["UTC -3"], pd.Timestamp("2022-07-15 20:30:07"))
        self.assertEqual((r["Temp int"], r["Pressao inst"], r["Temperatura inst"], r["Umidade Relativa inst"]),
                         (22.5, 1016.4, 32.5, 57))
        self.assertEqual((r["Radiação solar líquida inst"], r["Radiação solar líquida min"]), (-3, -3))
        # layout antigo: depois da radiação líquida vêm direção e velocidade do vento
        self.assertEqual((r["Direção vento med"], r["Direção vento max"], r["Direção vento min"]), (322, 8, 275))
        self.assertEqual((r["Velocidade vento med"], r["Velocidade vento max"], r["Velocidade vento min"]), (1.3, 2.8, 0.5))
        self.assertEqual((r["Temp solo inst"], r["Umid solo inst"], r["Umid solo max"], r["Precipitação"]),
                         (24.6, 0.473, 0.474, 0.0))
        self.assertTrue(r[leitor.GRUPO_NTC].isna().all(), "no layout de 52 o grupo NTC não existe")
        self.assertEqual(df.attrs["linhas_layout_52"], 1)

    def test_arquivo_real_1900(self):
        r = leitor.ler_maws55(REAL_1900).iloc[0]
        self.assertEqual(r["UTC -3"], pd.Timestamp("2022-07-15 16:00:07"))
        self.assertEqual((r["Radiação solar global inst LPPYRA02"], r["Radiação solar global max LPNET14"]), (147, 160))
        self.assertEqual((r["Direção vento med"], r["Direção vento min"], r["Velocidade vento max"], r["Umid solo inst"]), (37, 358, 8.1, 0.475))

    def test_layout_de_56_valores_inclui_o_grupo_ntc(self):
        r = leitor.ler_maws55(texto([linha_bruta("2025-09-22 10:00:07", 5.5, **{"Temperatura inst LPNET14 (NTC)": 23.4})])).iloc[0]
        self.assertEqual((r["Temperatura inst LPNET14 (NTC)"], r["Pressao inst"]), (23.4, 5.5))

    def test_varias_linhas_no_mesmo_arquivo(self):
        df = leitor.ler_maws55(texto([linha_bruta("2025-09-22 10:00:07", 5.5), linha_bruta("2025-09-22 10:15:08", 6.5)]))
        self.assertEqual(list(df["Pressao inst"]), [5.5, 6.5])
        self.assertEqual(df["UTC -3"].iloc[1], pd.Timestamp("2025-09-22 10:15:08"))

    def test_valor_vazio_e_nao_numerico(self):
        df = leitor.ler_maws55(texto([linha_bruta("2025-09-22 10:00:07", **{"Pressao inst": "erro", "Precipitação": np.nan})]))
        self.assertTrue(pd.isna(df["Pressao inst"].iloc[0]) and pd.isna(df["Precipitação"].iloc[0]))
        self.assertEqual(df.attrs["valores_nao_numericos"], 1, "vazio não conta como lixo, texto conta")

    def test_quantidade_de_valores_inesperada_da_erro_claro(self):
        cortado = REAL_2330.rsplit(b",", 3)[0] + b"\n"                  # arquivo cortado no meio da transferência
        for conteudo in (b"", b"isto nao e dado da estacao\n", cortado, b"EMA_SER_01,15m,2022-07-15\n",
                         REAL_2330.rstrip() + b", 1.0\n"):
            with self.assertRaises(leitor.FormatoInvalido):
                leitor.ler_maws55(conteudo)

    def test_horario_invalido_descarta_a_linha_e_conta(self):
        bom = texto([linha_bruta("2025-09-22 10:00:07")])
        ruim = texto([linha_bruta("2025-09-22 10:15:07")], utc_texto="lixo lixo")
        df = leitor.ler_maws55(bom + ruim)
        self.assertEqual((len(df), df.attrs["linhas_invalidas"]), (1, 1))
        with self.assertRaises(leitor.FormatoInvalido):
            leitor.ler_maws55(ruim)

    def test_latin1_e_final_de_linha_windows(self):
        self.assertEqual(len(leitor.ler_maws55(REAL_2330.replace(b"\n", b"\r\n"))), 1)


class TestTratamento(unittest.TestCase):
    def tratar(self, **valores):
        return tratamento.tratar(leitor.ler_maws55(texto([linha_bruta("2025-09-22 10:00:07", **valores)])))

    def test_colunas_sao_as_do_catalogo(self):
        t = self.tratar()
        self.assertEqual(list(t.columns), catalogo.colunas_meteorologia_15min())

    def test_balde_de_15_min_e_horario_original(self):
        t = self.tratar()
        self.assertEqual(t["timestamp_15min"].iloc[0], pd.Timestamp("2025-09-22 10:00:00"))
        self.assertEqual(t["timestamp_original"].iloc[0], pd.Timestamp("2025-09-22 10:00:07"))

    def test_regras_um_caso_por_grupo(self):
        casos = [  # (coluna bruta, valor invalido, coluna do banco, valor valido)
            ("Temperatura inst", -40, "temperatura_c", 25),
            ("Umidade Relativa inst", 101, "umidade_relativa_inst_pct", 99),
            ("Umidade Relativa min", -1, "umidade_relativa_min_pct", 0),
            ("Direção vento med", 361, "vento_dir_med_graus", 360),
            ("Velocidade vento max", -0.1, "vento_vel_max_m_s", 0),
            ("Precipitação", -1, "precipitacao", 0),
            ("Radiação solar global inst LPPYRA02", -5, "ghi_lppyra02_w_m2", 0),
            ("Umid solo inst", -400, "umid_solo_inst", -0.4),
        ]
        for bruta, invalido, coluna, valido in casos:
            t = self.tratar(**{bruta: invalido})
            self.assertTrue(pd.isna(t[coluna].iloc[0]), f"{bruta}={invalido} deveria virar vazio")
            self.assertTrue(bool(t[f"flag_{coluna}"].iloc[0]), f"{bruta}={invalido} deveria ter flag")
            t = self.tratar(**{bruta: valido})
            self.assertEqual(t[coluna].iloc[0], valido, f"{bruta}={valido} deveria ser mantido")
            self.assertFalse(bool(t[f"flag_{coluna}"].iloc[0]))

    def test_zero_verdadeiro_continua_zero(self):
        t = self.tratar(**{"Umidade Relativa inst": 0, "Precipitação": 0})
        self.assertEqual(t["umidade_relativa_inst_pct"].iloc[0], 0)
        self.assertEqual(t["precipitacao"].iloc[0], 0)

    def test_variavel_sem_regra_segue_bruta_e_sem_flag(self):
        t = self.tratar(**{"Temperatura med": -40, "Pressao inst": 5000})
        self.assertEqual(t["temperatura_med_c"].iloc[0], -40, "sem tratamento prévio: valor bruto preservado")
        self.assertEqual(t["pressao_inst_hpa"].iloc[0], 5000)
        self.assertNotIn("flag_temperatura_med_c", t.columns)

    def test_vazio_bruto_fica_vazio_com_flag_falsa(self):
        t = self.tratar(**{"Precipitação": np.nan})
        self.assertTrue(pd.isna(t["precipitacao"].iloc[0]))
        self.assertFalse(bool(t["flag_precipitacao"].iloc[0]))

    def test_coluna_ausente_no_arquivo_fica_vazia_e_flag_desconhecida(self):
        bruto = leitor.ler_maws55(texto([linha_bruta("2025-09-22 10:00:07")])).drop(columns=["Precipitação"])
        t = tratamento.tratar(bruto)
        self.assertTrue(pd.isna(t["precipitacao"].iloc[0]))
        self.assertTrue(pd.isna(t["flag_precipitacao"].iloc[0]), "flag None = não avaliado, diferente de False")

    def test_indice_nao_sequencial_nao_cria_linhas_extras(self):
        bruto = leitor.ler_maws55(texto([linha_bruta(f"2025-09-22 10:{m:02d}:07") for m in (0, 15, 30)]))
        t = tratamento.tratar(bruto.iloc[[0, 2]])                  # índice 0 e 2
        self.assertEqual(len(t), 2)

    def test_lacuna_temporal_e_desconhecida(self):
        self.assertTrue(pd.isna(self.tratar()["lacuna_temporal"].iloc[0]))

    def test_horarios_no_mesmo_balde_mantem_o_mais_recente(self):
        registros = [linha_bruta("2025-09-22 10:00:07", 1.0), linha_bruta("2025-09-22 10:00:40", 2.0)]
        t = tratamento.tratar(leitor.ler_maws55(texto(registros)))
        self.assertEqual((len(t), t["pressao_inst_hpa"].iloc[0], t.attrs["duplicados_descartados"]), (1, 2.0, 1))


@unittest.skipUnless(os.path.exists(ARQUIVO_TRATADO), "arquivo tratado do Estudante 1 não está nesta máquina")
class TestTratamentoContraOArquivoDoEstudante1(unittest.TestCase):
    """Roda as regras sobre as colunas BRUTAS do arquivo tratado dele e exige o mesmo resultado."""

    _cache = None

    def referencia(self):
        """Lê o xlsx grande uma vez só para a classe (a leitura leva cerca de 1 minuto)."""
        if TestTratamentoContraOArquivoDoEstudante1._cache is None:
            ref = pd.read_excel(ARQUIVO_TRATADO, sheet_name="dados_tratados")
            ref["UTC -3"] = pd.to_datetime(ref["UTC -3"])
            TestTratamentoContraOArquivoDoEstudante1._cache = ref
        return TestTratamentoContraOArquivoDoEstudante1._cache.copy()

    def test_valores_e_flags_identicos_no_layout_de_56(self):
        """Layout de 56 valores (a partir de 22/08/2022): resultado idêntico ao dele.
        As linhas do layout de 52 ficam de fora de propósito: nelas o arquivo dele tem os nomes
        das colunas deslocados (ver o teste seguinte)."""
        ref = self.referencia()
        ref = ref.loc[ref["Precipitação"].notna() | ref["Umid solo med"].notna()]
        bruto = ref[["UTC -3"] + nomes_brutos()].copy()
        t = tratamento.tratar(bruto)
        ref = ref.sort_values("UTC -3")
        ref = ref.loc[~ref["UTC -3"].dt.floor("15min").duplicated(keep="last")].reset_index(drop=True)
        self.assertEqual(len(t), len(ref))
        diferentes = []
        for v in catalogo.VARIAVEIS:
            esperado = pd.to_numeric(ref[v.coluna_arquivo], errors="coerce").astype(float).values
            obtido = t[v.coluna].astype(float).values
            if not np.array_equal(esperado, obtido, equal_nan=True):
                diferentes.append(v.coluna)
            if v.flag_arquivo:
                if not (ref[v.flag_arquivo].astype(bool).values == t[catalogo.nome_flag(v)].astype(bool).values).all():
                    diferentes.append(catalogo.nome_flag(v))
        self.assertEqual(diferentes, [], "colunas que divergem do tratamento do Estudante 1")

    def test_texto_de_56_valores_chega_igual_ao_arquivo_dele(self):
        """Do .txt (sintético, feito dos valores brutos dele) até a tabela, sem perder nem trocar valor."""
        ref = self.referencia()
        ref = ref.loc[ref["Precipitação"].notna()].sample(300, random_state=1).sort_values("UTC -3")
        linhas = []
        for _, r in ref.iterrows():
            valores = ["" if pd.isna(r[n]) else repr(float(r[n])) for n in leitor.ORDEM_56]
            linhas.append(",".join(["EMA_SER_01", "15m", f"{pd.Timestamp(r['UTC']):%Y-%m-%d}", f"{pd.Timestamp(r['UTC']):%H:%M:%S}"] + valores))
        df = leitor.ler_maws55(("\n".join(linhas) + "\n").encode())
        self.assertEqual(len(df), 300)
        pd.testing.assert_frame_equal(df[leitor.ORDEM_56].reset_index(drop=True),
                                      ref[leitor.ORDEM_56].astype("float64").reset_index(drop=True))
        self.assertTrue((df["UTC -3"].values == ref["UTC -3"].values).all())

    def test_trecho_de_52_valores_esta_deslocado_no_arquivo_dele(self):
        """No arquivo tratado do Estudante 1, as linhas de 15/07 a 22/08/2022 (52 valores) receberam
        nomes de 56 colunas na ordem; por isso 'Temperatura inst LPNET14 (NTC)' traz a direção do vento.
        O leitor usa o layout de 52 e coloca cada valor na variável certa."""
        ref = self.referencia()
        antigo = ref.loc[ref["Precipitação"].isna() & ref["Umid solo med"].isna()]
        self.assertEqual(len(antigo), 3653)
        r = antigo.iloc[0]
        valores = [r[n] for n in leitor.ORDEM_56[:52]]            # os 52 valores na posição em que vieram
        linha = ",".join(["EMA_SER_01", "15m", f"{pd.Timestamp(r['UTC']):%Y-%m-%d}", f"{pd.Timestamp(r['UTC']):%H:%M:%S}"]
                         + [repr(float(v)) for v in valores]).encode()
        certo = leitor.ler_maws55(linha).iloc[0]
        self.assertEqual(certo["Direção vento med"], r["Temperatura inst LPNET14 (NTC)"])
        self.assertEqual(certo["Temp solo inst"], r["Velocidade vento max"])
        self.assertEqual(certo["Precipitação"], r["Umid solo inst"])
        self.assertTrue(pd.isna(certo["Temperatura inst LPNET14 (NTC)"]))


class FtpFalso:
    """Imita o mínimo de ftplib.FTP, sem rede."""
    instancias = []

    def __init__(self, arquivos, falhas_download=0):
        self.arquivos, self.falhas = arquivos, falhas_download
        self.conexoes = 0
        self.cwd_chamado = None

    def __call__(self, timeout=None):
        self.conexoes += 1
        return self

    def connect(self, host, porta): self.host = (host, porta)
    def login(self, usuario, senha): self.login_ok = (usuario, senha)
    def set_pasv(self, v): pass
    def cwd(self, pasta): self.cwd_chamado = pasta
    def quit(self): pass
    def nlst(self): return list(self.arquivos)

    def retrbinary(self, comando, callback):
        if self.falhas > 0:
            self.falhas -= 1
            raise OSError("queda de conexão simulada")
        callback(self.arquivos[comando.split(" ", 1)[1]])


class TestFontes(unittest.TestCase):
    def test_filtrar_e_ordenar(self):
        nomes = ["lixo.txt", "EMA_15m_20250922_1015.txt", "EMA_15m_20250922_1000.txt", "EMA_15m_20260101_0000.txt",
                 "/pasta/EMA_15m_20250921_2345.TXT", "EMA_1h_20250922_1000.txt"]
        self.assertEqual(filtrar_e_ordenar(nomes, "tudo"), [
            "EMA_15m_20250921_2345.TXT", "EMA_15m_20250922_1000.txt", "EMA_15m_20250922_1015.txt", "EMA_15m_20260101_0000.txt"])
        self.assertEqual(len(filtrar_e_ordenar(nomes, "202509")), 3)
        self.assertEqual(len(filtrar_e_ordenar(nomes, "20250922")), 2)
        self.assertEqual(filtrar_e_ordenar(nomes, None, 1), ["EMA_15m_20260101_0000.txt"])
        self.assertEqual(filtrar_e_ordenar(nomes, None, 0), [])
        with self.assertRaises(ValueError):
            filtrar_e_ordenar(nomes, "2025-09")

    def test_pasta_local(self):
        with tempfile.TemporaryDirectory() as pasta:
            with open(os.path.join(pasta, "a.txt"), "wb") as f:
                f.write(b"oi")
            with FontePastaLocal(pasta) as fonte:
                self.assertEqual(fonte.listar(), ["a.txt"])
                self.assertEqual(fonte.ler("a.txt"), b"oi")
        with self.assertRaises(FileNotFoundError):
            with FontePastaLocal("/nao/existe"):
                pass

    def config(self, **extra):
        return ConfigFTP(host="ftp.exemplo", usuario="u", senha="SEGREDO123", pasta="/dados", **extra)

    def test_ftp_lista_e_baixa(self):
        falso = FtpFalso({"a.txt": b"conteudo"})
        with FonteFTP(self.config(), fabrica_ftp=falso, espera_s=0) as fonte:
            self.assertEqual(fonte.listar(), ["a.txt"])
            self.assertEqual(fonte.ler("a.txt"), b"conteudo")
        self.assertEqual(falso.cwd_chamado, "/dados")
        self.assertEqual(falso.host, ("ftp.exemplo", 21))

    def test_ftp_reconecta_depois_de_falha(self):
        falso = FtpFalso({"a.txt": b"x"}, falhas_download=1)
        with FonteFTP(self.config(), fabrica_ftp=falso, espera_s=0) as fonte:
            self.assertEqual(fonte.ler("a.txt"), b"x")
        self.assertEqual(falso.conexoes, 2)

    def test_ftp_desiste_depois_das_tentativas(self):
        falso = FtpFalso({"a.txt": b"x"}, falhas_download=99)
        with FonteFTP(self.config(), fabrica_ftp=falso, espera_s=0, tentativas=2) as fonte:
            with self.assertRaises(ConnectionError):
                fonte.ler("a.txt")

    def test_falha_de_conexao_nao_vaza_a_senha(self):
        def quebrada(timeout=None):
            raise OSError("sem rede, senha=SEGREDO123")
        with self.assertRaises(ConnectionError) as ctx:
            with FonteFTP(self.config(), fabrica_ftp=quebrada):
                pass
        self.assertNotIn("SEGREDO123", str(ctx.exception))

    def test_criar_fonte(self):
        self.assertIsInstance(criar_fonte("pasta", pasta="/x"), FontePastaLocal)
        for args in (("pasta", None, None), ("ftp", None, None), ("outra", None, None)):
            with self.assertRaises(ValueError):
                criar_fonte(*args)


class TestConfig(unittest.TestCase):
    def test_arquivo_env_e_variaveis_de_ambiente(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "config.env")
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("# comentario\nFTP_HOST=h1\nFTP_USER='u1'\nFTP_PASS=\"p1\"\nFTP_DIR=/d\n")
            self.assertEqual(ler_arquivo_env(caminho)["FTP_USER"], "u1")
            c = carregar_config_ftp(caminho, ambiente={"FTP_HOST": "h2"})
            self.assertEqual((c.host, c.usuario, c.senha, c.pasta, c.porta, c.tls), ("h2", "u1", "p1", "/d", 21, False))
            self.assertNotIn("p1", repr(c), "senha não pode aparecer no repr")

    def test_faltando_cita_so_o_nome(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = os.path.join(pasta, "config.env")
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("FTP_HOST=h\nFTP_USER=u\nFTP_PASS=COLOQUE_A_SENHA\n")
            with self.assertRaises(ConfigError) as ctx:
                carregar_config_ftp(caminho, ambiente={})
            self.assertIn("FTP_PASS", str(ctx.exception))
            self.assertNotIn("COLOQUE_A_SENHA", str(ctx.exception))

    def test_arquivo_ausente_e_porta_invalida(self):
        with self.assertRaises(ConfigError):
            carregar_config_ftp("/nao/existe.env", ambiente={})
        with self.assertRaises(ConfigError):
            carregar_config_ftp("/nao/existe.env", ambiente={"FTP_HOST": "h", "FTP_USER": "u", "FTP_PASS": "p", "FTP_PORT": "abc"})

    def test_exemplo_nao_tem_segredo_real(self):
        exemplo = ler_arquivo_env(os.path.join(PASTA_PROJETO, "config.exemplo.env"))
        for chave in ("FTP_HOST", "FTP_USER", "FTP_PASS"):
            self.assertTrue(exemplo[chave].startswith("COLOQUE_"))


class BancoETemp(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.db_original, self.brutos_original = banco.DB_PATH, ingestao.PASTA_BRUTOS
        banco.DB_PATH = os.path.join(self.pasta, "dados", "leituras.db")
        ingestao.PASTA_BRUTOS = os.path.join(self.pasta, "brutos")
        os.makedirs(os.path.dirname(banco.DB_PATH))
        self.conn = sqlite3.connect(banco.DB_PATH)
        consultas.inicializar_schema(self.conn)
        self.fonte_dir = os.path.join(self.pasta, "fonte")
        os.makedirs(self.fonte_dir)

    def tearDown(self):
        self.conn.close()
        banco.DB_PATH, ingestao.PASTA_BRUTOS = self.db_original, self.brutos_original
        shutil.rmtree(self.pasta, ignore_errors=True)

    def escrever(self, horario, valor=1.0, conteudo=None, **espec):
        with open(os.path.join(self.fonte_dir, nome_arquivo(horario)), "wb") as f:
            f.write(conteudo if conteudo is not None else texto([linha_bruta(horario, valor, **espec)]))

    def n(self, tabela="meteorologia_15min"):
        return self.conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]


class TestIngestao(BancoETemp):
    def executar(self, **kw):
        with FontePastaLocal(self.fonte_dir) as fonte:
            nomes = filtrar_e_ordenar(fonte.listar(), "tudo")
            return ingestao.executar(self.conn, fonte, nomes, **kw)

    def test_grava_diario_e_nao_repete(self):
        for i, h in enumerate(("2025-09-22 10:00:07", "2025-09-22 10:15:08", "2025-09-22 10:30:07")):
            self.escrever(h, 10 + i)
        r = self.executar()
        self.assertEqual([x.status for x in r], ["ok"] * 3)
        self.assertEqual(self.n(), 3)
        self.assertEqual(len(consultas.ultimas_ingestoes(self.conn)), 3)
        r2 = self.executar()
        self.assertEqual([x.status for x in r2], ["ignorado"] * 3)
        self.assertEqual((self.n(), len(consultas.ultimas_ingestoes(self.conn))), (3, 3))

    def test_arquivo_novo_nao_apaga_o_resto_do_dia(self):
        consultas.salvar_meteorologia(self.conn, pd.DataFrame({
            "timestamp_15min": pd.date_range("2025-09-22", periods=96, freq="15min"), "pressao_inst_hpa": 1.0}))
        self.escrever("2025-09-22 10:00:07", 777.0)
        self.executar()
        self.assertEqual(self.n(), 96)
        v = self.conn.execute("SELECT pressao_inst_hpa FROM meteorologia_15min "
                              "WHERE timestamp_15min='2025-09-22 10:00:00'").fetchone()[0]
        self.assertEqual(v, 777.0)

    def test_arquivo_reenviado_com_conteudo_novo_e_reprocessado(self):
        self.escrever("2025-09-22 10:00:07", 1.0)
        self.executar()
        self.escrever("2025-09-22 10:00:07", 2.0)
        self.assertEqual(self.executar()[0].status, "ok")
        v = self.conn.execute("SELECT pressao_inst_hpa FROM meteorologia_15min").fetchone()[0]
        self.assertEqual((v, self.n()), (2.0, 1))

    def test_arquivo_ruim_nao_derruba_os_outros_e_fica_no_diario(self):
        self.escrever("2025-09-22 10:00:07", 1.0)
        self.escrever("2025-09-22 10:15:08", conteudo=b"isto nao e dado da estacao")
        self.escrever("2025-09-22 10:30:07", 3.0)
        r = self.executar()
        self.assertEqual([x.status for x in r], ["ok", "erro", "ok"])
        self.assertIn("FormatoInvalido", r[1].mensagem)
        self.assertEqual(self.n(), 2)
        erros = self.conn.execute("SELECT nome_arquivo, mensagem FROM ingestao_arquivos WHERE status='erro'").fetchall()
        self.assertEqual(len(erros), 1)
        # corrigido o arquivo, ele é reprocessado (erro não conta como feito)
        self.escrever("2025-09-22 10:15:08", 2.0)
        self.assertEqual(self.executar()[1].status, "ok")
        self.assertEqual(self.n(), 3)

    def test_simular_nao_grava_nada(self):
        self.escrever("2025-09-22 10:00:07", 1.0)
        r = self.executar(simular=True)
        self.assertEqual((r[0].status, r[0].linhas_gravadas), ("simulado", 1))
        self.assertEqual((self.n(), self.n("ingestao_arquivos")), (0, 0))

    def test_flags_e_vazios_chegam_ao_banco(self):
        self.escrever("2025-09-22 10:00:07", **{"Umidade Relativa inst": 150, "Precipitação": np.nan})
        self.executar()
        linha = self.conn.execute("SELECT umidade_relativa_inst_pct, flag_umidade_relativa_inst_pct, "
                                  "precipitacao, flag_precipitacao FROM meteorologia_15min").fetchone()
        self.assertEqual(linha, (None, 1, None, 0))

    def test_meteorologia_nova_aparece_na_leitura_da_usina(self):
        self.conn.execute("INSERT INTO leitura_15min (timestamp_15min, potencia_fv_kw) VALUES ('2025-09-22 10:00:00', 50)")
        self.conn.commit()
        self.escrever("2025-09-22 10:00:07", **{"Radiação solar global inst LPPYRA02": 800, "Radiação solar global inst LPNET14": 780})
        self.executar()
        d = consultas.leitura_15min_do_dia(self.conn, "2025-09-22")
        self.assertEqual((d.loc[0, "ghi_lppyra02_w_m2"], d.loc[0, "ghi_disponivel"]), (800, 1))

    def test_copia_bruta_so_para_ftp_e_sem_sobrescrever(self):
        conteudo = texto([linha_bruta("2025-09-22 10:00:07", 1.0)])
        nome = nome_arquivo("2025-09-22 10:00:07")
        falso = FtpFalso({nome: conteudo})
        with FonteFTP(ConfigFTP("h", "u", "s"), fabrica_ftp=falso, espera_s=0) as fonte:
            r = ingestao.executar(self.conn, fonte, [nome])
        self.assertEqual(r[0].status, "ok")
        with open(os.path.join(ingestao.PASTA_BRUTOS, nome), "rb") as f:
            self.assertEqual(f.read(), conteudo)
        novo = texto([linha_bruta("2025-09-22 10:00:07", 2.0)])
        destino = ingestao.guardar_copia_bruta(nome, novo)
        self.assertNotEqual(os.path.basename(destino), nome, "conteúdo diferente não sobrescreve")
        self.assertEqual(len(os.listdir(ingestao.PASTA_BRUTOS)), 2)
        self.assertEqual(os.listdir(self.fonte_dir), [], "fonte pasta não copia nada")

    def test_ftp_falha_ao_baixar_vai_para_o_diario(self):
        falso = FtpFalso({"X_15m_20250922_1000.txt": b"a"}, falhas_download=99)
        with FonteFTP(ConfigFTP("h", "u", "s"), fabrica_ftp=falso, espera_s=0, tentativas=1) as fonte:
            r = ingestao.executar(self.conn, fonte, ["X_15m_20250922_1000.txt"])
        self.assertEqual(r[0].status, "erro")
        self.assertEqual(self.n("ingestao_arquivos"), 1)


class TestLinhaDeComando(BancoETemp):
    def test_pasta_local_ponta_a_ponta(self):
        self.escrever("2025-09-22 10:00:07", 1.0)
        self.escrever("2025-09-22 10:15:08", 2.0)
        codigo = aquisicao_maws55.main(["--fonte", "pasta", "--pasta", self.fonte_dir, "--periodo", "tudo"])
        self.assertEqual((codigo, self.n()), (0, 2))

    def test_sem_config_ftp_sai_com_codigo_2_sem_vazar(self):
        sem_env = os.path.join(self.pasta, "nao_existe.env")
        antigos = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("FTP_")}
        try:
            codigo = aquisicao_maws55.main(["--config", sem_env])
        finally:
            os.environ.update(antigos)
        self.assertEqual(codigo, 2)

    def test_erro_em_arquivo_da_codigo_1(self):
        self.escrever("2025-09-22 10:00:07", conteudo=b"lixo")
        self.assertEqual(aquisicao_maws55.main(["--fonte", "pasta", "--pasta", self.fonte_dir, "--periodo", "tudo"]), 1)

    def test_muitos_arquivos_exigem_confirmacao(self):
        for i in range(aquisicao_maws55.LIMITE_SEM_CONFIRMAR + 1):
            h = pd.Timestamp("2025-01-01") + pd.Timedelta(minutes=15 * i)
            with open(os.path.join(self.fonte_dir, nome_arquivo(h)), "wb") as f:
                f.write(b"x")
        self.assertEqual(aquisicao_maws55.main(["--fonte", "pasta", "--pasta", self.fonte_dir, "--periodo", "tudo"]), 2)
        self.assertEqual(self.n("ingestao_arquivos"), 0)


if __name__ == "__main__":
    unittest.main()
