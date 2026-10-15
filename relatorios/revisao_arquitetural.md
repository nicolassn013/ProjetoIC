# Revisão Arquitetural e de Processo — Fechamento dos Passos 2-6 e Transição para a Atividade 2

**Nicolas Soares — 25/09/2026**

Esta não é mais uma sessão de "adicionar funcionalidade". É uma parada pra olhar pro que já existe, decidir o que fica, o que muda, e o que só será decidido quando tiver mais informação real. Segui a estrutura pedida (A a H).

---

## A. Diagnóstico do estado atual (o que realmente está pronto)

**Pronto e validado com dado real:**
- Mapeamento de 2 das 3 fontes (usina 119kW/PHB e MAWS55) com portal, formato de exportação e variáveis confirmadas.
- Pipeline (`pipeline/integra_usina_meteorologia.py`) generaliza por data automaticamente, trata o bug de número ambíguo, agrega corretamente em 15min.
- Banco (`leituras.db`) com 4 tabelas, idempotente, 0 duplicatas, validado.
- Camada de consulta (`consultas.py`) e cálculo de PR (`performance_ratio.py`) isolados e testados contra o banco real.
- Achados de diagnóstico reais e documentados: strings desconectadas, INV03 (0 kWh 2020-2024), INV04 (14kW, hipótese forte), cobertura de meteorologia até 31/07/2026.

**Existe como protótipo, não como prioridade:**
- `dashboard.py` — código escrito, sintaxe validada, camada de dados testada isoladamente, mas **nunca rodado de fato** (sem `streamlit`/`plotly` instalados no ambiente onde foi escrito). Concordo com sua decisão: ele fica pausado aqui, não é a prioridade agora.

**Não existe ainda:**
- Qualquer comunicação em tempo real (MQTT, Modbus, ESP32, RPi) — 100% do que foi feito até aqui é leitura de arquivo exportado (relatório da usina, telemetria pontual do KSTAR, planilha da MAWS55). Isso é importante deixar explícito porque o plano de trabalho fala em "comunicação", e o que existe hoje é "integração de arquivo", que é uma coisa diferente.
- Histórico em lote do Espaço Energia/KSTAR.
- Tabela `historico_alarmes`.
- Qualquer confirmação de protocolo físico dos inversores (Modbus? API HTTP? só o portal mesmo?).

## B. Problemas encontrados (dados, pipeline, banco, arquitetura, documentação)

| # | Problema | Onde | Gravidade |
|---|---|---|---|
| 1 | Agregação de 15min não agregava de fato (ficava em 5min) | Passo 4 | Já corrigido |
| 2 | `glob` não batia com o nome real do arquivo (faltava um `*`) | Passo 4 | Já corrigido |
| 3 | Número ambíguo (`"367.169.80"`) nos relatórios estatísticos | Passo 4 | Já corrigido |
| 4 | **Duas superfícies de acesso ao banco**: `carrega_banco.py` escreve via `cursor.execute`/`to_sql` direto; `consultas.py` lê via `pd.read_sql`. Não existe um único lugar que "sabe" o schema inteiro. | Passo 5/6 | **Não corrigido — ver seção C** |
| 5 | `resumo_diario` guarda valores derivados (ex: correlação) que podem ficar desatualizados se `leitura_15min` mudar sem reprocessar aquele dia — é um cache, não dado bruto, e isso não está documentado em lugar nenhum | Passo 5 | Risco baixo hoje (só 2 dias), mas cresce se a base crescer |
| 6 | `dashboard.py` nunca foi executado de verdade | Passo 6 | Aceito como protótipo pausado, não bloqueia o fechamento desta fase |
| 7 | Nenhuma tabela ainda comporta uma segunda fonte de geração (KSTAR) sem forçar colunas específicas em `leitura_15min` | Banco | Ver seção C/7 |

Nenhum desses é grave a ponto de exigir reescrita. O ponto 4 é o único que eu classificaria como "vale corrigir antes de crescer mais", porque é exatamente o tipo de duplicação que gera bug silencioso (alguém muda uma regra em `consultas.py` e esquece de espelhar em `carrega_banco.py`, ou vice-versa).

## C. Proposta de arquitetura revisada (Factory, Strategy, Repository, Observer, Command)

### Repository — **vale aplicar agora, é o único com problema real já existente**

Hoje `consultas.py` já funciona como um Repository de leitura. O que falta é o lado de escrita: `carrega_banco.py` faz `CREATE TABLE`, `DELETE`, `to_sql` diretamente, sem passar por nenhuma camada comum. Isso significa duas fontes de verdade sobre "como o banco é estruturado".

**Proposta concreta e pequena**: unificar em um único módulo (posso chamar de `repositorio.py`, ou simplesmente expandir o `consultas.py` atual pra cobrir também escrita — sem criar uma classe `Repository` genérica e abstrata, que seria over-engineering pra um banco com 4 tabelas). Esse módulo concentra:
- criação de schema (`inicializar_banco`);
- inserção/idempotência (`salvar_dia`, `salvar_historico_anual`);
- todas as consultas que já existem em `consultas.py`.

Ganho real: se um dia a estrutura de uma tabela mudar, muda em um lugar só. Não é sobre deixar o código "mais bonito" — é sobre não ter os dois scripts descrevendo o mesmo schema de jeitos diferentes.

**Não faria** uma classe abstrata `RepositorioBase` com métodos genéricos `get()/save()/delete()` — isso é abstração pra um problema que você não tem (só existe um banco, uma tecnologia, SQLite). Funções simples e nomeadas bastam.

### Strategy — **ainda não vale, mas é a próxima a entrar quando o KSTAR chegar**

Hoje não existe nenhum `if fonte == "PHB": ... elif fonte == "KSTAR": ...` no código — porque só uma fonte elétrica (a usina PHB) está de fato integrada em lote. `ler_relatorio_usina()` e `carregar_meteorologia()` já são funções separadas, chamadas explicitamente, sem nenhum despacho condicional. Introduzir Strategy agora significaria criar uma interface (`ProcessadorFonte.processar()`) com uma única implementação real — abstração sem uso.

**Quando vale**: no dia em que você tiver um relatório em lote do KSTAR e precisar decidir, em tempo de execução, qual função de tratamento aplicar a qual arquivo. Aí sim, duas implementações concretas (`ProcessadorPHB`, `ProcessadorKSTAR`) atrás de uma interface comum evita um `if/elif` que só cresceria. Registro isso como pendência **condicionada** a um evento concreto (chegada do dado do KSTAR em lote), não como tarefa de agora.

### Factory — **depende do Strategy, mesma lógica**

Só faz sentido combinado com o Strategy acima (fábrica que escolhe o processador certo pra cada arquivo). Sem Strategy, não há o que a Factory precisaria "fabricar". Adiar junto.

### Observer — **concordo em não implementar, fica só a leitura de quando fizer sentido**

O sistema é 100% batch hoje (roda script, lê arquivo, grava banco, termina). Observer resolve o problema de "vários componentes precisam reagir a um evento" — isso só existe quando há um fluxo contínuo (dado chegando via MQTT, por exemplo). Implementar agora seria construir infraestrutura de evento pra um sistema que não tem eventos.

### Command — **não vejo necessidade real ainda**

As "operações" hoje (importar meteorologia, importar PHB, popular banco) já são só chamadas de função dentro de scripts sequenciais — não há necessidade de desfazer (`undo`), enfileirar, ou logar comandos como objetos. Encapsular isso em classes `Command` adicionaria uma camada sem resolver nenhum problema que você tenha hoje. Se no futuro você quiser uma CLI com "rodar comando X" escolhido dinamicamente pelo usuário, aí Command volta a fazer sentido — não antes.

### Resumo da decisão de padrões

| Padrão | Decisão agora | Condição para reconsiderar |
|---|---|---|
| Repository | **Aplicar** (unificar leitura+escrita) | — |
| Strategy | Adiar | Chegada de 2ª fonte elétrica em lote (KSTAR) |
| Factory | Adiar (junto com Strategy) | Mesmo gatilho do Strategy |
| Observer | Adiar | Sistema passar a ser event-driven/contínuo |
| Command | Adiar | Necessidade real de desfazer/enfileirar operações |

## D. Plano de refatoração

Só um item concreto, pequeno, com benefício claro:

1. Criar (ou expandir o `consultas.py` existente) pra também cobrir a escrita hoje em `carrega_banco.py` — mover `inicializar_banco`, a lógica de `DELETE`+`INSERT` idempotente, e a gravação do histórico anual pra lá. `carrega_banco.py` passa a ser só um script fino que chama essas funções, igual `dashboard.py` já faz do lado de leitura.

Não tocaria em mais nada — nem em `integra_usina_meteorologia.py` (ele lê arquivo, não banco, então não tem o problema de duas superfícies), nem no schema das tabelas (nenhum problema real aponta pra mudança de schema agora).

## E. Critérios objetivos para considerar o Passo 6 (dashboard) realmente encerrado

Isso fica registrado pra quando você retomar — não é pra fazer agora:

1. `streamlit run dashboard.py` executado numa máquina real, sem erro, com os 3 pacotes instalados de verdade.
2. Testado manualmente: dia com meteorologia completa, dia sem meteorologia, seleção de histórico anual, e o cenário de banco ausente (mensagem amigável, sem crash).
3. Repositório de escrita unificado (item D) já feito, pra o dashboard não herdar a duplicação.
4. Repositório GitHub criado de fato e primeiro `git push` realizado.

## F. Revisão do plano de trabalho oficial

Comparando com "Comunicação entre usina fotovoltaica, estação meteorológica e microrrede inteligente":

- **O que já foi preparatório pro plano (mas não é "comunicação" ainda)**: mapeamento das fontes, pipeline de integração de arquivo, banco de dados, validação de qualidade. Isso é a fundação — não é a atividade-fim do seu plano, é o que faz a Atividade 2 ter chão real pra pisar.
- **O que pertence de fato à Atividade 1 (bibliográfica)**: os relatórios de estudo, o dicionário técnico, a fundamentação teórica — já em andamento, falta só a revisão formal.
- **O que já começa a ser Atividade 2**: o mapeamento real de portais/equipamentos (Passos 2-3) é, na prática, o começo da Atividade 2 ("Mapear e analisar os sistemas de comunicação existentes"), só que feito olhando pro dado exportado, não pro protocolo de rede.
- **Tecnologias do plano ainda não confirmadas fisicamente**: MQTT, Modbus, OPC-UA, HTTP/REST, ESP32, Raspberry Pi — nenhuma delas foi usada de verdade ainda. Tudo que existe até aqui rodou em cima de arquivo exportado do portal, não de comunicação direta com equipamento.
- **SCADA**: na prática, já existe — o PowerStation/SolarPortal+ **são** sistemas SCADA (do fabricante). O que falta não é "criar um SCADA", é decidir como o seu sistema vai buscar dado desse SCADA existente (API? scraping? export agendado?) e/ou se vai instrumentar pontos que o SCADA do fabricante não cobre (ex: Espaço Energia sem meteorologia integrada).

Não estou alterando o plano — só separando com mais precisão o que nele já foi tocado do que ainda é hipótese.

## G. Plano de transição para a Atividade 2 (etapas práticas)

Seguindo a ordem que você mesmo propôs, mas marcando o que já está feito:

1. ~~Identificar quais equipamentos podem ser acessados~~ — feito nos Passos 2-3 (usina, MAWS55; KSTAR parcial).
2. ~~Identificar como cada equipamento fornece dados hoje~~ — feito: usina via export do PowerStation, MAWS55 via FTP, KSTAR via portal (sem lote ainda).
3. **Identificar protocolos/interfaces disponíveis** — **não feito**. Isso é investigação, não código: descobrir se PowerStation/SolarPortal+ têm API oficial, endpoint de exportação agendada, ou se só dá pra baixar manualmente.
4. **Identificar limitações** — parcialmente feito (sabemos que meteorologia não cobre datas recentes, que KSTAR não tem lote); falta confirmar limitação de acesso/API dos portais.
5. **Confirmar presencialmente o que depende de infraestrutura física** — não feito. Depende de conversa com quem administra a usina/rede do campus.
6. Desenhar a arquitetura de comunicação — só depois dos passos 3-5 acima.
7. Definir protocolo por trecho — idem.
8. Primeiro protótipo — só depois de tudo isso.

**Ordem prática recomendada**: passos 3, 4 e 5 primeiro (são investigação/conversa, não implementação), e só então 6-8.

## H. Próximo passo concreto

> **Depois da atualização da planilha, a próxima coisa que Nicolas deve fazer é: descobrir se o PowerStation/SolarPortal+ oferece alguma forma de acesso automatizado aos dados (API oficial, exportação agendada, ou pelo menos um endpoint que dá pra inspecionar via DevTools do navegador) — em vez de escrever qualquer linha de código de MQTT, Modbus ou ESP32.**

Essa é uma tarefa de investigação (perguntar pro suporte da PHB/KSTAR, ou pro responsável do GERA que administra o acesso), não de programação. É o item 3 da seção G, e é o que decide se a Atividade 2 vira "integração via API/webhook" ou "protocolo de campo direto com o equipamento" — duas arquiteturas bem diferentes, e você não deveria escolher uma sem saber qual é possível.

Enquanto isso não é respondido, o único código que eu faria é o item pequeno da seção D (unificar leitura/escrita do banco) — porque isso não depende de nenhuma informação externa, só organiza o que já existe.
