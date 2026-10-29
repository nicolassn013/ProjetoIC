# Padrões de projeto: o que foi aplicado e o que foi adiado

Atualizado em 23/10/2026. Regra adotada: **só se aplica um padrão quando existe um problema concreto que ele resolve**. Cada decisão abaixo diz qual é o gatilho.

## Aplicados

| Padrão | Onde | Gatilho (problema concreto) |
|---|---|---|
| **Repository** | `app/consultas.py` (já existia) | Todo o SQL num lugar só. Estendido com `salvar_meteorologia`, o diário de ingestão e leituras pela view. Nenhum outro módulo escreve SQL |
| **Strategy / porta e adaptadores** | `pipeline/aquisicao/fontes.py` (`FonteFTP`, `FontePastaLocal`) | Duas fontes reais de arquivo: o servidor FTP e a pasta do FileZilla/teste. O resto do código só conhece `listar()` e `ler()`; trocar de fonte não mexe em tratamento nem em banco. Também permite testar sem rede |
| **Regras orientadas por dados** (tabela `REGRAS`) | `pipeline/aquisicao/tratamento.py` | Uma regra por grupo do catálogo, em vez de `if` por variável. Acrescentar uma variável é editar o catálogo, não o código |
| **Fonte única de verdade (catálogo)** | `app/catalogo_meteorologia.py` | Nomes de colunas repetidos em pipeline, banco, dicionário e testes. Agora vêm de um lugar e o teste avisa se divergirem |
| **Migrações versionadas** | `app/migracoes.py` e `app/migracoes/*.sql` | Estrutura do banco que evolui (4 versões) sem editar o `.db` à mão e sem perder dado |

## Considerados e adiados (com o gatilho que os traria de volta)

| Padrão | Por que não agora | Gatilho para aplicar |
|---|---|---|
| **Factory** formal | `criar_fonte()` já é uma função simples de 8 linhas; uma hierarquia de fábricas seria enfeite | Mais de 3 fontes com construção complicada |
| **Observer** | Não há eventos nem assinantes: a rotina roda por agendador | Alertas automáticos (por exemplo, INV04 offline) ou atualização em tempo real do dashboard |
| **Command** | Não há ações de controle, só leitura | Qualquer escrita em equipamento (Modbus de escrita). Hoje proibido |
| **Singleton** | A conexão com o SQLite é aberta e fechada por `with`, que é mais simples e mais seguro | Nunca previsto |
| **Adapter / nova porta para Modbus** | Sem mapa de registradores nem hardware decididos | Quando houver mapa: uma porta `FonteMedicoes` ao lado de `FonteArquivos`, com o mesmo desenho |

## Efeito prático

Para acrescentar o Modbus no futuro: nova fonte + nova regra de tratamento + migração de tabela, sem mexer no que já funciona.
