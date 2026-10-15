# Investigação de Comunicação — Início Real da Atividade 2

**Nicolas Soares — 25/09/2026**

Antes de qualquer código de protocolo. Usei os arquivos/telas que já tenho + pesquisa sobre as plataformas e equipamentos reais envolvidos (PHB, KSTAR, Vaisala MAWS). Nenhuma tecnologia foi escolhida ainda — isso é só o levantamento pedido.

---

## A. Diagnóstico atual sobre comunicação

O que sei com certeza hoje: **as três fontes já entregam dado pra algum lugar** (isso é bom — comunicação já existe entre sensor→nuvem, só não é minha ainda). O que não sei: se dá pra automatizar a busca desse dado sem intervenção manual, e com qual protocolo.

Achado de pesquisa relevante: fabricantes concorrentes de PHB/KSTAR (SolarEdge, Solis, FoxESS, Goodwe/SEMS, SMA) **têm** API documentada publicamente pros seus portais de monitoramento — é uma prática comum na indústria. Não achei nenhuma documentação pública equivalente pra "SolarPortal+" (a marca "Azure Solar Co., Ltd." aparece como desenvolvedora do app SolarPortal+ nas lojas de aplicativo — parece ser uma plataforma white-label usada tanto por PHB quanto por KSTAR) nem para "PowerStation" da PHB especificamente. Isso não significa que não exista — só que não é pública/indexada como a de outros fabricantes.

## B. Matriz de comunicação

| Fonte | Equipamento | Como fornece dado hoje | Interface atual | Protocolo possível | Automatização possível | Evidência | Situação |
|---|---|---|---|---|---|---|---|
| PHB (usina 119kW) | INV01-04 | Portal web SolarPortal+/PowerStation, exportação manual (PDF/Excel) e tela "Data Comparison" | Web (login+navegador) | Desconhecido — API não documentada publicamente; pode existir endpoint interno inspecionável via DevTools | Possível (a confirmar) | Prints/exports reais que já tenho | **Confirmado o portal; API não confirmada** |
| KSTAR (Espaço Energia) | Inversor 5KDM + datalogger `I0718330248133` | Portal SolarPortal+/Ksolar, telemetria a cada ~5min | Web | Desconhecido — mesma plataforma-base da PHB, então provavelmente mesma situação (API não documentada publicamente) | Possível (a confirmar) | Telemetria pontual já inspecionada | **Confirmado o portal; sem lote/API confirmada** |
| KSTAR (alternativa local) | Datalogger | — | Possível RS-485/Modbus local no datalogger, se ele tiver porta física acessível (outros fabricantes de inversor permitem isso — ex: Kostal é lido via Ethernet+RS485 direto por projetos open-source) | Modbus RTU/TCP (hipótese, não confirmada neste equipamento) | Depende de acesso físico | Nenhuma evidência direta no meu equipamento | **Não confirmado — precisa inspeção física** |
| MAWS55 | Estação Vaisala (linha MAWS) | Arquivo baixado via FTP | FTP | FTP (é o protocolo padrão dessa família de estação, documentado pelo próprio fabricante) | **Sim** | Dado real já em mãos, tratado pelo Estudante 1 | **Confirmado** |
| Microrrede/Espaço Energia (parte não-KSTAR) | ? | ? | ? | ? | ? | Nenhuma | **Não confirmado** |

## C. Lacunas (o que ainda precisamos descobrir)

1. Se PowerStation/SolarPortal+ têm API oficial, chave de acesso, ou algum tipo de webhook/exportação agendada — ou se exportação manual é mesmo a única via oficial.
2. Se existe algum endpoint HTTP inspecionável no navegador (F12 → Network) quando o portal carrega os gráficos — isso não precisa de documentação oficial pra descobrir, só inspeção.
3. Se os dataloggers (tanto da usina quanto do KSTAR) têm porta física (RS-485/Ethernet) acessível localmente, sem depender da nuvem do fabricante.
4. Se existe algum PLC, gateway ou controlador na microrrede/Espaço Energia além do datalogger do inversor KSTAR — isso ainda é uma caixa-preta total.
5. Estrutura exata do FTP da MAWS55: é uma pasta com arquivo novo aparecendo periodicamente? Precisa de credencial própria ou é a mesma que o Estudante 1 já usa? Isso decide se dá pra automatizar com um cronjob simples.
6. Se existe alguma limitação de acesso (rate limit, necessidade de autorização formal do administrador da usina) pra qualquer uma dessas vias.

## D. Perguntas objetivas pro responsável do IFES (levar presencialmente)

1. Existe alguma documentação de integração/API fornecida pela PHB ou KSTAR junto com a instalação (manual técnico, termo de garantia, contrato de instalação)?
2. Quem tem a credencial de administrador do SolarPortal+/PowerStation — dá pra eu ter acesso de leitura próprio, sem depender de login compartilhado?
3. Os dataloggers (da usina e do Espaço Energia) têm alguma porta de comunicação local (RS-485, Ethernet) fisicamente acessível, ou tudo passa só pelo módulo Wi-Fi/celular que já sobe pra nuvem?
4. O acesso FTP da MAWS55 é exclusivo do projeto GERA ou é uma credencial da SEAMA-ES compartilhada — e existe uma pasta/estrutura fixa onde os arquivos novos aparecem automaticamente?
5. Existe algum equipamento de controle (PLC, gateway, controlador de carga) na instalação do Espaço Energia além do inversor KSTAR?
6. Há alguma restrição de rede do campus (firewall, VLAN isolada) que impediria um dispositivo meu (ex: Raspberry Pi) de acessar esses sistemas na mesma rede?
7. Existe algum contato técnico da PHB ou da KSTAR (suporte, integrador local) que já tenha resolvido esse tipo de integração antes?

## E. Documentos/fontes a procurar

- Manual técnico do inversor PHB (modelo específico dos INV01-04) — geralmente traz a seção de comunicação/protocolo.
- Manual técnico do KSTAR 5KDM — o datasheet costuma indicar se há RS-485/Modbus nativo.
- Qualquer termo de instalação/contrato com a PHB ou integradora que tenha instalado a usina — pode mencionar acesso a dados.
- Documentação da estação MAWS55 (linha Vaisala MAWS) — o fabricante documenta publicamente os protocolos de saída padrão dessa família (serial, Ethernet, FTP); vale achar o manual específico do modelo instalado.
- Política de rede/TI do campus (se existir), pra saber se um dispositivo próprio pode ficar na mesma rede dos equipamentos.

## F. Próximo passo prático da Atividade 2

O primeiro passo não é escrever código — é **inspecionar o tráfego do navegador enquanto uso o PowerStation/SolarPortal+ normalmente** (F12 → aba Network, ver se aparece alguma requisição JSON que eu poderia repetir programaticamente) e, em paralelo, **levar a lista de perguntas da seção D pra quem administra a usina/rede do campus**. São as duas ações que não dependem de decidir arquitetura antes da hora — uma é técnica e imediata, a outra é de agendar conversa.

Só depois dessas duas coisas decido se a Atividade 2 vira "cliente de API/scraping do portal" ou "protocolo de campo direto no equipamento" — e aí sim desenho a arquitetura.

---

*Nota paralela: aproveitei a liberação já dada pra consolidar o Repository (seção C da revisão anterior) — `carrega_banco.py` agora só chama `consultas.py`, que passou a cobrir leitura E escrita do banco. No processo, achei mais um bug real: `banco.conectar()` exigia que o banco já existisse, o que quebrava justamente o script que deveria criá-lo pela primeira vez. Separei em `conectar()` (leitura, exige banco existente) e `conectar_ou_criar()` (escrita, cria se precisar). Testado do zero: pipeline → banco → leitura, idempotência confirmada de novo, mesmos números de antes.*
