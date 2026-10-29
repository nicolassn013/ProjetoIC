# Relatório — Passo 5 concluído (e um bug a mais encontrado no caminho)

**Nicolas Soares — 24/09/2026**

Rodei o `carrega_banco.py` que o ChatGPT desenhou. Antes de rodar de verdade contra os meus arquivos, achei mais um bug — dessa vez na minha própria pipeline do Passo 4, não no script do Passo 5.

## O bug que achei antes de conseguir rodar o Passo 5

A aba `integracao_15min` que eu gerei no Passo 4 **não estava realmente agregada em 15 minutos** — continuava em 5 em 5 minutos (288 linhas por dia, quando o certo seria 96). Eu só tinha colado um rótulo `timestamp_15min` nas linhas de 5min e cruzado com a meteorologia, sem de fato agrupar/agregar. Isso não dava erro nenhum sozinho, mas quebrou na hora de inserir no banco: como o script do Passo 5 usa `timestamp_15min` como chave primária, ele tentou inserir 3 linhas com o mesmo timestamp (as três amostras de 5min que caem no mesmo bucket de 15min) e o SQLite recusou (`UNIQUE constraint failed`).

Corrigi agrupando (`groupby + mean`) o elétrico em 15 minutos **antes** de cruzar com a meteorologia. Resultado depois da correção: 96 registros de 15min por dia (24h × 4), como devia ser desde o início.

Moral: o erro só apareceu porque o Passo 5 impôs uma restrição (chave primária única) que expôs uma agregação que eu achava que já tinha feito e não tinha. Bom exemplo de por que vale a pena ter a camada de banco com constraint de verdade, não só planilha solta.

## Resposta ao feedback do ChatGPT e do Gemini

- **INV03 (0 kWh por 5 anos)**: concordo que precisa de destaque visual no dashboard — vou tratar como alerta, não como nota de rodapé.
- **Cobertura meteorológica até 31/07/2026**: a estratégia de aviso amigável + omitir o PR nesse período faz sentido; não vou tentar "inventar" meteorologia pra data sem cobertura.
- **Potência nominal do INV04 (14 kW)**: o Gemini trouxe um argumento bom que eu não tinha reparado — **35+35+35+14 = 119 kW**, que é exatamente a potência AC total da usina. Isso não é prova definitiva, mas é uma evidência numérica forte a favor de manter os 14 kW (além do prefixo de série do INV04 ser diferente dos outros três: `9014...` vs `9035...`, sugerindo modelo diferente mesmo). Vou considerar essa pendência como **resolvida-com-ressalva**: uso 14 kW, mas registro que a confirmação final ainda depende de ver a especificação oficial do equipamento.

## O que ficou pronto (Passo 5)

- `leituras.db` criado com 4 tabelas: `leitura_15min` (192 linhas, 2 dias), `resumo_diario` (2 linhas), `historico_anual_inversores` (4 linhas), `historico_anual_usina` (1 linha).
- Testei idempotência rodando o script duas vezes seguidas — mesma contagem de linhas nas duas, sem duplicar.
- Validação de sanidade: 0 timestamps duplicados em `leitura_15min`, dados batendo com o que o Passo 4 gerou (correlação usina×inversores, máximos por inversor, etc.).

## Nomenclatura (nota sobre a sugestão do Gemini)

O Gemini sugeriu chamar a tabela histórica de `historico_geracao_anual` (uma tabela só). Eu mantive como o ChatGPT desenhou — duas tabelas separadas, `historico_anual_inversores` e `historico_anual_usina` — porque é exatamente assim que o meu `historico_anual_inversores.xlsx` do Passo 4 já está estruturado (duas abas: `por_inversor` e `usina_total`), então não precisei reformatar nada pra encaixar. Não é uma escolha melhor ou pior, só a que exigia menos fricção com o que eu já tinha pronto.

## Próximo passo: Passo 6 (dashboard)

Banco pronto e validado. Agora dá pra montar o Streamlit em cima do `leituras.db` direto (sem precisar reabrir Excel), com:
- gráfico de potência 15min (usina + por inversor) puxando de `leitura_15min`;
- KPI de correlação e cobertura de meteorologia puxando de `resumo_diario`;
- gráfico de barras histórico 2020-2026 puxando de `historico_anual_inversores`/`historico_anual_usina`, com destaque visual pro buraco do INV03.

Arquivos em anexo: `integra_usina_meteorologia.py` (corrigido), `carrega_banco.py`, e o `leituras.db` já populado.


---

## Atualização de 21/10/2026 — estrutura versão 2 (meteorologia completa)

**Acrescentado**
- Tabela `meteorologia_15min` (78 colunas: 51 valores, 24 flags, 3 de apoio) e a view `vw_leitura_completa`.
- `app/catalogo_meteorologia.py` (56 variáveis), `app/migracoes.py` e `app/migracoes/001_base.sql`, `002_meteorologia_15min.sql`.
- Funções em `consultas.py`: `salvar_meteorologia`, `meteorologia_15min_do_dia`, `leitura_completa_do_dia`, `cobertura_meteorologia`, `verificar_schema_meteorologia`.
- Aba `meteorologia_15min` nos arquivos `integracao_usina_YYYYMMDD.xlsx` e `carregar_meteorologia_completa` no pipeline.
- `testes/test_banco.py` (21 testes) e `relatorios/dicionario_meteorologia.md`.

**Substituído**
- `inicializar_schema`: antes tinha `CREATE TABLE` dentro do código; agora aplica as migrações.
- `salvar_dia`: passa a devolver `{linhas_antes, linhas_depois}`; `carrega_banco.py` avisa quando um dia fica com menos linhas.
- `dados/leituras.db`: agora na versão 2; os mesmos 2 dias de exemplo e 96 linhas de meteorologia completa de 22/09/2025.

**Retirado**
- Os `CREATE TABLE` de `consultas.py` (movidos, sem mudar, para `001_base.sql`).

**Conferido** (cópia isolada, banco antigo migrado com backup): `leitura_15min` igual ao banco anterior (tolerância 1e-9), PR de 22/09/2025 = 0,831, 96 linhas de meteorologia que batem coluna a coluna com o xlsx tratado, 2 cargas seguidas sem duplicar, `integrity_check` ok. O dashboard **não** foi executado (Streamlit não instalado aqui).


---

## Atualização de 23/10/2026 — estrutura versão 4 (consolidação e aquisição)

**Acrescentado**
- Migração `003_meteorologia_valores_legados.sql`: as 5 variáveis antigas ganham coluna em `meteorologia_15min` (que passa a ter as 56) e a view `vw_leitura_completa` é recriada, preferindo o valor de `meteorologia_15min` e caindo para a cópia legada de `leitura_15min`.
- Migração `004_ingestao_arquivos.sql`: diário dos arquivos baixados (nome, hash, status, linhas, erro).
- `salvar_meteorologia(modo="mesclar")`, `ingestao_ja_feita`, `registrar_ingestao`, `ultimas_ingestoes` em `consultas.py`.
- Módulo `pipeline/aquisicao/` (config, fontes FTP/pasta, leitor, tratamento, ingestão) e `pipeline/aquisicao_maws55.py`.
- `config.exemplo.env`, `relatorios/aquisicao_maws55.md`, `relatorios/padroes_de_projeto.md`, `testes/test_aquisicao.py` (47 testes).

**Substituído**
- `leitura_15min_do_dia` e `cobertura_geral` passam a ler pela view (mesmas colunas e mesmos números de antes).
- Catálogo: as 5 variáveis antigas passam a viver em `meteorologia_15min` (56 valores, 24 flags, 83 colunas).
- `dados/leituras.db`: versão 4.

**Retirado**
- Nada. `001` e `002` não foram alteradas (conferido byte a byte com o que foi entregue ao Estudante 1).

**Conferido** (cópia isolada, banco versão 2 migrado para 4 com backup)
- `leitura_15min` e `leitura_15min_do_dia` iguais ao banco original (tolerância 1e-9); PR de 22/09/2025 = 0,831; `cobertura_geral` igual (96 de 192 com meteorologia).
- Regras de tratamento da aquisição **idênticas** às do Estudante 1 nas 111.555 linhas do arquivo tratado (56 valores e 24 flags).
- Um dia (96 linhas) reconstruído como 96 arquivos .txt sintéticos e ingerido do zero: banco **igual** ao do pipeline atual em todas as colunas (exceto `lacuna_temporal`, que fica vazia na aquisição).
- 76 testes passando (3 só rodam com o arquivo tratado do Estudante 1 presente); `integrity_check` ok.
- **Formato real do .txt confirmado (24/10/2026)** com 2 arquivos do FTP: sem cabeçalho, vírgulas, horário em UTC, 52 ou 56 valores por linha. Leitor reescrito para isso. Achado: no xlsx tratado do Estudante 1, as 3.653 linhas de 15/07 a 22/08/2022 têm nomes de colunas deslocados (detalhes em `aquisicao_maws55.md`, seção 4.2).

**Não conferido:** formato real do .txt do FTP, o FTP real e o dashboard.
