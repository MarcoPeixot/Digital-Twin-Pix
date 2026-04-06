# Analise Final dos Resultados Experimentais

## Objetivo

Consolidar a comparacao final entre execucoes with-twin e without-twin, com foco em metricas operacionais, interpretacao por cenario e conclusao objetiva para uso na IC.

## Rastreabilidade

- analysis_id: `20260406T014623Z`
- generated_at: `2026-04-06T01:46:23+00:00`
- source_runs_dir: `results/runs`
- analyzed_pairs: `1`

## Conclusao consolidada

- No conjunto disponivel, o efeito agregado do gemeo digital foi predominantemente favoravel.
- Cenarios favoraveis ao twin: 1
- Cenarios desfavoraveis ao twin: 0
- Cenarios neutros ou inconclusivos: 0
- Disponibilidade dos dados: Ainda faltam pares completos para os cenarios: cenario-02-pico-repentino, cenario-03-directory-degradado, cenario-04-saturacao-fila, cenario-05-falha-parcial-processing.

## Cenarios analisados

### Cenario 1 - Operacao normal

- scenario_id: `cenario-01-operacao-normal`
- efeito consolidado: `favoravel ao twin`
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
