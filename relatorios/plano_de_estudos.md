# Plano de Estudos — Entender de Verdade o que Foi Construído (Passos 2 a 6)

**Objetivo:** você conseguir explicar, sem mim do lado, o que cada arquivo faz, por que ele é assim, e onde mexer se precisar mudar algo. Não é decorar código: é entender a lógica o suficiente pra defender isso numa banca ou continuar sozinho.

Formato: cada bloco tem **o que ler**, **o que rodar/mexer** (aprender fazendo, não só lendo) e **perguntas de autoavaliação** (se você não conseguir responder, ainda não entendeu: volta e revê).

Ordem sugerida: a ordem em que o dado realmente flui pelo sistema (fonte → pipeline → banco → consulta/análise → planilha de acompanhamento).

**Onde está cada arquivo (estrutura reorganizada):**

```text
projeto_ic_usina_fv/
├── app/        banco.py, consultas.py, performance_ratio.py, dashboard.py
├── pipeline/   integra_usina_meteorologia.py, carrega_banco.py, legado/integracao_usina_v1_dia_unico.py
├── dados/      leituras.db, processados/, brutos/usina_powerstation/, estudante1_meteorologia/
└── relatorios/ relatórios .md, dicionário técnico e a planilha de acompanhamento
```

---

## Bloco 0 — Pré-requisitos de Python/Pandas (se algo aqui for novidade, comece por aqui)

Antes de ler os scripts, confirme que você está confortável com:

| Conceito | Onde aparece no seu projeto | Se não souber, estude |
|---|---|---|
| `pandas.DataFrame`, seleção de colunas/linhas | Todo lugar | Pandas: indexação básica (`.loc`, `.iloc`, seleção por coluna) |
| `groupby(...).mean()` / `.agg()` | `integra_usina_meteorologia.py`, correção do bug de 15min | Pandas: agregação (`groupby`) |
| `merge()` (inner/left join) | `preparar_dados_eletricos`, `integrar_15min` | Pandas: `merge` (é igual JOIN de SQL) |
| `resample()` / `.dt.floor()` | `integrar_15min` | Séries temporais em Pandas |
| `regex` (`re.search`) | `extrair_data_relatorio`, `extrair_inversor`, `parse_numero_ptbr_ambiguo` | Módulo `re` do Python: só o básico (`search`, grupos `(...)`) |
| `glob.glob()` | `encontrar_datas_disponiveis` | Módulo `glob`: casar nome de arquivo com padrão |
| `sqlite3` + `pandas.to_sql`/`read_sql` | `banco.py`, `consultas.py` | SQL básico: `SELECT`, `WHERE`, `GROUP BY`, `CREATE TABLE`, chave primária |
| `contextmanager` (`with ... as`) | `banco.conectar()` | Gerenciadores de contexto do Python: por que usamos `with` |

**Exercício rápido:** abra um terminal Python e, usando só um DataFrame pequeno que você mesmo cria (5 linhas), pratique um `groupby().mean()` e um `merge()`. Se isso já é natural, pule pro Bloco 1.

---

## Bloco 1 — Passos 2 e 3 (mapeamento e diagnóstico): revisão conceitual

Aqui não tem código pra rodar: é reler seus próprios relatórios, mas agora prestando atenção em COMO cada achado virou uma decisão de código depois.

**O que reler:**
- `relatorios/Relatorio_Passos_2_3_4.md`
- Prints/PDFs reais das plataformas (PowerStation, SolarPortal+)

**Perguntas de autoavaliação:**
1. Por que as colunas PV-2, PV-5, PV-8, PV-11 do INV01 aparecem sempre com 0,00A? Isso é erro de leitura ou característica física?
2. O que exatamente significa a estação MAWS55 "cobrir até 31/07/2026"? O que acontece se eu pedir dado de uma data depois disso?
3. Por que a correlação usina × soma dos inversores é uma validação, e não só uma curiosidade estatística? O que ela prova (e o que ela NÃO prova)?

Se você não consegue responder essas 3 de cabeça, volte no relatório antes de seguir.

---

## Bloco 2 — `pipeline/integra_usina_meteorologia.py` (o coração da integração)

Esse é o arquivo mais importante pra entender bem, porque é onde a maior parte das decisões de tratamento de dado vive. Leia na ordem das funções (é a ordem lógica do fluxo, não a ordem alfabética):

1. **`extrair_data_relatorio(valor)` e `conferir_data_no_arquivo(...)`**: o fluxo pega a data do NOME do arquivo (`YYYYMMDD`), e estas duas funções conferem se a data escrita DENTRO do relatório é a mesma. Pergunta: por que vale conferir as duas, em vez de confiar só no nome do arquivo? (dica: o que acontece se alguém renomear um relatório de outro dia?)
2. **`criar_timestamps(data, horarios)`**: junta a data (do passo 1) com cada horário da tabela, virando um timestamp completo. Pergunta: o que acontece se um horário vier corrompido/ilegível? (veja o `try/except` e o `pd.NaT`)
3. **`encontrar_datas_disponiveis()`**: usa regex + `glob` pra descobrir sozinho quais dias têm os dois relatórios (usina E inversor) juntos. Pergunta: por que ele exige os DOIS arquivos (`datas_usina & datas_inversor`, interseção), e não só um?
4. **`ler_relatorio_usina` / `ler_relatorio_inversores`**: leem a planilha bruta linha por linha procurando o indicador certo ("Potência FV(kW)", "Potência ativa(kW)"). Pergunta: por que o código escolhe a linha com MAIS valores não-nulos (`maior_quantidade`), em vez da primeira linha que encontrar?
5. **`preparar_dados_eletricos`**: aqui nasce a validação: soma dos 4 inversores vs. potência da usina. Pergunta: por que a soma só é calculada quando os 4 inversores têm dado ao mesmo tempo (`mascara_completa`)? O que estragaria se somasse mesmo com um inversor faltando?
6. **`carregar_meteorologia`**: filtra só o dia pedido dentro do arquivo gigante do Estudante 1. Pergunta: o que acontece se o dia pedido não existir na meteorologia (teste você mesmo: rode pra uma data de 2027)?
7. **`integrar_15min`**: **este é o trecho onde o bug de agregação aconteceu**. Leia com atenção o `groupby("timestamp_15min")[colunas_numericas].mean()`. Pergunta: sem esse `groupby`, quantas linhas por timestamp você teria (dica: quantas amostras de 5min cabem em 15min)?
8. **`parse_numero_ptbr_ambiguo`**: a função que resolve o `"367.169.80"`. Pergunta: por que `"".join(partes[:-1])` e não simplesmente pegar `partes[0]`? (dica: e se o número tivesse 3 pontos, tipo milhões?)

**Exercício prático (recomendado):** rode o script (`python pipeline/integra_usina_meteorologia.py`) e, antes de cada `print`, tente adivinhar o número que vai aparecer. Errar e descobrir por quê é o jeito mais rápido de fixar isso.

**Exercício de quebra proposital:** faça uma cópia de segurança do arquivo, comente a linha do `groupby` em `integrar_15min` (faça o merge direto sem agregar) e rode de novo. Veja o erro que aparece quando tentar inserir no banco: é literalmente o bug real que apareceu no Passo 5. Depois restaure o original.

---

## Bloco 3 — `app/banco.py` + `app/consultas.py` (a camada de dados / Repository)

1. **`banco.py`**: só duas funções. Leia por que existem DUAS formas de conectar (`conectar()` vs `conectar_ou_criar()`). Pergunta: por que o dashboard nunca deveria usar `conectar_ou_criar()`?
2. **`consultas.py`, parte de escrita**: `inicializar_schema`, `salvar_dia`, `salvar_historico_anual`. Pergunta: por que `salvar_dia` faz um `DELETE` antes do `INSERT`? O que aconteceria se você rodasse o pipeline duas vezes sem esse `DELETE`?
3. **`consultas.py`, parte de leitura**: `datas_disponiveis`, `leitura_15min_do_dia`, `cobertura_geral`. Pergunta: em `cobertura_geral`, por que cada contagem é uma query SQL separada (`SELECT COUNT(*)...`) em vez de trazer tudo com `SELECT *` e contar em Python com Pandas depois?

**Exercício prático:** abra um terminal Python dentro da pasta `app/` e rode manualmente:
```python
import banco, consultas
with banco.conectar() as conn:
    print(consultas.cobertura_geral(conn))
```
Depois, tente escrever você mesmo uma nova função em `consultas.py` que devolva, por exemplo, "o dia com a maior potência máxima registrada". Isso força você a mexer no arquivo real, não só ler.

---

## Bloco 4 — `pipeline/carrega_banco.py` (o orquestrador)

Depois do Bloco 3, este arquivo deve parecer quase óbvio: ele só chama as funções de `consultas.py` na ordem certa. Se ainda parecer confuso, é sinal de que o Bloco 3 não fixou.

Pergunta: por que esse arquivo praticamente não tem lógica própria (SQL, regras de negócio)? Isso é bom ou ruim, e por quê?

---

## Bloco 5 — `app/performance_ratio.py` (a parte com mais física/engenharia, menos programação)

Esse arquivo é pequeno, mas exige entender a fórmula, não só o código:

- Releia o comentário no topo do arquivo (a fórmula do IEC 61724).
- Pergunta: por que `pr_calculavel()` exige que **100%** dos registros do dia tenham GHI, em vez de calcular com o que tiver disponível?
- Pergunta: por que a potência nominal usada é 140 kWp (DC) e não 119 kW (AC)? O que isso mudaria no resultado se você trocasse um pelo outro?

**Exercício prático:** calcule o PR manualmente (numa calculadora ou planilha) usando 2-3 linhas de dado real do dia 22/09/2025 (pegue de `dados/processados/integracao_usina_20250922.xlsx`) e confira se bate, na ordem de grandeza, com o que o código calculou (0,831).

---

## Bloco 6 — `app/dashboard.py` (ler mesmo sem rodar)

Como o Streamlit não pôde ser executado no ambiente onde foi escrito, este bloco é só leitura + imaginação de como ficaria na tela. O dashboard está pausado como protótipo, então aqui o objetivo é entender, não evoluir.

- Percorra as 7 seções (`if pagina == ...`) uma por uma.
- Pergunta: por que `carregar_dados()` e `carregar_dia()` têm `@st.cache_data`? O que aconteceria (em termos de performance) sem esse decorador, toda vez que você trocasse de página no menu lateral?

**Exercício (quando tiver `pip install streamlit plotly` numa máquina com internet):** rode `streamlit run app/dashboard.py` de verdade e clique em cada seção. Anote qualquer coisa que quebrar: isso vira uma lista de bugs reais pra corrigir, igual aconteceu no Passo 4/5.

---

## Bloco 7 — A planilha `Organizacao_Projeto_PICTI.xlsx`

Diferente do código, aqui o objetivo é entender a ESTRUTURA, não a lógica de programação:

- Abra a aba **Cronograma Geral**: entenda a fórmula da coluna de progresso (H): ela lê o texto da coluna de status (G) e converte em número. Pergunta: por que "Em andamento" vale 0,5 e não, por exemplo, 0,3 ou 0,7? (não tem resposta certa: é uma convenção que vocês definiram; o importante é você saber que É uma convenção, não uma medição exata)
- Abra a aba **Atividade 1 - Detalhamento**: veja como o progresso dessa aba (F14) se relaciona com a linha da Atividade 1 no Cronograma Geral.
- Pergunta: se você quisesse adicionar uma aba "Atividade 2 - Detalhamento" igual à da Atividade 1, quais fórmulas você precisaria copiar/adaptar?

---

## Resumo — ordem e tempo estimado

| Bloco | Conteúdo | Tempo estimado |
|---|---|---|
| 0 | Pré-requisitos Python/Pandas | 0-2h (depende do que já sabe) |
| 1 | Revisão conceitual Passos 2/3 | 30min |
| 2 | `integra_usina_meteorologia.py` | 1h30 (é o mais denso) |
| 3 | `banco.py` + `consultas.py` | 45min |
| 4 | `carrega_banco.py` | 15min |
| 5 | `performance_ratio.py` | 30min |
| 6 | `dashboard.py` | 30min (leitura) + tempo variável se rodar de verdade |
| 7 | Planilha de acompanhamento | 20min |

**Teste final de entendimento:** feche todos os arquivos e tente desenhar, só de memória e num papel, o fluxo completo desde "arquivo exportado do PowerStation" até "número de PR aparecendo numa tela". Se você conseguir desenhar isso sem abrir nada, o plano funcionou.
