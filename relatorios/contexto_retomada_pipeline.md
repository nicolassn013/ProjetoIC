# Contexto do Projeto — da Proposta de Diferenciação (Estudante 2) até o Passo 4

Use este documento como "prompt de retomada": cole isso no início de uma nova conversa (com qualquer IA, ou pra você mesmo reler antes de continuar) pra recuperar o contexto completo sem precisar re-explicar tudo.

---

## 1. Quem é quem

- **Projeto**: PICTI/GERA, IFES Campus Serra — "Ações de Eficiência Energética associadas ao uso de Fontes Alternativas". Bolsa 2026-2027.
- **Eu (Nicolas Soares, Estudante 2)**: plano de trabalho oficial = "Comunicação entre usina fotovoltaica, estação meteorológica e microrrede inteligente".
- **Estudante 1 (colega)**: plano de trabalho = "Plataforma Integrada de Monitoramento de Usina Fotovoltaica". Já entregou: aquisição/limpeza da série meteorológica da MAWS55, com regras de qualidade (min/média/máx, flags, deduplicação, lacunas) e export em Excel multi-aba (`dados_meteorologicos_tratados.xlsx`).
- **Infraestrutura real do campus**: usina de 119 kW AC / 140 kWp (marca PHB, 4 inversores, plataforma SolarPortal+/PowerStation) + Espaço Energia de 3 kWp (inversor KSTAR 5KDM, mesma plataforma) + estação meteorológica MAWS55 (SEAMA-ES, acesso via FTP).

## 2. A proposta de diferenciação (ponto de partida)

Depois de ver o que o Estudante 1 já tinha feito (limpeza em **lote**, de **uma fonte só**, num Excel estático), a proposta foi: eu construo a camada de cima — **tempo real/contínuo + múltiplas fontes (usina × meteorologia × microrrede) + diagnóstico automático (índice de confiabilidade, correlação, detecção de deriva/evento)** — reaproveitando o dado já limpo do Estudante 1 como entrada, em vez de recomeçar do zero. Isso é, na prática, uma implementação concreta do meu próprio plano de trabalho oficial.

## 3. Mapeamento real da infraestrutura (Passo 2)

Confirmado com prints e exports reais das plataformas (não mais hipótese de literatura):

- **Usina 119kW/PHB**: SolarPortal+/PowerStation, estação "Ifes Serra". Exporta relatório PDF/Excel de operação (5 min), e relatório "estatístico (ALL)" com série anual desde 2020. Cada inversor expõe AC (V/A/Hz por fase), MPPT (4 canais), 12 strings PV-1 a PV-12, temperatura da câmara, tempo de operação, histórico de alarmes reais (falha de isolação no INV04, quedas de rede recuperadas nos INV01-03).
- **Espaço Energia/KSTAR**: mesma plataforma, telemetria a cada ~5min, só o canal PV2 fisicamente conectado.
- **MAWS55**: acesso via FTP, tratado pelo Estudante 1, cobre 15/07/2022 a 31/07/2026 (111 colunas, com flags de qualidade e versões `_tratado`).

## 4. Diagnóstico de qualidade (Passo 3)

- Strings desconectadas confirmadas numericamente (PV-2/5/8/11 do INV01 sempre em 0,00A).
- Amostragem do KSTAR não é rigorosamente fixa (achei um gap real de ~19min e um aglomerado de leituras a cada 30-40s no nascer do sol).
- **Achado grande**: Inversor 03 gerou 0,0 kWh de 2020 a 2024 (5 anos!) e só passou a gerar em 2025 — precisa ser investigado/confirmado com quem opera a usina.
- **Bug de formatação real**: os relatórios "estatístico (ALL)" trazem números tipo `"367.169.80"` (dois pontos, ambíguo). Regra resolvida: o último ponto é sempre o decimal, os anteriores são separador de milhar. Validado batendo a soma dos 4 inversores contra o total da usina.
- Validação cruzada usina × soma dos inversores: correlação de 0,99999999 (22/09/2025) e 0,99999937 (22/09/2026) — forte indício de que não há inconsistência na agregação de dado entre nível-planta e nível-inversor.
- Pendência: potência nominal do INV04 usada no script (14 kW, vs. 35 kW dos outros três) não está confirmada em nenhuma fonte oficial.

## 5. Pipeline de integração (Passo 4 — concluído)

Existia um script (`integracao_usina_v1_dia_unico.py`) já bem escrito, mas fixo pra um único dia (22/09/2025). O que fiz:

1. Generalizei pra descobrir sozinho quais dias têm relatório completo disponível e processar todos automaticamente.
2. Corrigi um bug de `glob` no meu próprio código (padrão de busca de arquivo não considerava o sufixo numérico depois da data no nome do arquivo real).
3. Adicionei a leitura dos relatórios "estatístico (ALL)" (não tocados antes), com o parser do número ambíguo.
4. Rodei pra 22/09/2025 e 22/09/2026, gerando 3 arquivos de saída: `integracao_usina_20250922.xlsx`, `integracao_usina_20260922.xlsx`, `historico_anual_inversores.xlsx`.

Resultado: pipeline reproduzível, e não mais um script de "um dia só" — qualquer novo relatório exportado da plataforma já cai automaticamente na próxima rodada.

## 6. O que falta (próximos passos, em ordem)

1. **Passo 5** — persistir tudo em SQLite (`leituras_meteorologicas`, `telemetria_inversores`, `historico_alarmes`), reaproveitando o padrão Repository que já vinha do EB-70.
2. Atualizar/estender o arquivo meteorológico tratado pra cobrir setembro/2026 em diante (hoje ele para em 31/07/2026).
3. Confirmar a potência nominal real do INV04 e investigar/documentar a lacuna de 5 anos do INV03.
4. Conseguir um relatório em lote (não só pontual) da telemetria do KSTAR/Espaço Energia pra integrar no mesmo pipeline.
5. **Passo 6** — dashboard Streamlit + cálculo de Performance Ratio de verdade, cruzando GHI da MAWS55 com a potência da usina, usando o dado já validado no Passo 4.

## 7. Arquivos que existem hoje (estado do projeto)

```
Projeto_IC/
├── tratamento_de_dados_meteorologicos.py      (Estudante 1)
├── analise_dados_meteorologicos.py
├── integracao_usina.py                        (script original, 1 dia fixo)
├── integra_usina_meteorologia.py                         (generalizado, Passo 4 — novo)
└── dados/
    ├── dados_meteorologicos.xlsx               (bruto, Estudante 1)
    ├── dados_meteorologicos_tratados.xlsx       (tratado, Estudante 1, cobre até 31/07/2026)
    ├── analise_meteorologicos.xlsx
    ├── integracao_usina_20250922.xlsx           (Passo 4)
    ├── integracao_usina_20260922.xlsx           (Passo 4)
    ├── historico_anual_inversores.xlsx          (Passo 4, novo)
    └── usina_powerstation/
        ├── Relatório de operação da usina(20250922)*.xlsx
        ├── Relatório de operação da usina(20260922)*.xlsx
        ├── Relatório de operação do inversor(20250922)*.xlsx
        ├── Relatório de operação do inversor(20260922)*.xlsx
        ├── Relatório estatístico da usina(ALL)*.xlsx
        └── Relatório estatístico do inversor(ALL)*.xlsx
```
