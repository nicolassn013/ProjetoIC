"""
Testes do banco: migrações, tabela meteorologia_15min e a view de junção.

Rodar a partir da raiz do projeto:
    python -m unittest discover -s testes -v

Cada teste usa um banco temporário (nunca toca em dados/leituras.db).
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

import banco                      # noqa: E402
import catalogo_meteorologia as catalogo  # noqa: E402
import consultas                  # noqa: E402
import migracoes                  # noqa: E402


def dia_meteorologia(data="2025-09-22", linhas=96):
    """DataFrame de um dia de meteorologia, com todas as colunas do catálogo."""
    ts = pd.date_range(f"{data} 00:00", periods=linhas, freq="15min")
    df = pd.DataFrame({"timestamp_15min": ts})
    df["timestamp_original"] = ts + pd.Timedelta(seconds=7)
    df["lacuna_temporal"] = False
    for c in catalogo.colunas_valores():
        df[c] = 1.0
    for c in catalogo.colunas_flags():
        df[c] = False
    return df


class BancoTemporario(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp()
        self.db_original = banco.DB_PATH
        banco.DB_PATH = os.path.join(self.pasta, "dados", "leituras.db")
        os.makedirs(os.path.dirname(banco.DB_PATH))
        self.conn = sqlite3.connect(banco.DB_PATH)

    def tearDown(self):
        self.conn.close()
        banco.DB_PATH = self.db_original
        shutil.rmtree(self.pasta, ignore_errors=True)

    def backups(self):
        pasta = os.path.join(os.path.dirname(banco.DB_PATH), "backups")
        return os.listdir(pasta) if os.path.isdir(pasta) else []


class TestMigracoes(BancoTemporario):
    def test_banco_novo_chega_na_ultima_versao(self):
        n = len(migracoes.listar_migracoes())
        aplicadas = consultas.inicializar_schema(self.conn)
        self.assertEqual(aplicadas, list(range(1, n + 1)))
        self.assertEqual(migracoes.versao_atual(self.conn), n)
        tabelas = {r[0] for r in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        for esperado in ("leitura_15min", "resumo_diario", "meteorologia_15min", "vw_leitura_completa"):
            self.assertIn(esperado, tabelas)
        self.assertEqual(self.backups(), [], "banco vazio não precisa de backup")

    def test_rodar_duas_vezes_nao_faz_nada_na_segunda(self):
        consultas.inicializar_schema(self.conn)
        self.assertEqual(consultas.inicializar_schema(self.conn), [])

    def test_banco_antigo_com_dados_e_atualizado_com_backup(self):
        # banco criado antes do sistema de migrações: tabelas existem, user_version = 0
        with open(os.path.join(migracoes.PASTA_MIGRACOES, "001_base.sql"), encoding="utf-8") as f:
            self.conn.executescript(f.read())
        self.conn.execute("INSERT INTO leitura_15min (timestamp_15min, potencia_fv_kw) "
                          "VALUES ('2025-09-22 12:00:00', 99.5)")
        self.conn.commit()
        self.assertEqual(migracoes.versao_atual(self.conn), 0)

        aplicadas = consultas.inicializar_schema(self.conn)
        self.assertEqual(aplicadas[0], 1)
        valor = self.conn.execute("SELECT potencia_fv_kw FROM leitura_15min").fetchone()[0]
        self.assertEqual(valor, 99.5, "dado antigo deve continuar intacto")
        self.assertEqual(len(self.backups()), 1, "banco com dados deve gerar 1 backup")

    def test_banco_v2_entregue_e_atualizado_para_a_ultima_versao(self):
        """Quem recebeu o banco versão 2 (001+002) precisa chegar na última versão sem perder dado."""
        for numero, caminho in migracoes.listar_migracoes()[:2]:
            with open(caminho, encoding="utf-8") as f:
                self.conn.executescript(f"BEGIN;\n{f.read()}\nPRAGMA user_version = {numero};\nCOMMIT;")
        self.conn.execute("INSERT INTO leitura_15min (timestamp_15min, potencia_fv_kw, temperatura_c) "
                          "VALUES ('2025-09-22 12:00:00', 99.5, 31.5)")
        self.conn.execute("INSERT INTO meteorologia_15min (timestamp_15min, pressao_inst_hpa) "
                          "VALUES ('2025-09-22 12:00:00', 1010.0)")
        self.conn.commit()
        aplicadas = consultas.inicializar_schema(self.conn)
        self.assertEqual(aplicadas, [3, 4])
        # 003 copia o valor legado de leitura_15min para a coluna nova
        self.assertEqual(self.conn.execute("SELECT temperatura_c FROM meteorologia_15min").fetchone()[0], 31.5)
        self.assertEqual(self.conn.execute("SELECT pressao_inst_hpa FROM meteorologia_15min").fetchone()[0], 1010.0)
        self.assertEqual(len(self.backups()), 1)

    def test_numeracao_das_migracoes_e_continua(self):
        numeros = [n for n, _ in migracoes.listar_migracoes()]
        self.assertEqual(numeros, list(range(1, len(numeros) + 1)))


class TestCatalogo(BancoTemporario):
    def test_catalogo_bate_com_schema(self):
        consultas.inicializar_schema(self.conn)
        self.assertEqual(consultas.verificar_schema_meteorologia(self.conn),
                         {"faltando_no_banco": [], "sobrando_no_banco": []})

    def test_contagens_do_catalogo(self):
        self.assertEqual(len(catalogo.VARIAVEIS), 56)
        self.assertEqual(len(catalogo.colunas_valores()), 56)
        self.assertEqual(len(catalogo.colunas_flags()), 24)
        self.assertEqual(len(catalogo.colunas_meteorologia_15min()), 83)
        todas = catalogo.colunas_meteorologia_15min()
        self.assertEqual(len(todas), len(set(todas)), "nome de coluna repetido")

    def test_variaveis_antigas_existem_nas_duas_tabelas(self):
        consultas.inicializar_schema(self.conn)
        leitura = {r[1] for r in self.conn.execute("PRAGMA table_info(leitura_15min)")}
        meteo = {r[1] for r in self.conn.execute("PRAGMA table_info(meteorologia_15min)")}
        for coluna in catalogo.COLUNAS_LEGADAS_EM_LEITURA:
            self.assertIn(coluna, leitura, "cópia legada sumiu de leitura_15min")
            self.assertIn(coluna, meteo, "valor novo não está em meteorologia_15min")


class TestSalvarMeteorologia(BancoTemporario):
    def setUp(self):
        super().setUp()
        consultas.inicializar_schema(self.conn)

    def n_linhas(self):
        return self.conn.execute("SELECT COUNT(*) FROM meteorologia_15min").fetchone()[0]

    def test_idempotente(self):
        df = dia_meteorologia()
        consultas.salvar_meteorologia(self.conn, df)
        consultas.salvar_meteorologia(self.conn, df)
        self.assertEqual(self.n_linhas(), 96)

    def test_outro_dia_nao_e_tocado(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia("2025-09-22"))
        consultas.salvar_meteorologia(self.conn, dia_meteorologia("2025-09-23"))
        consultas.salvar_meteorologia(self.conn, dia_meteorologia("2025-09-22"))
        self.assertEqual(self.n_linhas(), 192)

    def test_vazio_vira_null_e_zero_continua_zero(self):
        df = dia_meteorologia(linhas=4)
        df["umidade_relativa_inst_pct"] = [0.0, np.nan, 50.0, 60.0]
        consultas.salvar_meteorologia(self.conn, df)
        valores = [r[0] for r in self.conn.execute(
            "SELECT umidade_relativa_inst_pct FROM meteorologia_15min ORDER BY timestamp_15min")]
        self.assertEqual(valores, [0.0, None, 50.0, 60.0])

    def test_flags_viram_0_1_ou_null(self):
        df = dia_meteorologia(linhas=3)
        df["flag_temperatura_c"] = [True, False, np.nan]
        consultas.salvar_meteorologia(self.conn, df)
        valores = [r[0] for r in self.conn.execute(
            "SELECT flag_temperatura_c FROM meteorologia_15min ORDER BY timestamp_15min")]
        self.assertEqual(valores, [1, 0, None])

    def test_coluna_ausente_fica_null(self):
        df = dia_meteorologia(linhas=2)[["timestamp_15min", "pressao_inst_hpa"]]
        consultas.salvar_meteorologia(self.conn, df)
        linha = self.conn.execute(
            "SELECT pressao_inst_hpa, pressao_med_hpa FROM meteorologia_15min LIMIT 1").fetchone()
        self.assertEqual(linha, (1.0, None))

    def test_coluna_desconhecida_e_erro(self):
        df = dia_meteorologia(linhas=2)
        df["coluna_inventada"] = 1
        with self.assertRaises(ValueError):
            consultas.salvar_meteorologia(self.conn, df)
        self.assertEqual(self.n_linhas(), 0)

    def test_timestamp_repetido_e_erro_e_nao_apaga_nada(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=4))
        ruim = dia_meteorologia(linhas=4)
        ruim.loc[1, "timestamp_15min"] = ruim.loc[0, "timestamp_15min"]
        with self.assertRaises(ValueError):
            consultas.salvar_meteorologia(self.conn, ruim)
        self.assertEqual(self.n_linhas(), 4)

    def test_sem_timestamp_e_erro(self):
        with self.assertRaises(ValueError):
            consultas.salvar_meteorologia(self.conn, dia_meteorologia().drop(columns="timestamp_15min"))

    def test_avisa_quando_dia_fica_com_menos_linhas(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=96))
        resposta = consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=10))
        self.assertEqual(resposta["dias_com_menos_linhas"], ["2025-09-22"])
        self.assertEqual(resposta["dias"]["2025-09-22"], {"linhas_antes": 96, "linhas_depois": 10})

    def test_mesclar_preserva_os_outros_horarios_do_dia(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=96))
        um = dia_meteorologia(linhas=1)
        um["pressao_inst_hpa"] = 999.0
        resposta = consultas.salvar_meteorologia(self.conn, um, modo="mesclar")
        self.assertEqual(self.n_linhas(), 96, "mesclar 1 linha não pode apagar o resto do dia")
        self.assertEqual((resposta["linhas_gravadas"], resposta["linhas_substituidas"]), (1, 1))
        v = self.conn.execute("SELECT pressao_inst_hpa FROM meteorologia_15min "
                              "WHERE timestamp_15min = '2025-09-22 00:00:00'").fetchone()[0]
        self.assertEqual(v, 999.0)

    def test_substituir_dia_com_uma_linha_apaga_o_resto_do_dia(self):
        """Documenta o perigo do modo padrão (e por que a aquisição usa 'mesclar')."""
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=96))
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=1))
        self.assertEqual(self.n_linhas(), 1)

    def test_modo_invalido_e_erro(self):
        with self.assertRaises(ValueError):
            consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=1), modo="outro")

    def test_diario_de_ingestao(self):
        self.assertFalse(consultas.ingestao_ja_feita(self.conn, "a.txt", "abc"))
        consultas.registrar_ingestao(self.conn, "pasta", "a.txt", "abc", "erro", mensagem="falhou")
        self.assertFalse(consultas.ingestao_ja_feita(self.conn, "a.txt", "abc"), "erro não conta como feito")
        consultas.registrar_ingestao(self.conn, "pasta", "a.txt", "abc", "ok", linhas_lidas=1, linhas_gravadas=1)
        self.assertTrue(consultas.ingestao_ja_feita(self.conn, "a.txt", "abc"))
        self.assertFalse(consultas.ingestao_ja_feita(self.conn, "a.txt", "outro_conteudo"))
        consultas.registrar_ingestao(self.conn, "pasta", "a.txt", "abc", "ok", linhas_lidas=1, linhas_gravadas=1)
        self.assertEqual(len(consultas.ultimas_ingestoes(self.conn)), 2, "mesmo status não duplica")

    def test_leitura_do_dia(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia())
        df = consultas.meteorologia_15min_do_dia(self.conn, "2025-09-22")
        self.assertEqual(len(df), 96)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["timestamp_15min"]))

    def test_cobertura_lista_as_56_variaveis(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=4))
        cob = consultas.cobertura_meteorologia(self.conn)
        self.assertEqual(len(cob), 56)
        self.assertTrue((cob["tabela"] == "meteorologia_15min").all())
        linha = cob[cob["coluna"] == "pressao_inst_hpa"].iloc[0]
        self.assertEqual((linha["preenchidos"], linha["total_linhas"]), (4, 4))


class TestViewEJuncao(BancoTemporario):
    def setUp(self):
        super().setUp()
        consultas.inicializar_schema(self.conn)
        self.conn.execute("INSERT INTO leitura_15min (timestamp_15min, potencia_fv_kw) VALUES "
                          "('2025-09-22 00:00:00', 1.0), ('2025-09-22 00:15:00', 2.0), "
                          "('2025-09-23 00:00:00', 3.0)")
        self.conn.commit()

    def test_view_mantem_linhas_da_usina_sem_meteorologia(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=1))  # só 00:00 do dia 22
        df = consultas.leitura_completa_do_dia(self.conn, "2025-09-22")
        self.assertEqual(len(df), 2)
        self.assertEqual(df.loc[0, "pressao_inst_hpa"], 1.0)
        self.assertTrue(pd.isna(df.loc[1, "pressao_inst_hpa"]), "sem meteorologia deve vir NULL, não zero")

    def test_view_prefere_meteorologia_nova_e_cai_para_a_legada(self):
        self.conn.execute("UPDATE leitura_15min SET temperatura_c = 20.0")
        self.conn.commit()
        df = dia_meteorologia(linhas=1)       # só 00:00 do dia 22; valor 1.0 em tudo
        consultas.salvar_meteorologia(self.conn, df)
        v = consultas.leitura_completa_do_dia(self.conn, "2025-09-22")
        self.assertEqual(v.loc[0, "temperatura_c"], 1.0, "deve valer a meteorologia nova")
        self.assertEqual(v.loc[1, "temperatura_c"], 20.0, "sem meteorologia nova, vale a legada")

    def test_leitura_15min_do_dia_mantem_as_14_colunas_de_sempre(self):
        df = consultas.leitura_15min_do_dia(self.conn, "2025-09-22")
        self.assertEqual(list(df.columns), [
            "timestamp_15min", "potencia_fv_kw", "potencia_inversores_soma_kw",
            "INV01", "INV02", "INV03", "INV04", "ghi_lppyra02_w_m2", "ghi_lpnet14_w_m2",
            "temperatura_c", "vento_m_s", "precipitacao", "meteorologia_disponivel", "ghi_disponivel"])
        self.assertEqual(len(df), 2)

    def test_cobertura_geral_conta_meteorologia_pela_view(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=1))
        c = consultas.cobertura_geral(self.conn)
        self.assertEqual((c["total_registros_15min"], c["com_meteorologia"], c["com_ghi"]), (3, 1, 1))

    def test_view_tem_uma_linha_por_timestamp(self):
        consultas.salvar_meteorologia(self.conn, dia_meteorologia(linhas=2))
        n = self.conn.execute("SELECT COUNT(*) FROM vw_leitura_completa").fetchone()[0]
        self.assertEqual(n, 3)


class TestSalvarDia(BancoTemporario):
    def test_devolve_contagem_antes_e_depois(self):
        consultas.inicializar_schema(self.conn)
        ts = pd.date_range("2025-09-22", periods=4, freq="15min")
        df = pd.DataFrame({"timestamp_15min": ts, "potencia_fv_kw": [1.0] * 4})
        resumo = pd.DataFrame([{"data": "2025-09-22", "registros_15min": 4}])
        primeira = consultas.salvar_dia(self.conn, "2025-09-22", df, resumo)
        segunda = consultas.salvar_dia(self.conn, "2025-09-22", df.iloc[:2], resumo)
        self.assertEqual(primeira, {"linhas_antes": 0, "linhas_depois": 4})
        self.assertEqual(segunda, {"linhas_antes": 4, "linhas_depois": 2})


if __name__ == "__main__":
    unittest.main()
