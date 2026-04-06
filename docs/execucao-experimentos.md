# Execucao de Experimentos

## Objetivo

Padronizar a execucao reproduzivel dos cenarios experimentais com configuracao versionada, identificacao de versao e armazenamento estruturado dos resultados.

## Escopo

Inclui:

* cenarios versionados em `/experiments/scenarios`;
* runner unico em `/scripts/run_experiment.py`;
* modo `with-twin` e `without-twin`;
* armazenamento de resultados em `/results/runs`;
* comparacao simples em `/scripts/compare_runs.py`;
* analise final consolidada em `/scripts/analyze_results.py`.

Limitacoes:

* nao substitui dashboards complexos;
* nao aplica mitigacao automatica real;
* depende de Docker local para reproducao completa;
* depende dos artefatos previamente gerados em `/results/runs`;
* usa snapshots e resumos padronizados, nao series temporais completas por execucao.

## Estrutura de resultados

Cada execucao gera uma pasta em `/results/runs/<run_id>` contendo:

* `manifest.json`;
* `scenario.json`;
* `effective-config.json`;
* `load-summary.json`;
* `prometheus-snapshot.json`;
* `twin-state.json`;
* `events.json`;
* `summary.json`.

## Comparacao

Use `/scripts/compare_runs.py` para comparar duas execucoes e gerar um arquivo em `/results/comparisons`.

## Analise final

Use `/scripts/analyze_results.py` para:

* localizar pares completos `without-twin` e `with-twin` por cenario;
* gerar tabelas comparativas em CSV e Markdown;
* gerar graficos simples em SVG;
* produzir interpretacao objetiva por cenario;
* consolidar uma conclusao final em `/results/analysis/<timestamp>`.
