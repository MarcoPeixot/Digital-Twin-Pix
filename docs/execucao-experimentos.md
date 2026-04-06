# Execucao de Experimentos

## Objetivo

Padronizar a execucao reproduzivel dos cenarios experimentais com configuracao versionada, identificacao de versao e armazenamento estruturado dos resultados.

## Escopo

Inclui:

* cenarios versionados em `/experiments/scenarios`;
* runner unico em `/scripts/run_experiment.py`;
* modo `with-twin` e `without-twin`;
* armazenamento de resultados em `/results/runs`;
* comparacao simples em `/scripts/compare_runs.py`.

Limitacoes:

* nao substitui dashboards ou analise final detalhada;
* nao aplica mitigacao automatica real;
* depende de Docker local para reproducao completa;
* usa snapshots e resumos padronizados, nao uma camada analitica completa.

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
