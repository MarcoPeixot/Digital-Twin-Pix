# Cenario 1 - Operacao normal

## Objetivo

Comparar explicitamente as execucoes without-twin e with-twin do cenario com base nos artefatos consolidados do experimento.

## Rastreabilidade

- scenario_id: `cenario-01-operacao-normal`
- scenario_group: `baseline`
- config_sha256: `df7eaccdb2ebd28a8f4c5395392d6ea5731d3e0a22027775a817f42ac70f0993`
- without_twin run_id: `20260406T012528Z__cenario-01-operacao-normal__without-twin`
- with_twin run_id: `20260406T013316Z__cenario-01-operacao-normal__with-twin`
- without_twin commit: `66992fe5c3f8b5efc12e13eada417f3177ca91f7`
- with_twin commit: `66992fe5c3f8b5efc12e13eada417f3177ca91f7`
- without_twin dirty: `True`
- with_twin dirty: `True`

## Tabela comparativa

| Metrica | Sem twin | Com twin | Delta | Delta % | Melhor resultado |
| --- | ---: | ---: | ---: | ---: | --- |
| Throughput (req/s) | 760.18 | 796.39 | 36.21 | 4.76% | with-twin |
| Latencia media HTTP (ms) | 5.17 | 4.93 | -0.2417 | -4.67% | with-twin |
| Latencia p95 HTTP (ms) | 13.05 | 12.17 | -0.8738 | -6.70% | with-twin |
| Latencia p95 API Gateway (ms) | 11.47 | 10.94 | -0.5243 | -4.57% | with-twin |
| Latencia p95 Processing Core (ms) | 4.42 | 4.03 | -0.3932 | -8.89% | with-twin |
| Latencia p95 Directory (ms) | 0.0019 | 0.0017 | -0.0002 | -10.36% | with-twin |
| Taxa de sucesso (%) | 100.00% | 100.00% | 0.00% | 0.00% | n/a |
| Taxa de erro (%) | 0.00% | 0.00% | 0.00% | 0.00% | n/a |
| Backlog maximo (itens) | 0.0000 | 0.0000 | 0.0000 | 0.00% | n/a |
| Timeouts de processamento (eventos) | 0.0000 | 0.0000 | 0.0000 | 0.00% | n/a |
| Rejeicoes por fila (eventos) | 0.0000 | 0.0000 | 0.0000 | 0.00% | n/a |

## Interpretacao objetiva

- O sistema degradou? Nao houve degradacao observada no resumo consolidado.
- Em que ponto a degradacao comecou? O ponto exato de inicio da degradacao nao pode ser determinado com precisao porque os artefatos atuais sao snapshots finais, nao series temporais completas.
- O gemeo detectou antes da falha evidente? Nao houve alerta ou recomendacao registrada pelo twin neste cenario.
- A mitigacao melhorou o comportamento? Nao ha evidencia de mitigacao efetiva registrada nos artefatos atuais.
- O ganho foi mensuravel? Conclusao automatica do cenario: favoravel ao twin. O ganho mensuravel favoreceu o twin em throughput maior (796.39 vs 760.18); latencia p95 menor (12.17 vs 13.05).

## Grafico

Arquivo SVG: `chart-cenario-01-operacao-normal.svg`
