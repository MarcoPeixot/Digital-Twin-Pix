# Analise Final dos Resultados Experimentais

## Objetivo

Consolidar a comparacao final entre execucoes with-twin e without-twin, com foco em metricas operacionais, interpretacao por cenario e conclusao objetiva para uso na IC.

## Rastreabilidade

- analysis_id: `validation-check`
- generated_at: `2026-04-06T01:53:28+00:00`
- source_runs_dir: `results/runs`
- analyzed_pairs: `1`

## Conclusao consolidada

- No conjunto disponivel, o efeito agregado do gemeo digital ficou neutro ou inconclusivo.
- Cenarios favoraveis ao twin: 0
- Cenarios desfavoraveis ao twin: 0
- Cenarios neutros ou inconclusivos: 1
- Disponibilidade dos dados: Ainda faltam pares completos para os cenarios: cenario-02-pico-repentino, cenario-03-directory-degradado, cenario-04-saturacao-fila, cenario-05-falha-parcial-processing.

## Cenarios analisados

### Cenario 1 - Operacao normal

- scenario_id: `cenario-01-operacao-normal`
- efeito consolidado: `neutro ou inconclusivo`
- base da classificacao: Sem degradacao observada e sem atividade registrada do twin; diferencas pequenas ficam tratadas como variacao de execucao, nao como ganho experimental.
- config_sha256: `df7eaccdb2ebd28a8f4c5395392d6ea5731d3e0a22027775a817f42ac70f0993`
- without_twin run_id: `20260406T012528Z__cenario-01-operacao-normal__without-twin`
- with_twin run_id: `20260406T013316Z__cenario-01-operacao-normal__with-twin`
- relatorio detalhado: `scenarios/cenario-01-operacao-normal/report.md`

## Cenarios ainda sem par completo

- `cenario-02-pico-repentino`
- `cenario-03-directory-degradado`
- `cenario-04-saturacao-fila`
- `cenario-05-falha-parcial-processing`

## Limitacoes

- A analise depende apenas dos artefatos ja salvos em `results/runs`.
- O ponto exato de inicio da degradacao nao pode ser estimado com alta precisao sem series temporais completas por execucao.
- Os graficos desta etapa sao comparativos e simples; nao substituem dashboards ou observabilidade em tempo real.
