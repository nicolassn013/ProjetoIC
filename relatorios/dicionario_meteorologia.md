# Dicionário das variáveis meteorológicas (estação MAWS55)

Gerado do catálogo `app/catalogo_meteorologia.py` em 23/10/2026. Se a tabela e o catálogo divergirem, vale o catálogo e o banco (o teste `test_catalogo_bate_com_schema` avisa).

## Como as variáveis estão no banco (estrutura versão 4)

- Tabela **`meteorologia_15min`**: chave `timestamp_15min` (horário do arquivo em UTC-3, cortado para 15 min), `timestamp_original` (horário exato do arquivo), `lacuna_temporal`, **56 colunas de valor** e **24 colunas de flag** (83 colunas). É a **fonte de verdade da meteorologia**.
- As **5 variáveis que já existiam** em `leitura_15min` (radiação global dos dois sensores, temperatura, vento médio e precipitação) agora também estão em `meteorologia_15min`. A cópia em `leitura_15min` é **legado**: o pipeline da usina ainda a preenche e a view prefere o valor de `meteorologia_15min`.
- View **`vw_leitura_completa`**: junta `leitura_15min` + `meteorologia_15min` (toda linha da usina aparece; sem meteorologia no horário, as colunas vêm vazias). O cálculo do PR e o dashboard leem por ela, com as mesmas 14 colunas de sempre.
- Tabela **`ingestao_arquivos`**: diário dos arquivos baixados do FTP ou de pasta (nome, hash, status, linhas, erro).
- **Vazio é NULL**, nunca zero. **Flag 1** = valor invalidado pelo tratamento (o valor tratado fica vazio); flag 0 = valor mantido; flag vazia = não avaliado.
- Variáveis **sem tratamento** (32) entram **como vieram** (dado bruto), sem flag.
- Sufixo de unidade no nome (`_w_m2`, `_hpa`, `_c`, `_pct`, `_graus`, `_m_s`) só quando a grandeza deixa a unidade certa. **Todas as unidades são inferidas** e ainda não foram confirmadas.
- Ao tratar uma variável bruta: criar migração nova (ex.: `005_flags_pressao.sql` com `ALTER TABLE ... ADD COLUMN flag_...`), atualizar o catálogo e as regras em `pipeline/aquisicao/tratamento.py` e rodar os testes.

## Tabela das 56 variáveis

| Coluna no banco | Onde fica | Unidade (inferida) | Descrição | Tratada pelo Estudante 1 | Flag |
|---|---|---|---|---|---|
| `ghi_lppyra02_w_m2` | `meteorologia_15min` | W/m² | Radiação global, sensor LPPYRA02 (instantâneo) | sim | `flag_ghi_lppyra02_w_m2` |
| `ghi_lpnet14_w_m2` | `meteorologia_15min` | W/m² | Radiação global, sensor LPNET14 (instantâneo) | sim | `flag_ghi_lpnet14_w_m2` |
| `temperatura_c` | `meteorologia_15min` | °C | Temperatura do ar (instantâneo) | sim | `flag_temperatura_c` |
| `vento_m_s` | `meteorologia_15min` | m/s | Velocidade do vento (média) | sim | `flag_vento_m_s` |
| `precipitacao` | `meteorologia_15min` | mm | Precipitação no intervalo | sim | `flag_precipitacao` |
| `umidade_relativa_inst_pct` | `meteorologia_15min` | % | Umidade relativa do ar (instantâneo) | sim | `flag_umidade_relativa_inst_pct` |
| `umidade_relativa_med_pct` | `meteorologia_15min` | % | Umidade relativa do ar (média) | sim | `flag_umidade_relativa_med_pct` |
| `umidade_relativa_max_pct` | `meteorologia_15min` | % | Umidade relativa do ar (máximo) | sim | `flag_umidade_relativa_max_pct` |
| `umidade_relativa_min_pct` | `meteorologia_15min` | % | Umidade relativa do ar (mínimo) | sim | `flag_umidade_relativa_min_pct` |
| `vento_dir_med_graus` | `meteorologia_15min` | graus | Direção do vento (média) | sim | `flag_vento_dir_med_graus` |
| `vento_dir_max_graus` | `meteorologia_15min` | graus | Direção do vento (máximo) | sim | `flag_vento_dir_max_graus` |
| `vento_dir_min_graus` | `meteorologia_15min` | graus | Direção do vento (mínimo) | sim | `flag_vento_dir_min_graus` |
| `vento_vel_max_m_s` | `meteorologia_15min` | m/s | Velocidade do vento (máximo) | sim | `flag_vento_vel_max_m_s` |
| `vento_vel_min_m_s` | `meteorologia_15min` | m/s | Velocidade do vento (mínimo) | sim | `flag_vento_vel_min_m_s` |
| `ghi_lppyra02_med_w_m2` | `meteorologia_15min` | W/m² | Radiação global, sensor LPPYRA02 (média) | sim | `flag_ghi_lppyra02_med_w_m2` |
| `ghi_lppyra02_max_w_m2` | `meteorologia_15min` | W/m² | Radiação global, sensor LPPYRA02 (máximo) | sim | `flag_ghi_lppyra02_max_w_m2` |
| `ghi_lppyra02_min_w_m2` | `meteorologia_15min` | W/m² | Radiação global, sensor LPPYRA02 (mínimo) | sim | `flag_ghi_lppyra02_min_w_m2` |
| `ghi_lpnet14_med_w_m2` | `meteorologia_15min` | W/m² | Radiação global, sensor LPNET14 (média) | sim | `flag_ghi_lpnet14_med_w_m2` |
| `ghi_lpnet14_max_w_m2` | `meteorologia_15min` | W/m² | Radiação global, sensor LPNET14 (máximo) | sim | `flag_ghi_lpnet14_max_w_m2` |
| `ghi_lpnet14_min_w_m2` | `meteorologia_15min` | W/m² | Radiação global, sensor LPNET14 (mínimo) | sim | `flag_ghi_lpnet14_min_w_m2` |
| `umid_solo_inst` | `meteorologia_15min` | a confirmar | Umidade do solo (instantâneo) | sim | `flag_umid_solo_inst` |
| `umid_solo_med` | `meteorologia_15min` | a confirmar | Umidade do solo (média) | sim | `flag_umid_solo_med` |
| `umid_solo_max` | `meteorologia_15min` | a confirmar | Umidade do solo (máximo) | sim | `flag_umid_solo_max` |
| `umid_solo_min` | `meteorologia_15min` | a confirmar | Umidade do solo (mínimo) | sim | `flag_umid_solo_min` |
| `pressao_inst_hpa` | `meteorologia_15min` | hPa | Pressão atmosférica (instantâneo) | não (dado bruto) | — |
| `pressao_med_hpa` | `meteorologia_15min` | hPa | Pressão atmosférica (média) | não (dado bruto) | — |
| `pressao_max_hpa` | `meteorologia_15min` | hPa | Pressão atmosférica (máximo) | não (dado bruto) | — |
| `pressao_min_hpa` | `meteorologia_15min` | hPa | Pressão atmosférica (mínimo) | não (dado bruto) | — |
| `temp_int_c` | `meteorologia_15min` | °C | Temp int (definição a confirmar) | não (dado bruto) | — |
| `temperatura_med_c` | `meteorologia_15min` | °C | Temperatura do ar (média) | não (dado bruto) | — |
| `temperatura_max_c` | `meteorologia_15min` | °C | Temperatura do ar (máximo) | não (dado bruto) | — |
| `temperatura_min_c` | `meteorologia_15min` | °C | Temperatura do ar (mínimo) | não (dado bruto) | — |
| `rad_refletida_inst_w_m2` | `meteorologia_15min` | W/m² | Radiação solar refletida (instantâneo) | não (dado bruto) | — |
| `rad_refletida_med_w_m2` | `meteorologia_15min` | W/m² | Radiação solar refletida (média) | não (dado bruto) | — |
| `rad_refletida_max_w_m2` | `meteorologia_15min` | W/m² | Radiação solar refletida (máximo) | não (dado bruto) | — |
| `rad_refletida_min_w_m2` | `meteorologia_15min` | W/m² | Radiação solar refletida (mínimo) | não (dado bruto) | — |
| `rad_iv_inst_w_m2` | `meteorologia_15min` | W/m² | Radiação infravermelha (IV) (instantâneo) | não (dado bruto) | — |
| `rad_iv_med_w_m2` | `meteorologia_15min` | W/m² | Radiação infravermelha (IV) (média) | não (dado bruto) | — |
| `rad_iv_max_w_m2` | `meteorologia_15min` | W/m² | Radiação infravermelha (IV) (máximo) | não (dado bruto) | — |
| `rad_iv_min_w_m2` | `meteorologia_15min` | W/m² | Radiação infravermelha (IV) (mínimo) | não (dado bruto) | — |
| `rad_spf_inst_w_m2` | `meteorologia_15min` | W/m² | Radiação SPF (significado a confirmar) (instantâneo) | não (dado bruto) | — |
| `rad_spf_med_w_m2` | `meteorologia_15min` | W/m² | Radiação SPF (significado a confirmar) (média) | não (dado bruto) | — |
| `rad_spf_max_w_m2` | `meteorologia_15min` | W/m² | Radiação SPF (significado a confirmar) (máximo) | não (dado bruto) | — |
| `rad_spf_min_w_m2` | `meteorologia_15min` | W/m² | Radiação SPF (significado a confirmar) (mínimo) | não (dado bruto) | — |
| `rad_liquida_inst_w_m2` | `meteorologia_15min` | W/m² | Radiação solar líquida (instantâneo) | não (dado bruto) | — |
| `rad_liquida_med_w_m2` | `meteorologia_15min` | W/m² | Radiação solar líquida (média) | não (dado bruto) | — |
| `rad_liquida_max_w_m2` | `meteorologia_15min` | W/m² | Radiação solar líquida (máximo) | não (dado bruto) | — |
| `rad_liquida_min_w_m2` | `meteorologia_15min` | W/m² | Radiação solar líquida (mínimo) | não (dado bruto) | — |
| `temp_ntc_lpnet14_inst_c` | `meteorologia_15min` | °C | Temperatura do sensor LPNET14 (NTC) (instantâneo) | não (dado bruto) | — |
| `temp_ntc_lpnet14_med_c` | `meteorologia_15min` | °C | Temperatura do sensor LPNET14 (NTC) (média) | não (dado bruto) | — |
| `temp_ntc_lpnet14_max_c` | `meteorologia_15min` | °C | Temperatura do sensor LPNET14 (NTC) (máximo) | não (dado bruto) | — |
| `temp_ntc_lpnet14_min_c` | `meteorologia_15min` | °C | Temperatura do sensor LPNET14 (NTC) (mínimo) | não (dado bruto) | — |
| `temp_solo_inst` | `meteorologia_15min` | a confirmar | Temperatura do solo (instantâneo) | não (dado bruto) | — |
| `temp_solo_med` | `meteorologia_15min` | a confirmar | Temperatura do solo (média) | não (dado bruto) | — |
| `temp_solo_max` | `meteorologia_15min` | a confirmar | Temperatura do solo (máximo) | não (dado bruto) | — |
| `temp_solo_min` | `meteorologia_15min` | a confirmar | Temperatura do solo (mínimo) | não (dado bruto) | — |

## Observações sobre os dados (a confirmar com quem tratou)

Notadas ao conferir o arquivo `dados_meteorologicos_tratados.xlsx` (111.555 registros, 15/07/2022 16:00 a 31/07/2026 20:45):

| Variável | O que aparece | Pergunta |
|---|---|---|
| `temperatura_med_c`, `_max_c`, `_min_c` | Mínimo de **-40,0 °C** (em `inst` o tratamento já invalidou 6 valores) | Valor travado do sensor? Vai ser tratado? |
| `temp_ntc_lpnet14_*_c` | Máximo de **360** em `inst`, `med` e `max` | **Explicado (24/10/2026):** vem das 3.653 linhas de 15/07 a 22/08/2022, em que o xlsx tem nomes de colunas deslocados e esse campo traz a direção do vento. Não é erro do sensor. Ver `aquisicao_maws55.md`, seção 4.2 |
| `umid_solo_*` | Valores de **-0,4 a 1,0** | Qual a unidade (fração? índice?) e o que significa negativo? |
| `temp_solo_*` | Mínimo de 0,43 e máximo de 35 | Unidade e faixa válida? |
| `rad_iv_*`, `rad_spf_*` | Valores **negativos** (IV até -145; SPF de -86 a 88) | Negativo é esperado nesses sensores? O que é "SPF"? |
| `vento_vel_max_m_s` | Máximo de 37,7 | Unidade é m/s mesmo? (a média geral é 3,6) |
| `temp_int_c` | Entre 14,1 e 38,1 | É a temperatura interna de quê? |
| `timestamp_original` | Segundos 07 ou 08 (ex.: 16:00:07) | O registro marca o **começo ou o fim** do intervalo de 15 min? |
| `lacuna_temporal` | 51 lacunas no arquivo; ~30.257 registros ausentes estimados. Nos dados que chegam pela aquisição direta (FTP), esta coluna fica **vazia (desconhecida)** | Quais ficam vazios e quais são interpolados? |
| Cobertura | Termina em 31/07/2026 | Quando o arquivo é estendido? |
| `umid_solo_*` (regra de tratamento) | A regra do tratamento marca valor **igual a -400**, mas a coluna só tem valores de -0,4 a 1,0 (a regra nunca dispara) | O código de erro é -0,4 (valor já dividido por 1000)? |
