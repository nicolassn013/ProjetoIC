# Monitoramento Integrado — Usina Fotovoltaica IFES Campus Serra

Projeto de Iniciação Científica (PICTI/GERA, IFES Campus Serra) — plano de
trabalho "Comunicação entre usina fotovoltaica, estação meteorológica e
microrrede inteligente" (Estudante 2), construído em cima do tratamento de
dados meteorológicos feito pelo Estudante 1 ("Plataforma Integrada de
Monitoramento de Usina Fotovoltaica").

## 1. O que é

Um pipeline que integra três fontes de dados do campus — usina fotovoltaica
(119 kW AC / 140 kWp), estação meteorológica MAWS55 e (futuramente) o sistema
de microgeração do Espaço Energia (3 kWp, inversor KSTAR) — valida a
qualidade desses dados, persiste tudo num banco SQLite e (como protótipo
pausado) expõe um dashboard Streamlit de monitoramento e diagnóstico.

## 2. Arquitetura

```text
MAWS55 (Estudante 1) ─────────────────────┐
                                           │
Usina FV / Inversores (SolarPortal+) ─────┼──> pipeline/ ──> dados/leituras.db ──> app/
                                           │
KSTAR / Espaço Energia ────────────────────┘   (integração histórica ainda incompleta)
```

## 3. Estrutura de pastas

```text
projeto_ic_usina_fv/
├── README.md
├── requirements.txt
├── .gitignore
├── config.exemplo.env                <- modelo da configuração do FTP (sem segredo). O config.env real NÃO vai ao git
│
├── app/                              <- camada de consulta/apresentação
│   ├── banco.py                      <- conexão com o SQLite (leitura e escrita)
│   ├── consultas.py                  <- Repository: todo o SQL do projeto mora aqui
│   ├── catalogo_meteorologia.py      <- lista das 56 variáveis da MAWS55 (nomes, unidade, flag)
│   ├── migracoes.py                  <- aplica as mudanças de estrutura do banco, uma de cada vez
│   ├── migracoes/                    <- scripts SQL versionados (001 a 004; nunca editar um já aplicado)
│   ├── performance_ratio.py          <- cálculo do PR, isolado e documentado
│   └── dashboard.py                  <- Streamlit (protótipo PAUSADO, nunca executado)
│
├── pipeline/                         <- scripts de integração (ETL)
│   ├── integra_usina_meteorologia.py <- relatórios brutos + meteorologia -> dados/processados/
│   ├── carrega_banco.py              <- dados/processados/ -> dados/leituras.db
│   ├── aquisicao_maws55.py           <- linha de comando: FTP (ou pasta) da estação -> banco
│   ├── aquisicao/                    <- config, fontes (FTP/pasta), leitor, tratamento, ingestão
│   └── legado/
│       └── integracao_usina_v1_dia_unico.py  <- versão original (1 dia fixo). Só histórico:
│                                                não ajustada à estrutura atual, não executar.
│
├── dados/
│   ├── leituras.db                   <- banco final (pequeno, versionado; versão 4 da estrutura)
│   ├── backups/                      <- cópia automática antes de migrar um banco que já tinha dados (não versionada)
│   ├── processados/                  <- saídas do pipeline (versionadas)
│   │   ├── integracao_usina_YYYYMMDD.xlsx
│   │   └── historico_anual_inversores.xlsx
│   ├── brutos/
│   │   └── usina_powerstation/       <- relatórios exportados do PowerStation/SolarPortal+
│   │                                    (mantêm o nome original do portal de propósito:
│   │                                     o pipeline procura a data no nome do arquivo)
│   └── estudante1_meteorologia/      <- espaço do Estudante 1: só leitura, nunca editar
│       ├── scripts/
│       └── brutos/                   <- dados_meteorologicos_tratados.xlsx (~44 MB, NÃO versionado)
│
├── testes/
│   ├── test_banco.py                 <- 29 testes: migrações, meteorologia_15min, view, diário
│   └── test_aquisicao.py             <- 47 testes: leitor, tratamento, FTP simulado, ingestão, linha de comando
│
└── relatorios/                       <- documentação: dicionários, aquisição, padrões de projeto, banco, planilha
```

**Por que essa divisão:** `app/` (leitura) e `pipeline/` (ETL) têm ciclos de vida diferentes: abrir o
dashboard não deveria exigir reprocessar dado, e vice-versa. A pasta `estudante1_meteorologia/` isola
o que é do Estudante 1: eu só leio o arquivo tratado de lá.

## 4. Fontes de dados

| Fonte | O que fornece | Status |
|---|---|---|
| MAWS55 (SEAMA-ES) | Irradiância, temperatura, umidade, vento, chuva — 15 min | Tratada pelo Estudante 1, cobre 15/07/2022 a 31/07/2026 |
| Usina 119 kW AC / 140 kWp (PHB) | Potência, energia, MPPT, alarmes — ~5 min | Relatórios diários + histórico anual (2020-2026) já integrados |
| Espaço Energia (KSTAR 5KDM, 3 kWp) | Potência, energia por string | Só telemetria pontual inspecionada; sem histórico em lote ainda |

## 5. Como instalar e executar

```bash
pip install -r requirements.txt

# (re)gerar os dados a partir dos relatórios brutos
python pipeline/integra_usina_meteorologia.py
python pipeline/carrega_banco.py

# testes do banco (usam banco temporário; não tocam em dados/leituras.db)
python -m unittest discover -s testes -v

# aquisição direta da estação (precisa de config.env; veja relatorios/aquisicao_maws55.md)
python pipeline/aquisicao_maws55.py --simular     # lê e trata, não grava
python pipeline/aquisicao_maws55.py               # grava os 8 arquivos mais recentes

# abrir o dashboard (protótipo pausado, não é a prioridade atual)
streamlit run app/dashboard.py
```

O `dados/leituras.db` já vem pronto no repositório (é pequeno, ~100 KB) —
na maioria das vezes basta rodar os dois scripts do pipeline se quiser
reprocessar, ou nem isso se só for consultar o banco existente.

### Estrutura do banco (versão 4)

| Tabela / view | O que guarda |
|---|---|
| `leitura_15min` | Usina e inversores (uma linha por 15 min). As 5 colunas meteorológicas antigas são **legado** |
| `meteorologia_15min` | **As 56 variáveis da MAWS55** + 24 flags de qualidade: fonte de verdade da meteorologia (ver `relatorios/dicionario_meteorologia.md`) |
| `vw_leitura_completa` | Junção das duas anteriores; é por ela que o PR e o dashboard leem |
| `ingestao_arquivos` | Diário dos arquivos baixados do FTP ou de pasta (nome, hash, status, erro) |
| `resumo_diario` | Contagens e indicadores por dia |
| `historico_anual_inversores`, `historico_anual_usina` | Geração anual 2020-2026 (recriadas a cada carga) |

Mudança de estrutura **só por migração** (`app/migracoes/NNN_nome.sql`); nunca editar o `.db` à mão.

## 6. Tecnologias

Python, Pandas, NumPy, SQLite, Streamlit, Plotly, openpyxl.

## 7. Limitações conhecidas (documentadas, não escondidas)

- **INV03**: geração 0 kWh entre 2020–2024. Causa não determinada pelos
  dados — a confirmar com quem opera a usina.
- **INV04**: potência nominal de 14 kW usada por hipótese forte
  (35+35+35+14 = 119 kW bate com o total da usina), sem confirmação
  documental definitiva.
- **Meteorologia**: o arquivo tratado só cobre até 31/07/2026. Em `meteorologia_15min` hoje há só o dia
  22/09/2025 (exemplo); 32 das 56 variáveis estão como **dado bruto**, sem tratamento nem flag, e as
  unidades são inferidas (ver `relatorios/dicionario_meteorologia.md`).
- **Aquisição pelo FTP**: o leitor assume um formato de .txt que **ainda não foi confirmado com um
  arquivo real** e o FTP nunca foi testado contra o servidor (só contra um simulado). Ver
  `relatorios/aquisicao_maws55.md`, seção 4. O pipeline e o dashboard tratam
  isso explicitamente (aviso, sem inventar dado).
- **Espaço Energia (KSTAR)**: sem histórico em lote integrado ao banco
  ainda — só telemetria pontual foi inspecionada.
- **Comunicação**: tudo que existe hoje é integração de **arquivo
  exportado** das plataformas (PowerStation/SolarPortal+), não comunicação
  em tempo real (MQTT/Modbus/ESP32) — isso é investigação em andamento da
  Atividade 2, não uma decisão de arquitetura ainda tomada. Ver
  `relatorios/investigacao_comunicacao_atividade2.md`.
- **Intervalo de amostragem**: os relatórios de 22/09/2025 têm amostras de 5 em 5 min e os de
  22/09/2026 de 10 em 10 min. O campo `registros_eletricos_5min` do resumo conta *amostras*, não
  "5 minutos" (nome mantido para não quebrar o banco); o pipeline avisa quando o intervalo não é 5.
- **Dashboard**: prototipado, nunca executado de fato (`streamlit run`) —
  ver critérios de fechamento em
  `relatorios/revisao_arquitetural.md`.
- **Padrões de projeto**: Repository, Strategy (fontes de arquivo), regras orientadas por dados e
  migrações versionadas foram aplicados; Factory formal, Observer, Command e Singleton foram
  adiados com gatilho definido. Ver `relatorios/padroes_de_projeto.md`.

## 8. Próximos passos

1. Rodar a aquisição no campus (`--simular`) com os arquivos mais recentes do FTP: o formato de 52 valores foi confirmado com arquivos reais de 2022, o de 56 valores ainda não. Avisar o Estudante 1 do deslocamento de colunas no trecho de 15/07 a 22/08/2022 (`relatorios/aquisicao_maws55.md`, seção 4.2).
2. Investigar comunicação real com PHB/KSTAR (API? scraping? só manual
   mesmo?) — ver `relatorios/investigacao_comunicacao_atividade2.md`.
3. Levar as perguntas técnicas objetivas pro responsável do IFES (mesmo
   relatório, seção D).
4. Só depois disso, desenhar a arquitetura de comunicação da Atividade 2.
5. Rodar `streamlit run app/dashboard.py` de verdade numa máquina com
   internet e validar visualmente (protótipo pausado até lá).
6. Integrar histórico em lote do Espaço Energia/KSTAR quando disponível.

## 9. Publicar no GitHub

```bash
git init
git add .
git commit -m "Pipeline de integração usina + meteorologia, banco SQLite e documentação"
git branch -M main
git remote add origin <URL_DO_SEU_REPOSITORIO_AQUI>
git push -u origin main
```

## 10. Duas versões do projeto

Existem duas pastas com o **mesmo código executável**: `projeto_ic_usina_fv_limpo/` (a que vai para o GitHub)
e `projeto_ic_usina_fv_comentado/` (cada função explicada passo a passo, só para estudo). A única
diferença entre elas são comentários e docstrings; foi conferido por comparação da estrutura do código.
Quando mudar o código, mude primeiro a versão limpa e depois regenere a comentada.
