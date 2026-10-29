# Aquisição dos dados da MAWS55 até o banco

Atualizado em 24/10/2026 (formato confirmado com 2 arquivos reais do FTP). Documento de uso e de decisões da aquisição direta (FTP ou pasta) para o nosso banco `dados/leituras.db`.

## 1. O que faz

```text
FTP da estação ──┐
                 ├─> leitura (.txt -> tabela) -> tratamento (regras do Estudante 1) -> meteorologia_15min
Pasta com .txt ──┘                                                                   + diário ingestao_arquivos
```

- Baixa (ou lê de uma pasta) os arquivos `*_15m_AAAAMMDD_HHMM.txt`.
- Guarda uma **cópia bruta** de cada arquivo do FTP em `dados/brutos/maws55/` (não vai para o git).
- Lê o texto (seção 4), aplica as **mesmas regras de qualidade do script do Estudante 1** e grava em `meteorologia_15min`.
- Anota cada arquivo no **diário** `ingestao_arquivos` (nome, hash, status, linhas, mensagem de erro).
- Não envia nada ao site Lovable do GERA: a ponte do Estudante 1 (`GERAIF-Ponte`) continua separada e independente.

## 2. Como usar

```bash
# 1) configurar o FTP (uma vez): copie o modelo e preencha. O config.env nunca vai para o git
copy config.exemplo.env config.env          # Linux/Mac: cp

# 2) testar sem gravar nada
python pipeline/aquisicao_maws55.py --simular

# 3) rodar de verdade (os 8 arquivos mais recentes)
python pipeline/aquisicao_maws55.py

# outras formas
python pipeline/aquisicao_maws55.py --ultimos 20
python pipeline/aquisicao_maws55.py --periodo 202607            # um mês (AAAA, AAAAMM ou AAAAMMDD)
python pipeline/aquisicao_maws55.py --periodo tudo --confirmar  # histórico completo (> 500 arquivos exige --confirmar)
python pipeline/aquisicao_maws55.py --fonte pasta --pasta C:\dados\maws55   # arquivos baixados à mão com o FileZilla
```

Código de saída: 0 = tudo certo, 1 = algum arquivo deu erro, 2 = configuração ou uso errado.

**Rotina de 15 em 15 minutos:** agende no Agendador de Tarefas do Windows (ou cron) o comando `python pipeline/aquisicao_maws55.py` a cada 15 min. Ele só processa o que ainda não foi processado, então rodar a mais não faz mal.

## 3. Garantias (cobertas por testes)

| Garantia | Como |
|---|---|
| Rodar duas vezes não duplica nem muda nada | Arquivo com mesmo nome e mesmo conteúdo é pulado (diário) |
| Um arquivo novo não apaga o resto do dia | Gravação em modo `mesclar`: troca só os horários que ele traz |
| Arquivo reenviado com conteúdo diferente é reprocessado | O hash muda |
| Um arquivo ruim não derruba os outros | Cada arquivo tem a sua própria transação; o erro vai para o diário e o arquivo é tentado de novo na próxima rodada |
| Nada se perde na fonte | A cópia bruta é guardada; conteúdo diferente com o mesmo nome ganha sufixo de hash, não sobrescreve |
| Vazio é NULL e zero verdadeiro continua zero | Teste de umidade 0 % e precipitação 0 mm |
| Regras idênticas às do Estudante 1 | Teste que roda as regras nas **107.902 linhas** do layout de 56 valores do arquivo tratado dele e compara 56 valores + 24 flags: **resultado idêntico** (24/10/2026). As 3.653 linhas do layout de 52 ficam de fora de propósito (seção 4.2) |
| Senha nunca aparece | Fora do `repr`, das mensagens de erro e dos logs; só o **nome** da variável ausente é citado |

## 4. O formato do .txt e o que NÃO está validado

### 4.1 Formato real (confirmado com `EMA_SER_01_15m_20220715_1900.txt` e `..._2330.txt`)

Uma linha por arquivo, separada por vírgula, **sem cabeçalho**: `local, freq, data, hora (UTC), valores...`. O horário do arquivo é **UTC** (conferido contra a coluna `UTC` do xlsx tratado do Estudante 1); o horário local é UTC - 3 h. Como não há cabeçalho, o significado de cada posição vem da ordem fixa em `leitor.ORDEM_56` (a mesma ordem das colunas do arquivo bruto dele, conferida por teste).

| Layout | Valores por linha | Quando |
|---|---|---|
| Completo | 56 | a partir de 22/08/2022 (o dos 111.555 registros, menos os 3.653 primeiros) |
| Antigo | 52 (sem o grupo `Temperatura ... LPNET14 (NTC)`) | 15/07/2022 a 22/08/2022 (os dois arquivos recebidos são deste layout) |

Qualquer outra quantidade de valores (arquivo cortado no meio da transferência, formato novo) é **erro**: nada é gravado, o arquivo vai para o diário e é tentado de novo na próxima rodada. O layout é escolhido pela contagem, nunca por suposição.

### 4.2 Achado: nomes de colunas deslocados no arquivo tratado do Estudante 1

No xlsx tratado, as **3.653 linhas de 15/07/2022 19:00 a 22/08/2022 20:00 UTC** têm 52 valores, mas receberam os nomes das 56 colunas na ordem. Resultado: em `Temperatura inst LPNET14 (NTC)` está a direção do vento, em `Direção vento med` está a velocidade, em `Velocidade vento max` está a temperatura do solo, em `Umid solo inst` está a precipitação, e as 4 últimas colunas ficam vazias. Os valores deslocados fazem sentido físico só na leitura corrigida (direção 0 a 360, velocidade 0 a 17 m/s, temperatura do solo cerca de 25 °C, umidade do solo cerca de 0,45). Por isso a aquisição lê esse trecho pelo layout de 52 e a **comparação com o arquivo dele exclui essas linhas**. O banco ainda não recebeu esse período; quando o histórico for carregado, use a aquisição (pastas do FTP), não o xlsx dele, para essas 3.653 linhas. Avisar o Estudante 1.

### 4.3 O que continua sem validação

1. **Layout de 56 valores em arquivo real.** Só o de 52 foi visto em arquivo real. O de 56 segue a ordem do xlsx dele (teste confere) e foi testado com arquivos sintéticos feitos dos valores brutos dele (300 linhas por texto; um dia inteiro de 96 arquivos pela linha de comando, igual ao pipeline). Se aparecer um arquivo recente que falhe, mande a primeira linha (sem dados sensíveis, são só medições) para ajustar.
2. **FTP real.** Nunca foi testado contra o servidor (só contra um FTP simulado). O servidor só é acessível de dentro da rede do campus.
3. **Início ou fim do intervalo de 15 min** (pergunta aberta ao Estudante 1). Mantido o mesmo critério do pipeline atual: `timestamp_15min` = horário do arquivo cortado para múltiplo de 15 min.
4. **Fuso.** O arquivo traz só UTC; o horário local é `UTC - 3 h` fixo.
5. **`lacuna_temporal`** fica vazia (desconhecida) nos dados que chegam por aqui; só o arquivo histórico do Estudante 1 a preenche.
6. **Duas linhas no mesmo bloco de 15 min** (ex.: 16:00:07 e 16:00:40): fica a mais recente, e a contagem aparece na mensagem do diário.
7. **Regra de umidade do solo** (`== -400`) nunca dispara porque a coluna só tem valores de -0,4 a 1,0. Replicada como está, a confirmar com o Estudante 1.
8. **As 32 variáveis brutas** seguem sem tratamento nem flag.

## 5. Segurança

- O `config.env` e qualquer `*.env` estão no `.gitignore`; só o `config.exemplo.env` (sem segredo) é versionado.
- O zip `GERAIF-Ponte` contém um `config.env` com **usuário, senha do FTP e token do GERAIF reais**. Não copie esse arquivo para o repositório. Como ele circulou por chat e por zip, **combine a troca da senha do FTP e do token** com o responsável.
- O FTP comum (porta 21) trafega a senha **sem criptografia**. Se o servidor aceitar FTPS, use `FTP_TLS=1` no `config.env`.
- Antes de cada commit: `git status` e `git diff --cached --stat`, procurando `config.env`, `dados/brutos/maws55/` e `dados/backups/`.

## 6. Onde está no código

| Arquivo | Papel |
|---|---|
| `pipeline/aquisicao_maws55.py` | Linha de comando |
| `pipeline/aquisicao/config.py` | Lê `config.env` e variáveis de ambiente |
| `pipeline/aquisicao/fontes.py` | `FonteFTP` e `FontePastaLocal` (mesma interface) |
| `pipeline/aquisicao/leitor.py` | `.txt` para tabela |
| `pipeline/aquisicao/tratamento.py` | Regras de qualidade e conversão para as colunas do banco |
| `pipeline/aquisicao/ingestao.py` | Orquestra, cópia bruta e diário |
| `app/consultas.py` | `salvar_meteorologia(modo="mesclar")`, `ingestao_ja_feita`, `registrar_ingestao`, `ultimas_ingestoes` |
| `app/migracoes/003_...sql`, `004_...sql` | Estrutura nova do banco |
| `testes/test_aquisicao.py` | 47 testes da aquisição (inclui os 2 arquivos reais e a conferência com o xlsx dele) |
