# Dicionário Técnico do Projeto — Comunicação Usina FV + Estação Meteorológica + Microrrede

**Nicolas Soares — consolidado a partir dos relatórios de estudo (Tópicos 1-4 e Fontes 1, 3, 4, 6, 9)**

Organizado por área. Pra cada termo: o que é/faz, de onde vem, e por que importa pro projeto.

---

## 1. Energia Fotovoltaica

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **kWp (quilowatt-pico)** | Capacidade nominal instalada dos módulos, medida em condições padrão de teste (STC). É diferente da potência real de saída. | No IFES Serra: ~140 kWp de módulos, mas ~119 kW de saída AC nos inversores. Essa diferença é um critério de validação de dado — se um inversor informar mais do que fisicamente pode, é sinal de erro. |
| **Inversor** | Equipamento que converte a corrente contínua (DC) gerada pelos módulos em corrente alternada (AC), compatível com a rede elétrica. | O Campus Serra tem 4 inversores PHB. É a principal fonte de dado elétrico da usina e o ponto crítico a mapear (que protocolo ele fala?). |
| **Irradiância** | Quantidade de energia solar que chega por m² (W/m²). Varia com hora do dia, nuvens, estação. | Variável-chave pra explicar (e prever) a geração. Vem da MAWS55 ou de sensor próprio (célula calibrada / IMT Si-Sensor). |
| **Performance Ratio (PR)** | Indicador que compara o rendimento real da usina com o rendimento teórico esperado, dado a irradiância recebida. Quanto mais perto de 1 (ou 100%), melhor. | Métrica candidata pra transformar "geração bruta" em "geração avaliada" — depende de cruzar dado elétrico com dado meteorológico. |
| **Sujidade** | Acúmulo de poeira/sujeira nos módulos que reduz a geração sem que haja falha elétrica. | Pode explicar quedas de geração que não são causadas por baixa irradiância — só é possível investigar cruzando com dados de chuva/vento da estação. |
| **LCOE (Levelized Cost of Energy)** | Custo nivelado da energia: quanto custa, em média, gerar 1 kWh ao longo da vida útil do sistema, considerando investimento, manutenção e geração total. | Indicador econômico possível (não decidido) pra comparar o custo da energia solar do IFES com a tarifa da concessionária. |
| **LCOH (Levelized Cost of Hydrogen)** | Equivalente ao LCOE, mas para custo de produção de hidrogênio. | Não aplicável ao projeto (produção de H2 foi descartada do escopo), mas apareceu na Fonte 3 como referência conceitual. |
| **Payback** | Tempo necessário para o investimento se pagar com a economia gerada. | Indicador econômico complementar ao LCOE, útil se o projeto avançar pra análise financeira. |
| **HelioScope** | Software de simulação de sistemas fotovoltaicos (dimensionamento, sombreamento, cenários de expansão). | Referência de ferramenta pra simular cenários de expansão da usina — mas só cobre a parte FV, não a microrrede inteira. |
| **PV canopy** | Estrutura de cobertura solar (ex: sobre estacionamento) que gera energia e também fornece sombra/cobertura. | Apareceu como cenário de expansão em outro estudo de caso — não decidido pro IFES, depende de levantamento de área disponível. |
| **Trigeração** | Sistema que produz eletricidade, aquecimento e resfriamento a partir da mesma fonte de energia. | Não incorporada ao projeto — ficou só como referência de como uma microrrede pode integrar múltiplas necessidades energéticas. |
| **Geração Distribuída (GD)** | Modelo de geração de energia feito perto (ou no local) do consumo, ao invés de vir só de grandes usinas centralizadas — é o enquadramento regulatório da usina do IFES. | Base regulatória do projeto — a usina do IFES é uma instalação de minigeração distribuída conectada à rede da concessionária (EDP). |

## 2. Estação Meteorológica

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **MAWS55** | Modelo da estação meteorológica automática instalada no Campus Serra desde julho/2022, pertencente à rede da SEAMA-ES. | É a fonte oficial de dado ambiental do projeto — ainda preciso confirmar como ela disponibiliza os dados (frequência, formato, acesso). |
| **Piranômetro** | Sensor que mede irradiância solar com alta precisão (referência profissional, mas caro). | Citado na literatura como padrão-ouro de medição de irradiância — no projeto, a alternativa de baixo custo é célula FV calibrada. |
| **Temperatura do módulo vs. ambiente** | A temperatura do painel FV (que afeta diretamente a eficiência) é diferente da temperatura do ar ao redor. | Preciso medir as duas separadamente (Pt100 no módulo, DS18B20 no ambiente, por exemplo) porque uma não substitui a outra na análise. |

## 3. Microrrede

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **Microrrede** | Conjunto de fontes de geração, cargas e (às vezes) armazenamento que pode operar de forma integrada, conectada ou não à rede principal. | É o terceiro "pilar" do projeto (junto com usina e estação) — ainda em aberto como será modelada/simulada. |
| **Espaço Energia** | Instalação residencial protótipo no Campus Serra com 3 kWp de geração FV + 1 kVA de geração eólica. | Segunda fonte de geração do projeto, em escala pequena — útil como caso de teste pra Atividade 6 (simulação da rede integrada). |
| **SCADA (Supervisory Control and Data Acquisition)** | Sistema de supervisão que centraliza dados de vários equipamentos e permite monitoramento (e às vezes controle) em tempo real. | Conceito de referência pra como organizar o supervisório do projeto — o dashboard em Streamlit cumpre um papel parecido, em menor escala. |
| **Sincronização de geradores** | Fazer duas ou mais fontes de energia (ex: FV + gerador a gás) entregarem energia à mesma carga ao mesmo tempo, de forma coordenada. | Referência conceitual (Fonte 3) — ainda não sei se os equipamentos do IFES permitem esse tipo de integração. |

## 4. Hardware e Eletrônica

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **ESP32** | Microcontrolador com Wi-Fi/Bluetooth embutido, usado como unidade de aquisição na ponta (perto dos sensores). | Unidade de processamento escolhida pro firmware de aquisição — mas seu uso depende do mapeamento (se os equipamentos já entregam dado suficiente, pode não ser necessário duplicar sensor). |
| **Raspberry Pi** | Computador de placa única, roda Linux completo — usado como hub central. | Vai rodar o banco de dados, o broker MQTT (ou o cliente) e o dashboard Streamlit. |
| **ACS712** | Sensor de efeito Hall pra medir corrente elétrica, com isolamento galvânico (protege o circuito de medição de danos da parte de potência). | Sensor de corrente escolhido — citado repetidamente na literatura pelo mesmo motivo (segurança + custo baixo). |
| **Pt100 / Pt1000 (RTD)** | Sensor de temperatura baseado na resistência de um fio de platina, que varia previsivelmente com a temperatura. Alta precisão e estabilidade, mas mais caro. | Escolhido pra medir temperatura do módulo FV, onde precisão importa mais. |
| **DS18B20** | Sensor digital de temperatura, barato, de fácil integração (protocolo 1-Wire). | Escolhido pra temperatura ambiente, onde o custo-benefício importa mais que a precisão extrema do RTD. |
| **IMT Si-Sensor** | Sensor de irradiância baseado em célula de silício, referência "profissional" mais barata que piranômetro termopilha. | Opção de medição de irradiância com melhor custo-benefício que o piranômetro tradicional. |
| **Célula fotovoltaica calibrada** | Um pequeno módulo FV de referência, calibrado, usado como sensor de irradiância indireto (a corrente gerada por ele é proporcional à irradiância). | Alternativa redundante e até 20x mais barata que o piranômetro termopilha, segundo a literatura. |
| **ADC (Conversor Analógico-Digital)** | Componente que transforma um sinal analógico (tensão contínua de um sensor) em um número digital que o microcontrolador consegue processar. A "resolução" (8, 10, 12, 16, 18 bits) define a precisão dessa conversão. | O ESP32 tem ADC de 12 bits, melhor que o Arduino comum (8-10 bits), mas ainda pode ter ruído — ponto de atenção pra precisão das medições. |
| **Watchdog** | Mecanismo de hardware/firmware que reinicia o dispositivo automaticamente se ele travar (não responder dentro de um tempo). | Vai garantir que o ESP32 se recupere sozinho de travamentos, sem precisar de intervenção manual — importante pra monitoramento contínuo. |
| **millis() vs. delay()** | `delay()` trava o processador esperando um tempo fixo; `millis()` permite controlar tempo sem travar, possibilitando fazer várias coisas "ao mesmo tempo" no firmware. | Decisão de não usar `delay()` no ESP32 — assim ele consegue ler sensor, tentar reconectar e monitorar falhas simultaneamente. |
| **PLC (Controlador Lógico Programável)** | Computador industrial robusto, usado pra automação e controle em ambientes industriais, geralmente centraliza dados de vários equipamentos antes de mandar pro SCADA. | Apareceu na Fonte 4 como peça central de uma arquitetura industrial — referência conceitual, não necessariamente algo que vou usar. |
| **Datalogger** | Dispositivo dedicado a registrar dados de sensores ao longo do tempo, às vezes com pouca ou nenhuma capacidade de processamento. | Possibilidade de equipamento intermediário entre o inversor PHB e o meu sistema, caso a comunicação direta não seja viável. |
| **Gateway** | Equipamento que converte/traduz um protocolo de comunicação para outro, permitindo que sistemas diferentes conversem. | Possível necessidade caso os inversores PHB só falem um protocolo que o meu sistema não entende diretamente. |

## 5. Protocolos e Comunicação

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **MQTT** | Protocolo leve de mensageria, baseado em "publicar/assinar" (publish/subscribe) — dispositivos publicam dados num tópico, e quem tiver interesse assina esse tópico. | Camada de integração escolhida como espinha dorsal — permite que usina, estação e microrrede publiquem dados numa estrutura comum. |
| **Broker (Mosquitto)** | O "servidor" que intermedeia as mensagens MQTT entre quem publica e quem assina. Mosquitto é uma implementação open-source popular. | Vai rodar no Raspberry Pi, recebendo tudo que os dispositivos publicam. |
| **Modbus (RTU/TCP)** | Protocolo de comunicação industrial bastante usado em inversores, PLCs e equipamentos de automação. RTU roda sobre serial (RS-485), TCP roda sobre rede Ethernet. | Hipótese forte pra comunicação com os inversores PHB — mas ainda não confirmada, precisa verificar na documentação/equipamento real. |
| **Profibus** | Outro protocolo de comunicação industrial, mais comum na Europa, usado em automação de processo. | Apareceu na Fonte 4 como parte da arquitetura industrial estudada — referência, não necessariamente aplicável ao IFES. |
| **RS-485** | Padrão físico de comunicação serial, usado como "camada de transporte" para protocolos como Modbus RTU. Permite várias distâncias e múltiplos dispositivos numa mesma linha. | Hipótese de meio físico pra conversar com os inversores, caso eles usem Modbus RTU. |
| **Zigbee** | Protocolo de rádio de baixo consumo e baixo alcance/médio, formando redes mesh (os dispositivos se revezam retransmitindo mensagens uns dos outros). | Candidato pra formar uma rede de sensores sem fio (WSN) robusta dentro da área da usina. |
| **LoRa** | Protocolo de rádio de longo alcance e baixíssimo consumo, mas taxa de dados baixa. | Candidato pra conectar a MAWS55 ou outros pontos fisicamente distantes, sem precisar de cabo. |
| **Wi-Fi** | Protocolo de rede sem fio de curto/médio alcance e alta taxa de dados. | Meio de comunicação nativo do ESP32 — bom pra onde já existe cobertura de rede no campus. |
| **HTTP/REST** | Protocolo (HTTP) e estilo de arquitetura (REST) muito usados pra expor dados via web, geralmente em formato JSON. | Possível forma de acesso a dados caso algum equipamento (ex: sistema de monitoramento da usina) disponibilize uma API. |
| **OPC-UA** | Protocolo de comunicação industrial mais moderno, focado em interoperabilidade entre sistemas de automação diferentes. | Ficou no radar da pesquisa bibliográfica inicial como alternativa a Modbus em cenários mais modernos. |
| **Ethernet** | Padrão de rede cabeada, rápido e confiável. | Possível meio de comunicação caso os inversores ou o sistema de monitoramento da usina já ofereçam essa interface. |
| **JSON / JSON Lines** | JSON é um formato de dado estruturado, fácil de ler por humano e máquina. JSON Lines é um arquivo onde cada linha é um objeto JSON independente. | Formato usado no EB-70 (JSON Lines em arquivo) e formato das mensagens que vão trafegar via MQTT no novo projeto (JSON dentro do MQTT). |
| **sequence_number** | Número sequencial incluído em cada mensagem, que permite detectar se alguma mensagem se perdeu no caminho (ex: pulou de 1003 pra 1005). | Mecanismo de detecção de perda de mensagem na comunicação MQTT. |
| **Timestamp** | Marca de tempo (data/hora) associada a um dado, indicando quando ele foi gerado (ou transmitido, ou recebido). | Fundamental pra sincronizar dados vindos de sistemas diferentes (usina, estação, microrrede) e montar séries temporais corretas. |

## 6. Software e Engenharia de Programação

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **Python** | Linguagem de programação de alto nível, com muitas bibliotecas prontas pra ciência de dados e IoT. | Linguagem principal do supervisor (roda no Raspberry Pi), reaproveitando a experiência do EB-70. |
| **C++** | Linguagem de baixo nível, usada no EB-70 pro "dispositivo" (parte de hardware/simulação). | Referência de arquitetura anterior — no novo projeto, o firmware do ESP32 provavelmente vai usar C++ (via Arduino IDE) também. |
| **SQLite** | Banco de dados relacional leve, que roda como um arquivo único (não precisa de servidor de banco separado). | Escolhido pra persistência local no Raspberry Pi, reaproveitando a experiência do EB-70. Ponto de atenção: pode não aguentar bem escrita concorrente de 3 fontes simultâneas. |
| **Streamlit** | Framework Python pra criar dashboards web rapidamente, sem precisar programar front-end do zero. | Interface de visualização do projeto, reaproveitada do EB-70 (filtros por TAG, status colorido, etc.). |
| **NumPy / Pandas / SciPy** | Bibliotecas Python pra computação numérica (NumPy), manipulação de tabelas de dados (Pandas) e funções científicas como interpolação/estatística (SciPy). | Usadas na etapa de tratamento e limpeza de dados, incluindo interpolação de lacunas pequenas (spline cúbica via SciPy). |
| **Matplotlib** | Biblioteca Python pra criar gráficos. | Complementa o Streamlit em análises mais específicas ou exploratórias. |
| **Scikit-learn** | Biblioteca Python de Machine Learning "clássico" (regressão, classificação, etc., sem redes neurais profundas). | Ferramenta candidata pra modelos de previsão mais simples ou pra pré-processamento dos dados de ML. |
| **Statsmodels** | Biblioteca Python voltada a modelos estatísticos, incluindo séries temporais como ARIMA. | Ferramenta pra implementar o ARIMA como modelo de referência de previsão. |
| **PyTorch / TensorFlow** | Frameworks de Deep Learning (redes neurais), incluindo modelos como LSTM. | Ferramentas candidatas pra implementar o modelo LSTM de previsão de geração. |
| **Factory Pattern** | Padrão de projeto (GoF) que centraliza a criação de objetos (ex: sensores) num único ponto, permitindo adicionar novos tipos sem alterar código existente. | Já validado no EB-70 (adição do SensorTurbidez sem tocar em código antigo) — será reaproveitado pra criação dinâmica de sensores no novo projeto. |
| **Command Pattern** | Padrão de projeto que encapsula uma ação (ex: ligar/desligar algo) num objeto, com métodos de executar e desfazer, desacoplando quem pede da execução. | Reaproveitado do EB-70 — no novo projeto, serve pra ações de controle na microrrede (ligar/desligar cargas). |
| **Strategy Pattern** | Padrão de projeto que permite trocar um algoritmo por outro (ex: diferentes formas de calcular uma métrica) sem alterar o código que usa esse algoritmo. | Planejado pra este projeto (já estava anotado como pendência no README do EB-70) — útil pra alternar entre formas de calcular indicadores (ex: PR) ou modelos de previsão. |
| **Observer Pattern** | Padrão de projeto onde vários "observadores" são notificados automaticamente quando um "sujeito" muda de estado, sem acoplamento direto entre eles. | Planejado pra este projeto — útil pra notificar dashboard, alarme e log ao mesmo tempo quando um novo dado chega. |
| **Repository Pattern** | Padrão de projeto que abstrai o acesso a dados (ex: banco de dados) atrás de uma interface, separando a lógica de negócio de como o dado é armazenado. | Já existia informalmente no EB-70 (`sqlite_repository.py`) — formaliza o acesso ao SQLite no novo projeto. |
| **Dado real vs. dado imputado** | Dado real é o que veio efetivamente do sensor; dado imputado é um valor estimado depois, pra preencher uma lacuna. | Separação que precisa ficar marcada no banco, pra manter rastreabilidade entre o que foi medido e o que foi estimado. |
| **Interpolação (spline cúbica)** | Técnica matemática de estimar um valor dentro de uma lacuna de dados, com base na tendência dos valores ao redor. | Método escolhido pra preencher lacunas pequenas nas séries temporais, sem inventar uma série artificial longa demais. |
| **Outlier** | Valor que foge muito do padrão esperado dos dados — pode ser um evento real ou um erro de medição. | Precisa ser identificado antes de entrar em qualquer modelo de previsão, senão distorce o resultado. |
| **ARIMA** | Modelo estatístico clássico de previsão de séries temporais, baseado em autocorrelação, tendência e sazonalidade. | Candidato como modelo de referência mais simples pra prever a geração da usina. |
| **LSTM (Long Short-Term Memory)** | Tipo de rede neural recorrente, especializada em aprender dependências de longo prazo em sequências temporais. | Candidato como modelo mais avançado de previsão, pra comparar performance contra o ARIMA. |
| **Vision Transformer** | Arquitetura de rede neural originalmente pra processamento de imagens, adaptada aqui pra estimar irradiância a partir de imagens do céu. | Não incorporado ao projeto agora — complexidade alta demais pro escopo atual, fica como possibilidade futura. |
| **log-cosh (função de perda)** | Função usada pra treinar redes neurais, mais robusta a outliers que o erro quadrático médio comum. | Considerada como camada extra de proteção em modelos neurais — não substitui a limpeza prévia dos dados. |
| **Curva I-V** | Gráfico que relaciona corrente e tensão de um módulo/arranjo fotovoltaico, usado pra diagnosticar falhas (sombra parcial, degradação, etc.). | Técnica de diagnóstico possível, mas depende de ter acesso a esse tipo de dado no inversor — ainda em aberto. |

## 7. Economia, Regulação e Gestão (contexto brasileiro)

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **ANEEL** | Agência Nacional de Energia Elétrica — órgão regulador do setor elétrico brasileiro. | Referência regulatória pro enquadramento da usina do IFES (grupo A, subgrupo A4, tarifa verde). |
| **Resolução Normativa 482/2012 e 687/2015** | Normas da ANEEL que criaram e depois ampliaram o sistema de compensação de energia (net metering) pra geração distribuída no Brasil. | Base histórica da regulação de GD no Brasil — preciso confirmar a legislação vigente hoje, já que essas normas têm atualizações posteriores. |
| **Bandeiras tarifárias** | Sistema de sinalização que indica se a energia está mais cara ou mais barata no mês, dependendo das condições de geração (ex: hidrelétricas com pouca água acionam termelétricas mais caras). | Variável de contexto econômico — não indica a eficiência da usina, só o custo da energia da rede naquele período. |
| **Grupo A / Subgrupo A4 / Tarifa verde** | Classificação tarifária de consumidores de média/alta tensão (como o IFES), com tarifas diferentes pra ponta e fora de ponta. | Contexto tarifário real da instalação do IFES Campus Serra, relevante pra qualquer análise econômica futura. |
| **ISO 50001** | Norma internacional de sistema de gestão de energia. | Referida como inspiração pra uma possível norma nacional de gestão de energia FV — não será implementada diretamente no projeto. |
| **AHP (Analytic Hierarchy Process)** | Método de apoio à decisão que organiza critérios em hierarquia e usa comparações par-a-par pra chegar a uma priorização. | Ferramenta possível pra decisões futuras (ex: escolher entre cenários de expansão), mas sem necessidade definida ainda. |
| **PIMVP / M&V (Medição e Verificação)** | Protocolo internacional (da EVO) pra medir e verificar resultados de eficiência energética de forma padronizada. | Citado na proposta original do projeto como referência pra validar os resultados de economia de energia. |

---

## 8. Segurança Cibernético-Física

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **Segurança cibernético-física** | Abordagem de segurança que não olha só pra parte digital (rede, dados, software), mas também pro que pode acontecer fisicamente no sistema caso algo dê errado na parte cibernética. | Muda a forma de pensar segurança no projeto: não é só "proteger o banco de dados", é entender o que um dado falso ou uma comunicação perdida pode causar na usina/microrrede de verdade. |
| **CP-SAM (Cyber-Physical Security Assessment Metric)** | Métrica que combina vários fatores de segurança e resiliência de uma microrrede numa única avaliação. | Não vai ser implementada por completo (é muito grande pro escopo), mas o conceito geral — ter algum indicador de resiliência do sistema — fica como referência futura. |
| **Camadas física / dispositivos / comunicação / gerenciamento** | Forma de dividir uma microrrede em 4 níveis: o que é físico (usina), os aparelhos (sensores, ESP32), a comunicação (Wi-Fi, MQTT) e o gerenciamento (software, banco, dashboard). | Ajuda a organizar o próprio projeto em camadas parecidas — útil principalmente pra pensar o protocolo/interface de integração (Atividade 4). |
| **Confidencialidade, integridade, disponibilidade (CIA)** | Os três pilares clássicos da segurança da informação: dado não pode vazar (confidencialidade), não pode ser alterado indevidamente (integridade), e precisa estar acessível quando necessário (disponibilidade). | Base conceitual pra pensar quais requisitos de segurança cada tipo de dado do projeto precisa (monitoramento vs. um futuro comando de controle, por exemplo). |
| **Autenticidade** | Garantia de que um dado ou comando realmente veio de quem diz ter enviado (e não foi forjado por outra fonte). | Relevante principalmente se o sistema um dia evoluir de "só monitorar" pra "também controlar" algo na microrrede. |
| **Integral de Choquet / MCDM / Shapley Value** | Ferramentas matemáticas usadas no CP-SAM pra combinar múltiplos critérios de segurança numa avaliação só, considerando inclusive interação entre eles (MCDM = Multi-Criteria Decision Making). | Ficaram como referência teórica, não serão implementadas — a matemática é pesada demais pro escopo atual. |
| **Attack graph** | Representação gráfica dos possíveis caminhos que um ataque poderia seguir dentro de um sistema, de um ponto de entrada até um alvo. | Não será implementado — auditoria de segurança completa está fora do escopo atual do projeto. |
| **CVSS (Common Vulnerability Scoring System)** | Sistema padronizado de pontuação de vulnerabilidades conhecidas de software/hardware. | Referência pra uma possível análise futura de risco dos equipamentos (inversores, ESP32, Raspberry Pi) — não vou atribuir vulnerabilidade sem conhecer modelo/versão real do equipamento. |
| **Redundância de caminhos** | Quantos caminhos diferentes existem pra uma informação chegar de um ponto a outro — quanto mais caminhos, mais o sistema resiste a uma falha isolada. | Conceito interessante pra avaliar a robustez da comunicação depois, mas ainda não sei se a infraestrutura do IFES tem esse tipo de redundância. |
| **Latência / perda de pacotes** | Latência é o atraso entre o envio e o recebimento de um dado; perda de pacotes é quando parte da informação simplesmente não chega. | Métricas pra monitorar a qualidade da comunicação, além de só checar "os dados chegaram ou não" — conecta com os mecanismos de detecção de falha que já vinha desenhando (sequence_number, timestamp). |
| **Chaos Monkey** | Prática (originada na Netflix) de provocar falhas de forma controlada e proposital num sistema, pra testar se ele aguenta e se recupera. | Não vou aplicar literalmente nos equipamentos reais do IFES, mas o princípio (simular perda de sensor, de ESP32, de MQTT) pode ser usado num ambiente de simulação, na Atividade 6. |
| **Falha de comunicação vs. falha física** | Distinção importante: se o sistema parar de receber dado de um inversor, isso não significa que o inversor quebrou — pode ser o Wi-Fi, o MQTT, o firmware, etc. | Reforça a necessidade de um bom sistema de diagnóstico que não confunda "não recebi dado" com "o equipamento parou de gerar". |

## 9. Gestão de Energia e Tecnologias Emergentes (referências, não implementadas agora)

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **HEMS (Home Energy Management System)** | Sistema que gerencia geração, consumo, baterias e tarifas dentro de uma residência, buscando otimizar custo e conforto. | Referência conceitual (Fonte Extra 2) — o projeto do IFES não é um HEMS, mas ajudou a enxergar uma possível evolução futura do sistema (de "só monitorar" até "otimizar"). |
| **Demand Response** | Mecanismo em que o consumidor ajusta seu consumo de acordo com o preço ou a condição da rede elétrica naquele momento. | Não aplicável ao escopo atual (não há controle de cargas no projeto), mas é um conceito de gestão de demanda relacionado à Fonte 9 (regulação brasileira). |
| **Cargas rígidas vs. elásticas / interrompíveis vs. não interrompíveis** | Classificação de cargas elétricas conforme a flexibilidade que elas têm pra mudar de horário ou serem interrompidas. | Conceito de referência, não aplicado agora — o projeto ainda está na etapa de monitoramento, não de controle de cargas. |
| **BESS (Battery Energy Storage System)** | Sistema de armazenamento de energia por bateria, carregado quando há energia sobrando (ex: muito sol) e descarregado quando falta ou fica cara. | Não incorporado ao projeto agora — fica como possibilidade futura, dependendo de o IFES ter (ou vir a ter) esse tipo de equipamento. |
| **Distribuição Beta (probabilidade)** | Modelo estatístico usado pra representar a incerteza da irradiância solar (em vez de tratá-la como um valor fixo e previsível). | Referência de como tratar a variabilidade natural da geração solar — ainda não sei se esse modelo se aplica aos dados do IFES, depende de dado real. |
| **Simulação de Monte Carlo** | Técnica que gera muitos cenários aleatórios (baseados numa distribuição de probabilidade) pra entender o intervalo de resultados possíveis de um sistema incerto. | Possibilidade futura pra simular cenários de geração considerando a incerteza da irradiância — não decidido, depende de dados reais. |
| **UDV (User Disturbance Value)** | Métrica que mede o "desconforto" causado a um usuário quando um sistema desloca o funcionamento de um equipamento pra outro horário. | Não aplicável — o projeto do IFES não lida com conforto de usuário residencial. Descartado. |
| **NAA (Natural Aggregation Algorithm)** | Metaheurística de otimização inspirada em comportamento coletivo de animais, usada pra resolver problemas com múltiplas restrições. | Não implementado agora — não há, no momento, um problema de otimização no projeto que justifique usar isso. Fica como referência caso surja essa necessidade depois. |
| **Tarifa TOU (Time of Use) / Feed-in tariff** | TOU é tarifa que varia conforme o horário do dia; feed-in tariff é o valor pago por energia injetada na rede. | Conceitos do cenário australiano do artigo, não transferíveis diretamente — o Brasil tem suas próprias regras (bandeiras tarifárias, grupo A/subgrupo A4, já vistos na Fonte 9). |
| **V2H (Vehicle-to-Home)** | Tecnologia que permite usar a bateria de um veículo elétrico pra alimentar uma residência. | Fora do escopo do projeto — não há veículo elétrico envolvido. |
| **Digital Twin** | Representação virtual (um "gêmeo digital") de um sistema físico, atualizada com dados reais em tempo real, permitindo simular e acompanhar o comportamento do sistema real. | Tecnologia interessante pro futuro do projeto, mas depende de já ter uma base de dados confiável antes — deixada pra depois. |
| **Blockchain / smart contracts / mercado P2P de energia** | Blockchain é um registro distribuído e imutável de transações; smart contracts são acordos que se executam automaticamente; mercado P2P permite consumidores negociarem energia diretamente entre si. | Não acatado — está bem distante do foco atual do projeto (monitoramento e integração de dados). |
| **MPC (Model Predictive Control)** | Técnica de controle que usa um modelo do sistema pra prever o comportamento futuro e decidir a melhor ação a cada instante. | Não implementado agora — o projeto ainda não tem controle automatizado, só monitoramento. Fica como possibilidade bem futura. |
| **Sistemas multiagente** | Arquitetura onde vários "agentes" de software, cada um com sua responsabilidade, cooperam pra gerenciar um sistema maior. | Referência de uma arquitetura mais avançada de gerenciamento — não faz sentido ainda enquanto a base de aquisição/comunicação não estiver pronta. |
| **Internet da Energia (IoE)** | Visão de longo prazo em que a infraestrutura energética funciona de forma tão integrada e inteligente quanto a internet de dados hoje. | Visão de horizonte distante — não é meta do projeto atual, só contextualiza pra onde esse tipo de sistema pode evoluir. |
| **Flexibilidade energética** | Capacidade de um sistema adaptar geração e consumo diante de variações normais (não extremas) de operação. | Conceito que ajuda a diferenciar de "resiliência" — útil pra qualquer análise futura do comportamento da usina/microrrede. |
| **Resiliência energética** | Capacidade de um sistema suportar e se recuperar de eventos extremos, falhas ou perturbações. | Conceito relacionado à ideia de Chaos Monkey e testes de falha simulada — algo a considerar na Atividade 6 (simulação da rede). |
| **V2B / V2G (Vehicle-to-Building / Vehicle-to-Grid)** | Tecnologias que permitem usar a bateria de um veículo elétrico pra alimentar um prédio (V2B) ou devolver energia à rede (V2G). | Fora do escopo — não há veículo elétrico envolvido no projeto atual. |
| **PCM (Phase Change Material) / bombas de calor** | PCM é um material usado em armazenamento térmico (absorve/libera calor ao mudar de fase); bombas de calor transferem calor de um ambiente pra outro de forma eficiente. | Tecnologias de eficiência energética citadas no artigo, fora do escopo atual (o projeto foca em dados elétricos e meteorológicos, não em climatização). |

## 10. Infraestrutura Real do IFES Campus Serra (mapeamento concreto)

Diferente das seções anteriores (que vêm da literatura), esta seção documenta o que eu já confirmei olhando direto nas plataformas de monitoramento reais do campus — é a virada de "hipótese" pra "fato".

| Termo | O que é/faz | Por que ajuda no projeto |
|---|---|---|
| **PowerStation (PHBSolar)** | Portal web de monitoramento da marca PHB, usado pela usina principal do campus (estação "Ifes Serra"). Mostra potência instantânea, geração diária/total, receita estimada, status por inversor, MPPT e alarmes. | É a fonte de dado elétrico já pronta da usina de 119 kW/140 kWp — antes de instrumentar do zero, preciso descobrir se dá pra automatizar a extração desse portal (API, export, ou scraping). |
| **SolarPortal+** | Portal web de monitoramento (aparentemente da marca KSTAR), usado pelo sistema do Espaço Energia. Mostra geração, status do datalogger/inversor e (quando disponível) sensores ambientais. | Fonte de dado elétrico do Espaço Energia (3 kWp) — mesmo raciocínio do PowerStation: verificar possibilidade de extração automatizada. |
| **PHB / KSTAR** | Fabricantes de inversores identificados no campus — PHB na usina principal, KSTAR (modelo 5KDM) no Espaço Energia. | Saber a marca/modelo real permite pesquisar diretamente a documentação técnica (datasheet, protocolo, API) desses equipamentos específicos, em vez de trabalhar só com hipótese genérica. |
| **MPPT (Maximum Power Point Tracking)** | Mecanismo dentro do inversor que ajusta continuamente a operação pra extrair a máxima potência possível dos módulos, dado a tensão/corrente DC disponíveis naquele momento. Cada "canal" ou "entrada" MPPT corresponde a uma string de módulos. | A usina principal expõe 4 canais MPPT (tensão 600-850V DC, corrente até 22A) — é um dado elétrico já disponível no portal, útil pra diagnóstico mais fino do que só potência total. |
| **Datalogger** *(confirmação real)* | Equipamento que coleta os dados do inversor e os envia pra nuvem/portal. No campus, cada sistema tem seu próprio datalogger, identificado por número de série, com versão de firmware e força de sinal de comunicação. | Confirma que a comunicação inversor→nuvem já existe e funciona — o desafio não é criar essa ponte, é conseguir os dados de volta (extrair da nuvem pro meu sistema). |
| **AI Health / diagnóstico automático** | Funcionalidade do portal PowerStation que já roda uma checagem automática de saúde do sistema e sinaliza se há algum erro ativo. | Mostra que o fabricante já tem uma camada básica de diagnóstico — posso usar isso como referência (ou até como fonte adicional de dado) em vez de reinventar diagnóstico do zero. |
| **Falha de isolação (Low Insulation Resistance)** | Alarme que indica fuga de corrente — geralmente causada por umidade ou degradação na isolação dos cabos DC ou dos módulos. | Achado real no campus (Inversor 04, duas ocorrências) — é um exemplo concreto de falha física real que posso usar pra validar minhas regras de detecção de erro (Tópicos 1-4), em vez de só simular. |
| **Grid Outage / tensão e frequência fora da faixa** | Alarme disparado quando a rede elétrica da concessionária sai da faixa aceitável de tensão/frequência, fazendo o inversor se desconectar por segurança (e reconectar quando a rede normaliza). | Outro exemplo real de evento registrado no campus (Inversores 01-03, recuperados automaticamente) — mostra que uma "queda" na geração nem sempre é falha do sistema, pode ser evento da rede externa. |
| **FTP / FileZilla** | FTP é um protocolo antigo e simples de transferência de arquivos; FileZilla é um programa (cliente) usado pra acessar esse tipo de servidor manualmente. | Forma como os dados da MAWS55 são obtidos hoje (arquivo baixado manualmente via FTP) — um dos primeiros pontos de automação possível: trocar o download manual por um script Python que baixa o arquivo sozinho, periodicamente. |
| **Resampling (reamostragem)** | Técnica de agregar uma série temporal em um intervalo de tempo diferente do original (ex: transformar 15 em 15 minutos em médias horárias), usando `.resample()` no Pandas. | Necessário pra cruzar a MAWS55 (15 min) com os dados dos portais solares, que provavelmente têm frequência diferente — sem isso, não dá pra comparar os dois de forma justa. |

## Como usar esse dicionário

Os termos estão organizados pela área onde fazem mais sentido primeiro, mas muitos cruzam mais de uma (ex: MQTT é tanto "comunicação" quanto parte da "arquitetura de software"; Performance Ratio é tanto "energia" quanto um número que só existe se a "estação meteorológica" fornecer irradiância). Isso reflete bem a natureza do projeto: ele só funciona porque as áreas se cruzam.

Esse documento pode ser atualizado conforme novas fontes forem estudadas — é basicamente o glossário de apoio pra qualquer relatório ou seção de fundamentação teórica futura.
