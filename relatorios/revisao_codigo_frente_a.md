# Revisão do código e reorganização (Frente A)

Revisei os scripts que eu fiz (`app/` e `pipeline/`), rodei tudo de novo do zero e comparei com o banco que eu já tinha. Os números continuam iguais (192 linhas de 15 min, PR de 22/09/2025 = 0,831; diferença máxima entre as duas execuções de 1e-14, que é arredondamento do computador). Não mexi nos scripts do Estudante 1.

## O que eu achei e o que eu fiz

| # | Achado | O que fiz |
|---|---|---|
| 1 | O arquivo da meteorologia (44 MB) era relido a cada dia processado: o pipeline levava ~4 min | Passei a ler uma vez só (cache). Agora leva ~1 min 20 s, com o mesmo resultado |
| 2 | Os relatórios de 2026 vêm de **10 em 10 min**, os de 2025 de 5 em 5. O campo `registros_eletricos_5min` conta amostras, não 5 minutos | O pipeline agora mede o intervalo e avisa. Mantive o nome da coluna para não quebrar o banco; está documentado no README |
| 3 | O relatório da usina tem **duas plantas** ("Ifes Serra" e "Ifes Campus Serra"). O código escolhia a linha com mais valores, sem avisar | Mantive a regra, mas agora ele avisa se mais de uma planta tiver dado |
| 4 | Se faltasse potência da usina em horário de sol, o PR contava 0 kW e saía mais baixo sem aviso | O PR agora só é calculado se não houver buraco de potência quando há sol (GHI > 20 W/m²). Para 22/09/2025 não muda nada (0 buracos) |
| 5 | A função `extrair_data_relatorio` não era usada por ninguém (a data vinha só do nome do arquivo) | Passou a conferir se a data escrita dentro do arquivo bate com a do nome (`conferir_data_no_arquivo`) |
| 6 | O histórico anual não tinha conferência | Adicionei: a soma dos 4 inversores precisa bater com a usina em cada ano. Bate em todos os anos (2020 a 2026) |
| 7 | Se um arquivo não existisse, o erro era `IndexError` sem explicação; se houvesse dois, pegava um qualquer | Agora dá erro claro, ou avisa e usa o mais recente |
| 8 | Mensagens e comentários ainda citavam caminhos antigos (`scripts/popula_banco.py`) | Corrigidos |
| 9 | A soma dos inversores usava `pd.NA` (tipo "object") | Troquei por número vazio (`NaN`); o resultado é o mesmo |

## O que continua pendente (não dá para resolver só com código)

- **INV04 = 14 kW** é hipótese (35+35+35+14 = 119 kW). Precisa de confirmação com quem opera a usina.
- **INV03 com 0 kWh de 2020 a 2024**: causa desconhecida.
- **Meteorologia só até 31/07/2026**: o arquivo do Estudante 1 precisa ser estendido para cobrir 22/09/2026.
- **Hora da meteorologia**: não sei se o horário da MAWS55 marca o começo ou o fim de cada intervalo de 15 min. Isso muda em até 15 min o alinhamento com a usina. Vale perguntar ao Estudante 1.
- **Alinhamento 10 min → 15 min**: nos dias de 10 em 10 min, cada intervalo de 15 min fica com 1 ou 2 amostras, alternando. A média funciona, mas é menos uniforme que nos dias de 5 min.
- Só há **2 dias** completos (22/09/2025 e 22/09/2026), então qualquer conclusão estatística ainda é fraca.

## Nomes que mudei

| Antes | Depois |
|---|---|
| `pipeline/passo4_pipeline.py` | `pipeline/integra_usina_meteorologia.py` |
| `pipeline/popula_banco.py` | `pipeline/carrega_banco.py` |
| `pipeline/legado/integracao_usina.py` | `pipeline/legado/integracao_usina_v1_dia_unico.py` |
| `dados/brutos_usina/Relátorio da usina_inversores/` | `dados/brutos/usina_powerstation/` |
| `relatorios/Relatorio_Passos_2_3_4.md` etc. | `relatorios/relatorio_integracao_dados.md`, `relatorio_banco_de_dados.md`, `contexto_retomada_pipeline.md`, `revisao_arquitetural.md`, `investigacao_comunicacao_atividade2.md`, `plano_de_estudos.md`, `dicionario_tecnico.md`, `organizacao_projeto_picti.xlsx` |

Os arquivos brutos exportados do portal **mantêm o nome original** de propósito: o pipeline acha a data no nome (`(20250922)`) e os próximos downloads vão chegar com esse mesmo padrão. Os relatórios antigos (`relatorio_*.md`, `contexto_*.md`) só tiveram os nomes de arquivos atualizados dentro do texto; o conteúdo continua o do dia em que foram escritos.
