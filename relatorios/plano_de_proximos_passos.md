# Plano de próximos passos — Projeto IC (atualizado em 24/10/2026)

Lista que eu montei depois do plano de estudos, organizada em frentes. `[x]` = feito, `[ ]` = a fazer.

## Frente A — organizar o que já existe
- [x] Revisar o código e a margem de erro (`relatorios/revisao_codigo_frente_a.md`)
- [x] Renomear arquivos e pastas
- [x] Versão limpa + versão comentada (mesmo código executável)
- [x] Repositório no GitHub: nicolassn013/ProjetoIC (só a versão limpa)

## Frente B — dados do Estudante 1 e banco (código concluído em 24/10/2026)
Situação: o Estudante 1 entregou a ponte FTP para o site Lovable do GERA (`GERAIF-Ponte`) e informou que **não vai mudar mais nada** no banco. Por isso a aquisição dos dados do FileZilla/MAWS55 foi feita **do nosso lado**, direto para o nosso banco, sem depender do tratamento dele.

**Feito em 21/10/2026**
- [x] Decidido: os 2 dias de exemplo **ficam** (serão substituídos pelos dados reais)
- [x] Banco versão 2 e pacote para o Estudante 1 (`pacote_estudante1/`, hoje desatualizado: descreve a versão 2)

**Feito em 23 e 24/10/2026**
- [x] Banco consolidado na **versão 4**: as 56 variáveis vivem em `meteorologia_15min`, view `vw_leitura_completa`, diário `ingestao_arquivos`, migrações 001 a 004 com backup automático
- [x] **Aquisição FTP/pasta para o nosso banco** (`pipeline/aquisicao_maws55.py`): lê, trata com as regras do Estudante 1, grava em modo `mesclar`, diário, cópia bruta, `--simular`, códigos de saída 0/1/2. Documentação em `relatorios/aquisicao_maws55.md`
- [x] **Formato real do .txt confirmado** com 2 arquivos do FTP (sem cabeçalho, vírgulas, horário UTC, 52 ou 56 valores). Um dia inteiro (96 arquivos no formato real) ingerido pela linha de comando ficou igual ao pipeline
- [x] Padrões de projeto avaliados e aplicados com gatilho (`relatorios/padroes_de_projeto.md`)
- [x] 76 testes passando (3 só rodam com o xlsx tratado do Estudante 1 na máquina)
- [x] **Achado:** o xlsx tratado do Estudante 1 tem nomes de colunas deslocados em 3.653 linhas (15/07 a 22/08/2022). Detalhes em `aquisicao_maws55.md`, seção 4.2

**A fazer (só falta o que depende de acesso ao campus ou de decisão)**
- [ ] **Commits no GitHub** (você faz, com o guia `GUIA_COMMITS.md`; nada foi enviado)
- [ ] **Trocar a senha do FTP e o token do GERAIF**: o `config.env` do zip `GERAIF-Ponte` tem os dois reais e circulou por chat e zip
- [ ] No campus: `python pipeline/aquisicao_maws55.py --simular` com os arquivos mais recentes; confirmar o layout de 56 valores em arquivo real; depois rodar de verdade e agendar a cada 15 min
- [ ] Carregar o histórico pelo FTP (`--periodo tudo --confirmar`), em vez de usar o xlsx dele nas 3.653 linhas deslocadas
- [ ] Avisar o Estudante 1 do deslocamento de colunas e perguntar as unidades (`Temp int`, solo, SPF)
- [ ] Rodar o dashboard de verdade (nunca foi executado; Streamlit não instalado no ambiente de teste)

## Frente C — como os dados saem das fontes (Modbus)
- [x] Script de teste só de leitura pronto: `teste_modbus_phb.py` (autoteste passa; **não** foi testado com o `pymodbus` real nem com equipamento)
- [ ] **Visita técnica ao IFES** (prioridade, ver seção "Modbus" abaixo)
- [x] Obtidos (pasta "Suporte PHB" do Drive) datasheet, manual e registro do INMetro do PHB35K-MT e do PHB14K-DT (22/10/2026)
- [ ] Obter o **mapa de registradores Modbus da PHB**: os manuais **não trazem** a tabela. Pedir à PHB o documento de protocolo desses dois modelos (o mapa GoodWe segue sendo só hipótese)
- [ ] Confirmar na etiqueta física: INV01–03 = PHB35K-MT e INV04 = PHB14K-DT (hoje só **provável** pela série KMT/KDT e pela documentação)
- [ ] Confirmar no local: se há **PHB Wi-Fi Box** instalado, se há **PHB Logger Pro** na porta RS485, o endereço Modbus de cada um (menu "Cfg Modbus", padrão 247) e **quem é o mestre do barramento**
- [ ] Teste de leitura em **um** inversor autorizado: serial (`0200`–`0207`) e energia total (`0312`/`0313`) contra o histórico (INV01 367.169,8 / INV02 389.266,6 / INV03 73.243,0 / INV04 128.191,2 kWh)
- [ ] Mapear a comunicação do Espaço Energia (KSTAR, outro protocolo; fora do teste GoodWe/PHB)
- [ ] Ver o que bibliotecas como o pvlib ajudam (irradiância esperada, posição do sol)

## Frente D — pontes e integrações (depende da C)
- [ ] Ponte para os dados irem direto ao banco
- [ ] Integrar com o site do Rafael (Estudante 1)
- [ ] Decidir se o Modbus atrapalharia a atualização do portal (depende da resposta sobre o mestre do barramento)
- [ ] Tabelas do banco para dados Modbus: **só** a parte independente do mapa (inversor, timestamp, valor, origem da leitura, qualidade). Correntes por string e alarmes só depois de validar o mapa

## Frente E — gestão
- [ ] Combinar com o professor se sigo a planilha ou só atualizo o banco e monitoro
- [ ] Atualizar `organizacao_projeto_picti.xlsx` com as Frentes A, B e C
- [ ] Registrar as pistas Modbus no dicionário técnico e em `investigacao_comunicacao_atividade2.md`

---

## Banco: os 2 dias de exemplo (22/09/2025 e 22/09/2026) — resolvido

Decisão (21/10/2026): **ficam no banco** e serão substituídos quando os dados do Estudante 1 entrarem. O que foi testado em 16/10:
- Recarregar um dia apaga as linhas daquele dia e insere de novo; não duplica (192 linhas, 0 duplicados). Só o dia que chega é substituído.
- Risco real: um dia **incompleto** substitui o dia inteiro (96 linhas → 10). Agora o `carrega_banco.py` **avisa** quando um dia fica com menos linhas, e `salvar_meteorologia` devolve a lista desses dias.
- `historico_anual_*` é recriado por inteiro a cada carga, por desenho.
- Nada se perde: os relatórios brutos e os `.xlsx` processados continuam em `dados/`.

## Decisão pendente: Modbus e conversor RS485 para Ethernet (reunião de 22/10/2026)

A reunião debateu o assunto, **sem decisão**. Nada de compra ou instalação até fechar os critérios abaixo.

**Sabido:** os inversores têm RS485 (Modbus RTU) de fábrica; existe uma rede Wi-Fi só deles, então o PHB Wi-Fi Box provavelmente está instalado (é por ele que o SolarPortal+ recebe os dados). O INV04 aparece Offline no portal.

**Para decidir, falta:**
- [ ] Mapa de registradores Modbus da PHB (PHB35K-MT e PHB14K-DT). Sem ele, nenhum hardware ajuda
- [ ] Se a RS485 está livre e se há PHB Logger Pro (quem é o mestre do barramento)
- [ ] Endereço Modbus de cada inversor (padrão 247; precisam ser diferentes no mesmo barramento)
- [ ] Autorização do responsável técnico para a leitura (só função 03H, um inversor Running, de preferência o 01)
- [ ] Nível de acesso da minha conta no SolarPortal+ e se há exportação em lote

**Opções (escolher só depois dos itens acima):** (1) adaptador USB–RS485 + computador pequeno; (2) conversor RS485 para Ethernet/Wi-Fi (Modbus TCP); (3) PHB Logger Pro, se a PHB oferecer saída de dados; (4) exportação do SolarPortal+, sem hardware.

**Única compra razoável antes da decisão:** um adaptador USB–RS485 barato, para o teste de leitura em um inversor.

## Modbus: situação e visita técnica

**Estado atual (19/10/2026):**
- **Confirmado pela documentação da PHB (22/10/2026):** PHB35K-MT tem potência CA nominal de 35.000 W e PHB14K-DT de 14.000 W (**o 14 kW do INV04 passa a ter respaldo no datasheet/manual do modelo**, falta só a etiqueta física). Os dois têm interface **RS485 (Modbus RTU)**, USB e Wi-Fi (via **PHB Wi-Fi Box**, que envia ao portal de monitoramento). O manual diz que a RS485 é usada com o **PHB Logger Pro**, a distância máxima é 1000 m, cabo FTP par trançado, terminação "ON" só no último inversor, e o endereço Modbus se configura no menu do inversor (padrão 247). **Os manuais não trazem a tabela de registradores.** O registro INMetro lista PHB35K-MT e PHB14K-DT como modelos da PHB.
- A hipótese "os inversores PHB são GoodWe remarcados" é só uma **pista**: os seriais dos INV01 a INV03 têm "KMT" e o INV04 tem "KDT", parecidos com as séries MT e DT do manual GoodWe. Não prova fabricante, modelo nem mapa.
- Outro chat citou documentação pública da própria PHB (série MT de 35 e 60 kW com RS-485 e Modbus RTU; modelo PHB14K-DT). **Eu não consegui verificar** esses links. Pendente: colar o link do manual da PHB para conferir se há mapa de registradores.
- O manual GoodWe que eu tenho é a versão 1.1 de 2017, série MT, RTU a 9600 bps, endereço de 1 a 247 (padrão de fábrica 247).

**Script `teste_modbus_phb.py` (versão de 19/10/2026):**
- Só função 03H; endereço `--id` obrigatório; falha de leitura nunca vira zero.
- Energia classificada em COERENTE / INCONSISTENTE / INVESTIGAR / PARCIAL. O teto de aumento plausível vem da física (potência nominal × 10 h × dias), e não de um percentual. Para isso, informar `--data-relatorio` (data em que o relatório "estatístico (ALL)" foi baixado; a confirmar).
- O autoteste confere só a lógica e **não** valida a comunicação real. O 14 kW do INV04 ainda é hipótese.

**Caminhos (A, B e C do prompt mestre):**
1. **A — visita técnica: prioridade.** É o único que destrava.
2. **C — plano B, dentro da visita:** se o datalogger for o único mestre do barramento, **não** conectar um segundo mestre; investigar gateway ou dados disponibilizados pelo sistema existente.
3. **B — banco em paralelo**, só com o que independe do mapa (ver Frente D).

**Roteiro da visita (do outro chat) + 3 ajustes meus:**
- Antes: autorização, responsável técnico, levar o script e o resultado do `--autoteste` (deixando claro que ele não valida a comunicação física), relatórios do PowerStation, manual GoodWe e qualquer manual PHB, adaptador USB–RS-485 se autorizado.
- Fotografar (com autorização): etiqueta de cada inversor, interface RS-485, datalogger, topologia dos cabos, tela do portal com data e hora, documentação.
- Conferir os seriais físicos com INV01 `9035KMTS188W0071`, INV02 `9035KMTS188W0070`, INV03 `9035KMTS188W0064`, INV04 `9014KDTU183W0137`. Se divergirem, registrar e não mexer na associação no banco.
- Perguntar, nesta ordem: modelo do datalogger; se ele é o único mestre; se há segunda porta ou saída de dados independente; endereço Modbus de cada inversor; baud, paridade e stop bits; se a PHB tem mapa específico; se posso fazer uma leitura em **um** inversor numa janela combinada.
- Ordem no local: estado inicial do portal → identificar equipamentos → topologia (se a topologia for desconhecida, **parar e não conectar**) → configuração → `--autoteste` → leitura real autorizada de um inversor → conferir de novo o portal.
- Depois do teste, conferir se o portal **continua recebendo dados**: estado dos inversores, última atualização avançando, potência, energia acumulada e novos alarmes. Portal "abrir" não basta.
- **Ajuste 1 (corrigido em 22/10):** o portal da usina do IFES é o **SolarPortal+** (informado por mim mesmo; os relatórios exportados trazem outro nome, "PowerStation", a conferir) e o nível de acesso da minha conta ainda precisa ser confirmado. Perguntar: há **PHB Wi-Fi Box** e/ou **PHB Logger Pro** instalados? Se só há Wi-Fi Box, a porta RS485 pode estar livre. Se há Logger Pro, ele é o mestre do barramento.
- **Ajuste 2:** o KSTAR 5KDM tem protocolo próprio; o mapa GoodWe e o script **não** valem para ele.
- **Ajuste 3:** perguntar também por Modbus TCP, Wi-Fi ou outra saída de dados, para fechar o plano alternativo sem disputar o barramento.
- Ficha final: data e hora, responsável presente, modelo do datalogger, topologia, endereços confirmados, resultado do serial, resultado da energia, situação do portal depois, pendências.

**Regras de segurança (valem sempre):** só função 03H; nunca a função 10H. No manual GoodWe, os registradores `0120`/`0121` (Start/Stop) e `0000`–`0005` (limites de rede) são de escrita e podem desligar o inversor ou mudar a proteção. Não desconectar cabos, não mudar endereços, não conectar um segundo mestre ao barramento de produção sem autorização.

**Para usar depois de validar o mapa:** correntes por string (`035B`–`036E`), estado e código de falha (`030E`, `0310`, `0311`; falha de isolamento é o bit 18), potência com parte alta e baixa (`030D` + `0356`) e temperatura interna do inversor (`030F`, que **não** é a do módulo).

---

## Variáveis da MAWS55: situação em 21/10/2026

O arquivo `dados_meteorologicos_tratados.xlsx` tem 56 campos de medição. **Todos agora têm lugar no banco**:
- 5 em `leitura_15min` (radiação global dos dois sensores, temperatura, vento médio, precipitação);
- 51 em `meteorologia_15min`, mais 24 flags (inclusive as das 5 antigas).

Mas só o dia 22/09/2025 tem dado (96 linhas, copiadas do xlsx sem tratamento adicional). O resto depende do Estudante 1.

- **19 já tratadas por ele**: umidade relativa (4), direção do vento (3), velocidade do vento máx/mín (2), radiação global med/máx/mín dos 2 sensores (6), umidade do solo (4).
- **32 só dado bruto, sem flag**: pressão (4), `Temp int`, `Temperatura med/max/min`, radiação refletida, IV, SPF e líquida (16), NTC do LPNET14 (4), temperatura do solo (4).
- Unidades **inferidas**, não confirmadas.
- Valores estranhos para perguntar a ele: -40 °C em `Temperatura med/max/min`, umidade do solo de -0,4 a 1,0, IV e SPF negativos. O 360 no NTC está **explicado** (colunas deslocadas nas linhas de 2022; ver Frente B).
- Nome, unidade e flag de cada uma: `relatorios/dicionario_meteorologia.md`.
