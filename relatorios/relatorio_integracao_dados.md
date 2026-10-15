# Relatório — Resultados dos Passos 2, 3 e 4

**Nicolas Soares — 24/09/2026**

Sim, terminei o Passo 4. Nesse processo achei e corrigi um bug real no meu próprio script (não em dado externo), então vou registrar isso também, porque faz parte do diagnóstico.

---

## Passo 2 — Mapeamento dos portais e fontes de dados (confirmado com dado real)

### A. Usina principal (119 kW AC / 140 kWp, marca PHB)
- 425 módulos de 330 Wp, 4 inversores on-grid: INV01 (9035KMTS188W0071), INV02 (9035KMTS188W0070), INV03 (9035KMTS188W0064), INV04 (9014KDTU183W0137).
- Plataforma: **SolarPortal+ / PowerStation** (PHB), estação "Ifes Serra".
- Exportações obtidas: relatório PDF de operação, relatório Excel de operação (5 min), relatório Excel **estatístico (ALL)** — série anual desde 2020.
- Variáveis reais confirmadas na tela *Operating Data* (Inversor 01): AC por fase (V/A/Hz), Potência Ativa/Reativa, 4 canais MPPT, 12 entradas de string PV-1 a PV-12, Chamber Temperature, Total Working Time, campos de Insulation Resistance/Leakage Current (existem na interface, mas vieram "--" no instante capturado — não são "zerados", são "sem leitura naquele momento").

### B. Espaço Energia (3 kWp, inversor KSTAR 5KDM)
- Plataforma: **SolarPortal+/Ksolar**, Plant ID 10071955, Datalogger `I0718330248133`.
- Exportação obtida: telemetria contínua a cada ~5 min (PV1/PV2/PV3 tensão/corrente/potência, Output power, Radiator temperature, Operation mode, Total energy).
- Confirmado fisicamente: só o canal **PV2** está conectado a módulos de verdade (200–330V, até ~7A, pico 1895W no dia observado); PV1 tem tensão residual de barramento (1,4–9,4V, corrente quase nula); PV3 está sempre 0V/0A — desconectado.

### C. MAWS55 (estação meteorológica)
- Acesso via FTP (FileZilla), arquivo bruto tratado pelo Estudante 1 em `dados_meteorologicos_tratados.xlsx`, aba `dados_tratados` com 111.556 linhas, 111 colunas (dado bruto + flags de qualidade + versão `_tratado` de cada variável).
- **Cobertura temporal real confirmada agora**: 15/07/2022 até 31/07/2026. Ou seja, ainda não cobre o dia de hoje (setembro/2026) — isso limita a integração meteorologia×geração pra datas recentes até o Estudante 1 (ou eu) atualizar esse arquivo.

---

## Passo 3 — Diagnóstico e qualidade dos dados (com números reais, não mais hipótese)

1. **Strings desconectadas confirmadas numericamente** — no Inversor 01, PV-2/5/8/11 aparecem com 0,00A enquanto as outras 8 entradas variam entre 0,30A e 2,00A. Confirma o que eu já suspeitava, agora com print real da tela.

2. **Intervalo de amostragem do KSTAR não é exatamente fixo** — a documentação assume 5 em 5 minutos, mas os dados reais mostram variação: a maior parte fica entre 5:04 e 5:06min, só que apareceu um gap real de **19min17s** (entre 14:01:41 e 13:42:24) e um aglomerado de leituras muito próximas (30-40s) perto do nascer do sol (05:34-05:36), provavelmente por causa da transição OFF→STANDBY→NORMAL disparando envios extras. É um exemplo real do tipo de "lacuna temporal" que eu já tinha desenhado em teoria nos Tópicos 1-4 — agora tenho um caso de verdade pra citar.

3. **Achado grande: Inversor 03 ficou 5 anos sem gerar nada.** Os relatórios "estatístico (ALL)" mostram geração 0,0 kWh em INV03 de 2020 a 2024, e só passou a gerar em 2025 (27.795,6 kWh) e 2026 (45.447,4 kWh, ano ainda em curso). Isso é um evento real enorme — ou o inversor ficou desligado/com defeito por 5 anos, ou foi substituído/comissionado tardiamente. É um achado que merece pergunta direta pro pessoal que cuida da usina.

4. **Bug de formatação numérica nos relatórios "estatístico (ALL)"** — os valores vêm como texto tipo `"367.169.80"`, que não é um float válido (dois pontos). Descobri que o padrão é: o **último ponto é sempre o decimal**, os anteriores são separador de milhar (o arquivo original devia ter vírgula decimal e ela virou ponto na exportação, colidindo com o separador de milhar que também é ponto). Escrevi um parser pra isso (`parse_numero_ptbr_ambiguo`) e validei: a soma dos 4 inversores parseados bate com o total da usina (957.870,60 vs 957.869,80 — diferença de 0,8 kWh em 6 anos, arredondamento).

5. **Validação cruzada usina × soma dos inversores**: correlação de **0,99999999** em 22/09/2025 e **0,99999937** em 22/09/2026. Isso é uma validação forte de que a leitura "Potência FV" da usina (nível de planta) bate com a soma dos 4 inversores individuais — não tem inconsistência escondida na agregação.

6. **Pendência a verificar**: o script que eu peguei como base (`integracao_usina_v1_dia_unico.py`) assume potência nominal de 14 kW pro INV04 (os outros três são 35 kW). Não achei essa informação confirmada em nenhum lugar — pode ser um erro de configuração de quem escreveu o script original, ou pode ser real (INV04 é um modelo menor). Preciso confirmar isso antes de usar os percentuais relativos desse inversor em qualquer análise.

---

## Passo 4 — Pipeline generalizada (concluído hoje)

O que eu já tinha (`integracao_usina_v1_dia_unico.py`) funcionava muito bem, mas estava **hardcoded pra um único dia (22/09/2025)**. O que eu fiz:

1. **Generalizei a leitura por data** — a pipeline agora descobre sozinha quais dias têm relatório completo (usina + inversores) na pasta e processa todos automaticamente, em vez de eu editar o código toda vez que quiser rodar outro dia.
2. **No meio do caminho encontrei e corrigi um bug real no meu próprio código**: o padrão de busca de arquivo (`glob`) estava `"...usina(*).xlsx"`, mas os arquivos de verdade têm um sufixo numérico depois do parêntese (`...usina(20250922)_2102821090552160258.xlsx`), então o padrão nunca batia com nada. Corrigi pra `"...usina(*)*.xlsx"`. Foi um bom lembrete de sempre testar contra o nome de arquivo real, não contra o que eu *acho* que o nome é.
3. **Adicionei a leitura dos relatórios "estatístico (ALL)"**, que ainda não tinham sido tocados por nenhum script — foi aí que apareceu o achado do Inversor 03 e o bug do número ambíguo.
4. **Rodei pros dois dias disponíveis** (22/09/2025 e 22/09/2026) e gerei:
   - `integracao_usina_20250922.xlsx` (288 registros de 5min, 288 registros de 15min, 100% com meteorologia)
   - `integracao_usina_20260922.xlsx` (144 registros de 5min, mas só 10 com os 4 inversores completos, e **0 com meteorologia** — porque essa data está fora da cobertura do arquivo tratado, como falei no Passo 3)
   - `historico_anual_inversores.xlsx` (a série 2020-2026 já limpa, por inversor e da usina total)

Resumo numérico do que ficou pronto:

| Data | Registros 5min | Com 4 inversores | Registros 15min | Com meteorologia | Correlação usina×inversores |
|---|---|---|---|---|---|
| 22/09/2025 | 288 | 143 | 288 | 288 (100%) | 0,99999999 |
| 22/09/2026 | 144 | 10 | 144 | 0 (0%) | 0,99999937 |

---

## O que ainda falta (Passo 5 em diante)

- Persistir tudo isso em SQLite (tabelas `leituras_meteorologicas`, `telemetria_inversores`, `historico_alarmes`).
- Atualizar o arquivo meteorológico tratado pra cobrir setembro/2026 (senão qualquer PR calculado pra data recente fica sem irradiância).
- Confirmar a potência nominal real do INV04.
- Perguntar/documentar por que o INV03 ficou 5 anos sem gerar.
- Integrar os dados do KSTAR/Espaço Energia no mesmo pipeline (ainda não tenho um relatório em lote desse sistema, só a telemetria pontual de um dia).
- Dashboard Streamlit + cálculo de PR de verdade, cruzando GHI da MAWS55 com a potência da usina.

Os arquivos gerados (script `integra_usina_meteorologia.py` e as 3 planilhas de saída) estão nos anexos desta conversa.
