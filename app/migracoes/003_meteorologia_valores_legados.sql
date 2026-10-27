-- 003_meteorologia_valores_legados.sql
-- Consolidação: meteorologia_15min passa a guardar TODAS as 56 variáveis (as 5 que
-- antes só existiam em leitura_15min ganham coluna aqui). Motivo: a aquisição direta
-- do FTP da estação traz meteorologia sem relatório da usina, e leitura_15min exige
-- uma linha da usina. As colunas antigas de leitura_15min ficam como legado (o
-- pipeline da usina ainda as preenche) e a view prefere o valor de meteorologia_15min.

ALTER TABLE meteorologia_15min ADD COLUMN ghi_lppyra02_w_m2 REAL;
ALTER TABLE meteorologia_15min ADD COLUMN ghi_lpnet14_w_m2 REAL;
ALTER TABLE meteorologia_15min ADD COLUMN temperatura_c REAL;
ALTER TABLE meteorologia_15min ADD COLUMN vento_m_s REAL;
ALTER TABLE meteorologia_15min ADD COLUMN precipitacao REAL;

-- Copia o que já existia (banco antigo) para a nova coluna
UPDATE meteorologia_15min SET
    ghi_lppyra02_w_m2 = (SELECT l.ghi_lppyra02_w_m2 FROM leitura_15min l WHERE l.timestamp_15min = meteorologia_15min.timestamp_15min),
    ghi_lpnet14_w_m2 = (SELECT l.ghi_lpnet14_w_m2 FROM leitura_15min l WHERE l.timestamp_15min = meteorologia_15min.timestamp_15min),
    temperatura_c = (SELECT l.temperatura_c FROM leitura_15min l WHERE l.timestamp_15min = meteorologia_15min.timestamp_15min),
    vento_m_s = (SELECT l.vento_m_s FROM leitura_15min l WHERE l.timestamp_15min = meteorologia_15min.timestamp_15min),
    precipitacao = (SELECT l.precipitacao FROM leitura_15min l WHERE l.timestamp_15min = meteorologia_15min.timestamp_15min);

DROP VIEW IF EXISTS vw_leitura_completa;

-- Junção usina + meteorologia. Para as 5 variáveis antigas vale meteorologia_15min;
-- se ela estiver vazia, cai para a cópia legada de leitura_15min.
CREATE VIEW vw_leitura_completa AS
SELECT
    l.timestamp_15min,
    l.potencia_fv_kw,
    l.potencia_inversores_soma_kw,
    l.INV01, l.INV02, l.INV03, l.INV04,
    COALESCE(m.ghi_lppyra02_w_m2, l.ghi_lppyra02_w_m2) AS ghi_lppyra02_w_m2,
    COALESCE(m.ghi_lpnet14_w_m2, l.ghi_lpnet14_w_m2) AS ghi_lpnet14_w_m2,
    COALESCE(m.temperatura_c, l.temperatura_c) AS temperatura_c,
    COALESCE(m.vento_m_s, l.vento_m_s) AS vento_m_s,
    COALESCE(m.precipitacao, l.precipitacao) AS precipitacao,
    (m.timestamp_15min IS NOT NULL OR COALESCE(l.meteorologia_disponivel, 0) = 1) AS meteorologia_disponivel,
    (COALESCE(m.ghi_lppyra02_w_m2, l.ghi_lppyra02_w_m2, m.ghi_lpnet14_w_m2, l.ghi_lpnet14_w_m2) IS NOT NULL
        OR COALESCE(l.ghi_disponivel, 0) = 1) AS ghi_disponivel,
    m.timestamp_original,
    m.lacuna_temporal,
    m.umidade_relativa_inst_pct,
    m.umidade_relativa_med_pct,
    m.umidade_relativa_max_pct,
    m.umidade_relativa_min_pct,
    m.vento_dir_med_graus,
    m.vento_dir_max_graus,
    m.vento_dir_min_graus,
    m.vento_vel_max_m_s,
    m.vento_vel_min_m_s,
    m.ghi_lppyra02_med_w_m2,
    m.ghi_lppyra02_max_w_m2,
    m.ghi_lppyra02_min_w_m2,
    m.ghi_lpnet14_med_w_m2,
    m.ghi_lpnet14_max_w_m2,
    m.ghi_lpnet14_min_w_m2,
    m.umid_solo_inst,
    m.umid_solo_med,
    m.umid_solo_max,
    m.umid_solo_min,
    m.pressao_inst_hpa,
    m.pressao_med_hpa,
    m.pressao_max_hpa,
    m.pressao_min_hpa,
    m.temp_int_c,
    m.temperatura_med_c,
    m.temperatura_max_c,
    m.temperatura_min_c,
    m.rad_refletida_inst_w_m2,
    m.rad_refletida_med_w_m2,
    m.rad_refletida_max_w_m2,
    m.rad_refletida_min_w_m2,
    m.rad_iv_inst_w_m2,
    m.rad_iv_med_w_m2,
    m.rad_iv_max_w_m2,
    m.rad_iv_min_w_m2,
    m.rad_spf_inst_w_m2,
    m.rad_spf_med_w_m2,
    m.rad_spf_max_w_m2,
    m.rad_spf_min_w_m2,
    m.rad_liquida_inst_w_m2,
    m.rad_liquida_med_w_m2,
    m.rad_liquida_max_w_m2,
    m.rad_liquida_min_w_m2,
    m.temp_ntc_lpnet14_inst_c,
    m.temp_ntc_lpnet14_med_c,
    m.temp_ntc_lpnet14_max_c,
    m.temp_ntc_lpnet14_min_c,
    m.temp_solo_inst,
    m.temp_solo_med,
    m.temp_solo_max,
    m.temp_solo_min,
    m.flag_ghi_lppyra02_w_m2,
    m.flag_ghi_lpnet14_w_m2,
    m.flag_temperatura_c,
    m.flag_vento_m_s,
    m.flag_precipitacao,
    m.flag_umidade_relativa_inst_pct,
    m.flag_umidade_relativa_med_pct,
    m.flag_umidade_relativa_max_pct,
    m.flag_umidade_relativa_min_pct,
    m.flag_vento_dir_med_graus,
    m.flag_vento_dir_max_graus,
    m.flag_vento_dir_min_graus,
    m.flag_vento_vel_max_m_s,
    m.flag_vento_vel_min_m_s,
    m.flag_ghi_lppyra02_med_w_m2,
    m.flag_ghi_lppyra02_max_w_m2,
    m.flag_ghi_lppyra02_min_w_m2,
    m.flag_ghi_lpnet14_med_w_m2,
    m.flag_ghi_lpnet14_max_w_m2,
    m.flag_ghi_lpnet14_min_w_m2,
    m.flag_umid_solo_inst,
    m.flag_umid_solo_med,
    m.flag_umid_solo_max,
    m.flag_umid_solo_min
FROM leitura_15min l
LEFT JOIN meteorologia_15min m ON m.timestamp_15min = l.timestamp_15min;
