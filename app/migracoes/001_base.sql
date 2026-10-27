-- 001_base.sql
-- Tabelas principais do banco (usina + 5 variáveis meteorológicas originais).
-- IF NOT EXISTS: seguro em banco novo e em banco que já tinha essas tabelas
-- (os bancos criados antes do sistema de migrações têm user_version = 0).

CREATE TABLE IF NOT EXISTS leitura_15min (
    timestamp_15min DATETIME PRIMARY KEY,
    potencia_fv_kw REAL,
    potencia_inversores_soma_kw REAL,
    INV01 REAL, INV02 REAL, INV03 REAL, INV04 REAL,
    ghi_lppyra02_w_m2 REAL, ghi_lpnet14_w_m2 REAL,
    temperatura_c REAL, vento_m_s REAL, precipitacao REAL,
    meteorologia_disponivel BOOLEAN, ghi_disponivel BOOLEAN
);

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
);
